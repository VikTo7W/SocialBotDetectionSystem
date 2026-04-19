# VERSION.md - Social Bot Detection System

## System Version

v1.5 - Unified Modular Codebase

Packaged on 2026-04-19. The maintained release contract is now a single dataset-parameterized codebase with shared feature extraction, shared cascade orchestration, maintained train/eval entry points, and paper-output generation rooted at `paper_outputs/` and `tables/`.

## Maintained Model Artifacts

### BotSim / Reddit-native artifact

- Artifact: `trained_system_botsim.joblib`
- Training entry point: `train_botsim.py`
- Evaluation entry point: `eval_botsim_native.py`
- Purpose: train and evaluate the Reddit/BotSim cascade on BotSim-24

### TwiBot-native artifact

- Artifact: `trained_system_twibot.joblib`
- Training entry point: `train_twibot.py`
- Evaluation entry point: `eval_twibot_native.py`
- Purpose: train and evaluate the TwiBot-native cascade on TwiBot-20

## Maintained Evaluation Surface

- `eval_botsim_native.py`
  - writes `paper_outputs/metrics_botsim.json`
  - writes `paper_outputs/confusion_matrix_botsim.png`

- `eval_reddit_twibot_transfer.py`
  - writes `paper_outputs/metrics_reddit_transfer.json`
  - writes `paper_outputs/confusion_matrix_reddit_transfer.png`

- `eval_twibot_native.py`
  - writes `paper_outputs/metrics_twibot_native.json`
  - writes `paper_outputs/confusion_matrix_twibot_native.png`

- `generate_table5.py`
  - reads the maintained `paper_outputs/*.json` metrics files
  - writes `tables/table5_cross_dataset.tex`

## Canonical Commands

### Train BotSim

```bash
python train_botsim.py
```

### Train TwiBot

```bash
python train_twibot.py
```

### Evaluate BotSim native

```bash
python eval_botsim_native.py
```

### Evaluate Reddit -> TwiBot transfer

```bash
python eval_reddit_twibot_transfer.py
```

### Evaluate TwiBot native

```bash
python eval_twibot_native.py
```

### Generate Table 5

```bash
python generate_table5.py
```

## Current Contract Notes

- The maintained orchestration layer is `CascadePipeline`.
- Shared extractors live under `features/`.
- Stage 2b retains only the AMR embedding delta-logit path; the LSTM path is removed.
- Bayesian threshold calibration is maintained as a single-trial contract.
- The repo keeps one maintained evaluation surface only; removed duplicate scripts should not be revived in docs or commands.

## Current Workspace Caveat

Phase 20 code is complete, but this specific workspace still does not have a fresh local `trained_system_twibot.joblib`. That means:

- `eval_twibot_native.py` is the correct maintained entry point
- `generate_table5.py` is the correct maintained Table 5 driver
- full local TwiBot-native runtime smoke remains blocked until the deferred TwiBot retraining rerun succeeds

## Historical References

The following names are historical only and not part of the maintained v1.5 contract:

- `trained_system_v12.joblib`
- `trained_system_twibot20.joblib`
- `evaluate_twibot20.py`
- `evaluate_twibot20_native.py`

See `README.md` for the full system description, feature-stage mapping, and reproduction guide.
