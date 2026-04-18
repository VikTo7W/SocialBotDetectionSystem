# SocialBotDetectionSystem

## Overview

A three-stage cascade classifier for social bot detection with metadata,
content/temporal, and graph stages. The original system was trained on the
BotSim-24 Reddit dataset; v1.4 adds a Twitter-native TwiBot-20 baseline so the
repo can compare:

- Reddit-trained cascade on TwiBot-20 (`trained_system_v12.joblib`)
- TwiBot-trained cascade on TwiBot-20 (`trained_system_twibot20.joblib`)

The maintained paper-facing comparison is no longer "static vs recalibrated"
Reddit transfer. That older Phase 12 evidence remains archived for provenance,
but the active v1.4 story is Reddit transfer vs TwiBot-native supervised
performance.

## Environment Assumptions

- Python: CPython 3.13
- Key dependencies: `scikit-learn`, `lightgbm`, `sentence-transformers`,
  `torch`, `joblib`, `numpy`, `pandas`
- Deterministic seed: `SEED=42`
- OS: Windows 10 was the packaging environment

## Required Inputs

For the maintained Phase 16 comparison flow:

- `test.json` — TwiBot-20 test split
- `trained_system_v12.joblib` — Reddit-trained transfer baseline artifact
- `trained_system_twibot20.joblib` — TwiBot-native supervised artifact

Optional but useful when regenerating native artifacts from scratch:

- `train.json`
- `dev.json`

For the full `ablation_tables.py` run, the repo-root BotSim-24 assets are still
needed:

- `Users.csv`
- `user_post_comment.json`
- `edge_index.pt`
- `edge_type.pt`
- `edge_weight.pt`
- `results_v10.json`

## Reproduction Guide

### Step 1 — Confirm the model artifacts and TwiBot test split are present

```bash
ls test.json trained_system_v12.joblib trained_system_twibot20.joblib
```

### Step 2 — Generate the maintained Reddit-transfer baseline artifacts

```bash
python evaluate_twibot20.py test.json trained_system_v12.joblib \
  .planning/phases/16-comparative-paper-outputs-and-reddit-cleanup/artifacts
```

This writes:

- `.planning/phases/16-comparative-paper-outputs-and-reddit-cleanup/artifacts/results_twibot20_reddit_transfer.json`
- `.planning/phases/16-comparative-paper-outputs-and-reddit-cleanup/artifacts/metrics_twibot20_reddit_transfer.json`

### Step 3 — Generate the TwiBot-native evaluation artifacts

If the Phase 15 native metrics are not already present, run:

```bash
python evaluate_twibot20_native.py test.json trained_system_twibot20.joblib \
  .planning/phases/15-twibot-cascade-training-and-evaluation/artifacts
```

This writes:

- `.planning/phases/15-twibot-cascade-training-and-evaluation/artifacts/results_twibot20_native.json`
- `.planning/phases/15-twibot-cascade-training-and-evaluation/artifacts/metrics_twibot20_native.json`

### Step 4 — Regenerate the paper-facing comparison and Table 5 outputs

```bash
python ablation_tables.py
```

This writes:

- `.planning/phases/16-comparative-paper-outputs-and-reddit-cleanup/artifacts/metrics_twibot20_reddit_vs_native.json`
- `tables/table5_cross_dataset.tex`
- `tables/table5_transfer_interpretation.txt`

## Environment Overrides

`ablation_tables.py` supports the following overrides:

- `TWIBOT_COMPARISON_PATH` — override the Phase 16 Reddit-vs-native comparison artifact path
- `TWIBOT_REDDIT_METRICS_PATH` — override the Reddit-transfer metrics path
- `TWIBOT_NATIVE_METRICS_PATH` — override the TwiBot-native metrics path
- `TABLE5_OUTPUT_PATH` — override where `table5_cross_dataset.tex` is written
- `TABLE5_INTERPRETATION_PATH` — override where `table5_transfer_interpretation.txt` is written

Example:

```bash
TWIBOT_REDDIT_METRICS_PATH=/alt/reddit_metrics.json \
TWIBOT_NATIVE_METRICS_PATH=/alt/native_metrics.json \
TABLE5_OUTPUT_PATH=/alt/table5.tex \
TABLE5_INTERPRETATION_PATH=/alt/table5_interpretation.txt \
python ablation_tables.py
```

## Expected Outputs

The maintained v1.4 comparison flow produces:

- `results_twibot20_reddit_transfer.json` — per-account Reddit-transfer outputs
- `metrics_twibot20_reddit_transfer.json` — overall/per-stage/routing Reddit-transfer metrics
- `results_twibot20_native.json` — per-account TwiBot-native outputs
- `metrics_twibot20_native.json` — overall/per-stage/routing TwiBot-native metrics
- `metrics_twibot20_reddit_vs_native.json` — machine-readable Reddit-vs-native comparison artifact
- `tables/table5_cross_dataset.tex` — paper-ready cross-dataset comparison table
- `tables/table5_transfer_interpretation.txt` — concise interpretation text for the comparison result

Historical Phase 12 artifacts such as `metrics_twibot20_comparison.json` and
`transfer_evidence_summary.json` remain archived for provenance, but they are no
longer the maintained default comparison contract.

## Known Caveats

- Windows pytest temp-directory cleanup remains permission-sensitive in this environment. Production code is unaffected; the friction is in the test harness cleanup path.
- The Reddit-trained transfer result is expected to remain weak on TwiBot-20. That weak transfer result is the baseline contrast that motivates the TwiBot-native model.
- The Stage 2b AMR path is still the embedding-based proxy from v1.0, not true AMR graph parsing.
- Multi-seed stability and alternate calibration approaches remain deferred.

## Known Limitations

- No realtime serving or dashboard UI
- No online novelty recalibration in the maintained Reddit transfer path
- No true AMR graph parsing yet
- No confidence-interval / multi-seed paper analysis yet

See `VERSION.md` for the current release contract.
