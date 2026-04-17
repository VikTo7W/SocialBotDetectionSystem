# Plan 09-01 Summary

**Status:** Complete  
**Executed:** 2026-04-16

## What changed

- Added `build_calibration_report_summary()` in `calibrate.py` to condense `system.calibration_report_` into a compact winner-vs-alternatives structure.
- Added `write_calibration_report_artifact()` in `calibrate.py` so a real calibration run can emit a reproducible JSON artifact.
- Updated `main.py` so the real S2 calibration path writes Phase 9 evidence to `09-real-run-calibration-report.json`.
- Added regression coverage in `tests/test_calibrate.py` for the compact evidence contract.

## Real-run evidence

- `python main.py` completed using the local `trained_system.joblib` fallback because this environment could not initialize the online sentence-transformer.
- The emitted artifact is [09-real-run-calibration-report.json](c:/Users/dzeni/PycharmProjects/SocialBotDetectionSystem/.planning/workstreams/calibration-fix/phases/09-validation-and-selection-evidence/09-real-run-calibration-report.json).
- Real S2 calibration requested `50` trials, executed `20`, and stopped early with plateau patience `16`.
- All `20` executed trials tied on primary `F1=0.9966555183946488`.
- Those tied trials shared the same hard predictions but not the same routing behavior.
- Selected trial `3` had the best secondary log loss `0.016382755820816743` and Brier `0.0029705427709057768`.
- Near-best alternatives had the same F1 and positive prediction count, but materially different routing:
  - trial `7`: AMR usage `0.9151`, Stage 3 usage `0.1468`
  - trial `4`: AMR usage `0.6376`, Stage 3 usage `0.1307`
  - selected trial `3`: AMR usage `0.4450`, Stage 3 usage `0.0573`

## Why this matters

Phase 9 required real-path evidence that calibration can differentiate meaningful candidates. The artifact shows that headline F1 remains quantized, but routing behavior and smooth probability quality are not flat. That validates the hybrid Phase 8 design: keep F1 as the headline objective, choose among ties with smooth metrics, and stop once no lexicographic improvement appears.
