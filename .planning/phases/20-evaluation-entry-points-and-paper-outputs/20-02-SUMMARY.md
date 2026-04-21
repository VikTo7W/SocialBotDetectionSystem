---
phase: 20
plan: "02"
subsystem: botsim-native-evaluation
tags: [evaluation, botsim, paper-outputs]
key-files:
  created:
    - eval_botsim_native.py
  modified:
    - tests/test_eval_botsim_native.py
metrics:
  tasks_completed: 2
  tasks_total: 2
---

# Plan 20-02 Summary

## Outcome

Built the maintained BotSim-native evaluation entry point and turned the Wave 0 BotSim contract tests green.

## Delivered

- `eval_botsim_native.py` with `run_inference_botsim_native`, `evaluate_botsim_native`, `_write_confusion_matrix`, `_save_json`, and CLI support
- deterministic S3 reconstruction via `split_train_accounts(..., seed=SEED)`
- paper outputs:
  - `paper_outputs/metrics_botsim.json`
  - `paper_outputs/confusion_matrix_botsim.png`

## Verification

- `python -m py_compile eval_botsim_native.py`
- `python -m pytest tests/test_eval_botsim_native.py tests/test_eval_reddit_twibot_transfer.py tests/test_eval_twibot_native.py -x -q --basetemp .phase20_pytest_wave1`
  - validated in the combined Wave 1 run
- `python eval_botsim_native.py`
  - completed successfully and wrote fresh paper outputs

## Self-Check: PASSED

- [x] default model path stays on `trained_system_botsim.joblib`
- [x] inference routes through `CascadePipeline("botsim")`
- [x] metrics JSON matches `evaluate_s3()` structure
- [x] confusion matrix PNG is written as a non-empty file
