---
phase: 08-calibration-signal-recovery
plan: "01"
subsystem: calibration-diagnostics
tags: [optuna, diagnostics, tie-analysis, reproducibility, testing]

requires: []
provides:
  - Trial-level calibration diagnostics for plateau analysis
  - Deterministic reporting for best-score ties
  - Test coverage proving diagnostic metadata remains available
affects:
  - 08-02 (consumes diagnostic groundwork for tie-breaking and early stopping)

tech-stack:
  added: []
  patterns:
    - "Optuna trial user_attrs as an audit trail for calibration decisions"
    - "Deterministic signatures for hard predictions and routing behavior"

key-files:
  created: []
  modified:
    - calibrate.py
    - tests/test_calibrate.py
    - tests/conftest.py

requirements-completed:
  - CALFIX-01
  - CALFIX-02

duration: 10min
completed: 2026-04-16
---

# Phase 8 Plan 01: Calibration Diagnostics Summary

**Instrumented `calibrate_thresholds()` so tied F1 trials are diagnosable instead of opaque, and added regression coverage for deterministic diagnostic metadata.**

## Accomplishments

- Added per-trial Optuna `user_attrs` for:
  - primary score
  - secondary log loss and Brier score
  - positive prediction count
  - AMR and Stage 3 usage rates
  - hard-label and routing signatures
- Switched final threshold reconstruction away from raw `study.best_params` to a ranked completed-trial view, which made diagnostic tie analysis possible.
- Added calibration reporting on:
  - number of best-score ties
  - whether tied trials share hard predictions
  - whether tied trials share routing behavior
- Extended `tests/test_calibrate.py` with diagnostic-report coverage.

## Verification

`python -m pytest tests/test_calibrate.py -q`

Result:
- `9 passed`

## Deviation from Plan

- Updated `tests/conftest.py` with single-core environment defaults so the existing sklearn histogram-based synthetic fixture can run inside this Windows sandbox without `PermissionError` during thread setup. This was a harness-support change, not a functional calibration change.

## Outcome

Phase 8 now has enough visibility to explain whether the plateau comes from hard-label quantization, unchanged routing, or both. That diagnostic foundation feeds directly into Plan 02's hybrid selection and early-stop policy.

