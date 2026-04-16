# Plan 09-01 Summary

**Status:** Complete  
**Executed:** 2026-04-16

## What changed

- Added explicit Stage 2b variant selection in [botdetector_pipeline.py](c:/Users/dzeni/PycharmProjects/SocialBotDetectionSystem/botdetector_pipeline.py) via `normalize_stage2b_variant()` and `apply_stage2b_refiner()`.
- Extended `TrainedSystem` with a persisted `stage2b_variant` field so trained systems record whether they were built with the `amr` or `lstm` Stage 2b branch.
- Updated `train_system()` to validate the requested Stage 2b variant up front and train the selected branch while leaving the rest of the cascade shared.
- Preserved the AMR path as a first-class baseline while allowing LSTM-only systems to be built intentionally.

## Execution notes

- Phase 9 keeps the existing Stage 2b routing mask and only changes which refiner is applied after routing.
- Unsupported Stage 2b variant names now fail fast before expensive training starts.

## Verification

- `python -m pytest tests/test_calibrate.py -q`
  - result: `16 passed`
