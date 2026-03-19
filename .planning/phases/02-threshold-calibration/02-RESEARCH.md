# Phase 2: Threshold Calibration - Research

**Researched:** 2026-03-19
**Domain:** Bayesian hyperparameter optimization applied to cascade routing thresholds
**Confidence:** HIGH

---

## Summary

Phase 2 adds a `calibrate_thresholds()` function that wraps `predict_system()` inside an Optuna study, runs on S2 only (no S3 contamination), finds the `StageThresholds` values that maximize the chosen metric, and writes the result back into `TrainedSystem.th`. The core challenge is wiring an existing multi-stage inference function as a black-box objective in a way that is both data-leakage-free and exactly reproducible under SEED=42.

The dataset is small: 2,907 total accounts, S2 ~436 accounts (~285 human / ~150 bot at a 65/35 class ratio). This matters for threshold search — the objective surface is noisy, so the optimizer must be sample-efficient and the search space must be bounded sensibly. Optuna with TPESampler is the correct choice here; scikit-optimize (skopt) is explicitly NOT compatible with the project's Python 3.13 environment and must not be used.

The calibration module should be a single new file (`calibrate.py`) that imports from `botdetector_pipeline.py` without modifying it. The only change to `botdetector_pipeline.py` is a one-line update to `train_system()` or a post-training call that replaces `TrainedSystem.th` with the calibrated result (CALIB-03).

**Primary recommendation:** Use Optuna 4.8.0 with `TPESampler(seed=42)`, `n_trials=200`, sequential execution (`n_jobs=1`), and `direction="maximize"`. Wire `predict_system()` as the objective, extracting the chosen metric from sklearn.metrics after each call.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CALIB-01 | System can optimize novelty and probability routing thresholds using Bayesian optimization over the S2 split | Optuna 4.8.0 with TPESampler; `predict_system()` called on S2 data; 9 continuous threshold parameters defined with sensible bounds |
| CALIB-02 | Optimization objective is configurable (default: F1; alternatives: AUC, precision, recall) | sklearn.metrics functions dispatched by string key; passed as `metric` argument to calibrate function |
| CALIB-03 | Calibrated thresholds are persisted as part of TrainedSystem for reproducibility | Best trial's params used to construct `StageThresholds`; assigned to `trained_system.th` in-place; `TrainedSystem` already holds a `th` field |
</phase_requirements>

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| optuna | 4.8.0 | Bayesian optimization driver | Active, Python 3.13-compatible, TPESampler is sample-efficient on small budgets, native seed support |
| sklearn.metrics | (sklearn 1.6.1, already installed) | F1/AUC/precision/recall computation | Already a project dependency |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| optuna.logging | (bundled with optuna) | Suppress per-trial stdout noise | Always — set to WARNING level in calibrate.py |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| optuna | scikit-optimize (skopt 0.10.2) | skopt only declares Python <= 3.12 support (released June 2024, before Python 3.13). Known numpy compatibility fragility. Do NOT use. |
| optuna | hyperopt | Less maintained, no native study persistence, worse TPE implementation for small budgets |
| optuna | scipy.optimize | Gradient-based; thresholds are discontinuous step functions — gradient methods will fail |
| TPESampler | RandomSampler | Random search requires ~5x more trials for same quality on 9-dimensional space |
| TPESampler | CmaEsSampler | CMA-ES needs ~10x population size before it converges; overkill for 200 trials |

**Installation:**

```bash
pip install optuna==4.8.0
```

**Version verification (run before writing tasks):**

```bash
pip show optuna
# Expect: Version: 4.8.0
python -c "import optuna; print(optuna.__version__)"
```

---

## Architecture Patterns

### Recommended Project Structure

```
SocialBotDetectionSystem/
├── botdetector_pipeline.py   # EXISTING — do not modify routing logic
├── calibrate.py              # NEW — entire Phase 2 deliverable
├── main.py                   # EXISTING — call calibrate after train_system()
└── tests/
    └── test_calibrate.py     # NEW — unit tests for calibrate.py
```

### Pattern 1: Optuna Objective Closure

**What:** Wrap `predict_system()` in a closure that holds S2 data and edges, constructs a `StageThresholds` from Optuna's suggested trial values, calls inference, and returns the scalar metric.

**When to use:** Always — this is the standard Optuna pattern. The closure captures fixed data; each trial only varies thresholds.

```python
# Source: https://optuna.readthedocs.io/en/stable/faq.html (reproducibility section)
import optuna
from sklearn.metrics import f1_score, roc_auc_score, precision_score, recall_score
from botdetector_pipeline import StageThresholds, predict_system, TrainedSystem

METRIC_FNS = {
    "f1":        lambda y_true, p: f1_score(y_true, (p >= 0.5).astype(int), zero_division=0),
    "auc":       lambda y_true, p: roc_auc_score(y_true, p),
    "precision": lambda y_true, p: precision_score(y_true, (p >= 0.5).astype(int), zero_division=0),
    "recall":    lambda y_true, p: recall_score(y_true, (p >= 0.5).astype(int), zero_division=0),
}

def make_objective(system, S2, edges_S2, nodes_total, y_true, metric="f1"):
    metric_fn = METRIC_FNS[metric]

    def objective(trial):
        th = StageThresholds(
            s1_bot               = trial.suggest_float("s1_bot",               0.80, 0.999),
            s1_human             = trial.suggest_float("s1_human",             0.001, 0.20),
            n1_max_for_exit      = trial.suggest_float("n1_max_for_exit",      1.0,  6.0),
            s2a_bot              = trial.suggest_float("s2a_bot",              0.70, 0.999),
            s2a_human            = trial.suggest_float("s2a_human",            0.001, 0.30),
            n2_trigger           = trial.suggest_float("n2_trigger",           1.0,  6.0),
            disagreement_trigger = trial.suggest_float("disagreement_trigger", 1.0,  8.0),
            s12_bot              = trial.suggest_float("s12_bot",              0.70, 0.999),
            s12_human            = trial.suggest_float("s12_human",            0.001, 0.30),
            novelty_force_stage3 = trial.suggest_float("novelty_force_stage3", 1.0, 6.0),
        )
        system.th = th  # swap thresholds before inference
        result = predict_system(system, S2, edges_S2, nodes_total=nodes_total)
        p_final = result["p_final"].to_numpy()
        return metric_fn(y_true, p_final)

    return objective
```

### Pattern 2: Constraint — s1_human < s1_bot

**What:** The three "human/bot band" pairs must satisfy `human_threshold < bot_threshold`. Optuna can enforce this via a constraint or by always sampling human as a fraction of bot.

**When to use:** Required — without this guard, trials will produce logically invalid thresholds (e.g., s1_human=0.9 and s1_bot=0.8) that cause every account to route to Stage 2.

**Simplest approach:** Sample the human threshold as `trial.suggest_float("s1_human", 0.001, 0.20)` with its upper bound set below the bot lower bound `0.80`. This works because the default bounds below do not overlap.

```python
# For the s2a pair where ranges could overlap, use relative sampling:
s2a_human = trial.suggest_float("s2a_human", 0.001, 0.30)
s2a_bot   = trial.suggest_float("s2a_bot",   max(s2a_human + 0.05, 0.70), 0.999)
```

### Pattern 3: Writing Calibrated Thresholds Back to TrainedSystem

**What:** After `study.optimize()`, extract `study.best_params`, reconstruct `StageThresholds`, assign to `system.th`.

**When to use:** Always — this satisfies CALIB-03.

```python
def calibrate_thresholds(
    system: TrainedSystem,
    S2, edges_S2, nodes_total,
    metric: str = "f1",
    n_trials: int = 200,
    seed: int = 42,
) -> StageThresholds:
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    y_true = S2["label"].to_numpy()

    sampler = optuna.samplers.TPESampler(seed=seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    objective = make_objective(system, S2, edges_S2, nodes_total, y_true, metric)
    study.optimize(objective, n_trials=n_trials, n_jobs=1)  # n_jobs=1 for reproducibility

    best = study.best_params
    best_th = StageThresholds(
        s1_bot               = best["s1_bot"],
        s1_human             = best["s1_human"],
        n1_max_for_exit      = best["n1_max_for_exit"],
        s2a_bot              = best["s2a_bot"],
        s2a_human            = best["s2a_human"],
        n2_trigger           = best["n2_trigger"],
        disagreement_trigger = best["disagreement_trigger"],
        s12_bot              = best["s12_bot"],
        s12_human            = best["s12_human"],
        novelty_force_stage3 = best["novelty_force_stage3"],
    )
    system.th = best_th  # persist in-place (CALIB-03)
    return best_th
```

### Threshold Search Space — Sensible Bounds

The bounds below are derived from the existing hardcoded defaults and domain reasoning about what physically makes sense for a cascade router:

| Threshold | Default | Search Min | Search Max | Rationale |
|-----------|---------|------------|------------|-----------|
| `s1_bot` | 0.98 | 0.80 | 0.999 | Must be high-confidence for early exit |
| `s1_human` | 0.02 | 0.001 | 0.20 | Must be well below s1_bot; keeps band meaningful |
| `n1_max_for_exit` | 3.0 | 1.0 | 6.0 | Novelty values are Mahalanobis distances; >6 is very rare |
| `s2a_bot` | 0.95 | 0.70 | 0.999 | AMR gate needs less certainty than final exit |
| `s2a_human` | 0.05 | 0.001 | 0.30 | Symmetric logic; wide range to find AMR sweet spot |
| `n2_trigger` | 3.0 | 1.0 | 6.0 | Same Mahalanobis scale as n1 |
| `disagreement_trigger` | 4.0 | 1.0 | 8.0 | Logit scale; 4.0 = large disagreement |
| `s12_bot` | 0.98 | 0.70 | 0.999 | Combined meta12 threshold for Stage 3 skip |
| `s12_human` | 0.02 | 0.001 | 0.30 | Symmetric lower bound |
| `novelty_force_stage3` | 3.5 | 1.0 | 6.0 | Mahalanobis scale |

**10-dimensional search space** — all continuous float parameters.

### Anti-Patterns to Avoid

- **Passing S3 into the objective:** S3 is the held-out test set. Calibration must only touch S2. Pass `S2` and `edges_S2` explicitly; never derive from the main dataset.
- **Running with n_jobs > 1:** Breaks TPESampler seed reproducibility per Optuna documentation. Always `n_jobs=1`.
- **Modifying models inside the objective:** Only `system.th` should be swapped per trial. Do not retrain anything inside the objective function — this would be data leakage and extremely slow.
- **Using skopt on Python 3.13:** skopt 0.10.2 only declares support through Python 3.12. It is not installed and should not be installed in this environment.
- **Forgetting to suppress Optuna's verbose logging:** By default Optuna prints one line per trial. With 200 trials this creates 200 lines of stdout noise. Call `optuna.logging.set_verbosity(optuna.logging.WARNING)` at the top of `calibrate_thresholds()`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Bayesian surrogate model | Custom Gaussian Process loop | `optuna.TPESampler` | TPE handles mixed continuous/discrete spaces, does not require gradient info, is sample-efficient from trial 1 |
| Trial history tracking | Manual dict of (params → score) | `study.best_params`, `study.trials_dataframe()` | Optuna stores the full history in-memory by default |
| AUC calculation | Manual ROC integration | `sklearn.metrics.roc_auc_score` | Handles edge cases (all-one-class predictions) cleanly |
| F1 with zero predictions | Manual branch for empty prediction | `f1_score(..., zero_division=0)` | Avoids division-by-zero when a trial makes all predictions the same class |
| Reproducible seeding | Setting numpy/random seeds globally | `TPESampler(seed=42)` + `n_jobs=1` | Global seed setting interferes with pipeline model training; Optuna's sampler seed is local |

**Key insight:** The routing thresholds are discontinuous step functions — TPE's tree-based surrogate handles this correctly where gradient-based methods cannot.

---

## Common Pitfalls

### Pitfall 1: Data Leakage via S3 Contamination

**What goes wrong:** Calibration inadvertently uses S3 data (test set), inflating reported performance on evaluation.

**Why it happens:** The `system` object has already seen S1 and S2 during training. If S3 accounts are passed to the objective, the calibrated thresholds overfit to the test set.

**How to avoid:** Always pass `S2` and `edges_S2` to `calibrate_thresholds()`. The function signature should make S2 explicit. Add an assertion that the passed DataFrame index does not overlap with S3 if paranoia is warranted.

**Warning signs:** Evaluation on S3 significantly outperforms S2 calibration score (should be similar or lower, not higher).

### Pitfall 2: Objective Returns NaN (All Accounts Route Same Way)

**What goes wrong:** An extreme threshold set causes every account to exit at Stage 1 (or never exit Stage 1). Meta123 still produces a p_final, but it may be degenerate. AUC with one unique predicted probability = NaN.

**Why it happens:** e.g., s1_bot=0.80 with a well-calibrated Stage 1 means nearly all bots exit at Stage 1, so Stage 3 sees almost no traffic. Novelty thresholds at extremes can also suppress all Stage 3 routing.

**How to avoid:** In the objective, catch NaN return values and return a penalty (e.g., `0.0` or `-1.0`). Add a fallback:

```python
score = metric_fn(y_true, p_final)
if np.isnan(score):
    return 0.0
return float(score)
```

**Warning signs:** Many trials showing identical scores of 0.0 early in optimization.

### Pitfall 3: system.th Mutation Across Trials

**What goes wrong:** Because `system` is a mutable dataclass passed by reference, the objective mutates `system.th` in every trial. If trials run in any parallel context this causes race conditions.

**Why it happens:** Python passes objects by reference. `system.th = th` in the objective replaces the field each call.

**How to avoid:** The fix is `n_jobs=1` (sequential optimization). This is already required for reproducibility, so it also fixes this issue. If parallel optimization ever becomes needed in future, deep-copy `system` inside the objective before mutating `.th`.

### Pitfall 4: skopt Install Failure on Python 3.13

**What goes wrong:** `pip install scikit-optimize` either fails or silently installs a version with runtime errors (numpy `np.int` removal, etc.).

**Why it happens:** skopt 0.10.2 was released June 2024, before Python 3.13 was released. Its classifiers stop at 3.12. Internal uses of deprecated numpy APIs may fail at runtime.

**How to avoid:** Do not attempt to install skopt. Use Optuna exclusively.

### Pitfall 5: Reproducibility Failure — Same Seed, Different Results

**What goes wrong:** Re-running calibration with SEED=42 produces different best thresholds.

**Why it happens:** Three possible causes: (a) n_jobs != 1 was used; (b) a different `study_name` was created in the same in-memory storage session; (c) the objective function itself is non-deterministic (e.g., relies on random state from `predict_system`).

**How to avoid:**
- Always `n_jobs=1`
- Create a fresh `optuna.create_study()` with no persistent storage between runs (in-memory is default)
- `predict_system()` is deterministic for fixed models and thresholds — verify no randomness is introduced in any feature extraction step

**Warning signs:** `study.best_value` differs between two runs with the same seed.

### Pitfall 6: S2 Size is Small (~436 accounts)

**What goes wrong:** With ~436 samples and ~10 thresholds, the objective surface is extremely noisy. The optimizer may not converge to a meaningfully better threshold set in 200 trials for some metrics.

**Why it happens:** F1 in particular is discrete (integer TP/FP/FN counts), so small changes in thresholds cause step changes in the objective.

**How to avoid:**
- Use AUC as the default metric if F1 optimization converges poorly (AUC is smoother on small datasets)
- Set `n_trials=200` as the minimum; accept that calibration may only marginally improve over defaults on small data
- Report both the default-threshold score and the calibrated score so the gain is transparent

---

## Code Examples

### Full calibrate.py skeleton

```python
# Source: Optuna 4.8.0 docs — https://optuna.readthedocs.io/en/stable/faq.html
import numpy as np
import optuna
from sklearn.metrics import f1_score, roc_auc_score, precision_score, recall_score

from botdetector_pipeline import StageThresholds, TrainedSystem, predict_system

METRIC_FNS = {
    "f1":        lambda y, p: f1_score(y, (p >= 0.5).astype(int), zero_division=0),
    "auc":       lambda y, p: roc_auc_score(y, p),
    "precision": lambda y, p: precision_score(y, (p >= 0.5).astype(int), zero_division=0),
    "recall":    lambda y, p: recall_score(y, (p >= 0.5).astype(int), zero_division=0),
}


def calibrate_thresholds(
    system: TrainedSystem,
    S2,
    edges_S2,
    nodes_total: int,
    metric: str = "f1",
    n_trials: int = 200,
    seed: int = 42,
) -> StageThresholds:
    """
    Optimize StageThresholds on S2 using Bayesian optimization (Optuna TPESampler).
    Mutates system.th in-place and returns the best StageThresholds found.
    """
    if metric not in METRIC_FNS:
        raise ValueError(f"Unknown metric '{metric}'. Choose from: {list(METRIC_FNS)}")

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    y_true = S2["label"].to_numpy()
    metric_fn = METRIC_FNS[metric]

    def objective(trial):
        s1_human = trial.suggest_float("s1_human", 0.001, 0.20)
        s1_bot   = trial.suggest_float("s1_bot",   max(s1_human + 0.05, 0.80), 0.999)

        s2a_human = trial.suggest_float("s2a_human", 0.001, 0.30)
        s2a_bot   = trial.suggest_float("s2a_bot",   max(s2a_human + 0.05, 0.70), 0.999)

        s12_human = trial.suggest_float("s12_human", 0.001, 0.30)
        s12_bot   = trial.suggest_float("s12_bot",   max(s12_human + 0.05, 0.70), 0.999)

        system.th = StageThresholds(
            s1_bot               = s1_bot,
            s1_human             = s1_human,
            n1_max_for_exit      = trial.suggest_float("n1_max_for_exit",      1.0, 6.0),
            s2a_bot              = s2a_bot,
            s2a_human            = s2a_human,
            n2_trigger           = trial.suggest_float("n2_trigger",           1.0, 6.0),
            disagreement_trigger = trial.suggest_float("disagreement_trigger", 1.0, 8.0),
            s12_bot              = s12_bot,
            s12_human            = s12_human,
            novelty_force_stage3 = trial.suggest_float("novelty_force_stage3", 1.0, 6.0),
        )
        result = predict_system(system, S2, edges_S2, nodes_total=nodes_total)
        p_final = result["p_final"].to_numpy()
        score = metric_fn(y_true, p_final)
        return 0.0 if np.isnan(score) else float(score)

    sampler = optuna.samplers.TPESampler(seed=seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    study.optimize(objective, n_trials=n_trials, n_jobs=1)

    # Reconstruct and persist best thresholds
    best = study.best_params
    best_th = StageThresholds(
        s1_bot               = best["s1_bot"],
        s1_human             = best["s1_human"],
        n1_max_for_exit      = best["n1_max_for_exit"],
        s2a_bot              = best["s2a_bot"],
        s2a_human            = best["s2a_human"],
        n2_trigger           = best["n2_trigger"],
        disagreement_trigger = best["disagreement_trigger"],
        s12_bot              = best["s12_bot"],
        s12_human            = best["s12_human"],
        novelty_force_stage3 = best["novelty_force_stage3"],
    )
    system.th = best_th  # CALIB-03: persisted in TrainedSystem
    print(f"[calibrate] Best {metric}: {study.best_value:.4f} | trials: {n_trials}")
    print(f"[calibrate] Best thresholds: {best_th}")
    return best_th
```

### Integration in main.py (after train_system call)

```python
from calibrate import calibrate_thresholds

# After: sys = train_system(S1, S2, ...)
best_th = calibrate_thresholds(
    system=sys,
    S2=S2,
    edges_S2=edges_S2,
    nodes_total=len(users),
    metric="f1",   # or "auc", "precision", "recall"
    n_trials=200,
    seed=SEED,
)
# sys.th is now updated; predict_system() will use calibrated thresholds automatically
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Grid search over thresholds | Bayesian optimization (TPE) | ~2018 (Optuna first release) | ~10x reduction in trials needed for equivalent quality |
| skopt/hyperopt | Optuna | ~2022 (Optuna matured) | Better Python 3.x compatibility, simpler API, active maintenance |
| Fixed hardcoded thresholds | Per-dataset calibration | Project decision (this phase) | Reproducible, dataset-specific optimal routing |

**Deprecated/outdated for this project:**
- scikit-optimize: Last released June 2024, not Python 3.13 tested, history of sklearn/numpy API breakage
- hyperopt: Last meaningful update 2021; less maintained than Optuna

---

## Open Questions

1. **Will 200 trials be sufficient given S2 noise?**
   - What we know: S2 has ~436 accounts; 10-dimensional continuous space; TPE becomes effective after ~30-50 trials of random exploration
   - What's unclear: How smooth the objective surface is under the actual trained models (unknown until Phase 1 is run end-to-end)
   - Recommendation: Make `n_trials` a configurable parameter (default 200). Expose it in `calibrate_thresholds()`. Caller can increase to 500 for a publication run.

2. **Should `disagreement_trigger` be calibrated?**
   - What we know: It is in `StageThresholds` as `disagreement_trigger=4.0` (logit scale). gate_amr uses it.
   - What's unclear: Whether this logit-scale threshold is sensitive enough at S2 size to meaningfully tune
   - Recommendation: Include it in calibration. If it shows very low importance (check `study.best_params` variance across runs), it can be frozen in a follow-up.

3. **AUC vs F1 as default metric**
   - What we know: F1 is noisy on small integer counts; AUC is smoother and scale-invariant
   - What's unclear: Project preference — "default: F1" is stated in CALIB-02
   - Recommendation: Implement F1 as default per CALIB-02 spec. Document in calibrate.py that AUC is often more stable on S2-sized data and can be selected via `metric="auc"`.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | None — no pytest.ini or pyproject.toml detected; Wave 0 must create `tests/` directory |
| Quick run command | `pytest tests/test_calibrate.py -x -q` |
| Full suite command | `pytest tests/ -q` |

### Phase Requirements to Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CALIB-01 | `calibrate_thresholds()` runs without error and returns a StageThresholds with values inside the defined search bounds | unit | `pytest tests/test_calibrate.py::test_calibrate_runs -x` | Wave 0 |
| CALIB-01 | Objective metric value improves over hardcoded defaults when run on S2 (or at least does not regress) | unit | `pytest tests/test_calibrate.py::test_calibrate_improves_or_holds -x` | Wave 0 |
| CALIB-02 | `calibrate_thresholds(metric="auc")` completes and returns a valid score | unit | `pytest tests/test_calibrate.py::test_metric_switching -x` | Wave 0 |
| CALIB-02 | Invalid metric string raises `ValueError` | unit | `pytest tests/test_calibrate.py::test_invalid_metric_raises -x` | Wave 0 |
| CALIB-03 | After `calibrate_thresholds()`, `system.th` matches the returned `StageThresholds` | unit | `pytest tests/test_calibrate.py::test_th_persisted_in_system -x` | Wave 0 |
| CALIB-03 | Running `calibrate_thresholds` twice with `seed=42` produces identical `StageThresholds` values | unit | `pytest tests/test_calibrate.py::test_reproducibility -x` | Wave 0 |

**Note on test data:** Full BotSim-24 loading is slow. Tests should use a synthetic 50-account mock DataFrame (25 human, 25 bot) with dummy features to keep each test under 10 seconds. Fixture should produce a pre-trained `TrainedSystem` with minimal models (small LightGBM, 10 trees) or sklearn stubs.

### Sampling Rate

- **Per task commit:** `pytest tests/test_calibrate.py -x -q`
- **Per wave merge:** `pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/__init__.py` — empty, marks tests as package
- [ ] `tests/test_calibrate.py` — all 6 test functions listed above
- [ ] `tests/conftest.py` — shared fixture: `minimal_trained_system(tmp_path)` producing a fast-training TrainedSystem on synthetic data
- [ ] Framework install: `pip install optuna==4.8.0` — not yet installed

---

## Sources

### Primary (HIGH confidence)

- Optuna 4.8.0 official docs (FAQ — reproducibility) — https://optuna.readthedocs.io/en/stable/faq.html — TPESampler seed behavior, n_jobs=1 requirement
- Optuna PyPI index — `pip index versions optuna` — confirmed 4.8.0 available, installable on Python 3.13
- scikit-optimize PyPI — https://pypi.org/project/scikit-optimize/ — confirmed Python <= 3.12 only, last release June 4, 2024
- `botdetector_pipeline.py` (project file, read directly) — StageThresholds fields, predict_system() signature, TrainedSystem.th field
- BotSim-24 Readme (project file) — 2,907 total accounts; S2 ~436 accounts

### Secondary (MEDIUM confidence)

- Optuna GitHub issues #3526 and discussion #5245 — confirmed n_jobs!=1 breaks seed reproducibility
- scikit-optimize GitHub issue #1077 — confirmed history of sklearn/numpy API incompatibility

### Tertiary (LOW confidence)

- Rule of thumb for TPE warm-up (30-50 random trials before surrogate is useful) — from general hyperparameter optimization literature, not formally cited

---

## Metadata

**Confidence breakdown:**

- Standard stack (Optuna 4.8.0): HIGH — verified installable on Python 3.13 via `pip install --dry-run`; skopt exclusion verified via PyPI Python classifier
- Architecture (objective closure pattern): HIGH — directly from Optuna official docs and FAQ
- Search bounds: MEDIUM — derived from existing hardcoded defaults and domain reasoning; actual useful ranges depend on trained model behavior
- Pitfalls: HIGH (leakage, mutation, reproducibility) / MEDIUM (convergence on small data)

**Research date:** 2026-03-19
**Valid until:** 2026-06-19 (90 days; Optuna releases frequently but API is stable; re-verify if Python or numpy version changes)
