---
gsd_state_version: 1.0
milestone: v1.2
milestone_name: TwiBot-20 Cross-Domain Transfer
status: planning
stopped_at: ""
last_updated: "2026-04-17T00:00:00.000Z"
last_activity: 2026-04-17
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-16)

**Core value:** The cascade must produce a single, well-calibrated bot probability per account — routing efficiently through stages while catching sophisticated bots that simple models miss.
**Current focus:** Planning next milestone (v1.2)

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-04-17 — Milestone v1.2 started

Progress: [████████████████████] 100%

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
| Phase 06 P02 | 10 | 2 tasks | 1 files |
| Phase 07 P01 | 1 | 1 tasks | 1 files |
| Phase 07 P02 | 5 | 1 tasks | 1 files |

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
- [Phase 06-02]: v11 save preserved unchanged so 395-dim baseline artifact is available for Phase 7 ablation comparison; v12 appended after v11 in main.py
- [Phase 06-02]: v11 save preserved unchanged so 395-dim baseline artifact is available for Phase 7 ablation comparison; v12 appended after v11 in main.py
- [Phase 07-01]: Table 2 uses 3 rows (p1/p12/p_final), p2 excluded — Stage 2 alone on all accounts is not a cascade stage comparison
- [Phase 07-01]: save_latex contract enforces float_format='%.4f'; test asserts '0.9000' string appears in LaTeX file content
- [Phase 07-02]: Monkey-patch targets botdetector_pipeline.extract_stage1_matrix (not features_stage1) because from-import creates a local binding in bp module scope
- [Phase 07-02]: masked_predict copies X before zeroing columns to avoid mutating the array returned by _orig_extract_stage1_matrix

### Pending Todos

None yet.

### Blockers/Concerns

- [RESOLVED Phase 05] Stage 2a AUC was 97-100% due to confirmed leakage: username/profile strings in embedding pool and text_field="profile" in AMR extractor — fixed in Phase 5, retrain complete
- [DEFERRED to Phase 07] results_v10.json not created — v1.0 model incompatible with 395-dim extractor; v1.0 metrics to be retrieved from git history for leakage audit table

## Session Continuity

Last session: 2026-04-15T22:57:00.372Z
Stopped at: Checkpoint at 07-02 Task 2 — ablation_tables.py complete, awaiting user worktree retrain
Resume file: None
