# Phase 9: Sliding-Window Online Threshold Recalibration - Pattern Map

**Mapped:** 2026-04-17
**Files analyzed:** 2 (1 modified, 1 new test)
**Analogs found:** 2 / 2

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `evaluate_twibot20.py` (`run_inference` modification) | service | batch + transform | `evaluate_twibot20.py` current (self-analog, chunking wraps existing call) | exact |
| `tests/test_evaluate_twibot20.py` (new tests appended) | test | request-response | `tests/test_evaluate_twibot20.py` existing tests (TW-04/TW-05 pattern) | exact |

---

## Pattern Assignments

### `evaluate_twibot20.py` — `run_inference()` modification

**Analog:** `evaluate_twibot20.py` lines 35–133 (existing function, plus `calibrate.py` for `dataclasses.replace` on `StageThresholds`)

---

#### Imports pattern — current top of file (lines 11–24)

```python
from __future__ import annotations

import json
import sys

import joblib
import numpy as np
import pandas as pd

import botdetector_pipeline as bp
from botdetector_pipeline import TrainedSystem, predict_system
from evaluate import evaluate_s3
from features_stage1 import extract_stage1_matrix as _orig_extract_stage1_matrix
from twibot20_io import _detect_encoding, build_edges, load_accounts, parse_tweet_types, validate
```

**Phase 9 addition:** add `import dataclasses` and `import copy` (or use `dataclasses` only — `dataclasses.replace` is sufficient) after the stdlib imports.

---

#### Existing function signature pattern (line 35–38)

```python
def run_inference(
    path: str,
    model_path: str = "trained_system_v12.joblib",
) -> pd.DataFrame:
```

**Phase 9 new signature** — extend with two optional parameters:

```python
def run_inference(
    path: str,
    model_path: str = "trained_system_v12.joblib",
    online_calibration: bool = True,
    window_size: int = 100,
) -> pd.DataFrame:
```

The external call sites in `evaluate_twibot20()` (line 142) and `__main__` (line 153) pass only positional args — they continue to work unchanged because the new params have defaults (D-02, D-06).

---

#### Core monkey-patch + try/finally pattern (lines 125–133)

This is the single most important pattern to preserve and extend. Phase 9 moves `predict_system()` calls inside a chunking loop but keeps the `bp.extract_stage1_matrix` monkey-patch wrapping the **entire** loop — not just a single inner call.

```python
bp.extract_stage1_matrix = _clamped_s1
try:
    results = predict_system(
        sys_loaded, df, edges_df, nodes_total=len(accounts_df)
    )
finally:
    bp.extract_stage1_matrix = _orig_extract_stage1_matrix
```

**Phase 9 transformed version** — the `try/finally` block expands to contain the chunking loop:

```python
bp.extract_stage1_matrix = _clamped_s1
try:
    # --- sliding-window calibration loop replaces single predict_system call ---
    if not online_calibration:
        chunk_results = [predict_system(sys_loaded, df, edges_df, nodes_total=len(accounts_df))]
    else:
        import dataclasses
        current_th = dataclasses.replace(sys_loaded.th)   # D-07: immutable original
        novelty_buffer = []
        chunk_results = []
        indices = list(range(0, len(df), window_size))
        for start in indices:
            chunk_df = df.iloc[start:start + window_size].reset_index(drop=True)
            chunk_edges = edges_df  # edge_df is graph-global; pass full each time
            # Apply current thresholds by temporary swap (restored in finally)
            sys_loaded.th = current_th
            chunk_out = predict_system(sys_loaded, chunk_df, chunk_edges, nodes_total=len(accounts_df))
            chunk_results.append(chunk_out)
            # Accumulate n1 and n2 into buffer
            novelty_buffer.extend(chunk_out["n1"].tolist())
            novelty_buffer.extend(chunk_out["n2"].tolist())
            # Update thresholds only after first full window (D-08 cold-start)
            if len(novelty_buffer) >= window_size * 2:   # n1+n2 doubles entries
                p = np.percentile(novelty_buffer, 75)    # D-04: percentile P=75
                current_th = dataclasses.replace(
                    current_th,
                    n1_max_for_exit=p,
                    n2_trigger=p,
                    novelty_force_stage3=p,
                )
                print(f"[cal] window updated thresholds: n1_max={p:.3f} n2_trigger={p:.3f} novelty_force_stage3={p:.3f}")
        sys_loaded.th = dataclasses.replace(sys_loaded.th)  # restore to original
    results = pd.concat(chunk_results, ignore_index=True)
finally:
    bp.extract_stage1_matrix = _orig_extract_stage1_matrix
```

**NOTE for planner:** The exact buffer sizing strategy (separate n1/n2 buffers vs. combined `max(n1,n2)` per account) and the exact percentile default are implementation details — see D-04/D-05 in CONTEXT.md. The pattern above uses a combined flat list; the planner may choose to keep separate lists if per-dimension percentiles are preferred.

---

#### `dataclasses.replace` pattern for `StageThresholds` — from `calibrate.py` lines 340–351

The existing codebase already reconstructs `StageThresholds` field-by-field in `calibrate.py`:

```python
best_th = StageThresholds(
    s1_bot=best["s1_bot"],
    s1_human=best["s1_human"],
    n1_max_for_exit=best["n1_max_for_exit"],
    s2a_bot=best["s2a_bot"],
    s2a_human=best["s2a_human"],
    n2_trigger=best["n2_trigger"],
    disagreement_trigger=best["disagreement_trigger"],
    s12_bot=best["s12_bot"],
    s12_human=best["s12_human"],
    novelty_force_stage3=best["novelty_force_stage3"],
)
system.th = best_th
```

Phase 9 uses `dataclasses.replace()` instead of full reconstruction, which is cleaner for partial field updates (only the three novelty fields change — D-03). Copy from `botdetector_pipeline.py` line 3 for the import: `from dataclasses import dataclass` → Phase 9 needs `import dataclasses` (stdlib) at the top of `evaluate_twibot20.py`.

---

#### `StageThresholds` field reference — `botdetector_pipeline.py` lines 224–239

The three novelty thresholds targeted by D-03 are:

```python
@dataclass
class StageThresholds:
    # Stage 1 early exits
    s1_bot: float = 0.98
    s1_human: float = 0.02
    n1_max_for_exit: float = 3.0        # <-- D-03 target 1

    # Stage 2 AMR gate
    s2a_bot: float = 0.95
    s2a_human: float = 0.05
    n2_trigger: float = 3.0             # <-- D-03 target 2
    disagreement_trigger: float = 4.0

    # Stage 12 -> Stage 3 routing
    s12_bot: float = 0.98
    s12_human: float = 0.02
    novelty_force_stage3: float = 3.5   # <-- D-03 target 3
```

Only these three field names are passed to `dataclasses.replace()`. The six probability thresholds and `disagreement_trigger` are untouched.

---

#### `predict_system` output columns used for buffer — `botdetector_pipeline.py` lines 910–922

```python
return pd.DataFrame({
    "account_id": df["account_id"].astype(str).values,
    "p1": out1["p1"],
    "n1": out1["n1"],          # Stage 1 Mahalanobis — always populated
    "p2": p2,
    "n2": out2["n2"],          # Stage 2a Mahalanobis — always populated
    "amr_used": amr_mask.astype(int),
    "p12": p12,
    "stage3_used": stage3_mask.astype(int),
    "p3": p3,
    "n3": n3,                  # sparse (zero for accounts not routed to Stage 3)
    "p_final": p_final,
})
```

Buffer reads `chunk_out["n1"]` and `chunk_out["n2"]` (always populated). Do not use `n3` (sparse — zero for unrouted accounts would distort percentile).

---

#### `pd.concat` result assembly pattern — from `calibrate.py` (result DataFrame convention)

Phase 9 must assemble chunk results with:

```python
results = pd.concat(chunk_results, ignore_index=True)
```

`ignore_index=True` resets row indices so the returned DataFrame has a clean 0..N-1 integer index, matching what the existing single-call path returns. Column order is preserved automatically because each chunk produces identical schema from `predict_system()`.

---

### `tests/test_evaluate_twibot20.py` — new Phase 9 tests appended

**Analog:** `tests/test_evaluate_twibot20.py` existing tests (lines 107–663) — same file, append new test functions.

---

#### Test structure pattern (lines 107–131) — `test_run_inference_returns_correct_schema`

All existing tests follow this pattern: use `minimal_system` fixture, create synthetic data via `_make_twibot_json` / `_make_twibot_df` / `_make_twibot_edges`, patch the four I/O functions with `unittest.mock.patch`, call `run_inference()`, assert on result.

```python
def test_run_inference_returns_correct_schema(minimal_system, tmp_path):
    sys_obj, _, _, _ = minimal_system
    path = _make_twibot_json(tmp_path, n=5)
    df = _make_twibot_df(n=5)
    edges = _make_twibot_edges(n=5)

    from unittest.mock import patch, MagicMock

    with patch("evaluate_twibot20.load_accounts", return_value=df), \
         patch("evaluate_twibot20.build_edges", return_value=edges), \
         patch("evaluate_twibot20.validate", return_value=None), \
         patch("evaluate_twibot20.joblib.load", return_value=sys_obj):

        result = run_inference(path, "fake_model.joblib")

    # assertions follow
```

Phase 9 tests must use the same four-patch pattern and the same `minimal_system` fixture. The new optional parameters `online_calibration` and `window_size` are passed explicitly to distinguish the calibration code paths.

---

#### Spy pattern for inspecting intermediate state (lines 466–481)

When a test needs to verify threshold values passed to `predict_system`, it uses the spy/capture pattern already established:

```python
captured_df = {}

def _spy_predict(sys_loaded, df_inner, edges_df, **kwargs):
    captured_df["df"] = df_inner.copy()
    from botdetector_pipeline import predict_system as _real_predict
    return _real_predict(sys_loaded, df_inner, edges_df, **kwargs)

with patch("evaluate_twibot20.predict_system", side_effect=_spy_predict):
    run_inference(path, "fake_model.joblib")
```

Phase 9 tests that verify threshold mutation (e.g., "after window 1, n1_max_for_exit was updated") can extend this pattern by capturing `sys_loaded.th` at each call:

```python
captured_thresholds = []

def _spy_predict(sys_loaded, df_inner, edges_df, **kwargs):
    import dataclasses
    captured_thresholds.append(dataclasses.replace(sys_loaded.th))
    from botdetector_pipeline import predict_system as _real_predict
    return _real_predict(sys_loaded, df_inner, edges_df, **kwargs)
```

---

#### Cold-start assertion pattern (D-08, CAL-03)

Test that when `len(accounts) < window_size`, thresholds are never updated. Based on the structure of `test_ratio_clamping_applied` (lines 196–234), which asserts that the original trained value is preserved:

```python
def test_cold_start_preserves_original_thresholds(minimal_system, tmp_path):
    """With n < window_size accounts, thresholds must not change (CAL-03 cold-start)."""
    sys_obj, _, _, _ = minimal_system
    original_n1 = sys_obj.th.n1_max_for_exit

    # 3 accounts, window_size=100 -> cold-start
    path = _make_twibot_json(tmp_path, n=3)
    df = _make_twibot_df(n=3)
    edges = _make_twibot_edges(n=3)

    captured_thresholds = []

    def _spy_predict(sys_loaded, df_inner, edges_df, **kwargs):
        import dataclasses
        captured_thresholds.append(dataclasses.replace(sys_loaded.th))
        from botdetector_pipeline import predict_system as _real_predict
        return _real_predict(sys_loaded, df_inner, edges_df, **kwargs)

    from unittest.mock import patch

    with patch("evaluate_twibot20.load_accounts", return_value=df), \
         patch("evaluate_twibot20.build_edges", return_value=edges), \
         patch("evaluate_twibot20.validate", return_value=None), \
         patch("evaluate_twibot20.joblib.load", return_value=sys_obj), \
         patch("evaluate_twibot20.predict_system", side_effect=_spy_predict):

        run_inference(path, "fake_model.joblib", online_calibration=True, window_size=100)

    for th in captured_thresholds:
        assert th.n1_max_for_exit == original_n1, "Cold-start must not update thresholds"
```

---

#### `online_calibration=False` isolation pattern (D-06)

Test that `online_calibration=False` produces identical results to the pre-Phase-9 single-call path by calling `predict_system` exactly once:

```python
def test_online_calibration_false_calls_predict_system_once(minimal_system, tmp_path):
    """online_calibration=False must call predict_system exactly once (single-batch path)."""
    sys_obj, _, _, _ = minimal_system
    call_count = []

    def _spy_predict(sys_loaded, df_inner, edges_df, **kwargs):
        call_count.append(1)
        from botdetector_pipeline import predict_system as _real_predict
        return _real_predict(sys_loaded, df_inner, edges_df, **kwargs)

    from unittest.mock import patch

    with ...:  # standard four-patch context
        run_inference(path, "fake_model.joblib", online_calibration=False)

    assert len(call_count) == 1
```

---

#### `sys.th` immutability assertion pattern (D-07)

Verify `sys.th` is unchanged after `run_inference` with calibration enabled:

```python
import copy
original_th_copy = copy.copy(sys_obj.th)
# ... run_inference with online_calibration=True ...
assert sys_obj.th.n1_max_for_exit == original_th_copy.n1_max_for_exit
assert sys_obj.th.n2_trigger == original_th_copy.n2_trigger
assert sys_obj.th.novelty_force_stage3 == original_th_copy.novelty_force_stage3
```

---

## Shared Patterns

### Monkey-patch isolation with try/finally
**Source:** `evaluate_twibot20.py` lines 125–133
**Apply to:** The Phase 9 chunking loop — the `bp.extract_stage1_matrix = _clamped_s1` assignment and `finally: bp.extract_stage1_matrix = _orig_extract_stage1_matrix` restoration must wrap the entire loop body, not each individual `predict_system` call.

```python
bp.extract_stage1_matrix = _clamped_s1
try:
    # ... entire chunking loop or single call ...
    results = pd.concat(chunk_results, ignore_index=True)
finally:
    bp.extract_stage1_matrix = _orig_extract_stage1_matrix
```

### Logging convention
**Source:** `evaluate_twibot20.py` lines 91–94 (stdout print pattern)
**Apply to:** Per-window threshold update log line in `run_inference()`

```python
print(f"[twibot20] tweet distribution: RT={total_rt}, MT={total_mt}, original={total_orig}")
print(f"[twibot20] zero-tweet fraction: {zero_tweet_frac:.3f}")
```

Phase 9 log lines follow the same `[twibot20]` or a new `[cal]` prefix for threshold update events. One line per window update is sufficient (D per CONTEXT.md "Claude's Discretion").

### `np.percentile` usage
**Source:** `evaluate_twibot20.py` lines 116–118 (already uses `np.percentile` for ratio diagnostics)
**Apply to:** Threshold update formula (D-04)

```python
_p95 = np.percentile(_ratios, 95)
_p99 = np.percentile(_ratios, 99)
```

Exact same call form for threshold update: `new_val = np.percentile(novelty_buffer, 75)`.

### `dataclasses.replace` for partial struct copy
**Source:** `calibrate.py` lines 340–351 (full reconstruction), `botdetector_pipeline.py` line 3 (imports `dataclass`)
**Apply to:** Local `current_th` management in Phase 9

```python
import dataclasses
current_th = dataclasses.replace(sys_loaded.th)   # full copy at start
# ...later...
current_th = dataclasses.replace(
    current_th,
    n1_max_for_exit=p,
    n2_trigger=p,
    novelty_force_stage3=p,
)
```

`dataclasses` is already available as stdlib — no new dependency.

### Test fixture reuse
**Source:** `tests/conftest.py` lines 130–268 (`minimal_system` fixture)
**Apply to:** All new Phase 9 tests

All new test functions accept `minimal_system` as their first fixture argument. They unpack as `sys_obj, _, _, _ = minimal_system` when only the system object is needed.

---

## No Analog Found

No files in Phase 9 are entirely novel — both the modified function and the new tests have close analogs in the existing codebase.

---

## Metadata

**Analog search scope:** root Python files, `tests/`, `calibrate.py`, `botdetector_pipeline.py`
**Files scanned:** `evaluate_twibot20.py`, `botdetector_pipeline.py` (lines 224–239, 641–922), `calibrate.py`, `tests/test_evaluate_twibot20.py`, `tests/conftest.py`, `.planning/REQUIREMENTS.md`
**Pattern extraction date:** 2026-04-17
