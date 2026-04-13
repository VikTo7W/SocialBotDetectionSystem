# Phase 5: Leakage Fix and Baseline Retrain - Research

**Researched:** 2026-04-13
**Domain:** Feature leakage removal, behavioral feature engineering, ML cascade retrain
**Confidence:** HIGH

## Summary

Phase 5 makes three coordinated surgical changes to the pipeline, then retrains everything from scratch. The two identity leakage paths in Stage 2a (username/profile text appended to the embedding pool in `features_stage2.py`, and `text_field="profile"` in the AMR extractor in `botdetector_pipeline.py`) inflate AUC to 97–100% by encoding bot-discriminating identity strings directly into content embeddings. Fixing both paths in a single atomic commit, then adding three behavioral features (CoV of inter-post intervals, character length stats, posting hour entropy), and dropping `character_setting` at load time completes the scope.

The retrain is a full cascade retrain: Stage 1 is unaffected by feature changes but must be rerun because the split/seed must stay consistent. Stage 2a retrains on clean features (expected AUC drop to 70–85%). The AMR refiner, meta12, and meta123 all trained on leaky Stage 2a logits during v1.0 and must be fully retrained — not just Stage 2a. The v1.0 artifact (`trained_system.joblib`) must be preserved; the v1.1 artifact saves to `trained_system_v11.joblib`.

Before any code changes, `results_v10.json` must be written capturing exact v1.0 S3 metrics for Phase 7's leakage audit table.

**Primary recommendation:** Fix all three leakage/column issues atomically in one commit, add all three FEAT-01/02/03 features in the same commit, then run a single full retrain — do not retrain incrementally between individual fixes.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Leakage fix approach:**
- Fix both leakage paths + drop `character_setting` + add FEAT-01/02/03 in a single commit, then do one retrain run
- Do not verify each fix in isolation — atomic fix per the research note in STATE.md (residual leakage risk if fixed separately)

**AMR anchor text (replacing text_field="profile"):**
- Use the most recent message in the account's post/comment history as the anchor text (last item in the messages list, consistent with the `messages[-max_msgs:]` slicing in `extract_stage2_features`)
- Truncate to `max_chars` characters (same limit as `extract_stage2_features`, currently 500)
- For accounts with no messages: return a zero embedding vector (consistent with how `extract_stage2_features` handles empty accounts)
- `text_field="profile"` call site in `botdetector_pipeline.py` line 539 must be removed entirely — no fallback to any identity field

**New behavioral features (FEAT-01, FEAT-02, FEAT-03):**
- Placement: Append after the existing temporal features `[rate, delta_mean, delta_std]` — do not replace them
- Final temporal block: `[rate, delta_mean, delta_std, cv_intervals, char_len_mean, char_len_std, hour_entropy]`
- FEAT-01 (CoV of inter-post intervals): `cv = delta_std / max(delta_mean, 1e-6)` — default to `0.0` for accounts with 0 or 1 messages (undefined intervals)
- FEAT-02 (character length stats): mean and std of message character lengths across all messages — default both to `0.0` for accounts with no messages
- FEAT-03 (posting hour entropy): `entropy = -sum(p * log2(p))` over the 24-hour distribution — default to `0.0` for accounts with 0 or 1 messages (entropy trivially 0 for one message)
- Entropy uses timestamps already collected in `ts` list; extract hour via `datetime.utcfromtimestamp(ts_val).hour`

**character_setting column handling:**
- Drop `character_setting` at load time inside `build_account_table` in `botsim24_io.py` — not retained in the returned DataFrame at all
- Add an assertion after `build_account_table` returns to verify `"character_setting" not in df.columns`

**Post-retrain validation:**
- Minimum validation: Stage 2a AUC < 90% (from S3 evaluation) + assertion that `character_setting` is absent from the DataFrame produced by `build_account_table`
- Full cascade (meta12, meta123, recalibrated thresholds) must train end-to-end and serialize to `trained_system_v11.joblib` without error

**Artifact preservation and versioning:**
- The existing `trained_system.joblib` (v1.0 artifact) must not be overwritten — leave it in place
- The v1.1 retrain saves to `trained_system_v11.joblib` (new file)
- Before any code changes: run evaluation on the existing `trained_system.joblib` and save results to `results_v10.json` — this captures exact v1.0 S3 metrics (F1, AUC, precision, recall) for Phase 7's leakage audit table
- `results_v10.json` format: `{"auc": float, "f1": float, "precision": float, "recall": float, "stage": "S3"}`

### Claude's Discretion
- Exact implementation of `datetime.utcfromtimestamp` import and hour extraction
- Whether to add `results_v10.json` to `.gitignore` or commit it
- Internal structure of the evaluation script/function used to capture v1.0 metrics

### Deferred Ideas (OUT OF SCOPE)
- None — discussion stayed within phase scope
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| LEAK-01 | Developer can run Stage 2a evaluation and see AUC below 90% (confirming leakage removed) | Removing `texts.append("USERNAME: " + username)` and `texts.append("PROFILE: " + profile)` from `features_stage2.py` lines 50–53 eliminates the primary leakage. After retrain on clean features, Stage 2a AUC on behavioral content alone is expected to fall to the 70–85% range. |
| LEAK-02 | `extract_stage2_features` embeds message texts only (no username, no profile text) | Lines 50–53 of `features_stage2.py` append identity strings to `texts` after message texts. These two conditionals must be deleted entirely. The `username` and `profile` variables can remain (they are read from `r.get()`) but must not be appended to `texts`. |
| LEAK-03 | AMR extractor uses representative message text instead of profile field | `extract_amr_embeddings_for_accounts()` currently reads `r.get(text_field)` where `text_field="profile"`. The function signature must drop the `text_field` parameter and instead read the most recent message text from `r.get("messages")`. Zero-vector fallback for accounts with no messages. Both call sites (lines 539 and 567 in `botdetector_pipeline.py`) plus the `predict_system` call site (line 651) must be updated. |
| LEAK-04 | `character_setting` column is dropped at load time in `build_account_table` | Line 183 of `botsim24_io.py` adds `"character_setting": u.get("character_setting", None)` to each row dict. This key must be removed from the dict literal. The assertion `assert "character_setting" not in df.columns` goes in `main.py` after the `build_account_table()` call. |
| LEAK-05 | Full system retrains cleanly with recalibrated thresholds after feature changes | `train_system()` (lines 505–614 of `botdetector_pipeline.py`) must run end-to-end, `calibrate_thresholds()` must complete, and `joblib.dump(sys, "trained_system_v11.joblib")` must succeed. Feature vector dimension changes from 391 to 394 (adding cv_intervals, char_len_mean, char_len_std, hour_entropy = 4 new scalars; removing no existing scalars but shrinking embedding pool for accounts with no messages — note: probe_dim stays 384). |
| FEAT-01 | Stage 2a includes coefficient of variation of inter-post intervals | Computed after the existing `delta_mean`/`delta_std` block in `extract_stage2_features`. Uses the already-collected `ts` list. Formula: `cv = delta_std / max(delta_mean, 1e-6)`. Default `0.0` when `len(ts) < 2`. |
| FEAT-02 | Stage 2a includes message character length distribution stats (mean, std) | Iterate over `messages` to collect `len(m.get("text") or "")` per message. `char_len_mean = np.mean(lengths)`, `char_len_std = np.std(lengths)`. Both default to `0.0` when `len(messages) == 0`. |
| FEAT-03 | Stage 2a includes entropy of posting hour-of-day distribution | Extract hour bucket per timestamp via `datetime.utcfromtimestamp(ts_val).hour`. Build 24-bin count histogram, convert to probability distribution, compute Shannon entropy in bits: `entropy = -sum(p * log2(p))`. Default `0.0` for `len(ts) <= 1`. |
</phase_requirements>

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | existing | Array ops, feature vector construction, histogram | Already used throughout; `np.histogram`, `np.log2` cover FEAT-03 |
| datetime (stdlib) | stdlib | UTC timestamp to hour conversion | Already imported in `botsim24_io.py`; needed in `features_stage2.py` |
| joblib | existing | Serialize/deserialize trained system | `trained_system_v11.joblib` save |
| sklearn.metrics | existing | AUC, F1, precision, recall for v1.0 capture | `roc_auc_score` already used in `evaluate.py` |
| json (stdlib) | stdlib | Write `results_v10.json` | Standard; no new dependency |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sentence-transformers | existing | Text embeddings (MiniLM-L6) | AMR anchor text embedding; already loaded by `TextEmbedder` |
| pytest | existing | Unit tests for leakage fix and new features | Wave 0 test scaffolding |

**No new dependencies required.** All functionality needed for Phase 5 is available in libraries already present in the project.

## Architecture Patterns

### Change Targets and Their Locations

```
features_stage2.py
├── Lines 50–53: DELETE username/profile append block (LEAK-02)
├── Lines 74–83: existing temporal block (keep as-is)
├── Line 84: extend temporal array with 4 new scalars (FEAT-01, FEAT-02, FEAT-03)
└── Add: from datetime import datetime  (for hour extraction)

botdetector_pipeline.py
├── Lines 131–150: extract_amr_embeddings_for_accounts()
│   ├── Remove text_field parameter from signature
│   └── Replace r.get(text_field) with most-recent-message logic
├── Line 539: remove text_field="profile" argument
├── Line 567: remove text_field="profile" argument
└── Line 651: remove text_field="profile" argument (predict_system)

botsim24_io.py
└── Line 183: remove "character_setting" key from rows.append dict

main.py
├── After build_account_table() call: add assertion
├── Before any code changes: v1.0 metrics capture block
└── End of script: joblib.dump(sys, "trained_system_v11.joblib")
```

### Pattern 1: Atomic Leakage Fix in features_stage2.py

**What:** Remove the two identity-leakage lines while preserving message text embedding.
**When to use:** This is a targeted deletion — no new logic, just removal.

```python
# BEFORE (lines 50–53 to be deleted):
if username:
    texts.append("USERNAME: " + username)
if profile:
    texts.append("PROFILE: " + profile)

# AFTER: those four lines simply do not exist.
# The username/profile variables are still read (they exist in r) but never used.
# The for-loop over messages above them is unchanged.
```

### Pattern 2: AMR Anchor from Most Recent Message

**What:** Replace profile-field lookup with most-recent-message text, zero-vector fallback for empty accounts.
**When to use:** `extract_amr_embeddings_for_accounts()` — replace body, remove `text_field` param.

```python
def extract_amr_embeddings_for_accounts(
    df: pd.DataFrame,
    cfg: FeatureConfig,
    embedder: TextEmbedder,
) -> np.ndarray:
    """
    AMR anchor is the most recent message text (last item in messages list
    after messages[-max_msgs:] slicing performed upstream). Accounts with
    no messages receive a zero embedding vector.
    """
    max_chars = cfg.max_chars_per_message if cfg is not None else 500
    amr_texts = []
    zero_mask = []

    for _, r in df.iterrows():
        messages = r.get("messages") or []
        if messages:
            # Most recent = last in the list (already sorted temporally by build_account_table)
            anchor = str(messages[-1].get("text") or "")[:max_chars].strip()
            amr_texts.append(amr_linearize_stub(anchor) if anchor else "")
            zero_mask.append(not bool(anchor))
        else:
            amr_texts.append("")
            zero_mask.append(True)

    # Encode all texts; replace zero-mask rows with actual zeros
    emb = embedder.encode(amr_texts).astype(np.float32)
    for i, is_zero in enumerate(zero_mask):
        if is_zero:
            emb[i] = np.zeros(emb.shape[1], dtype=np.float32)
    return emb
```

Note: `cfg` may be `None` (main.py passes `cfg=None`). Guard with `if cfg is not None else 500`.

### Pattern 3: Three New Behavioral Features in extract_stage2_features

**What:** Extend temporal block from 3 to 7 scalars: add cv_intervals, char_len_mean, char_len_std, hour_entropy.
**When to use:** Inside `extract_stage2_features()`, after the existing temporal computation block.

```python
# Add import at module top:
from datetime import datetime

# Inside the per-account loop, after the existing temporal block:

# FEAT-01: CoV of inter-post intervals
if len(ts) >= 2:
    cv_intervals = float(delta_std / max(delta_mean, 1e-6))
else:
    cv_intervals = 0.0

# FEAT-02: Character length stats
if len(messages) > 0:
    char_lens = [len(m.get("text") or "") for m in messages]
    char_len_mean = float(np.mean(char_lens))
    char_len_std = float(np.std(char_lens))
else:
    char_len_mean, char_len_std = 0.0, 0.0

# FEAT-03: Posting hour entropy (Shannon, bits)
if len(ts) >= 2:
    hours = [datetime.utcfromtimestamp(t).hour for t in ts]
    counts = np.bincount(hours, minlength=24).astype(np.float64)
    probs = counts / counts.sum()
    # Shannon entropy in bits; ignore zero-probability bins
    nonzero = probs[probs > 0]
    hour_entropy = float(-np.sum(nonzero * np.log2(nonzero)))
else:
    hour_entropy = 0.0

temporal = np.array(
    [rate, delta_mean, delta_std, cv_intervals, char_len_mean, char_len_std, hour_entropy],
    dtype=np.float32,
)
```

### Pattern 4: Drop character_setting in botsim24_io.py

**What:** Remove one key from the `rows.append({...})` dict in `build_account_table`.
**When to use:** Surgical deletion — no logic change.

```python
# BEFORE (line 182–183):
# Keep character_setting for analysis only, not features (README: can't be used)
"character_setting": u.get("character_setting", None),

# AFTER: both lines deleted. The returned DataFrame will not contain the column.
```

### Pattern 5: Assertion in main.py After build_account_table

```python
accounts = build_account_table(users, upc)
assert "character_setting" not in accounts.columns, (
    "character_setting must not appear in account table — it's a target leak"
)
```

### Pattern 6: v1.0 Metrics Capture in main.py (Before Code Changes)

This is a one-time operation — capture before any feature code changes are made.

```python
import json

# Load v1.0 trained system (do NOT retrain)
sys_v10 = joblib.load("trained_system.joblib")
out_v10 = predict_system(sys_v10, df=S3, edges_df=edges_S3, nodes_total=len(users))
y_true = S3["label"].to_numpy()

from evaluate import evaluate_s3
report_v10 = evaluate_s3(out_v10, y_true)

results_v10 = {
    "auc":       report_v10["per_stage"]["p2"]["auc"],   # Stage 2a AUC
    "f1":        report_v10["overall"]["f1"],
    "precision": report_v10["overall"]["precision"],
    "recall":    report_v10["overall"]["recall"],
    "stage":     "S3",
}
with open("results_v10.json", "w") as f:
    json.dump(results_v10, f, indent=2)
```

Note: The CONTEXT.md specifies S3 metrics. The `evaluate_s3` report returns `per_stage["p2"]["auc"]` for Stage 2a AUC specifically. Cross-check whether "auc" in the JSON refers to overall (p_final) or Stage 2a — the CONTEXT.md says `"stage": "S3"` and lists the four metrics without specifying which AUC column. Use `overall["auc"]` for the top-level `"auc"` key (p_final AUC on S3), consistent with the format spec.

### Pattern 7: Save v1.1 Artifact in main.py

```python
# After full retrain + calibration:
joblib.dump(sys, "trained_system_v11.joblib")
print("[main] Saved v1.1 TrainedSystem to trained_system_v11.joblib")
```

The existing line `joblib.dump(sys, "trained_system.joblib")` on the final line of main.py must NOT be changed. Add a new line alongside it saving to `trained_system_v11.joblib`. Both files coexist.

### Anti-Patterns to Avoid

- **Partial leakage fix:** Fixing only `features_stage2.py` without fixing the AMR `text_field="profile"` call sites — AMR logit refinement would still encode profile identity, leaving residual leakage in the retrained system.
- **Retrain after each individual fix:** Produces intermediate retrained artifacts where some leakage is present; wastes time and risks confusing artifact versions.
- **Overwriting trained_system.joblib:** The v1.0 artifact is required for Phase 7's leakage audit table. If overwritten, Phase 7 cannot compute the before/after comparison.
- **Adding character_setting assertion inside botsim24_io.py:** The assertion belongs in main.py (the integration point), not inside the I/O module — keeps I/O functions pure and testable.
- **Using `datetime.now()` for hour extraction:** Must use `datetime.utcfromtimestamp(ts_val).hour` — the `ts` values are Unix UTC timestamps; local timezone conversion would corrupt the hour distribution.
- **Using natural log for entropy:** Must use `np.log2` for Shannon entropy in bits, consistent with the CONTEXT.md formula. `np.log` (natural) would produce nats — a different scale.
- **Zero-dividing CoV when delta_mean is tiny:** Use `max(delta_mean, 1e-6)` as the denominator guard, matching the `eps=1e-6` pattern already used in `features_stage1.py`.
- **Not guarding cfg=None in AMR function:** `main.py` passes `cfg=None` to `train_system`. The AMR function receives `cfg` — guard `max_chars = cfg.max_chars_per_message if cfg is not None else 500`.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Hour-of-day histogram | Custom loop with dict accumulation | `np.bincount(hours, minlength=24)` | Simpler, vectorized, handles missing hours correctly |
| Shannon entropy | Manual log loop | `-np.sum(probs * np.log2(probs))` (mask zeros) | NumPy vectorized; avoids log(0) by pre-filtering |
| Serialization of trained system | Custom pickle protocol | `joblib.dump` / `joblib.load` | Already established in project; handles large numpy arrays efficiently |
| AUC computation | Manual ROC calculation | `sklearn.metrics.roc_auc_score` | Already used in `evaluate.py`; no new code needed |
| JSON metrics file | YAML / CSV | `json.dump` with `indent=2` | Spec explicitly defines JSON format with specific keys |

**Key insight:** All required operations are available in numpy stdlib or already-imported sklearn. This phase is surgical code removal + small extensions, not new subsystems.

## Common Pitfalls

### Pitfall 1: Missing the Third AMR Call Site in predict_system

**What goes wrong:** The CONTEXT.md canonical refs list lines 539 and 567 in `train_system()`. A planner might miss that `predict_system()` also calls `extract_amr_embeddings_for_accounts()` at line 651 with `text_field="profile"`.
**Why it happens:** `train_system` and `predict_system` are separate functions; the call sites are far apart in the file.
**How to avoid:** Search for all occurrences of `text_field` in `botdetector_pipeline.py` — there are three, not two. Line 651 is inside `predict_system`, which runs on S3.
**Warning signs:** If `predict_system` raises `TypeError: extract_amr_embeddings_for_accounts() got an unexpected keyword argument 'text_field'` at inference time, a call site was missed.

### Pitfall 2: Feature Vector Dimension Change Breaks Existing Tests

**What goes wrong:** `conftest.py`'s `_make_synthetic_dataframe` builds accounts with messages that have valid `ts` and `text` fields. After adding 4 new scalars to `temporal`, the output of `extract_stage2_features` grows from shape `(n, 391)` to `(n, 395)` — but `FakeEmbedder` returns fixed 384-dim vectors. The computation is: 384 (embedding) + 4 (linguistic) + 7 (temporal, was 3) = 395. Existing model `fit()` calls in conftest use the pre-fix feature matrix shape. Tests that call `predict_system` via `minimal_system` fixture will fail at `stage2a.predict()` because the fitted model has 391 input features but receives 395.
**Why it happens:** Sklearn models store the number of features during `fit()` and validate at `predict()`.
**How to avoid:** The `conftest.py` `minimal_system` fixture must be updated to include the 4 new temporal fields. Since messages in the fixture have valid `ts` values (`1700000000 + j * 3600`), FEAT-01 and FEAT-03 will produce nonzero values; FEAT-02 will compute char_len stats from `"sample message text {j} for account {i}"`. The fixture's `_make_synthetic_dataframe` is correct — it just needs the feature extraction to be re-run after the code change.
**Warning signs:** `sklearn ValueError: X has N features, but model is expecting M features`.

### Pitfall 3: character_setting Assertion Placement

**What goes wrong:** Adding the assertion inside `build_account_table` rather than in `main.py` breaks the function's unit testability — any test that calls `build_account_table` and provides data with `character_setting` would fail.
**Why it happens:** It feels natural to put the guard where the data is created.
**How to avoid:** The assertion goes in `main.py` after the return from `build_account_table`, per CONTEXT.md decision.

### Pitfall 4: Zero Embedding vs Empty texts List in AMR Function

**What goes wrong:** If `amr_texts` contains an empty string `""` for accounts with no messages, the embedder encodes an empty string. `SentenceTransformer.encode([""])` returns a valid (non-zero) normalized vector. The CONTEXT.md specifies a zero embedding for no-message accounts.
**Why it happens:** Empty string is not the same as "no content" to SentenceTransformer.
**How to avoid:** After `embedder.encode(amr_texts)`, apply the `zero_mask` to overwrite rows where the account had no valid message text.

### Pitfall 5: results_v10.json Requires the OLD Code Path

**What goes wrong:** If `results_v10.json` capture runs after code changes are committed, the "v1.0" metrics will actually be from the v1.1 code path.
**Why it happens:** The capture logic lives in main.py alongside the retrain — a developer might run the whole script once thinking the load/save is correct.
**How to avoid:** The v1.0 capture is a separate, isolated operation. It loads `trained_system.joblib` (unchanged artifact) and calls `predict_system` with the OLD feature extraction code. The capture must be run (or saved to file) before any feature code changes are committed. The planner should structure this as Wave 0: capture v1.0 metrics first, commit `results_v10.json`, then proceed with code changes.

### Pitfall 6: ts Collected Before username/profile Removal

**What goes wrong:** In the current `extract_stage2_features`, `ts` is collected inside the message loop (before the deleted username/profile lines). The feature additions (FEAT-01, FEAT-03) use `ts`. This ordering is correct — no reordering needed. But if someone restructures the loop incorrectly, FEAT-03 might compute entropy from timestamps that include the username/profile entries (which have no timestamps, so they'd never be in `ts`). Structural confusion can arise during editing.
**How to avoid:** Confirm that `ts` is only appended from `m.get("ts")` inside the message loop (line 47–48), which is before the deleted username/profile block. After deletion, the loop and `ts` collection are unchanged.

## Code Examples

### Verified — Existing temporal block to extend (features_stage2.py lines 74–86)

```python
# Source: features_stage2.py (read directly)
# temporal stats
if len(ts) >= 2:
    ts_sorted = np.sort(np.array(ts, dtype=np.float64))
    deltas = np.diff(ts_sorted)
    span = max(ts_sorted[-1] - ts_sorted[0], 1.0)
    rate = len(ts_sorted) / span
    delta_mean = float(np.mean(deltas))
    delta_std = float(np.std(deltas))
else:
    rate, delta_mean, delta_std = 0.0, 0.0, 0.0

temporal = np.array([rate, delta_mean, delta_std], dtype=np.float32)
```

After the fix, this block gains 4 more lines computing cv_intervals, char_len_mean, char_len_std, hour_entropy, then the `temporal = np.array([...7 items...], dtype=np.float32)` line replaces the current 3-item version.

### Verified — Existing eps pattern (features_stage1.py line ~21)

```python
# Source: features_stage1.py (read directly)
eps = 1e-6
post_c1 = post_num / (c1 + eps)
```

FEAT-01 uses the same `1e-6` denominator guard: `cv = delta_std / max(delta_mean, 1e-6)`.

### Verified — Existing zero-vector fallback (features_stage2.py lines 62–64)

```python
# Source: features_stage2.py (read directly)
if probe_dim is None:
    probe_dim = 384
emb_pool = np.zeros(probe_dim, dtype=np.float32)
```

AMR function zero fallback for no-message accounts uses same pattern: `np.zeros(emb.shape[1], dtype=np.float32)`.

### Verified — Existing evaluate_s3 return structure (evaluate.py lines 115–119)

```python
# Source: evaluate.py (read directly)
return {
    "overall":   overall,    # {"f1", "auc", "precision", "recall"}
    "per_stage": per_stage,  # {"p1", "p2", "p12", "p_final"} each with same 4 keys
    "routing":   routing,
}
```

For `results_v10.json`: use `report["overall"]["auc"]` (p_final AUC) for the top-level `"auc"` key, consistent with "stage": "S3" semantics.

### Verified — datetime already imported in botsim24_io.py (line 7)

```python
# Source: botsim24_io.py line 7 (read directly)
from datetime import datetime, timezone
```

`features_stage2.py` currently has no datetime import. Add `from datetime import datetime` at the top of `features_stage2.py` for FEAT-03's `datetime.utcfromtimestamp(ts_val).hour` call.

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Profile/username in embedding pool | Message texts only | Phase 5 | AUC drops from ~97% to expected 70–85% — realistic for behavioral content features alone |
| `text_field="profile"` AMR anchor | Most recent message text | Phase 5 | AMR refiner now learns from actual content, not identity-correlated profile text |
| `character_setting` in DataFrame | Dropped at load time | Phase 5 | Eliminates silent path for target leakage into downstream features |
| 3-scalar temporal block | 7-scalar temporal block | Phase 5 | FEAT-01/02/03 add meaningful behavioral signals for regular/irregular bot patterns |

**Deprecated/outdated after Phase 5:**
- `text_field` parameter in `extract_amr_embeddings_for_accounts` — parameter removed entirely, no fallback
- `character_setting` column in account DataFrame — never present post-fix
- `trained_system.joblib` as the current production artifact — superseded by `trained_system_v11.joblib` for v1.1 work

## Open Questions

1. **Whether results_v10.json should capture p2 AUC or overall AUC as the "auc" key**
   - What we know: CONTEXT.md format spec is `{"auc": float, "f1": float, "precision": float, "recall": float, "stage": "S3"}` — no further disambiguation
   - What's unclear: Phase 7's leakage audit table will compare "before" vs "after" Stage 2a AUC specifically — the leakage is in Stage 2a, so `per_stage["p2"]["auc"]` is the directly relevant metric
   - Recommendation: Save BOTH — `"auc_overall": overall["auc"]` and `"auc_stage2a": per_stage["p2"]["auc"]` in `results_v10.json`. This satisfies the spec and provides the Stage 2a comparison Phase 7 needs. Claude's discretion permits this extension.

2. **Handling of cfg=None in AMR function**
   - What we know: `main.py` passes `cfg=None` to `train_system()` (line 101: `cfg=None`). `train_system()` passes `cfg` to `extract_amr_embeddings_for_accounts()`.
   - What's unclear: The CONTEXT.md says `max_chars` (currently 500) — is it safe to hardcode 500 as the fallback?
   - Recommendation: Hardcode `max_chars = cfg.max_chars_per_message if cfg is not None else 500` in the AMR function. 500 matches the `max_chars` default in `extract_stage2_features` signature, ensuring consistency.

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (confirmed — tests/ directory, conftest.py, test_*.py files exist) |
| Config file | none detected (no pytest.ini or pyproject.toml with pytest config) |
| Quick run command | `pytest tests/test_features_stage2.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| LEAK-02 | `extract_stage2_features` output is independent of username/profile values | unit | `pytest tests/test_features_stage2.py::test_no_identity_in_embeddings -x` | Wave 0 |
| LEAK-03 | AMR extractor returns zero vector for no-message accounts | unit | `pytest tests/test_features_stage2.py::test_amr_zero_for_no_messages -x` | Wave 0 |
| LEAK-03 | AMR extractor does not read profile field | unit | `pytest tests/test_features_stage2.py::test_amr_uses_message_not_profile -x` | Wave 0 |
| LEAK-04 | `build_account_table` returns DataFrame without character_setting column | unit | `pytest tests/test_botsim24_io.py::test_no_character_setting_in_table -x` | Wave 0 |
| LEAK-01 | Stage 2a AUC < 90% after retrain | integration/manual | Run `main.py` and check printed AUC — not automatable without real data | manual-only — requires BotSim-24 data |
| LEAK-05 | Full cascade trains end-to-end, serializes to trained_system_v11.joblib | integration/manual | Run `main.py` — requires real data and sentence-transformers | manual-only — requires BotSim-24 data |
| FEAT-01 | cv_intervals is 0.0 for 0 or 1 message accounts | unit | `pytest tests/test_features_stage2.py::test_feat01_default_zero -x` | Wave 0 |
| FEAT-01 | cv_intervals is delta_std/max(delta_mean, 1e-6) for multi-message accounts | unit | `pytest tests/test_features_stage2.py::test_feat01_formula -x` | Wave 0 |
| FEAT-02 | char_len_mean and char_len_std are 0.0 for no-message accounts | unit | `pytest tests/test_features_stage2.py::test_feat02_default_zero -x` | Wave 0 |
| FEAT-02 | char_len stats correct for known messages | unit | `pytest tests/test_features_stage2.py::test_feat02_values -x` | Wave 0 |
| FEAT-03 | hour_entropy is 0.0 for 0 or 1 timestamp | unit | `pytest tests/test_features_stage2.py::test_feat03_default_zero -x` | Wave 0 |
| FEAT-03 | hour_entropy uses UTC hours from timestamps | unit | `pytest tests/test_features_stage2.py::test_feat03_entropy_value -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_features_stage2.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_features_stage2.py` — covers LEAK-02, LEAK-03, FEAT-01, FEAT-02, FEAT-03 (does not exist; must be created)
- [ ] `tests/test_botsim24_io.py` — covers LEAK-04 (does not exist; must be created)
- [ ] `conftest.py` update — `_make_synthetic_dataframe` and `minimal_system` fixture must account for the new 7-scalar temporal block (feature dimension changes from 391 to 395); existing fixture will break if not updated before integration tests run

Note: LEAK-01 and LEAK-05 require real BotSim-24 data (`Users.csv`, `user_post_comment.json`, edge `.pt` files). They are validated by running `main.py` and checking output, not by automated pytest. The AUC < 90% check for LEAK-01 is verified by reading the printed evaluation report from `main.py`.

## Sources

### Primary (HIGH confidence)
- `features_stage2.py` — read directly; lines 29–89 contain both leakage paths and temporal block
- `botdetector_pipeline.py` — read directly; lines 131–151 (AMR function), 539, 567, 651 (call sites)
- `botsim24_io.py` — read directly; lines 100–187 (`build_account_table` with character_setting at line 183)
- `main.py` — read directly; full orchestration, current artifact save pattern
- `evaluate.py` — read directly; `evaluate_s3` return structure for v1.0 metrics capture
- `tests/conftest.py` — read directly; `minimal_system` fixture, `FakeEmbedder`, `_make_synthetic_dataframe`
- `features_stage1.py` — read directly; `eps=1e-6` pattern confirmed
- `.planning/phases/05-leakage-fix-and-baseline-retrain/05-CONTEXT.md` — primary spec source
- `.planning/REQUIREMENTS.md` — LEAK-01 through FEAT-03 definitions

### Secondary (MEDIUM confidence)
- Shannon entropy formula in bits: standard information theory — `H = -sum(p * log2(p))`, verified against project's own `entropy_from_p` utility in `botdetector_pipeline.py` (which uses natural log for the binary case; Phase 5's hour entropy uses log2 per spec)

### Tertiary (LOW confidence)
- Expected AUC range 70–85% after leakage fix — stated in CONTEXT.md and STATE.md based on prior research; not independently verified (depends on actual BotSim-24 data)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all libraries are pre-existing; no new installs
- Architecture: HIGH — all change targets identified with exact line numbers from source reads
- Pitfalls: HIGH — identified from direct source code inspection, not speculation
- Expected AUC range: MEDIUM — stated in project context, not independently measured

**Research date:** 2026-04-13
**Valid until:** Stable — this is internal codebase research; valid until source files change
