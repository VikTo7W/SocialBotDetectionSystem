---
phase: 22
plan: 03
subsystem: pipeline
tags: [pipeline-surface, caller-alignment, cascade-pipeline, botdetector-pipeline, docs-refresh]
dependency_graph:
  requires: [22-02-PLAN.md]
  provides: []
  affects:
    - train_botsim.py
    - train_twibot.py
    - api.py
    - run_batch.py
    - README.md
tech_stack:
  added: []
  patterns: [single-ownership-import, compat-shim-isolation]
key_files:
  created: []
  modified:
    - train_botsim.py
    - train_twibot.py
    - api.py
    - run_batch.py
    - README.md
decisions:
  - All maintained callers now import types/helpers directly from cascade_pipeline; botdetector_pipeline is never used as an import source in maintained code
  - api.py and run_batch.py updated to call CascadePipeline.predict() directly instead of the predict_system compat wrapper
  - eval_botsim_native.py, eval_reddit_twibot_transfer.py, eval_twibot_native.py do not exist in this worktree branch (not yet implemented); skipped with no action needed
  - README compatibility layer section reworded from "still contains" to explicit re-export shim description; VERSION.md had no dual-surface wording and required no changes
metrics:
  duration: ~10 minutes
  completed: 2026-04-19
  tasks_completed: 3
  files_created: 0
  files_modified: 5
---

# Phase 22 Plan 03: Caller Alignment and Documentation Refresh Summary

## One-liner

All maintained training, inference, and API callers updated to import directly from cascade_pipeline; README compatibility-layer section updated to describe botdetector_pipeline.py as a re-export shim only; 30+9+5 tests confirm routing and prediction contracts survived the cleanup.

## What Was Built

**Task 1 - Update maintained callers:**

- `train_botsim.py`: removed `from botdetector_pipeline import StageThresholds`; consolidated to `from cascade_pipeline import CascadePipeline, StageThresholds`
- `train_twibot.py`: removed `from botdetector_pipeline import FeatureConfig, StageThresholds`; consolidated to `from cascade_pipeline import CascadePipeline, FeatureConfig, StageThresholds`
- `api.py`: removed `from botdetector_pipeline import predict_system`; now imports `CascadePipeline, infer_dataset` from `cascade_pipeline` and calls `pipeline.predict()` directly in the route handler
- `run_batch.py`: removed `from botdetector_pipeline import predict_system, TrainedSystem`; now imports `CascadePipeline, TrainedSystem, infer_dataset` from `cascade_pipeline` and calls `pipeline.predict()` directly in `main()`

The eval entry points (`eval_botsim_native.py`, `eval_reddit_twibot_transfer.py`, `eval_twibot_native.py`) do not exist in this worktree branch (they are planned for Phase 20 implementation) and were skipped.

**Task 2 - Refresh documentation:**

- `README.md` compatibility layer section updated: old wording implied `botdetector_pipeline.py` still contains stage-model classes; new wording explicitly states it is a re-export shim with no new pipeline logic
- `VERSION.md` examined and required no changes — it already used accurate single-surface language

**Task 3 - Phase-level verification:**

```
python -m py_compile train_botsim.py train_twibot.py api.py run_batch.py cascade_pipeline.py botdetector_pipeline.py
# ALL OK

python -m pytest tests/test_pipeline_surface.py -v
# 30 passed

python -m pytest tests/test_train_botsim.py tests/test_train_twibot.py -v
# 9 passed

python -m pytest tests/test_api.py -v
# 5 passed
```

## Verification

All 44 targeted tests pass. No compile errors in any modified or maintained surface file.

## Deviations from Plan

### Auto-fixed Issues

None.

### Scope Observations

The plan listed `eval_botsim_native.py`, `eval_reddit_twibot_transfer.py`, and `eval_twibot_native.py` as files to update. None of these exist in the current worktree branch (they are planned Phase 20 files not yet present at the HEAD commit 70e222f). No action was taken for absent files — this is expected behavior per plan instructions ("if exists — caller to update").

## Commits

| Task | Description | Commit |
|------|-------------|--------|
| 1 | Align maintained callers to cascade_pipeline as sole pipeline owner | fedefda |
| 2 | Refresh README compatibility-layer description | 8c72d13 |
| 3 | Verification run (no source changes; 44 tests passing) | — |

## Known Stubs

None. No new stubs introduced.

## Threat Flags

None. No new network endpoints, auth paths, file access patterns, or schema changes introduced.

## Self-Check: PASSED

- train_botsim.py: FOUND, imports StageThresholds from cascade_pipeline
- train_twibot.py: FOUND, imports FeatureConfig, StageThresholds from cascade_pipeline
- api.py: FOUND, uses CascadePipeline.predict() directly
- run_batch.py: FOUND, uses CascadePipeline.predict() directly
- README.md: FOUND, compatibility layer section updated
- Commit fedefda: FOUND
- Commit 8c72d13: FOUND
- 30 test_pipeline_surface.py tests: PASSED
- 9 train caller tests: PASSED
- 5 api tests: PASSED
