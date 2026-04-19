---
phase: 22
plan: 02
subsystem: pipeline
tags: [pipeline-surface, cascade-pipeline, botdetector-pipeline, consolidation, compat-shim]
dependency_graph:
  requires: [22-01-PLAN.md]
  provides: []
  affects: [cascade_pipeline.py, botdetector_pipeline.py]
tech_stack:
  added: []
  patterns: [compat-shim-re-export, single-ownership-module]
key_files:
  created: []
  modified:
    - cascade_pipeline.py
    - botdetector_pipeline.py
decisions:
  - cascade_pipeline.py owns all orchestration types and helpers; botdetector_pipeline.py is a re-export shim
  - botdetector_pipeline.py keeps train_system/predict_system as explicit forwarding wrappers for callers not yet updated
  - extract_amr_embeddings_for_accounts and simple_linguistic_features retained in botdetector_pipeline.py for callers (conftest.py etc.)
  - build_graph_features_nodeidx re-exported from features.stage3 via botdetector_pipeline.py for conftest.py compatibility
metrics:
  duration: ~10 minutes
  completed: 2026-04-19
  tasks_completed: 3
  files_created: 0
  files_modified: 2
---

# Phase 22 Plan 02: Orchestration Ownership Consolidation Summary

## One-liner

All stage models, math helpers, routing logic, and contract types moved from botdetector_pipeline into cascade_pipeline, which now owns the full maintained surface; botdetector_pipeline reduced to a re-export compatibility shim.

## What Was Built

**Task 1 - Move pipeline-level helpers into cascade_pipeline.py:**

`cascade_pipeline.py` now contains everything it needs without importing from `botdetector_pipeline`:
- Math helpers: `sigmoid`, `logit`, `entropy_from_p`
- Novelty: `MahalanobisNovelty`
- Contract types: `FeatureConfig`, `StageThresholds`, `TextEmbedder`, `TrainedSystem`
- Stage models: `Stage1MetadataModel`, `Stage2BaseContentModel`, `AMRDeltaRefiner`, `Stage3StructuralModel`
- Routing: `gate_amr`, `gate_stage3`
- Meta-model helpers: `build_meta12_table`, `oof_meta12_predictions`, `train_meta12`, `train_meta123`
- `infer_dataset`, `CascadePipeline.fit()`, `CascadePipeline.predict()`

The old `cascade_pipeline.py` imported 15 names from `botdetector_pipeline`; after this change it imports zero.

**Task 2 - Simplify botdetector_pipeline.py to a compatibility shim:**

`botdetector_pipeline.py` rewritten to:
- Re-export the full maintained surface from `cascade_pipeline` (all 15+ names listed above)
- Re-export `build_graph_features_nodeidx` from `features.stage3` for existing callers (conftest.py)
- Re-export legacy feature-extraction stubs (`extract_stage1_matrix`, `extract_stage2_features`) for existing callers
- Keep `extract_amr_embeddings_for_accounts` and `simple_linguistic_features` as local helpers used by conftest.py
- Module docstring clearly states this is a compatibility shim, not a competing pipeline implementation

**Task 3 - Forwarding behavior made obvious:**

- `train_system()` and `predict_system()` have docstrings reading "Compatibility wrapper. Delegates to CascadePipeline.fit/predict()."
- Module-level docstring at the top of `botdetector_pipeline.py` explicitly states: "Do NOT add new pipeline logic here. New code belongs in cascade_pipeline.py."
- The re-export block is visually grouped with a clear comment header separating it from the compat helpers section

## Verification

```
python -m py_compile cascade_pipeline.py botdetector_pipeline.py train_botsim.py train_twibot.py calibrate.py api.py evaluate.py
# all pass

python -m pytest tests/test_pipeline_surface.py -v
# 30 passed
```

## Deviations from Plan

None - plan executed exactly as written. The three tasks were implemented as a single atomic commit because moving helpers out of botdetector_pipeline and updating its re-exports are inseparable changes.

## Known Stubs

None. This plan does not introduce any new stubs. The existing `amr_linearize_stub` in `botdetector_pipeline.py` predates this plan and was carried forward as-is.

## Threat Flags

None. No new network endpoints, auth paths, file access patterns, or schema changes introduced.

## Self-Check: PASSED

- cascade_pipeline.py: FOUND and contains CascadePipeline, all stage models, all helpers
- botdetector_pipeline.py: FOUND and re-exports from cascade_pipeline
- Commit d3a9916: FOUND
- All 30 test_pipeline_surface.py tests: PASSED
