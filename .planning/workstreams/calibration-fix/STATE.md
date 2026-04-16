---
gsd_state_version: 1.0
workstream: calibration-fix
milestone: v1.1.1
milestone_name: Threshold Calibration Search Fix
created: 2026-04-16
status: ready_to_discuss
stopped_at: Phase 9 context gathered; ready for planning
last_updated: "2026-04-16T01:35:00Z"
---

# Project State

## Project Reference

See: `.planning/workstreams/calibration-fix/PROJECT.md`

**Core value:** Calibration should produce a meaningful threshold policy, not spend repeated trials rediscovering an identical plateau.
**Current focus:** Plan Phase 9 validation work around real-run evidence for the new calibration selection behavior.

## Current Position
**Status:** Context gathered
**Current Phase:** Phase 9 - Validation and Selection Evidence
**Last Activity:** 2026-04-16
**Last Activity Description:** Phase 9 context captured for real-run validation and selection evidence

## Progress
**Phases Complete:** 1 / 2
**Current Plan:** Ready for planning

## Blockers/Concerns

- The current Optuna objective optimizes hard-thresholded F1 on S2, which likely creates broad score plateaus where many threshold vectors are indistinguishable.
- Any fix must preserve seed-based reproducibility and avoid introducing leakage between S1, S2, and S3.
- Phase 9 still needs stronger evidence that the chosen selection rule improves meaningful differentiation on real calibration behavior, not just synthetic tie scenarios.

## Session Continuity
**Last Session:** 2026-04-16
**Stopped At:** Phase 9 context gathered; ready for planning
**Resume File:** .planning/workstreams/calibration-fix/phases/09-validation-and-selection-evidence/09-CONTEXT.md
