# SocialBotDetectionSystem

## Overview

A three-stage cascade classifier (metadata → content/temporal → graph structure) for detecting social media bots, trained on the BotSim-24 Reddit dataset. The system routes accounts through escalating detection stages using novelty-aware gating, with AMR semantic refinement at Stage 2b and logistic-regression meta-learners stacking the stage outputs. v1.3 ships the zero-shot transfer path to TwiBot-20: the BotSim-24-trained cascade evaluates TwiBot-20 test accounts without retraining, using a behaviorally grounded Twitter-to-Reddit feature adapter and optional sliding-window online threshold recalibration. See `VERSION.md` for the v1.3 release contract.

## Environment Assumptions

- **Python**: CPython 3.13.
- **Dependencies**: `scikit-learn`, `lightgbm`, `sentence-transformers`, `torch` (tensor loading only), `joblib`, `numpy`, `pandas`. Dependencies are installed manually — no pinned requirements file currently ships with this repository.
- **Deterministic seed**: `SEED=42` across all experiments.
- **Operating system**: The release was packaged on Windows 10. The production code path contains no `tempfile`/`gettempdir` usage (pytest-level friction only — see Known Caveats).

## Required Inputs (User-Supplied)

The following files are gitignored and must be provided locally before running:

- `test.json` — TwiBot-20 test split. Obtain from the TwiBot-20 dataset release and place at the repo root.
- `trained_system_v12.joblib` — v1.2 trained cascade. Produced by the v1.2 training pipeline (Phase 5 of this repo). Place at the repo root.

The following files are also gitignored but are **NOT** required for the v1.3 system-version reproduction (v1.3 is zero-shot inference only):

- `train.json` — TwiBot-20 training split.
- `dev.json` — TwiBot-20 development split.
- `trained_system_v11.joblib` — v1.1 model, retained for ablation comparison only.

## Reproduction Guide

Follow these steps to reproduce the live Phase 12 TwiBot system-version artifacts end to end.

**Step 1 — Confirm required inputs are present at the repo root:**

```bash
ls test.json trained_system_v12.joblib
```

Both files must exist before proceeding.

**Step 2 — Run the canonical TwiBot evaluation:**

```bash
python evaluate_twibot20.py test.json trained_system_v12.joblib \
  .planning/workstreams/milestone/phases/12-fresh-transfer-evidence-and-paper-outputs/artifacts
```

This writes four files to `.planning/workstreams/milestone/phases/12-fresh-transfer-evidence-and-paper-outputs/artifacts/`:

- `results_twibot20.json`
- `metrics_twibot20.json`
- `metrics_twibot20_comparison.json`
- `transfer_evidence_summary.json`

**Step 3 — Regenerate Table 5 and the transfer interpretation text:**

```bash
python ablation_tables.py
```

This writes two files to `tables/`:

- `tables/table5_cross_dataset.tex`
- `tables/table5_transfer_interpretation.txt`

**Step 4 (Optional) — Redirect Table 5 reads/writes via environment variables:**

```bash
TWIBOT_COMPARISON_PATH=/alt/path/metrics_twibot20_comparison.json \
TABLE5_OUTPUT_PATH=/alt/path/table5.tex \
TABLE5_INTERPRETATION_PATH=/alt/path/table5_interpretation.txt \
python ablation_tables.py
```

## Expected Outputs

The canonical run produces the following files:

- `results_twibot20.json` — per-account cascade outputs for all TwiBot-20 test accounts.
- `metrics_twibot20.json` — overall/per-stage/routing metrics for the recalibrated run.
- `metrics_twibot20_comparison.json` — static vs recalibrated comparison plus deltas (consumed by Table 5).
- `transfer_evidence_summary.json` — compact evidence summary with interpretation verdict.
- `tables/table5_cross_dataset.tex` — paper-ready cross-dataset LaTeX table.
- `tables/table5_transfer_interpretation.txt` — human-readable transfer-result interpretation.

Release-time verdict (live Phase 12 run):

> static F1=0.0 / AUC=0.5964 · recalibrated F1=0.0 / AUC=0.5879 · verdict: `no_material_change`

Recalibration shifts Stage 3 routing on TwiBot accounts but does not improve final F1 at the fixed 0.5 decision threshold. BotSim-24 in-domain performance: F1=0.9767, AUC=0.9992.

## Known Caveats

- **Windows pytest tmp_path cleanup**: `pytest` emits permission warnings on Windows when clearing `.pytest_cache` and `tmp_path` directories. The production code paths themselves use zero `tempfile`/`gettempdir` calls (confirmed in Phase 11) — this does not affect the canonical evaluation command above. Only the test suite is affected.
- **TwiBot zero-shot weakness**: at release time the TwiBot transfer produces static F1=0.0 (AUC=0.5964) and recalibrated F1=0.0 (AUC=0.5879). Recalibration shifts Stage 3 routing but does NOT improve final F1. Verdict: `no_material_change`. This is the documented transfer regime for v1.3.
- **Stage 2b AMR stub**: the v1.3 system version still uses the embedding-based AMR proxy from v1.0, not true AMR graph parsing. The Stage 2b delta-logit adjustment is active but is grounded in sentence-transformer embeddings, not semantic role labels.
- **Weak-label calibration artifact**: because TwiBot zero-shot predictions are near the decision threshold, precision and recall collapse to 0.0 on the fixed 0.5 threshold. This is a transfer-regime artifact — the pipeline is not broken.

## Environment Assumptions (Addendum)

- The release was exercised on Windows 10 with Python 3.13. Linux/macOS have not been re-verified for this specific v1.3 release cut.
- The gitignored input files (`test.json`, `trained_system_v12.joblib`) must be present at the repo root for the canonical command to succeed.
- `ablation_tables.py` expects additional BotSim-24 assets (`Users.csv`, `user_post_comment.json`, `edge_index.pt`, `edge_type.pt`, `edge_weight.pt`) at the repo root for the full table set. Table 5 itself only requires the Phase 12 comparison artifact (`metrics_twibot20_comparison.json`).

## Known Limitations (Out of Scope for v1.3)

- No TwiBot-20 retraining or supervised adaptation in this release (zero-shot transfer only).
- No new social platform integrations beyond TwiBot-20.
- No frontend or dashboard work.
- No full Twitter-native Stage 2 or Stage 3 redesign (deferred).
- No multi-seed confidence intervals on cross-domain metrics (deferred).
- No true AMR graph parsing replacing the current embedding stub (deferred).

See `VERSION.md` for the exact artifact contract of this release.
