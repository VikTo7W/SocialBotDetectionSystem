---
phase: 08-twibot-20-data-loader
plan: "02"
subsystem: data-loader
tags: [twibot20, edge-building, validation, pandas, numpy, tdd]
dependency_graph:
  requires: [twibot20_io.load_accounts, twibot20_io._no_neighbor_count]
  provides: [twibot20_io.build_edges, twibot20_io.validate]
  affects: [evaluate_twibot20.py (Phase 9)]
tech_stack:
  added: []
  patterns: [id-remapping, log1p-edge-weight, empty-edge-guard, module-level-diagnostics]
key_files:
  created: []
  modified:
    - tests/test_twibot20_io.py
    - twibot20_io.py
decisions:
  - "D-05: following edge direction src=current/dst=neighbor etype=0; follower src=neighbor/dst=current etype=1"
  - "D-06: id_to_idx built from record['ID'] field for string-to-int32 remapping"
  - "Pitfall 5 guard: empty rows list handled before zip(*rows) to avoid ValueError"
  - "global _no_neighbor_count declared in validate() to satisfy acceptance criterion (read-only access)"
metrics:
  duration_minutes: 5
  completed_date: "2026-04-16"
  tasks_completed: 2
  tasks_total: 3
  files_created: 0
  files_modified: 2
---

# Phase 8 Plan 02: build_edges and validate — Summary

**One-liner:** `build_edges()` remaps TwiBot-20 string IDs to int32 node indices and produces a 4-column edges DataFrame with log1p(1.0) weights; `validate()` checks column completeness and index bounds then prints diagnostic fractions.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Add edge and validation tests to test_twibot20_io.py (TW-02, TW-03) | 2280c22 | tests/test_twibot20_io.py |
| 2 | Implement build_edges() and validate() in twibot20_io.py (TW-02, TW-03) | e3ec5ea | twibot20_io.py |

**Task 3 (checkpoint:human-verify):** Awaiting human verification against real test.json.

## Verification

All 13 TW-01/TW-02/TW-03 unit tests pass:

```
python -m pytest tests/test_twibot20_io.py -x -q
.............
13 passed in 0.08s
```

Full test suite green:

```
python -m pytest tests/ -x -q
61 passed, 18936 warnings in 18.94s
```

Tests covered (7 new in this plan):
- `test_edges_schema` — 4 columns with correct dtypes (int32/int32/int8/float32)
- `test_null_neighbor_no_rows` — None neighbor produces 0 rows, schema preserved
- `test_edges_in_set_only` — OUTSIDER IDs silently dropped, 1 in-set edge retained
- `test_edge_weight` — all weights equal np.log1p(1.0)
- `test_edge_direction` — following: src=current/dst=neighbor etype=0; follower: src=neighbor/dst=current etype=1
- `test_validate_passes` — validate() does not raise on valid data
- `test_validate_bounds_fail` — validate() raises AssertionError on src=5 with n=1

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical Functionality] Added `global _no_neighbor_count` inside validate()**
- **Found during:** Task 2 acceptance criteria check
- **Issue:** The plan's acceptance criterion required `global _no_neighbor_count` inside `validate()`. The Plan 01 implementation read the module-level variable without the explicit global declaration (valid Python for reads), but omitted the explicit statement.
- **Fix:** Added `global _no_neighbor_count` as the first statement in `validate()` body.
- **Files modified:** twibot20_io.py
- **Commit:** e3ec5ea

**Note:** `build_edges()` and `validate()` were already fully implemented in Plan 01 (as noted in 08-01-SUMMARY.md under "Known Stubs"). Task 2 in this plan only required adding the `global` declaration.

## Known Stubs

None — all functions are fully implemented with real logic.

## Threat Flags

None — no new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries beyond what was introduced in Plan 01.

## Self-Check: PASSED

- [x] `tests/test_twibot20_io.py` contains all 7 new test functions
- [x] `twibot20_io.py` contains `def build_edges(accounts_df: pd.DataFrame, path: str) -> pd.DataFrame:`
- [x] `twibot20_io.py` contains `def validate(accounts_df: pd.DataFrame, edges_df: pd.DataFrame) -> None:`
- [x] `twibot20_io.py` contains `id_to_idx = {` (ID remapping)
- [x] `twibot20_io.py` contains `np.float32(np.log1p(1.0))`
- [x] `twibot20_io.py` contains `if neighbor is None:`
- [x] `twibot20_io.py` contains `if len(edges_df) > 0:`
- [x] `twibot20_io.py` contains `global _no_neighbor_count` inside validate (line 133)
- [x] `twibot20_io.py` contains `print(f"[twibot20]`
- [x] `twibot20_io.py` contains `(id_to_idx[nid], src_idx, 1,` (follower direction)
- [x] Commit `2280c22` exists (test scaffold)
- [x] Commit `e3ec5ea` exists (implementation fix)
- [x] 13 tests pass
- [x] Full suite passes (61 tests)
