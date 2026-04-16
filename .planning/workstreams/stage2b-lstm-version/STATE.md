---
gsd_state_version: 1.0
workstream: stage2b-lstm-version
milestone: v1.2.1
milestone_name: Stage 2b LSTM Variant
created: 2026-04-16
status: ready_to_execute
stopped_at: Phase 8 planned; ready for execution
last_updated: "2026-04-16T20:20:00Z"
---

# Project State

## Project Reference

See: `.planning/workstreams/stage2b-lstm-version/PROJECT.md`

**Core value:** The cascade must still produce a single, well-calibrated bot probability per account while letting us test whether a sequence-model Stage 2b adds useful signal beyond the current AMR-inspired refinement path.
**Current focus:** Execute Phase 8 to establish the LSTM Stage 2b sequence contract and fixture-backed `z2`-compatible prototype.

## Current Position
**Status:** Planned
**Current Phase:** Phase 8 - LSTM Stage 2b Foundation
**Last Activity:** 2026-04-16
**Last Activity Description:** Phase 8 plans and verification criteria created

## Progress
**Phases Complete:** 0
**Current Plan:** 08-01 and 08-02 ready for execution

## Blockers/Concerns

- The existing Stage 2b path is implemented as an AMR-inspired delta refiner over Stage 2a logits, so the LSTM variant needs a clear compatibility contract instead of an ad hoc branch.
- Sequence modeling introduces preprocessing and batching decisions that can quietly affect reproducibility if they are not pinned down early.
- This milestone must preserve the AMR baseline so any LSTM result is comparable rather than anecdotal.

## Session Continuity
**Last Session:** 2026-04-16
**Stopped At:** Phase 8 planned; ready for execution
**Resume File:** .planning/workstreams/stage2b-lstm-version/phases/08-lstm-stage-2b-foundation/08-01-PLAN.md
