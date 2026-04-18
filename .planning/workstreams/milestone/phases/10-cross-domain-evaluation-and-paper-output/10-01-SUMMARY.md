# Plan 10-01 Summary

## Outcome

Implemented the executable TwiBot Phase 10 comparison path in `evaluate_twibot20.py`.

## Changes Made

- Added `compare_twibot20_conditions()` to evaluate TwiBot-20 in both supported Phase 10 modes:
  - static thresholds via `online_calibration=False`
  - online recalibrated thresholds via `online_calibration=True`
- Extended `evaluate_twibot20()` so the single-condition helper remains usable while also accepting explicit `online_calibration` and `window_size` parameters
- Added a compact command-line comparison summary for:
  - `F1`
  - `AUC`
  - `Precision`
  - `Recall`
- Persisted the comparison artifact to `metrics_twibot20_comparison.json`
- Preserved the legacy per-run artifacts:
  - `results_twibot20.json`
  - `metrics_twibot20.json`

## Verification

- `python -m py_compile evaluate_twibot20.py tests/test_evaluate_twibot20.py`
- Direct Python smoke check confirmed:
  - both static and recalibrated conditions are evaluated
  - the comparison artifact is JSON-serializable
  - the delta block is populated
- Targeted pytest remained blocked by the local Windows temp/cache permission issue during pytest directory cleanup

## Notes

- Phase 10 "before/after" now means static thresholds vs online recalibrated thresholds on the revised TwiBot adapter
- The deprecated demographic-proxy adapter was not reintroduced
