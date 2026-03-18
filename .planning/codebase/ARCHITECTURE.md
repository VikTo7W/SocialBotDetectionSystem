# Architecture

**Analysis Date:** 2026-03-18

## Pattern Overview

**Overall:** Multi-stage cascade classifier system with progressive refinement and novelty-aware gating.

**Key Characteristics:**
- Sequential three-stage pipeline where each stage targets different account characteristics
- Hierarchical routing logic with probabilistic thresholds and novelty scores driving decisions
- Out-of-fold (OOF) meta-learner approach to avoid overfitting during multi-stage stacking
- Dual feature pathways: base features (metadata, content) plus optional semantic text embeddings (AMR)

## Layers

**Data Loading & Preprocessing:**
- Purpose: Ingest BotSim-24 dataset and normalize account information
- Location: `botsim24_io.py`
- Contains: CSV parsing, JSON deserialization, timestamp normalization, account table construction
- Depends on: pandas, numpy, standard library
- Used by: `main.py` orchestration

**Feature Extraction (Stage-Specific):**
- Purpose: Convert raw account/message data into model-ready numerical representations
- Location: `features_stage1.py`, `features_stage2.py`, embedded in `botdetector_pipeline.py`
- Contains:
  - Stage 1: Account metadata ratios (name length, comment/submission counts, subreddit diversity, ratios)
  - Stage 2: Content embeddings (sentence-transformers), linguistic features, temporal patterns
  - Stage 3: Graph structural features (degree, weighted degree per edge type)
- Depends on: pandas, numpy, sentence-transformers, graph utilities
- Used by: Stage model training and inference

**Stage Models (Classifiers):**
- Purpose: Produce probability scores, uncertainty, and novelty measures at each detection stage
- Location: `botdetector_pipeline.py` (classes: `Stage1MetadataModel`, `Stage2BaseContentModel`, `Stage3StructuralModel`)
- Contains:
  - Base classifier (LightGBM or HistGradientBoosting)
  - Calibration layer (CalibratedClassifierCV)
  - Novelty scorer (MahalanobisNovelty via LedoitWolf covariance)
- Depends on: sklearn, lightgbm, numpy
- Used by: `train_system()`, `predict_system()`

**Semantic Refinement (AMR):**
- Purpose: Optionally refine base Stage 2 scores using Abstract Meaning Representation embeddings
- Location: `botdetector_pipeline.py` (classes: `TextEmbedder`, `AMRDeltaRefiner`)
- Contains: Sentence-transformer wrapper, AMR linearization stub, learned logit delta via gradient descent
- Depends on: sentence-transformers, numpy
- Used by: Stage 2 refinement path in training/prediction

**Routing & Gating:**
- Purpose: Decide whether to invoke next stage or perform special handling (AMR extraction)
- Location: `botdetector_pipeline.py` (functions: `gate_amr()`, `gate_stage3()`)
- Contains: Threshold-based boolean masks on probability, novelty, and disagreement
- Depends on: `StageThresholds` config dataclass, numpy
- Used by: `train_system()`, `predict_system()`

**Meta-Learners (Stacking):**
- Purpose: Combine outputs from stages into final predictions with out-of-fold training
- Location: `botdetector_pipeline.py` (functions: `train_meta12()`, `train_meta123()`, `oof_meta12_predictions()`)
- Contains:
  - meta12: Logistic regression combining Stage 1 + Stage 2 outputs
  - meta123: Logistic regression incorporating Stage 3 outputs
  - OOF stacking: StratifiedKFold loop to avoid leakage during S2 training
- Depends on: sklearn, pandas, numpy
- Used by: `train_system()`, `predict_system()`

**Orchestration:**
- Purpose: Coordinate full training pipeline and inference flow
- Location: `main.py`, `botdetector_pipeline.py` (functions: `train_system()`, `predict_system()`)
- Contains: Data split (S1/S2/S3), sequential stage training, meta-learner training, evaluation
- Depends on: All layers above
- Used by: Entry point for experiments

## Data Flow

**Training Flow (train_system):**

1. **Receive splits & edges:**
   - S1 (stage training): ~70% of data
   - S2 (meta training): ~15% of data with OOF predictions
   - S3 (held-out test): ~15% of data
   - Graph edges pre-filtered for each split in `main.py`

2. **Stage 1 on S1:**
   - Extract Stage 1 metadata features via `extract_stage1_matrix(S1)` → X1_tr
   - Train Stage1MetadataModel: LGB classifier + calibration + Mahalanobis novelty
   - Output: {p1, u1, n1, z1} (probability, uncertainty, novelty, logit)

3. **Stage 2 on S1:**
   - Extract Stage 2 content features via `extract_stage2_features(S1, embedder)` → X2_tr
   - Train Stage2BaseContentModel: LGB classifier + calibration + novelty
   - Output: {p2a, u2, n2, z2a} (base probability, uncertainty, novelty, logit)

4. **AMR Refiner on S1:**
   - Extract AMR embeddings via `extract_amr_embeddings_for_accounts(S1)`
   - Train AMRDeltaRefiner: learn logit adjustment h_amr → delta via gradient descent
   - Stores: weights and bias for z2a + delta

5. **Stage 3 on S1:**
   - Extract structural features via `build_graph_features_nodeidx(S1, edges_S1, nodes_total)` → X3_tr
   - Train Stage3StructuralModel: LGB classifier + calibration + novelty
   - Output: {p3, u3, n3, z3}

6. **Meta12 stacking on S2 (with OOF):**
   - Apply Stage 1 to S2 → {p1, z1, ...}
   - Apply Stage 2 to S2, including AMR gating:
     - Compute amr_mask = gate_amr(p2a, n2, z1, z2a, thresholds)
     - Extract AMR embeddings only for gated accounts
     - Refine z2 = z2a + AMR_delta for gated accounts
   - Build meta12 feature table: z1, z2, u1, u2, n1, n2, amr_used, disagreement
   - Run OOF via oof_meta12_predictions(): StratifiedKFold, train/predict on folds
   - Train final meta12 on all S2 with OOF predictions
   - Output: p12 (meta-combined probability)

7. **Stage 3 routing & meta123 on S2:**
   - Compute stage3_mask = gate_stage3(p12_oof, n1, n2, thresholds)
   - Apply Stage 3 only to masked subset → {p3, z3, n3}
   - Build meta123 feature table: z12 (logit of p12), z3, stage3_used, n1, n2, n3
   - Train meta123 logistic regression
   - Output: p_final (three-stage combined probability)

**Inference Flow (predict_system):**

1. **Stage 1 inference:**
   - Extract Stage 1 features from test dataframe
   - Apply stage1.predict() → {p1, u1, n1, z1}

2. **Stage 2 inference with optional AMR:**
   - Extract Stage 2 content features
   - Apply stage2a.predict() → {p2a, u2, n2, z2a}
   - Gate AMR: amr_mask = gate_amr(p2a, n2, z1, z2a, thresholds)
   - Extract AMR embeddings only for amr_mask == True
   - Refine: z2[amr_mask] = amr_refiner.refine(z2a[amr_mask], H_amr[amr_mask])
   - Output: {p2, z2, u2, n2}

3. **Meta12 combination:**
   - Build meta12 table from Stage outputs
   - Apply meta12.predict_proba() → p12

4. **Stage 3 gating:**
   - Compute stage3_mask = gate_stage3(p12, n1, n2, thresholds)
   - Extract structural features for entire dataset
   - Apply stage3.predict() only to stage3_mask == True subset
   - Default to p3=0.5, z3=0, n3=0 for non-routed samples

5. **Meta123 final combination:**
   - Build meta123 table with all three-stage outputs and stage3_used flag
   - Apply meta123.predict_proba() → p_final
   - Return DataFrame with per-account: p1, p2, p12, p3, p_final plus flags

**State Management:**
- Stateless feature extraction (functions operate on DataFrames in isolation)
- Trained models stored in `TrainedSystem` dataclass: stage1, stage2a, amr_refiner, meta12, stage3, meta123, embedder, config
- No mutable global state; all state passed through function arguments and return values

## Key Abstractions

**MahalanobisNovelty:**
- Purpose: Detect out-of-distribution samples using Mahalanobis distance with shrinkage covariance
- Examples: `botdetector_pipeline.py` lines 44-68
- Pattern: Fit on training features, score test samples; integrated into every stage model

**StageThresholds:**
- Purpose: Configure all routing decisions (Stage 1 early exit, Stage 2 AMR gating, Stage 3 routing)
- Examples: `botdetector_pipeline.py` lines 155-171
- Pattern: Dataclass with default values; can be overridden per experiment

**TrainedSystem:**
- Purpose: Encapsulate all trained components for inference
- Examples: `botdetector_pipeline.py` lines 490-503
- Pattern: Dataclass holding all trained models, configs, and embedder

**FeatureConfig:**
- Purpose: Configure feature extraction settings (embedding model, max messages, max chars)
- Examples: `botdetector_pipeline.py` lines 75-83
- Pattern: Dataclass with configurable embedding and text length limits

## Entry Points

**main.py (Orchestration):**
- Location: `/c/Users/dzeni/PycharmProjects/SocialBotDetectionSystem/main.py`
- Triggers: Manual execution; loads dataset, orchestrates train/predict
- Responsibilities:
  - Load Users.csv and user_post_comment.json
  - Build account tables with message aggregation
  - Create stratified S1/S2/S3 splits
  - Load and filter graph edges per split
  - Call train_system() and predict_system()
  - Print classification metrics on S3

**train_system():**
- Location: `botdetector_pipeline.py` lines 505-614
- Triggers: Called from main.py
- Responsibilities:
  - Initialize and train all stage models
  - Build meta-learner training data
  - Handle OOF stacking for meta12
  - Return TrainedSystem object

**predict_system():**
- Location: `botdetector_pipeline.py` lines 617-696
- Triggers: Called from main.py after train_system()
- Responsibilities:
  - Apply all stages with routing logic
  - Compute final combined probabilities
  - Return DataFrame with per-account predictions and metadata

## Error Handling

**Strategy:** Defensive programming with explicit null checks and fallback defaults.

**Patterns:**
- NaN handling: `np.nan_to_num()` in feature extraction (features_stage1.py line 39)
- Missing text: Empty string defaults in botsim24_io.py; empty arrays return zero vectors
- Unfitted models: Explicit RuntimeError on predict() if not fitted (botdetector_pipeline.py lines 62-63, 207, 248, 338)
- Division by zero: eps=1e-6 in ratio calculations (features_stage1.py line 20)
- Temporal data: Filters out None timestamps in botsim24_io.py line 164; defaults to 0.0 temporal stats
- Graph coverage: Main.py comments note uncertainty about full edge coverage; Stage 3 disabled in example

## Cross-Cutting Concerns

**Logging:** console.print() and simple print() statements; no structured logging framework

**Validation:**
- Assert for data integrity (main.py line 29: check node_idx mapping completeness)
- Sanity checks on label distribution (main.py line 38)

**Authentication:** Not applicable; file-based dataset

**Reproducibility:**
- Random seed passed through all layers (random_state=42 by default)
- StratifiedKFold in OOF ensures consistent fold splits
- LGB and HistGradientBoosting both respect random_state parameter

**Calibration:** CalibratedClassifierCV ensures output probabilities are well-calibrated (not raw model scores)

**Novelty Integration:** Every stage produces novelty scores independently; combined in meta-learners for routing decisions

---

*Architecture analysis: 2026-03-18*
