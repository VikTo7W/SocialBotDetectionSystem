# Phase 19: Training Entry Points and Fresh Model Retraining - Research

**Researched:** 2026-04-19
**Domain:** training entry-point cleanup and fresh artifact regeneration after shared-pipeline unification
**Confidence:** HIGH

## Summary

Phase 18 finished the shared orchestration work, but the maintained training surface is still transitional. BotSim training still lives in `main.py`, TwiBot training still lives in `train_twibot20.py`, and the default artifact names still reflect the older release story (`trained_system.joblib`, `trained_system_v12.joblib`, `trained_system_twibot20.joblib`). Phase 19 should convert that transitional state into two explicit maintained training commands:

- `train_botsim.py` -> `trained_system_botsim.joblib`
- `train_twibot.py` -> `trained_system_twibot.joblib`

The main implementation risk is not model math anymore; it is command-surface clarity, artifact routing safety, and making sure the fresh training run proves the unified pipeline is genuinely production-ready rather than only test-ready.

## Requirements Support

| Requirement | Research Support |
|-------------|------------------|
| TRAIN-01 | BotSim needs a clean dedicated training entry point that no longer presents `main.py` as the maintained script and that writes only the BotSim artifact. |
| TRAIN-02 | TwiBot needs the same treatment: a clean maintained script name, explicit artifact path, and no dependence on the older `twibot20` naming in the maintained contract. |

## Codebase Evidence

### Shared core is ready

- `cascade_pipeline.py` now owns maintained fit/predict orchestration.
- `calibrate.py` now enforces the maintained single-trial contract.
- Phase 18 verification already confirmed both current training callers use the shared pipeline directly.

### Entry points are still legacy-shaped

- `main.py` is still the only BotSim training script and still writes `trained_system.joblib`, `trained_system_v11.joblib`, and `trained_system_v12.joblib`.
- `train_twibot20.py` is still the maintained TwiBot training surface and still defaults to `trained_system_twibot20.joblib`.
- There is no `train_botsim.py` or `train_twibot.py` yet.
- The test suite still centers on `tests/test_train_twibot20.py`; there is no equivalent maintained BotSim entry-point test file.

### Artifact contract is the real Phase 19 seam

The roadmap now expects fresh unified-code artifacts named:

- `trained_system_botsim.joblib`
- `trained_system_twibot.joblib`

That means Phase 19 must do more than add wrappers. It must also pin:

- safe output defaults
- non-overwrite behavior across datasets
- reproducible seed usage
- loadability of the new artifacts after fresh training

## Recommended Plan Split

### Wave 0

- add tests that pin the new entry-point names, artifact defaults, and non-overwrite guarantees before refactoring the scripts

### Wave 1

- build `train_botsim.py` as the maintained BotSim training entry point, likely by extracting reusable helpers out of `main.py`
- build `train_twibot.py` as the maintained TwiBot training entry point, keeping `train_twibot20.py` only as a compatibility shim if needed

### Wave 2

- run fresh training for both maintained artifacts
- smoke-load both joblibs and record verification/results paths
- document any remaining environment caveats separately from code issues

## Architectural Recommendation

Keep the shared training logic shallow at the script layer. The maintained scripts should mostly:

1. load and split dataset-specific inputs
2. instantiate `CascadePipeline(...)`
3. calibrate with the maintained one-trial path
4. write one canonical artifact each
5. emit reproducible metrics and artifact-path summaries

Do not re-expand training math into new helpers unless it is necessary to share dataset-loading or split utilities between the two scripts.

## Risks and Pitfalls

### Risk 1: legacy artifact overwrites survive the rename

If the new maintained scripts still default to old filenames or still write compatibility copies by default, the phase will not satisfy the roadmap intent. Compatibility outputs should be explicit and limited.

### Risk 2: BotSim refactor silently changes baseline behavior

`main.py` currently contains data loading, split logic, Stage 3 edge filtering, calibration artifact writing, and multiple legacy artifact dumps. Extracting a clean BotSim trainer must preserve the actual training/evaluation behavior while removing the historical extra outputs from the maintained path.

### Risk 3: phase tries to solve evaluation cleanup too early

Phase 19 should produce fresh train artifacts and the training entry points only. Renaming all evaluation scripts and paper outputs belongs to Phase 20.

### Risk 4: fresh retraining blocked by data availability or runtime cost

State already flags that both BotSim-24 and TwiBot-20 data must be present locally. The plan should include an explicit execution/verification wave that records whether the fresh artifacts were fully rebuilt or whether the environment blocked full retraining.

## Primary Recommendation

Plan Phase 19 around four deliverables:

1. contract tests for the new maintained training surface,
2. a clean `train_botsim.py`,
3. a clean `train_twibot.py`,
4. a final wave that generates and smoke-verifies `trained_system_botsim.joblib` and `trained_system_twibot.joblib`.

That keeps the phase tightly aligned with `TRAIN-01` and `TRAIN-02` while leaving evaluation-surface cleanup for Phase 20.
