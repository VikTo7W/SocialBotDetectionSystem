---
gsd_state_version: 1.0
workstream: stage2b-lstm-version
milestone: v1.2.1
milestone_name: Stage 2b LSTM Variant
created: 2026-04-16
status: ready_to_execute
stopped_at: Phase 9 plans written; ready for execution
last_updated: "2026-04-16T21:05:00Z"
---

# Project State

## Project Reference

See: `.planning/workstreams/stage2b-lstm-version/PROJECT.md`

**Core value:** The cascade must still produce a single, well-calibrated bot probability per account while letting us test whether a sequence-model Stage 2b adds useful signal beyond the current AMR-inspired refinement path.
**Current focus:** Plan Phase 9 around an explicit AMR-vs-LSTM selector wired through both training and inference while preserving the shared cascade pipeline.

## Current Position
**Status:** Planned
**Current Phase:** Phase 9 - Cascade Integration and Variant Selection
**Last Activity:** 2026-04-16
**Last Activity Description:** Phase 9 plans written for explicit AMR-vs-LSTM selection and deterministic integration coverage

## Progress
**Phases Complete:** 1
**Current Plan:** Ready for execution

## Blockers/Concerns

- The LSTM foundation is now in place, but execution still needs to wire it into `train_system()` and `predict_system()`.
- Phase 9 must preserve clean variant selection semantics so the AMR and LSTM paths are comparable rather than tangled.
- The fixture-backed proof is intentionally narrower than a real-data benchmark; that comparison belongs later in Phase 10.

## Session Continuity
**Last Session:** 2026-04-16
**Stopped At:** Phase 9 plans written; ready for execution
**Resume File:** .planning/workstreams/stage2b-lstm-version/phases/09-cascade-integration-and-variant-selection/09-01-PLAN.md
