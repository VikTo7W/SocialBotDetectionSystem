---
gsd_state_version: 1.0
workstream: stage2b-lstm-version
milestone: v1.2.1
milestone_name: Stage 2b LSTM Variant
created: 2026-04-16
status: ready_to_plan
stopped_at: Phase 8 context gathered; ready for planning
last_updated: "2026-04-16T20:12:00Z"
---

# Project State

## Project Reference

See: `.planning/workstreams/stage2b-lstm-version/PROJECT.md`

**Core value:** The cascade must still produce a single, well-calibrated bot probability per account while letting us test whether a sequence-model Stage 2b adds useful signal beyond the current AMR-inspired refinement path.
**Current focus:** Plan Phase 8 around an embedded-message LSTM Stage 2b variant that preserves the `z2` refinement contract beside the AMR baseline.

## Current Position
**Status:** Context gathered
**Current Phase:** Phase 8 - LSTM Stage 2b Foundation
**Last Activity:** 2026-04-16
**Last Activity Description:** Phase 8 context captured for the Stage 2b LSTM foundation

## Progress
**Phases Complete:** 0
**Current Plan:** Ready for planning

## Blockers/Concerns

- The existing Stage 2b path is implemented as an AMR-inspired delta refiner over Stage 2a logits, so the LSTM variant needs a clear compatibility contract instead of an ad hoc branch.
- Sequence modeling introduces preprocessing and batching decisions that can quietly affect reproducibility if they are not pinned down early.
- This milestone must preserve the AMR baseline so any LSTM result is comparable rather than anecdotal.

## Session Continuity
**Last Session:** 2026-04-16
**Stopped At:** Phase 8 context gathered; ready for planning
**Resume File:** .planning/workstreams/stage2b-lstm-version/phases/08-lstm-stage-2b-foundation/08-CONTEXT.md
