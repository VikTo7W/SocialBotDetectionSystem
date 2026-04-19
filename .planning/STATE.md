---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Phase 22 planned; next clean step is $gsd-execute-phase 22
last_updated: "2026-04-19T19:02:30.220Z"
last_activity: 2026-04-19 -- Phase 22 execution started
progress:
  total_phases: 4
  completed_phases: 0
  total_plans: 3
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` and `.planning/ROADMAP.md`

**Core value:** The cascade must produce a single, well-calibrated bot probability per account while routing efficiently through stages and remaining interpretable when transferred out of domain.
**Current focus:** Phase 22 — pipeline-surface-consolidation

## Current Position

Phase: 22 (pipeline-surface-consolidation) — EXECUTING
Plan: 1 of 3
Status: Executing Phase 22
Last activity: 2026-04-19 -- Phase 22 execution started

## Progress Bar

```text
v1.6: [ ] Phase 22  [ ] Phase 23  [ ] Phase 24  [ ] Phase 25
```

## Accumulated Context

### Decisions

Carried forward from v1.5:

- [2026-04-18] LSTM Stage 2b path removed from the maintained system - AMR embedding delta-logit only
- [2026-04-18] Bayesian threshold calibration reduced to a single trial
- [2026-04-18] Training artifacts moved to `trained_system_botsim.joblib` and `trained_system_twibot.joblib`
- [2026-04-18] Three maintained evaluation entry points replace the older mixed evaluation scripts
- [2026-04-19] Shared cascade orchestration lives in `CascadePipeline`, with temporary compatibility behavior still present in `botdetector_pipeline.py`
- [2026-04-19] Phase 19 was closed with a user-accepted deferment for the long-running local `train_twibot.py` artifact build
- [2026-04-19] Phase 20 added maintained evaluation entry points plus a standalone Table 5 driver rooted at `paper_outputs/` and `tables/table5_cross_dataset.tex`
- [2026-04-19] Phase 21 rewrote README/VERSION around the maintained v1.5 modular architecture, feature-stage mapping, and reproduction contract

New in v1.6:

- [2026-04-19] The next milestone prioritizes fewer maintained files and fewer overlapping internal surfaces over compatibility layering
- [2026-04-19] Pipeline, feature extraction, and dataset I/O are the main structural consolidation targets
- [2026-04-19] A final short lowercase comment pass is part of the milestone scope, but comments must stay low-noise and genuine

### Deferred Items

| Category | Item | Status |
|----------|------|--------|
| testing | Full pytest green-suite blocked by Windows temp-dir cleanup permissions | deferred |
| retraining | Fresh `trained_system_twibot.joblib` still needs a successful full local rerun | deferred by user |
| cleanup | Stale pre-Phase-12 TwiBot artifacts at repo root | deferred |
| paper | Multi-seed ablation stability | deferred |
| research | True AMR graph parsing | deferred |

### Blockers/Concerns

- Windows friction is still pytest tmp_path cleanup permissions plus long-running local TwiBot retraining/runtime debugging
- TwiBot-20 data files (`train.json`, `dev.json`, `test.json`) must be present locally for training and evaluation
- Structural cleanup must preserve split discipline, routing behavior, and maintained external artifact/output contracts

## Session Continuity

Last session: 2026-04-19
Stopped at: Phase 22 planned; next clean step is $gsd-execute-phase 22
Resume file: .planning/phases/22-pipeline-surface-consolidation/22-03-PLAN.md
