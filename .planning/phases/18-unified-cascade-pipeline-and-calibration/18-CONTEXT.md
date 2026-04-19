# Phase 18: Unified Cascade Pipeline and Calibration - Context

**Gathered:** 2026-04-19
**Status:** Ready for planning

<domain>
## Phase Boundary

Phase 18 unifies the maintained cascade training and inference logic into a reusable dataset-parameterized pipeline layer and reduces threshold calibration to a single trial. Feature extraction already moved into `features/` in Phase 17; this phase reorganizes the pipeline and calibration code that still lives primarily in `botdetector_pipeline.py`, `calibrate.py`, `main.py`, and `train_twibot20.py`.

This phase does not yet introduce the final clean entry points `train_botsim.py` / `train_twibot.py` or the final evaluation entry points. Those belong to Phases 19 and 20. Phase 18 must leave behind a shared implementation that those later scripts can call directly.

Files likely created/modified in this phase:
- new shared pipeline module(s), likely under a new package or dedicated module
- `botdetector_pipeline.py` reduced to compatibility wrappers or re-exports
- `calibrate.py` simplified to the single-trial maintained contract
- `main.py` and `train_twibot20.py` updated to consume the shared pipeline surface instead of bespoke procedural wiring
- focused tests covering shared pipeline orchestration and single-trial calibration behavior

</domain>

<decisions>
## Implementation Decisions

### Shared Pipeline Direction
- **D-01:** The maintained cascade pipeline must become one reusable implementation shared by both BotSim-24 and TwiBot-20 training flows.
- **D-02:** Dataset choice must be represented explicitly in the shared pipeline layer rather than through monkeypatch-only feature overrides.
- **D-03:** Feature extraction stays in `features/`; the new pipeline layer should compose those extractors rather than move or duplicate their logic.

### Scope Boundaries
- **D-04:** Phase 18 may keep legacy entry points (`main.py`, `train_twibot20.py`) as callers for backward compatibility, but the source of truth must move into the new shared pipeline layer.
- **D-05:** Phase 18 does not rename artifacts to the final v1.5 names yet; Phase 19 owns the fresh artifact naming and retraining flow.
- **D-06:** Phase 18 should not broaden scope into evaluation-entry-point cleanup; it should only provide the shared training/inference/calibration core those later scripts need.

### Calibration
- **D-07:** The maintained calibration contract becomes single-trial only. Any multi-restart or plateau-stop behavior is retired from the maintained path.
- **D-08:** Calibration evidence artifacts must still be written in a stable format, but they should reflect the single executed trial rather than ranked alternatives from many trials.

### Code Quality
- **D-09:** Pipeline code should be organized as classes with methods, not a single procedural script.
- **D-10:** New comments should be sparse, lowercase, and explain why.

### Inferred from Phase 17
- **D-11:** The maintained Stage 2b path is AMR-only; no plan in this phase may reintroduce Stage 2b variant switching.
- **D-12:** Legacy feature modules remain temporary compatibility shims and should not regain ownership of logic.

</decisions>

<canonical_refs>
## Canonical References

**Downstream planning and implementation must read these first.**

### Current maintained pipeline
- `botdetector_pipeline.py` - current training and inference logic, still procedural and still the main source of pipeline behavior
- `calibrate.py` - current Optuna-based threshold calibration with multi-trial search, tie-breaking, and plateau stopping

### Current training callers
- `main.py` - BotSim-24 maintained training/evaluation script, still directly orchestrates training/calibration/inference
- `train_twibot20.py` - TwiBot training flow, still relies on `native_feature_overrides()` monkeypatching shared pipeline globals

### Current shared extraction foundation
- `features/stage1.py`
- `features/stage2.py`
- `features/stage3.py`
- `data_io.py`

### Prior phase evidence
- `.planning/phases/17-shared-feature-extraction-module/17-CONTEXT.md`
- `.planning/phases/17-shared-feature-extraction-module/17-VERIFICATION.md`

### Requirements
- `.planning/REQUIREMENTS.md` - CORE-03, CORE-04, QUAL-01, QUAL-02

</canonical_refs>

<code_context>
## Existing Code Insights

### What is already unified
- Feature extraction is already dataset-parameterized via `Stage1Extractor`, `Stage2Extractor`, and `Stage3Extractor`.
- Data loading is already partially unified via `data_io.load_dataset()`.
- The maintained pipeline is already AMR-only after Phase 17.

### What is still duplicated or procedural
- `botdetector_pipeline.py` still mixes helpers, model classes, training orchestration, and prediction orchestration in one file.
- `main.py` still performs BotSim orchestration directly instead of calling a dataset-aware pipeline object.
- `train_twibot20.py` still uses `native_feature_overrides()` to monkeypatch module-level extractor functions.
- `calibrate.py` still defaults to many Optuna trials and includes early-stop/tie-analysis logic that conflicts with the v1.5 single-trial requirement.

### Likely pressure points
- `extract_stage1_matrix` / `extract_stage2_features` compatibility globals in `botdetector_pipeline.py`
- `FeatureConfig(stage1_numeric_cols=...)` as the remaining dataset-specific hint passed through the old API
- calibration tests that currently assert multi-trial and plateau behavior
- TwiBot training tests that currently expect `calibrate_trials` to flow through as an arbitrary integer

</code_context>

<specifics>
## Specific Ideas

- Introduce an explicit dataset-aware pipeline class such as `CascadePipeline` or `CascadeTrainer` that owns:
  - extractor construction
  - stage-model fitting
  - OOF stacking
  - AMR refinement
  - prediction/inference
- Keep the stage-model classes (`Stage1MetadataModel`, `Stage2BaseContentModel`, `AMRDeltaRefiner`, `Stage3StructuralModel`) but move orchestration around them into the new class surface.
- Convert `calibrate_thresholds()` into a thin maintained wrapper over a single-trial calibrator contract, while preserving enough output structure for downstream artifact writers and tests.
- Update `main.py` and `train_twibot20.py` to consume the shared pipeline class rather than performing bespoke orchestration or monkeypatching.

</specifics>

<deferred>
## Deferred Ideas

- Final artifact renaming to `trained_system_botsim.joblib` / `trained_system_twibot.joblib`
- Final clean training script names (`train_botsim.py`, `train_twibot.py`)
- Final evaluation entry point unification and paper-output refresh

</deferred>

---

*Phase: 18-unified-cascade-pipeline-and-calibration*
*Context gathered: 2026-04-19*
