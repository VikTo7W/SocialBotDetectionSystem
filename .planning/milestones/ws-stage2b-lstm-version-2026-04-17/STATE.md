---
gsd_state_version: 1.0
workstream: stage2b-lstm-version
milestone: v1.2.1
milestone_name: Stage 2b LSTM Variant
created: 2026-04-16
status: complete
stopped_at: Phase 10 executed; real AMR-vs-LSTM comparison and reusable tables recorded
last_updated: "2026-04-16T23:59:00Z"
---

# Project State

## Project Reference

See: `.planning/workstreams/stage2b-lstm-version/PROJECT.md`

**Core value:** The cascade must still produce a single, well-calibrated bot probability per account while letting us test whether a sequence-model Stage 2b adds useful signal beyond the current AMR-inspired refinement path.
**Current focus:** Milestone complete; Phase 10 captured the final AMR-vs-LSTM comparison and recommendation.

## Current Position
**Status:** Complete
**Current Phase:** Phase 10 - Evaluation and Baseline Comparison
**Last Activity:** 2026-04-16
**Last Activity Description:** Phase 10 executed; real S3 comparison, recommendation artifact, and reusable tables recorded

## Progress
**Phases Complete:** 3
**Current Plan:** None - milestone complete

## Blockers/Concerns

- The real S3 comparison recommended `lstm`, but with materially higher Stage 2b and Stage 3 routing, so operational cost should be considered before making it the permanent default.
- The reusable comparison outputs now live in the Phase 10 artifact JSON and the exported Stage 2b comparison tables.
- Planning assumed no separate research phase was needed because the comparison surfaces (`main.py`, `evaluate.py`, `ablation_tables.py`) were already local and well-understood, and execution validated that assumption.

## Session Continuity
**Last Session:** 2026-04-16
**Stopped At:** Milestone complete after Phase 10 execution
**Resume File:** .planning/workstreams/stage2b-lstm-version/phases/10-evaluation-and-baseline-comparison/10-VERIFICATION.md
