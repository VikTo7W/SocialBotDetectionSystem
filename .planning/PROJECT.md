# Social Bot Detection System

## What This Is

A multi-stage cascade classifier for detecting social bots on Reddit using the BotSim-24 dataset. The system escalates accounts through three detection stages (metadata -> content/temporal -> graph structure), using novelty-aware routing to balance compute efficiency with accuracy. The research contribution is the cascade architecture with AMR semantic refinement and zero-shot transfer experiments.

v1.0 delivered Bayesian threshold calibration, a paper-ready S3 evaluation module, and a REST API for single-account inference.
v1.1 delivered Stage 2 leakage removal, new behavioral and similarity features, a clean retrain, and paper-ready ablation tables.

## Current State

v1.2 shipped the TwiBot-20 zero-shot transfer path for the Reddit-trained cascade. The codebase now includes a behaviorally grounded Twitter adapter, missingness-aware TwiBot feature handling, online novelty-threshold recalibration, and a paper-output path for static-vs-recalibrated TwiBot comparison.

The milestone closed with acknowledged gaps rather than a pristine verification finish:

- fresh real-data TwiBot comparison artifacts still need to be regenerated
- final pytest/runtime verification remains partially blocked by local Windows temp/process permission issues
- no dedicated v1.2 milestone audit was run before close

## Next Milestone Goals

- Regenerate TwiBot comparison evidence and confirm whether recalibration materially improves transfer quality
- Decide whether the next step is better zero-shot robustness, a supervised TwiBot baseline, or a broader Stage 2/Stage 3 domain adaptation effort
- Tighten planning/state hygiene so requirements and verification stay current during execution rather than only at closeout

## Current Milestone: v1.3 Twibot System Version

**Goal:** Turn the TwiBot transfer path into a reproducible, evidence-backed system version with fresh evaluation artifacts, cleaner execution flow, and an explicit versioned release record.

**Target features:**
- Reproducible TwiBot evaluation flow that can run static and recalibrated comparisons without the current temp/cache friction
- Fresh live artifacts for TwiBot metrics, comparison outputs, and the final cross-dataset table
- Explicit system-version documentation describing the chosen model artifact, commands, outputs, and remaining caveats

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

### Active

- Generate fresh static-vs-recalibrated evidence and final paper outputs from live runs
- Publish the chosen TwiBot system version and its execution/documentation contract
- Multi-seed ablation stability for paper confidence intervals
- CalibratedClassifierCV on a held-out calibration subset
- True AMR graph parsing replacing the current embedding stub

### Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time streaming classification | Batch inference only |
| Multi-platform supervised training | v1.2 is zero-shot transfer only |
| Frontend or dashboard UI | API and scripts only |
| Model retraining through the API | Offline training only |
| Profile or description features | Permanently excluded after the leakage audit |
| Full Twitter-native Stage 2 or Stage 3 redesign | Deferred beyond transfer stabilization |

## Context

- **Dataset:** BotSim-24 provides Reddit metadata, timelines, and graph tensors. TwiBot-20 is the zero-shot transfer target for v1.2.
- **Architecture:** Three-stage cascade with novelty-aware gating and logistic-regression stackers.
- **Current state:** `trained_system_v12.joblib` is the active clean model. v1.3 starts from an implemented but not fully evidenced TwiBot transfer path and focuses on reproducible execution plus release-quality artifacts.
- **AMR status:** The Stage 2b semantic path is still an embedding-based proxy, not true AMR graph parsing.
- **Paper contribution:** The novel contribution remains the cascade plus routing and semantic refinement, now strengthened by explicit cross-domain transfer analysis.

## Constraints

- **Tech stack:** Python, scikit-learn, LightGBM, sentence-transformers, and PyTorch tensor loading only
- **No leakage:** keep split boundaries, graph filtering, OOF stacking, and Stage 2 leakage exclusions intact
- **Zero-shot transfer:** TwiBot-20 labels are for evaluation, not adaptation or retraining
- **Reproducibility:** seed all experiments with `SEED=42`
- **Feature shape stability:** Phase 8 may revise semantics and missingness handling, but should not retrain models or change expected feature dimensionality

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

---
*Last updated: 2026-04-18 after Phase 11 (Reproducible TwiBot Evaluation Flow)*
