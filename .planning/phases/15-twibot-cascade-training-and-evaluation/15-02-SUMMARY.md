# Plan 15-02 Summary

## Outcome

Implemented the TwiBot-native evaluation entry point in `evaluate_twibot20_native.py`.

## Delivered

- `evaluate_twibot20_native.py`
- `tests/test_evaluate_twibot20_native.py`

## What It Does

- loads the separate `trained_system_twibot20.joblib` artifact by default
- loads `test.json` through the TwiBot loader
- scopes in the Phase 14 native extractors for inference
- runs `predict_system()` and `evaluate_s3()`
- writes:
  - `results_twibot20_native.json`
  - `metrics_twibot20_native.json`

## Verification

- `python -m py_compile evaluate_twibot20_native.py tests/test_evaluate_twibot20_native.py`
- workspace-local smoke checks covering:
  - default native model path
  - override restoration after inference
  - stable native result/metric artifact writing
  - separation from the legacy zero-shot path

## Notes

- The native evaluation path is intentionally separate from `evaluate_twibot20.py`.
- Phase 16 can consume the native metrics artifact directly for comparison work.
