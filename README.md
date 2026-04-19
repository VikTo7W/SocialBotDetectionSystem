# SocialBotDetectionSystem

## Overview

This repository contains a staged cascade for social bot detection with a single maintained v1.5 codebase shared across two datasets:

- BotSim-24 for Reddit-native training and evaluation
- TwiBot-20 for zero-shot transfer and TwiBot-native training/evaluation

The maintained system is organized around shared feature extractors, a shared cascade pipeline, clean training/evaluation entry points, and paper-output scripts. The cascade routes each account through progressively more expensive evidence sources:

1. Stage 1: account-level metadata and activity signals
2. Stage 2a: text/content and timeline behavior
3. Stage 2b: AMR-style semantic refinement as a delta on the Stage 2a logit
4. Stage 3: graph structure features
5. Meta-learners and threshold calibration: combine stage outputs into one final bot probability

The maintained v1.5 entry points are:

- `train_botsim.py`
- `train_twibot.py`
- `eval_botsim_native.py`
- `eval_reddit_twibot_transfer.py`
- `eval_twibot_native.py`
- `generate_table5.py`

## Architecture

### Core modules

- `features/stage1.py`: shared Stage 1 extractor for `botsim` and `twibot`
- `features/stage2.py`: shared Stage 2a text/behavior extractor and Stage 2b AMR embedding extractor
- `features/stage3.py`: shared graph-structure extractor
- `cascade_pipeline.py`: maintained fit/predict orchestration for the whole cascade
- `data_io.py`: shared dataset-aware loading helpers
- `evaluate.py`: shared evaluation helper that computes overall, per-stage, and routing metrics

### Entry points

- `train_botsim.py`: trains the Reddit/BotSim cascade and writes `trained_system_botsim.joblib`
- `train_twibot.py`: trains the TwiBot-native cascade and writes `trained_system_twibot.joblib`
- `eval_botsim_native.py`: evaluates the Reddit-trained model on BotSim-24
- `eval_reddit_twibot_transfer.py`: evaluates the Reddit-trained model on TwiBot-20 in transfer mode
- `eval_twibot_native.py`: evaluates the TwiBot-trained model on TwiBot-20
- `generate_table5.py`: builds `tables/table5_cross_dataset.tex` from the maintained `paper_outputs/*.json`

### Compatibility layer

`botdetector_pipeline.py` is a re-export shim. All stage-model classes, math helpers, routing logic, and contract types are defined in `cascade_pipeline.py` and re-exported from `botdetector_pipeline.py` for any callers that have not yet been updated. Do not add new pipeline logic to `botdetector_pipeline.py`; all new orchestration code belongs in `cascade_pipeline.py`.

## Technique Rationale

### LightGBM stage models

LightGBM is used for the stage classifiers because the inputs are tabular, heterogeneous, and mix dense embeddings with hand-engineered features. It gives strong performance without forcing the whole system into a single opaque neural pipeline.

### Mahalanobis novelty scores

Each stage carries a novelty signal so routing can react not just to confidence, but also to whether an account looks out-of-distribution for that stage. This matters especially for transfer from Reddit to Twitter, where a model can be overconfident on unfamiliar structure.

### AMR delta-logit refinement

Stage 2b does not replace Stage 2a with a second classifier. Instead, it learns a correction to the Stage 2a logit when the account looks uncertain, novel, or contradictory enough to justify a semantic second look. In v1.5 the maintained path is AMR embedding delta-logit only; the older LSTM variant is removed.

### Logistic-regression stackers

The cascade uses logistic regression for `meta12` and `meta123` because the stacking sets are smaller than the base-model training sets and the combiner should stay interpretable. This keeps the final probability grounded in simple stage-level evidence rather than another large flexible model.

### Bayesian threshold calibration

The system trains probabilistic models and then calibrates the routing/decision thresholds separately. This keeps model fitting and operating-point selection decoupled. In v1.5 the maintained calibration contract is a single trial, not the older multi-restart loop.

## Dataset And Stage Mapping

The codebase uses one extractor package with a `dataset` parameter. The exact signals differ by dataset because the source data differs.

### BotSim-24

#### Stage 1

BotSim Stage 1 uses compact Reddit/account activity signals from `features/stage1.py`:

- username length
- submission count
- first and second comment counts
- total comment count
- subreddit count
- submission-to-comment and submission-to-subreddit ratios

This stage is cheap and acts as the first routing screen.

#### Stage 2a

BotSim Stage 2a combines pooled text embeddings with simple message-level behavior and temporal signals from `features/stage2.py`:

- pooled sentence-transformer embeddings over recent messages
- mean linguistic features such as text length, token uniqueness, punctuation ratio, and digit ratio
- posting-rate and inter-arrival statistics when timestamps exist
- hour-of-day entropy
- cross-message similarity and near-duplicate fraction

This stage captures content style and activity patterns beyond raw account metadata.

#### Stage 2b

BotSim Stage 2b uses the shared AMR embedding extraction path:

- one semantic anchor embedding per account
- learned delta-logit refinement applied only to gated accounts

It exists to refine uncertain Stage 2a cases rather than score every account independently.

#### Stage 3

BotSim Stage 3 uses graph features over filtered split-local edges from `features/stage3.py`:

- in-degree and out-degree
- weighted in/out totals
- per-edge-type degree and weight features

This stage is reserved for the hardest accounts because graph computation is more expensive and only needed when earlier evidence is insufficient.

### TwiBot-20

#### Stage 1

TwiBot Stage 1 uses Twitter-native metadata and lightweight activity summaries from `features/stage1.py`:

- screen-name length
- screen-name digit ratio
- statuses, followers, and friends counts
- follower/friend ratio
- account age and statuses per day
- tweet count loaded
- domain count
- retweet, modified-tweet, and original fractions
- count of unique RT/MT targets

This is intentionally Twitter-native rather than a fake Reddit column mapping.

#### Stage 2a

TwiBot Stage 2a uses pooled message embeddings plus per-message statistics from the same shared extractor:

- pooled sentence-transformer embeddings
- mean text-length, token-uniqueness, punctuation-ratio, and digit-ratio features
- message count
- message-length variance
- cross-message similarity
- near-duplicate fraction
- non-empty message fraction

Unlike BotSim, this path does not rely on Reddit-style timestamp-derived temporal features when that information is absent or structurally different.

#### Stage 2b

TwiBot Stage 2b is the same maintained AMR embedding delta-logit contract:

- semantic anchor embedding from the shared extractor
- gated correction to Stage 2a logits

There is no maintained LSTM Stage 2b path in v1.5.

#### Stage 3

TwiBot Stage 3 uses graph features from the follower/following graph:

- in-degree and out-degree
- weighted totals
- per-edge-type degree and weight features for following/follower relations

The extractor stays shared, but the underlying edge semantics reflect the Twitter graph rather than Reddit interaction tensors.

### Transfer-specific note

`eval_reddit_twibot_transfer.py` adapts TwiBot accounts into the minimum BotSim-style Stage 1/2a surface needed by the Reddit-trained model. That adapter exists only for evaluation of the transfer baseline. It is not the maintained feature definition for TwiBot-native training.

## Training And Evaluation Flow

### Training

- `train_botsim.py` loads BotSim-24, creates S1/S2/S3 splits, trains the shared cascade, calibrates thresholds, and writes `trained_system_botsim.joblib`
- `train_twibot.py` loads TwiBot-20 `train/dev/test`, trains the shared cascade, calibrates on `dev.json`, and writes `trained_system_twibot.joblib`

### Evaluation

- `eval_botsim_native.py` writes:
  - `paper_outputs/metrics_botsim.json`
  - `paper_outputs/confusion_matrix_botsim.png`
- `eval_reddit_twibot_transfer.py` writes:
  - `paper_outputs/metrics_reddit_transfer.json`
  - `paper_outputs/confusion_matrix_reddit_transfer.png`
- `eval_twibot_native.py` writes:
  - `paper_outputs/metrics_twibot_native.json`
  - `paper_outputs/confusion_matrix_twibot_native.png`
- `generate_table5.py` reads the three metrics JSON files and writes:
  - `tables/table5_cross_dataset.tex`

The shared `evaluate.py` helper reports:

- `overall`
- `per_stage`
- `routing`

## Data Requirements

### BotSim-24

Required for BotSim training/evaluation:

- `Users.csv`
- `user_post_comment.json`
- `edge_index.pt`
- `edge_type.pt`
- `edge_weight.pt`

### TwiBot-20

Required for TwiBot training/evaluation:

- `train.json`
- `dev.json`
- `test.json`

## Reproduction Guide

### 1. Train the maintained BotSim artifact

```bash
python train_botsim.py
```

Expected artifact:

- `trained_system_botsim.joblib`

### 2. Train the maintained TwiBot artifact

```bash
python train_twibot.py
```

Expected artifact:

- `trained_system_twibot.joblib`

### 3. Evaluate the Reddit-trained model on BotSim-24

```bash
python eval_botsim_native.py
```

Expected outputs:

- `paper_outputs/metrics_botsim.json`
- `paper_outputs/confusion_matrix_botsim.png`

### 4. Evaluate the Reddit-trained model on TwiBot-20 transfer

```bash
python eval_reddit_twibot_transfer.py
```

Expected outputs:

- `paper_outputs/metrics_reddit_transfer.json`
- `paper_outputs/confusion_matrix_reddit_transfer.png`

### 5. Evaluate the TwiBot-trained model on TwiBot-20 native

```bash
python eval_twibot_native.py
```

Expected outputs:

- `paper_outputs/metrics_twibot_native.json`
- `paper_outputs/confusion_matrix_twibot_native.png`

### 6. Generate Table 5

```bash
python generate_table5.py
```

Expected output:

- `tables/table5_cross_dataset.tex`

## Current Output Status

Confirmed present in this workspace now:

- `paper_outputs/metrics_botsim.json`
- `paper_outputs/confusion_matrix_botsim.png`
- `paper_outputs/metrics_reddit_transfer.json`
- `paper_outputs/confusion_matrix_reddit_transfer.png`

Still blocked on the deferred fresh TwiBot artifact rerun:

- `trained_system_twibot.joblib`
- `paper_outputs/metrics_twibot_native.json`
- `paper_outputs/confusion_matrix_twibot_native.png`

Because of that missing local artifact, `eval_twibot_native.py` and `generate_table5.py` are correct maintained entry points but may still be blocked in this specific workspace until the TwiBot retraining run completes successfully.

## Known Caveats

- Windows pytest temp-directory cleanup remains permission-sensitive in this workspace. The production code path is unaffected; the issue is in local test harness cleanup.
- The Stage 2b AMR path is still an embedding-based proxy, not true AMR graph parsing.
- Multi-seed stability and richer paper uncertainty analysis remain deferred.
- The Reddit-to-TwiBot transfer result is expected to be much weaker than the TwiBot-native path; that gap is part of the research story, not a bug.

## Historical Notes

- Older duplicate evaluation scripts such as `evaluate_twibot20.py` and `evaluate_twibot20_native.py` are no longer part of the maintained surface.
- Older artifact names such as `trained_system_v12.joblib` and `trained_system_twibot20.joblib` remain historical references only and should not be used for new reproduction instructions.

## Release Contract

See `VERSION.md` for the concise v1.5 release contract.
