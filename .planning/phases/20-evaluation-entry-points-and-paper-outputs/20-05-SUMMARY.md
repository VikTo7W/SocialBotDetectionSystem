---
phase: 20
plan: "05"
subsystem: table5-and-verification
tags: [paper-outputs, verification, latex]
key-files:
  created:
    - generate_table5.py
    - .planning/phases/20-evaluation-entry-points-and-paper-outputs/20-VERIFICATION.md
  modified:
    - tests/test_paper_outputs.py
metrics:
  tasks_completed: 2
  tasks_total: 2
---

# Plan 20-05 Summary

## Outcome

Built the standalone Table 5 driver, turned the paper-output contract tests green, and recorded the full Phase 20 verification evidence.

## Delivered

- `generate_table5.py` reading:
  - `paper_outputs/metrics_botsim.json`
  - `paper_outputs/metrics_reddit_transfer.json`
  - `paper_outputs/metrics_twibot_native.json`
- default Table 5 output:
  - `tables/table5_cross_dataset.tex`
- `20-VERIFICATION.md` with per-requirement evidence and environment blockers

## Verification

- `python -m pytest tests/test_paper_outputs.py tests/test_eval_botsim_native.py tests/test_eval_reddit_twibot_transfer.py tests/test_eval_twibot_native.py -x -q --basetemp .phase20_pytest_all_v2`
  - `21 passed`
- `python -m pytest tests/test_ablation_tables.py --collect-only -q`
  - `12 tests collected`
- `python -m pytest tests/test_evaluate.py tests/test_evaluate_twibot20_native.py -x -q`
  - `22 passed`

## Self-Check: PASSED

- [x] Table 5 driver reads the maintained `paper_outputs/` JSON locations
- [x] LaTeX output path is `tables/table5_cross_dataset.tex`
- [x] new Phase 20 test surface is green
- [x] verification report captures the remaining TwiBot-artifact runtime blocker explicitly
