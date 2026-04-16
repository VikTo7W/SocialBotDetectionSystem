---
gsd_state_version: 1.0
workstream: calibration-fix
milestone: v1.1.1
milestone_name: Threshold Calibration Search Fix
created: 2026-04-16
status: ready_to_discuss
stopped_at: Phase 8 complete; next step is Phase 9 discussion/planning
last_updated: "2026-04-16T01:15:00Z"
---

# Project State

## Project Reference

See: `.planning/workstreams/calibration-fix/PROJECT.md`

**Core value:** Calibration should produce a meaningful threshold policy, not spend repeated trials rediscovering an identical plateau.
**Current focus:** Prepare Phase 9 validation work for the new calibration selection behavior.

## Current Position
**Status:** Phase 8 complete
**Current Phase:** Phase 9 - Validation and Selection Evidence
**Last Activity:** 2026-04-16
**Last Activity Description:** Phase 8 executed and verified; calibration diagnostics and hybrid stop/tie-break logic are in place

## Progress
**Phases Complete:** 1 / 2
**Current Plan:** Phase 9 not yet planned

## Blockers/Concerns

- The current Optuna objective optimizes hard-thresholded F1 on S2, which likely creates broad score plateaus where many threshold vectors are indistinguishable.
- Any fix must preserve seed-based reproducibility and avoid introducing leakage between S1, S2, and S3.
- Phase 9 still needs stronger evidence that the chosen selection rule improves meaningful differentiation on real calibration behavior, not just synthetic tie scenarios.

## Session Continuity
**Last Session:** 2026-04-16
**Stopped At:** Phase 8 complete; next step is Phase 9 discussion/planning
**Resume File:** .planning/workstreams/calibration-fix/phases/08-calibration-signal-recovery/08-VERIFICATION.md
