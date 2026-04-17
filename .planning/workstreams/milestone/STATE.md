---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: TwiBot-20 Cross-Domain Transfer
status: in_progress
stopped_at: "Phase 8 complete — behavioral tweet parser and transfer adapter stabilized; ready for Phase 9 sliding-window recalibration"
last_updated: "2026-04-17T12:00:00.000Z"
last_activity: 2026-04-17
progress:
  total_phases: 3
  completed_phases: 1
  total_plans: 2
  completed_plans: 2
  percent: 33
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` and `.planning/workstreams/milestone/ROADMAP.md`

**Core value:** The cascade must produce a single, well-calibrated bot probability per account while routing efficiently through stages and remaining interpretable when transferred out of domain.
**Current focus:** Phase 8 transfer adapter stabilization and verification

## Current Position

Phase: 08 - Behavioral Tweet Parser and Transfer Adapter Stabilization
Plan: 2/2 complete
Status: Complete
Last activity: 2026-04-17 - Phase 8 verified: 101 tests pass, behavioral adapter stable

Progress: Phase 8 complete. Behavioral tweet parser (parse_tweet_types) and revised Stage 1 adapter verified. 101 tests pass. Ready for Phase 9 (sliding-window recalibration).

## Performance Metrics

**Latest transfer check:**

- Saved TwiBot evaluation predicts only 1 bot out of 1183 accounts at threshold 0.5
- `F1 = 0.0`
- `AUC = 0.4674`
- Stage 3 usage is near zero despite graph coverage

## Accumulated Context

### Decisions

Recent decisions affecting current work:

- [2026-04-17] Phase 8 scope revised: the original Stage 1 Twitter mapping is no longer frozen
- [2026-04-17] `subreddit_list` may map from TwiBot `domain` when topical breadth is the better Reddit analog
- [2026-04-17] `comment_num_1` may be reassigned away from RT count if non-RT or non-MT tweets better capture authored contribution
- [2026-04-17] Missingness-aware handling is allowed for systematically absent TwiBot fields, especially timestamp-derived Stage 2 features
- [2026-04-17] Full Twitter-native redesign and any TwiBot retraining remain out of scope for v1.2

### Pending Todos

- Rewrite the TwiBot transfer adapter under the revised Phase 8 scope
- Decide and implement the missingness strategy for timestamp-derived Stage 2 features
- Re-run TwiBot evaluation and compare against the saved collapsed baseline
- Update Phase 8 verification artifacts after the revised run

### Blockers/Concerns

- Current TwiBot zero-shot results are not acceptable under the saved adapter
- The old workstream state had become stale and understated completed implementation work
- Verification inside this environment may still be partially affected by Windows temp or process-permission issues

## Session Continuity

Last session: 2026-04-17
Stopped at: Phase 8 scope revision complete; ready for revised execution planning or direct implementation
Resume file: None
