---
gsd_state_version: 1.0
milestone: v1.4
milestone_name: Twitter-Native Supervised Baseline
status: in_progress
stopped_at: Defining requirements
last_updated: "2026-04-18T00:00:00.000Z"
last_activity: 2026-04-18 — Milestone v1.4 started
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` and `.planning/ROADMAP.md`

**Core value:** The cascade must produce a single, well-calibrated bot probability per account while routing efficiently through stages and remaining interpretable when transferred out of domain.
**Current focus:** v1.4 — Twitter-Native Supervised Baseline

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-04-18 — Milestone v1.4 started

## Performance Metrics

**Latest transfer results (v1.3 Phase 12 live run):**

- BotSim-24 in-domain: `F1=0.9767`, `AUC=0.9992`
- TwiBot static: `F1=0.0`, `AUC=0.5964`
- TwiBot recalibrated: `F1=0.0`, `AUC=0.5879`
- Transfer verdict: `no_material_change`

**v1.4 target:**
- TwiBot-trained on TwiBot test: expected strong F1/AUC (platform-matched)

## Accumulated Context

### Decisions

Carried forward into v1.4:

- [2026-04-18] Twitter-native features required for TwiBot cascade — no Reddit→Twitter mapping, no imputing, no zero-fill
- [2026-04-18] Reddit-trained and TwiBot-trained systems stored as separate joblib artifacts
- [2026-04-18] Online novelty recalibration to be removed from Reddit cascade — does not improve results
- [2026-04-17] Full Twitter-native redesign and any TwiBot retraining remain out of scope for the Reddit cascade

### Deferred Items

| Category | Item | Status |
|----------|------|--------|
| testing | Full pytest green-suite blocked by Windows temp-dir cleanup permissions | deferred |
| cleanup | Stale pre-Phase-12 TwiBot artifacts at repo root | deferred |
| paper | Multi-seed ablation stability | deferred from v1.3 |
| paper | CalibratedClassifierCV on held-out calibration subset | deferred from v1.3 |
| research | True AMR graph parsing | deferred from v1.3 |

### Blockers/Concerns

- Windows friction is pytest tmp_path cleanup permissions only — production code unaffected
- TwiBot-20 data files (train.json, test.json) must be present locally for training and evaluation

## Session Continuity

Last session: 2026-04-18
Stopped at: Milestone v1.4 started, defining requirements
Resume file: None
