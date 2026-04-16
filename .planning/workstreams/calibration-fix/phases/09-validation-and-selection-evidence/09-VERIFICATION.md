# Phase 9 Verification

**Phase:** 09 - Validation and Selection Evidence  
**Status:** passed  
**Last updated:** 2026-04-16

## Checks run

1. `python -m pytest tests/test_calibrate.py -q`
   - result: `10 passed`
2. `python main.py`
   - result: completed successfully using the local `trained_system.joblib` fallback because online embedder initialization was blocked in this environment
3. Reviewed [09-real-run-calibration-report.json](c:/Users/dzeni/PycharmProjects/SocialBotDetectionSystem/.planning/workstreams/calibration-fix/phases/09-validation-and-selection-evidence/09-real-run-calibration-report.json)

## What the real run proved

1. The real S2 calibration path now emits a compact reproducible artifact containing:
   - selected trial and thresholds
   - primary and secondary scores
   - tie count
   - near-best alternatives
   - routing and prediction behavior deltas
   - early-stop status
2. The selected trial was meaningfully distinguishable from alternatives even though F1 tied across all executed trials:
   - selected trial `3` had the best log loss `0.016382755820816743`
   - selected trial `3` had the best Brier score `0.0029705427709057768`
   - alternatives showed materially different routing, including much higher AMR and Stage 3 usage
3. Trial count was no longer redundant in practice:
   - `50` trials were requested
   - only `20` were executed
   - the search stopped early after a documented plateau with patience `16`
4. The final shipped policy is explicitly a **hybrid**:
   - optimize primary F1
   - break ties with log loss then Brier score
   - stop early on a stable lexicographic plateau

## Requirement coverage

- `CALFIX-05` verified
  - the selected rule distinguishes between candidate threshold sets using both smooth score and routing behavior
- `CALFIX-06` verified
  - tests plus the real-run artifact show that configured trial count is no longer blindly exhausted
- `CALFIX-07` verified
  - the phase artifacts explicitly record that the shipped fix is hybrid and explain why

## Verdict

Phase 9 achieved its goal and closes the `calibration-fix` milestone.
