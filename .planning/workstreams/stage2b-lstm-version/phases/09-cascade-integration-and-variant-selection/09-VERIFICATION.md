# Phase 9 Verification

**Phase:** 09 - Cascade Integration and Variant Selection  
**Status:** passed  
**Last updated:** 2026-04-16

## Checks run

1. `python -m pytest tests/test_calibrate.py -q`
   - result: `16 passed`
2. `python -m pytest tests/test_evaluate.py -q`
   - result: `15 passed`

## What execution proved

1. `train_system()` can intentionally select and record the active Stage 2b variant.
2. `predict_system()` honors the configured Stage 2b branch for both AMR and LSTM paths.
3. The AMR delta-refiner remains available as the baseline path after LSTM integration.
4. Shared-pipeline semantics are preserved outside the Stage 2b branch.

## Requirement targets

- `LSTM-04` targeted
  - the cascade can run with the LSTM variant enabled without breaking the AMR baseline path
- `LSTM-05` targeted
  - the active Stage 2b variant is explicit during training and inference
- `LSTM-06` targeted
  - deterministic integration tests cover the new training/inference contract

## Verdict

Phase 9 achieved its goal and is complete.
