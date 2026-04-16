# Phase 8 Verification Plan

**Phase:** 08 - LSTM Stage 2b Foundation  
**Status:** Planned  
**Last updated:** 2026-04-16

## What execution must prove

1. The project has a deterministic embedded-message sequence contract for an LSTM Stage 2b path.
2. Zero-message and short-history accounts are handled explicitly and reproducibly.
3. A trainable LSTM Stage 2b prototype can produce a refined `z2`-compatible output under fixture-backed train/infer conditions.
4. The current AMR delta-refiner path remains intact as the baseline for later phases.

## Required execution checks

1. `python -m pytest tests/test_features_stage2.py -x -q`
2. `python -m pytest tests/test_calibrate.py -x -q`

## Pass conditions

- `LSTM-01`: Passes only if the LSTM Stage 2b foundation can be trained under the existing seeded split discipline in a scoped proof path.
- `LSTM-02`: Passes only if the prototype exposes a refined `z2`-compatible output contract or an explicitly documented equivalent.
- `LSTM-03`: Passes only if sequence preprocessing and empty-history handling are deterministic and covered by tests.

## Failure conditions

- Sequence shaping is implicit or unstable across runs.
- Zero-message handling is left undefined.
- The prototype cannot show a stable train/infer contract under fixture conditions.
- The new work silently breaks or repurposes the AMR baseline path during this phase.
