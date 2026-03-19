---
phase: 02-threshold-calibration
plan: 02
subsystem: calibration
tags: [optuna, tpe, threshold-calibration, botdetector, calibrate.py]

# Dependency graph
requires:
  - phase: 02-threshold-calibration/02-01
    provides: tests/ scaffold with 6 test stubs, optuna 4.8.0, minimal_system fixture

provides:
  - calibrate.py with calibrate_thresholds() implementing Optuna TPE optimization over 10 thresholds
  - main.py wired to call calibrate_thresholds between train_system and predict_system
  - CALIB-01, CALIB-02, CALIB-03 all satisfied

affects:
  - main.py execution pipeline (calibration now runs on S2 before S3 evaluation)
  - system.th (mutated in-place with best thresholds from TPE study)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Optuna closure pattern: predict_system wrapped in objective closure capturing S2 data; only system.th swapped per trial"
    - "Dynamic lower-bound constraint: s2a_bot lower = max(s2a_human + 0.05, 0.70) prevents human/bot threshold inversion"
    - "NaN guard: objective returns 0.0 on NaN score (handles degenerate routing where all predictions are same class)"
    - "In-place mutation pattern: system.th replaced at trial end and after study for CALIB-03 persistence"

key-files:
  created:
    - calibrate.py
  modified:
    - main.py

key-decisions:
  - "s1_human/s1_bot sampled independently (ranges don't overlap) — simplest approach per RESEARCH.md Pattern 2"
  - "s2a_bot and s12_bot use dynamic lower bound max(human+0.05, 0.70) to guarantee human < bot ordering"
  - "n_jobs=1 enforced for TPESampler reproducibility per Optuna docs"
  - "NaN guard returns 0.0 penalty to handle degenerate threshold combinations"
  - "calibrate_thresholds placed in main.py before predict_system so S3 evaluation uses calibrated thresholds"

# Metrics
duration: 2min
completed: 2026-03-19
---

# Phase 2 Plan 02: Threshold Calibration Implementation Summary

**calibrate_thresholds() implemented with Optuna TPESampler over 10 threshold dimensions on S2 data; all 6 tests green in 9s; wired into main.py between train_system and predict_system**

## Performance

- **Duration:** 2 min
- **Started:** 2026-03-19T21:15:41Z
- **Completed:** 2026-03-19T21:17:52Z
- **Tasks:** 2
- **Files modified:** 2 (1 created, 1 modified)

## Accomplishments

- Created calibrate.py (107 lines) with calibrate_thresholds() using Optuna TPESampler for Bayesian optimization of all 10 StageThresholds dimensions
- METRIC_FNS dict dispatches "f1", "auc", "precision", "recall" from sklearn.metrics; unknown metric raises ValueError with "Unknown metric" message
- system.th mutated in-place during each trial and set to best_th after study.optimize() satisfying CALIB-03
- Reproducibility guaranteed via TPESampler(seed=seed) + n_jobs=1
- All 6 tests in tests/test_calibrate.py pass in 9.08 seconds
- Wired calibrate_thresholds call into main.py with metric="f1", n_trials=200, seed=SEED between train_system() (line 92) and predict_system() (line 116)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create calibrate.py** - `5604b5b` (feat)
2. **Task 2: Wire into main.py** - `b795b6c` (feat)

## Files Created/Modified

- `calibrate.py` - calibrate_thresholds() function, METRIC_FNS dict, Optuna TPE optimization loop (107 lines)
- `main.py` - Added import and calibrate_thresholds() call between training and evaluation

## Decisions Made

- s1_human (max 0.20) and s1_bot (min 0.80) sampled with non-overlapping ranges — no dynamic lower bound needed for s1 pair since ranges are separated by 0.60
- s2a_bot and s12_bot use dynamic lower bound `max(human+0.05, 0.70)` to handle the overlapping ranges (human up to 0.30, bot down to 0.70)
- n_jobs=1 required for TPESampler seed reproducibility per Optuna documentation
- NaN guard in objective returns 0.0 penalty for degenerate trial configurations

## Deviations from Plan

None - plan executed exactly as written.

## Self-Check

### Files exist:
- calibrate.py: exists
- main.py: exists (modified)

### Commits exist:
- 5604b5b: feat(02-02): implement calibrate_thresholds
- b795b6c: feat(02-02): wire calibrate_thresholds into main.py

## Self-Check: PASSED

---
*Phase: 02-threshold-calibration*
*Completed: 2026-03-19*
