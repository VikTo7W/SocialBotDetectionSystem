# Plan 17-05 Summary

## Outcome

Removed the LSTM Stage 2b path from the maintained pipeline and simplified the pipeline contract to the AMR-only delta-logit path.

## Delivered

- `botdetector_pipeline.py`
- `main.py`
- `tests/test_lstm_removed.py`
- `tests/test_calibrate.py`
- `tests/test_train_twibot20.py`

## What It Does

- deletes `_Stage2LSTMNet`, `Stage2LSTMRefiner`, sequence helpers, and variant-switching helpers from `botdetector_pipeline.py`
- removes `stage2b_lstm` and `stage2b_variant` from `TrainedSystem`
- inlines AMR-only refinement in both `train_system()` and `predict_system()`
- updates `main.py` from dual-variant comparison training to a single AMR-only maintained path
- removes the last test stub that fabricated `stage2b_variant`

## Verification

- `python -m py_compile botdetector_pipeline.py main.py tests/test_calibrate.py tests/test_lstm_removed.py tests/test_train_twibot20.py`
- `python -c "import botdetector_pipeline as bp; import dataclasses; print(sorted(f.name for f in dataclasses.fields(bp.TrainedSystem)))"`

## Notes

- Historical comparison and artifact naming from earlier phases remain in archival files and paper-output helpers, but they are no longer part of the maintained Stage 2b execution path.
