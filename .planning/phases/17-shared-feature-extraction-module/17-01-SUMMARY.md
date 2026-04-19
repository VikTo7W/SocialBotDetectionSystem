# Plan 17-01 Summary

## Outcome

Created the Wave 0 test scaffolding for the shared `features/` refactor and removed LSTM-oriented test fixtures from the maintained shared test surface.

## Delivered

- `tests/conftest.py`
- `tests/test_features_stage1.py`
- `tests/test_data_io.py`
- `tests/test_lstm_removed.py`
- `tests/test_features_stage2.py`
- `tests/test_features_stage1_twitter.py`
- `tests/test_features_stage2_twitter.py`
- `tests/test_features_stage3_twitter.py`
- `tests/test_calibrate.py`

## What It Does

- removes the `minimal_lstm_stage2b_inputs` fixture and all shared-test imports of LSTM-only pipeline symbols
- adds new tests that pin:
  - shared Stage 1 extractor contract
  - shared `load_dataset()` dispatch contract
  - absence of LSTM Stage 2b symbols and dataclass fields
- retargets twitter extractor tests to `features.stage1`, `features.stage2`, and `features.stage3`
- excises LSTM-specific tests from Stage 2 and calibration coverage

## Verification

- `python -c "import sys; sys.path.insert(0, '.'); import tests.conftest"`
- `python -m py_compile tests/conftest.py tests/test_features_stage1.py tests/test_data_io.py tests/test_lstm_removed.py tests/test_features_stage2.py tests/test_features_stage1_twitter.py tests/test_features_stage2_twitter.py tests/test_features_stage3_twitter.py tests/test_calibrate.py`

## Notes

- The intended Wave 0 red state existed only briefly during implementation; by the end of Phase 17 the shared `features.*` package is present and those imports now resolve normally.
