---
phase: 8
slug: twibot-20-data-loader
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-16
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3.4 |
| **Config file** | none (auto-discovered from `tests/`) |
| **Quick run command** | `python -m pytest tests/test_twibot20_io.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_twibot20_io.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------------|-----------|-------------------|-------------|--------|
| 08-01-01 | 01 | 0 | TW-01, TW-02, TW-03 | N/A | unit | `python -m pytest tests/test_twibot20_io.py -x -q` | ❌ W0 | ⬜ pending |
| 08-02-01 | 02 | 1 | TW-01 | defensive .get() on profile fields | unit | `python -m pytest tests/test_twibot20_io.py::test_load_accounts_schema tests/test_twibot20_io.py::test_node_idx_contiguous tests/test_twibot20_io.py::test_messages_structure tests/test_twibot20_io.py::test_null_tweet_handled -x -q` | ❌ W0 | ⬜ pending |
| 08-03-01 | 03 | 2 | TW-02 | cross-set ID drop | unit | `python -m pytest tests/test_twibot20_io.py::test_edges_schema tests/test_twibot20_io.py::test_null_neighbor_no_rows tests/test_twibot20_io.py::test_edges_in_set_only tests/test_twibot20_io.py::test_edge_weight -x -q` | ❌ W0 | ⬜ pending |
| 08-04-01 | 04 | 3 | TW-03 | assertion on out-of-bounds indices | unit | `python -m pytest tests/test_twibot20_io.py::test_validate_passes tests/test_twibot20_io.py::test_validate_bounds_fail -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_twibot20_io.py` — all TW-01/TW-02/TW-03 tests (does not exist yet):
  - `test_load_accounts_schema` — DataFrame has all 8 columns, correct dtypes, 1183 rows, label as int
  - `test_node_idx_contiguous` — node_idx is int32, 0-indexed by row, no gaps
  - `test_messages_structure` — each tweet → `{text, ts:None, kind:"tweet"}`
  - `test_null_tweet_handled` — tweet=None records produce empty messages list, not error
  - `test_edges_schema` — edges_df has correct 4-column schema and dtypes
  - `test_null_neighbor_no_rows` — neighbor=None records produce no rows
  - `test_edges_in_set_only` — cross-set IDs dropped; all src/dst are valid node_idx values
  - `test_edge_weight` — weight column is uniformly `log1p(1.0)`
  - `test_validate_passes` — validate() passes on valid accounts_df + edges_df
  - `test_validate_bounds_fail` — validate() raises AssertionError when src.max() >= len(accounts_df)

*Existing infrastructure covers everything else: pytest, conftest.py, test discovery.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| print() output includes no-neighbor fraction (~9.2%) and no-tweet fraction | TW-03 | validate() prints to stdout; no capture in automated tests | Run `python -c "from twibot20_io import load_accounts, build_edges, validate; a=load_accounts('test.json'); e=build_edges(a); validate(a, e)"` and verify two fraction lines print |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
