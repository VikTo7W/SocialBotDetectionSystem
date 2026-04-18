---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Twibot System Version
status: in_progress
stopped_at: "Phase 13 complete — VERSION.md and README.md authored; v1.3 ready to close"
last_updated: "2026-04-18T17:00:00.000Z"
last_activity: 2026-04-18
progress:
  total_phases: 3
  completed_phases: 3
  total_plans: 6
  completed_plans: 6
  percent: 100
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` and `.planning/workstreams/milestone/ROADMAP.md`

**Core value:** The cascade must produce a single, well-calibrated bot probability per account while routing efficiently through stages and remaining interpretable when transferred out of domain.
**Current focus:** Phase 13 packaging and release documentation

## Current Position

Phase: 13 - System Version Packaging and Release Docs
Plan: 13-02 complete
Status: Complete — all 3 phases done, milestone ready to close
Last activity: 2026-04-18 - VERSION.md and README.md authored; all Phase 13 plans complete

Progress: All 3 v1.3 phases complete (6/6 plans). VERSION.md names the v1.3 release contract. README.md has end-to-end reproduction guide, caveats, and limitations. v1.3 milestone is ready to close.

## Performance Metrics

**Latest transfer check:**

- Fresh Phase 12 static run: `F1 = 0.0`, `AUC = 0.5964`
- Fresh Phase 12 recalibrated run: `F1 = 0.0`, `AUC = 0.5879`
- Fresh interpretation: `no_material_change`
- Recalibration increased Stage 3 usage substantially on TwiBot, but did not improve F1 and slightly reduced AUC in the fresh run

## Accumulated Context

### Decisions

Recent decisions affecting current work:

- [2026-04-17] Phase 8 scope revised: the original Stage 1 Twitter mapping is no longer frozen
- [2026-04-17] `subreddit_list` may map from TwiBot `domain` when topical breadth is the better Reddit analog
- [2026-04-17] `comment_num_1` may be reassigned away from RT count if non-RT or non-MT tweets better capture authored contribution
- [2026-04-17] Missingness-aware handling is allowed for systematically absent TwiBot fields, especially timestamp-derived Stage 2 features
- [2026-04-17] Full Twitter-native redesign and any TwiBot retraining remain out of scope for v1.2
- [2026-04-17] Phase 9 recalibration updates only novelty thresholds: `n1_max_for_exit`, `n2_trigger`, and `novelty_force_stage3`

### Deferred Items

Current deferred items:

| Category | Item | Status |
|----------|------|--------|
| verification | full pytest/runtime verification in a cleaner environment | pending |
| planning | v1.2 milestone audit | deferred carry-over |
| planning | stale Phase 8 verification artifact reconciliation if needed | deferred carry-over |

### Blockers/Concerns

- Verification inside this environment is still partially affected by Windows temp and cache-permission issues
- Phase 13 should package the live Phase 12 artifacts rather than the older root-level TwiBot outputs
- The fresh evidence shows recalibration changes routing behavior but not final F1, which should be called out explicitly in release docs

## Session Continuity

Last session: 2026-04-18
Stopped at: Phase 12 completed with fresh artifacts; next clean step is `$gsd-plan-phase 13`
Resume file: None
