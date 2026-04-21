# Wave 0 Collection Snapshot

Date: 2026-04-19
Phase: 20-01

## Ablation Import Gate

- `python -c "import ablation_tables; print(ablation_tables.filter_edges_for_split.__module__)"`
  - Result: `train_botsim`
- `python -m pytest tests/test_ablation_tables.py --collect-only -q`
  - Result: success, 12 tests collected
- `tests/test_ablation_tables.py` now collects without `ImportError: cannot import name 'filter_edges_for_split' from 'main'`

## New Red Tests

### tests/test_eval_botsim_native.py

- Module count: 5 tests
- Collect-only state inside full suite: `ModuleNotFoundError`
- Expected missing module: `eval_botsim_native`

### tests/test_eval_reddit_twibot_transfer.py

- Module count: 5 tests
- Collect-only state inside full suite: `ModuleNotFoundError`
- Expected missing module: `eval_reddit_twibot_transfer`

### tests/test_eval_twibot_native.py

- Module count: 5 tests
- Collect-only state inside full suite: `ModuleNotFoundError`
- Expected missing module: `eval_twibot_native`

### tests/test_paper_outputs.py

- Module count: 5 tests
- Collect-only state inside full suite: `ModuleNotFoundError`
- Expected missing module: `generate_table5`

## Pre-Existing Regression Check

- `python -m pytest tests/test_evaluate.py tests/test_evaluate_twibot20_native.py -x -q`
  - Result: `22 passed`
- No regression detected in the pre-existing green evaluation tests

## Full Suite Collect-Only Snapshot

- `python -m pytest tests/ --collect-only -q`
  - Result: 148 tests collected before interruption on 4 expected module-missing errors
  - New-error classes: only the four expected `ModuleNotFoundError` entries above
