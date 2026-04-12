---
gsd_state_version: 1.0
milestone: v1.1
milestone_name: Feature Leakage Audit & Fix
status: not_started
stopped_at: ""
last_updated: "2026-04-12T00:00:00.000Z"
last_activity: "2026-04-12 — Milestone v1.1 started"
progress:
  total_phases: 0
  completed_phases: 0
  total_plans: 0
  completed_plans: 0
  percent: 0
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-04-12)

**Core value:** The cascade must produce a single, well-calibrated bot probability per account — routing efficiently through stages while catching sophisticated bots that simple models miss.
**Current focus:** Phase: Not started (defining requirements)

## Current Position

Phase: Not started (defining requirements)
Plan: —
Status: Defining requirements
Last activity: 2026-04-12 — Milestone v1.1 started

Progress: [░░░░░░░░░░] 0%

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- Bayesian optimization chosen for threshold search (sample-efficient for high-dimensional threshold space)
- AMR is a delta-logit updater (Option C) — not a full second classifier
- Logistic regression for meta-learners — interpretable, calibrated, resistant to overfitting on small S2
- S1/S2/S3 three-way split — S3 is fully held out; calibration runs on S2 only
- [Phase 04-api]: Eager module-level joblib.load in addition to lifespan — Starlette 0.52.1 TestClient without with-block does not trigger lifespan

### Pending Todos

None yet.

### Blockers/Concerns

- Stage 2a+ evaluation metrics suspiciously near 97-100%; suspected cause: profile/username text in Stage 2a features encoding label directly (bots have AI-generated descriptions, humans have organic descriptions)
- AMR refiner also uses profile text (text_field="profile"), compounding the issue
