# Roadmap: Social Bot Detection System

## Milestones

- [x] **v1.0 MVP** - Phases 1-4 (shipped 2026-04-12)
- [x] **v1.1 Feature Leakage Audit & Fix** - Phases 5-7 (shipped 2026-04-16)
- [x] **v1.2 TwiBot-20 Cross-Domain Transfer** - Phases 8-10 (shipped 2026-04-18)
- [x] **v1.3 Twibot System Version** - Phases 11-13 (shipped 2026-04-18)
- [x] **v1.4 Twitter-Native Supervised Baseline** - Phases 14-16 (shipped 2026-04-18)
- [ ] **v1.5 Unified Modular Codebase** - Phases 17-21 (active)

## Phases

<details>
<summary>[x] v1.0 MVP (Phases 1-4) - SHIPPED 2026-04-12</summary>

- [x] Phase 1: Pipeline Integration (0/0 plans) - completed 2026-03-19
- [x] Phase 2: Threshold Calibration (2/2 plans) - completed 2026-03-19
- [x] Phase 3: Evaluation (1/1 plans) - completed 2026-03-19
- [x] Phase 4: REST API (2/2 plans) - completed 2026-03-19

</details>

<details>
<summary>[x] v1.1 Feature Leakage Audit & Fix (Phases 5-7) - SHIPPED 2026-04-16</summary>

- [x] Phase 5: Leakage Fix and Baseline Retrain (2/2 plans) - completed 2026-04-14
- [x] Phase 6: Ablation Infrastructure and Differentiator Features (2/2 plans) - completed 2026-04-15
- [x] Phase 7: Ablation Execution and Paper Tables (2/2 plans) - completed 2026-04-15

</details>

<details>
<summary>[x] v1.2 TwiBot-20 Cross-Domain Transfer (Phases 8-10) - SHIPPED 2026-04-18</summary>

- [x] Phase 8: Behavioral Tweet Parser and Transfer Adapter Stabilization (2/2 plans) - completed 2026-04-17
- [x] Phase 9: Sliding-Window Online Threshold Recalibration (1/1 plans) - completed 2026-04-18
- [x] Phase 10: Cross-Domain Evaluation and Paper Output (2/2 plans) - completed 2026-04-18

</details>

<details>
<summary>[x] v1.3 Twibot System Version (Phases 11-13) - SHIPPED 2026-04-18</summary>

- [x] Phase 11: Reproducible TwiBot Evaluation Flow (2/2 plans) - completed 2026-04-18
- [x] Phase 12: Fresh Transfer Evidence and Paper Outputs (2/2 plans) - completed 2026-04-18
- [x] Phase 13: System Version Packaging and Release Docs (2/2 plans) - completed 2026-04-18

</details>

<details>
<summary>[x] v1.4 Twitter-Native Supervised Baseline (Phases 14-16) - SHIPPED 2026-04-18</summary>

- [x] **Phase 14: Twitter-Native Feature Pipeline** - Build TwiBot-native Stage 1, Stage 2, and Stage 3 feature extraction without Reddit mappings, imputing, or zero-fill stand-ins
- [x] **Phase 15: TwiBot Cascade Training and Evaluation** - Train a TwiBot-native cascade, persist separate model artifact(s), and evaluate on the TwiBot test split
- [x] **Phase 16: Comparative Paper Outputs and Reddit Cleanup** - Compare Reddit-trained vs TwiBot-trained results, remove Reddit novelty recalibration, and update release-facing docs

</details>

<details open>
<summary>[ ] v1.5 Unified Modular Codebase (Phases 17-21) - ACTIVE</summary>

- [ ] **Phase 17: Shared Feature Extraction Module** - Unify all feature extractor classes into a single dataset-parameterized module, removing duplication across Reddit and TwiBot codebases
- [ ] **Phase 18: Unified Cascade Pipeline and Calibration** - Implement the cascade training pipeline once (OOF stacking, meta-learner fitting, single-trial Bayesian calibration) with object-oriented structure
- [ ] **Phase 19: Training Entry Points and Fresh Model Retraining** - Build clean train_botsim.py and train_twibot.py entry points and retrain both cascade artifacts from the unified code
- [ ] **Phase 20: Evaluation Entry Points and Paper Outputs** - Build three clean evaluation entry points and regenerate all paper-facing outputs (confusion matrices, routing stats, metric tables, Table 5)
- [ ] **Phase 21: Documentation** - Write a comprehensive README covering system architecture, technique rationale, feature-stage mapping, and full reproduction guide

</details>

## Phase Details

### Phase 14: Twitter-Native Feature Pipeline
**Goal**: TwiBot-20 accounts can be transformed into native Stage 1, Stage 2, and Stage 3 feature inputs without relying on Reddit analog mappings
**Depends on**: Phase 13
**Requirements**: TWN-01, TWN-02, TWN-03
**Success Criteria** (what must be TRUE):
  1. Stage 1 uses only TwiBot-native account/activity signals and does not reuse Reddit slot mappings
  2. Stage 2 uses only TwiBot-native tweet text and timeline signals, with unavailable fields omitted rather than imputed as fake in-distribution values
  3. Stage 3 uses only TwiBot-native graph relations and feature definitions that correspond to available TwiBot structure
  4. Feature extraction paths are testable independently of full model training
**Plans**: 3 plans
Plans:
- [x] 14-01-PLAN.md - Build standalone TwiBot-native Stage 1 extractor and focused unit tests (TWN-01)
- [x] 14-02-PLAN.md - Build standalone TwiBot-native Stage 2 extractor and focused unit tests (TWN-02)
- [x] 14-03-PLAN.md - Define the TwiBot-native Stage 3 graph feature contract via wrapper/helper and focused graph tests (TWN-03)
**Completed**: 2026-04-18
**UI hint**: no

### Phase 15: TwiBot Cascade Training and Evaluation
**Goal**: A separate TwiBot-trained cascade can be trained, stored, and evaluated on TwiBot-20 with leakage-safe splits and reproducible metrics
**Depends on**: Phase 14
**Requirements**: TRN-01, TRN-02, TRN-03
**Success Criteria** (what must be TRUE):
  1. A complete training flow produces a TwiBot-trained artifact without overwriting the Reddit-trained system
  2. Evaluation on TwiBot test produces overall, per-stage, and routing metrics
  3. The training and evaluation flow is reproducible with explicit artifact paths and seed usage
**Plans**: 2 plans
Plans:
- [x] 15-01-PLAN.md - Build the TwiBot-native training/calibration entry point with separate artifact routing and focused tests (TRN-01, TRN-03)
- [x] 15-02-PLAN.md - Build the TwiBot-native evaluation entry point with stable native metrics artifacts and focused tests (TRN-02, TRN-03)
**Completed**: 2026-04-18
**UI hint**: no

### Phase 16: Comparative Paper Outputs and Reddit Cleanup
**Goal**: v1.4 records the platform-matched TwiBot baseline, compares it against the Reddit transfer result, and removes the unsupported recalibration path from the Reddit system
**Depends on**: Phase 15
**Requirements**: CMP-01, CMP-02, CMP-03
**Success Criteria** (what must be TRUE):
  1. A paper-facing comparison output contrasts Reddit-trained-on-TwiBot with TwiBot-trained-on-TwiBot
  2. The Reddit online novelty-recalibration path is removed or retired from the maintained system path
  3. Docs clearly explain the separate artifacts, reproduction path, and caveats
**Plans**: 3 plans
Plans:
- [x] 16-01-PLAN.md - Refresh the paper-facing comparison artifact and Table 5 to compare Reddit-trained transfer against the TwiBot-native baseline (CMP-01)
- [x] 16-02-PLAN.md - Retire online novelty recalibration from the maintained Reddit transfer evaluation path and lock down the post-cleanup baseline contract (CMP-02)
- [x] 16-03-PLAN.md - Update README/VERSION release docs for the separate artifacts and revised v1.4 comparison story (CMP-03)
**Completed**: 2026-04-18
**UI hint**: no

### Phase 17: Shared Feature Extraction Module
**Goal**: All Stage 1, 2a, 2b, and 3 feature extractors live in a single features/ module, parameterized by dataset, with no duplicated extractor code across the Reddit and TwiBot codebases
**Depends on**: Phase 16
**Requirements**: CORE-01, CORE-02, CORE-05
**Success Criteria** (what must be TRUE):
  1. A single dataset parameter (`botsim` or `twibot`) passed at construction selects the correct extractors, data loaders, and split logic without any dataset-specific branches in shared pipeline code
  2. All Stage 1, 2a, 2b, and 3 extractor classes live under features/ and accept the dataset parameter
  3. Stage 2b exposes only the AMR embedding delta-logit path; no LSTM class, method, or code path remains in the module
  4. The features/ module can be imported and the extractors instantiated for both datasets without importing unrelated pipeline code
**Plans**: TBD
**UI hint**: no

### Phase 18: Unified Cascade Pipeline and Calibration
**Goal**: The cascade training pipeline (OOF stacking, meta-learner fitting, Bayesian threshold calibration) exists as a single reusable implementation consumed by both training entry points, structured with classes and methods, with calibration reduced to one trial
**Depends on**: Phase 17
**Requirements**: CORE-03, CORE-04, QUAL-01, QUAL-02
**Success Criteria** (what must be TRUE):
  1. OOF stacking, meta-learner fitting, and threshold calibration are implemented once and invoked identically by both training entry points — no duplicated pipeline logic
  2. Bayesian threshold calibration runs exactly one trial for both systems; any previous multi-restart loop is removed
  3. Pipeline code is organized into classes with methods (data loading, feature extraction per stage, cascade pipeline, evaluation); no loose top-level procedural scripts
  4. Code comments are lowercase, explain the why rather than the what, and are used sparingly — no AI-style block commentary
**Plans**: TBD
**UI hint**: no

### Phase 19: Training Entry Points and Fresh Model Retraining
**Goal**: Two clean training entry points (train_botsim.py and train_twibot.py) invoke the shared pipeline and produce fresh, separately named cascade artifacts that replace the previous separately coded training scripts
**Depends on**: Phase 18
**Requirements**: TRAIN-01, TRAIN-02
**Success Criteria** (what must be TRUE):
  1. Running train_botsim.py completes a full BotSim-24 cascade training and writes trained_system_botsim.joblib without touching any TwiBot artifact
  2. Running train_twibot.py completes a full TwiBot-20 cascade training from train.json and writes trained_system_twibot.joblib without touching any BotSim artifact
  3. Both artifacts are produced by the unified pipeline code (Phase 18), not by any legacy separate training scripts
  4. Both training runs complete reproducibly with SEED=42 and produce artifacts that load without error
**Plans**: TBD
**UI hint**: no

### Phase 20: Evaluation Entry Points and Paper Outputs
**Goal**: Three evaluation entry points cover all maintained evaluation paths and each produces the full set of paper-ready outputs (confusion matrices, routing statistics, per-stage metric tables, and the Reddit-transfer-vs-native comparison table)
**Depends on**: Phase 19
**Requirements**: EVAL-01, EVAL-02, EVAL-03, PAPER-01, PAPER-02, PAPER-03
**Success Criteria** (what must be TRUE):
  1. eval_botsim_native.py evaluates the Reddit-trained model on the BotSim-24 test split and produces per-stage breakdown and routing statistics
  2. eval_reddit_twibot_transfer.py evaluates the Reddit-trained model on TwiBot-20 test data in zero-shot mode and produces the same output format
  3. eval_twibot_native.py evaluates the TwiBot-trained model on TwiBot-20 test data and produces the same output format
  4. Every evaluation entry point writes a confusion matrix image file and a routing statistics / per-stage metric table in the existing paper format
  5. The Reddit-transfer-vs-native comparison artifact (Table 5) is generated from the outputs of EVAL-02 and EVAL-03 without manual steps
**Plans**: TBD
**UI hint**: no

### Phase 21: Documentation
**Goal**: README.md is a self-contained reference that a reader unfamiliar with the codebase can use to understand the system architecture, the rationale for each technique, the feature-stage mapping for both datasets, and the exact commands needed to reproduce all results
**Depends on**: Phase 20
**Requirements**: DOC-01, DOC-02, DOC-03
**Success Criteria** (what must be TRUE):
  1. README.md explains the cascade architecture and the rationale for each technique (LightGBM, Mahalanobis novelty, AMR delta-logit, logistic-regression stackers, Bayesian calibration)
  2. README.md documents, per dataset (BotSim-24 and TwiBot-20), which features are extracted and how they map to Stage 1, 2a, 2b, and Stage 3
  3. README.md contains a reproduction guide listing data requirements, training commands, evaluation commands, and expected outputs for all three evaluation paths
**Plans**: TBD
**UI hint**: no

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Pipeline Integration | v1.0 | 0/0 | Complete | 2026-03-19 |
| 2. Threshold Calibration | v1.0 | 2/2 | Complete | 2026-03-19 |
| 3. Evaluation | v1.0 | 1/1 | Complete | 2026-03-19 |
| 4. REST API | v1.0 | 2/2 | Complete | 2026-03-19 |
| 5. Leakage Fix and Baseline Retrain | v1.1 | 2/2 | Complete | 2026-04-14 |
| 6. Ablation Infrastructure and Differentiator Features | v1.1 | 2/2 | Complete | 2026-04-15 |
| 7. Ablation Execution and Paper Tables | v1.1 | 2/2 | Complete | 2026-04-15 |
| 8. Behavioral Tweet Parser and Transfer Adapter Stabilization | v1.2 | 2/2 | Complete | 2026-04-17 |
| 9. Sliding-Window Online Threshold Recalibration | v1.2 | 1/1 | Complete | 2026-04-18 |
| 10. Cross-Domain Evaluation and Paper Output | v1.2 | 2/2 | Complete | 2026-04-18 |
| 11. Reproducible TwiBot Evaluation Flow | v1.3 | 2/2 | Complete | 2026-04-18 |
| 12. Fresh Transfer Evidence and Paper Outputs | v1.3 | 2/2 | Complete | 2026-04-18 |
| 13. System Version Packaging and Release Docs | v1.3 | 2/2 | Complete | 2026-04-18 |
| 14. Twitter-Native Feature Pipeline | v1.4 | 3/3 | Complete | 2026-04-18 |
| 15. TwiBot Cascade Training and Evaluation | v1.4 | 2/2 | Complete | 2026-04-18 |
| 16. Comparative Paper Outputs and Reddit Cleanup | v1.4 | 3/3 | Complete | 2026-04-18 |
| 17. Shared Feature Extraction Module | v1.5 | 0/? | Not started | - |
| 18. Unified Cascade Pipeline and Calibration | v1.5 | 0/? | Not started | - |
| 19. Training Entry Points and Fresh Model Retraining | v1.5 | 0/? | Not started | - |
| 20. Evaluation Entry Points and Paper Outputs | v1.5 | 0/? | Not started | - |
| 21. Documentation | v1.5 | 0/? | Not started | - |
