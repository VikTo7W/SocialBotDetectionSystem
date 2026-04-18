---
gsd_state_version: 1.0
milestone: v1.5
milestone_name: Unified Modular Codebase
status: in_progress
stopped_at: "Defining requirements"
last_updated: "2026-04-18T00:00:00.000Z"
last_activity: 2026-04-18 -- Milestone v1.5 started
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` and `.planning/ROADMAP.md`

**Core value:** The cascade must produce a single, well-calibrated bot probability per account while routing efficiently through stages and remaining interpretable when transferred out of domain.
**Current focus:** v1.5 — Unified Modular Codebase (defining requirements)

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-04-18 -- Milestone v1.5 started

## Accumulated Context

### Decisions

Carried forward from v1.4:

- [2026-04-18] Twitter-native features required for TwiBot cascade - no Reddit->Twitter mapping, no imputing, no zero-fill
- [2026-04-18] Reddit-trained and TwiBot-trained systems stored as separate joblib artifacts
- [2026-04-18] Online novelty recalibration removed from the maintained Reddit cascade path

New in v1.5:

- [2026-04-18] LSTM Stage 2b path removed from Reddit system — AMR embedding delta-logit only
- [2026-04-18] Bayesian threshold calibration reduced to single trial — multiple trials produce identical results
- [2026-04-18] Codebase unified into dataset-parameterized architecture; no separate Reddit/TwiBot file sets

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

## Session Continuity

Last session: 2026-04-18
Stopped at: Milestone v1.5 started — requirements definition in progress
Resume file: None
