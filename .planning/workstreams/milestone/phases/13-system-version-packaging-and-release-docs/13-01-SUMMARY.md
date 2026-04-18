---
phase: 13-system-version-packaging-and-release-docs
plan: 01
status: complete
completed: "2026-04-18"
requirements_satisfied:
  - VERS-01
---

# 13-01 Summary: Author VERSION.md

## What Was Done

Created `VERSION.md` at the project root. The file identifies the v1.3 TwiBot system version with all required sections:

- **System Version**: v1.3 — TwiBot System Version (zero-shot transfer), packaged 2026-04-18, no TwiBot retraining.
- **Model Artifact**: `trained_system_v12.joblib` named as the active artifact; `trained_system_v11.joblib` noted as ablation-only.
- **Evaluation Entry Points**: `evaluate_twibot20.py` and `ablation_tables.py` named; canonical command shown as fenced bash blocks including the concrete Phase 12 invocation.
- **Evaluation Modes**: `static` (online_calibration=False) and `recalibrated` (online_calibration=True, window_size=100) listed.
- **Expected Output Files**: All six output filenames listed with descriptions and paths.
- **Release-Time Transfer Verdict**: Live Phase 12 numbers — static F1=0.0/AUC=0.5964, recalibrated F1=0.0/AUC=0.5879, verdict=`no_material_change`.
- **Environment Overrides**: `TWIBOT_COMPARISON_PATH`, `TABLE5_OUTPUT_PATH`, `TABLE5_INTERPRETATION_PATH` all listed.
- **Cross-References**: Points to README.md for reproduction steps and caveats.

## Verification

Automated grep chain (14 checks): all passed. No forward-looking language in the file.

## Files Modified

- `VERSION.md` (created, 80+ lines)
