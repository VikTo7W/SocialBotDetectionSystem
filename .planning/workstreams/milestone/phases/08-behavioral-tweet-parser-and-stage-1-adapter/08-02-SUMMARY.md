---
phase: "08"
plan: "02"
subsystem: twibot20-adapter
completed_date: "2026-04-17"
---

# Phase 08 Plan 02 Summary

The TwiBot-20 Stage 1 adapter now maps behavioral tweet counts and account
domain breadth into the existing BotSim-24 schema, preserving the Stage 1
ratio clamp via the existing monkey-patch wrapper.

## What changed

- `submission_num <- total tweet volume (rt + mt + original)`
- `comment_num_1  <- original_count (authored tweets)`
- `comment_num_2  <- mt_count (modified retweets)`
- `subreddit_list <- domain_list` (from `load_accounts`, normalized per account)
- `_normalize_domain_list` helper removed; `load_accounts()` already normalizes domain
- Adapter logs: `tweet distribution`, `zero-tweet fraction`, `domain breadth`,
  `timestamp-missing fraction`, `ratio distribution (pre-cap) p95/p99`
- `_RATIO_CAP = 1000.0` retained with inline FEAT-03 justification comment

## Fix applied after initial execution

`test_behavioral_adapter_subreddit_list_is_domain_list` was failing because the
adapter re-read `domain` from raw JSON (all accounts got the same value) instead
of using the per-account `domain_list` column already populated by `load_accounts`.
Fixed by replacing the raw JSON re-read with `df["domain_list"].tolist()`.

## Verification

- `python -m pytest tests/test_evaluate_twibot20.py -q` → 14 passed
- `python -m pytest tests/ -q` → 101 passed, 0 failed (full suite green)
- `grep -c "r\[.profile.\]" evaluate_twibot20.py` → 0 (Pitfall 1 root cause removed)
- `grep -c "parse_tweet_types" evaluate_twibot20.py` → 2 (import + call)
- Monkey-patch and `_RATIO_CAP` structurally preserved
