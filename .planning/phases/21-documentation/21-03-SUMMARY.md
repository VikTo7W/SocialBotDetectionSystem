---
phase: 21
plan: "03"
subsystem: reproduction-and-release-docs
tags: [documentation, versioning, reproduction]
key-files:
  modified:
    - README.md
    - VERSION.md
  created:
    - .planning/phases/21-documentation/21-VERIFICATION.md
metrics:
  tasks_completed: 5
  tasks_total: 5
---

# Plan 21-03 Summary

## Outcome

Aligned the reproduction guide and release contract with the maintained v1.5 scripts, artifacts, outputs, and current workspace caveats.

## Delivered

- reproduction commands updated to:
  - `train_botsim.py`
  - `train_twibot.py`
  - `eval_botsim_native.py`
  - `eval_reddit_twibot_transfer.py`
  - `eval_twibot_native.py`
  - `generate_table5.py`
- artifact names updated to:
  - `trained_system_botsim.joblib`
  - `trained_system_twibot.joblib`
- output paths updated to `paper_outputs/` and `tables/`
- `VERSION.md` rewritten for the v1.5 unified modular release
- deferred TwiBot-native runtime caveat documented honestly

## Self-Check: PASSED

- [x] reproduction docs now point to maintained scripts
- [x] old artifact names are no longer used for current instructions
- [x] output paths point to maintained directories
- [x] current local TwiBot artifact blocker is documented as a workspace/runtime gap
