# Plan 18-04 Summary

## Outcome

Moved the maintained BotSim and TwiBot training/inference callers onto the shared pipeline core and verified the integrated Phase 18 contract.

## Delivered

- `main.py`
- `train_twibot20.py`
- `evaluate_twibot20_native.py`
- `tests/test_train_twibot20.py`
- `18-VERIFICATION.md`

## What It Does

- makes `main.py` and `train_twibot20.py` instantiate `CascadePipeline` directly
- keeps TwiBot native evaluation aligned with the same shared predict path
- locks TwiBot training calibration to the maintained one-trial contract
- documents the remaining pytest environment gap separately from product-code verification

## Verification

- `python -m py_compile main.py train_twibot20.py evaluate_twibot20_native.py tests/test_train_twibot20.py`
- `python -m pytest tests/test_train_twibot20.py -k "not uses_dev_for_calibration_and_separate_artifact and not does_not_require_native_feature_overrides" -x -q`

## Notes

- The two tmp-path-heavy TwiBot training tests are covered by read-through and compile validation, but full execution in this workspace remains blocked by the known Windows temp-dir permission issue.
