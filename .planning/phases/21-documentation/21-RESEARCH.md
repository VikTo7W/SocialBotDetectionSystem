# Phase 21 Research: Documentation

**Date:** 2026-04-19
**Phase:** 21 - Documentation
**Status:** Complete

## Goal

Turn `README.md` into the maintained v1.5 reference for the unified modular codebase, and align release-facing docs with the actual entry points, artifacts, outputs, and current caveats in the repo.

## What Changed Before This Phase

- Phase 17 unified feature extraction under `features/`
- Phase 18 unified cascade orchestration under `cascade_pipeline.py`
- Phase 19 introduced maintained training entry points:
  - `train_botsim.py`
  - `train_twibot.py`
- Phase 20 introduced maintained evaluation entry points:
  - `eval_botsim_native.py`
  - `eval_reddit_twibot_transfer.py`
  - `eval_twibot_native.py`
  - `generate_table5.py`
- Legacy duplicate evaluation entry points were removed after Phase 20 cleanup

## Current Documentation Drift

### README.md

Observed issues:

- still describes the repo as a v1.4 comparison surface instead of the maintained v1.5 modular codebase
- still references old artifact names such as `trained_system_v12.joblib` and `trained_system_twibot20.joblib`
- still routes reproduction outputs into old phase artifact directories instead of the maintained `paper_outputs/` and `tables/` outputs
- does not fully explain the maintained architecture choices:
  - LightGBM stage models
  - Mahalanobis novelty signals
  - AMR delta-logit Stage 2b path
  - logistic-regression stackers
  - Bayesian threshold calibration
- does not clearly document feature-stage mapping for both datasets

### VERSION.md

Observed issues:

- still headed as `v1.4 - Twitter-Native Supervised Baseline`
- still references old artifact naming and older output directories
- no longer matches the maintained Phase 19/20 entry points and outputs

## Maintained Code Surface To Document

### Architecture

- `cascade_pipeline.py` is the maintained orchestration layer
- `features/stage1.py`, `features/stage2.py`, `features/stage3.py` are the shared feature modules
- `data_io.py` is the shared dataset loader/dispatch surface
- `botdetector_pipeline.py` remains as compatibility wrappers rather than the primary maintained path

### Training Entry Points

- `train_botsim.py`
- `train_twibot.py`

Maintained artifact names:

- `trained_system_botsim.joblib`
- `trained_system_twibot.joblib`

### Evaluation Entry Points

- `eval_botsim_native.py`
- `eval_reddit_twibot_transfer.py`
- `eval_twibot_native.py`
- `generate_table5.py`

### Maintained Outputs

Confirmed present now:

- `paper_outputs/metrics_botsim.json`
- `paper_outputs/confusion_matrix_botsim.png`
- `paper_outputs/metrics_reddit_transfer.json`
- `paper_outputs/confusion_matrix_reddit_transfer.png`

Expected when the deferred TwiBot artifact exists:

- `paper_outputs/metrics_twibot_native.json`
- `paper_outputs/confusion_matrix_twibot_native.png`
- `tables/table5_cross_dataset.tex`

## Documentation Constraints

- README must be self-contained for a new reader
- docs must describe the maintained path only, while clearly labeling deferred or blocked pieces
- the deferred `trained_system_twibot.joblib` rerun should be documented as an environment/runtime gap, not as a code-path gap
- removed duplicate evaluation entry points must not reappear in examples or command lists

## Planning Implications

Phase 21 should split into three plans:

1. rewrite README architecture and rationale sections around the actual v1.5 modular system
2. add explicit feature-stage mapping for BotSim-24 and TwiBot-20 based on the shared extractors
3. rewrite reproduction and release docs so commands, artifact names, outputs, and caveats match the maintained codebase

## Verification Strategy

- readback verification of `README.md` and `VERSION.md`
- search for stale references to removed or superseded artifacts:
  - `trained_system_v12.joblib`
  - `trained_system_twibot20.joblib`
  - `evaluate_twibot20.py`
  - `evaluate_twibot20_native.py`
- sanity-check command lists against the maintained scripts present in repo
- verify output filenames mentioned in docs exist now or are clearly labeled as expected after deferred TwiBot retraining
