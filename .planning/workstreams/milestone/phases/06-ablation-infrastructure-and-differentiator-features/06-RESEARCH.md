# Phase 6: Ablation Infrastructure and Differentiator Features - Research

**Researched:** 2026-04-15
**Domain:** Python ablation runner design, force-routing cascade evaluation, cross-message cosine similarity features
**Confidence:** HIGH (all findings grounded in direct codebase inspection)

## Summary

Phase 6 has two independent deliverables: (1) a reusable `ablation.py` module with `AblationConfig` and force-routing threshold helpers, and (2) two new Stage 2a features — cross-message cosine similarity (mean pairwise) and near-duplicate fraction (sim > 0.9).

Force-routing is implemented by replacing `StageThresholds` fields with extreme values that guarantee every account exits at a given stage. The existing `predict_system()` function already contains all the conditional logic needed — the ablation runner just needs to manipulate thresholds to disable downstream routing. No changes to `predict_system()` itself are needed.

FEAT-04 (cross-message similarity) is a pure addition to `extract_stage2_features()` in `features_stage2.py`. The embedder already produces normalized 384-dim vectors; cosine similarity between normalized vectors is the dot product, so mean pairwise similarity requires only a matrix multiply on the (N_msgs x 384) embedding matrix. No new dependencies are introduced.

**Primary recommendation:** Build `ablation.py` as a thin orchestration module that wraps `predict_system()` and `evaluate_s3()`. Force-routing to Stage 1 means setting `s1_bot=0.0` and `s1_human=1.0`, making no account exit early via Stage 1 thresholds — then disabling AMR and Stage 3 gates entirely by setting `n1_max_for_exit=1e9`, `s2a_bot=0.0`, `s2a_human=1.0`, `n2_trigger=1e9`, `disagreement_trigger=1e9`, `s12_bot=0.0`, `s12_human=1.0`, `novelty_force_stage3=1e9`.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| FEAT-04 | Stage 2a includes cross-message cosine similarity (mean pairwise) and near-duplicate fraction (sim > 0.9) | Embedder already normalizes; pairwise cosine = dot product on normalized; implemented in `extract_stage2_features()` as 2 scalar features appended after the existing 395-dim vector |
| ABL-01 | Ablation runner supports force-routing to evaluate full test set at each stage | `StageThresholds` extreme-value substitution pattern; wraps existing `predict_system()` + `evaluate_s3()`; `AblationConfig` dataclass controls which stage to force-route to |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | already installed | Pairwise cosine similarity, mean/fraction computation | In-project standard; `np.dot` on normalized vectors = cosine |
| dataclasses | stdlib | `AblationConfig` dataclass | Pattern already used (`StageThresholds`, `TrainedSystem`, `FeatureConfig`) |
| botdetector_pipeline | in-project | `predict_system()`, `StageThresholds`, `TrainedSystem` | Existing cascade entry points |
| evaluate | in-project | `evaluate_s3()` for per-variant S3 metrics | Already returns structured dict |

### No New Dependencies

All Phase 6 work uses only existing imports. No new pip installs are required.

**Verified current feature vector dimensions:**
- `emb_pool`: 384 (indices 0–383)
- `ling_pool`: 4 (indices 384–387)
- `temporal`: 7 — rate, delta_mean, delta_std, cv_intervals, char_len_mean, char_len_std, hour_entropy (indices 388–394)
- **Total: 395 dims** (confirmed in `test_features_stage2.py` assertions)

After FEAT-04, the vector will be **397 dims**:
- index 395: `cross_msg_sim_mean` (mean pairwise cosine similarity)
- index 396: `near_dup_frac` (fraction of message pairs with cosine similarity > 0.9)

## Architecture Patterns

### Recommended Project Structure

```
SocialBotDetectionSystem/
├── ablation.py              # NEW: AblationConfig, force_route_thresholds(), run_ablation()
├── features_stage2.py       # MODIFY: add FEAT-04 features at end of extract_stage2_features()
├── tests/
│   ├── test_ablation.py     # NEW: ABL-01 verification tests
│   └── test_features_stage2.py  # EXTEND: add FEAT-04 tests
```

### Pattern 1: Force-Routing via Threshold Extremes

**What:** Override `StageThresholds` so that every account is forced to evaluate at exactly one stage. Since the routing conditions in `predict_system()` use threshold comparisons, setting thresholds to impossible values makes conditions never trigger.

**When to use:** Any time you need to evaluate all accounts at Stage 1 only, Stage 2 only, or Stage 3 only for ablation.

**How it works — Stage 1 force-routing (all accounts evaluate at Stage 1 ONLY):**

The routing logic in `predict_system()`:
```python
# AMR gate: uncertain | novel | disagree
amr_mask = gate_amr(p2a, n2, z1, z2a, th)

# gate_amr internals:
uncertain = (p2a > th.s2a_human) & (p2a < th.s2a_bot)
novel = n2 >= th.n2_trigger
disagree = np.abs(z1 - z2a) >= th.disagreement_trigger
```

To force ALL accounts to Stage 1 only (never escalate to AMR or Stage 3):
```python
# Force-route to Stage 1: disable AMR and Stage 3 entirely
th_force_s1 = StageThresholds(
    s1_bot=0.0,          # never exit early via Stage 1 bot threshold
    s1_human=1.0,        # never exit early via Stage 1 human threshold
    n1_max_for_exit=1e9, # novelty never blocks exit
    s2a_bot=0.0,         # AMR uncertain band never triggers (p2a never in (1.0, 0.0))
    s2a_human=1.0,
    n2_trigger=1e9,      # novelty never triggers AMR
    disagreement_trigger=1e9,  # disagreement never triggers AMR
    s12_bot=0.0,         # Stage 3 routing never triggers
    s12_human=1.0,
    novelty_force_stage3=1e9,
)
```

NOTE: Stage 1's exit thresholds (`s1_bot`, `s1_human`, `n1_max_for_exit`) are NOT used by `predict_system()` currently — it runs all stages and combines via meta-models. The force-routing achieves the per-stage ablation effect by ensuring only Stage 1's output contributes meaningfully to `p_final`. The cleanest interpretation is: `p1` from Stage 1 is the ablation-stage output, evaluated directly against S3 labels.

**CRITICAL DESIGN DECISION:** Looking at `predict_system()` carefully, it always runs ALL stages and then combines them with meta-models. The "force-routing to Stage 1 only" ablation means evaluating `p1` (not `p_final`) against S3. ABL-01 Success Criterion 3 states: "no accounts escalated to Stage 2 or 3" — this means the force-routing must prevent AMR gate and Stage 3 gate from activating.

The correct interpretation: force-routing creates `amr_mask=False` for all accounts (so no AMR computed) and `stage3_mask=False` for all accounts (so Stage 3 never runs). Evaluation then uses `p1` as the ablation output.

**Stage 2 force-routing (all accounts evaluate AMR but no Stage 3):**
```python
th_force_s2 = StageThresholds(
    s2a_bot=0.0,         # AMR uncertain band always true
    s2a_human=1.0,       # (p2a always in (0.0, 1.0) in practice — wait, this fails)
    # CORRECT: to force AMR always ON, need uncertain to be always True:
    # uncertain = (p2a > s2a_human) & (p2a < s2a_bot)
    # To make this True for all p2a in [0,1]: s2a_human=0.0, s2a_bot=1.0+eps
    s2a_human=0.0,
    n2_trigger=-1.0,     # novelty always >= -1: forces novel=True redundantly
    disagreement_trigger=-1.0,
    s12_bot=0.0,         # Stage 3 never escalates
    s12_human=1.0,
    novelty_force_stage3=1e9,
)
```

**Cleaner approach — explicit per-stage threshold builders:**

```python
from dataclasses import dataclass
from typing import Literal

ForceStage = Literal["stage1", "stage2", "stage3", "normal"]

@dataclass
class AblationConfig:
    name: str
    force_stage: ForceStage = "normal"
    description: str = ""

def force_route_thresholds(force_stage: ForceStage) -> StageThresholds:
    """Return StageThresholds that route all accounts to exactly the given stage."""
    if force_stage == "stage1":
        # Disable AMR (s2a_human=1.0, s2a_bot=0.0 — impossible band) and Stage 3
        return StageThresholds(
            s2a_human=1.0, s2a_bot=0.0,       # amr uncertain band impossible
            n2_trigger=1e9,                    # amr novelty never triggers
            disagreement_trigger=1e9,          # amr disagreement never triggers
            s12_human=1.0, s12_bot=0.0,        # stage3 uncertain band impossible
            novelty_force_stage3=1e9,          # stage3 novelty never triggers
        )
    if force_stage == "stage2":
        # Force AMR always (set uncertain band to cover all probabilities),
        # disable Stage 3
        return StageThresholds(
            s2a_human=0.0, s2a_bot=1.0,        # amr uncertain band covers [0,1]
            n2_trigger=-1.0,                   # redundant: novel always True
            disagreement_trigger=-1.0,
            s12_human=1.0, s12_bot=0.0,        # stage3 never
            novelty_force_stage3=1e9,
        )
    if force_stage == "stage3":
        # Force Stage 3 always
        return StageThresholds(
            s2a_human=0.0, s2a_bot=1.0,
            n2_trigger=-1.0,
            disagreement_trigger=-1.0,
            s12_human=0.0, s12_bot=1.0,        # stage3 uncertain band covers [0,1]
            novelty_force_stage3=-1.0,
        )
    return StageThresholds()  # normal: calibrated defaults
```

**Evaluation metric for each force-stage:**
- `force_stage="stage1"` → evaluate `p1` (Stage 1 output) against S3 labels
- `force_stage="stage2"` → evaluate `p2` or `p12` against S3 labels
- `force_stage="stage3"` → evaluate `p_final` (full cascade) against S3 labels
- `force_stage="normal"` → evaluate `p_final` against S3 labels

The ABL-01 success criterion for force-routing to Stage 1 specifically checks that `amr_used` and `stage3_used` are all 0 in the results.

### Pattern 2: FEAT-04 — Cross-Message Cosine Similarity

**What:** Compute mean pairwise cosine similarity and near-duplicate fraction across an account's message embeddings. Because `TextEmbedder.encode()` uses `normalize_embeddings=True`, all embedding vectors are already unit-normalized — cosine similarity is simply the dot product.

**When to use:** Always computed as part of `extract_stage2_features()`.

**Key edge cases:**
- 0 messages: both features = 0.0
- 1 message: no pairs exist; both features = 0.0
- 2+ messages: pairwise cosine similarity matrix = `emb @ emb.T`; exclude diagonal; mean and fraction threshold

```python
# FEAT-04: Cross-message cosine similarity (indices 395, 396)
# emb shape: (N_msgs, 384), already normalized by embedder
if len(texts) >= 2:
    sim_matrix = emb @ emb.T  # (N, N), values in [-1, 1]
    n_msgs = sim_matrix.shape[0]
    # Exclude diagonal (self-similarity = 1.0)
    mask = np.ones((n_msgs, n_msgs), dtype=bool)
    np.fill_diagonal(mask, False)
    off_diag = sim_matrix[mask]  # (N*(N-1),)
    cross_msg_sim_mean = float(np.mean(off_diag))
    near_dup_frac = float(np.mean(off_diag > 0.9))
else:
    cross_msg_sim_mean = 0.0
    near_dup_frac = 0.0
```

**Position in feature vector:** Appended after the existing `temporal` array:
```python
feat = np.concatenate([emb_pool, ling_pool, temporal, np.array([cross_msg_sim_mean, near_dup_frac], dtype=np.float32)], axis=0)
```

New total: **397 dims**

**Scoping: `emb` variable availability**

In the current `extract_stage2_features()`, `emb` is computed only when `len(texts) > 0` and scoped inside that branch. The FEAT-04 code must be placed inside the `if len(texts) > 0:` block, or `emb` must be made available to the outer scope via an `else` branch:

```python
# Placement within current code structure:
if len(texts) > 0:
    emb = embedder.encode(texts)
    if probe_dim is None:
        probe_dim = emb.shape[1]
    emb_pool = emb.mean(axis=0).astype(np.float32)
    
    # FEAT-04 (inside this block, emb is available)
    if emb.shape[0] >= 2:
        sim_matrix = emb @ emb.T
        n_msgs = emb.shape[0]
        mask = np.ones((n_msgs, n_msgs), dtype=bool)
        np.fill_diagonal(mask, False)
        off_diag = sim_matrix[mask]
        cross_msg_sim_mean = float(np.mean(off_diag))
        near_dup_frac = float(np.mean(off_diag > 0.9))
    else:
        cross_msg_sim_mean = 0.0
        near_dup_frac = 0.0
else:
    if probe_dim is None:
        probe_dim = 384
    emb_pool = np.zeros(probe_dim, dtype=np.float32)
    cross_msg_sim_mean = 0.0
    near_dup_frac = 0.0
```

### Pattern 3: AblationConfig and run_ablation()

```python
@dataclass
class AblationConfig:
    name: str
    force_stage: ForceStage = "normal"
    eval_col: str = "p_final"  # which column from predict_system() to evaluate
    description: str = ""

def run_ablation(
    system: TrainedSystem,
    S3: pd.DataFrame,
    edges_S3: pd.DataFrame,
    nodes_total: int,
    configs: List[AblationConfig],
    threshold: float = 0.5,
) -> Dict[str, dict]:
    """
    Run one or more ablation variants against S3.
    Returns: {config.name: evaluate_s3() result dict}
    """
```

### Anti-Patterns to Avoid

- **Modifying `predict_system()`:** Do NOT add `force_stage` parameters to `predict_system()`. Keep ablation logic in `ablation.py`; it only manipulates `system.th` before calling the existing function.
- **Mutating the system in place permanently:** `run_ablation()` should save and restore `system.th` after each variant, or use a copy. The trained system is reused across variants.
- **Using `s2a_bot=0.0, s2a_human=1.0` to "force" AMR:** The uncertain band `(p2a > s2a_human) & (p2a < s2a_bot)` = `(p2a > 1.0) & (p2a < 0.0)` is always False — this correctly DISABLES AMR (Stage 1 force-route). To ENABLE always, use `s2a_human=0.0, s2a_bot=1.0` (uncertain if 0 < p2a < 1, which is always true for calibrated probabilities).
- **Retraining for ablation:** Force-routing ablation evaluates the ALREADY TRAINED `trained_system_v11.joblib` with different routing thresholds. No retraining occurs in Phase 6.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pairwise similarity | Custom similarity loop | `emb @ emb.T` (numpy) | O(N^2) matrix multiply is vectorized; explicit loop over pairs is slow for max_msgs=50 |
| Deep copy of TrainedSystem | Manual field copying | `copy.deepcopy(system.th)` or save/restore `th` | `TrainedSystem` is a dataclass with nested models; deepcopy the threshold object only |
| Ablation metric collection | Custom metric aggregation | `evaluate_s3()` return dict | Already returns structured `{"overall", "per_stage", "routing"}` |

**Key insight:** The cascade architecture was designed for interpretability — each stage produces clean `(p, u, n, z)` outputs accessible via the results DataFrame. Ablation runner requires zero internal changes to production code.

## Common Pitfalls

### Pitfall 1: Mutating system.th During Ablation

**What goes wrong:** `run_ablation()` loops over variants, mutating `system.th` for each. If not restored, later variants run with a corrupted threshold state.

**Why it happens:** `predict_system()` reads `sys.th` directly; changing it changes behavior immediately.

**How to avoid:** Save original `th` before loop; restore after each variant. Or use `copy.deepcopy(system.th)` to create per-variant threshold objects:
```python
original_th = system.th
for cfg in configs:
    system.th = force_route_thresholds(cfg.force_stage)
    result = predict_system(system, S3, edges_S3, nodes_total)
    ...
system.th = original_th  # always restore
```

**Warning signs:** Second ablation variant produces identical routing statistics to the first.

### Pitfall 2: Feature Dimension Mismatch After FEAT-04

**What goes wrong:** Existing tests assert `feat.shape == (1, 395)`. After adding FEAT-04, shape becomes `(1, 397)`. All existing FEAT-01/02/03 index assertions (391, 392, 393, 394) still hold — new features are appended at the end.

**Why it happens:** Tests hard-code expected shape.

**How to avoid:** Update the shape assertion in `test_feat01_default_zero` (and any other shape checks) to `(1, 397)`. Do NOT change the existing feature indices — they are correct.

**Warning signs:** `test_feat01_default_zero` fails with `AssertionError: Expected (1, 395), got (1, 397)`.

### Pitfall 3: Near-Duplicate Fraction Threshold in Embedding Space

**What goes wrong:** The 0.9 threshold for near-duplicates applies to cosine similarity of normalized embeddings. MiniLM embeddings for very similar texts will cluster around 0.85-0.99 cosine similarity. For genuine near-duplicates (copy-paste spam), similarity exceeds 0.9 reliably. For thematically similar but distinct texts, similarity is typically 0.6-0.8.

**Why it happens:** Threshold choice is domain-specific; 0.9 is specified in ABL-01 requirements.

**How to avoid:** Hard-code the 0.9 threshold as a constant at module level for clarity:
```python
_NEAR_DUP_SIM_THRESHOLD = 0.9
```

**Warning signs:** `near_dup_frac` is uniformly 0.0 (threshold too high) or uniformly 1.0 (threshold too low).

### Pitfall 4: ABL-01 Verification — What "Force-Route to Stage 1" Means

**What goes wrong:** The success criterion says "no accounts escalated to Stage 2 or 3". In `predict_system()`, the `amr_used` and `stage3_used` columns in the results DataFrame track escalation. Force-routing to Stage 1 must result in all zeros in both columns.

**Why it happens:** The force_stage="stage1" threshold configuration must correctly disable BOTH the AMR gate and the Stage 3 gate. Missing one condition means some accounts still escalate.

**How to avoid:** Test assertion:
```python
assert (results["amr_used"] == 0).all(), "Some accounts were escalated to AMR/Stage 2"
assert (results["stage3_used"] == 0).all(), "Some accounts were escalated to Stage 3"
```

**Warning signs:** `results["amr_used"].sum() > 0` after force-routing to Stage 1.

### Pitfall 5: Embedder Not Normalizing in FakeEmbedder

**What goes wrong:** `FakeEmbedder.encode()` in `conftest.py` returns `rng.randn(...)` — raw normal samples, NOT normalized. When `cross_msg_sim_mean = emb @ emb.T` is computed, it gives values far outside [-1, 1], and `near_dup_frac` will be meaningless.

**Why it happens:** FEAT-04 assumes `normalize_embeddings=True` which is only set in the real `TextEmbedder`.

**How to avoid:** Normalize fake embedder output in tests, OR test FEAT-04 with a separate test embedder that returns L2-normalized vectors:
```python
class NormalizedFakeEmbedder:
    def encode(self, texts, batch_size=64):
        rng = np.random.RandomState(42)
        raw = rng.randn(len(texts), 384).astype(np.float32)
        norms = np.linalg.norm(raw, axis=1, keepdims=True)
        return raw / np.maximum(norms, 1e-8)
```

The shape/index tests can still use `FakeEmbedder` since they don't assert specific similarity values.

## Code Examples

### Cross-Message Similarity Computation (FEAT-04)

```python
# Source: derived from numpy dot product property for normalized vectors
# emb: (N_msgs, 384), already L2-normalized by TextEmbedder
if emb.shape[0] >= 2:
    sim_matrix = emb @ emb.T          # cosine sim since normalized
    n = sim_matrix.shape[0]
    mask = ~np.eye(n, dtype=bool)     # exclude diagonal
    off_diag = sim_matrix[mask]       # shape: (N*(N-1),)
    cross_msg_sim_mean = float(np.mean(off_diag))
    near_dup_frac = float(np.mean(off_diag > 0.9))
else:
    cross_msg_sim_mean = 0.0
    near_dup_frac = 0.0
```

### Force-Route Threshold Helpers (ablation.py)

```python
# Source: derived from gate_amr() and gate_stage3() logic in botdetector_pipeline.py
from botdetector_pipeline import StageThresholds

def force_route_thresholds(force_stage: str) -> StageThresholds:
    if force_stage == "stage1":
        return StageThresholds(
            s2a_human=1.0, s2a_bot=0.0,
            n2_trigger=1e9,
            disagreement_trigger=1e9,
            s12_human=1.0, s12_bot=0.0,
            novelty_force_stage3=1e9,
        )
    if force_stage == "stage2":
        return StageThresholds(
            s2a_human=0.0, s2a_bot=1.0,
            n2_trigger=-1.0,
            disagreement_trigger=-1.0,
            s12_human=1.0, s12_bot=0.0,
            novelty_force_stage3=1e9,
        )
    if force_stage == "stage3":
        return StageThresholds(
            s2a_human=0.0, s2a_bot=1.0,
            n2_trigger=-1.0,
            disagreement_trigger=-1.0,
            s12_human=0.0, s12_bot=1.0,
            novelty_force_stage3=-1.0,
        )
    return StageThresholds()
```

### Verifying Force-Route Outcome

```python
# Test that force_stage="stage1" produces zero AMR and Stage 3 usage
import copy

original_th = copy.deepcopy(system.th)
system.th = force_route_thresholds("stage1")
results = predict_system(system, S3, edges_S3, nodes_total)
system.th = original_th

assert (results["amr_used"] == 0).all()
assert (results["stage3_used"] == 0).all()
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Feature vector 391-dim | 395-dim (after Phase 5) | Phase 5 (2026-04-13) | All tests assert 395 dims; FEAT-04 extends to 397 |
| No ablation module | `ablation.py` to be created | Phase 6 | Enables Phase 7 paper tables |
| No cross-message similarity | FEAT-04 adds at indices 395, 396 | Phase 6 | 2 new features; retrain required after addition |

**Deprecated/outdated:**
- `test_feat01_default_zero` shape assertion `(1, 395)`: will need updating to `(1, 397)` after FEAT-04 is added

## Open Questions

1. **Does Phase 6 require a retrain after FEAT-04?**
   - What we know: Adding FEAT-04 changes `extract_stage2_features()` output from 395 to 397 dims. The `Stage2BaseContentModel` is trained on the 395-dim features in `trained_system_v11.joblib`.
   - What's unclear: Phase 6 success criteria do not explicitly mention retraining — success criterion 2 says features "appear in the trained feature set", implying a retrain IS required.
   - Recommendation: Plan for a retrain after FEAT-04 is coded and tested. This means Phase 6 has two sub-phases: (a) code + test FEAT-04 and ablation.py, (b) retrain on 397-dim features and produce `trained_system_v12.joblib`.

2. **Which column to evaluate for force-stage="stage1"?**
   - What we know: ABL-01 success criterion 3 says "evaluates all S3 accounts at Stage 1 only". `predict_system()` always returns `p1`, `p2`, `p12`, and `p_final`.
   - What's unclear: Whether the ablation runner should evaluate `p1` (purest Stage 1 signal) or `p_final` (combined by meta-models, but with only Stage 1 features contributing).
   - Recommendation: Use `p1` for Stage 1 ablation — evaluating `p_final` with forced routing still mixes meta-model weights trained on all stages. Document the `eval_col` parameter in `AblationConfig`.

3. **Should `ablation.py` load `trained_system_v11.joblib` from disk, or accept a `TrainedSystem` argument?**
   - What we know: Phase 7 will run multiple ablation variants. Loading from disk each time is wasteful.
   - Recommendation: `run_ablation()` accepts `system: TrainedSystem` as a parameter. The caller loads from disk once. This also makes the ablation runner testable with `minimal_system`.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | none — see existing `tests/` directory |
| Quick run command | `pytest tests/test_ablation.py tests/test_features_stage2.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FEAT-04 | `extract_stage2_features()` returns (N, 397) after FEAT-04 | unit | `pytest tests/test_features_stage2.py -x -q` | Partially (file exists, needs new tests for indices 395, 396) |
| FEAT-04 | `cross_msg_sim_mean=0.0` and `near_dup_frac=0.0` for 0- and 1-message accounts | unit | `pytest tests/test_features_stage2.py::test_feat04_default_zero -x` | Wave 0 gap |
| FEAT-04 | `cross_msg_sim_mean` matches `np.mean(off_diag)` for known messages | unit | `pytest tests/test_features_stage2.py::test_feat04_sim_mean -x` | Wave 0 gap |
| FEAT-04 | `near_dup_frac` fraction correctly counts pairs with cosine > 0.9 | unit | `pytest tests/test_features_stage2.py::test_feat04_near_dup -x` | Wave 0 gap |
| ABL-01 | `force_route_thresholds("stage1")` produces `amr_used=0, stage3_used=0` for all accounts | unit | `pytest tests/test_ablation.py::test_force_stage1_no_escalation -x` | Wave 0 gap |
| ABL-01 | `force_route_thresholds("stage2")` produces `amr_used=1` for all accounts | unit | `pytest tests/test_ablation.py::test_force_stage2_all_amr -x` | Wave 0 gap |
| ABL-01 | `run_ablation()` returns dict keyed by config name with evaluate_s3 structure | unit | `pytest tests/test_ablation.py::test_run_ablation_returns_dict -x` | Wave 0 gap |

### Sampling Rate

- **Per task commit:** `pytest tests/test_features_stage2.py tests/test_ablation.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_ablation.py` — covers ABL-01 (force-routing verification)
- [ ] `tests/test_features_stage2.py` — extend with FEAT-04 tests (indices 395, 396)
- [ ] Update shape assertion in `test_feat01_default_zero`: `(1, 395)` → `(1, 397)`

## Sources

### Primary (HIGH confidence)

- Direct codebase inspection of `features_stage2.py` — current feature vector layout, `emb` scope, embedder usage
- Direct codebase inspection of `botdetector_pipeline.py` — `gate_amr()`, `gate_stage3()`, `predict_system()` conditional logic, `StageThresholds` fields
- Direct codebase inspection of `evaluate.py` — `evaluate_s3()` return structure (`overall`, `per_stage`, `routing`)
- Direct codebase inspection of `tests/test_features_stage2.py` — confirmed 395-dim assertion, existing FEAT-01/02/03 index layout
- Direct codebase inspection of `tests/conftest.py` — `FakeEmbedder` (not normalized), `minimal_system` fixture pattern

### Secondary (MEDIUM confidence)

- numpy documentation (in-training knowledge, HIGH confidence for dot product on normalized vectors = cosine similarity)

### Tertiary (LOW confidence)

- None — all findings are grounded in direct codebase inspection

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all verified by direct code inspection; no new libraries needed
- Architecture: HIGH — `predict_system()` routing logic inspected; force-routing design derived directly from `gate_amr()` and `gate_stage3()` conditionals
- Pitfalls: HIGH — derived from direct reading of embedding normalization, test assertions, and threshold logic

**Research date:** 2026-04-15
**Valid until:** 2026-05-15 (stable codebase; no external library changes expected)
