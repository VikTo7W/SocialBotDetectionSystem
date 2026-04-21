# Phase 21 Verification

Date: 2026-04-19
Phase: 21 - Documentation
Status: Passed

## Documentation Checks

- `README.md`
  - read back completed
  - result: passed
- `VERSION.md`
  - read back completed
  - result: passed

## Stale Reference Search

- `rg -n "trained_system_v12\.joblib|trained_system_twibot20\.joblib|evaluate_twibot20\.py|evaluate_twibot20_native\.py" README.md VERSION.md`
  - result: passed with historical-reference-only matches
  - interpretation: the old names now appear only inside clearly labeled historical sections, not in maintained commands or reproduction guidance

## Runtime/File Reality Checks

- `Get-ChildItem paper_outputs | Select-Object -ExpandProperty Name`
  - result:
    - `confusion_matrix_botsim.png`
    - `confusion_matrix_reddit_transfer.png`
    - `metrics_botsim.json`
    - `metrics_reddit_transfer.json`
- `Get-ChildItem tables | Select-Object -ExpandProperty Name`
  - result includes:
    - `table5_cross_dataset.tex`

## Per-Requirement Evidence

| Requirement | Status | Evidence |
|-------------|--------|----------|
| DOC-01 | passed | `README.md` now documents the maintained architecture plus rationale for LightGBM, Mahalanobis novelty, AMR delta-logit, logistic-regression stackers, and Bayesian calibration |
| DOC-02 | passed | `README.md` now includes BotSim-24 and TwiBot-20 feature-stage mapping across Stage 1, Stage 2a, Stage 2b, and Stage 3 |
| DOC-03 | passed | `README.md` now includes maintained data requirements, training commands, evaluation commands, expected outputs, and current TwiBot-native caveat; `VERSION.md` aligns the release contract with those commands |

## Notes

- The workspace still lacks a fresh local `trained_system_twibot.joblib`, so the docs intentionally describe `eval_twibot_native.py` and `generate_table5.py` as maintained paths that may remain locally blocked until the deferred retraining rerun succeeds
- Historical names remain documented only to prevent confusion when reading older milestone artifacts
