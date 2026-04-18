# 09-01 Summary

## Outcome

Implemented the Phase 9 sliding-window online threshold recalibration path in `evaluate_twibot20.py` and added the planned test coverage in `tests/test_evaluate_twibot20.py`.

## Files Modified

- `evaluate_twibot20.py`
- `tests/test_evaluate_twibot20.py`

## Delivered Behavior

- `run_inference` signature is now:
  `run_inference(path: str, model_path: str = "trained_system_v12.joblib", online_calibration: bool = True, window_size: int = 100) -> pd.DataFrame`
- When `online_calibration=False`, `run_inference` preserves the prior single-call behavior.
- When `online_calibration=True`, `run_inference` processes accounts in chunks of `window_size`, accumulates a combined flat `n1` + `n2` novelty buffer, and updates:
  - `n1_max_for_exit`
  - `n2_trigger`
  - `novelty_force_stage3`
- The update rule uses `float(np.percentile(novelty_buffer, 75))`.
- `sys_loaded.th` is restored before returning, so the caller's threshold object is not left mutated.

## Test Delta

- Added 6 Phase 9 tests covering:
  - single-call toggle-off behavior
  - cold-start preservation
  - threshold update after first full window
  - window-size cadence changes
  - threshold immutability after inference
  - concat/schema preservation across chunked inference

## Deviations

- No intended behavior deviation from the plan.
- Verification was only partial in this environment because local Windows permissions blocked full pytest/temp-dir cleanup and a direct minimal-system runtime path hit sklearn/joblib IPC permission errors.

## Verification Notes

- `python -m py_compile evaluate_twibot20.py tests/test_evaluate_twibot20.py` passed.
- Signature verification passed for the new `run_inference` parameters.
- Full pytest confirmation remains blocked by the current environment's permission issues.

## Phase 10 Note

Phase 10 should call:

- `run_inference(..., online_calibration=False)` for the baseline
- `run_inference(..., online_calibration=True, window_size=100)` for the recalibrated run
