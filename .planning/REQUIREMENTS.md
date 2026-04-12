# Requirements: Social Bot Detection System

**Defined:** 2026-03-19
**Updated:** 2026-04-12 (v1.1 requirements added)
**Core Value:** The cascade must produce a single, well-calibrated bot probability per account — routing efficiently through stages while catching sophisticated bots that simple models miss.

## v1.0 Requirements (Validated)

### Pipeline

- ✓ **PIPE-01**: Full 3-stage cascade trains and predicts end-to-end — Phase 1
- ✓ **PIPE-02**: S1/S2/S3 splits are stratified and leakage-free — Phase 1
- ✓ **PIPE-03**: TrainedSystem serializes to joblib and reloads cleanly — Phase 4

### Calibration

- ✓ **CALIB-01**: Bayesian threshold calibration runs on S2 via Optuna TPE — Phase 2
- ✓ **CALIB-02**: 10-dimensional threshold space optimizes F1 — Phase 2
- ✓ **CALIB-03**: Calibrated thresholds persist in TrainedSystem — Phase 2

### Evaluation

- ✓ **EVAL-01**: Overall metrics (F1, AUC, precision, recall) on S3 — Phase 3
- ✓ **EVAL-02**: Per-stage metrics table (p1, p2, p12, p_final) — Phase 3
- ✓ **EVAL-03**: Routing statistics (exit percentages, AMR trigger rate) — Phase 3

### REST API

- ✓ **API-01**: POST /predict endpoint accepts JSON account data — Phase 4
- ✓ **API-02**: Response includes p_final and bot/human label — Phase 4
- ✓ **API-03**: Integration tests pass for API endpoints — Phase 4

## v1.1 Requirements

Requirements for the Feature Leakage Audit & Fix milestone.

### Leakage Fix

- [ ] **LEAK-01**: Developer can run Stage 2a evaluation and see AUC below 90% (confirming leakage removed)
- [ ] **LEAK-02**: `extract_stage2_features` embeds message texts only (no username, no profile text)
- [ ] **LEAK-03**: AMR extractor uses representative message text instead of profile field
- [ ] **LEAK-04**: `character_setting` column is dropped at load time in `build_account_table`
- [ ] **LEAK-05**: Full system retrains cleanly with recalibrated thresholds after feature changes

### Content Features

- [ ] **FEAT-01**: Stage 2a includes coefficient of variation of inter-post intervals
- [ ] **FEAT-02**: Stage 2a includes message character length distribution stats (mean, std)
- [ ] **FEAT-03**: Stage 2a includes entropy of posting hour-of-day distribution
- [ ] **FEAT-04**: Stage 2a includes cross-message cosine similarity and near-duplicate fraction

### Ablation & Paper Tables

- [ ] **ABL-01**: Ablation runner supports force-routing to evaluate full test set at each stage
- [ ] **ABL-02**: Table 1 (leakage audit) generated: v1.0 vs v1.1 metrics on S3
- [ ] **ABL-03**: Table 2 (stage contribution) generated: force-routed ablation per stage
- [ ] **ABL-04**: Table 3 (routing efficiency) generated: % stage exits + AMR trigger rate
- [ ] **ABL-05**: Table 4 (Stage 1 feature group ablation) generated: per-column-group masking
- [ ] **ABL-06**: All tables exported as LaTeX via `pd.to_latex()` and include AUC-ROC alongside F1

## v2 Requirements

Deferred to a future milestone.

### Calibration Improvements

- **CAL-01**: `CalibratedClassifierCV` uses a held-out calibration subset (not training data) — requires pipeline restructure
- **CAL-02**: Multi-seed ablation stability (3 seeds) for paper confidence intervals

### AMR Enhancement

- **AMR-01**: True AMR graph parsing replacing the text-embedding stub

## Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time streaming classification | Batch inference only; architectural change |
| Multi-platform detection | BotSim-24 (Reddit) only |
| Frontend / dashboard UI | API only |
| Model retraining via API | Offline training only |
| Profile/description features of any kind | Root cause of leakage — permanently excluded from Stage 2 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| PIPE-01 | Phase 1 | Complete |
| PIPE-02 | Phase 1 | Complete |
| PIPE-03 | Phase 4 | Complete |
| CALIB-01 | Phase 2 | Complete |
| CALIB-02 | Phase 2 | Complete |
| CALIB-03 | Phase 2 | Complete |
| EVAL-01 | Phase 3 | Complete |
| EVAL-02 | Phase 3 | Complete |
| EVAL-03 | Phase 3 | Complete |
| API-01 | Phase 4 | Complete |
| API-02 | Phase 4 | Complete |
| API-03 | Phase 4 | Complete |
| LEAK-01 | Phase 5 | Pending |
| LEAK-02 | Phase 5 | Pending |
| LEAK-03 | Phase 5 | Pending |
| LEAK-04 | Phase 5 | Pending |
| LEAK-05 | Phase 5 | Pending |
| FEAT-01 | Phase 5 | Pending |
| FEAT-02 | Phase 5 | Pending |
| FEAT-03 | Phase 5 | Pending |
| FEAT-04 | Phase 6 | Pending |
| ABL-01 | Phase 6 | Pending |
| ABL-02 | Phase 7 | Pending |
| ABL-03 | Phase 7 | Pending |
| ABL-04 | Phase 7 | Pending |
| ABL-05 | Phase 7 | Pending |
| ABL-06 | Phase 7 | Pending |

**Coverage (v1.1):**
- v1.1 requirements: 15 total
- Mapped to phases: 15
- Unmapped: 0 ✓

---
*Requirements defined: 2026-03-19*
*Last updated: 2026-04-12 after v1.1 milestone definition*
