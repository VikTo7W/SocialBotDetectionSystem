# Plan 15-01 Summary

## Outcome

Implemented the TwiBot-native training/calibration entry point in `train_twibot20.py`.

## Delivered

- `train_twibot20.py`
- `tests/test_train_twibot20.py`

## What It Does

- loads `train.json`, `dev.json`, and `test.json` through `twibot20_io`
- adds stable `account_id` values from the raw TwiBot records
- splits `train.json` into leakage-safe S1/S2 subsets with fixed seed
- filters split-local edges
- scopes in the Phase 14 native Stage 1 and Stage 2 extractors via a safe `try/finally` override helper
- trains the cascade with `train_system()`
- calibrates thresholds on `dev.json`
- saves a separate native model artifact and native metrics/results/calibration artifacts

## Verification

- `python -m py_compile train_twibot20.py tests/test_train_twibot20.py`
- workspace-local smoke checks covering:
  - deterministic S1/S2 splitting
  - protected-model-path rejection
  - override restoration
  - calibration on `dev.json`
  - distinct native artifact routing

## Notes

- Protected Reddit-trained artifacts are explicitly rejected as output targets.
- The repo-local split naming is now enforced as `train.json` / `dev.json` / `test.json`.
