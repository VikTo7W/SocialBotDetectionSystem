---
phase: 10-evaluation-metrics-and-paper-table
reviewed: 2026-04-16T00:00:00Z
depth: standard
files_reviewed: 4
files_reviewed_list:
  - evaluate_twibot20.py
  - ablation_tables.py
  - tests/test_evaluate_twibot20.py
  - tests/test_ablation_tables.py
findings:
  critical: 0
  warning: 4
  info: 5
  total: 9
status: issues_found
---

# Phase 10: Code Review Report

**Reviewed:** 2026-04-16T00:00:00Z
**Depth:** standard
**Files Reviewed:** 4
**Status:** issues_found

## Summary

Four files reviewed: two production modules (`evaluate_twibot20.py`, `ablation_tables.py`) and their corresponding test suites. The code is well-structured, the monkey-patch pattern is consistently guarded with `finally` blocks, and the public API contracts are clearly documented. No security vulnerabilities or data-loss risks were found.

Four warnings were identified: a silent double-load of `test.json` that can cause a row-order mismatch between `accounts_df` and the `raw` JSON records (the most consequential issue), a missing `encoding` argument on a file open that will misread Unicode on Windows, an unused spy fixture in a test that gives no coverage for what it claims, and a `torch.load` call without `weights_only=True` that triggers a deprecation warning in PyTorch >= 2.4. Five informational items cover minor dead code, duplicated imports, a magic number, and a comment inaccuracy.

## Warnings

### WR-01: Row-order assumption between `load_accounts()` and raw JSON re-read may silently misalign account IDs

**File:** `evaluate_twibot20.py:66-71`

**Issue:** `run_inference()` calls `load_accounts(path)` (line 56) to build `accounts_df`, then re-opens the same JSON file at line 67 to extract `account_id` strings from `raw`. The code comment says "load_accounts() iterates data in JSON array order; this re-read uses the same order." This is only true if `load_accounts()` preserves JSON array order without any sort or dedup step. If `load_accounts()` ever performs a sort, deduplication, or index reset that reorders rows, then `[r["ID"] for r in raw]` will be assigned to the wrong rows — silently mislabeling every account. There is no assertion or alignment check to guard against this. The misassignment would corrupt `account_id` (and downstream `p_final` attribution) without raising any error.

**Fix:** Align by key rather than relying on positional correspondence. Build a lookup dict from the raw JSON and merge on a stable key that `load_accounts()` already preserves:

```python
id_map = {r["ID"]: r["ID"] for r in raw}   # or richer mapping if needed
# After load_accounts(), assert the stable key exists, then map:
# e.g. if load_accounts preserves a 'user_id' or 'screen_name' that equals ID:
raw_by_screen = {r["screen_name"]: r["ID"] for r in raw}
df["account_id"] = df["screen_name"].map(raw_by_screen)
assert df["account_id"].notna().all(), "Some screen_names had no match in raw JSON"
```

If positional alignment is truly guaranteed by the `twibot20_io` contract, add an explicit assertion:

```python
assert len(raw) == len(accounts_df), (
    f"Row count mismatch: raw={len(raw)}, accounts_df={len(accounts_df)}"
)
```

---

### WR-02: `open(metrics_path, "w")` in `__main__` block missing `encoding` argument — will fail or corrupt on Windows with non-ASCII content

**File:** `evaluate_twibot20.py:146-147`

**Issue:** The `__main__` block writes `metrics_twibot20.json` without specifying `encoding`:

```python
with open(metrics_path, "w") as f:
    json.dump(metrics, f, indent=2)
```

On Windows, `open()` defaults to the system locale encoding (often `cp1252`). If any metric key or string value contains non-ASCII characters (e.g. Unicode account IDs that propagated into the dict), `json.dump` will raise a `UnicodeEncodeError` at runtime — a crash that only manifests on Windows. The symmetrical `open(path, "r", encoding="utf-8")` earlier at line 67 shows the project is already aware of this requirement.

**Fix:**

```python
with open(metrics_path, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)
```

---

### WR-03: `captured_x1` spy in `test_ratio_clamping_applied` is populated but never asserted — the test provides no coverage of the clamping behavior it claims to test

**File:** `tests/test_evaluate_twibot20.py:183-198`

**Issue:** The test sets up a `spy_extract` closure that appends captured Stage 1 matrices into `captured_x1`, but then discards the spy entirely — `spy_extract` is defined but never installed, and `captured_x1` is never inspected. The test only checks that `p_final` is finite and in [0, 1], which would pass even if clamping were removed. The comment "Capture X1 values that reach the stage1 model" is therefore misleading, and the stated TW-05 clamping behavior is not actually verified by this test.

**Fix:** Either install the spy and assert on captured values, or remove the dead spy code and update the docstring to accurately describe what the test does cover:

```python
# Option A: Remove dead spy and update docstring
def test_ratio_clamping_applied(minimal_system, tmp_path):
    """
    With statuses_count=100000, run_inference() must produce finite p_final
    values in [0,1] (confirms pipeline does not crash on extreme ratio features).
    """
    # ... (remove captured_x1, spy_extract, original_patch lines) ...

# Option B: Install the spy and assert clamping
bp.extract_stage1_matrix = spy_extract   # install spy before run_inference
result = run_inference(path, "fake_model.joblib")
assert len(captured_x1) > 0, "spy was never called"
for X in captured_x1:
    assert X[:, 6:10].max() <= 50.0, f"Ratio columns not clamped: max={X[:, 6:10].max()}"
```

---

### WR-04: `torch.load` called without `weights_only=True` — triggers deprecation warning and is unsafe with untrusted files

**File:** `ablation_tables.py:331-337`

**Issue:** Three `torch.load` calls load edge tensor files:

```python
edge_index = torch.load("edge_index.pt", map_location="cpu").numpy()
edge_type  = torch.load("edge_type.pt",  map_location="cpu").numpy()
edge_w     = torch.load("edge_weight.pt", map_location="cpu").numpy()
```

Since PyTorch 2.4, omitting `weights_only=True` emits a `FutureWarning` (which `warnings.filterwarnings("ignore", category=FutureWarning)` on line 40 silently suppresses). More importantly, `weights_only=False` allows arbitrary Python objects to be unpickled from the `.pt` files — a remote-code-execution risk if these files are ever sourced from outside the project. The suppressed warning means no signal will surface when PyTorch eventually makes `weights_only=True` the enforced default.

**Fix:**

```python
edge_index = torch.load("edge_index.pt", map_location="cpu", weights_only=True).numpy()
edge_type  = torch.load("edge_type.pt",  map_location="cpu", weights_only=True).numpy()
edge_w     = torch.load("edge_weight.pt", map_location="cpu", weights_only=True).numpy()
```

If the stored tensors are plain `torch.Tensor` objects (which they appear to be, given the immediate `.numpy()` calls), `weights_only=True` is safe and eliminates both the warning and the deserialization risk.

---

## Info

### IN-01: `from unittest.mock import patch` is imported twice in `test_ratio_clamping_applied`

**File:** `tests/test_evaluate_twibot20.py:183,191`

**Issue:** `from unittest.mock import patch` is imported at line 183 (inside the function body) and again at line 191, seven lines later. The second import is a no-op but suggests copy-paste editing without cleanup.

**Fix:** Remove the duplicate import at line 191.

---

### IN-02: `evaluate_twibot20.py` calls `load_accounts(path)` twice — once in `evaluate_twibot20()` and once in `run_inference()` — loading the same file twice

**File:** `evaluate_twibot20.py:121-122`

**Issue:** `evaluate_twibot20()` calls `run_inference(path, model_path)` (line 120), which internally calls `load_accounts(path)` (line 56). Then `evaluate_twibot20()` calls `load_accounts(path)` again at line 121 to obtain `y_true`. For large test sets this is wasteful; more importantly, it is a latent correctness risk: if `load_accounts()` had any non-determinism (random sampling, OS-level file buffering) the labels would be extracted from a different ordering than the inference results.

**Fix:** Thread the loaded DataFrame through the call chain rather than re-loading:

```python
def run_inference(path, model_path="trained_system_v12.joblib"):
    accounts_df = load_accounts(path)
    # ... existing logic ...
    return results, accounts_df   # return alongside results

def evaluate_twibot20(path="test.json", model_path="trained_system_v12.joblib", threshold=0.5):
    results, accounts_df = run_inference(path, model_path)
    y_true = accounts_df["label"].to_numpy()
    return evaluate_s3(results, y_true, threshold)
```

Alternatively, accept `accounts_df` as an optional parameter to `evaluate_twibot20()`.

---

### IN-03: Magic number `50.0` in Stage 1 ratio clamp not defined as a named constant

**File:** `evaluate_twibot20.py:85`

**Issue:** The clamp bound `50.0` appears in two separate places — in `run_inference()` (line 85) and is the same bound described in the TW-05 ticket reference. If this threshold is ever tuned, it must be updated in multiple locations. The value has no documentation at the usage site explaining why 50 was chosen.

**Fix:** Define a module-level constant:

```python
# Maximum allowed value for Stage 1 post/comment ratio features (TW-05, D-04).
# Ratios above this indicate implausibly sparse engagement and are clamped
# to prevent cascade collapse in zero-shot TwiBot-20 inference.
_RATIO_CLAMP_MAX: float = 50.0
```

Then use `_RATIO_CLAMP_MAX` in the clip call.

---

### IN-04: `build_table5` and `build_table6` docstrings say "(supplementary)" but have no cross-reference to the table numbering scheme

**File:** `ablation_tables.py:197-198, 214-215`

**Issue:** The module docstring at the top defines tables 1-6 by name, but `build_table5` and `build_table6` are the Stage 2b variant tables — not "Table 5: Cross-Dataset Comparison" (which is `generate_cross_dataset_table`). This naming conflict (two different functions both described as "Table 5") will be confusing to future maintainers and anyone reading the paper alongside the code.

**Fix:** Rename the Stage 2b functions to `build_stage2b_variant_table` and `build_stage2b_routing_table`, or update the module docstring numbering to avoid the collision.

---

### IN-05: `test_main_saves_metrics_json` simulates `__main__` logic manually rather than exercising the actual block

**File:** `tests/test_evaluate_twibot20.py:309-361`

**Issue:** The test manually replicates the `__main__` block's logic (calling `run_inference`, writing JSON, etc.) rather than importing and executing the module's `__main__` block via `runpy.run_module` or `subprocess`. This means if someone changes the `__main__` block (e.g. adds a new output file or changes the JSON path), the test will continue to pass without detecting the regression.

**Fix:** This is low-priority, but for stronger coverage consider:

```python
import runpy
import sys

monkeypatch.setattr(sys, "argv", ["evaluate_twibot20.py", path, "fake.joblib"])
monkeypatch.chdir(tmp_path)
runpy.run_module("evaluate_twibot20", run_name="__main__", alter_sys=True)
assert (tmp_path / "results_twibot20.json").exists()
assert (tmp_path / "metrics_twibot20.json").exists()
```

---

_Reviewed: 2026-04-16T00:00:00Z_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
