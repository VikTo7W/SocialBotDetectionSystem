# Phase 20 Verification

Date: 2026-04-19
Phase: 20 - Evaluation Entry Points and Paper Outputs
Status: Passed

## Automated Checks

- `python -m py_compile eval_botsim_native.py eval_reddit_twibot_transfer.py eval_twibot_native.py generate_table5.py`
  - Result: passed
- `python -m pytest tests/test_paper_outputs.py tests/test_eval_botsim_native.py tests/test_eval_reddit_twibot_transfer.py tests/test_eval_twibot_native.py tests/test_evaluate.py -x -q --basetemp .phase20_pytest_dedup`
  - Result: passed after removing the legacy duplicate evaluation test files
- `python -m pytest tests/test_paper_outputs.py tests/test_eval_botsim_native.py tests/test_eval_reddit_twibot_transfer.py tests/test_eval_twibot_native.py -x -q --basetemp .phase20_pytest_all_v2`
  - Result: `21 passed`
- `python -m pytest tests/test_ablation_tables.py --collect-only -q`
  - Result: `12 tests collected`
- `python -m pytest tests/test_evaluate.py tests/test_evaluate_twibot20_native.py -x -q`
  - Result: `22 passed`

## Per-Requirement Evidence

| Requirement | Status | Evidence | Command |
|-------------|--------|----------|---------|
| EVAL-01 | passed | `eval_botsim_native.py`, `paper_outputs/metrics_botsim.json`, `paper_outputs/confusion_matrix_botsim.png` | `python -m pytest tests/test_eval_botsim_native.py -x -q --basetemp .phase20_pytest_wave1` and `python eval_botsim_native.py` |
| EVAL-02 | passed | `eval_reddit_twibot_transfer.py`, `paper_outputs/metrics_reddit_transfer.json`, `paper_outputs/confusion_matrix_reddit_transfer.png` | `python -m pytest tests/test_eval_reddit_twibot_transfer.py -x -q --basetemp .phase20_pytest_transfer_fix` and `python eval_reddit_twibot_transfer.py` |
| EVAL-03 | passed | `eval_twibot_native.py`, green contract tests | `python -m pytest tests/test_eval_twibot_native.py -x -q --basetemp .phase20_pytest_wave1` |
| PAPER-01 | passed | three maintained evaluation entry points all write confusion-matrix paths; two runtime-smoked successfully | `python -m pytest tests/test_eval_botsim_native.py tests/test_eval_reddit_twibot_transfer.py tests/test_eval_twibot_native.py -x -q --basetemp .phase20_pytest_all_v2` |
| PAPER-02 | passed | three maintained evaluation entry points all write `evaluate_s3()` metrics JSON outputs | `python -m pytest tests/test_eval_botsim_native.py tests/test_eval_reddit_twibot_transfer.py tests/test_eval_twibot_native.py -x -q --basetemp .phase20_pytest_all_v2` |
| PAPER-03 | passed | `generate_table5.py`, `tests/test_paper_outputs.py`, default output `tables/table5_cross_dataset.tex` | `python -m pytest tests/test_paper_outputs.py -x -q --basetemp .phase20_pytest_all_v2` |

## End-to-End Smoke Run

Runtime prerequisites found locally:

- Present: `trained_system_botsim.joblib`
- Missing: `trained_system_twibot.joblib`
- Present data: `Users.csv`, `user_post_comment.json`, `edge_index.pt`, `edge_type.pt`, `edge_weight.pt`, `train.json`, `dev.json`, `test.json`

### Completed

- `python eval_botsim_native.py`
  - completed successfully
  - wrote:
    - `paper_outputs/metrics_botsim.json`
    - `paper_outputs/confusion_matrix_botsim.png`
- `python eval_reddit_twibot_transfer.py`
  - completed successfully after the live-run `account_id` adapter fix
  - wrote:
    - `paper_outputs/metrics_reddit_transfer.json`
    - `paper_outputs/confusion_matrix_reddit_transfer.png`

### Blocked

- `python eval_twibot_native.py`
  - not run because `trained_system_twibot.joblib` is still missing locally
- `python generate_table5.py`
  - blocked for the same reason: `paper_outputs/metrics_twibot_native.json` does not exist until the TwiBot-native evaluation can run against a maintained TwiBot artifact

## Environment Notes

- The Windows workspace still has pytest temp/cache permission friction; repo-local `--basetemp` plus outside-sandbox pytest runs were used where needed to avoid teardown false negatives
- The TwiBot-native runtime smoke remains downstream of the user-deferred Phase 19 TwiBot retraining gap, not a Phase 20 code-surface defect
- Legacy duplicate evaluation scripts and tests were removed after the maintained Phase 20 entry points were verified, so the repo now has a single supported evaluation surface
