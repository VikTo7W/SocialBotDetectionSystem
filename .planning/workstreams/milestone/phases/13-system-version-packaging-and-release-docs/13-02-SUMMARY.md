---
phase: 13-system-version-packaging-and-release-docs
plan: 02
status: complete
completed: "2026-04-18"
requirements_satisfied:
  - VERS-02
  - VERS-03
---

# 13-02 Summary: Expand README.md

## What Was Done

Replaced the single-line `README.md` placeholder with full release-facing content in two passes:

**Task 1 (VERS-02) — Reproduction Guide:**
- `## Overview`: three-stage cascade description, points to `VERSION.md` for release contract.
- `## Environment Assumptions`: Python 3.13, dependencies list, SEED=42, Windows note.
- `## Required Inputs (User-Supplied)`: `test.json` and `trained_system_v12.joblib` as gitignored user-supplied files; clarifies what is NOT required for v1.3.
- `## Reproduction Guide`: four numbered steps with exact fenced bash code blocks — confirm inputs, run `evaluate_twibot20.py` with Phase 12 artifact dir, run `ablation_tables.py`, optional env-var overrides.
- `## Expected Outputs`: all six output filenames listed; release-time verdict quoted verbatim (`no_material_change`, F1=0.0, AUC=0.5964/0.5879).

**Task 2 (VERS-03) — Caveats and Limitations:**
- `## Known Caveats`: Windows pytest tmp_path friction, TwiBot zero-shot F1=0.0, AMR embedding stub, weak-label calibration artifact.
- `## Environment Assumptions (Addendum)`: Windows 10 / Python 3.13 note, gitignored inputs requirement, `ablation_tables.py` BotSim-24 asset list.
- `## Known Limitations (Out of Scope for v1.3)`: six bullets from REQUIREMENTS.md/PROJECT.md out-of-scope tables.
- Closing cross-reference: "See `VERSION.md` for the exact artifact contract of this release."

## Verification

Combined Task 1 + Task 2 grep chain (22 checks): all passed. No forward-looking language in the added sections.

## Files Modified

- `README.md` (rewritten, 100+ lines)
