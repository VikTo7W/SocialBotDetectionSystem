---
gsd_state_version: 1.0
workstream: stage2b-lstm-version
milestone: v1.2.1
milestone_name: Stage 2b LSTM Variant
created: 2026-04-16
status: ready_to_execute
stopped_at: Phase 10 plans written; ready for execution
last_updated: "2026-04-16T21:47:00Z"
---

# Project State

## Project Reference

See: `.planning/workstreams/stage2b-lstm-version/PROJECT.md`

**Core value:** The cascade must still produce a single, well-calibrated bot probability per account while letting us test whether a sequence-model Stage 2b adds useful signal beyond the current AMR-inspired refinement path.
**Current focus:** Execute Phase 10 to produce the real BotSim S3 AMR-vs-LSTM comparison, compact report, and reusable tables.

## Current Position
**Status:** Planned
**Current Phase:** Phase 10 - Evaluation and Baseline Comparison
**Last Activity:** 2026-04-16
**Last Activity Description:** Phase 10 plans written for real S3 comparison evidence, reusable tables, and final recommendation output

## Progress
**Phases Complete:** 2
**Current Plan:** Ready for execution

## Blockers/Concerns

- The LSTM variant is now integrated through both `train_system()` and `predict_system()`.
- Phase 10 must compare AMR and LSTM on the real BotSim S3 path, not just synthetic or fixture-backed evidence.
- The final recommendation should remain neutral and evidence-driven; AMR may still be the outcome.
- Planning assumed no separate research phase was needed because the comparison surfaces (`main.py`, `evaluate.py`, `ablation_tables.py`) are already local and well-understood from prior work.

## Session Continuity
**Last Session:** 2026-04-16
**Stopped At:** Phase 10 plans written; ready for execution
**Resume File:** .planning/workstreams/stage2b-lstm-version/phases/10-evaluation-and-baseline-comparison/10-01-PLAN.md
