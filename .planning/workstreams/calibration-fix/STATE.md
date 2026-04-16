---
gsd_state_version: 1.0
workstream: calibration-fix
milestone: v1.1.1
milestone_name: Threshold Calibration Search Fix
created: 2026-04-16
status: ready_to_execute
stopped_at: Phase 9 planned; ready for execution
last_updated: "2026-04-16T01:55:00Z"
---

# Project State

## Project Reference

See: `.planning/workstreams/calibration-fix/PROJECT.md`

**Core value:** Calibration should produce a meaningful threshold policy, not spend repeated trials rediscovering an identical plateau.
**Current focus:** Execute Phase 9 to validate the hybrid fix on the real S2 path and emit a compact selection-evidence artifact.

## Current Position
**Status:** Planned
**Current Phase:** Phase 9 - Validation and Selection Evidence
**Last Activity:** 2026-04-16
**Last Activity Description:** Phase 9 execution plans and verification criteria created

## Progress
**Phases Complete:** 1 / 2
**Current Plan:** 09-01 and 09-02 ready for execution

## Blockers/Concerns

- The current Optuna objective optimizes hard-thresholded F1 on S2, which likely creates broad score plateaus where many threshold vectors are indistinguishable.
- Any fix must preserve seed-based reproducibility and avoid introducing leakage between S1, S2, and S3.
- Phase 9 still depends on a successful real-run validation path; if `python main.py` is too heavy or environment-sensitive, execution may need a narrowly scoped reproducible runner or artifact hook.

## Session Continuity
**Last Session:** 2026-04-16
**Stopped At:** Phase 9 planned; ready for execution
**Resume File:** .planning/workstreams/calibration-fix/phases/09-validation-and-selection-evidence/09-01-PLAN.md
