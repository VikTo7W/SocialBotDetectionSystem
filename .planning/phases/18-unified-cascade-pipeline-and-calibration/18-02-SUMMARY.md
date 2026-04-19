# Plan 18-02 Summary

## Outcome

Added a shared class-based cascade orchestration layer and reduced `botdetector_pipeline.py` to maintained stage-model and compatibility-wrapper responsibilities.

## Delivered

- `cascade_pipeline.py`
- `botdetector_pipeline.py`
- `tests/conftest.py`
- `tests/test_evaluate.py`

## What It Does

- introduces `CascadePipeline(dataset)` as the maintained fit/predict source of truth
- makes dataset choice explicit through `infer_dataset(...)` and pipeline state
- routes shared Stage 1, Stage 2, and Stage 3 extraction through `features/`
- keeps `train_system()` and `predict_system()` as thin wrappers so existing callers remain stable during migration

## Verification

- `python -m py_compile cascade_pipeline.py botdetector_pipeline.py tests/conftest.py tests/test_evaluate.py`
- `python -m pytest tests/test_evaluate.py -x -q`

## Notes

- This plan intentionally preserved compatibility wrappers so Phase 19 can clean entry points without breaking the maintained runtime surface mid-refactor.
