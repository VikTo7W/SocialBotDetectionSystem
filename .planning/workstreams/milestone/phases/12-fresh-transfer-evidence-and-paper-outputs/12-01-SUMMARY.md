# Plan 12-01 Summary

## Outcome

Added a stable Phase 12 evidence-output convention and a derivative machine-readable transfer summary for fresh TwiBot comparison runs.

## Changes Made

- Updated `evaluate_twibot20.py` to default its CLI output directory to:
  - `.planning/workstreams/milestone/phases/12-fresh-transfer-evidence-and-paper-outputs/artifacts`
- Added explicit expected-artifact reporting for:
  - `results_twibot20.json`
  - `metrics_twibot20.json`
  - `metrics_twibot20_comparison.json`
  - `transfer_evidence_summary.json`
- Added `build_transfer_evidence_summary()` to derive:
  - `static_overall`
  - `recalibrated_overall`
  - `delta_overall`
  - categorical interpretation: `improved`, `worsened`, or `no_material_change`
- Added focused Phase 12 tests in `tests/test_evaluate_twibot20.py` covering:
  - summary structure
  - materiality-band interpretation behavior
  - stable expected artifact filenames

## Verification

- `python -m py_compile evaluate_twibot20.py tests/test_evaluate_twibot20.py`
- Direct Python smoke check passed for:
  - `build_transfer_evidence_summary()`
  - `list_expected_output_files()`
- Targeted pytest passed:
  - `tests/test_evaluate_twibot20.py::test_phase12_evidence_summary_shape_and_interpretation`
  - `tests/test_evaluate_twibot20.py::test_phase12_evidence_summary_uses_materiality_band`
  - `tests/test_evaluate_twibot20.py::test_phase12_expected_output_files_are_stable`
- Real fresh run completed:
  - `python evaluate_twibot20.py test.json trained_system_v12.joblib .planning/workstreams/milestone/phases/12-fresh-transfer-evidence-and-paper-outputs/artifacts`
  - produced:
    - `results_twibot20.json`
    - `metrics_twibot20.json`
    - `metrics_twibot20_comparison.json`
    - `transfer_evidence_summary.json`

## Notes

- Observed fresh evidence result:
  - static `F1=0.0`, `AUC=0.5964`
  - recalibrated `F1=0.0`, `AUC=0.5879`
  - summary verdict: `no_material_change`
