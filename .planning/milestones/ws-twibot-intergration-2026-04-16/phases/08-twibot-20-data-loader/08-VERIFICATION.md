---
phase: 08-twibot-20-data-loader
verified: 2026-04-16T00:00:00Z
status: passed
score: 14/14
overrides_applied: 0
human_verification:
  - test: "Run integration check against real test.json: python -c \"from twibot20_io import load_accounts, build_edges, validate; a=load_accounts('test.json'); e=build_edges(a, 'test.json'); validate(a, e); assert len(a)==1183; assert len(e)==154; print('OK')\""
    expected: "1183 accounts loaded, 154 edges (116 etype-0 following + 38 etype-1 follower), no-neighbor fraction ~0.092, no-tweet fraction ~0.008, label distribution {0: 543, 1: 640}, exit 0"
    why_human: "test.json is the real TwiBot-20 dataset file. Its presence on the local filesystem cannot be assumed during automated CI verification. The integration check confirms exact counts from data inspection in 08-RESEARCH.md."
---

# Phase 8: TwiBot-20 Data Loader Verification Report

**Phase Goal:** Create a TwiBot-20 data loader module (twibot20_io.py) with load_accounts(), build_edges(), and validate() functions that produce BotSim-24-compatible DataFrames for cross-dataset evaluation.
**Verified:** 2026-04-16T00:00:00Z
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

All truths verified from both PLAN frontmatter must_haves, merged across Plan 01 and Plan 02.

#### Plan 01 Truths (TW-01)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | load_accounts() returns a DataFrame with 8 columns: node_idx, screen_name, statuses_count, followers_count, friends_count, created_at, messages, label | VERIFIED | twibot20_io.py lines 41-50 build all 8 columns; behavioral spot-check confirmed `(2, 8)` shape and correct column names |
| 2 | node_idx column is int32, 0-indexed, contiguous | VERIFIED | `df["node_idx"].astype(np.int32)` at line 53; `test_node_idx_contiguous` confirms `[0,1,2]` and `dtype==np.int32`; spot-check: `int32` confirmed |
| 3 | messages column contains list-of-dicts with keys text, ts, kind for each account | VERIFIED | Line 38: `{"text": str(t), "ts": None, "kind": "tweet"}`; `test_messages_structure` confirms exact dict equality |
| 4 | tweet=None records produce empty messages list, not an error | VERIFIED | Line 37: `tweets = record.get("tweet") or []`; `test_null_tweet_handled` confirms `df.iloc[0]["messages"] == []`; spot-check confirmed `[]` |
| 5 | label column contains int 0 or 1, not string | VERIFIED | Line 49: `int(record["label"])`; `test_label_is_int` confirms `is_integer_dtype`; spot-check: `int64` dtype, values `[0, 1]` |
| 6 | All profile string fields have trailing whitespace stripped | VERIFIED | Lines 43-47: `.strip()` on all profile string fields; `test_trailing_whitespace_stripped` confirms `"alice"` not `"alice "` and `statuses_count == 10` |

#### Plan 02 Truths (TW-02, TW-03)

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 7 | build_edges() returns a DataFrame with 4 columns: src (int32), dst (int32), etype (int8), weight (float32) | VERIFIED | Lines 103-108: explicit dtype casting; `test_edges_schema` confirms all 4 column names and dtypes; spot-check: `{'src': int32, 'dst': int32, 'etype': int8, 'weight': float32}` |
| 8 | neighbor=None records produce zero edge rows | VERIFIED | Line 88-89: `if neighbor is None: continue`; `test_null_neighbor_no_rows` confirms `len == 0` with 4-column schema preserved |
| 9 | Cross-set IDs not in evaluation set are silently dropped | VERIFIED | Lines 92-96: `if nid in id_to_idx` guard; `test_edges_in_set_only` confirms OUTSIDER and OUTSIDER2 dropped, exactly 1 in-set edge retained |
| 10 | following edges have etype=0 with src=current_account, dst=neighbor | VERIFIED | Line 93: `rows.append((src_idx, id_to_idx[nid], 0, WEIGHT))`; `test_edge_direction` confirms `src=0, dst=1, etype=0` for X following Y |
| 11 | follower edges have etype=1 with src=neighbor, dst=current_account | VERIFIED | Line 96: `rows.append((id_to_idx[nid], src_idx, 1, WEIGHT))`; `test_edge_direction` confirms `src=1, dst=0, etype=1` for Y following X |
| 12 | All edge weights are log1p(1.0) = 0.6931471805599453 | VERIFIED | Line 84: `WEIGHT = np.float32(np.log1p(1.0))`; `test_edge_weight` uses `np.allclose`; spot-check: `0.6931471824645996` (float32 rounding is expected and correct) |
| 13 | validate() passes without error on valid data and raises AssertionError on invalid | VERIFIED | Lines 130-137: assert checks; `test_validate_passes` passes; `test_validate_bounds_fail` confirms `AssertionError` on src=5 with n=1 |
| 14 | validate() prints no-neighbor and no-tweet fractions via print() | VERIFIED | Lines 142-144: three `print(f"[twibot20] ...")` statements; spot-check output confirmed `no-neighbor fraction: 0.500` and `no-tweet fraction: 0.500` |

**Score:** 14/14 truths verified

---

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `twibot20_io.py` | load_accounts, build_edges, validate functions plus `_no_neighbor_count` module-level variable | VERIFIED | 145-line file; all 3 public functions present; `_no_neighbor_count: int = 0` at line 11 |
| `tests/test_twibot20_io.py` | 13 unit tests covering TW-01, TW-02, TW-03 | VERIFIED | 231-line file; 13 test functions confirmed; 2 helper functions `_write_test_json` and `_make_record` present |

---

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| `tests/test_twibot20_io.py` | `twibot20_io.py` | `from twibot20_io import load_accounts, build_edges, validate` | WIRED | Line 14 of test file; all 3 symbols imported and actively called across 13 tests |
| `twibot20_io.py::build_edges` | `twibot20_io.py::load_accounts` | `id_to_idx` built from `accounts_df` produced by `load_accounts` | WIRED | Lines 79-82: `id_to_idx = {record["ID"]: int(accounts_df.iloc[i]["node_idx"]) ...}`; `test_edges_schema` and `test_edges_in_set_only` exercise the link |
| `twibot20_io.py::validate` | `twibot20_io.py::_no_neighbor_count` | `global _no_neighbor_count` — module-level variable set by load_accounts, read by validate | WIRED | Line 28 in `load_accounts` sets it; line 133 in `validate` declares `global _no_neighbor_count`; line 140 reads it |
| `twibot20_io.py::build_edges` | `botdetector_pipeline.py::build_graph_features_nodeidx` | edges_df schema must be drop-in compatible (src/dst int32, etype int8, weight float32) | WIRED | `botdetector_pipeline.py` lines 369-372 consume exact same column names and dtypes; schema matches precisely |

---

### Data-Flow Trace (Level 4)

`twibot20_io.py` is a loader/utility module, not a rendering component. It reads from a JSON file (filesystem) and returns DataFrames. Data flow is:

| Artifact | Data Source | Real Data Flows | Status |
|----------|-------------|-----------------|--------|
| `load_accounts` | `json.load(f)` from path parameter | Yes — iterates all records from JSON, no hardcoded returns | FLOWING |
| `build_edges` | `json.load(f)` from path parameter + `accounts_df` from caller | Yes — builds id_to_idx from real data, appends real edge tuples | FLOWING |
| `validate` | `accounts_df` and `edges_df` parameters | Yes — reads `accounts_df["messages"]`, `edges_df` bounds, `_no_neighbor_count` | FLOWING |

---

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| load_accounts returns 8-column DataFrame with correct schema | Python inline with synthetic 2-record JSON | `(2, 8)` shape, columns correct, `node_idx` int32 | PASS |
| tweet=None produces empty messages list | Python inline spot-check | `messages[1] == []` | PASS |
| label is int, not string | Python inline spot-check | `int64` dtype, values `[0, 1]` | PASS |
| screen_name trailing whitespace stripped | Python inline spot-check | `'alice'` not `'alice '` | PASS |
| build_edges produces correct dtype schema | Python inline spot-check | `{'src': int32, 'dst': int32, 'etype': int8, 'weight': float32}` | PASS |
| edge weight equals log1p(1.0) | Python inline spot-check | `0.6931471824645996` (float32 rounding of log1p(1.0)) | PASS |
| validate() prints diagnostics | Python inline spot-check | `[twibot20] accounts: 2, edges: 1` etc printed | PASS |
| All 13 unit tests pass | `python -m pytest tests/test_twibot20_io.py -v -q` | `13 passed in 0.08s` | PASS |
| Full test suite passes | `python -m pytest tests/ -q` | `61 passed, 18936 warnings in 17.85s` | PASS |
| Real test.json integration (1183 rows, 154 edges) | Requires test.json on filesystem | Not run — file not in repo | SKIP (human needed) |

---

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| TW-01 | 08-01-PLAN.md | Load TwiBot-20 accounts from test.json into BotSim-24-compatible DataFrame with profile fields mapped, tweets as messages, label parsed inline as int, node_idx as int32 | SATISFIED | `load_accounts()` implements all specified behaviors; 6 unit tests covering schema, dtypes, message format, None handling, label casting, whitespace stripping — all pass |
| TW-02 | 08-02-PLAN.md | Edge loader builds edges_df from neighbor.following/follower lists with ID remapping, etype assignment, log1p(1.0) weight, None=no edges; schema drop-in compatible with build_graph_features_nodeidx | SATISFIED | `build_edges()` implements all specified behaviors; 5 unit tests covering schema, null-neighbor, in-set filtering, weight, direction — all pass; confirmed compatible with `botdetector_pipeline.py` lines 369-372 |
| TW-03 | 08-02-PLAN.md | Validate data integrity — assert src.max/dst.max < len(accounts_df), required columns present; log no-neighbor count (~9%) and no-tweet count | SATISFIED | `validate()` implements column check, bounds check, print diagnostics; `test_validate_passes` and `test_validate_bounds_fail` both pass; `global _no_neighbor_count` declaration present at line 133 |

All 3 requirements claimed in PLAN frontmatter are fully covered. No orphaned requirements — REQUIREMENTS.md maps TW-04 through TW-07 to later phases (9 and 10) which are outside this phase's scope.

---

### Anti-Patterns Found

No anti-patterns detected.

| File | Pattern Checked | Result |
|------|----------------|--------|
| `twibot20_io.py` | TODO/FIXME/placeholder comments | None found |
| `twibot20_io.py` | Stub returns (return null, return {}, return []) | None found — all functions return substantive DataFrames |
| `twibot20_io.py` | Hardcoded empty initial state flowing to output | None — empty list `[]` is the `else` branch of `if rows:` Pitfall 5 guard, correctly produces an empty-but-typed DataFrame |
| `tests/test_twibot20_io.py` | TODO/FIXME/placeholder comments | None found |

---

### Human Verification Required

#### 1. Real test.json Integration Test

**Test:** With `test.json` present in the project root, run:
```
python -c "from twibot20_io import load_accounts, build_edges, validate; a=load_accounts('test.json'); e=build_edges(a, 'test.json'); validate(a, e); assert len(a)==1183; assert len(e)==154; assert (a['label']==1).sum()==640; assert (a['label']==0).sum()==543; print('Integration OK')"
```
**Expected:**
- `len(a) == 1183` (all accounts in test split)
- `len(e) == 154` (116 etype-0 following + 38 etype-1 follower)
- `(a['label']==1).sum() == 640`, `(a['label']==0).sum() == 543`
- validate() prints `no-neighbor fraction: 0.092` and `no-tweet fraction: 0.008` (approximately)
- No AssertionError raised; command exits 0
**Why human:** `test.json` is the actual TwiBot-20 dataset file. It is not committed to the repository. The exact row/edge counts and label distribution can only be confirmed against the real data file that must be present locally. All unit tests use synthetic minimal records.

---

### Gaps Summary

No gaps found. All 14 must-haves are verified. All 3 requirement IDs (TW-01, TW-02, TW-03) are satisfied with test evidence. No anti-patterns detected. One human verification item remains: integration against the real `test.json` dataset file which cannot be verified programmatically in this environment.

---

_Verified: 2026-04-16T00:00:00Z_
_Verifier: Claude (gsd-verifier)_
