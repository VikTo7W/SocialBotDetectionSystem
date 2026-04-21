---
phase: 20
plan: "01"
subsystem: wave-0-red-tests
tags: [testing, contracts, paper-outputs]
key-files:
  created:
    - tests/test_eval_botsim_native.py
    - tests/test_eval_reddit_twibot_transfer.py
    - tests/test_eval_twibot_native.py
    - tests/test_paper_outputs.py
    - .planning/phases/20-evaluation-entry-points-and-paper-outputs/20-01-NOTES.md
  modified:
    - ablation_tables.py
metrics:
  tasks_completed: 6
  tasks_total: 6
---

# Plan 20-01 Summary

## Outcome

Established the Wave 0 contract scaffold for all three maintained evaluation entry points plus the standalone Table 5 driver, and removed the `ablation_tables.py` import break that was preventing clean collection.

## Delivered

- One-line import fix in `ablation_tables.py`: `filter_edges_for_split` now comes from `train_botsim`
- `tests/test_eval_botsim_native.py` with 5 contract tests
- `tests/test_eval_reddit_twibot_transfer.py` with 5 contract tests
- `tests/test_eval_twibot_native.py` with 5 contract tests
- `tests/test_paper_outputs.py` with 5 contract tests
- `20-01-NOTES.md` recording the collect-only snapshot and expected missing-module failure modes

## Expected Red State

- `eval_botsim_native`, `eval_reddit_twibot_transfer`, `eval_twibot_native`, and `generate_table5` do not exist yet
- The four new test files therefore fail with `ModuleNotFoundError`, which is the intended Wave 0 contract state

## Verification

- `python -c "import ablation_tables; print(ablation_tables.filter_edges_for_split.__module__)"`
- `python -m pytest tests/test_ablation_tables.py --collect-only -q`
- `python -m py_compile tests/test_eval_botsim_native.py tests/test_eval_reddit_twibot_transfer.py tests/test_eval_twibot_native.py tests/test_paper_outputs.py`
- `python -m pytest tests/test_evaluate.py tests/test_evaluate_twibot20_native.py -x -q`
- `python -m pytest tests/ --collect-only -q`

## Self-Check: PASSED

- [x] `ablation_tables` imports without error
- [x] `tests/test_ablation_tables.py` collects cleanly
- [x] All four new contract files exist with 5 tests each
- [x] Pre-existing green tests remained green
- [x] Full-suite collect-only failed only for the four intentionally absent production modules
