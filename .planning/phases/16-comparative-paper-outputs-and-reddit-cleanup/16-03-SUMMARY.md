# Plan 16-03 Summary

## Outcome

Updated the release-facing docs so v1.4 tells a consistent two-artifact comparison story.

## Delivered

- `README.md`
- `VERSION.md`

## What It Does

- documents the maintained Reddit-transfer evaluation command and output directory
- documents the separate TwiBot-native evaluation command and artifact directory
- documents the comparison/table generation flow for the v1.4 paper outputs
- removes online novelty recalibration from the maintained release contract and labels the older comparison story as historical

## Verification

- `python -m py_compile ablation_tables.py evaluate_twibot20.py`
- manual doc consistency check against the implemented commands, env vars, and artifact names

## Notes

- `VERSION.md` now acts as the concise release-contract source of truth for the maintained v1.4 artifact set.
