---
workstream: twibot-intergration
gsd_state_version: 1.0
milestone: v1.2
milestone_name: TwiBot-20 Cross-Dataset Evaluation
status: in_progress
last_updated: "2026-04-16"
last_activity: 2026-04-16
---

# Project State

## Current Position

Phase: 8 — TwiBot-20 Data Loader
Plan: —
Status: Roadmap created, ready to plan Phase 8
Last activity: 2026-04-16 — Roadmap created, 3 phases defined (8–10)

## Progress
**Phases Complete:** 0 / 3
**Current Plan:** N/A

```
[                              ] 0%
Phase 8 → Phase 9 → Phase 10
```

## Accumulated Context

### Decisions

- [v1.2 scoping]: Zero-shot transfer only — BotSim-24-trained cascade runs on TwiBot-20 without retraining; measures raw cross-platform generalization
- [v1.2 data format]: test.json records contain `ID`, `profile` dict, `tweet` list of plain strings, `neighbor` dict or None, `domain` list, `label` string "0"/"1" — no separate edge.csv or label.csv
- [v1.2 edges]: Edges come from `neighbor.following` / `neighbor.follower` inside each test.json record; string Twitter IDs remapped to zero-indexed node_idx integers
- [v1.2 temporal]: Tweets are plain strings with no per-tweet timestamps — temporal features (cv_intervals, rate, delta_mean, delta_std, hour_entropy) will be zero for all TwiBot-20 accounts; this is expected and must be documented, not treated as an error
- [v1.2 clamping]: Stage 1 ratio clamping (cols 6–9 to [0.0, 50.0]) must happen in the TwiBot-20 inference path only — no changes to existing BotSim-24 code paths
- [v1.2 isolation]: NO changes to existing pipeline files (predict_system, evaluate_s3, extract_stage1_matrix, etc.); new files are twibot20_io.py and evaluate_twibot20.py; one function added to ablation_tables.py

### Pending Todos

- Plan Phase 8 (twibot20_io.py: loader + edge builder + validation)
- Plan Phase 9 (evaluate_twibot20.py: inference pipeline + clamping)
- Plan Phase 10 (metrics + generate_cross_dataset_table())

### Blockers/Concerns

None.

## Session Continuity
**Stopped At:** Roadmap created — ready for `/gsd-plan-phase 8`
**Resume File:** `.planning/workstreams/twibot-intergration/ROADMAP.md`
