---
gsd_state_version: 1.0
workstream: stage2b-lstm-version
milestone: v1.2.1
milestone_name: Stage 2b LSTM Variant
created: 2026-04-16
status: ready_to_discuss
stopped_at: Milestone initialized; Phase 8 ready for discussion
last_updated: "2026-04-16T19:58:00Z"
---

# Project State

## Project Reference

See: `.planning/workstreams/stage2b-lstm-version/PROJECT.md`

**Core value:** The cascade must still produce a single, well-calibrated bot probability per account while letting us test whether a sequence-model Stage 2b adds useful signal beyond the current AMR-inspired refinement path.
**Current focus:** Define the Stage 2b LSTM foundation work and decide how it should fit beside the current AMR delta-refiner baseline.

## Current Position
**Status:** Milestone initialized
**Current Phase:** Phase 8 - LSTM Stage 2b Foundation
**Last Activity:** 2026-04-16
**Last Activity Description:** Workstream-local milestone, requirements, and roadmap created

## Progress
**Phases Complete:** 0
**Current Plan:** Ready for discussion

## Blockers/Concerns

- The existing Stage 2b path is implemented as an AMR-inspired delta refiner over Stage 2a logits, so the LSTM variant needs a clear compatibility contract instead of an ad hoc branch.
- Sequence modeling introduces preprocessing and batching decisions that can quietly affect reproducibility if they are not pinned down early.
- This milestone must preserve the AMR baseline so any LSTM result is comparable rather than anecdotal.

## Session Continuity
**Last Session:** 2026-04-16
**Stopped At:** Milestone initialized; Phase 8 ready for discussion
**Resume File:** .planning/workstreams/stage2b-lstm-version/ROADMAP.md
