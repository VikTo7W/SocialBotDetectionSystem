# Phase 22: Pipeline Surface Consolidation - Research

**Researched:** 2026-04-19
**Domain:** internal pipeline-surface cleanup in an existing Python ML codebase
**Confidence:** HIGH

## Summary

Phase 22 is not a model-change phase. The repo already has a maintained orchestration surface in `cascade_pipeline.py`, but the older `botdetector_pipeline.py` still owns most of the pipeline ingredients and still exposes compatibility wrappers that look like a second maintained path. The overlap is real enough to confuse future work:

1. `cascade_pipeline.py` owns the maintained `CascadePipeline.fit()` and `CascadePipeline.predict()` flow.
2. `botdetector_pipeline.py` still owns the stage-model classes, math helpers, gating logic, meta-model training helpers, and the compatibility `train_system()` / `predict_system()` wrappers.
3. Several maintained callers still import the legacy module for types or compatibility behavior, so simply deleting one file would break the public project surface.

The right Phase 22 outcome is a single clearly named pipeline source of truth with compatibility behavior demoted to thin wrappers only. The work should stop short of the broader feature and dataset-I/O consolidation planned for Phases 23 and 24.

## Requirements Support

| Requirement | Research Support |
|-------------|------------------|
| CONS-01 | One module must clearly own orchestration, fit/predict flow, and pipeline-level helpers so there is no ambiguity between `botdetector_pipeline.py` and `cascade_pipeline.py`. |
| PRES-03 | Split discipline, AMR-only Stage 2b behavior, routing gates, and meta-table semantics must stay unchanged while ownership is consolidated. |

## Codebase Evidence

### What `cascade_pipeline.py` already owns

- `CascadePipeline` is the maintained fit/predict class consumed by `train_botsim.py`, `train_twibot.py`, and the maintained evaluation entry points.
- It already constructs dataset-aware extractors directly and owns the end-to-end training and inference sequence.
- `README.md` and `VERSION.md` already describe `CascadePipeline` as the maintained orchestration surface.

### What `botdetector_pipeline.py` still owns

- Stage model classes: `Stage1MetadataModel`, `Stage2BaseContentModel`, `AMRDeltaRefiner`, `Stage3StructuralModel`
- Pipeline math and routing helpers: `sigmoid`, `logit`, `entropy_from_p`, `gate_amr`, `gate_stage3`
- Meta helpers: `build_meta12_table`, `oof_meta12_predictions`, `train_meta12`, `train_meta123`
- Compatibility entry points: `train_system()` and `predict_system()`
- Legacy extraction wrappers such as `extract_stage1_matrix()` and `extract_stage2_features()`

### Where the overlap shows up in callers

- `train_botsim.py`, `train_twibot.py`, and maintained eval scripts import `CascadePipeline`
- `api.py`, `run_batch.py`, `calibrate.py`, `ablation_tables.py`, and many tests still import from `botdetector_pipeline.py`
- `cascade_pipeline.py` currently imports most of its implementation pieces back from `botdetector_pipeline.py`, which means orchestration ownership is conceptually split even though the maintained entry points already prefer `CascadePipeline`

## Architectural Recommendation

### Recommended shape

Keep `cascade_pipeline.py` as the one maintained pipeline/orchestration module and move the pipeline-level helpers it truly owns into that module or into one clearly subordinate internal surface. Then reduce `botdetector_pipeline.py` to one of these acceptable states:

- a thin compatibility layer that re-exports stage-model pieces and forwards to `CascadePipeline`, or
- a narrower stage-components module with a name and responsibility that no longer competes with the maintained pipeline surface

For this phase, the safest path is to preserve the filename `botdetector_pipeline.py` but demote it to compatibility-only duties so the maintained callers and docs can stay stable while future phases reduce file count further.

### Why this shape fits the roadmap

- It satisfies the user’s request to eliminate duplicate maintained functionality without forcing the broader file-merging work into the wrong phase.
- It preserves Phase 23’s room to redesign the feature surface cleanly instead of mixing pipeline cleanup with feature consolidation.
- It preserves Phase 24’s room to unify dataset I/O without reopening Phase 22 decisions.

## Recommended Plan Split

### Wave 0

- add or adjust tests so they pin `CascadePipeline` as the maintained orchestration surface and treat `botdetector_pipeline.py` as compatibility-only

### Wave 1

- consolidate orchestration ownership into `cascade_pipeline.py`
- trim or demote duplicated helpers and wrappers in `botdetector_pipeline.py`

### Wave 2

- migrate maintained callers and tests to the clarified ownership model
- verify that routing, AMR gating, and final prediction shape remain unchanged

## Risks and Pitfalls

### Risk 1: silent behavioral drift during helper moves

If helper relocation changes meta-table column order, default dtypes, or routing masks, the trained system can drift without obvious compile errors. The plan should require parity tests around `predict_system()` / `CascadePipeline.predict()` outputs and the gating helpers.

### Risk 2: collapsing too much too early

Phase 22 should not also merge all feature or dataset-I/O files. That would blur milestone boundaries and make verification much harder.

### Risk 3: leaving duplicate responsibility with new comments only

If Phase 22 merely updates docs or comments while both modules still look equally authoritative, `CONS-01` is not met. Ownership needs to become obvious from imports, wrappers, and maintained callers.

## Primary Recommendation

Plan Phase 22 around one main deliverable: `cascade_pipeline.py` becomes the unmistakable maintained pipeline source of truth, while `botdetector_pipeline.py` is demoted to compatibility or stage-components support only. Protect the current routing and AMR behavior with tests first, then move callers and wrappers with parity verification at the end.
