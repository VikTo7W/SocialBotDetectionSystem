---
phase: 10-evaluation-metrics-and-paper-table
plan: "02"
subsystem: ablation-tables
tags: [ablation, cross-dataset, twibot20, latex, tdd]
requirements: [TW-07]

dependency_graph:
  requires:
    - ablation_tables.py (build_table1/2/3/4, save_latex — existing patterns)
    - metrics_twibot20.json (written by evaluate_twibot20.py — Plan 10-01)
    - evaluate_s3() return structure (overall/per_stage/routing keys)
  provides:
    - ablation_tables.generate_cross_dataset_table() — Table 5 builder function
    - tables/table5_cross_dataset.tex — LaTeX cross-dataset comparison table
  affects:
    - ablation_tables.py main() — now loads metrics_twibot20.json and exports Table 5

tech_stack:
  added: []
  patterns:
    - TDD red/green cycle (test → implement)
    - build_table1/2/3/4 pattern extended with generate_cross_dataset_table()
    - os.path.exists guard for graceful skip when JSON artifact missing

key_files:
  created: []
  modified:
    - ablation_tables.py
    - tests/test_ablation_tables.py

decisions:
  - "generate_cross_dataset_table() reads metrics['overall'] from full evaluate_s3() dicts — consistent with D-06"
  - "main() uses os.path.exists guard for metrics_twibot20.json — mitigates T-10-04 (DoS from missing file)"
  - "Column headers are exact strings per D-08: 'BotSim-24 (Reddit, in-dist.)' and 'TwiBot-20 (Twitter, zero-shot)'"

metrics:
  duration_minutes: 3
  completed_date: "2026-04-16"
  tasks_completed: 1
  tasks_total: 1
  files_modified: 2
  tests_added: 3
  tests_total: 9
---

# Phase 10 Plan 02: Cross-Dataset Table (Table 5) Summary

**One-liner:** TDD implementation of `generate_cross_dataset_table()` that produces a 4x3 DataFrame comparing BotSim-24 (Reddit, in-dist.) vs TwiBot-20 (Twitter, zero-shot) overall metrics, wired into `ablation_tables.py main()` to export `tables/table5_cross_dataset.tex`.

## What Was Built

Added `generate_cross_dataset_table(botsim24_metrics, twibot20_metrics)` to `ablation_tables.py` following the established `build_table1/2/3/4` pattern. The function accepts two full `evaluate_s3()` return dicts, reads `metrics["overall"]` from each, and returns a 4-row DataFrame with columns `["Metric", "BotSim-24 (Reddit, in-dist.)", "TwiBot-20 (Twitter, zero-shot)"]` and rows F1 / AUC-ROC / Precision / Recall.

Wired into `main()` as step 8: loads `metrics_twibot20.json` (written by `evaluate_twibot20.py`), calls `generate_cross_dataset_table(report, twibot20_metrics)`, prints the table, and saves `tables/table5_cross_dataset.tex` via `save_latex()`. Includes a graceful skip with guidance when `metrics_twibot20.json` does not exist (threat T-10-04 mitigation).

Updated module docstring to mention Table 5.

## Tasks

| Task | Name | Commit | Files |
|------|------|--------|-------|
| RED | Add failing tests for generate_cross_dataset_table() | 8f05d86 | tests/test_ablation_tables.py |
| GREEN | Implement generate_cross_dataset_table() and wire main() | 9f937cf | ablation_tables.py |

## TDD Gate Compliance

- RED gate: commit `8f05d86` — `test(10-02): add failing tests for generate_cross_dataset_table()`
- GREEN gate: commit `9f937cf` — `feat(10-02): add generate_cross_dataset_table() and wire Table 5 into main()`
- All 3 new tests failed at RED stage (ImportError — function not yet defined)
- All 9 ablation_tables tests pass after GREEN implementation

## Verification

```
python -m pytest tests/test_ablation_tables.py -v     -> 9 passed
python -m pytest tests/ -x -q                          -> 82 passed, no regressions
python -c "from ablation_tables import generate_cross_dataset_table; print('import OK')"  -> import OK
```

## Acceptance Criteria Check

- [x] `ablation_tables.py` contains `def generate_cross_dataset_table(`
- [x] `ablation_tables.py` contains `"BotSim-24 (Reddit, in-dist.)"`
- [x] `ablation_tables.py` contains `"TwiBot-20 (Twitter, zero-shot)"`
- [x] `ablation_tables.py` contains `botsim24_metrics["overall"]`
- [x] `ablation_tables.py` contains `twibot20_metrics["overall"]`
- [x] `ablation_tables.py` contains `metrics_twibot20.json`
- [x] `ablation_tables.py` contains `table5_cross_dataset.tex`
- [x] `tests/test_ablation_tables.py` contains `def test_table5_cross_dataset`
- [x] `tests/test_ablation_tables.py` contains `def test_table5_uses_overall_key`
- [x] `tests/test_ablation_tables.py` contains `def test_table5_latex`
- [x] `tests/test_ablation_tables.py` contains `generate_cross_dataset_table`
- [x] `python -m pytest tests/test_ablation_tables.py -v -x` exits 0 with 9 passed
- [x] `python -m pytest tests/ -x -q` exits 0 (82 passed, no regressions)
- [x] `python -c "from ablation_tables import generate_cross_dataset_table; print('import OK')"` prints "import OK"

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

None — `generate_cross_dataset_table()` is fully implemented. `main()` is wired to load `metrics_twibot20.json` and call the function. The graceful skip branch is intentional (not a stub) — it handles the case where `evaluate_twibot20.py` has not yet been run.

## Threat Flags

None — no new network endpoints, auth paths, or trust boundaries introduced. The `os.path.exists` guard for `metrics_twibot20.json` directly mitigates T-10-04 (denial of service from missing file) as specified in the plan's threat register.

## Self-Check: PASSED

- `ablation_tables.py` exists and contains `def generate_cross_dataset_table(` [x]
- `tests/test_ablation_tables.py` contains all 3 new test functions [x]
- Commit `8f05d86` (RED) exists [x]
- Commit `9f937cf` (GREEN) exists [x]
- 9 ablation_tables tests pass, 82 full suite tests pass [x]
