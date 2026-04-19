# Phase 18: Unified Cascade Pipeline and Calibration - Research

**Researched:** 2026-04-19
**Domain:** pipeline unification and code-structure refactor within an existing Python ML project
**Confidence:** HIGH

## Summary

Phase 18 is a structural refactor around code that already works, not an algorithmic rewrite. The main risk is behavioral drift while moving orchestration out of `botdetector_pipeline.py` and collapsing calibration from many Optuna trials to one maintained trial. The repo already has the hardest prerequisite in place from Phase 17: dataset-parameterized feature extractors and an AMR-only Stage 2b path. What remains is to make training and inference consume those abstractions directly instead of through legacy module-level functions and monkeypatching.

The current state shows three clear seams:

1. `botdetector_pipeline.py` still contains stage-model classes plus all orchestration logic for training and prediction.
2. `calibrate.py` still implements a multi-trial Optuna search with plateau stopping, tie ranking, and alternative-trial reporting.
3. `train_twibot20.py` still relies on `native_feature_overrides()` to swap twitter feature extractors into globally imported pipeline functions.

The strongest Phase 18 outcome is a shared pipeline class that accepts a dataset identifier and composes the shared `features/` extractors internally. That lets Phase 19 build clean `train_botsim.py` and `train_twibot.py` scripts as thin wrappers rather than repeating orchestration.

## Requirements Support

| Requirement | Research Support |
|-------------|------------------|
| CORE-03 | Shared pipeline should move orchestration into one reusable dataset-aware class/module consumed by both current training paths. |
| CORE-04 | Calibration should be reduced to a single executed trial and the test suite updated away from multi-trial/plateau assumptions. |
| QUAL-01 | The refactor should create class-based orchestration rather than leave training/prediction as large procedural functions. |
| QUAL-02 | The new surface should avoid verbose block comments and keep explanation-focused lowercase comments only where needed. |

## Architectural Recommendation

### Recommended shape

Create a dedicated shared pipeline layer, for example:

```python
class CascadePipeline:
    def __init__(self, dataset: str, cfg: FeatureConfig, thresholds: StageThresholds, ...): ...
    def fit(self, S1, S2, edges_S1, edges_S2, nodes_total: int) -> TrainedSystem: ...
    def predict(self, system: TrainedSystem, df, edges_df, nodes_total: int) -> pd.DataFrame: ...
```

Supporting classes or helpers can break apart:

- dataset-aware feature access
- stage fitting
- meta-table assembly / OOF stacking
- calibration

The key is that `main.py` and `train_twibot20.py` should stop knowing how the cascade is built internally.

### Why this shape fits the repo

- It preserves the tested stage-model math while only relocating orchestration.
- It aligns with Phase 17, which already separated feature extraction from the pipeline.
- It lets later phases treat training and evaluation scripts as shallow wrappers.
- It removes the need for TwiBot monkeypatching because dataset choice becomes a first-class constructor argument.

## Calibration Findings

### Current maintained mismatch

`calibrate.py` still defaults to `n_trials=200`, computes plateau patience, ranks many trials, and stores comparison-oriented diagnostics. That conflicts with the v1.5 requirement that maintained calibration runs exactly one trial.

### Recommended Phase 18 contract

- `calibrate_thresholds()` should execute exactly one trial in the maintained path.
- The report structure can stay stable enough for downstream artifact writing, but it should record:
  - `requested_trials == 1`
  - `executed_trials == 1`
  - `stopped_early == False`
  - one completed trial with threshold values and behavior metrics
- Multi-trial tie-analysis logic should be removed from the maintained code path rather than merely bypassed by defaults.

This is important because leaving the multi-trial logic in place encourages future callers to keep using it and keeps the maintained code more complex than the roadmap intends.

## Codebase Evidence

### Shared extraction is ready

- `features/stage1.py`, `features/stage2.py`, and `features/stage3.py` already preserve dataset-specific contracts behind shared interfaces.
- `data_io.py` already provides top-level dataset dispatch.

### Pipeline still needs unification

- `botdetector_pipeline.py` still imports compatibility functions `extract_stage1_matrix` and `extract_stage2_features` rather than constructing shared extractors directly.
- `train_system()` and `predict_system()` are still top-level procedural functions instead of methods on a pipeline object.

### TwiBot path still needs to stop monkeypatching

- `train_twibot20.py` uses `native_feature_overrides()` to rewrite module globals inside `botdetector_pipeline.py`.
- That pattern is acceptable as a temporary bridge but is the clearest sign that shared pipeline orchestration is not complete.

## Recommended Plan Split

### Wave 0

- add or update tests that pin the desired shared pipeline API and the single-trial calibration contract

### Wave 1

- build the new shared pipeline class/module around existing stage-model classes
- migrate the calibration layer to the maintained single-trial contract

### Wave 2

- migrate existing BotSim and TwiBot callers onto the shared pipeline surface
- run integrated verification and clean up remaining compatibility edges

## Risks and Pitfalls

### Risk 1: accidental model-behavior drift

If the refactor changes meta-table column order, gating inputs, or which rows receive AMR refinement, metrics may shift subtly. Preserve existing helper math and add focused parity tests around `predict_system()` outputs.

### Risk 2: over-coupling Phase 18 to Phase 19

Phase 18 should provide the shared core, not spend time finalizing artifact naming, final CLI names, or full retraining orchestration. Those belong to the next phase.

### Risk 3: keeping monkeypatching alive under a different name

If TwiBot still requires swapping module globals after Phase 18, the pipeline is not truly unified. Dataset must move into constructor/config state.

### Risk 4: partial single-trial conversion

Changing only the default `n_trials` to `1` while keeping the multi-trial machinery intact would technically pass some tests but would not satisfy the intent of CORE-04. The maintained implementation should be simplified, not just defaulted.

## Primary Recommendation

Plan Phase 18 around one central deliverable: a dataset-aware shared cascade pipeline class that becomes the maintained source of truth for training and prediction. Treat single-trial calibration as a first-class simplification in that same refactor, then migrate existing BotSim and TwiBot training callers onto the shared core with compatibility retained only at the entry-point level.
