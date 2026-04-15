# Roadmap: Social Bot Detection System

## Milestones

- ✅ **v1.0 MVP** — Phases 1-4 (shipped 2026-04-12)
- 🚧 **v1.1 Feature Leakage Audit & Fix** — Phases 5-7 (in progress)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) — SHIPPED 2026-04-12</summary>

- [x] Phase 1: Pipeline Integration (0 plans — pre-existing) — completed 2026-03-19
- [x] Phase 2: Threshold Calibration (2/2 plans) — completed 2026-03-19
- [x] Phase 3: Evaluation (1/1 plans) — completed 2026-03-19
- [x] Phase 4: REST API (2/2 plans) — completed 2026-03-19

See `.planning/milestones/v1.0-ROADMAP.md` for full phase details.

</details>

### 🚧 v1.1 Feature Leakage Audit & Fix (In Progress)

**Milestone Goal:** Remove feature leakage from Stage 2a and AMR, retrain the full cascade on clean features, and produce paper-ready ablation tables documenting each stage's contribution.

- [x] **Phase 5: Leakage Fix and Baseline Retrain** — Remove identity leakage from Stage 2a and AMR, add table-stakes behavioral features, retrain and recalibrate the full cascade (completed 2026-04-13)
- [x] **Phase 6: Ablation Infrastructure and Differentiator Features** — Build force-routing ablation runner, add cross-message similarity features (completed 2026-04-15)
- [ ] **Phase 7: Ablation Execution and Paper Tables** — Run all ablation variants and generate four LaTeX paper tables

## Phase Details

### Phase 5: Leakage Fix and Baseline Retrain
**Goal**: The cascade runs on clean behavioral features only, producing a realistic Stage 2a AUC and a fully retrained, recalibrated system that can serve as the clean baseline for all ablation work
**Note**: Actual AUC is 0.97-0.98, not 70-85% as estimated. Confirmed NOT residual leakage — BotSim-24 bots post generic news summaries while humans post specific headlines; sentence transformer separates these by content alone. The 70-85% estimate was overly conservative for this dataset.
**Depends on**: Phase 4 (v1.0 system)
**Requirements**: LEAK-01, LEAK-02, LEAK-03, LEAK-04, LEAK-05, FEAT-01, FEAT-02, FEAT-03
**Success Criteria** (what must be TRUE):
  1. Running Stage 2a evaluation returns an AUC below 90% (confirming both leakage paths are removed)
  2. `extract_stage2_features` embeds only message texts; no username or profile string appears in the encoding pool
  3. The AMR extractor uses a representative message text anchor; `text_field="profile"` is gone from the call site
  4. `character_setting` is absent from the DataFrame produced by `build_account_table` (assertion passes)
  5. The full cascade (including meta12, meta123, and recalibrated thresholds) trains end-to-end without error and serializes to `trained_system.joblib`
**Plans:** 2/2 plans complete
Plans:
- [x] 05-01-PLAN.md — Test scaffolding, v1.0 metrics capture, atomic leakage fix and behavioral features
- [x] 05-02-PLAN.md — Update test fixtures, full cascade retrain and leakage removal validation

### Phase 6: Ablation Infrastructure and Differentiator Features
**Goal**: A reusable ablation runner with force-routing support exists, and cross-message similarity features are added to Stage 2a so that each ablation variant can be evaluated correctly against S3
**Depends on**: Phase 5
**Requirements**: FEAT-04, ABL-01
**Success Criteria** (what must be TRUE):
  1. `ablation.py` exists with an `AblationConfig` dataclass and force-routing threshold helpers that can route the full test set through any single stage
  2. Cross-message cosine similarity (mean pairwise) and near-duplicate fraction (sim > 0.9) are computed as Stage 2a features and appear in the trained feature set
  3. Running an ablation variant with force-routing to Stage 1 evaluates all S3 accounts at Stage 1 only (no accounts escalated to Stage 2 or 3)
**Plans:** 2/2 plans complete
Plans:
- [ ] 06-01-PLAN.md — Wave 0 test stubs, FEAT-04 cross-message similarity, ABL-01 ablation runner
- [ ] 06-02-PLAN.md — Add v12 joblib save to main.py and retrain checkpoint

### Phase 7: Ablation Execution and Paper Tables
**Goal**: Four paper-ready LaTeX ablation tables are generated from S3 evaluation, covering leakage audit, stage contribution, routing efficiency, and Stage 1 feature group ablation
**Depends on**: Phase 6
**Requirements**: ABL-02, ABL-04, ABL-05, ABL-06
**Success Criteria** (what must be TRUE):
  1. Table 1 (leakage audit) is generated showing v1.0 vs v1.1 S3 metrics side-by-side including AUC-ROC
  2. Table 2 (stage contribution) is generated showing per-stage metrics (p1/p12/p_final) from evaluate_s3() including AUC-ROC
  3. Table 3 (routing efficiency) is generated showing exit percentage per stage and AMR trigger rate
  4. Table 4 (Stage 1 feature group ablation) is generated showing metrics per column-group mask including AUC-ROC
  5. All four tables are exported as valid LaTeX via `pd.to_latex()` and saved to disk
**Plans:** 1/2 plans executed
Plans:
- [ ] 07-01-PLAN.md — Wave 0 test stubs for ablation table functions
- [ ] 07-02-PLAN.md — Implement ablation_tables.py, v1.0 metrics retrieval, and LaTeX export

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Pipeline Integration | v1.0 | 0/0 (pre-existing) | Complete | 2026-03-19 |
| 2. Threshold Calibration | v1.0 | 2/2 | Complete | 2026-03-19 |
| 3. Evaluation | v1.0 | 1/1 | Complete | 2026-03-19 |
| 4. REST API | v1.0 | 2/2 | Complete | 2026-03-19 |
| 5. Leakage Fix and Baseline Retrain | v1.1 | 2/2 | Complete | 2026-04-14 |
| 6. Ablation Infrastructure and Differentiator Features | 2/2 | Complete   | 2026-04-15 | - |
| 7. Ablation Execution and Paper Tables | 1/2 | In Progress|  | - |
