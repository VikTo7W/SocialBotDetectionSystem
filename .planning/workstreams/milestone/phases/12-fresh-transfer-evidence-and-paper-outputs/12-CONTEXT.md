# Phase 12 Context - Fresh Transfer Evidence and Paper Outputs

## Goal

Generate fresh TwiBot transfer evidence from the current revised adapter and use those live artifacts to regenerate the cross-dataset paper outputs.

## Why This Phase Exists

Phase 11 hardened the TwiBot evaluation path, but it intentionally did not regenerate evidence. The repo still contains stale root-level TwiBot artifacts from older runs, and the milestone close explicitly deferred a fresh static-vs-recalibrated comparison run. Phase 12 converts the now-reproducible evaluation path into current evidence.

## Inputs Now Available

- `evaluate_twibot20.py` writes:
  - `results_twibot20.json`
  - `metrics_twibot20.json`
  - `metrics_twibot20_comparison.json`
  into a developer-specified output directory
- `ablation_tables.py` can read the comparison artifact via `TWIBOT_COMPARISON_PATH`
- Phase 11 already documented the canonical TwiBot evaluation command and artifact schema

## Live Constraints

- The environment still has Windows temp/cache permission friction during pytest teardown
- The milestone remains zero-shot only:
  - no TwiBot retraining
  - no new feature-shape changes
  - no model redesign
- Fresh evidence must be generated from the current revised adapter with:
  - static thresholds
  - online recalibration

## What Phase 12 Must Answer

1. Can the current TwiBot evaluation command produce fresh live artifacts successfully?
2. What are the actual static vs recalibrated metrics on the current transfer system?
3. Did recalibration materially help, hurt, or have negligible effect?
4. Can Table 5 be regenerated from those fresh artifacts rather than stale placeholders?

## Expected Outputs

- A fresh output directory containing live TwiBot artifacts
- A machine-readable evidence summary that records the observed result
- Regenerated `tables/table5_cross_dataset.tex` based on the live comparison artifact
- A concise written milestone-facing interpretation of whether recalibration improved transfer

## Recommended Split

- Plan 12-01:
  generate fresh TwiBot comparison artifacts and capture the observed metrics
- Plan 12-02:
  consume the live comparison artifact in `ablation_tables.py`, regenerate the paper table, and write the evidence summary
