---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: executing
stopped_at: Phase 19 planned; next clean step is `$gsd-execute-phase 19`
last_updated: "2026-04-19T13:25:56.125Z"
last_activity: 2026-04-19 -- Phase 19 execution started
progress:
  total_phases: 8
  completed_phases: 5
  total_plans: 22
  completed_plans: 18
  percent: 82
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` and `.planning/ROADMAP.md`

**Core value:** The cascade must produce a single, well-calibrated bot probability per account while routing efficiently through stages and remaining interpretable when transferred out of domain.
**Current focus:** Phase 19 — training-entry-points-and-fresh-model-retraining

## Current Position

Phase: 19 (training-entry-points-and-fresh-model-retraining) — EXECUTING
Plan: 1 of 4
Status: Executing Phase 19
Last activity: 2026-04-19 -- Phase 19 execution started

## Progress Bar

```text
v1.5: [x] Phase 17  [x] Phase 18  [ ] Phase 19  [ ] Phase 20  [ ] Phase 21
```

## Accumulated Context

### Decisions

Carried forward from v1.4:

- [2026-04-18] Twitter-native features required for TwiBot cascade - no Reddit->Twitter mapping, no imputing, no zero-fill
- [2026-04-18] Reddit-trained and TwiBot-trained systems stored as separate joblib artifacts
- [2026-04-18] Online novelty recalibration removed from the maintained Reddit cascade path

New in v1.5:

- [2026-04-18] LSTM Stage 2b path removed from the maintained system - AMR embedding delta-logit only
- [2026-04-18] Bayesian threshold calibration reduced to a single trial
- [2026-04-18] Codebase will be unified into dataset-parameterized architecture with shared features and pipeline layers
- [2026-04-18] Training artifacts will move to `trained_system_botsim.joblib` and `trained_system_twibot.joblib`
- [2026-04-18] Three maintained evaluation entry points will replace the current mixed evaluation scripts
- [2026-04-19] Shared cascade orchestration now lives in `CascadePipeline`, with compatibility wrappers preserved temporarily in `botdetector_pipeline.py`

### Deferred Items

| Category | Item | Status |
|----------|------|--------|
| testing | Full pytest green-suite blocked by Windows temp-dir cleanup permissions | deferred |
| cleanup | Stale pre-Phase-12 TwiBot artifacts at repo root | deferred |
| paper | Multi-seed ablation stability | deferred from v1.3 |
| research | True AMR graph parsing | deferred from v1.3 |

### Blockers/Concerns

- Windows friction is pytest tmp_path cleanup permissions only - production code unaffected
- TwiBot-20 data files (`train.json`, `dev.json`, `test.json`) must be present locally for training and evaluation
- Fresh retraining in Phase 19 requires both BotSim-24 and TwiBot-20 data to be available

## Session Continuity

Last session: 2026-04-19
Stopped at: Phase 19 planned; next clean step is `$gsd-execute-phase 19`
Resume file: .planning/phases/19-training-entry-points-and-fresh-model-retraining/19-RESEARCH.md
