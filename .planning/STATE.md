---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Feature Leakage Audit & Fix
status: in-progress
stopped_at: "Phase 6 plan 01 complete — FEAT-04 implemented; ready to execute 06-02-PLAN.md (retrain to v12)"
last_updated: "2026-04-15T00:00:00Z"
last_activity: 2026-04-15 — Phase 6 planned; ABL-01/ABL-03 dropped (redundant with existing evaluate_s3 output)
progress:
  total_phases: 3
  completed_phases: 1
  total_plans: 4
  completed_plans: 2
  percent: 33
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-12)

**Core value:** The cascade must produce a single, well-calibrated bot probability per account — routing efficiently through stages while catching sophisticated bots that simple models miss.
**Current focus:** Phase 6 — Ablation Infrastructure and Differentiator Features (ready to execute)

## Current Position

Phase: 6 of 7 (Ablation Infrastructure and Differentiator Features) — IN PROGRESS
Plan: 01 of 02 (06-01 complete; 06-02 retrain pending)
Status: Phase 6 plan 01 complete — FEAT-04 implemented, 397-dim output; retrain to v12 next
Last activity: 2026-04-15 — 06-01 executed: FEAT-04 cross-message cosine similarity features added at indices 395-396

Progress: [███░░░░░░░] 33%

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: —
- Total execution time: —

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

*Updated after each plan completion*
| Phase 05 P01 | 30 | 3 tasks | 6 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [v1.0]: Eager module-level joblib.load in api.py — Starlette TestClient without with-block does not trigger lifespan
- [v1.1 research]: Both leakage paths (features_stage2.py:50-53 and botdetector_pipeline.py:539) must be fixed atomically in the same commit and retrain run to avoid residual leakage
- [v1.1 research]: character_setting column must be dropped at load time in build_account_table — retained currently with only a comment warning
- [v1.1 research]: All ablation paper tables must report S3 metrics only — S2 is the Optuna calibration set
- [Phase 05]: AMR anchor switched from profile field to most-recent message text; text_field parameter removed entirely
- [Phase 05]: character_setting dropped from build_account_table at load time (not just commented)
- [Phase 05]: Feature vector grows from (N,391) to (N,395) with cv_intervals, char_len_mean, char_len_std, hour_entropy
- [Phase 05-02]: conftest.py minimal_system fixture uses extract_amr_embeddings_for_accounts(S2, FeatureConfig(...), embedder) — no more raw profile text encoding
- [Phase 05-02]: AUC 0.97-0.98 on BotSim-24 S3 is legitimate content discrimination (bots: generic news summaries; humans: specific headlines) — not residual leakage
- [Phase 05-02]: results_v10.json not created — v1.0 model incompatible with 395-dim extractor; v1.0 metrics will be retrieved from git history in Phase 7
- [Phase 05-02]: ROADMAP criterion "AUC below 90%" was overspecified for BotSim-24; leakage removal confirmed by code inspection, not AUC threshold
- [Phase 06 planning]: ABL-01 and ABL-03 dropped — predict_system() already runs all stages on all accounts unconditionally; evaluate_s3() already reports p1/p12/p_final on full test set; force-routing adds nothing
- [Phase 06 planning]: Feature vector grows 395→397 with FEAT-04 (cross_msg_sim_mean at index 395, near_dup_frac at index 396)
- [Phase 06-01]: NormalizedFakeEmbedder must be defined locally in test files — conftest.py is pytest-injected, not directly importable as a module
- [Phase 06-01]: FEAT-04 defaults to 0.0 for accounts with 0 or 1 messages; near-dup threshold = 0.9 (_NEAR_DUP_SIM_THRESHOLD constant)

### Pending Todos

None yet.

### Blockers/Concerns

- [RESOLVED Phase 05] Stage 2a AUC was 97-100% due to confirmed leakage: username/profile strings in embedding pool and text_field="profile" in AMR extractor — fixed in Phase 5, retrain complete
- [DEFERRED to Phase 07] results_v10.json not created — v1.0 model incompatible with 395-dim extractor; v1.0 metrics to be retrieved from git history for leakage audit table

## Session Continuity

Last session: 2026-04-15T00:48:00Z
Stopped at: 06-01-PLAN.md complete — FEAT-04 implemented (397-dim output); ready to execute 06-02-PLAN.md (retrain to v12)
Resume file: None
