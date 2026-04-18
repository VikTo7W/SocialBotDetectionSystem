---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Not started
stopped_at: Phase 17 context gathered
last_updated: "2026-04-18T22:24:07.772Z"
last_activity: 2026-04-18 -- Roadmap created; ready to begin Phase 17
progress:
  total_phases: 8
  completed_phases: 3
  total_plans: 8
  completed_plans: 8
  percent: 100
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` and `.planning/ROADMAP.md`

**Core value:** The cascade must produce a single, well-calibrated bot probability per account while routing efficiently through stages and remaining interpretable when transferred out of domain.
**Current focus:** v1.5 — Unified Modular Codebase (Phase 17 next)

## Current Position

Phase: 17 — Shared Feature Extraction Module
Plan: —
Status: Not started
Last activity: 2026-04-18 -- Roadmap created; ready to begin Phase 17

## Progress Bar

```
v1.5: [ ] Phase 17  [ ] Phase 18  [ ] Phase 19  [ ] Phase 20  [ ] Phase 21
```

## Accumulated Context

### Decisions

Carried forward from v1.4:

- [2026-04-18] Twitter-native features required for TwiBot cascade — no Reddit->Twitter mapping, no imputing, no zero-fill
- [2026-04-18] Reddit-trained and TwiBot-trained systems stored as separate joblib artifacts
- [2026-04-18] Online novelty recalibration removed from the maintained Reddit cascade path

New in v1.5:

- [2026-04-18] LSTM Stage 2b path removed from Reddit system — AMR embedding delta-logit only
- [2026-04-18] Bayesian threshold calibration reduced to single trial — multiple trials produce identical results
- [2026-04-18] Codebase unified into dataset-parameterized architecture; no separate Reddit/TwiBot file sets
- [2026-04-18] Training artifacts renamed: trained_system_botsim.joblib and trained_system_twibot.joblib
- [2026-04-18] Three evaluation entry points: eval_botsim_native.py, eval_reddit_twibot_transfer.py, eval_twibot_native.py

### Deferred Items

| Category | Item | Status |
|----------|------|--------|
| testing | Full pytest green-suite blocked by Windows temp-dir cleanup permissions | deferred |
| cleanup | Stale pre-Phase-12 TwiBot artifacts at repo root | deferred |
| paper | Multi-seed ablation stability | deferred from v1.3 |
| research | True AMR graph parsing | deferred from v1.3 |

### Blockers/Concerns

- Windows friction is pytest tmp_path cleanup permissions only — production code unaffected
- TwiBot-20 data files (`train.json`, `dev.json`, `test.json`) must be present locally for training and evaluation
- Fresh retraining in Phase 19 requires both BotSim-24 and TwiBot-20 data to be available

## Session Continuity

Last session: 2026-04-18T22:24:07.768Z
Stopped at: Phase 17 context gathered
Resume file: .planning/phases/17-shared-feature-extraction-module/17-CONTEXT.md
