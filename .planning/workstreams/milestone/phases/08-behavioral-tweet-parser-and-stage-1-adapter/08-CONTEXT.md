# Phase 8: Behavioral Tweet Parser and Stage 1 Adapter - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Replace the current demographic proxy (followers_count / friends_count / listed_count) in the evaluate_twibot20.py Stage 1 adapter with behaviorally-grounded Twitter equivalents derived from tweet text: RT count, MT count, original tweet count, and the set of distinct @usernames from RT/MT tweets. No model retraining. Zero-shot transfer only.

</domain>

<decisions>
## Implementation Decisions

### Tweet Classification Logic

- **D-01:** Classify each tweet using a **case-insensitive simple prefix check** — `text.strip().upper().startswith("RT ")` for retweets, same pattern for `"MT "`. No regex for classification.
- **D-02:** @username extraction uses **best-effort space-split**: after stripping the RT/MT prefix token, find the first space-delimited token starting with `@`. Skip the tweet if no `@` token is found. This covers the canonical `RT @user: text` and `RT @user text` formats without regex overhead.
- **D-03:** Prefix check is **case-insensitive** — `rt @user`, `Rt @user`, and `RT @user` all count as retweets. Real tweet data varies in casing.

### Parser Location

- **D-04:** Tweet parser lives in **twibot20_io.py** as a new `parse_tweet_types(messages)` helper function. Consistent with existing `_detect_encoding()` private helper pattern. Keeps all TwiBot-20 data processing in one module.
- **D-05:** `parse_tweet_types()` accepts the `messages` list (list of `{"text": str, "ts": None, "kind": "tweet"}` dicts) and returns a dict: `{"rt_count": int, "mt_count": int, "original_count": int, "rt_mt_usernames": list[str]}`.

### Stage 1 Feature Mapping

- **D-06:** `submission_num` ← original tweet count (replaces `statuses_count`). Original tweets are the Twitter semantic equivalent of Reddit submissions — statuses_count includes RT+MT which dilutes the signal.
- **D-07:** `comment_num_1` ← RT count (pure amplification = closest Twitter analog to Reddit type-1 comments)
- **D-08:** `comment_num_2` ← MT count (modified amplification = Reddit type-2 comment analog)
- **D-09:** `subreddit_list` ← list of distinct `@usernames` extracted from RT/MT tweets (breadth of accounts engaged = Reddit subreddit diversity analog)
- **D-10:** The evaluate_twibot20.py column adapter block calls `parse_tweet_types()` per-account to produce these values. The monkey-patch and ratio cap remain in place (cap value may be reviewed — not explicitly discussed, left to Claude's discretion based on tweet count distributions).

### Zero-Tweet Accounts

- **D-11:** Zero-tweet accounts are **left as all-zero features**. The nan_to_num call in features_stage1.py already handles 0/eps → 0 cleanly. Zero-tweet is a real bot signal and should flow through the model unchanged.
- **D-12:** **Log tweet type distribution** in validate() or at adapter time, consistent with existing `no-neighbor fraction` and `no-tweet fraction` diagnostics — report RT count, MT count, original count, and zero-tweet account fraction across the dataset.

### Claude's Discretion

- Ratio cap value (currently 1000.0): review against actual TwiBot-20 tweet count distributions and adjust if needed. Tweet counts are smaller than follower counts, but 1000.0 may still be appropriate — planner/executor should check distributions and document the decision.
- Whether `parse_tweet_types()` should be exported from twibot20_io.py's public API or remain a private `_parse_tweet_types()` helper.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing TwiBot-20 data layer
- `twibot20_io.py` — `load_accounts()` returns messages as `{"text": str, "ts": None, "kind": "tweet"}`; `_detect_encoding()` shows the private helper naming convention; `validate()` shows the diagnostic logging pattern
- `evaluate_twibot20.py` lines 87–130 — current Stage 1 column adapter (demographic proxy D-09); monkey-patch pattern (TW-05) that replaces `bp.extract_stage1_matrix`; `_RATIO_CAP = 1000.0` definition

### Stage 1 feature pipeline
- `features_stage1.py` — all 10 Stage 1 features; `np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)` at the end handles zero-tweet all-zero vectors cleanly

### Requirements
- `.planning/REQUIREMENTS.md` — FEAT-01, FEAT-02, FEAT-03 define the acceptance criteria for this phase

### Conventions
- `.planning/codebase/CONVENTIONS.md` — snake_case, verb-prefixed functions (`parse_*`, `load_*`, `build_*`), private helpers with `_` prefix, type hints throughout

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_detect_encoding(path)` in twibot20_io.py — pattern for private helper functions exported via explicit import
- `_int_field(profile, key)` in evaluate_twibot20.py — pattern for safe field coercion helpers defined locally
- `np.nan_to_num` in features_stage1.py — already handles all-zero vectors from zero-tweet accounts

### Established Patterns
- Module-level private helpers (`_detect_encoding`, `_no_neighbor_count`) in twibot20_io.py
- Monkey-patch pattern in evaluate_twibot20.py for replacing `bp.extract_stage1_matrix` at inference time
- Diagnostic print statements in `validate()`: `[twibot20] accounts: N, edges: M` format

### Integration Points
- `parse_tweet_types()` in twibot20_io.py called by the column adapter in `run_inference()` in evaluate_twibot20.py
- Column adapter at lines 91–107 of evaluate_twibot20.py is the direct replacement target for D-06–D-09
- `load_accounts()` already stores `messages` list — no changes to data loading needed

</code_context>

<specifics>
## Specific Ideas

- Tweet type counts and username extraction should be computable per-account from the `messages` field already loaded by `load_accounts()` — no re-reading of JSON required at adapter time
- The `messages` list entries use `{"text": str(t), "ts": None, "kind": "tweet"}` — access via `msg["text"]` for classification

</specifics>

<deferred>
## Deferred Ideas

- Ratio cap value tuning deferred to executor (Claude's discretion based on distribution check)
- Stage 2a / Stage 3 Twitter feature adapters — out of v1.2 scope
- Named-entity extraction from tweet text for richer @mention analysis — future milestone

</deferred>

---

*Phase: 08-behavioral-tweet-parser-and-stage-1-adapter*
*Context gathered: 2026-04-17*
