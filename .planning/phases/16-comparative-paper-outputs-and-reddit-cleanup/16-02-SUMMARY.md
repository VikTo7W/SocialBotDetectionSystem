# Plan 16-02 Summary

## Outcome

Retired online novelty recalibration from the maintained Reddit-transfer contract in `evaluate_twibot20.py`.

## Delivered

- `evaluate_twibot20.py`
- `tests/test_evaluate_twibot20.py`

## What It Does

- changes the maintained Reddit transfer path to the static zero-shot baseline only
- locks the active output contract to:
  - `results_twibot20_reddit_transfer.json`
  - `metrics_twibot20_reddit_transfer.json`
- routes the maintained Reddit-transfer artifacts into the Phase 16 artifact directory by default
- keeps historical helper functions available for archived Phase 12 evidence without presenting recalibration as an active v1.4 system feature

## Verification

- `python -m py_compile evaluate_twibot20.py tests/test_evaluate_twibot20.py`
- workspace-local smoke checks covering:
  - stable expected output filenames
  - Phase 16 artifact routing
  - baseline evaluation contract after recalibration retirement
- targeted pytest logic updated, but full pytest execution in this environment is blocked by Windows temp-dir permission failures during tmp-path setup/cleanup

## Notes

- The separate TwiBot-native evaluation entry point in `evaluate_twibot20_native.py` is unchanged.
