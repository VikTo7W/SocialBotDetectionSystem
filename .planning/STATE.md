---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Twibot System Version
status: in_progress
stopped_at: Phase 11 complete, ready to plan Phase 12
last_updated: "2026-04-18T12:30:00.000Z"
last_activity: 2026-04-18 -- Phase 11 complete (4/4 UAT passed)
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` and `.planning/workstreams/milestone/ROADMAP.md`

**Core value:** The cascade must produce a single, well-calibrated bot probability per account while routing efficiently through stages and remaining interpretable when transferred out of domain.
**Current focus:** Defining and planning v1.3 Twibot System Version

## Current Position

Phase: 12 of 13 — Fresh Transfer Evidence and Paper Outputs
Plan: Not started
Status: Ready to plan
Last activity: 2026-04-18 — Phase 11 complete (4/4 UAT passed)

Progress: Phase 11 complete. TwiBot evaluation path hardened: output_dir routing, stable artifact filenames, documented canonical command, TWIBOT_COMPARISON_PATH env-var override. Phase 12 is next.

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
- [2026-04-17] Phase 9 recalibration updates only novelty thresholds: `n1_max_for_exit`, `n2_trigger`, and `novelty_force_stage3`

### Deferred Items

Carried forward context from v1.2 close:

| Category | Item | Status |
|----------|------|--------|
| verification | real TwiBot comparison artifact regeneration | deferred |
| verification | final pytest/runtime verification in a cleaner environment | deferred |
| planning | v1.2 milestone audit | deferred carry-over |
| planning | stale Phase 8 verification artifact reconciliation if needed | deferred carry-over |

### Blockers/Concerns

- Windows friction is pytest tmp_path cleanup permissions only — production code has zero tempfile usage (confirmed Phase 11)
- Fresh TwiBot outputs still need to be generated for final evidence (Phase 12 scope)
- metrics_twibot20_comparison.json does not exist yet — Phase 12 must generate it via a live run

## Session Continuity

Last session: 2026-04-18
Stopped at: Phase 11 complete, ready to plan Phase 12
Resume file: None
