# Plan 09-02 Summary

**Status:** Complete  
**Executed:** 2026-04-16

## What changed

- Updated `predict_system()` to honor the explicit `stage2b_variant` stored on `TrainedSystem`.
- Reused the shared `apply_stage2b_refiner()` helper so training-time and inference-time Stage 2b selection follow the same rules.
- Added deterministic integration coverage in `tests/test_calibrate.py` for:
  - invalid variant rejection
  - training-time recording of the selected `lstm` variant
  - inference using the AMR branch when configured
  - inference using the LSTM branch when configured
- Added `synthetic_training_split` in `tests/conftest.py` for end-to-end `train_system()` coverage without loading external models.

## Execution notes

- The external prediction contract stays stable: downstream code still receives the same probability and routing columns.
- The `amr_used` output column remains the Stage 2b routing indicator for compatibility with existing evaluation/reporting code.

## Verification

- `python -m pytest tests/test_calibrate.py -q`
  - result: `16 passed`
- `python -m pytest tests/test_evaluate.py -q`
  - result: `15 passed`
