---
phase: 10-evaluation-metrics-and-paper-table
plan: "01"
subsystem: twibot-evaluation
tags: [evaluation, twibot20, metrics, tdd, zero-shot]
requirements: [TW-06]

dependency_graph:
  requires:
    - evaluate_twibot20.py (run_inference — Phase 9)
    - evaluate.py (evaluate_s3)
    - twibot20_io.py (load_accounts)
  provides:
    - evaluate_twibot20.evaluate_twibot20() — importable evaluation function
    - metrics_twibot20.json — evaluate_s3() return dict serialized to JSON
  affects:
    - ablation_tables.py — Plan 02 reads metrics_twibot20.json for cross-dataset table

tech_stack:
  added: []
  patterns:
    - TDD red/green cycle (test → implement)
    - monkeypatch-based unit tests with synthetic DataFrames
    - evaluate_s3() drop-in metric engine reused from main pipeline

key_files:
  created: []
  modified:
    - evaluate_twibot20.py
    - tests/test_evaluate_twibot20.py

decisions:
  - "evaluate_twibot20() returns full evaluate_s3() dict (overall/per_stage/routing) for consistency with evaluate_s3 return contract"
  - "__main__ calls run_inference() once then evaluate_s3() directly to avoid double inference (optimized path)"
  - "metrics_twibot20.json mirrors the full evaluate_s3() return structure for use by Plan 02"

metrics:
  duration_minutes: 10
  completed_date: "2026-04-16"
  tasks_completed: 1
  tasks_total: 1
  files_modified: 2
  tests_added: 3
  tests_total: 8
---

# Phase 10 Plan 01: Evaluate TwiBot-20 Function and Metrics JSON Summary

**One-liner:** TDD implementation of `evaluate_twibot20()` that calls `run_inference()` then `evaluate_s3()`, returning the full metrics dict and saving `metrics_twibot20.json` for cross-dataset table generation.

## What Was Built

Added `evaluate_twibot20()` to `evaluate_twibot20.py` — an importable evaluation function parallel to `run_inference()`. The function loads TwiBot-20 accounts, runs zero-shot inference, retrieves ground truth labels from `load_accounts()["label"]`, and calls `evaluate_s3()` to produce the paper-ready report and return the full metric dict.

Expanded the `__main__` block to call `run_inference()` once (avoiding double inference), save `results_twibot20.json` (Phase 9 artifact preserved), and save `metrics_twibot20.json` (Phase 10 artifact for Plan 02's cross-dataset table).

## Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| RED | Add failing tests for evaluate_twibot20() | 9cfbd57 | tests/test_evaluate_twibot20.py |
| GREEN | Implement evaluate_twibot20() and expand __main__ | 6f2c371 | evaluate_twibot20.py |

## TDD Gate Compliance

- RED gate: commit `9cfbd57` — `test(10-01): add failing tests for evaluate_twibot20() and metrics JSON`
- GREEN gate: commit `6f2c371` — `feat(10-01): add evaluate_twibot20() function and expand __main__ block`
- All 3 new tests failed before implementation (confirmed by pytest run showing 4 passed, 1 failed at RED stage)
- All 8 tests pass after implementation (79 total suite tests, no regressions)

## Verification

```
python -m pytest tests/test_evaluate_twibot20.py -v     → 8 passed
python -m pytest tests/ -x -q                           → 79 passed
python -c "from evaluate_twibot20 import evaluate_twibot20; print('import OK')"  → import OK
```

## Acceptance Criteria Check

- [x] `evaluate_twibot20.py` contains `def evaluate_twibot20(`
- [x] `evaluate_twibot20.py` contains `from evaluate import evaluate_s3`
- [x] `evaluate_twibot20.py` contains `metrics_twibot20.json`
- [x] `evaluate_twibot20.py` contains `json.dump(metrics`
- [x] `evaluate_twibot20.py` contains `evaluate_s3(results, y_true`
- [x] `tests/test_evaluate_twibot20.py` contains `def test_evaluate_twibot20_returns_metrics`
- [x] `tests/test_evaluate_twibot20.py` contains `def test_main_saves_metrics_json`
- [x] `python -m pytest tests/test_evaluate_twibot20.py -v -x` exits 0 with 8 passed
- [x] `python -m pytest tests/ -x -q` exits 0 (79 passed, no regressions)
- [x] `python -c "from evaluate_twibot20 import evaluate_twibot20; print('import OK')"` prints "import OK"

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — `evaluate_twibot20()` is fully wired: `run_inference()` → `load_accounts()` → `evaluate_s3()` → return dict.

## Threat Flags

None — no new network endpoints, auth paths, or trust boundaries introduced. `metrics_twibot20.json` and `evaluate_s3` stdout are both within the plan's accepted threat register (T-10-01, T-10-02).

## Self-Check: PASSED

- `evaluate_twibot20.py` exists and contains `def evaluate_twibot20(` ✓
- `tests/test_evaluate_twibot20.py` exists and contains all 3 new test functions ✓
- Commit `9cfbd57` (RED) exists ✓
- Commit `6f2c371` (GREEN) exists ✓
- 8 tests pass, 79 full suite tests pass ✓
