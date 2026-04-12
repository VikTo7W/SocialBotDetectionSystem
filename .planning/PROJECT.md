# Social Bot Detection System

## What This Is

A multi-stage cascade classifier for detecting social bots on Reddit using the BotSim-24 dataset. The system progressively escalates accounts through three detection stages (metadata → content/temporal → graph structure), using novelty-aware routing to balance compute efficiency with accuracy. Designed as a research contribution: the cascade architecture with AMR semantic refinement is the novel element, targeting a paper submission with competitive results.

The v1.0 milestone delivered: Bayesian threshold calibration (Optuna TPE), a paper-ready S3 evaluation module, and a REST API for single-account inference.

## Core Value

The cascade must produce a single, well-calibrated bot probability per account — routing efficiently through stages while catching sophisticated bots that simple models miss.

## Requirements

### Validated

- ✓ Stage 1 metadata classifier — LightGBM on numeric metadata (counts, ratios, name length) with Mahalanobis novelty scoring and CalibratedClassifierCV — v1.0
- ✓ Stage 2a content/temporal classifier — Sentence-transformer embeddings (MiniLM) fused with linguistic/temporal features, LightGBM + calibration + novelty — v1.0
- ✓ Stage 2b AMR delta refiner — learned logit adjustment from AMR embeddings via gradient descent, applied to gated subset — v1.0
- ✓ Stage 3 structural classifier — LightGBM on graph-derived features (weighted/unweighted in/out degrees per edge type) with calibration + novelty — v1.0
- ✓ AMR gating logic — gate_amr() applies AMR refinement only when p2a is uncertain, novelty is high, or Stage 1/2 strongly disagree — v1.0
- ✓ Stage 3 routing logic — gate_stage3() escalates accounts when p12 is uncertain or novelty is high — v1.0
- ✓ Meta12 stacking combiner — logistic regression over Stage 1 + Stage 2 logits, novelty scores, and amr_used flag — v1.0
- ✓ Meta123 final combiner — logistic regression over meta12 + Stage 3 outputs with stage3_used flag — v1.0
- ✓ OOF stacking for leakage-free meta-model training — StratifiedKFold over S2 split — v1.0
- ✓ S1/S2/S3 data splits — ~70%/15%/15% stratified splits with per-split graph edge filtering — v1.0
- ✓ BotSim-24 data loading — CSV parsing, JSON deserialization, timestamp normalization, account table construction — v1.0
- ✓ TrainedSystem encapsulation — single dataclass holding all trained models, configs, embedder — v1.0
- ✓ Threshold calibration via Bayesian optimization — Optuna TPE over 10 routing thresholds on S2, maximizing F1 — v1.0
- ✓ REST API wrapper — POST /predict endpoint accepting JSON account data, returning p_final + label — v1.0
- ✓ End-to-end evaluation pipeline — full S3 metrics (F1, AUC, precision/recall) + per-stage breakdown + routing statistics — v1.0

## Current Milestone: v1.1 Feature Leakage Audit & Fix

**Goal:** Identify and remove features causing near-perfect Stage 2a+ performance, producing legitimate paper-ready results.

**Target features:**
- Per-feature ablation to isolate leaky features at Stage 1 and Stage 2a
- Remove profile/username text from Stage 2a and AMR embeddings; use content-only features
- Re-train and re-evaluate the full cascade; confirm scores are realistic
- Generate paper-ready ablation tables documenting each stage's contribution

### Active

_(Requirements defined in REQUIREMENTS.md)_

### Out of Scope

- Real-time streaming classification — batch inference only; no streaming ingestion
- Multi-platform detection — BotSim-24 (Reddit) only; no generalization to Twitter/X or other platforms in v1
- Full AMR parser integration — AMR linearization is currently a stub; true graph-based AMR parsing deferred
- Frontend / dashboard UI — API only; no visualization layer
- Model retraining via API — serve only; training runs offline

## Context

- **Dataset:** BotSim-24 — Reddit account dataset with Users.csv (metadata) and user_post_comment.json (timeline). Graph edges stored as PyTorch tensors (edge_index.pt, edge_type.pt, edge_weight.pt).
- **Architecture:** Three-stage cascade with novelty-aware gating. Each stage produces (p, u, n, z). Meta-learners combine stages via logistic regression stacking. Novelty overrides confidence — high novelty forces escalation regardless of classifier confidence.
- **Current state (v1.0):** Fully trained system serializes to `trained_system.joblib`. API serves via `uvicorn api:app`. 26 tests green (calibration + evaluation + API). Threshold calibration uses Optuna TPE over 10 dimensions.
- **AMR status:** Stage 2b is implemented as a learned delta-logit over sentence-transformer embeddings of text. True AMR graph parsing is a stub — the semantic representation is approximated via embedding similarity. This is the "Option C delta updater" design.
- **Paper contribution:** The cascade architecture + novelty-aware routing + AMR refinement combination is the novel element. Requires ablation study showing each stage contributes.
- **Known issue:** `predict_system()` in `botdetector_pipeline.py` had incorrect calling conventions for `extract_stage1_matrix` and `extract_stage2_features` (extra `cfg` argument). Fixed in `botdetector_pipeline.py` directly.

## Constraints

- **Tech stack:** Python + scikit-learn + LightGBM + sentence-transformers + PyTorch (tensor loading only) — no changes to core ML stack
- **No data leakage:** S1/S2/S3 splits must remain strictly separated; graph edges must only use intra-split nodes; meta-models trained with OOF predictions only
- **Reproducibility:** All experiments must be seeded (SEED=42); results must be reproducible for paper submission
- **API input format:** JSON account data must match the schema derivable from BotSim-24 Users.csv + user_post_comment.json fields

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| AMR as delta-logit updater (Option C) | Avoids full second classifier; treats AMR as incremental evidence; reduces compute | ✓ Implemented and working |
| Mahalanobis distance for novelty | Analytically grounded OOD detection; no need for separate novelty model | ✓ Good |
| Logistic regression for meta-learners | Interpretable; resistant to overfitting on small S2 set; produces calibrated probabilities | ✓ Good |
| Bayesian optimization for thresholds (Optuna TPE) | More sample-efficient than grid search; scikit-optimize dropped due to Python 3.13 incompatibility | ✓ Working, 10 dims, reproducible |
| S1/S2/S3 three-way split | Avoids leakage in meta-learner training; S3 is fully held out for final evaluation | ✓ Good |
| Eager module-level joblib.load in api.py | Starlette TestClient doesn't trigger async lifespan; eager load makes tests work while lifespan handles production | ✓ Working |
| s2a_bot lower bound enforced | Prevents threshold inversion during Bayesian search (bot threshold below human threshold) | ✓ Necessary |

---
*Last updated: 2026-04-12 after v1.1 milestone start*
