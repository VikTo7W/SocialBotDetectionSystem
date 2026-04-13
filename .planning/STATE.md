---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Feature Leakage Audit & Fix
status: planning
stopped_at: "Checkpoint: 05-02 Task 2 — awaiting user to run python main.py"
last_updated: "2026-04-13T21:03:05.546Z"
last_activity: 2026-04-12 — Roadmap created for v1.1 (Phases 5-7)
progress:
  total_phases: 3
  completed_phases: 1
  total_plans: 2
  completed_plans: 2
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-12)

**Core value:** The cascade must produce a single, well-calibrated bot probability per account — routing efficiently through stages while catching sophisticated bots that simple models miss.
**Current focus:** Phase 5 — Leakage Fix and Baseline Retrain (ready to plan)

## Current Position

Phase: 5 of 7 (Leakage Fix and Baseline Retrain)
Plan: —
Status: Ready to plan
Last activity: 2026-04-12 — Roadmap created for v1.1 (Phases 5-7)

Progress: [░░░░░░░░░░] 0%

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

### Pending Todos

None yet.

### Blockers/Concerns

- Stage 2a AUC is 97-100% due to confirmed leakage: username/profile strings in embedding pool and text_field="profile" in AMR extractor — Phase 5 addresses this
- Meta-learners (meta12, meta123) were trained on leaky Stage 2a outputs and must be fully retrained after the fix — not just Stage 2a

## Session Continuity

Last session: 2026-04-13T21:03:00.655Z
Stopped at: Checkpoint: 05-02 Task 2 — awaiting user to run python main.py
Resume file: None
