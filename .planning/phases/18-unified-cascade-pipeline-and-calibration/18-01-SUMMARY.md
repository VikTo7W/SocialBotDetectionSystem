# Plan 18-01 Summary

## Outcome

Updated the refactor safety net so Phase 18 is pinned to the shared pipeline surface and the maintained single-trial calibration contract.

## Delivered

- `tests/conftest.py`
- `tests/test_calibrate.py`
- `tests/test_evaluate.py`
- `tests/test_train_twibot20.py`

## What It Does

- removes test expectations tied to the retired multi-trial calibration loop
- pins `CascadePipeline` as the maintained dataset-aware orchestration surface
- verifies TwiBot training uses the shared pipeline directly instead of relying on `native_feature_overrides()`
- keeps compatibility coverage explicit where thin legacy wrappers still exist

## Verification

- `python -m py_compile tests/conftest.py tests/test_calibrate.py tests/test_evaluate.py tests/test_train_twibot20.py`
- `python -m pytest tests/test_calibrate.py tests/test_evaluate.py -x -q`

## Notes

- The tmp-path-based TwiBot training tests remain subject to the existing Windows permission issue, so they were verified separately from the non-temp targeted set.
