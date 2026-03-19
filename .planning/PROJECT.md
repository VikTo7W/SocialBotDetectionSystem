# Social Bot Detection System

## What This Is

A multi-stage cascade classifier for detecting social bots on Reddit using the BotSim-24 dataset. The system progressively escalates accounts through three detection stages (metadata → content/temporal → graph structure), using novelty-aware routing to balance compute efficiency with accuracy. Designed as a research contribution: the cascade architecture with AMR semantic refinement is the novel element, targeting a paper submission with competitive results.

## Core Value

The cascade must produce a single, well-calibrated bot probability per account — routing efficiently through stages while catching sophisticated bots that simple models miss.

## Requirements

### Validated

- ✓ Stage 1 metadata classifier — LightGBM on numeric metadata (counts, ratios, name length) with Mahalanobis novelty scoring and CalibratedClassifierCV — existing
- ✓ Stage 2a content/temporal classifier — Sentence-transformer embeddings (MiniLM) fused with linguistic/temporal features, LightGBM + calibration + novelty — existing
- ✓ Stage 2b AMR delta refiner — learned logit adjustment from AMR embeddings via gradient descent, applied to gated subset — existing
- ✓ Stage 3 structural classifier — LightGBM on graph-derived features (weighted/unweighted in/out degrees per edge type) with calibration + novelty — existing
- ✓ AMR gating logic — gate_amr() applies AMR refinement only when p2a is uncertain, novelty is high, or Stage 1/2 strongly disagree — existing
- ✓ Stage 3 routing logic — gate_stage3() escalates accounts when p12 is uncertain or novelty is high — existing
- ✓ Meta12 stacking combiner — logistic regression over Stage 1 + Stage 2 logits, novelty scores, and amr_used flag — existing
- ✓ Meta123 final combiner — logistic regression over meta12 + Stage 3 outputs with stage3_used flag — existing
- ✓ OOF stacking for leakage-free meta-model training — StratifiedKFold over S2 split — existing
- ✓ S1/S2/S3 data splits — ~70%/15%/15% stratified splits with per-split graph edge filtering — existing
- ✓ BotSim-24 data loading — CSV parsing, JSON deserialization, timestamp normalization, account table construction — existing
- ✓ TrainedSystem encapsulation — single dataclass holding all trained models, configs, embedder — existing

### Active

- [ ] Threshold calibration via Bayesian optimization — optimize novelty and probability routing thresholds on S2/validation to maximize F1/AUC on S3
- [ ] REST API wrapper — POST /predict endpoint accepting JSON account data, returning bot probability (p_final) and label
- [ ] End-to-end evaluation pipeline — full metrics on S3 (F1, AUC, precision/recall) plus per-stage breakdown and routing statistics

### Out of Scope

- Real-time streaming classification — batch inference only; no streaming ingestion
- Multi-platform detection — BotSim-24 (Reddit) only; no generalization to Twitter/X or other platforms in v1
- Full AMR parser integration — AMR linearization is currently a stub; true graph-based AMR parsing deferred
- Frontend / dashboard UI — API only; no visualization layer
- Model retraining via API — serve only; training runs offline

## Context

- **Dataset:** BotSim-24 — Reddit account dataset with Users.csv (metadata) and user_post_comment.json (timeline). Graph edges stored as PyTorch tensors (edge_index.pt, edge_type.pt, edge_weight.pt).
- **Architecture:** Three-stage cascade with novelty-aware gating. Each stage produces (p, u, n, z). Meta-learners combine stages via logistic regression stacking. Novelty overrides confidence — high novelty forces escalation regardless of classifier confidence.
- **Current thresholds:** Hardcoded defaults in StageThresholds dataclass (e.g., s1_bot=0.98, n1_max_for_exit=3.0). These are initial guesses, not calibrated values.
- **AMR status:** Stage 2b is implemented as a learned delta-logit over sentence-transformer embeddings of text. True AMR graph parsing is a stub — the semantic representation is approximated via embedding similarity. This is the "Option C delta updater" design.
- **Paper contribution:** The cascade architecture + novelty-aware routing + AMR refinement combination is the novel element. Requires ablation study showing each stage contributes.

## Constraints

- **Tech stack:** Python + scikit-learn + LightGBM + sentence-transformers + PyTorch (tensor loading only) — no changes to core ML stack
- **No data leakage:** S1/S2/S3 splits must remain strictly separated; graph edges must only use intra-split nodes; meta-models trained with OOF predictions only
- **Reproducibility:** All experiments must be seeded (SEED=42); results must be reproducible for paper submission
- **API input format:** JSON account data must match the schema derivable from BotSim-24 Users.csv + user_post_comment.json fields

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| AMR as delta-logit updater (Option C) | Avoids full second classifier; treats AMR as incremental evidence; reduces compute | — Pending |
| Mahalanobis distance for novelty | Analytically grounded OOD detection; no need for separate novelty model | — Pending |
| Logistic regression for meta-learners | Interpretable; resistant to overfitting on small S2 set; produces calibrated probabilities | — Pending |
| Bayesian optimization for thresholds | More sample-efficient than grid search for high-dimensional threshold space | — Pending |
| S1/S2/S3 three-way split | Avoids leakage in meta-learner training; S3 is fully held out for final evaluation | — Pending |

---
*Last updated: 2026-03-19 after initialization*
