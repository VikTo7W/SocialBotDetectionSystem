# Plan 18-03 Summary

## Outcome

Collapsed maintained calibration to a single deterministic evaluation pass while preserving the downstream report schema.

## Delivered

- `calibrate.py`
- `tests/test_calibrate.py`

## What It Does

- removes the maintained Optuna-style multi-trial search loop and plateau handling
- evaluates the current thresholds once and stores stable report evidence
- keeps artifact-writing helpers intact so downstream reporting stays compatible
- returns a cloned `StageThresholds` object so calibration persistence behavior remains explicit in tests

## Verification

- `python -m py_compile calibrate.py tests/test_calibrate.py`
- `python -m pytest tests/test_calibrate.py -x -q`

## Notes

- The public function signature still accepts `n_trials` and `seed` for caller stability, but the maintained implementation now always executes one trial.
