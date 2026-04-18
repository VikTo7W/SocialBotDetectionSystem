# Roadmap: Social Bot Detection System

## Milestones

- [x] **v1.0 MVP** - Phases 1-4 (shipped 2026-04-12)
- [x] **v1.1 Feature Leakage Audit & Fix** - Phases 5-7 (shipped 2026-04-16)
- [x] **v1.2 TwiBot-20 Cross-Domain Transfer** - Phases 8-10 (shipped 2026-04-18)
- [x] **v1.3 Twibot System Version** - Phases 11-13 (shipped 2026-04-18)
- [x] **v1.4 Twitter-Native Supervised Baseline** - Phases 14-16 (shipped 2026-04-18)

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

<details open>
<summary>[x] v1.4 Twitter-Native Supervised Baseline (Phases 14-16) - SHIPPED 2026-04-18</summary>

- [x] **Phase 14: Twitter-Native Feature Pipeline** - Build TwiBot-native Stage 1, Stage 2, and Stage 3 feature extraction without Reddit mappings, imputing, or zero-fill stand-ins
- [x] **Phase 15: TwiBot Cascade Training and Evaluation** - Train a TwiBot-native cascade, persist separate model artifact(s), and evaluate on the TwiBot test split
- [x] **Phase 16: Comparative Paper Outputs and Reddit Cleanup** - Compare Reddit-trained vs TwiBot-trained results, remove Reddit novelty recalibration, and update release-facing docs

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
