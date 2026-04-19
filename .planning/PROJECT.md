# Social Bot Detection System

## What This Is

A multi-stage cascade classifier for detecting social bots on Reddit using the BotSim-24 dataset. The system escalates accounts through three detection stages (metadata -> content/temporal -> graph structure), using novelty-aware routing to balance compute efficiency with accuracy. The research contribution is the cascade architecture with AMR semantic refinement and transfer experiments.

v1.0 delivered Bayesian threshold calibration, a paper-ready S3 evaluation module, and a REST API for single-account inference.
v1.1 delivered Stage 2 leakage removal, new behavioral and similarity features, a clean retrain, and paper-ready ablation tables.
v1.2 delivered the TwiBot-20 zero-shot transfer path for the Reddit-trained cascade.
v1.3 delivered a reproducible TwiBot evaluation flow, fresh transfer evidence, and release-facing documentation.
v1.4 delivered a separate TwiBot-native supervised baseline, a maintained Reddit-transfer-vs-native comparison path, and retirement of online novelty recalibration from the maintained Reddit-transfer story.
v1.5 delivered a unified modular codebase parameterized by dataset, LSTM Stage 2b removal, single-trial calibration, clean training and evaluation entry points, fresh model retraining, and a comprehensive README.
v1.6 targets a second cleanup pass that collapses remaining duplicate maintained surfaces, reduces file count further, and adds a genuine low-noise comment layer to the simplified codebase.

## Current Milestone: v1.6 Structural Consolidation and Code Surface Cleanup

**Goal:** Collapse remaining duplicate maintained surfaces so the project has one clear pipeline layer, one unified feature module, one unified dataset I/O module, fewer active files overall, and a final short comment pass that improves readability without bloating the code.

**Target features:**
- Unified pipeline surface -> one maintained orchestration layer instead of overlapping `botdetector_pipeline.py` and `cascade_pipeline.py`
- Unified feature module -> one maintained feature-extraction file or module surface with one unifying class contract for BotSim-24 and TwiBot-20
- Unified dataset I/O -> one maintained dataset loading/building surface covering both BotSim-24 and TwiBot-20
- File-count reduction -> redundant compatibility layers and duplicate maintained helpers removed wherever the simplified surface already covers the behavior
- Caller preservation -> maintained training, evaluation, API, and batch entry points still work against the consolidated code surface
- Output preservation -> artifact names, metric schema, and paper-output filenames stay stable while internal structure is simplified
- Comment pass -> short lowercase descriptive comments added to maintained classes and methods where they genuinely help the next reader

## Current State

v1.5 shipped on 2026-04-19. Phases 17 through 21 completed the first modular unification pass: the codebase now has shared dataset-parameterized feature extraction, a shared `CascadePipeline` orchestration layer with maintained single-trial calibration, maintained training entry points, maintained evaluation entry points, a standalone Table 5 driver, and documentation aligned to the maintained modular surface.

v1.6 starts from that shipped baseline and focuses on structural consolidation rather than new modeling behavior. The main remaining cleanup targets are overlapping maintained pipeline layers, a still-fragmented feature surface, split dataset I/O files, and the lack of a final intentional comment pass across the maintained code.

Known gaps carried forward:
- Full pytest green-suite is still blocked in this Windows workspace by temp-dir cleanup permissions
- Fresh `trained_system_twibot.joblib` still needs the user-deferred full local rerun/debug cycle from Phase 19
- Stale pre-Phase-12 TwiBot artifacts remain at repo root

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
- Reproducible Reddit-transfer evaluation flow with stable output routing - v1.3/v1.4
- Fresh Reddit-transfer evidence generated on TwiBot-20 - v1.3
- Twitter-native Stage 1, Stage 2, and Stage 3 extractors for TwiBot-20 - v1.4
- Separate TwiBot-native cascade training and evaluation entry points - v1.4
- Reddit-transfer-vs-native comparison artifact and Table 5 rewrite - v1.4
- Release-facing docs for the maintained two-artifact comparison story - v1.4
- Unified dataset-parameterized feature extraction shared across BotSim-24 and TwiBot-20 - v1.5
- Unified cascade training core shared across maintained callers - v1.5
- Stage 2b LSTM path removed; AMR embedding delta-logit version only - v1.5
- Single-trial Bayesian threshold calibration for both systems - v1.5
- Three maintained evaluation entry points: Reddit-native, Reddit-to-TwiBot transfer, TwiBot-native - v1.5
- Fresh BotSim retraining from unified code plus a deferred manual TwiBot full-retraining rerun - v1.5
- Paper outputs from unified evaluation - v1.5
- Comprehensive README with technique rationale and feature-stage mapping - v1.5

### Active

- Collapse overlapping maintained pipeline responsibilities into one clear source of truth - v1.6
- Consolidate maintained feature extraction into one unified file or module surface with one unifying class contract - v1.6
- Consolidate BotSim-24 and TwiBot-20 dataset I/O into one maintained surface - v1.6
- Reduce active repo file count by removing redundant maintained helpers and compatibility layers - v1.6
- Preserve maintained training, evaluation, API, and batch behavior while simplifying internals - v1.6
- Add short lowercase descriptive comments to maintained classes and methods where they materially help readability - v1.6

### Out of Scope

| Feature | Reason |
|---------|--------|
| Real-time streaming classification | Batch inference only |
| Frontend or dashboard UI | API and scripts only |
| Model retraining through the API | Offline training only |
| Profile or description features | Permanently excluded after the leakage audit |
| New model families or architecture redesign | This milestone is structural cleanup, not algorithm replacement |
| Changing maintained artifact names or paper-output filenames | External contract stays stable while internals are simplified |
| Online novelty recalibration in the maintained Reddit path | Removed in v1.4 because it does not improve transfer results |

## Context

- **Dataset:** BotSim-24 provides Reddit metadata, timelines, and graph tensors. TwiBot-20 provides Twitter metadata, tweet timelines, and follower/following neighbor lists with canonical train/val/test splits.
- **Architecture:** Three-stage cascade with novelty-aware gating and logistic-regression stackers.
- **Current state:** `trained_system_v12.joblib` is the active historical Reddit-trained model. `trained_system_botsim.joblib` is the fresh maintained BotSim artifact. The maintained training surface is `train_botsim.py` and `train_twibot.py`. The maintained evaluation surface is `eval_botsim_native.py`, `eval_reddit_twibot_transfer.py`, `eval_twibot_native.py`, and `generate_table5.py`. `train_twibot.py` is the maintained TwiBot training entry point, but the fresh `trained_system_twibot.joblib` rerun is still deferred for manual follow-up after Phase 19 closeout.
- **AMR status:** The Stage 2b semantic path is still an embedding-based proxy, not true AMR graph parsing.
- **Cleanup target:** The next milestone is about collapsing duplicate maintained code surfaces without weakening the released v1.5 external contract.
- **Paper contribution:** The novel contribution is the cascade architecture. v1.4 strengthened the paper by showing the cascade works when platform-matched and remains weak under Reddit-trained zero-shot transfer.

## Constraints

- **Tech stack:** Python, scikit-learn, LightGBM, sentence-transformers, and PyTorch tensor loading only
- **No leakage:** keep split boundaries, graph filtering, OOF stacking, and Stage 2 leakage exclusions intact
- **Zero-shot transfer (Reddit model):** TwiBot-20 labels are not used to adapt the Reddit-trained cascade
- **Twitter-native features:** TwiBot-20 cascade must use only fields genuinely present in TwiBot-20 - no imputing or zero-fill stand-ins for absent Reddit analogs
- **Separate artifacts:** Reddit-trained and TwiBot-trained systems are stored as distinct joblib files; neither overwrites the other
- **External contract stability:** maintained artifact names, metric schema, and paper-output filenames must remain stable across the cleanup
- **Reproducibility:** seed all experiments with `SEED=42`

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| AMR as delta-logit updater | Preserves AMR as incremental evidence instead of a second full classifier | Good |
| Mahalanobis distance for novelty | Analytically grounded OOD signal without extra model training | Good |
| Logistic regression for meta-learners | Interpretable and resistant to overfitting on the small stacking set | Good |
| Bayesian optimization for thresholds | More sample-efficient than grid search and compatible with current environment | Simplified to one maintained trial in v1.5 |
| S1/S2/S3 split discipline | Prevents leakage during training and evaluation | Good |
| Preserve v11 alongside v12 | Needed for leakage-audit and ablation comparisons | Good |
| Missingness-aware handling was acceptable as an interim transfer bridge | Avoided fake in-distribution signals before the native feature rewrite | Adopted in v1.2 |
| Windows temp friction is pytest-level, not production | Production code does not depend on temp-dir plumbing; the issue is workspace-local test cleanup | Confirmed |
| `VERSION.md` is the concise release-contract source of truth | Keeps artifact naming and maintained-vs-historical boundaries explicit | Adopted |
| Online novelty recalibration is historical only after v1.4 | It did not materially improve TwiBot transfer performance and complicated the maintained story | Adopted |
| v1.6 will favor consolidation over compatibility shims where maintained callers already cover the behavior | Reduces file count and duplicate maintenance burden without changing the public release contract | Adopted |

---
*Last updated: 2026-04-19 - Milestone v1.6 started (structural consolidation and code surface cleanup)*
