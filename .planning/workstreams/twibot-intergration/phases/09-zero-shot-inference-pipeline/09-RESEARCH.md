# Phase 9: Zero-Shot Inference Pipeline - Research

**Researched:** 2026-04-16
**Domain:** Python inference pipeline integration, DataFrame schema adaptation, numerical stability
**Confidence:** HIGH

---

## Summary

Phase 9 delivers a single new file, `evaluate_twibot20.py`, that adapts the TwiBot-20
DataFrame produced by Phase 8's `twibot20_io.py` into the BotSim-24 pipeline schema and
runs `predict_system()` from `botdetector_pipeline.py` zero-shot (no retraining). The
cascade (Stage 1 → 2a → 2b → 3) is invoked unchanged; the only domain-specific logic is
a column adapter and a `np.clip` call on the Stage 1 ratio columns immediately after
`extract_stage1_matrix()` returns.

The central technical risk is the schema gap between what `load_accounts()` returns and
what `predict_system()` requires. `load_accounts()` outputs 8 columns
(`node_idx`, `screen_name`, `statuses_count`, `followers_count`, `friends_count`,
`created_at`, `messages`, `label`). `predict_system()` requires at minimum
`account_id`, `node_idx`, `username`, `submission_num`, `comment_num_1`,
`comment_num_2`, `subreddit_list`, `messages`. The adapter inside
`evaluate_twibot20.py` bridges this gap entirely — no existing file is modified.

The second risk is numerical: when `comment_num_1`, `comment_num_2`, and `subreddit_list`
are zero-filled, the ratio features at columns 6–9 of `extract_stage1_matrix()` output
reach `post_num / eps` (up to ~5e7 for prolific users). Without clamping, these values
drive Stage 1 novelty scores into extreme territory, causing routing collapse. The fix is
a single `np.clip` call after `extract_stage1_matrix()` — already specified in D-04.

**Primary recommendation:** Implement `evaluate_twibot20.py` as a module with
`run_inference(path, model_path) -> pd.DataFrame` plus a `__main__` block. Use the
column adapter pattern from the conftest synthetic DataFrame to understand what
`predict_system()` requires, then populate the missing columns from TwiBot-20 data per
D-02/D-03/D-07.

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** `evaluate_twibot20.py` is structured as module + `__main__`: a
  `run_inference(path: str, model_path: str) -> pd.DataFrame` function that Phase 10
  can import directly, plus a `if __name__ == "__main__":` block for manual execution.
  No subprocess needed between phases.
- **D-02:** `statuses_count` maps to `submission_num`. This is the closest available
  analog (tweet count ≈ post-activity proxy). Stage 1 ratio clamping (D-04) handles
  the side-effects.
- **D-03:** Reddit-specific columns that have no TwiBot-20 equivalent are zero-filled:
  - `comment_num_1` = 0.0
  - `comment_num_2` = 0.0
  - `subreddit_list` = [] (empty list)
  - `username` = `screen_name` (direct mapping)
  - `account_id` = `ID` field (Twitter user ID string, e.g. `"12345"`)
- **D-04:** After calling `extract_stage1_matrix(df)`, clamp columns 6–9 (inclusive)
  of the resulting `X1` matrix to `[0.0, 50.0]` using
  `X1[:, 6:10] = np.clip(X1[:, 6:10], 0.0, 50.0)`. Done inside `evaluate_twibot20.py`
  only — not in `features_stage1.py`.
- **D-05:** `run_inference()` returns the full results `pd.DataFrame` with columns:
  `account_id`, `p1`, `n1`, `p2`, `n2`, `amr_used`, `p12`, `stage3_used`, `p3`,
  `n3`, `p_final`.
- **D-06:** The `__main__` block saves results to `results_twibot20.json`
  (records-oriented). Phase 10 imports `run_inference()` directly.
- **D-07:** Use `record["ID"]` (Twitter user ID string) as `account_id` in the
  adapter. This requires reading the raw JSON a second time, OR having `load_accounts()`
  include the `ID` field. Since `load_accounts()` does NOT include `ID`, the adapter
  must recover it by reading `test.json` again or by calling `load_accounts()` and
  then building the `account_id` column from the same JSON.
- **D-08:** All TwiBot-20 messages have `ts: None`. Temporal features will naturally
  be zero. No special handling needed. Document in docstring.

### Claude's Discretion

- Threshold value passed to `predict_system()` — use `sys.th` (the calibrated
  threshold from the loaded model artifact). No override needed.
- Whether to print a brief summary after saving JSON — print is fine for human
  verification.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TW-04 | User can run zero-shot inference on TwiBot-20 test accounts via `evaluate_twibot20.py` using `trained_system_v12.joblib` unchanged — no retraining, full cascade runs as-is | `predict_system()` is a drop-in function (lines 634–710 of `botdetector_pipeline.py`); `joblib.load()` returns a `TrainedSystem` dataclass with all fitted models; the adapter DataFrame is the only required work |
| TW-05 | TwiBot-20 inference path clamps Stage 1 ratio features (columns 6–9 of `extract_stage1_matrix` output) to [0.0, 50.0], preventing cascade routing collapse from divide-by-zero on zero-filled Reddit-specific columns | `extract_stage1_matrix()` already applies `eps=1e-6` and `nan_to_num` but does NOT clamp; ratio values of `post_num / eps` can reach ~5e7 for active users; `np.clip(X1[:, 6:10], 0.0, 50.0)` immediately after the call is the correct, isolated fix |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Data loading (TwiBot-20 JSON) | `twibot20_io` (Phase 8) | — | Already implemented; `load_accounts()`, `build_edges()`, `validate()` are all available |
| Column adapter (TwiBot-20 → pipeline schema) | `evaluate_twibot20.py` (inline) | — | Adapter is not reusable outside this script; keeping it inline avoids polluting `twibot20_io.py` per D-01 |
| Stage 1 ratio clamping | `evaluate_twibot20.py` (local np.clip) | — | Must NOT touch `features_stage1.py`; isolation is a hard requirement (TW-05, D-04) |
| Full cascade inference | `botdetector_pipeline.predict_system()` | — | Drop-in; no changes |
| Model loading | `evaluate_twibot20.py` via `joblib.load()` | — | Same pattern as `main.py` lines 155–160 |
| Results serialization | `evaluate_twibot20.py __main__` block | — | JSON output for audit; `run_inference()` returns DataFrame for Phase 10 import |

---

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| numpy | (project-pinned) | `np.clip` for ratio clamping; array operations | Already in project deps |
| pandas | (project-pinned) | DataFrame construction for adapter | Already in project deps |
| joblib | (project-pinned) | `joblib.load("trained_system_v12.joblib")` | Same pattern as `main.py` |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json (stdlib) | stdlib | Saving `results_twibot20.json` (records-oriented) | `__main__` block only |
| sys (stdlib) | stdlib | `sys.argv` for `__main__` argument parsing | `__main__` block only |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `json.dump` for output | `pd.DataFrame.to_json` | Either works; `to_json(orient="records")` is simpler one-liner and consistent with how evaluate_s3 data moves |

---

## Architecture Patterns

### System Architecture Diagram

```
test.json
    |
    v
twibot20_io.load_accounts(path)
    --> accounts_df [node_idx, screen_name, statuses_count, followers_count,
                     friends_count, created_at, messages, label]
    |
    v
twibot20_io.build_edges(accounts_df, path)
    --> edges_df [src, dst, etype, weight]
    |
    v
twibot20_io.validate(accounts_df, edges_df)   -- prints diagnostic fractions
    |
    v
Column Adapter (inline in evaluate_twibot20.py)
    - account_id  <- record["ID"]  (re-read JSON or carry from load step)
    - username    <- screen_name
    - submission_num <- statuses_count
    - comment_num_1  = 0.0
    - comment_num_2  = 0.0
    - subreddit_list = []
    --> df [all columns predict_system() needs]
    |
    v
features_stage1.extract_stage1_matrix(df)
    --> X1: np.ndarray shape (n, 10)
    |
    v
np.clip(X1[:, 6:10], 0.0, 50.0)   [TW-05 — TwiBot-20 path only]
    |
    v
botdetector_pipeline.predict_system(sys, df, edges_df, nodes_total)
    [Internally calls extract_stage1_matrix again — see PITFALL 1]
    --> results_df [account_id, p1, n1, p2, n2, amr_used, p12,
                    stage3_used, p3, n3, p_final]
    |
    v
run_inference() returns results_df
    |
    v
__main__: results_twibot20.json  (records-oriented)
          print summary
```

### Recommended Project Structure
```
evaluate_twibot20.py        # New file — this phase's only deliverable
tests/
└── test_evaluate_twibot20.py   # New test file
```

### Pattern 1: Column Adapter

**What:** Build the pipeline-schema DataFrame from `load_accounts()` output plus zero-fills and ID mapping.

**When to use:** Once, inside `run_inference()` before calling `predict_system()`.

```python
# Source: CONTEXT.md D-02/D-03/D-07 + verified against botdetector_pipeline.py line 702
# and conftest.py _make_synthetic_dataframe() schema

import json
import numpy as np
import pandas as pd

def _build_adapter_df(accounts_df: pd.DataFrame, path: str) -> pd.DataFrame:
    """Map TwiBot-20 accounts_df to BotSim-24 pipeline schema."""
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    account_ids = [r["ID"] for r in raw]

    df = accounts_df.copy()
    df["account_id"] = account_ids                           # D-07
    df["username"] = df["screen_name"]                       # D-03
    df["submission_num"] = df["statuses_count"].astype(float)  # D-02
    df["comment_num_1"] = 0.0                                # D-03
    df["comment_num_2"] = 0.0                                # D-03
    df["subreddit_list"] = [[] for _ in range(len(df))]      # D-03
    return df
```

**Key insight:** `predict_system()` at line 702 calls `df["account_id"].astype(str).values` — this column MUST be present. `extract_stage1_matrix()` at lines 10–37 requires `username`, `submission_num`, `comment_num_1`, `comment_num_2`, `subreddit_list`. `build_graph_features_nodeidx()` at line 367 requires `node_idx`. All other columns (`screen_name`, `statuses_count`, etc.) are not read by the pipeline functions and can remain.

### Pattern 2: Stage 1 Ratio Clamping

**What:** Clamp columns 6–9 of the `extract_stage1_matrix()` output before passing control to `predict_system()`.

**When to use:** Immediately after `extract_stage1_matrix(df)` in the TwiBot-20 path.

```python
# Source: CONTEXT.md D-04, verified against features_stage1.py lines 19-37
from features_stage1 import extract_stage1_matrix

X1 = extract_stage1_matrix(df)
X1[:, 6:10] = np.clip(X1[:, 6:10], 0.0, 50.0)  # TW-05: clamp post_c1/c2/ct/sr
```

**CRITICAL PITFALL:** `predict_system()` internally calls `extract_stage1_matrix(df)` again (line 647). The pre-call `X1` you clip is NOT used by `predict_system()`. This means the clamping above does nothing unless you patch around `predict_system()`.

See **Pitfall 1** below for the resolution.

### Pattern 3: Model Loading

**What:** Load `trained_system_v12.joblib` into a `TrainedSystem` dataclass.

**When to use:** Once at the start of `run_inference()`.

```python
# Source: main.py lines 155-160, verified against botdetector_pipeline.py TrainedSystem dataclass
import joblib
from botdetector_pipeline import TrainedSystem

sys_loaded: TrainedSystem = joblib.load(model_path)
# sys_loaded.th  -> StageThresholds (calibrated)
# sys_loaded.embedder -> TextEmbedder (sentence-transformers MiniLM)
```

### Pattern 4: run_inference() Structure

**What:** Public function signature for Phase 10 import compatibility.

```python
# Source: CONTEXT.md D-01, D-05, D-06

def run_inference(path: str, model_path: str = "trained_system_v12.joblib") -> pd.DataFrame:
    """
    Run zero-shot inference on TwiBot-20 test accounts.

    Note: All temporal features (cv_intervals, rate, delta_mean, delta_std,
    hour_entropy) are zero for all TwiBot-20 accounts because tweets are
    plain strings with no per-tweet timestamps (ts=None). This is expected
    and documented, not an error.

    Args:
        path:       Path to TwiBot-20 test.json
        model_path: Path to joblib model artifact (default: trained_system_v12.joblib)

    Returns:
        pd.DataFrame with columns: account_id, p1, n1, p2, n2, amr_used,
        p12, stage3_used, p3, n3, p_final
    """
    ...
```

### Anti-Patterns to Avoid

- **Modifying `features_stage1.py`:** Forbidden by D-04 and v1.2 isolation constraint. The clamp is TwiBot-20-specific and must not affect BotSim-24 inference.
- **Modifying `botdetector_pipeline.py`:** Forbidden by v1.2 isolation constraint.
- **Calling `extract_stage1_matrix()` before `predict_system()` and expecting it to affect the prediction:** `predict_system()` calls `extract_stage1_matrix()` internally. Any pre-call result is discarded. See Pitfall 1 for the correct implementation strategy.
- **Omitting `account_id` from the adapter DataFrame:** `predict_system()` reads `df["account_id"]` at line 702 and will raise `KeyError` if missing.
- **Using `node_idx` as `account_id`:** Loses the stable Twitter user ID string. D-07 requires `record["ID"]`.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Inference cascade | Custom Stage 1/2/3 calls | `predict_system(sys, df, edges_df, nodes_total)` | Already handles AMR gate, meta12, Stage 3 gate, meta123, output schema |
| Temporal feature zeroing | `if ts is None: skip` logic | Nothing — `extract_stage2_features` already guards at line 49 | The existing guard `if m.get("ts") is not None: ts.append(...)` produces empty `ts` list, which naturally yields zero temporal features at lines 93, 97, 117 |
| Edge graph construction | Manual adjacency dict | `twibot20_io.build_edges()` | Already implemented and tested in Phase 8 |
| Schema validation | Custom column checkers | `twibot20_io.validate()` | Already prints diagnostics and asserts bounds |

---

## Common Pitfalls

### Pitfall 1: Pre-Clipping X1 Has No Effect on predict_system()

**What goes wrong:** Developer calls `X1 = extract_stage1_matrix(df)`, clips `X1[:, 6:10]`, then calls `predict_system()`. The clip has no effect because `predict_system()` calls `extract_stage1_matrix(df)` internally (line 647) and produces a fresh unclamped `X1`.

**Why it happens:** `predict_system()` is a self-contained function that re-derives all features from the DataFrame. There is no way to inject a pre-computed `X1` into it.

**How to avoid:** Two valid approaches (planner should choose one):

**Option A — Monkey-patch `extract_stage1_matrix` in `botdetector_pipeline`:**
```python
import botdetector_pipeline as bp
from features_stage1 import extract_stage1_matrix as _orig_s1

def _clamped_s1(df, *args, **kwargs):
    X = _orig_s1(df)
    X[:, 6:10] = np.clip(X[:, 6:10], 0.0, 50.0)
    return X

bp.extract_stage1_matrix = _clamped_s1
results = predict_system(sys_loaded, df, edges_df, nodes_total=len(df))
# Restore afterwards if needed (or scope with contextmanager)
bp.extract_stage1_matrix = _orig_s1
```

**Option B — Implement a thin `predict_system_twibot20()` wrapper that duplicates `predict_system()` internals with the clamp inserted:**
This violates the spirit of "no changes to existing pipeline files" because it requires copying private logic. Not recommended.

**Option C — Add a `clamp_s1` parameter to `predict_system()`:**
Forbidden — changes an existing pipeline file.

**Recommended:** Option A (monkey-patch). It is the cleanest, isolated, and reversible approach. The conftest already uses this pattern successfully (lines 159–172 in `tests/conftest.py`). It does not modify any file.

**Warning signs:** If `predict_system()` does not numerically error but produces suspiciously high novelty scores or near-100% Stage 3 routing rates on TwiBot-20, the clamp likely was not applied.

### Pitfall 2: account_id Column Missing from load_accounts() Output

**What goes wrong:** `predict_system()` raises `KeyError: 'account_id'` because `twibot20_io.load_accounts()` does not include this column (confirmed by reading `twibot20_io.py`).

**Why it happens:** Phase 8 used `screen_name` and `node_idx` as primary identifiers. BotSim-24 uses `account_id` (a string Reddit user ID). They serve the same role but with different column names.

**How to avoid:** The column adapter must explicitly set `df["account_id"] = [r["ID"] for r in raw_json]`. The `ID` field is a Twitter user ID string matching D-07.

**Warning signs:** `KeyError: 'account_id'` at `botdetector_pipeline.py` line 702.

### Pitfall 3: nodes_total Must Be len(accounts_df), Not Hardcoded

**What goes wrong:** `build_graph_features_nodeidx()` allocates arrays of size `nodes_total` (line 375–376). If `nodes_total < max(node_idx)`, array index out-of-bounds errors occur.

**Why it happens:** TwiBot-20 test.json has ~11,826 accounts. `node_idx` values are 0-indexed by row enumeration (Phase 8 D-04), so `max(node_idx) = len(accounts_df) - 1`. `nodes_total = len(accounts_df)` is correct.

**How to avoid:** Always pass `nodes_total=len(accounts_df)`.

**Warning signs:** `IndexError` inside `build_graph_features_nodeidx()`.

### Pitfall 4: JSON Re-Read for account_id Alignment

**What goes wrong:** Developer re-reads `test.json` to extract `["ID"]` values but uses a different iteration order than `load_accounts()`, causing `account_id` to be misaligned with the DataFrame rows.

**Why it happens:** Both `load_accounts()` and the adapter iterate over `data = json.load(f)` in the same order (JSON array order), so alignment is preserved. However, if the developer filters records in one place but not the other, misalignment occurs.

**How to avoid:** The adapter reads `test.json` once and extracts `[r["ID"] for r in raw]` without filtering. `load_accounts()` also does not filter (all records are loaded). Alignment is guaranteed by array index correspondence.

### Pitfall 5: results_twibot20.json Serialization of NumPy Types

**What goes wrong:** `json.dump(results_df.to_dict(orient="records"))` raises `TypeError` on `numpy.float32` / `numpy.int32` values.

**Why it happens:** Python's `json` module does not serialize NumPy scalar types by default.

**How to avoid:** Use `results_df.to_json("results_twibot20.json", orient="records", indent=2)` (pandas handles NumPy type coercion internally) OR convert with `.to_dict(orient="records")` after casting to Python native types.

---

## Code Examples

### Full run_inference() Skeleton

```python
# Source: CONTEXT.md D-01 through D-08, verified against botdetector_pipeline.py

import json
import sys

import joblib
import numpy as np
import pandas as pd

from twibot20_io import load_accounts, build_edges, validate
from features_stage1 import extract_stage1_matrix as _orig_extract_stage1_matrix
import botdetector_pipeline as bp
from botdetector_pipeline import predict_system, TrainedSystem


def run_inference(path: str, model_path: str = "trained_system_v12.joblib") -> pd.DataFrame:
    """
    Run zero-shot inference on TwiBot-20 test accounts.

    Temporal features (cv_intervals, rate, delta_mean, delta_std, hour_entropy)
    are zero for all accounts — tweets are plain strings with no per-tweet timestamps.
    This is expected behavior, not an error.

    Args:
        path:       Path to TwiBot-20 test.json
        model_path: Path to joblib model artifact

    Returns:
        pd.DataFrame: columns account_id, p1, n1, p2, n2, amr_used, p12,
                      stage3_used, p3, n3, p_final
    """
    # 1. Load data (Phase 8)
    accounts_df = load_accounts(path)
    edges_df = build_edges(accounts_df, path)
    validate(accounts_df, edges_df)

    # 2. Load model
    sys_loaded: TrainedSystem = joblib.load(model_path)

    # 3. Column adapter (TwiBot-20 -> pipeline schema)
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)
    df = accounts_df.copy()
    df["account_id"]    = [r["ID"] for r in raw]      # D-07
    df["username"]      = df["screen_name"]             # D-03
    df["submission_num"]= df["statuses_count"].astype(float)  # D-02
    df["comment_num_1"] = 0.0                           # D-03
    df["comment_num_2"] = 0.0                           # D-03
    df["subreddit_list"]= [[] for _ in range(len(df))]  # D-03

    # 4. Stage 1 ratio clamping via monkey-patch (TW-05, D-04)
    #    Must patch bp.extract_stage1_matrix because predict_system() calls it internally.
    def _clamped_s1(df_inner, *args, **kwargs):
        X = _orig_extract_stage1_matrix(df_inner)
        X[:, 6:10] = np.clip(X[:, 6:10], 0.0, 50.0)  # clamp post_c1/c2/ct/sr
        return X

    bp.extract_stage1_matrix = _clamped_s1
    try:
        results = predict_system(sys_loaded, df, edges_df, nodes_total=len(df))
    finally:
        bp.extract_stage1_matrix = _orig_extract_stage1_matrix  # always restore

    return results


if __name__ == "__main__":
    data_path  = sys.argv[1] if len(sys.argv) > 1 else "test.json"
    model_path = sys.argv[2] if len(sys.argv) > 2 else "trained_system_v12.joblib"

    results = run_inference(data_path, model_path)
    out_path = "results_twibot20.json"
    results.to_json(out_path, orient="records", indent=2)
    print(f"[twibot20] Saved {len(results)} results to {out_path}")
    print(f"[twibot20] Stage 3 used: {results['stage3_used'].mean():.3f}")
    print(f"[twibot20] AMR used:     {results['amr_used'].mean():.3f}")
    print(f"[twibot20] p_final mean: {results['p_final'].mean():.4f}")
```

---

## Runtime State Inventory

Step 2.5: SKIPPED. This is a greenfield file creation phase, not a rename/refactor/migration. No runtime state items to inventory.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| `trained_system_v12.joblib` | `run_inference()` | To verify | — | If missing, `main.py` must be run first to produce it |
| `test.json` | `load_accounts()` | To verify | — | Human must provide dataset |
| `twibot20_io.py` | `load_accounts`, `build_edges`, `validate` | Yes (Phase 8 complete) | — | — |
| `botdetector_pipeline.py` | `predict_system()` | Yes | — | — |
| `features_stage1.py` | `extract_stage1_matrix()` | Yes | — | — |
| `features_stage2.py` | `extract_stage2_features()` | Yes | — | — |
| numpy | array operations, `np.clip` | Yes (project dep) | — | — |
| pandas | DataFrame construction | Yes (project dep) | — | — |
| joblib | model loading | Yes (project dep) | — | — |

**Missing dependencies with no fallback:**
- `trained_system_v12.joblib` — must exist before running `evaluate_twibot20.py`. Main plan task must verify existence or note that `main.py` produces it.
- `test.json` — TwiBot-20 dataset file; not in repo, must be provided by human.

**Missing dependencies with fallback:**
- None among code dependencies.

---

## Validation Architecture

`nyquist_validation` is enabled in `.planning/config.json`.

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 (confirmed from conftest pyc filename) |
| Config file | none explicitly — uses default discovery |
| Quick run command | `python -m pytest tests/test_evaluate_twibot20.py -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TW-04 | `run_inference()` returns a DataFrame with 11 expected columns | unit (synthetic) | `pytest tests/test_evaluate_twibot20.py::test_run_inference_returns_correct_schema -x` | No — Wave 0 |
| TW-04 | `run_inference()` runs without errors on synthetic TwiBot-20 data | unit (synthetic) | `pytest tests/test_evaluate_twibot20.py::test_run_inference_end_to_end -x` | No — Wave 0 |
| TW-04 | `__main__` block saves `results_twibot20.json` as records-oriented JSON | unit | `pytest tests/test_evaluate_twibot20.py::test_main_block_saves_json -x` | No — Wave 0 |
| TW-05 | Stage 1 ratio columns 6–9 are clamped to [0.0, 50.0] in TwiBot-20 path | unit | `pytest tests/test_evaluate_twibot20.py::test_ratio_clamping_applied -x` | No — Wave 0 |
| TW-05 | BotSim-24 path (`extract_stage1_matrix` directly) is NOT clamped | unit | `pytest tests/test_evaluate_twibot20.py::test_botsim_path_not_clamped -x` | No — Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_evaluate_twibot20.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green (currently 61 tests pass) before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_evaluate_twibot20.py` — covers TW-04, TW-05 (all 5 tests above)
  - Needs a synthetic test fixture that mimics TwiBot-20 JSON structure (4–5 accounts)
  - Needs `minimal_system` fixture from `conftest.py` for model (already available)
  - For clamping test: create accounts with very high `statuses_count` (e.g., 100000) and zero comment/subreddit columns; verify that the `X1[:, 6:10]` values inside `predict_system()` are bounded at 50.0 (requires capturing via mock or inspecting output for absence of NaN/Inf)

*(No gaps in existing test infrastructure for other tests — 61 tests already pass.)*

---

## Key Implementation Insight: Monkey-Patch is the Established Pattern

The codebase already uses monkey-patching as the standard approach for intercepting `extract_stage1_matrix` inside `predict_system()`. The `tests/conftest.py` fixture `minimal_system` does exactly this at lines 159–173:

```python
def patched_extract_stage1_matrix(df, *args, **kwargs):
    return extract_stage1_matrix(df)

monkeypatch.setattr(bp, "extract_stage1_matrix", patched_extract_stage1_matrix)
```

The Phase 9 implementation uses the same pattern — wrapping the original function to insert the `np.clip` call — and restores the original via a `finally` block (since `run_inference()` is not a test and does not have `monkeypatch`). This is idiomatic, safe, and isolated to the TwiBot-20 code path.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `trained_system_v12.joblib` exists on the target machine (produced by `main.py`) | Environment Availability | `run_inference()` raises `FileNotFoundError`; plan task must add existence check or prerequisite step |
| A2 | TwiBot-20 `test.json` is available locally at user-provided path | Environment Availability | Script cannot run; must be documented in `__main__` help text |
| A3 | `bp.extract_stage1_matrix` is the name used by `predict_system()` (confirmed at line 14 of `botdetector_pipeline.py`: `from features_stage1 import extract_stage1_matrix`) | Pitfall 1, Code Examples | Monkey-patch would not intercept — but this is VERIFIED by reading `botdetector_pipeline.py` lines 1–16 |

**A3 is VERIFIED** — `botdetector_pipeline.py` line 14 shows `from features_stage1 import extract_stage1_matrix` (module-level import into `bp` namespace), so `bp.extract_stage1_matrix = _clamped_s1` will intercept the call at line 647. Confidence: HIGH.

---

## Open Questions

1. **Does `trained_system_v12.joblib` already exist on the developer machine?**
   - What we know: `main.py` lines 159–160 produce it as the last step of training
   - What's unclear: Whether training has been run since Phase 5 leakage fix
   - Recommendation: Plan task 1 should verify existence of the artifact; if missing, document that `python main.py` must be run first (out of this phase's scope)

2. **Does the embedder inside `trained_system_v12.joblib` load cleanly on the target machine?**
   - What we know: The `TextEmbedder` class wraps `sentence-transformers` / MiniLM (384-dim output confirmed from conftest line 52)
   - What's unclear: Whether `sentence-transformers` is installed and the model cached locally
   - Recommendation: Document as a known prerequisite; the test suite uses `FakeEmbedder` to avoid this dependency, so the risk is runtime-only

---

## Sources

### Primary (HIGH confidence)
- `botdetector_pipeline.py` lines 634–710 — `predict_system()` full implementation, column requirements, output schema — [VERIFIED: direct read]
- `botdetector_pipeline.py` lines 361–403 — `build_graph_features_nodeidx()` implementation — [VERIFIED: direct read]
- `features_stage1.py` lines 1–40 — `extract_stage1_matrix()` full implementation, ratio columns 6–9 confirmed as `post_c1`, `post_c2`, `post_ct`, `post_sr` — [VERIFIED: direct read]
- `features_stage2.py` lines 27–124 — `extract_stage2_features()`, `ts=None` guard at line 49 — [VERIFIED: direct read]
- `twibot20_io.py` — `load_accounts()`, `build_edges()`, `validate()` implementations, confirmed Phase 8 complete — [VERIFIED: direct read]
- `tests/conftest.py` lines 155–173 — monkey-patch pattern for `extract_stage1_matrix` in tests — [VERIFIED: direct read]
- `botsim24_io.py` lines 100–184 — `build_account_table()`, confirmed `account_id` column requirement and BotSim-24 schema — [VERIFIED: direct read]
- `.planning/workstreams/twibot-intergration/phases/09-zero-shot-inference-pipeline/09-CONTEXT.md` — locked decisions D-01 through D-08 — [VERIFIED: direct read]
- `.planning/workstreams/twibot-intergration/REQUIREMENTS.md` — TW-04, TW-05 — [VERIFIED: direct read]
- Phase 8 summaries (08-01-SUMMARY.md, 08-02-SUMMARY.md) — Phase 8 complete, 13 tests pass — [VERIFIED: direct read]

### Secondary (MEDIUM confidence)
- None — all claims verified from direct codebase reads.

### Tertiary (LOW confidence)
- None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — all dependencies are existing project libraries, confirmed present
- Architecture: HIGH — all integration points verified by direct code reading
- Pitfalls: HIGH — Pitfall 1 (critical) confirmed by reading `predict_system()` internals; monkey-patch pattern confirmed from conftest
- Test strategy: HIGH — existing test infrastructure understood, Wave 0 gaps are additive only

**Research date:** 2026-04-16
**Valid until:** Until `botdetector_pipeline.py` or `features_stage1.py` are modified (stable)
