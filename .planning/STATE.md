---
gsd_state_version: 1.0
milestone: v1.3
milestone_name: Twibot System Version
status: complete
stopped_at: v1.3 milestone closed — all phases and plans complete, archived, tagged
last_updated: "2026-04-18T17:00:00.000Z"
last_activity: 2026-04-18 -- Phase 13 complete (VERSION.md and README.md authored)
---

# Project State

## Project Reference

See: `.planning/PROJECT.md` and `.planning/workstreams/milestone/ROADMAP.md`

**Core value:** The cascade must produce a single, well-calibrated bot probability per account while routing efficiently through stages and remaining interpretable when transferred out of domain.
**Current focus:** Planning next milestone

## Current Position

Phase: 13 of 13 — complete
Plan: All plans complete
Status: v1.3 milestone closed and archived
Last activity: 2026-04-18 — v1.3 archived to .planning/milestones/v1.3-ROADMAP.md

Progress: All 13 phases complete across v1.0–v1.3. v1.3 closed with VERSION.md release contract, README.md reproduction guide, and live TwiBot evidence (no_material_change verdict). Run /gsd-new-milestone to start v1.4.

## Performance Metrics

**Latest transfer results (Phase 12 live run):**

- BotSim-24 in-domain: `F1=0.9767`, `AUC=0.9992`
- TwiBot static: `F1=0.0`, `AUC=0.5964`
- TwiBot recalibrated: `F1=0.0`, `AUC=0.5879`
- Transfer verdict: `no_material_change` (recalibration does not materially improve zero-shot transfer)

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
- TwiBot F1=0.0 across both conditions — the zero-shot transfer is weak; Phase 13 docs must clearly state this as a known limitation
- Pytest cache warnings persist in this environment (permission-constrained .pytest_cache creation) but targeted assertions pass

## Session Continuity

Last session: 2026-04-18
Stopped at: Phase 12 complete, ready to plan Phase 13
Resume file: None
