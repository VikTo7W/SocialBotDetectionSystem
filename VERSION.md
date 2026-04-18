# VERSION.md - Social Bot Detection System

## System Version

v1.4 - Twitter-Native Supervised Baseline

Packaged on 2026-04-18. The maintained release contract now includes two
distinct TwiBot-20 evaluation artifacts:

- Reddit-trained transfer baseline: `trained_system_v12.joblib`
- TwiBot-native supervised baseline: `trained_system_twibot20.joblib`

The active comparison story is Reddit transfer vs TwiBot-native performance on
the TwiBot-20 test split. The older static-vs-recalibrated Reddit transfer
evidence from Phase 12 remains archived for provenance only.

## Model Artifacts

### Reddit transfer baseline

- Artifact: `trained_system_v12.joblib`
- Entry point: `evaluate_twibot20.py`
- Purpose: run the BotSim-24-trained cascade on TwiBot-20 without retraining

### TwiBot-native supervised baseline

- Artifact: `trained_system_twibot20.joblib`
- Entry point: `evaluate_twibot20_native.py`
- Purpose: run the TwiBot-trained cascade on TwiBot-20 using the native feature pipeline

## Evaluation Entry Points

- `evaluate_twibot20.py`
  Maintained Reddit-transfer evaluation path. Writes the static Reddit-transfer
  artifacts only.

- `evaluate_twibot20_native.py`
  TwiBot-native evaluation path. Writes native results and metrics for the
  supervised baseline artifact.

- `ablation_tables.py`
  Builds the paper-facing Reddit-vs-native comparison artifact and writes Table
  5 outputs.

## Canonical Commands

### Reddit transfer baseline

```bash
python evaluate_twibot20.py test.json trained_system_v12.joblib \
  .planning/phases/16-comparative-paper-outputs-and-reddit-cleanup/artifacts
```

### TwiBot-native baseline

```bash
python evaluate_twibot20_native.py test.json trained_system_twibot20.joblib \
  .planning/phases/15-twibot-cascade-training-and-evaluation/artifacts
```

### Paper-facing comparison

```bash
python ablation_tables.py
```

## Maintained Output Files

### Reddit transfer artifacts

Written to `.planning/phases/16-comparative-paper-outputs-and-reddit-cleanup/artifacts/`:

- `results_twibot20_reddit_transfer.json`
- `metrics_twibot20_reddit_transfer.json`

### TwiBot-native artifacts

Written to `.planning/phases/15-twibot-cascade-training-and-evaluation/artifacts/`:

- `results_twibot20_native.json`
- `metrics_twibot20_native.json`
- `calibration_twibot20_native.json`

### Comparison / paper artifacts

Written by `ablation_tables.py`:

- `.planning/phases/16-comparative-paper-outputs-and-reddit-cleanup/artifacts/metrics_twibot20_reddit_vs_native.json`
- `tables/table5_cross_dataset.tex`
- `tables/table5_transfer_interpretation.txt`

## Historical Outputs

The following remain archived but are no longer the maintained default:

- `metrics_twibot20_comparison.json`
- `transfer_evidence_summary.json`

Those files describe the older Phase 12 static-vs-recalibrated Reddit transfer
comparison.

## Environment Overrides

`ablation_tables.py` honors:

- `TWIBOT_COMPARISON_PATH`
- `TWIBOT_REDDIT_METRICS_PATH`
- `TWIBOT_NATIVE_METRICS_PATH`
- `TABLE5_OUTPUT_PATH`
- `TABLE5_INTERPRETATION_PATH`

## Current Contract Notes

- Online novelty recalibration is no longer part of the maintained Reddit
  transfer path.
- Reddit-trained and TwiBot-trained artifacts must stay separate.
- The maintained paper-facing comparison is Reddit transfer vs TwiBot-native,
  not static vs recalibrated transfer.

See `README.md` for the end-to-end reproduction guide and caveats.
