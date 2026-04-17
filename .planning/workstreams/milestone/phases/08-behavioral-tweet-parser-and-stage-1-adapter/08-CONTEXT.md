# Phase 8: Behavioral Tweet Parser and Transfer Adapter Stabilization - Context

**Gathered:** 2026-04-17
**Status:** Revised scope

<domain>
## Phase Boundary

Replace the current demographic proxy (followers_count / friends_count / listed_count) in the TwiBot transfer adapter with behaviorally-grounded Twitter equivalents, and stabilize zero-shot transfer when TwiBot fields are systematically unavailable. Phase 8 remains zero-shot only: no model retraining, but adapter semantics and dimensionality-preserving missingness handling may be revised if the current transfer result collapses.

</domain>

<decisions>
## Implementation Decisions

### Tweet Classification Logic

- **D-01:** Classify each tweet using a case-insensitive simple prefix check: `text.strip().upper().startswith("RT ")` for retweets, same pattern for `"MT "`. No regex for classification.
- **D-02:** @username extraction uses best-effort space-split: after stripping the RT/MT prefix token, find the first space-delimited token starting with `@`. Skip the tweet if no `@` token is found.
- **D-03:** Prefix check is case-insensitive: `rt @user`, `Rt @user`, and `RT @user` all count as retweets.

### Parser Location

- **D-04:** Tweet parser lives in `twibot20_io.py` as `parse_tweet_types(messages)`.
- **D-05:** `parse_tweet_types()` accepts the `messages` list and returns a dict with `rt_count`, `mt_count`, `original_count`, and `rt_mt_usernames`.

### Transfer Adapter Scope Revision

- **D-06:** The original locked Stage 1 Twitter mapping is no longer frozen. Phase 8 now explicitly allows revising the zero-shot transfer mapping when TwiBot evaluation shows collapse.
- **D-07:** `comment_num_1` may be reassigned from RT count to non-RT / non-MT tweet count if that better matches the behavioral contribution signal required by the Reddit-trained Stage 1 model.
- **D-08:** `comment_num_2` remains the preferred slot for MT count unless execution evidence shows a better zero-shot analog.
- **D-09:** `subreddit_list` may be sourced from TwiBot `domain` instead of RT/MT @usernames when topical breadth is a better analog to Reddit subreddit diversity.
- **D-10:** `submission_num` may be reviewed alongside the other Stage 1 slots during execution. The chosen mapping must be documented and justified by measured TwiBot behavior, not intuition alone.
- **D-11:** The `evaluate_twibot20.py` column adapter remains the integration point for these mappings. The monkey-patch and ratio cap remain in place.

### Missingness and Diagnostics

- **D-12:** Zero-tweet accounts are still left as all-zero Stage 1 features. Zero-tweet is a real signal and should not be imputed away.
- **D-13:** TwiBot fields that are systematically unavailable but not semantically zero, especially Stage 2 timestamp-derived features when `ts=None` for all tweets, may use missingness-aware handling in Phase 8 without retraining, provided feature dimensionality stays unchanged.
- **D-14:** Log transfer diagnostics at adapter or evaluation time: tweet type distribution, zero-tweet fraction, timestamp-missing fraction, and any imputation/fallback path that activates on TwiBot.

### Claude's Discretion

- Ratio cap value (currently `1000.0`): review against actual TwiBot-20 tweet count distributions and adjust if needed.
- Whether `parse_tweet_types()` should remain public.
- Which missingness-aware strategy is smallest and safest for zero-shot transfer: fixed medians, persisted reference values, or another dimensionality-preserving fallback.

</decisions>

<canonical_refs>
## Canonical References

### Existing TwiBot-20 data layer
- `twibot20_io.py` - `load_accounts()` returns messages as `{"text": str, "ts": None, "kind": "tweet"}` and raw JSON carries `domain`
- `evaluate_twibot20.py` - current transfer adapter, diagnostics, and Stage 1 monkey-patch path

### Feature pipelines
- `features_stage1.py` - all 10 Stage 1 features and ratio construction
- `features_stage2.py` - current temporal block behavior when timestamps are missing

### Requirements
- `.planning/REQUIREMENTS.md` - FEAT-01 through FEAT-04 define the revised acceptance criteria for this phase

### Conventions
- `.planning/codebase/CONVENTIONS.md` - snake_case, verb-prefixed functions, type hints throughout

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `_detect_encoding(path)` in `twibot20_io.py`
- `np.nan_to_num` in `features_stage1.py`
- diagnostic print patterns in `validate()`

### Established Patterns
- module-level helper functions in `twibot20_io.py`
- monkey-patch pattern in `evaluate_twibot20.py` for replacing `bp.extract_stage1_matrix`
- deterministic test fixtures in `tests/test_twibot20_io.py` and `tests/test_evaluate_twibot20.py`

### Integration Points
- `parse_tweet_types()` in `twibot20_io.py` called by the column adapter in `run_inference()`
- transfer adapter in `evaluate_twibot20.py` is the direct replacement target for D-06 through D-14
- `features_stage2.py` is the direct target for timestamp-missing fallback behavior

</code_context>

<specifics>
## Specific Ideas

- `domain` is available in TwiBot raw JSON for every account inspected so far and is a credible candidate for `subreddit_list`
- Tweet type counts and username extraction remain computable from the already-loaded `messages` field
- Missing TwiBot timestamps currently collapse several Stage 2 features to zeros, which likely creates a cross-domain shift rather than a meaningful behavioral signal

</specifics>

<deferred>
## Deferred Ideas

- Full Twitter-native Stage 2a / Stage 3 feature redesign remains out of v1.2 scope
- Supervised TwiBot retraining remains out of scope
- Named-entity extraction from tweet text for richer mention analysis is future work

</deferred>

---

*Phase: 08-behavioral-tweet-parser-and-stage-1-adapter*
*Context revised: 2026-04-17*
