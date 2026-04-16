---
workstream: twibot-intergration
milestone: v1.2
milestone_name: TwiBot-20 Cross-Dataset Evaluation
created: "2026-04-16"
phase_range: "8-10"
---

# Roadmap: v1.2 TwiBot-20 Cross-Dataset Evaluation

**Goal:** Demonstrate cross-platform robustness of the BotSim-24-trained cascade on TwiBot-20 Twitter data (zero-shot transfer), generating paper-ready metrics for a cross-dataset robustness section.

**Granularity:** standard
**Coverage:** 7/7 requirements mapped

## Phases

- [ ] **Phase 8: TwiBot-20 Data Loader** — Load test.json into BotSim-24-compatible DataFrame with edge builder and validation
- [ ] **Phase 9: Zero-Shot Inference Pipeline** — Run trained_system_v12.joblib on TwiBot-20 accounts with Stage 1 ratio clamping
- [ ] **Phase 10: Evaluation Metrics and Paper Table** — Produce full evaluation metrics and cross-dataset LaTeX table

## Phase Details

### Phase 8: TwiBot-20 Data Loader
**Goal**: TwiBot-20 test data is fully loaded, edge-indexed, and validated for use in inference
**Depends on**: Nothing (new files only, no changes to existing pipeline)
**Requirements**: TW-01, TW-02, TW-03
**Success Criteria** (what must be TRUE):
  1. `twibot20_io.py` loads `test.json` into a DataFrame with columns `node_idx`, `screen_name`, `statuses_count`, `followers_count`, `friends_count`, `created_at`, `messages`, `label` — zero row loss
  2. Edge builder produces an `edges_df` with schema `{src: int32, dst: int32, etype: int8, weight: float32}` — `following` mapped to etype 0, `follower` to etype 1, all weights `log1p(1.0)`, accounts with `neighbor: None` contribute no rows
  3. Validation asserts `src.max() < len(accounts_df)` and `dst.max() < len(accounts_df)` without error; logs the fraction of accounts with no neighbors (~9%) and no tweets
  4. All required columns are present after loading; `label` is int (0 or 1), `node_idx` is int32 and 0-indexed by row
**Plans:** 2 plans
Plans:
- [x] 08-01-PLAN.md — Test scaffold + load_accounts() implementation (TW-01)
- [x] 08-02-PLAN.md — build_edges() + validate() + integration verification (TW-02, TW-03)

### Phase 9: Zero-Shot Inference Pipeline
**Goal**: Users can run zero-shot inference on TwiBot-20 accounts via `evaluate_twibot20.py` with correct Stage 1 ratio clamping
**Depends on**: Phase 8
**Requirements**: TW-04, TW-05
**Success Criteria** (what must be TRUE):
  1. `evaluate_twibot20.py` runs end-to-end against `test.json` using `trained_system_v12.joblib` without retraining or modifying any existing pipeline file
  2. Stage 1 ratio features (columns 6–9 of `extract_stage1_matrix` output) are clamped to [0.0, 50.0] in the TwiBot-20 inference path only — no change to any existing BotSim-24 code path
  3. The full cascade (Stage 1 → 2a → 2b → 3) executes without numerical errors, NaNs, or routing collapse on TwiBot-20 accounts that have zero-filled Reddit-specific columns (`comment_num_1`, `comment_num_2`, `subreddit_list`)
  4. Temporal features (`cv_intervals`, `rate`, `delta_mean`, `delta_std`, `hour_entropy`) are zero for all TwiBot-20 accounts and this is noted in the inference output without error
**Plans**: TBD

### Phase 10: Evaluation Metrics and Paper Table
**Goal**: Full evaluation results on TwiBot-20 are computed and a paper-ready cross-dataset LaTeX table is generated
**Depends on**: Phase 9
**Requirements**: TW-06, TW-07
**Success Criteria** (what must be TRUE):
  1. Evaluation output includes F1, AUC-ROC, precision, and recall on the TwiBot-20 test set
  2. Per-stage breakdown is reported: `p1_auc`, `p12_auc`, `p_final_auc`
  3. Routing statistics are reported: `stage3_used` rate and `amr_used` rate across TwiBot-20 accounts
  4. `generate_cross_dataset_table()` in `ablation_tables.py` produces a LaTeX table comparing BotSim-24 S3 (in-distribution, Reddit) vs. TwiBot-20 test (zero-shot, Twitter) side-by-side with dataset context labels; table renders without LaTeX errors
**Plans:** 2 plans
Plans:
- [ ] 10-01-PLAN.md — evaluate_twibot20() function + metrics_twibot20.json output (TW-06)
- [ ] 10-02-PLAN.md — generate_cross_dataset_table() + Table 5 LaTeX (TW-07)

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 8. TwiBot-20 Data Loader | 0/2 | Planned | - |
| 9. Zero-Shot Inference Pipeline | 0/? | Not started | - |
| 10. Evaluation Metrics and Paper Table | 0/2 | Planned | - |

---
*Roadmap created: 2026-04-16*
*Phase range: 8-10 (continues from v1.1 which ended at phase 7)*
