# Social Bot Detection System

## What This Is

A multi-stage cascade classifier for detecting social bots on Reddit using the BotSim-24 dataset. The system escalates accounts through three detection stages (metadata -> content/temporal -> graph structure), using novelty-aware routing to balance compute efficiency with accuracy. The research contribution is the cascade architecture with AMR semantic refinement and zero-shot transfer experiments.

v1.0 delivered Bayesian threshold calibration, a paper-ready S3 evaluation module, and a REST API for single-account inference.
v1.1 delivered Stage 2 leakage removal, new behavioral and similarity features, a clean retrain, and paper-ready ablation tables.

## Current State

v1.2 shipped the TwiBot-20 zero-shot transfer path for the Reddit-trained cascade. The codebase now includes a behaviorally grounded Twitter adapter, missingness-aware TwiBot feature handling, online novelty-threshold recalibration, and a paper-output path for static-vs-recalibrated TwiBot comparison.

v1.3 shipped the reproducible evaluation flow, fresh live TwiBot evidence (static F1=0.0/AUC=0.5964, recalibrated F1=0.0/AUC=0.5879, verdict=`no_material_change`), and release-facing documentation (`VERSION.md` + `README.md` reproduction guide with caveats and limitations).

## Current Milestone: v1.4 Twitter-Native Supervised Baseline

**Goal:** Build a Twitter-native cascade trained on TwiBot-20 to prove the system degrades without platform-matched training, and remove the broken novelty recalibration from the Reddit system.

**Target features:**
- Twitter-native feature extraction for all three stages (no Reddit mappings, no imputing, no zero-fill)
- Full cascade trained on TwiBot-20 train.json, evaluated on test.json
- Paper comparison table: Reddit-trained on TwiBot (F1=0.0, v1.3) vs TwiBot-trained on TwiBot
- Remove online novelty recalibration from the Reddit cascade

## Current State

v1.3 shipped 2026-04-18. The active Reddit model is `trained_system_v12.joblib`. Zero-shot TwiBot transfer produces weak but reproducible results (F1=0.0, AUC=0.5964); recalibration does not materially improve F1. The pipeline is well-documented and reproducible from `README.md`.

Known gaps carried into v1.4:
- Full pytest green-suite blocked by Windows temp-dir cleanup permissions (production code unaffected)
- Stale pre-Phase-12 TwiBot artifacts at repo root (superseded by Phase 12 artifacts)

## Core Value

The cascade must produce a single, well-calibrated bot probability per account while routing efficiently through stages and remaining interpretable when transferred out of domain.

## Requirements

### Validated

- Stage 1 metadata classifier - LightGBM on numeric metadata with Mahalanobis novelty scoring and calibrated probabilities - v1.0
- Stage 2a content/temporal classifier - sentence-transformer embeddings fused with linguistic/temporal features, LightGBM, calibration, and novelty - v1.0
- Stage 2b AMR delta refiner - learned logit adjustment from AMR-style embeddings, applied to gated subsets - v1.0
- Stage 3 structural classifier - LightGBM on graph-derived degree and weight features with calibration and novelty - v1.0
- AMR gating logic - AMR refinement activates on uncertainty, disagreement, or novelty - v1.0
- Stage 3 routing logic - escalation triggers on uncertainty or novelty - v1.0
- Meta12 stacking combiner - logistic regression over Stage 1 and Stage 2 outputs plus routing signals - v1.0
- Meta123 final combiner - logistic regression over meta12 and Stage 3 outputs with routing signal - v1.0
- OOF stacking for leakage-free meta-model training - v1.0
- S1/S2/S3 data splits with intra-split graph filtering - v1.0
- BotSim-24 data loading and normalization - v1.0
- TrainedSystem encapsulation - v1.0
- Threshold calibration via Bayesian optimization - v1.0
- REST API wrapper - v1.0
- End-to-end evaluation pipeline with per-stage breakdown and routing statistics - v1.0
- Feature leakage removed from Stage 2 paths - v1.1
- Behavioral and cross-message similarity features added to Stage 2a - v1.1
- Paper ablation tables generated from the clean feature set - v1.1
- Reproducible TwiBot evaluation flow with output_dir routing, stable artifact filenames, documented canonical command, and TWIBOT_COMPARISON_PATH env-var override - v1.3 Phase 11
- Fresh live TwiBot evidence generated: static F1=0.0/AUC=0.5964, recalibrated F1=0.0/AUC=0.5879, verdict=no_material_change - v1.3 Phase 12
- Table 5 cross-dataset LaTeX regenerated from live Phase 12 artifacts with TABLE5_OUTPUT_PATH and TABLE5_INTERPRETATION_PATH env-var overrides - v1.3 Phase 12
- VERSION.md release contract at project root naming model artifact, evaluation modes, output files, live verdict, and env-var overrides - v1.3 Phase 13
- README.md reproduction guide with numbered commands, environment assumptions, known caveats, and known limitations - v1.3 Phase 13

### Active

- Twitter-native Stage 1 feature set for TwiBot-20 (no Reddit mappings, no imputing)
- Twitter-native Stage 2 content/temporal feature set for TwiBot-20 tweet timelines
- Twitter-native Stage 3 graph feature set from TwiBot-20 neighbor lists
- Full cascade training on TwiBot-20 train.json with OOF stacking and meta-learners
- TwiBot-20 test.json evaluation (F1, AUC, per-stage breakdown)
- Paper comparison table: Reddit-trained vs TwiBot-trained on TwiBot-20 test set
- Remove online novelty recalibration from the Reddit cascade
- Multi-seed ablation stability for paper confidence intervals (deferred from v1.3)
- CalibratedClassifierCV on a held-out calibration subset (deferred from v1.3)
- True AMR graph parsing replacing the current embedding stub (deferred from v1.3)

### Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time streaming classification | Batch inference only |
| Frontend or dashboard UI | API and scripts only |
| Model retraining through the API | Offline training only |
| Profile or description features | Permanently excluded after the leakage audit |
| Reddit→Twitter feature mapping (missingness-aware adapter) | Replaced by Twitter-native features in v1.4 |
| Online novelty recalibration | Removed in v1.4 — does not improve transfer results |

## Context

- **Dataset:** BotSim-24 provides Reddit metadata, timelines, and graph tensors. TwiBot-20 provides Twitter metadata, tweet timelines, and follower/following neighbor lists with canonical train/val/test splits.
- **Architecture:** Three-stage cascade with novelty-aware gating and logistic-regression stackers.
- **Current state:** `trained_system_v12.joblib` is the active Reddit-trained model. v1.4 adds a separate TwiBot-20-trained cascade using Twitter-native features, stored as a distinct artifact.
- **AMR status:** The Stage 2b semantic path is still an embedding-based proxy, not true AMR graph parsing.
- **Paper contribution:** The novel contribution is the cascade architecture. v1.4 strengthens the paper by showing the cascade works well when platform-matched (TwiBot trained → TwiBot test) and fails without it (Reddit trained → TwiBot test, F1=0.0).

## Constraints

- **Tech stack:** Python, scikit-learn, LightGBM, sentence-transformers, and PyTorch tensor loading only
- **No leakage:** keep split boundaries, graph filtering, OOF stacking, and Stage 2 leakage exclusions intact
- **Zero-shot transfer (Reddit model):** TwiBot-20 labels are not used to adapt the Reddit-trained cascade
- **Twitter-native features:** TwiBot-20 cascade must use only fields genuinely present in TwiBot-20 — no imputing, no zero-fill for absent Reddit analogs
- **Separate artifacts:** Reddit-trained and TwiBot-trained systems are stored as distinct joblib files; neither overwrites the other
- **Reproducibility:** seed all experiments with `SEED=42`

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| AMR as delta-logit updater | Preserves AMR as incremental evidence instead of a second full classifier | Good |
| Mahalanobis distance for novelty | Analytically grounded OOD signal without extra model training | Good |
| Logistic regression for meta-learners | Interpretable and resistant to overfitting on the small stacking set | Good |
| Bayesian optimization for thresholds | More sample-efficient than grid search and compatible with current environment | Working |
| S1/S2/S3 split discipline | Prevents leakage during training and evaluation | Good |
| Preserve v11 alongside v12 | Needed for leakage-audit and ablation comparisons | Good |
| Phase 8 scope revised on 2026-04-17 | Saved TwiBot results showed collapse, so the frozen Stage 1 mapping was reopened and missingness-aware stabilization was allowed without retraining | Adopted in v1.2 |
| TwiBot `domain` is eligible for `subreddit_list` analog | It is a closer topical-breadth signal than RT/MT usernames for Reddit transfer | Adopted in v1.2 |
| Missingness-aware handling is allowed when TwiBot fields are systematically absent | Hard-zero defaults can create misleading in-distribution signals in zero-shot transfer | Adopted in v1.2 |
| Phase 10 before/after semantics changed during execution | The live comparison now means static thresholds vs online recalibration on the revised adapter, not a return to the deprecated demographic-proxy path | Adopted in v1.2 |
| Windows temp friction is pytest-level, not production | grep confirmed zero tempfile/gettempdir usage in production code; friction is pytest tmp_path cleanup permissions only | Confirmed Phase 11 |
| output_dir parameter added to evaluate_twibot20.py __main__ | Artifacts route through os.path.join(output_dir, ...) with os.makedirs; backward-compatible default is cwd | Adopted v1.3 Phase 11 |
| TwiBot zero-shot F1=0.0 is documented as the v1.3 release state, not a bug | Predictions cluster near the 0.5 threshold; precision and recall collapse — a transfer-regime artifact | Adopted v1.3 Phase 13 |
| VERSION.md is the single source of release-contract truth | README links to it; avoids duplication between reproduction guide and artifact contract | Adopted v1.3 Phase 13 |

---
*Last updated: 2026-04-18 — v1.4 milestone started (Twitter-Native Supervised Baseline)*
