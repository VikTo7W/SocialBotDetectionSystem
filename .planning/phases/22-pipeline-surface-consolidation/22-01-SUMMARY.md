---
phase: 22
plan: 01
subsystem: tests
tags: [pipeline-surface, safety-net, cascade-pipeline, compatibility-wrappers, routing, amr]
dependency_graph:
  requires: []
  provides: [22-02-PLAN.md, 22-03-PLAN.md]
  affects: [tests/test_pipeline_surface.py]
tech_stack:
  added: []
  patterns: [test-safety-net, behavioral-parity-assertions, monkeypatch-delegation-verification]
key_files:
  created:
    - tests/test_pipeline_surface.py
  modified: []
decisions:
  - Safety net tests are in a single file covering all 3 task groups — structural, compatibility, and parity assertions together form a coherent Wave 0 module
  - test_train_system_calls_cascade_pipeline_fit patches cascade_pipeline.CascadePipeline (module-level) because train_system() uses a local import; the sentinel-return pattern avoids real ML training in the delegation test
  - Existing tests in test_train_botsim.py/test_train_twibot.py already monkeypatch CascadePipeline directly and were sufficient as-is; no modifications needed to those files
metrics:
  duration: ~15 minutes
  completed: 2026-04-19
  tasks_completed: 3
  files_created: 1
  files_modified: 0
---

# Phase 22 Plan 01: Pipeline Surface Safety Net Summary

## One-liner

30-test safety net pinning CascadePipeline as the sole maintained orchestration surface and protecting routing masks, output columns, and AMR-only behavior before helper relocation begins.

## What Was Built

`tests/test_pipeline_surface.py` establishes the Wave 0 red-test safety net for Phase 22 pipeline-surface consolidation. It is organized into four test classes:

**TestCascadePipelineIsMaintenedSurface** (Task 1): Asserts that `CascadePipeline` is defined in `cascade_pipeline.py`, exposes `fit()` and `predict()`, accepts `"botsim"` and `"twibot"` dataset strings, rejects unknown datasets with a `ValueError`, and that both `train_botsim.py` and `train_twibot.py` import `CascadePipeline` directly rather than going through `botdetector_pipeline.train_system`.

**TestCompatibilityWrappersForwardToCascadePipeline** (Task 2): Asserts that `train_system()` and `predict_system()` remain exported from `botdetector_pipeline` for compatibility, that `train_system()` delegates to `CascadePipeline.fit()` (verified by monkeypatching `cascade_pipeline.CascadePipeline` and confirming the fit sentinel is returned), that `predict_system()` delegates to `CascadePipeline.predict()`, and that `predict_system()` output matches `CascadePipeline.predict()` output column-for-column with matching `p_final` values.

**TestPredictionOutputColumns** + **TestRoutingMaskBehavior** + **TestAMROnlyBehavior** (Task 3): Parity assertions that will catch accidental drift during helper relocation: exact output column set and order, row count and account_id order preservation, all probability columns in [0, 1], `amr_used`/`stage3_used` as integer {0,1} flags, `gate_amr`/`gate_stage3` return boolean arrays, AMR gate activates on uncertainty and suppresses on confidence, `TrainedSystem` has `amr_refiner.refine()` and `amr_refiner.delta()`, no LSTM attributes survive on `TrainedSystem` or `CascadePipeline`, and AMR refinement is additive (`z_base + delta`).

## Verification

```
python -m py_compile tests/test_train_botsim.py tests/test_train_twibot.py tests/test_evaluate.py tests/test_api.py tests/conftest.py
# all pass

python -m pytest tests/test_pipeline_surface.py -v
# 30 passed
```

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] FakePipeline.fit() had wrong signature in delegation test**
- **Found during:** Task 2 test execution
- **Issue:** The initial `FakePipeline.fit()` accepted `**kwargs` but `train_system()` calls `pipeline.fit(S1, S2, edges_S1, edges_S2, th, ...)` with positional args; also the fake body tried to build a real `TrainedSystem` using `np.ones` which caused a singular matrix in `MahalanobisNovelty`.
- **Fix:** Changed `fit(**kwargs)` to `fit(self, S1, S2, edges_S1, edges_S2, th, nodes_total=None, embedder=None)` and replaced the real-ML body with a sentinel-return pattern (`return _sentinel_system`). The test then asserts `result is _sentinel_system`.
- **Files modified:** `tests/test_pipeline_surface.py`
- **Commit:** c7d3296

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1-3  | add pipeline-surface safety net tests | c7d3296 |

## Known Stubs

None. This plan creates tests only; no implementation stubs.

## Threat Flags

None. This plan creates test-only code with no new network endpoints, auth paths, file access patterns, or schema changes.

## Self-Check: PASSED

- tests/test_pipeline_surface.py: FOUND
- Commit c7d3296: FOUND (git log --oneline -1 = c7d3296 test(22-01): add pipeline-surface safety net tests)
- All 30 tests: PASSED
