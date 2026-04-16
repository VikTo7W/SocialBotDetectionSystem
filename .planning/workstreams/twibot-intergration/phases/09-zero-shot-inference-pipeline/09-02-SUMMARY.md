---
phase: 09
plan: 02
subsystem: twibot-integration
tags: [inference, __main__, json-output, tdd, serialization]
requirements: [TW-04, TW-05]

dependency_graph:
  requires:
    - evaluate_twibot20.run_inference (Plan 01)
    - features_stage1.extract_stage1_matrix
    - botdetector_pipeline.predict_system
  provides:
    - evaluate_twibot20.__main__ block (script entry point)
    - results_twibot20.json (JSON array of inference records)
  affects:
    - Phase 10 (imports run_inference — now fully functional module)

tech_stack:
  added: []
  patterns:
    - pandas to_json(orient='records', indent=2) for NumPy-safe serialization (Pitfall 5)
    - sys.argv argument parsing with defaults in __main__ block (D-06)
    - monkeypatch.setattr for I/O mocking in test_main_block_saves_json

key_files:
  created:
    - .planning/workstreams/twibot-intergration/phases/09-zero-shot-inference-pipeline/09-02-SUMMARY.md
  modified:
    - evaluate_twibot20.py
    - tests/test_evaluate_twibot20.py

decisions:
  - results.to_json(orient='records', indent=2) used (not json.dump) to avoid TypeError on numpy.float32/int32 scalars (Pitfall 5, D-06)
  - __main__ prints 5 summary lines with [twibot20] prefix: saved count, bot count, stage3_used mean, amr_used mean, p_final mean
  - test_main_block_saves_json calls run_inference() directly (not via subprocess/runpy) to avoid I/O complexity

metrics:
  duration_seconds: 210
  completed_date: "2026-04-16"
  tasks_completed: 2
  tasks_total: 2
  files_created: 1
  files_modified: 2
---

# Phase 09 Plan 02: __main__ Block + JSON Output + All 5 Tests Summary

**One-liner:** Completes evaluate_twibot20.py with __main__ entry point using pandas to_json for NumPy-safe serialization and wires the final unit test to achieve 5/5 green.

---

## Tasks Completed

| Task | Type | Name | Commit | Result |
|------|------|------|--------|--------|
| 01 | feat | Add __main__ block to evaluate_twibot20.py (D-06) | 0977c98 | __main__ block added; syntax OK |
| 02 | feat | Implement test_main_block_saves_json — all 5 tests green | 628509e | 5/5 tests pass; full suite 67 passed |

---

## Verification Results

```
python -m pytest tests/test_evaluate_twibot20.py -v -q
# 5 passed — test_run_inference_returns_correct_schema, test_run_inference_end_to_end,
#             test_main_block_saves_json, test_ratio_clamping_applied, test_botsim_path_not_clamped

python -m pytest tests/ -x -q
# 67 passed, 0 failed, 0 skipped

python -c "from evaluate_twibot20 import run_inference; print('import OK')"
# import OK

python -c "
import botdetector_pipeline as bp
from features_stage1 import extract_stage1_matrix as orig
assert bp.extract_stage1_matrix is orig, 'Monkey-patch leaked!'
print('bp.extract_stage1_matrix is original — isolation confirmed')
"
# bp.extract_stage1_matrix is original — isolation confirmed
```

---

## TDD Gate Compliance

- RED gate: Inherited from Plan 01 — `test(09-01)` commit f382d28
- GREEN gate (wave 2): `feat(09-02)` commit 628509e — all 5 tests pass
- REFACTOR gate: Not needed — implementation matched plan structure exactly

---

## Deviations from Plan

None — plan executed exactly as written.

test_main_block_saves_json was implemented by calling run_inference() directly and saving via
results.to_json() rather than via runpy/subprocess — this matches the plan's strategy note
("Strategy: mock the I/O and verify JSON output, without launching a subprocess").

---

## Known Stubs

None — all stubs from Plan 01 have been resolved.

---

## Threat Surface Scan

No new threat surface introduced in Plan 02.

- __main__ block uses sys.argv paths — documented in T-09-01/T-09-02 from Plan 01.
- results_twibot20.json written to local cwd only — accepted per T-09-02.

---

## Self-Check: PASSED

Files modified:
- evaluate_twibot20.py — contains `if __name__ == "__main__":` block — CONFIRMED
- tests/test_evaluate_twibot20.py — test_main_block_saves_json implemented — CONFIRMED

Commits:
- 0977c98 (feat __main__ block) — FOUND
- 628509e (feat 5 tests green) — FOUND

Test results: 67 passed, 0 failed — all pre-existing tests continue to pass.
