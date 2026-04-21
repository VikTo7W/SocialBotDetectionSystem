---
phase: 19
plan: "01"
subsystem: test-safety-net
tags: [testing, training-entry-points, red-tests]
key-files:
  created:
    - tests/test_train_botsim.py
    - tests/test_train_twibot.py
  modified:
    - tests/test_train_twibot20.py
    - tests/test_evaluate_twibot20_native.py
metrics:
  tasks_completed: 3
  tasks_total: 3
---

# Plan 19-01 Summary

## Outcome

Created the RED contract test safety net for the maintained v1.5 training entry points before implementation.

## Delivered

- `tests/test_train_botsim.py` — contract tests pinning `train_botsim.py` as the maintained BotSim training surface with `DEFAULT_BOTSIM_MODEL_PATH == "trained_system_botsim.joblib"`, artifact isolation from twibot, and SEED=42
- `tests/test_train_twibot.py` — contract tests pinning `train_twibot.py` as the maintained TwiBot training surface with `DEFAULT_TWIBOT_MODEL_PATH == "trained_system_twibot.joblib"`, cross-artifact isolation, and SEED=42
- `tests/test_train_twibot20.py` — marked as compatibility shim with docstring pointing to maintained contracts
- `tests/test_evaluate_twibot20_native.py` — updated to match the renamed maintained artifact

## Commits

| Task | Commit | Description |
|------|--------|-------------|
| 1 | eb30cb0 | feat(19-01/02/03): training entry points and test safety net |

## Deviations

None — test safety net established as planned.

## Self-Check: PASSED

- [x] tests/test_train_botsim.py created with contract tests
- [x] tests/test_train_twibot.py created with contract tests
- [x] Tests correctly fail RED until implementation is present
- [x] No modifications to STATE.md or ROADMAP.md
