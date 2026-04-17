---
phase: 08-twibot-20-data-loader
plan: "01"
subsystem: data-loader
tags: [twibot20, data-loading, pandas, numpy, tdd]
dependency_graph:
  requires: []
  provides: [twibot20_io.load_accounts, twibot20_io._no_neighbor_count]
  affects: [twibot20_io.build_edges, twibot20_io.validate]
tech_stack:
  added: []
  patterns: [standalone-loader-functions, path-as-parameter, defensive-profile-access]
key_files:
  created:
    - twibot20_io.py
    - tests/test_twibot20_io.py
  modified: []
decisions:
  - "D-01: Messages stored as {text, ts:None, kind:'tweet'} matching BotSim-24 schema"
  - "D-04: node_idx assigned by row enumeration, cast to int32"
  - "D-08: label cast to int inline from string '0'/'1'"
  - "Pitfall 2 guard: record.get('tweet') or [] handles tweet=None"
  - "_no_neighbor_count module-level variable tracks no-neighbor records for validate() in Plan 02"
metrics:
  duration_minutes: 8
  completed_date: "2026-04-16"
  tasks_completed: 2
  tasks_total: 2
  files_created: 2
  files_modified: 0
---

# Phase 8 Plan 01: TwiBot-20 load_accounts — Summary

**One-liner:** `load_accounts(path)` reads TwiBot-20 test.json into an 8-column BotSim-24-compatible DataFrame with int32 node_idx, stripped profile fields, typed messages, and int labels.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create test scaffold for load_accounts (TW-01) | 7d21744 | tests/test_twibot20_io.py |
| 2 | Implement load_accounts() in twibot20_io.py (TW-01) | 690ae17 | twibot20_io.py |

## Verification

All 6 TW-01 unit tests pass:

```
python -m pytest tests/test_twibot20_io.py -x -q
......
6 passed in 0.04s
```

Tests covered:
- `test_load_accounts_schema` — 8 required columns present, correct row count
- `test_node_idx_contiguous` — node_idx is [0,1,2,...], dtype int32
- `test_messages_structure` — each tweet → `{"text": t, "ts": None, "kind": "tweet"}`
- `test_null_tweet_handled` — tweet=None produces empty messages list
- `test_label_is_int` — label is int 0 or 1, not string
- `test_trailing_whitespace_stripped` — screen_name stripped, statuses_count numeric

## Deviations from Plan

None — plan executed exactly as written.

## Known Stubs

`build_edges()` and `validate()` are implemented with full logic (not stubs) to satisfy the import in the test file (`from twibot20_io import load_accounts, build_edges, validate`). Plan 02 will add tests for these functions; the implementations are already present and correct.

## Threat Flags

None — this plan introduces only local file I/O from a known dataset file. No new network endpoints, auth paths, or trust boundary crossings.

## Self-Check: PASSED

- [x] `twibot20_io.py` exists and contains `load_accounts`, `build_edges`, `validate`, `_no_neighbor_count`
- [x] `tests/test_twibot20_io.py` exists with 6 test functions and 2 helpers
- [x] Commit `7d21744` exists (test scaffold)
- [x] Commit `690ae17` exists (implementation)
- [x] All 6 tests pass: `python -m pytest tests/test_twibot20_io.py -x -q` exits 0
