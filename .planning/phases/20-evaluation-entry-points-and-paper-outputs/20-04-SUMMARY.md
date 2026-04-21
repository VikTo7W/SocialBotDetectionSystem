---
phase: 20
plan: "04"
subsystem: twibot-native-evaluation
tags: [evaluation, twibot, paper-outputs]
key-files:
  created:
    - eval_twibot_native.py
  modified:
    - tests/test_eval_twibot_native.py
metrics:
  tasks_completed: 2
  tasks_total: 2
---

# Plan 20-04 Summary

## Outcome

Built the maintained TwiBot-native evaluation entry point and turned the Wave 0 TwiBot-native contract tests green.

## Delivered

- `eval_twibot_native.py` with `run_inference_twibot_native`, `evaluate_twibot_native`, `_write_confusion_matrix`, `_save_json`, and CLI support
- removed the superseded legacy native entry point `evaluate_twibot20_native.py` and its duplicate test file once the maintained path was green
- paper outputs are defined as:
  - `paper_outputs/metrics_twibot_native.json`
  - `paper_outputs/confusion_matrix_twibot_native.png`

## Verification

- `python -m py_compile eval_twibot_native.py`
- `python -m pytest tests/test_eval_botsim_native.py tests/test_eval_reddit_twibot_transfer.py tests/test_eval_twibot_native.py -x -q --basetemp .phase20_pytest_wave1`
  - validated in the combined Wave 1 run
- direct runtime smoke remains blocked until `trained_system_twibot.joblib` exists locally

## Self-Check: PASSED WITH EXTERNAL ARTIFACT BLOCKER

- [x] default model path stays on `trained_system_twibot.joblib`
- [x] inference routes through `CascadePipeline("twibot")`
- [x] metrics/confusion-matrix filenames are pinned for the maintained paper path
- [x] runtime smoke is documented as blocked by the deferred Phase 19 TwiBot artifact
