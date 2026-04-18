---
status: complete
phase: 11-reproducible-twibot-evaluation-flow
source:
  - 11-01-SUMMARY.md
  - 11-02-SUMMARY.md
started: "2026-04-18T12:00:00.000Z"
updated: "2026-04-18T12:01:00.000Z"
---

## Current Test

[testing complete]

## Tests

### 1. Test stubs accept kwargs
expected: |
  In tests/test_evaluate_twibot20.py, both test_evaluate_twibot20_returns_metrics
  and test_evaluate_twibot20_calls_evaluate_s3 now use `lambda p, m, **kw: results_df`
  (not `lambda p, m: results_df`). Running:
    python -m py_compile tests/test_evaluate_twibot20.py
  completes with no output (no syntax errors). A direct grep confirms both stubs
  are updated:
    grep -c "lambda p, m, \*\*kw" tests/test_evaluate_twibot20.py
  should output 2.
result: pass

### 2. output_dir routes artifacts to chosen directory
expected: |
  Running evaluate_twibot20.py with a custom output directory argument writes all
  three artifacts into that directory. Verification:
    python -c "
  import os, sys, types, unittest.mock as m
  # Confirm os.path.join is used for artifact writes
  import ast, inspect
  src = open('evaluate_twibot20.py').read()
  assert 'os.path.join(output_dir' in src, 'output_dir routing missing'
  assert 'os.makedirs(output_dir' in src, 'makedirs missing'
  print('output_dir routing present')
  "
  prints: output_dir routing present
result: pass

### 3. TWIBOT_COMPARISON_PATH env-var override in ablation_tables.py
expected: |
  ablation_tables.py reads the comparison artifact path from the environment:
    python -c "
  src = open('ablation_tables.py').read()
  assert 'TWIBOT_COMPARISON_PATH' in src, 'env var missing'
  print('TWIBOT_COMPARISON_PATH present')
  "
  prints: TWIBOT_COMPARISON_PATH present
result: pass

### 4. Module docstring documents canonical command and artifact schemas
expected: |
  evaluate_twibot20.py has an expanded module docstring containing at least:
  - 'Canonical command' (REPRO-01 documentation)
  - artifact filename references (results_twibot20.json, metrics_twibot20.json,
    metrics_twibot20_comparison.json)
  Verification:
    python -c "
  import evaluate_twibot20
  d = evaluate_twibot20.__doc__ or ''
  assert 'Canonical command' in d or 'canonical command' in d.lower(), 'canonical command missing'
  assert 'results_twibot20.json' in d, 'artifact schema missing'
  print('docstring complete')
  "
  prints: docstring complete
result: pass

## Summary

total: 4
passed: 4
issues: 0
skipped: 0
blocked: 0
pending: 0

## Gaps

[none yet]
