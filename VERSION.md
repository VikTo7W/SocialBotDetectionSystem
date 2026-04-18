# VERSION.md — Social Bot Detection System

## System Version

v1.3 — TwiBot System Version (zero-shot transfer)

Packaged on 2026-04-18. This is the zero-shot transfer system version derived from the v1.2 trained cascade — no retraining on TwiBot-20 was performed. The system applies the BotSim-24-trained cascade directly to TwiBot-20 test accounts using a behaviorally-grounded transfer adapter introduced in v1.2.

## Model Artifact

Active artifact: `trained_system_v12.joblib`

This is the v1.2 clean, leakage-audited cascade produced in Phase 5 (v1.1 leakage fix and retrain) and reused unchanged for TwiBot-20 zero-shot transfer. It encapsulates the full three-stage cascade (Stage 1 LightGBM, Stage 2a sentence-transformer + LightGBM, Stage 2b AMR delta, Stage 3 LightGBM graph) plus logistic-regression meta-learners and calibrated probability outputs.

`trained_system_v11.joblib` is preserved in the repository for ablation comparison purposes but is **NOT** the released system version for v1.3.

## Evaluation Entry Points

- **Evaluation:** `evaluate_twibot20.py` — runs zero-shot inference on a TwiBot-20 test split and writes comparison artifacts.
- **Paper output:** `ablation_tables.py` — reads the comparison artifact and writes LaTeX and text outputs for the paper's cross-dataset table.

Canonical command (from `evaluate_twibot20.py` docstring):

```bash
python evaluate_twibot20.py <test_json> <model_joblib> [output_dir]
```

Concrete invocation used in Phase 12 to produce the shipped artifacts:

```bash
python evaluate_twibot20.py test.json trained_system_v12.joblib \
  .planning/workstreams/milestone/phases/12-fresh-transfer-evidence-and-paper-outputs/artifacts
python ablation_tables.py
```

## Evaluation Modes

Both modes are produced by a single invocation of the canonical command:

- `static` — `online_calibration=False`; uses the trained cascade thresholds unchanged throughout the evaluation run.
- `recalibrated` — `online_calibration=True`; applies the Phase 9 sliding-window novelty-threshold recalibration (default `window_size=100`) as accounts are processed.

## Expected Output Files

Written to `.planning/workstreams/milestone/phases/12-fresh-transfer-evidence-and-paper-outputs/artifacts/`:

- `results_twibot20.json` — per-account cascade outputs (11 keys per record: `account_id`, `p1`, `n1`, `p2`, `n2`, `amr_used`, `p12`, `stage3_used`, `p3`, `n3`, `p_final`).
- `metrics_twibot20.json` — overall/per-stage/routing metrics for the recalibrated run.
- `metrics_twibot20_comparison.json` — static vs recalibrated comparison plus scalar deltas (consumed by `ablation_tables.py` to build Table 5).
- `transfer_evidence_summary.json` — compact Phase 12 evidence summary with interpretation verdict.

Written to `tables/`:

- `table5_cross_dataset.tex` — paper-ready cross-dataset LaTeX table.
- `table5_transfer_interpretation.txt` — human-readable transfer-result interpretation.

## Release-Time Transfer Verdict

Live Phase 12 numbers (from `transfer_evidence_summary.json`):

| Condition    | F1  | AUC    | Precision | Recall |
|--------------|-----|--------|-----------|--------|
| static       | 0.0 | 0.5964 | 0.0       | 0.0    |
| recalibrated | 0.0 | 0.5879 | 0.0       | 0.0    |
| delta        | 0.0 | -0.0085| 0.0       | 0.0    |

Verdict: `no_material_change` (interpretation_basis: `f1_delta`)

Recalibration shifts Stage 3 routing thresholds on TwiBot accounts but does not improve final F1 at the fixed 0.5 decision threshold. BotSim-24 in-domain performance: F1=0.9767, AUC=0.9992.

## Environment Overrides

The v1.3 output paths honour three environment variables:

- `TWIBOT_COMPARISON_PATH` — override the comparison metrics file that Table 5 reads (default: the `metrics_twibot20_comparison.json` path in the Phase 12 artifacts directory).
- `TABLE5_OUTPUT_PATH` — override where `table5_cross_dataset.tex` is written.
- `TABLE5_INTERPRETATION_PATH` — override where `table5_transfer_interpretation.txt` is written.

## Cross-References

See `README.md` for end-to-end reproduction steps and known caveats.
