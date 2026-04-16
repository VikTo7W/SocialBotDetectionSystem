---
phase: 08-calibration-signal-recovery
plan: "02"
subsystem: calibration-selection
tags: [optuna, tie-break, early-stop, plateau, testing]

requires:
  - phase: 08-01
    provides: deterministic trial diagnostics and tie analysis
provides:
  - Secondary-score tie-breaking for equal primary-score trials
  - Plateau early-stop guardrail for flat searches
  - Regression coverage for redundant-trial prevention
affects:
  - Phase 9 validation and selection evidence

tech-stack:
  added: []
  patterns:
    - "Lexicographic candidate ranking: primary metric, then smooth secondary metrics"
    - "Patience-based early stopping driven by meaningful calibration improvement"

key-files:
  created: []
  modified:
    - calibrate.py
    - tests/test_calibrate.py

requirements-completed:
  - CALFIX-03
  - CALFIX-04

duration: 10min
completed: 2026-04-16
---

# Phase 8 Plan 02: Hybrid Calibration Fix Summary

**Implemented the Phase 8 hybrid fix: tied headline-score trials now use a smooth secondary metric for selection, and long flat searches can stop early once the plateau is stable.**

## Accomplishments

- Added deterministic lexicographic ranking over completed trials:
  - maximize primary score
  - minimize secondary log loss
  - minimize secondary Brier score
  - fall back to trial number only when all meaningful metrics still tie
- Replaced implicit first-best selection with explicit ranked-trial selection.
- Added a plateau callback with patience-based early stopping for redundant long runs.
- Stored a structured `system.calibration_report_` containing:
  - requested vs executed trials
  - selected trial number
  - whether early stopping triggered
  - tie count and tie characteristics
  - per-trial diagnostics
- Added regression tests for:
  - diagnostic report availability
  - secondary-metric tie breaking
  - plateau early stopping

## Verification

`python -m pytest tests/test_calibrate.py -q`

Result:
- `9 passed`

## Outcome

The calibration path no longer defaults to arbitrary first-trial-wins behavior when the primary metric ties, and longer flat searches can terminate early with a documented reason. Phase 8 is ready to hand off to Phase 9 for deeper validation and evidence capture.

