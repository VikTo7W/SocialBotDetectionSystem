---
phase: 20
plan: "03"
subsystem: reddit-transfer-evaluation
tags: [evaluation, transfer, twibot]
key-files:
  created:
    - eval_reddit_twibot_transfer.py
  modified:
    - tests/test_eval_reddit_twibot_transfer.py
metrics:
  tasks_completed: 2
  tasks_total: 2
---

# Plan 20-03 Summary

## Outcome

Built the maintained Reddit-to-TwiBot transfer evaluation entry point, replaced the legacy global monkey-patch pattern with a DataFrame rewrite adapter, and fixed the live-run `account_id` gap revealed during smoke testing.

## Delivered

- `eval_reddit_twibot_transfer.py` with `_apply_transfer_adapter`, `run_inference_transfer`, `evaluate_reddit_twibot_transfer`, `_write_confusion_matrix`, `_save_json`, and CLI support
- adapter populates the BotSim Stage 1 columns on a copied DataFrame and synthesizes `account_id` from `node_idx` when the live TwiBot loader does not provide it
- removed the superseded legacy transfer entry point `evaluate_twibot20.py` and its duplicate test file once the maintained path was green
- paper outputs:
  - `paper_outputs/metrics_reddit_transfer.json`
  - `paper_outputs/confusion_matrix_reddit_transfer.png`

## Verification

- `python -m py_compile eval_reddit_twibot_transfer.py`
- `python -m pytest tests/test_eval_reddit_twibot_transfer.py -x -q --basetemp .phase20_pytest_transfer_fix`
  - `6 passed`
- `python eval_reddit_twibot_transfer.py`
  - completed successfully after the `account_id` adapter fix and wrote fresh paper outputs

## Self-Check: PASSED

- [x] default model path stays on `trained_system_botsim.joblib`
- [x] no mutation of `botdetector_pipeline.extract_stage1_matrix`
- [x] inference routes through `CascadePipeline("botsim")`
- [x] transfer metrics/confusion-matrix outputs land in `paper_outputs/`
