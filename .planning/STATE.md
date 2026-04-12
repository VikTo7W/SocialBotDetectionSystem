---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Feature Leakage Audit & Fix
status: ready_to_plan
stopped_at: ""
last_updated: "2026-04-12T00:00:00.000Z"
last_activity: "2026-04-12 — Roadmap created for v1.1 (Phases 5-7)"
progress:
  total_phases: 3
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
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

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [v1.0]: Eager module-level joblib.load in api.py — Starlette TestClient without with-block does not trigger lifespan
- [v1.1 research]: Both leakage paths (features_stage2.py:50-53 and botdetector_pipeline.py:539) must be fixed atomically in the same commit and retrain run to avoid residual leakage
- [v1.1 research]: character_setting column must be dropped at load time in build_account_table — retained currently with only a comment warning
- [v1.1 research]: All ablation paper tables must report S3 metrics only — S2 is the Optuna calibration set

### Pending Todos

None yet.

### Blockers/Concerns

- Stage 2a AUC is 97-100% due to confirmed leakage: username/profile strings in embedding pool and text_field="profile" in AMR extractor — Phase 5 addresses this
- Meta-learners (meta12, meta123) were trained on leaky Stage 2a outputs and must be fully retrained after the fix — not just Stage 2a

## Session Continuity

Last session: 2026-04-12
Stopped at: Roadmap created — Phase 5 ready to plan
Resume file: None
