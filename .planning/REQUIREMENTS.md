# Requirements: Social Bot Detection System

**Defined:** 2026-03-19
**Core Value:** The cascade must produce a single, well-calibrated bot probability per account — routing efficiently through stages while catching sophisticated bots that simple models miss.

## v1 Requirements

### Pipeline Core

Already implemented — validated from codebase map.

- [x] **CORE-01**: Stage 1 metadata classifier — LightGBM on numeric account metadata with Mahalanobis novelty scoring and probability calibration
- [x] **CORE-02**: Stage 2a content/temporal classifier — MiniLM embeddings fused with linguistic/temporal features, LightGBM + calibration + novelty
- [x] **CORE-03**: Stage 2b AMR delta refiner — learned logit adjustment from AMR embeddings, applied only to gated subset
- [x] **CORE-04**: Stage 3 structural classifier — LightGBM on graph-derived structural features (weighted/unweighted degrees per edge type)
- [x] **CORE-05**: AMR gating logic — gate_amr() triggers AMR refinement only when p2a is uncertain, novelty is high, or Stage 1/2 strongly disagree
- [x] **CORE-06**: Stage 3 routing logic — gate_stage3() escalates when p12 is uncertain or novelty is high
- [x] **CORE-07**: Meta12 logistic regression stacking combiner — combines Stage 1 + Stage 2 logits, novelty scores, amr_used flag
- [x] **CORE-08**: Meta123 logistic regression final combiner — combines meta12 + Stage 3 outputs with stage3_used flag
- [x] **CORE-09**: OOF stacking for leakage-free meta-model training — StratifiedKFold over S2 split
- [x] **CORE-10**: S1/S2/S3 data splits — ~70%/15%/15% stratified splits with per-split graph edge filtering
- [x] **CORE-11**: BotSim-24 data loading — CSV parsing, JSON deserialization, timestamp normalization, account table construction
- [x] **CORE-12**: TrainedSystem encapsulation — single dataclass holding all trained models, configs, and embedder

### Threshold Calibration

- [x] **CALIB-01**: System can optimize novelty and probability routing thresholds using Bayesian optimization over the S2 split
- [x] **CALIB-02**: Optimization objective is configurable (default: F1; alternatives: AUC, precision, recall)
- [x] **CALIB-03**: Calibrated thresholds are persisted as part of TrainedSystem for reproducibility

### REST API

- [x] **API-01**: POST /predict endpoint accepts JSON account data and returns p_final (bot probability) and binary label
- [x] **API-02**: API loads a pre-trained and serialized TrainedSystem from disk and routes requests through predict_system()
- [x] **API-03**: Input JSON schema is validated against expected account fields before inference

### Evaluation

- [x] **EVAL-01**: End-to-end evaluation on S3 produces F1, AUC, precision, and recall
- [x] **EVAL-02**: Per-stage breakdown reports individual stage contributions (p1, p2, p12, p_final vs labels)
- [x] **EVAL-03**: Routing statistics reported — percentage of accounts exiting at each stage and percentage with AMR triggered

## v2 Requirements

### Ablation Study
- **ABL-01**: Automated ablation runner comparing cascade vs. Stage-1-only, Stage-2-only, no-AMR, no-Stage-3 configurations
- **ABL-02**: Results table formatted for paper inclusion

### AMR Enhancement
- **AMR-01**: Replace AMR embedding stub with true AMR graph parser (e.g., AMR-BART or SPRING)
- **AMR-02**: Evaluate delta from true AMR vs. embedding approximation

### Generalization
- **GEN-01**: Dataset-agnostic data loader interface for non-BotSim-24 datasets

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time streaming classification | Batch inference only; streaming adds infrastructure complexity not needed for paper |
| Multi-platform detection | BotSim-24 is Reddit-only; generalization to Twitter/X deferred to v2+ |
| True AMR graph parsing | AMR linearization stub sufficient for v1; full parser is a research extension |
| Frontend / dashboard UI | API only; visualization not needed for paper submission |
| Model retraining via API | Training runs offline; API is inference-only |
| Online learning / model updates | Static trained model per experiment run |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORE-01 | Phase 1 (Pipeline Integration) | Complete — existing |
| CORE-02 | Phase 1 (Pipeline Integration) | Complete — existing |
| CORE-03 | Phase 1 (Pipeline Integration) | Complete — existing |
| CORE-04 | Phase 1 (Pipeline Integration) | Complete — existing |
| CORE-05 | Phase 1 (Pipeline Integration) | Complete — existing |
| CORE-06 | Phase 1 (Pipeline Integration) | Complete — existing |
| CORE-07 | Phase 1 (Pipeline Integration) | Complete — existing |
| CORE-08 | Phase 1 (Pipeline Integration) | Complete — existing |
| CORE-09 | Phase 1 (Pipeline Integration) | Complete — existing |
| CORE-10 | Phase 1 (Pipeline Integration) | Complete — existing |
| CORE-11 | Phase 1 (Pipeline Integration) | Complete — existing |
| CORE-12 | Phase 1 (Pipeline Integration) | Complete — existing |
| CALIB-01 | Phase 2 (Threshold Calibration) | Complete |
| CALIB-02 | Phase 2 (Threshold Calibration) | Complete |
| CALIB-03 | Phase 2 (Threshold Calibration) | Complete |
| EVAL-01 | Phase 3 (Evaluation) | Complete |
| EVAL-02 | Phase 3 (Evaluation) | Complete |
| EVAL-03 | Phase 3 (Evaluation) | Complete |
| API-01 | Phase 4 (REST API) | Complete |
| API-02 | Phase 4 (REST API) | Complete |
| API-03 | Phase 4 (REST API) | Complete |

**Coverage:**
- v1 requirements: 21 total (12 validated + 3 calibration + 3 evaluation + 3 API)
- Mapped to phases: 21
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-19*
*Last updated: 2026-03-19 after roadmap creation — traceability expanded to individual CORE entries*
