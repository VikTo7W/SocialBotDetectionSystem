---
phase: 09
plan: 01
subsystem: twibot-integration
tags: [inference, column-adapter, monkey-patch, clamping, tdd]
requirements: [TW-04, TW-05]

dependency_graph:
  requires:
    - twibot20_io.load_accounts
    - twibot20_io.build_edges
    - twibot20_io.validate
    - botdetector_pipeline.predict_system
    - features_stage1.extract_stage1_matrix
  provides:
    - evaluate_twibot20.run_inference
  affects:
    - Phase 10 (imports run_inference directly)

tech_stack:
  added:
    - evaluate_twibot20.py (new module)
    - tests/test_evaluate_twibot20.py (5 tests)
  patterns:
    - monkey-patch restore via try/finally (T-09-01 mitigation)
    - column adapter inline in run_inference()
    - np.clip for Stage 1 ratio clamping (TW-05, D-04)

key_files:
  created:
    - evaluate_twibot20.py
    - tests/test_evaluate_twibot20.py
  modified: []

decisions:
  - Column adapter is inline in run_inference() — not extracted to twibot20_io.py (D-01)
  - statuses_count maps to submission_num (D-02); Reddit-specific columns zero-filled (D-03)
  - Clamping applied via monkey-patch of bp.extract_stage1_matrix (D-04, Pitfall 1)
  - account_id extracted from record["ID"] via second JSON read (D-07)
  - __main__ block deferred to Plan 02

metrics:
  duration_seconds: 170
  completed_date: "2026-04-16"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 0
---

# Phase 09 Plan 01: Wave 1 TDD — Test Stubs + run_inference() Summary

**One-liner:** Zero-shot TwiBot-20 inference via monkey-patch clamping and column adapter; run_inference() returns 11-column DataFrame with Stage 1 ratio features clamped to [0.0, 50.0].

---

## Tasks Completed

| Task | Type | Name | Commit | Result |
|------|------|------|--------|--------|
| 01 | TDD RED | Write 5 test stubs (all fail with ImportError) | f382d28 | 5 tests collected, all fail — RED confirmed |
| 02 | TDD GREEN | Implement evaluate_twibot20.py | 8b2d455 | 3/5 wave-1 tests green; full suite 66 passed, 1 skipped |

---

## Verification Results

```
python -m pytest tests/test_evaluate_twibot20.py::test_run_inference_returns_correct_schema -x -q  # PASS
python -m pytest tests/test_evaluate_twibot20.py::test_run_inference_end_to_end -x -q               # PASS
python -m pytest tests/test_evaluate_twibot20.py::test_ratio_clamping_applied -x -q                 # PASS
python -m pytest tests/test_evaluate_twibot20.py::test_botsim_path_not_clamped -x -q                # PASS
python -m pytest tests/test_evaluate_twibot20.py::test_main_block_saves_json -x -q                  # SKIPPED (Plan 02)
python -m pytest tests/ -x -q                                                                        # 66 passed, 1 skipped
```

**bp.extract_stage1_matrix after import:** Confirmed restored to original function (not _clamped_s1).

---

## TDD Gate Compliance

- RED gate: `test(09-01)` commit f382d28 — 5 stubs created, all fail with ImportError
- GREEN gate: `feat(09-01)` commit 8b2d455 — 3 wave-1 tests pass, full suite clean
- REFACTOR gate: Not needed — implementation matched plan structure exactly

---

## Deviations from Plan

None — plan executed exactly as written.

The plan noted `test_botsim_path_not_clamped` "may PASS already" and it did — it depends only on `features_stage1.extract_stage1_matrix` directly, which is not wrapped by `evaluate_twibot20.py`. This is correct isolation behavior.

---

## Known Stubs

| Stub | File | Line | Reason |
|------|------|------|--------|
| `test_main_block_saves_json` | `tests/test_evaluate_twibot20.py` | ~88 | Deferred to Plan 02 per plan spec; pytest.skip() used |
| `# __main__ block implemented in Plan 02` | `evaluate_twibot20.py` | last line | __main__ block deferred to Plan 02 per plan spec |

---

## Threat Surface Scan

| Flag | File | Description |
|------|------|-------------|
| threat_flag: Tampering | evaluate_twibot20.py | bp.extract_stage1_matrix monkey-patch — mitigated by try/finally restore in finally block (T-09-01) |
| threat_flag: Information Disclosure | evaluate_twibot20.py | json.load + joblib.load on caller-supplied paths — accepted (T-09-02, local paths only, no network I/O) |

Both threat flags match the plan's STRIDE register and are handled per specified dispositions.

---

## Self-Check: PASSED

Files created:
- evaluate_twibot20.py — FOUND
- tests/test_evaluate_twibot20.py — FOUND

Commits:
- f382d28 (test RED) — FOUND
- 8b2d455 (feat GREEN) — FOUND

Test results: 66 passed, 1 skipped — all pre-existing 62 tests continue to pass.
