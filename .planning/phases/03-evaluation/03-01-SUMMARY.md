---
phase: 03-evaluation
plan: "01"
subsystem: evaluation
tags: [evaluation, metrics, sklearn, tdd]
dependency_graph:
  requires: [botdetector_pipeline.predict_system, calibrate.calibrate_thresholds]
  provides: [evaluate.evaluate_s3]
  affects: [main.py]
tech_stack:
  added: []
  patterns: [sklearn.metrics, plain print formatting, TDD red-green]
key_files:
  created:
    - evaluate.py
    - tests/test_evaluate.py
  modified:
    - main.py
decisions:
  - Plain print() formatting (no tabulate/rich) per acceptance criteria — keeps evaluate.py dependency-free
  - pct_stage1_exit = amr_used==0 AND stage3_used==0 (true early-exit path, no AMR refinement)
  - pct_stage2_exit = amr_used==1 AND stage3_used==0 (AMR-refined but no structural stage)
  - pct_stage3_exit = stage3_used==1 (regardless of AMR, routed to Stage 3 structural model)
  - Invariant: pct_stage1_exit + pct_stage2_exit + pct_stage3_exit == 100% enforced by construction
metrics:
  duration: "3 min"
  completed: "2026-03-19"
  tasks_completed: 2
  files_created: 2
  files_modified: 1
---

# Phase 3 Plan 01: Evaluation Module Summary

**One-liner:** sklearn-based evaluate_s3() producing three-section paper-ready console report — overall F1/AUC/precision/recall, per-stage breakdown (p1/p2/p12/p_final), and routing statistics with exit-percentage invariant summing to 100%.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create evaluate.py with evaluate_s3() function (TDD) | 1b69768 | evaluate.py, tests/test_evaluate.py |
| 2 | Wire evaluate_s3 into main.py | be443b3 | main.py |

## Decisions Made

- **Plain print() chosen over tabulate/rich:** Acceptance criteria explicitly required no external deps beyond sklearn. The formatted output uses f-string alignment to produce a clean tabular layout.
- **Routing partition definition:** Three mutually exclusive buckets — stage1_exit (no AMR, no Stage3), stage2_exit (AMR used, no Stage3), stage3_exit (Stage3 used). This guarantees the 100% sum invariant without floating-point ambiguity.
- **zero_division=0 for F1/precision/recall:** Prevents crashes on degenerate predictions (all-zero or all-one) while returning a valid float in [0, 1].

## Test Coverage

15 tests across 7 test classes:
- `TestReturnStructure`: top-level key presence
- `TestOverallMetrics`: key presence and float in [0, 1] range
- `TestPerStageMetrics`: per-stage key structure and value ranges
- `TestRoutingStatistics`: routing key presence and [0, 100] ranges
- `TestRoutingPercentageInvariant`: sum == 100.0 (within 0.01 tolerance), edge cases
- `TestPrintedOutput`: capsys checks for all three section headers
- `TestEdgeCaseNoAmrNoStage3`: 100% stage1 exit with all-zeros amr/stage3
- `TestIntegrationWithMinimalSystem`: full end-to-end with predict_system() output

## Requirements Satisfied

- EVAL-01: Overall metrics (F1, AUC, precision, recall) for p_final vs ground truth
- EVAL-02: Per-stage metrics table (p1, p2, p12, p_final each vs labels)
- EVAL-03: Routing statistics (stage exit percentages, AMR trigger rate)

## Deviations from Plan

None — plan executed exactly as written.

## Self-Check

- [x] evaluate.py exists with >= 80 lines
- [x] tests/test_evaluate.py exists with >= 60 lines
- [x] evaluate_s3 pattern matches `def evaluate_s3.*results.*pd\.DataFrame`
- [x] sklearn.metrics imported in evaluate.py
- [x] main.py contains `from evaluate import evaluate_s3`
- [x] main.py calls `evaluate_s3(out, y_true)`
- [x] main.py does NOT contain `classification_report`
- [x] All 15 tests pass

## Self-Check: PASSED
