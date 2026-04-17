# Phase 8: Behavioral Tweet Parser and Stage 1 Adapter - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-17
**Phase:** 08-behavioral-tweet-parser-and-stage-1-adapter
**Areas discussed:** Tweet classifier logic, Parser location, Zero-tweet accounts

---

## Tweet Classifier Logic

| Option | Description | Selected |
|--------|-------------|----------|
| Simple prefix check | text.strip().upper().startswith("RT ") — fast, zero dependencies | ✓ |
| Regex with @username capture | ^(RT\|MT) @\w+: — stricter, extracts username in one pass | |
| Prefix check + fallback regex | Prefix for classification, regex only for username extraction | |

**Case sensitivity:**

| Option | Selected |
|--------|----------|
| Case-insensitive | ✓ |
| Uppercase only | |

**@username extraction:**

| Option | Description | Selected |
|--------|-------------|----------|
| Best-effort space-split | First @-prefixed token after RT/MT prefix | ✓ |
| Regex findall @mentions | All @mentions in RT/MT tweets | |
| No extraction — use listed_count | Keep demographic proxy for subreddit_list slot | |

---

## Parser Location

| Option | Description | Selected |
|--------|-------------|----------|
| Extend twibot20_io.py | Add parse_tweet_types() alongside load_accounts() | ✓ |
| Keep in evaluate_twibot20.py | Inline adapter helper | |
| New twibot20_features.py | Separate module | |

**submission_num mapping:**

| Option | Selected |
|--------|----------|
| Replace: submission_num ← original tweet count | ✓ |
| Keep both columns | |

---

## Zero-Tweet Accounts

| Option | Description | Selected |
|--------|-------------|----------|
| Leave as all-zero features | Zero-tweet is a real bot signal; nan_to_num handles it | ✓ |
| Impute with dataset median | Reduces sparsity, loses zero signal | |
| Flag and exclude | Separate evaluation with/without | |

**Logging:**

| Option | Selected |
|--------|----------|
| Log RT/MT/original/zero-tweet counts | ✓ |
| Silent | |

---

## Claude's Discretion

- Ratio cap value (1000.0): review against TwiBot-20 tweet distributions and document decision
- Public vs private naming of parse_tweet_types()

## Deferred Ideas

- Stage 2a / Stage 3 Twitter adapters — out of v1.2 scope
- Named-entity extraction from tweet text — future milestone
