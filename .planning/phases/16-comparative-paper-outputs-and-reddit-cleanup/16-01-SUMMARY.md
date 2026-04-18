# Plan 16-01 Summary

## Outcome

Refreshed the maintained paper-facing comparison path in `ablation_tables.py` for the v1.4 Reddit-transfer-vs-TwiBot-native story.

## Delivered

- `ablation_tables.py`
- `tests/test_ablation_tables.py`

## What It Does

- introduces a stable Phase 16 comparison contract for Reddit-transfer vs TwiBot-native metrics
- rewires Table 5 generation to compare:
  - `BotSim-24 (Reddit, in-dist.)`
  - `TwiBot-20 (Reddit transfer)`
  - `TwiBot-20 (TwiBot-native)`
- auto-builds `metrics_twibot20_reddit_vs_native.json` from repo-local Phase 15 and Phase 16 artifacts when needed
- updates interpretation text so it explains the Reddit-transfer vs TwiBot-native delta instead of the retired static-vs-recalibrated story

## Verification

- `python -m py_compile ablation_tables.py tests/test_ablation_tables.py`
- workspace-local smoke checks covering:
  - stable comparison artifact schema generation
  - Reddit-transfer vs native delta values
  - Table 5 column labels and metric extraction
- targeted pytest logic updated, but full pytest execution in this environment is blocked by Windows temp-dir permission failures during tmp-path setup/cleanup

## Notes

- Historical Phase 12 static-vs-recalibrated evidence remains archived, but it is no longer the maintained v1.4 paper-output contract.
