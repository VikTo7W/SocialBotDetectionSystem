---
phase: "08"
plan: "01"
subsystem: twibot20-adapter
tags: [behavioral-features, tweet-parser, stage1-adapter, zero-shot-transfer, feat-01, feat-02, feat-03]
dependency_graph:
  requires:
    - twibot20_io.load_accounts (messages field already populated)
    - features_stage1.extract_stage1_matrix (column layout indices 0-9)
    - evaluate_twibot20.run_inference (adapter insertion point)
  provides:
    - twibot20_io.parse_tweet_types (new public function)
    - evaluate_twibot20._RATIO_CAP (module constant)
    - behavioral Stage 1 features: submission_num=original_count, comment_num_1=rt_count,
      comment_num_2=mt_count, subreddit_list=rt_mt_usernames
  affects:
    - zero-shot TwiBot-20 inference accuracy (behavioral vs demographic Stage 1 features)
tech_stack:
  added: []
  patterns:
    - case-insensitive prefix classification (D-01/D-03)
    - space-split @username extraction (D-02)
    - dict.fromkeys deduplication preserving insertion order
    - monkey-patch with finally-restore pattern (TW-05, T-09-01)
key_files:
  created: []
  modified:
    - twibot20_io.py (added parse_tweet_types())
    - tests/test_twibot20_io.py (added 9 FEAT-01 unit tests)
    - evaluate_twibot20.py (replaced column adapter, added _RATIO_CAP, added D-12 logging)
    - tests/test_evaluate_twibot20.py (added 3 FEAT-02 adapter verification tests)
decisions:
  - parse_tweet_types() made public (no underscore prefix) so unit tests import it cleanly
  - _RATIO_CAP kept at 1000.0; Twitter 3200-tweet API limit bounds behavioral counts well below cap
  - raw JSON re-read retained for account_id extraction (r["ID"]) — r["profile"] accesses removed
  - Distribution logging placed inside run_inference() after adapter block (D-12)
metrics:
  duration_minutes: 15
  completed_date: "2026-04-17"
  tasks_completed: 2
  files_modified: 4
  tests_added: 12
  tests_total: 96
---

# Phase 08 Plan 01: Behavioral Tweet Parser and Stage 1 Adapter Summary

**One-liner:** Case-insensitive RT/MT/original tweet classifier with deduplicated @username extraction wired into Stage 1 feature slots, replacing demographic proxies for zero-shot TwiBot-20 transfer.

## What Was Built

### Task 1: parse_tweet_types() in twibot20_io.py

Added `parse_tweet_types(messages)` as a public function to `twibot20_io.py`. The function:

- Classifies each tweet by case-insensitive prefix check: `text.strip().upper().startswith("RT ")` for retweets, same pattern for `"MT "` (D-01, D-03)
- Extracts the first space-delimited `@`-prefixed token after the RT/MT prefix word as the handle (D-02)
- Deduplicates handles with `dict.fromkeys()` preserving insertion order (Python 3.7+ guaranteed)
- Returns `{"rt_count": int, "mt_count": int, "original_count": int, "rt_mt_usernames": list[str]}`
- Zero-tweet accounts return all-zero dict — intentional signal per D-11

Added 9 unit tests to `test_twibot20_io.py` covering all FEAT-01 acceptance criteria: RT/MT/original classification, case-insensitivity, @username extraction, no-handle graceful skip, deduplication, insertion-order preservation, empty messages.

### Task 2: Stage 1 Column Adapter in evaluate_twibot20.py

Replaced the demographic proxy adapter block with behavioral counts:

| Column | Old Source | New Source | Decision |
|--------|------------|------------|----------|
| `submission_num` | `statuses_count` (includes RT+MT) | `parse_tweet_types()["original_count"]` | D-06 |
| `comment_num_1` | `followers_count` | `parse_tweet_types()["rt_count"]` | D-07 |
| `comment_num_2` | `friends_count` | `parse_tweet_types()["mt_count"]` | D-08 |
| `subreddit_list` | `[None]*listed_count` | `parse_tweet_types()["rt_mt_usernames"]` | D-09 |

Also:
- Added `_RATIO_CAP = 1000.0` module constant with documentation comment (FEAT-03: reviewed for Twitter tweet-count distributions — 3200-tweet API limit bounds ratios well below 1000.0)
- Changed inline `50.0` clamp to `_RATIO_CAP` in `_clamped_s1` wrapper
- Added tweet type distribution logging after adapter block (D-12): RT/MT/original totals and zero-tweet fraction
- Added 3 FEAT-02 adapter verification tests confirming behavioral counts flow into Stage 1 slots correctly, including zero-tweet account (all-zero) and all-original account behavior

## Decisions Made

| Decision | Rationale |
|----------|-----------|
| `parse_tweet_types()` public (no `_` prefix) | Unit tests import it directly; it is a meaningful public API for any caller wanting tweet statistics |
| `_RATIO_CAP = 1000.0` unchanged | Twitter 3200-tweet API limit means rt/mt/original ratios are well below 1000; empirically safe |
| `raw` JSON re-read retained | Still needed for `r["ID"]` (account_id column); `r["profile"]` accesses removed; cost is negligible |
| Distribution logging in `run_inference()` | Consistent with D-12 guidance; adjacent to adapter block where tweet_stats is computed |

## Test Results

All 96 project tests pass after both tasks. Target modules:

- `tests/test_twibot20_io.py`: 22 passed (13 pre-existing + 9 new FEAT-01 tests)
- `tests/test_evaluate_twibot20.py`: 11 passed (8 pre-existing + 3 new FEAT-02 tests)

## Deviations from Plan

None — plan executed exactly as specified by D-01 through D-12 decisions in CONTEXT.md.

## Known Stubs

None. `parse_tweet_types()` is fully implemented with real logic. The `subreddit_list` column now contains actual @username strings rather than the previous `[None]*N` length-encoding trick — `features_stage1.py` uses `len(subreddit_list)` which works identically with either representation.

## Threat Flags

No new network endpoints, auth paths, file access patterns, or schema changes at trust boundaries introduced. This phase is purely in-memory string processing on data already loaded from a local JSON file.

## Self-Check: PASSED

- `twibot20_io.py` — modified, parse_tweet_types present: FOUND
- `tests/test_twibot20_io.py` — 9 new tests: FOUND (22 total, all pass)
- `evaluate_twibot20.py` — _RATIO_CAP, parse_tweet_types import, behavioral adapter: FOUND
- `tests/test_evaluate_twibot20.py` — 3 new FEAT-02 tests: FOUND (11 total, all pass)
- Commit `0de9180`: FOUND (Task 1)
- Commit `71363f1`: FOUND (Task 2)
