---
gsd_state_version: 1.0
workstream: calibration-fix
milestone: v1.1.1
milestone_name: Threshold Calibration Search Fix
created: 2026-04-16
status: ready_to_discuss
stopped_at: Milestone initialized; ready to discuss Phase 8
last_updated: "2026-04-16T00:00:00Z"
---

# Project State

## Project Reference

See: `.planning/workstreams/calibration-fix/PROJECT.md`

**Core value:** Calibration should produce a meaningful threshold policy, not spend repeated trials rediscovering an identical plateau.
**Current focus:** Initialize a focused fix for the degenerate threshold search in `calibrate_thresholds()`.

## Current Position
**Status:** Ready to discuss
**Current Phase:** Phase 8 - Calibration Signal Recovery
**Last Activity:** 2026-04-16
**Last Activity Description:** Milestone v1.1.1 initialized for calibration search fix

## Progress
**Phases Complete:** 0 / 2
**Current Plan:** Not started

## Pending Todos

- Confirm whether the fix should prefer early stopping on a flat objective, a smoother optimization objective, or both.

## Blockers/Concerns

- The current Optuna objective optimizes hard-thresholded F1 on S2, which likely creates broad score plateaus where many threshold vectors are indistinguishable.
- Any fix must preserve seed-based reproducibility and avoid introducing leakage between S1, S2, and S3.

## Session Continuity
**Last Session:** 2026-04-16
**Stopped At:** Milestone initialized; next step is Phase 8 discussion/planning
**Resume File:** None
