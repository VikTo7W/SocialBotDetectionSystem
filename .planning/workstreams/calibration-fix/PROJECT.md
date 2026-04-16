# Calibration Fix Workstream

## What This Is

A focused parallel workstream for repairing threshold calibration in the cascade pipeline. The immediate problem is that `calibrate_thresholds()` repeatedly reports the same best `F1=0.993333` across Optuna trials, making larger trial counts effectively redundant and leaving the search insensitive to most threshold changes.

This workstream aims to restore meaningful calibration behavior by either:
- stopping early once the objective is proven flat enough to make additional trials wasteful, or
- redesigning the calibration objective/search so candidate threshold sets can be distinguished reliably.

## Parent Project

See `.planning/PROJECT.md` for the full system context, shipped milestones, and global constraints.

## Current Milestone: v1.1.1 Threshold Calibration Search Fix

**Goal:** Make threshold calibration informative and efficient by eliminating the current all-trials-tie behavior in `calibrate_thresholds()`.

**Target features:**
- Root-cause analysis for why Optuna trials collapse to the same objective value
- Calibration strategy update: early stopping, smoother objective, or a better search/evaluation technique
- Regression-proof validation showing calibration outcomes differ when candidate thresholds meaningfully differ
- Reproducible reporting so the selected threshold policy is auditable

## Constraints

- Keep the existing ML stack: Python, scikit-learn, LightGBM, Optuna, sentence-transformers, PyTorch tensor loading
- Preserve reproducibility with explicit seeding
- Do not weaken split discipline: S2 remains the calibration split and S3 remains the held-out evaluation split
- Avoid changes that silently invalidate previously trained artifacts without documenting the impact

## Key Questions

- Is the flat objective caused mainly by optimizing hard-thresholded F1 on already near-perfect predictions?
- Should calibration optimize a smoother metric, use tie-breakers, or explicitly stop once the plateau is detected?
- What evidence will show the new approach is genuinely better rather than merely more expensive?
