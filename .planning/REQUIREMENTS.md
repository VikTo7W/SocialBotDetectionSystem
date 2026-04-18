# Requirements: v1.5 Unified Modular Codebase

**Created:** 2026-04-18
**Milestone:** v1.5 Unified Modular Codebase
**Status:** Active

## Milestone Goal

Refactor the full system into a single parameterized codebase shared across BotSim-24 and TwiBot-20, removing the LSTM Stage 2b path, unifying calibration to a single trial, with clean entry points, fresh model retraining, paper-ready outputs, and a comprehensive README.

## Requirements

### Shared Core Infrastructure

- [ ] **CORE-01**: A dataset parameter (`botsim` / `twibot`) controls which feature extractors, data loaders, and split logic are used throughout the pipeline — no dataset-specific branches embedded in shared code
- [ ] **CORE-02**: All feature extractor classes live in one module (`features/`), with Stage 1, 2a, 2b, and 3 extractors accepting a dataset parameter
- [ ] **CORE-03**: The cascade training pipeline (OOF stacking, meta-learner fitting, threshold calibration) is implemented once and invoked by both training entry points
- [ ] **CORE-04**: Bayesian threshold calibration runs a single trial for both systems (no multi-restart loop)
- [ ] **CORE-05**: Stage 2b retains only the AMR embedding delta-logit path; the LSTM path is removed entirely

### Training Entry Points

- [ ] **TRAIN-01**: `train_botsim.py` trains the full Reddit cascade on BotSim-24 and writes `trained_system_botsim.joblib`
- [ ] **TRAIN-02**: `train_twibot.py` trains the full TwiBot cascade on TwiBot-20 (`train.json`) and writes `trained_system_twibot.joblib`

### Evaluation Entry Points

- [ ] **EVAL-01**: `eval_botsim_native.py` evaluates the Reddit-trained model on BotSim-24 test split with per-stage breakdown and routing statistics
- [ ] **EVAL-02**: `eval_reddit_twibot_transfer.py` evaluates the Reddit-trained model on TwiBot-20 test data (zero-shot transfer)
- [ ] **EVAL-03**: `eval_twibot_native.py` evaluates the TwiBot-trained model on TwiBot-20 test data (native)

### Paper Outputs

- [ ] **PAPER-01**: All three evaluation entry points produce confusion matrices as image files
- [ ] **PAPER-02**: All three evaluation entry points produce routing statistics and per-stage metric tables in the existing paper format
- [ ] **PAPER-03**: The Reddit-transfer-vs-native comparison artifact (Table 5) is generated from the outputs of EVAL-02 and EVAL-03

### Code Quality

- [ ] **QUAL-01**: Each logical component (data loading, feature extraction per stage, cascade pipeline, evaluation) is organized into classes with methods, not loose functions or procedural scripts
- [ ] **QUAL-02**: Comments are non-AI-style: lowercase, explaining the *why* not the *what*, and used sparingly

### Documentation

- [ ] **DOC-01**: `README.md` explains the full system: cascade architecture, why each technique was chosen (LightGBM, Mahalanobis novelty, AMR delta-logit, logistic-regression stackers, Bayesian calibration)
- [ ] **DOC-02**: `README.md` documents which features are extracted from each dataset and how they are distributed across Stage 1, 2a, 2b, and Stage 3
- [ ] **DOC-03**: `README.md` includes a reproduction guide: data requirements, training commands, evaluation commands, expected outputs

## Future Requirements

- Multi-seed ablation stability for paper confidence intervals (deferred from v1.3)
- True AMR graph parsing replacing the current embedding stub (deferred from v1.3)
- CalibratedClassifierCV on a held-out calibration subset (deferred from v1.3)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time streaming classification | Batch inference only |
| Frontend or dashboard UI | API and scripts only |
| Model retraining through the API | Offline training only |
| Profile or description features | Permanently excluded after leakage audit |
| LSTM Stage 2b path | Removed in v1.5 — AMR embedding version only |
| Online novelty recalibration in maintained path | Removed in v1.4 |
| Multi-trial Bayesian calibration | Single trial produces identical results |

## Traceability

| REQ-ID | Phase | Status |
|--------|-------|--------|
| CORE-01 | Phase 17 | Pending |
| CORE-02 | Phase 17 | Pending |
| CORE-05 | Phase 17 | Pending |
| CORE-03 | Phase 18 | Pending |
| CORE-04 | Phase 18 | Pending |
| QUAL-01 | Phase 18 | Pending |
| QUAL-02 | Phase 18 | Pending |
| TRAIN-01 | Phase 19 | Pending |
| TRAIN-02 | Phase 19 | Pending |
| EVAL-01 | Phase 20 | Pending |
| EVAL-02 | Phase 20 | Pending |
| EVAL-03 | Phase 20 | Pending |
| PAPER-01 | Phase 20 | Pending |
| PAPER-02 | Phase 20 | Pending |
| PAPER-03 | Phase 20 | Pending |
| DOC-01 | Phase 21 | Pending |
| DOC-02 | Phase 21 | Pending |
| DOC-03 | Phase 21 | Pending |
