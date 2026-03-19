# Roadmap: Social Bot Detection System

## Overview

The pipeline core (CORE-01 through CORE-12) is already implemented and validated. The remaining work
delivers the three capabilities required for a paper-ready system: verified end-to-end pipeline
integration, calibrated routing thresholds, a full S3 evaluation, and a REST API for inference.
Phases proceed in dependency order — calibration requires a runnable pipeline, evaluation requires
calibrated thresholds, and the API wraps the fully-tuned system.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Pipeline Integration** - Verify the existing cascade runs end-to-end on real data before calibration begins
- [x] **Phase 2: Threshold Calibration** - Bayesian optimization of routing thresholds on S2, persisted to TrainedSystem (completed 2026-03-19)
- [x] **Phase 3: Evaluation** - Full S3 metrics, per-stage breakdown, and routing statistics (completed 2026-03-19)
- [ ] **Phase 4: REST API** - POST /predict endpoint with schema validation, serving the calibrated system

## Phase Details

### Phase 1: Pipeline Integration
**Goal**: The full cascade pipeline executes on real BotSim-24 data without errors, producing p_final for every account in the test set
**Depends on**: Nothing (first phase)
**Requirements**: CORE-01, CORE-02, CORE-03, CORE-04, CORE-05, CORE-06, CORE-07, CORE-08, CORE-09, CORE-10, CORE-11, CORE-12
**Success Criteria** (what must be TRUE):
  1. Running the training script on BotSim-24 completes without error and produces a TrainedSystem object
  2. Every account in S3 receives a p_final value between 0 and 1 with no NaN or missing outputs
  3. Routing flags (amr_used, stage3_used) are populated and non-trivially distributed (at least some accounts trigger each branch)
  4. TrainedSystem serializes to disk and deserializes back with identical inference outputs
**Plans**: TBD

### Phase 2: Threshold Calibration
**Goal**: Routing thresholds are optimized on S2 via Bayesian optimization and stored in TrainedSystem for reproducible inference
**Depends on**: Phase 1
**Requirements**: CALIB-01, CALIB-02, CALIB-03
**Success Criteria** (what must be TRUE):
  1. Running calibration on S2 completes and reports the best threshold set found with its objective score
  2. The optimization objective can be switched between F1, AUC, precision, and recall via a config argument
  3. Calibrated thresholds are saved inside TrainedSystem and automatically used in subsequent predict_system() calls
  4. Re-running calibration with SEED=42 produces identical threshold values (reproducibility)
**Plans:** 2/2 plans complete
Plans:
- [x] 02-01-PLAN.md — Wave 0: Install optuna, create test infrastructure (conftest + 6 test stubs)
- [x] 02-02-PLAN.md — Wave 1: Implement calibrate.py and wire into main.py

### Phase 3: Evaluation
**Goal**: The system produces a complete, paper-ready evaluation report on the held-out S3 split
**Depends on**: Phase 2
**Requirements**: EVAL-01, EVAL-02, EVAL-03
**Success Criteria** (what must be TRUE):
  1. Running the evaluation script on S3 prints overall F1, AUC, precision, and recall for p_final vs. ground truth
  2. Per-stage metrics (p1 vs. labels, p2 vs. labels, p12 vs. labels, p_final vs. labels) are reported side-by-side
  3. Routing statistics are reported: percentage of accounts exiting at Stage 1, Stage 2, and Stage 3, plus AMR trigger rate
**Plans:** 1/1 plans complete
Plans:
- [ ] 03-01-PLAN.md — Create evaluate.py with evaluate_s3() and wire into main.py

### Phase 4: REST API
**Goal**: A running API endpoint accepts account JSON and returns a calibrated bot probability, suitable for external use
**Depends on**: Phase 3
**Requirements**: API-01, API-02, API-03
**Success Criteria** (what must be TRUE):
  1. POST /predict with a valid account JSON payload returns {"p_final": <float>, "label": <0|1>} with HTTP 200
  2. The server starts by loading a serialized TrainedSystem from disk and uses it for all requests without retraining
  3. Sending a payload missing required fields returns HTTP 422 with a descriptive validation error
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Pipeline Integration | 0/TBD | Complete | 2026-03-19 |
| 2. Threshold Calibration | 2/2 | Complete    | 2026-03-19 |
| 3. Evaluation | 1/1 | Complete    | 2026-03-19 |
| 4. REST API | 0/TBD | Not started | - |
