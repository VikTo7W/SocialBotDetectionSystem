# Phase 8 Verification

**Phase:** 08 - LSTM Stage 2b Foundation  
**Status:** passed  
**Last updated:** 2026-04-16

## Checks run

1. `python -m pytest tests/test_features_stage2.py -q`
   - result: `15 passed`
2. `python -m pytest tests/test_calibrate.py -q`
   - result: `12 passed`

## What execution proved

1. The project now has a deterministic embedded-message sequence contract for an LSTM Stage 2b path.
2. Zero-message and short-history accounts are handled explicitly:
   - zero-message accounts return all-zero padded sequences with length `0`
   - short histories remain shape-stable via trailing zero padding
   - recent-message truncation preserves order within the retained window
3. A trainable `Stage2LSTMRefiner` prototype can produce refined `z2`-compatible outputs under fixture-backed train/infer conditions.
4. The AMR delta-refiner baseline remains intact and semantically unchanged.

## Requirement coverage

- `LSTM-01` verified
  - the workstream now has a trainable LSTM Stage 2b prototype under seeded fixture conditions
- `LSTM-02` verified
  - the prototype preserves the `z2`-style refinement contract through `delta()` and `refine()`
- `LSTM-03` verified
  - deterministic preprocessing, truncation, padding, and zero-history handling are covered by tests

## Verdict

Phase 8 achieved its goal and is complete.
