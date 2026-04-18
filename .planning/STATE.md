---
gsd_state_version: 1.0
milestone: v1.4
milestone_name: Twitter-Native Supervised Baseline
status: complete
stopped_at: "Phase 16 complete - v1.4 shipped with comparative paper outputs and Reddit-transfer cleanup"
last_updated: "2026-04-18T16:45:00.000Z"
last_activity: 2026-04-18 -- Phase 16 completed and v1.4 shipped
progress:
  total_phases: 3
  completed_phases: 3
  total_plans: 8
  completed_plans: 8
  percent: 100
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` and `.planning/ROADMAP.md`

**Core value:** The cascade must produce a single, well-calibrated bot probability per account while routing efficiently through stages and remaining interpretable when transferred out of domain.
**Current focus:** v1.4 shipped - ready for next milestone or follow-up work

## Current Position

Phase: 16 (comparative-paper-outputs-and-reddit-cleanup) - COMPLETE
Plan: 16-03 complete
Status: Complete - all 3 phases done, milestone shipped
Last activity: 2026-04-18 -- Phase 16 completed and v1.4 shipped

## Performance Metrics

**Maintained comparison contract:**

- BotSim-24 in-domain: `F1=0.9767`, `AUC=0.9992`
- TwiBot Reddit transfer baseline: `results_twibot20_reddit_transfer.json` + `metrics_twibot20_reddit_transfer.json`
- TwiBot native baseline: `results_twibot20_native.json` + `metrics_twibot20_native.json`
- Table 5 comparison artifact: `metrics_twibot20_reddit_vs_native.json`

**v1.4 outcome:**

- Reddit transfer and TwiBot-native paths are now documented and maintained as separate artifacts
- Online novelty recalibration is retired from the maintained Reddit-transfer story

## Accumulated Context

### Decisions

Completed in v1.4:

- [2026-04-18] Twitter-native features required for TwiBot cascade - no Reddit->Twitter mapping, no imputing, no zero-fill
- [2026-04-18] Reddit-trained and TwiBot-trained systems stored as separate joblib artifacts
- [2026-04-18] Online novelty recalibration removed from the maintained Reddit cascade path
- [2026-04-17] Full Twitter-native redesign remains out of scope for the Reddit cascade

### Deferred Items

| Category | Item | Status |
|----------|------|--------|
| testing | Full pytest green-suite blocked by Windows temp-dir cleanup permissions | deferred |
| cleanup | Stale pre-Phase-12 TwiBot artifacts at repo root | deferred |
| paper | Multi-seed ablation stability | deferred from v1.3 |
| paper | CalibratedClassifierCV on held-out calibration subset | deferred from v1.3 |
| research | True AMR graph parsing | deferred from v1.3 |

### Blockers/Concerns

- Windows friction is pytest tmp_path cleanup permissions only - production code unaffected
- TwiBot-20 data files (`train.json`, `dev.json`, `test.json`) must be present locally for training and evaluation

## Session Continuity

Last session: 2026-04-18
Stopped at: Phase 16 complete - next clean step is milestone closeout or the next planned phase
Resume file: None
