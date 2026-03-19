# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-19)

**Core value:** The cascade must produce a single, well-calibrated bot probability per account — routing efficiently through stages while catching sophisticated bots that simple models miss.
**Current focus:** Phase 2 — Threshold Calibration

## Current Position

Phase: 2 of 4 (Threshold Calibration)
Plan: 1 of 2 in current phase
Status: In progress
Last activity: 2026-03-19 — Plan 02-01 complete: optuna 4.8.0 installed, tests/ scaffold created with conftest.py (minimal_system fixture) and 6 test stubs for calibrate_thresholds

Progress: [###░░░░░░░] 30%

## Performance Metrics

**Velocity:**
- Total plans completed: 0 (active phases)
- Average duration: -
- Total execution time: -

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| 1. Pipeline Integration | - | - | - |
| 2. Threshold Calibration | 1 completed | 3 min | 3 min |

**Recent Trend:**
- Last 5 plans: 02-01 (3 min)
- Trend: -

*Updated after each plan completion*

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Bayesian optimization chosen for threshold search (sample-efficient for high-dimensional threshold space)
- AMR is a delta-logit updater (Option C) — not a full second classifier
- Logistic regression for meta-learners — interpretable, calibrated, resistant to overfitting on small S2
- S1/S2/S3 three-way split — S3 is fully held out; calibration runs on S2 only
- FakeEmbedder with RandomState(42) for deterministic 384-dim test embeddings (avoids 90MB model load)
- monkeypatch botdetector_pipeline extract functions at module level to fix predict_system calling convention bug
- 50-account balanced synthetic DataFrame ensures StratifiedKFold(n_splits=5) works without class imbalance

### Pending Todos

None yet.

### Blockers/Concerns

- Current thresholds in StageThresholds are hardcoded defaults (e.g., s1_bot=0.98, n1_max_for_exit=3.0) — calibration will replace these
- AMR linearization is a stub (embedding approximation, not true AMR graph parsing) — documented as v2 work

## Session Continuity

Last session: 2026-03-19
Stopped at: Completed 02-01-PLAN.md — test scaffold installed (optuna 4.8.0, tests/, conftest.py, test_calibrate.py with 6 stubs). Next: Plan 02 implements calibrate.py.
Resume file: None
