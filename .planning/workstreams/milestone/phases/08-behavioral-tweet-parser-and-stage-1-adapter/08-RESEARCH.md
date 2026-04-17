# Phase 8: Behavioral Tweet Parser and Stage 1 Adapter - Research

**Researched:** 2026-04-17
**Domain:** Python — tweet text classification, Stage 1 feature adapter, monkey-patch pattern
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Classify each tweet using a case-insensitive simple prefix check —
  `text.strip().upper().startswith("RT ")` for retweets, same pattern for `"MT "`. No regex for
  classification.
- **D-02:** @username extraction uses best-effort space-split: after stripping the RT/MT prefix
  token, find the first space-delimited token starting with `@`. Skip the tweet if no `@` token is
  found. This covers canonical `RT @user: text` and `RT @user text` formats without regex overhead.
- **D-03:** Prefix check is case-insensitive — `rt @user`, `Rt @user`, and `RT @user` all count as
  retweets.
- **D-04:** Tweet parser lives in **twibot20_io.py** as a new `parse_tweet_types(messages)` helper
  function. Consistent with existing `_detect_encoding()` private helper pattern.
- **D-05:** `parse_tweet_types()` accepts the `messages` list (list of `{"text": str, "ts": None,
  "kind": "tweet"}` dicts) and returns a dict:
  `{"rt_count": int, "mt_count": int, "original_count": int, "rt_mt_usernames": list[str]}`.
- **D-06:** `submission_num` ← original tweet count (replaces `statuses_count`).
- **D-07:** `comment_num_1` ← RT count.
- **D-08:** `comment_num_2` ← MT count.
- **D-09:** `subreddit_list` ← list of distinct `@usernames` extracted from RT/MT tweets.
- **D-10:** The evaluate_twibot20.py column adapter block calls `parse_tweet_types()` per-account.
  The monkey-patch and ratio cap remain in place.
- **D-11:** Zero-tweet accounts are left as all-zero features.
- **D-12:** Log tweet type distribution in `validate()` or at adapter time — report RT count, MT
  count, original count, and zero-tweet account fraction across the dataset.

### Claude's Discretion

- Ratio cap value (currently `_RATIO_CAP = 1000.0`): review against actual TwiBot-20 tweet-count
  distributions and adjust if needed. Executor should check distributions and document the decision.
- Whether `parse_tweet_types()` should be exported as a public function or kept private
  `_parse_tweet_types()`.

### Deferred Ideas (OUT OF SCOPE)

- Stage 2a / Stage 3 Twitter feature adapters — out of v1.2 scope.
- Named-entity extraction from tweet text for richer @mention analysis — future milestone.
- Ratio cap value tuning deferred to executor (Claude's discretion based on distribution check).
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| FEAT-01 | Behavioral tweet parser classifies each account's tweets into RT-prefixed, MT-prefixed, and regular (original) buckets, and extracts distinct @usernames from RT/MT tweets | D-01/D-02/D-03/D-04/D-05 fully specify implementation; no external dependency; pure Python string ops on the existing `messages` field |
| FEAT-02 | Stage 1 adapter maps `submission_num` ← original tweet count, `comment_num_1` ← RT count, `comment_num_2` ← MT count, `subreddit_list` ← list of distinct @usernames from RT/MT tweets | D-06/D-07/D-08/D-09/D-10 specify the exact column substitution; column adapter block at evaluate_twibot20.py lines 91–107 is the direct replacement target |
| FEAT-03 | Ratio cap is reviewed and tuned for Twitter tweet-count distributions | Existing `_RATIO_CAP = 1000.0` at line 117 of evaluate_twibot20.py; distribution review is an empirical task at adapter call time |
</phase_requirements>

---

## Summary

Phase 8 replaces the current demographic proxy features in the TwiBot-20 Stage 1 adapter
(`followers_count`, `friends_count`, `listed_count`) with behavioral equivalents derived directly
from tweet text: RT count, MT count, original tweet count, and the set of distinct @usernames from
RT/MT tweets. The implementation is purely additive — no model retraining occurs, no new libraries
are required, and no data re-loading is needed because `load_accounts()` already stores the full
`messages` list on every row.

The work splits cleanly into two deliverables: (1) a new `parse_tweet_types(messages)` function
in `twibot20_io.py`, and (2) a replacement of the column adapter block in `run_inference()` inside
`evaluate_twibot20.py` that calls `parse_tweet_types()` per-account and maps its output to the four
Stage 1 slots. The monkey-patch wrapper and ratio cap remain structurally unchanged; only the
values that fill `submission_num`, `comment_num_1`, `comment_num_2`, and `subreddit_list` change.

There are 4 pre-existing failing tests in `test_evaluate_twibot20.py` (all caused by a
`KeyError: 'profile'` when `run_inference()` re-reads the JSON and synthetic test JSON records
contain no `"profile"` key). These tests were written against the prior demographic proxy design
and must be updated to match the behavioral adapter. The 17 tests in `test_twibot20_io.py` are
green and should stay green. New tests for `parse_tweet_types()` must be added to
`test_twibot20_io.py`.

**Primary recommendation:** Implement `parse_tweet_types()` in twibot20_io.py first, add unit
tests, then replace the column adapter block in evaluate_twibot20.py and fix the 4 failing tests.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Tweet classification (RT/MT/original) | Data layer (twibot20_io.py) | — | All TwiBot-20 data processing belongs in the IO module (D-04) |
| @username extraction | Data layer (twibot20_io.py) | — | Part of parse_tweet_types(); same module as classification |
| Stage 1 column adapter | Inference adapter (evaluate_twibot20.py) | — | Existing run_inference() column adapter block is the exact insertion point |
| Ratio cap / monkey-patch | Inference adapter (evaluate_twibot20.py) | — | Monkey-patch targets bp.extract_stage1_matrix — unchanged structurally |
| Tweet type distribution logging | Data layer (validate()) or Inference adapter | — | D-12 says validate() or adapter time; both are acceptable per context |
| nan/zero-vector handling | Feature extractor (features_stage1.py) | — | np.nan_to_num already handles zero-tweet all-zero vectors — no change needed |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python (stdlib) | 3.13 | str.strip(), str.upper(), str.startswith(), list operations | All tweet parsing logic is pure stdlib — no new dependencies |
| numpy | project-existing | np.nan_to_num, np.clip | Already used in features_stage1.py and evaluate_twibot20.py |
| pandas | project-existing | DataFrame column assignment | Already used throughout |

[VERIFIED: codebase grep — no new packages required for this phase]

### Supporting

No new packages. All operations are pure Python string manipulation on the existing `messages`
field.

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Simple prefix check (D-01) | regex `^RT @\w+` | Regex is more precise but slower and harder to reason about; D-01 explicitly rejects it |
| Space-split @username (D-02) | regex `@\w+` | Regex finds all mentions; D-02 restricts to first token after prefix, which is the canonical RT/MT handle position |

**Installation:** No new packages required.

---

## Architecture Patterns

### System Architecture Diagram

```
TwiBot-20 test.json
        |
        v
load_accounts()  ──────────────────────────────────────────────
        |                                                       |
        | messages: [{"text":str,"ts":None,"kind":"tweet"}]    |
        |                                                       |
        v                                                       |
parse_tweet_types(messages)                             accounts_df
        |
        | {"rt_count":N, "mt_count":N,
        |  "original_count":N, "rt_mt_usernames":[...]}
        |
        v
run_inference() — column adapter block
        |
        | df["submission_num"] = original_count    (was statuses_count)
        | df["comment_num_1"]  = rt_count          (was followers_count)
        | df["comment_num_2"]  = mt_count          (was friends_count)
        | df["subreddit_list"] = rt_mt_usernames   (was [None]*listed_count)
        |
        v
monkey-patch: _twitter_s1(df)
        |  X = _orig_extract_stage1_matrix(df)
        |  X[:, 6:10] = np.clip(X[:, 6:10], 0.0, _RATIO_CAP)
        v
predict_system(sys_loaded, df, edges_df) ──> results DataFrame
```

### Recommended Project Structure

No new files needed. Changes are confined to two existing files:

```
twibot20_io.py           # Add parse_tweet_types() (new function)
evaluate_twibot20.py     # Replace column adapter block (lines 91–107)
tests/
└── test_twibot20_io.py  # Add parse_tweet_types() unit tests (new test functions)
test_evaluate_twibot20.py # Fix 4 failing tests (update synthetic JSON + adapter expectations)
```

### Pattern 1: parse_tweet_types() in twibot20_io.py

**What:** A new module-level function that iterates over the `messages` list, classifies each tweet
by case-insensitive prefix, extracts the first `@`-prefixed token as the RT/MT handle, and returns
counts plus the deduplicated username set.

**When to use:** Called once per account inside the column adapter in `run_inference()`.

**Example:**
```python
# Source: CONTEXT.md D-01, D-02, D-03, D-05 [VERIFIED: codebase inspection]
def parse_tweet_types(messages: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Classify an account's tweets into RT, MT, and original buckets.

    Args:
        messages: List of {"text": str, "ts": None, "kind": "tweet"} dicts
            as returned by load_accounts().

    Returns:
        Dict with keys rt_count (int), mt_count (int), original_count (int),
        rt_mt_usernames (list[str] of distinct @-handles from RT/MT tweets).
    """
    rt_count = 0
    mt_count = 0
    original_count = 0
    rt_mt_usernames: List[str] = []

    for msg in messages:
        text = msg["text"].strip()
        upper = text.upper()
        if upper.startswith("RT "):
            rt_count += 1
            tokens = text.split()
            # tokens[0] is "RT", tokens[1] should be "@handle" or "@handle:"
            if len(tokens) > 1 and tokens[1].startswith("@"):
                rt_mt_usernames.append(tokens[1].lstrip("@").rstrip(":").lower())
        elif upper.startswith("MT "):
            mt_count += 1
            tokens = text.split()
            if len(tokens) > 1 and tokens[1].startswith("@"):
                rt_mt_usernames.append(tokens[1].lstrip("@").rstrip(":").lower())
        else:
            original_count += 1

    return {
        "rt_count": rt_count,
        "mt_count": mt_count,
        "original_count": original_count,
        "rt_mt_usernames": list(dict.fromkeys(rt_mt_usernames)),  # deduplicate, preserve order
    }
```

**Note on `dict.fromkeys`:** This is the idiomatic Python 3.7+ deduplication preserving insertion
order. An alternative is `list(set(...))` but that loses order and is non-deterministic.
[VERIFIED: Python 3.7+ language spec — dict preserves insertion order]

### Pattern 2: Column Adapter Replacement in run_inference()

**What:** Replace lines 91–107 (the demographic proxy block) in evaluate_twibot20.py with a
per-account call to `parse_tweet_types()` and direct assignment to the four Stage 1 slots.

**When to use:** Inside the Step 3 column adapter block of `run_inference()`.

**Example:**
```python
# Source: CONTEXT.md D-06/D-07/D-08/D-09/D-10 [VERIFIED: codebase inspection]
df = accounts_df.copy()
df["account_id"] = [r["ID"] for r in raw]        # D-07: stable Twitter user ID
df["username"]   = df["screen_name"]              # D-03: keep screen_name

# Behavioral tweet adapter (FEAT-01, FEAT-02)
tweet_stats = [parse_tweet_types(msgs) for msgs in df["messages"]]
df["submission_num"] = [s["original_count"] for s in tweet_stats]   # D-06
df["comment_num_1"]  = [s["rt_count"]       for s in tweet_stats]   # D-07
df["comment_num_2"]  = [s["mt_count"]       for s in tweet_stats]   # D-08
df["subreddit_list"] = [s["rt_mt_usernames"] for s in tweet_stats]  # D-09
```

The `raw` JSON re-read (currently used to extract `followers_count` etc.) is still required for
`account_id` extraction (the `"ID"` field). That re-read stays; only what we pull from `raw` changes.

### Pattern 3: Distribution Logging (D-12)

**What:** After computing `tweet_stats`, log aggregate counts and the zero-tweet fraction.

**When to use:** Inside `run_inference()` after the adapter block, or inside `validate()`.

**Example:**
```python
# Source: CONTEXT.md D-12; existing pattern in twibot20_io.validate() [VERIFIED: codebase]
n = len(tweet_stats)
total_rt  = sum(s["rt_count"]       for s in tweet_stats)
total_mt  = sum(s["mt_count"]       for s in tweet_stats)
total_orig = sum(s["original_count"] for s in tweet_stats)
zero_tweet_frac = sum(1 for s in tweet_stats
                      if s["rt_count"] + s["mt_count"] + s["original_count"] == 0) / n
print(f"[twibot20] tweet distribution: RT={total_rt}, MT={total_mt}, original={total_orig}")
print(f"[twibot20] zero-tweet fraction: {zero_tweet_frac:.3f}")
```

### Anti-Patterns to Avoid

- **Using statuses_count for submission_num after this phase:** After the adapter is in place,
  `df["submission_num"]` must come from `parse_tweet_types()["original_count"]`, not
  `df["statuses_count"]`. The statuses_count includes RT+MT and is a weaker signal.
- **Building the username list with regex on the full text:** D-02 explicitly requires space-split
  on the first token after the RT/MT prefix. Do not use `re.findall(r"@\w+", text)` — that would
  collect all @mentions in the tweet body, not just the retweeted account.
- **Re-reading the JSON file to get tweet text:** All tweets are already in `accounts_df["messages"]`
  from `load_accounts()`. No second file read is needed for tweet classification.
- **Mutating accounts_df in place:** The `run_inference()` function already does `df =
  accounts_df.copy()`. Keep the copy pattern to avoid side effects on the original DataFrame.
- **Closing over the raw json re-read unnecessarily:** The `raw` variable is still needed for the
  `account_id` column (`r["ID"]`). Do not remove it; just stop reading `r["profile"]` fields.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dict deduplication with order preservation | Custom seen-set + list | `list(dict.fromkeys(items))` | Python 3.7+ guaranteed dict ordering; one liner |
| NaN / Inf protection on ratio columns | Manual if-guards | `np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)` already in features_stage1.py | Already present; zero-tweet all-zero vector is handled cleanly |
| Ratio capping on X[:,6:10] | Custom loop | `np.clip(X[:, 6:10], 0.0, _RATIO_CAP)` in the existing monkey-patch | Already in evaluate_twibot20.py _twitter_s1 wrapper |

**Key insight:** This phase is almost entirely string parsing on data already in memory. There is
nothing to hand-roll. Every non-trivial numerical concern (nan, inf, ratio overflow) is already
handled downstream by existing code.

---

## Common Pitfalls

### Pitfall 1: Synthetic test JSON missing "profile" key causes KeyError in existing tests

**What goes wrong:** 4 tests in `test_evaluate_twibot20.py` currently FAIL with
`KeyError: 'profile'`. The synthetic JSON records generated by `_make_twibot_json()` have only
`{"ID": ..., "label": ...}` — no `"profile"` key. The current column adapter at line 103 does
`r["profile"]` causing the crash.

**Why it happens:** The tests were written before the raw JSON re-read block existed, or assume the
block would be refactored away. The new behavioral adapter should NOT re-read profile fields from
`raw`, so this pitfall may resolve naturally — but the test helper `_make_twibot_json()` still
needs to produce records that have `"ID"` (needed for `account_id` column).

**How to avoid:** After the adapter is rewritten to stop reading `r["profile"]`, verify the
synthetic JSON in test helpers only needs `"ID"` and `"label"` fields. If `account_id` extraction
(`r["ID"]`) is the only remaining use of `raw`, the tests will pass with the existing minimal
synthetic JSON. Confirm this explicitly.

**Warning signs:** `KeyError: 'profile'` or `KeyError: 'ID'` in test output.

### Pitfall 2: parse_tweet_types() called on accounts_df["messages"] but raw is still needed

**What goes wrong:** The `raw` JSON re-read (lines 84–85 of evaluate_twibot20.py) is retained
solely for `account_id = [r["ID"] for r in raw]`. If someone removes the `raw` re-read to
"simplify" the adapter, account_id extraction breaks.

**Why it happens:** The `"ID"` field (Twitter user ID string) is not stored in `load_accounts()`
output — it is pulled from the raw JSON in the current adapter. `accounts_df` has `node_idx` (int)
and `screen_name` (str) but not the `"ID"` field.

**How to avoid:** Keep the `raw` re-read. It is a single `json.load()` of an already-decoded file
and the encoding is already cached in `_detect_encoding()`. Alternatively, the planner could add
`"ID"` as a column in `load_accounts()` to eliminate the re-read — but that is a larger change
than D-04 implies and should only be done if the planner chooses it explicitly.

**Warning signs:** `AttributeError` or missing `account_id` column in results DataFrame.

### Pitfall 3: subreddit_list must be a list of strings, not a list of ints

**What goes wrong:** The Stage 1 feature extractor does
`sr_num = df["subreddit_list"].map(lambda x: len(x) if isinstance(x, list) else 0)`.
The only thing that matters is the *length* of the list. However, passing strings (from
`rt_mt_usernames`) instead of `[None] * count` changes the semantics slightly — but both produce
the same `sr_num` value (len(list)). This is intentional and correct per D-09.

**Why it happens:** The old adapter used `[None] * listed_count` as a length-encoding trick.
The new adapter uses the actual username list, which is also a list and `len()` works identically.
No change to features_stage1.py is needed.

**How to avoid:** No action needed. Verify with a quick unit test that
`len(["@a", "@b"]) == 2` as expected. The subreddit_list column type is list in both old and new
implementations.

### Pitfall 4: Zero-tweet account produces all-zero list from parse_tweet_types()

**What goes wrong:** An account with `messages = []` passed to `parse_tweet_types()` returns
`{"rt_count": 0, "mt_count": 0, "original_count": 0, "rt_mt_usernames": []}`. This is correct
per D-11. The downstream `sr_num = len([]) = 0`, and the ratio features produce `0 / (0 + eps) = 0`.
With `np.nan_to_num`, all values remain 0. This is intentional.

**How to avoid:** No action needed. Confirm with a unit test that an empty messages list produces
all zeros. The D-11 decision explicitly endorses this behavior.

### Pitfall 5: _RATIO_CAP review requires actual data distribution

**What goes wrong:** FEAT-03 requires the ratio cap to be reviewed. Tweet counts are typically
smaller than follower counts (which motivated raising the cap from 50 to 1000). But with behavioral
counts (rt_count, mt_count, original_count), the maximum plausible value is much smaller — prolific
tweeters in TwiBot-20 rarely exceed 3200 tweets (Twitter API historical limit was 3200). A ratio
like `original_count / (rt_count + eps)` with 1000 tweets original and 10 RTs = 100.0, well below
1000.0. The cap may be fine as-is but must be confirmed empirically.

**How to avoid:** At adapter time (or in a separate diagnostic step), compute the distribution of
`post_c1`, `post_c2`, `post_ct`, `post_sr` across all TwiBot-20 accounts and report the 95th/99th
percentile. Document the decision in a comment at the `_RATIO_CAP` definition.

---

## Code Examples

Verified patterns from codebase inspection:

### Existing validate() diagnostic pattern (to match for D-12)
```python
# Source: twibot20_io.py lines 169-174 [VERIFIED: codebase]
no_tweet_frac = sum(1 for m in accounts_df["messages"] if len(m) == 0) / n
no_neighbor_frac = _no_neighbor_count / n if n > 0 else 0.0

print(f"[twibot20] accounts: {n}, edges: {len(edges_df)}")
print(f"[twibot20] no-neighbor fraction: {no_neighbor_frac:.3f}")
print(f"[twibot20] no-tweet fraction: {no_tweet_frac:.3f}")
```

### Existing monkey-patch pattern (unchanged)
```python
# Source: evaluate_twibot20.py lines 119-130 [VERIFIED: codebase]
_RATIO_CAP = 1000.0

def _twitter_s1(df_inner, *args, **kwargs):
    X = _orig_extract_stage1_matrix(df_inner)
    X[:, 6:10] = np.clip(X[:, 6:10], 0.0, _RATIO_CAP)  # cap post_c1/c2/ct/sr
    return X

bp.extract_stage1_matrix = _twitter_s1
try:
    results = predict_system(
        sys_loaded, df, edges_df, nodes_total=len(accounts_df)
    )
finally:
    bp.extract_stage1_matrix = _orig_extract_stage1_matrix  # always restore (T-09-01)
```

### Stage 1 feature extraction layout (for ratio cap column indices)
```python
# Source: features_stage1.py lines 26-39 [VERIFIED: codebase]
# Columns 0-5: name_len, post_num, c1, c2, c_total, sr_num
# Columns 6-9: post_c1, post_c2, post_ct, post_sr  <-- capped by monkey-patch
X = np.stack([
    name_len,     # 0
    post_num,     # 1  <- submission_num (original tweet count after Phase 8)
    c1,           # 2  <- comment_num_1 (RT count after Phase 8)
    c2,           # 3  <- comment_num_2 (MT count after Phase 8)
    c_total,      # 4
    sr_num,       # 5  <- len(subreddit_list) = len(rt_mt_usernames) after Phase 8
    post_c1,      # 6  <- ratio, capped at _RATIO_CAP
    post_c2,      # 7  <- ratio, capped at _RATIO_CAP
    post_ct,      # 8  <- ratio, capped at _RATIO_CAP
    post_sr,      # 9  <- ratio, capped at _RATIO_CAP
], axis=1)
```

---

## Runtime State Inventory

This phase is a code-and-test change only. No runtime state inventory applies.

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None — no database records reference tweet parser logic | None |
| Live service config | None — no external service config | None |
| OS-registered state | None | None |
| Secrets/env vars | None | None |
| Build artifacts | trained_system_v12.joblib — no change to model; only adapter code changes | None — model is unchanged |

---

## State of the Art

| Old Approach | Current Approach | Impact |
|--------------|-----------------|--------|
| `followers_count` → comment_num_1 (demographic proxy) | `rt_count` → comment_num_1 (behavioral) | Measures what the account actually does, not who follows it |
| `friends_count` → comment_num_2 | `mt_count` → comment_num_2 | Measures amplification behavior |
| `[None]*listed_count` → subreddit_list | `rt_mt_usernames` → subreddit_list | Measures breadth of engagement, not passive list membership |
| `statuses_count` → submission_num (includes RT+MT) | `original_count` → submission_num | Original content only; more analogous to Reddit submission count |

---

## Environment Availability

Step 2.6: SKIPPED — phase is purely code/string-parsing changes with no external CLI tool or
service dependencies beyond the project's existing Python environment.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest (existing) |
| Config file | none detected (runs with default discovery) |
| Quick run command | `python -m pytest tests/test_twibot20_io.py tests/test_evaluate_twibot20.py -x -q` |
| Full suite command | `python -m pytest tests/ -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| FEAT-01 | parse_tweet_types() classifies RT/MT/original and extracts @usernames | unit | `pytest tests/test_twibot20_io.py -k "parse_tweet" -x` | ❌ Wave 0 — new test functions needed |
| FEAT-01 | Case-insensitive prefix detection (rt/RT/Rt) | unit | same | ❌ Wave 0 |
| FEAT-01 | Zero-tweet account returns all-zero dict | unit | same | ❌ Wave 0 |
| FEAT-01 | No @-token in RT tweet — username skipped gracefully | unit | same | ❌ Wave 0 |
| FEAT-02 | run_inference() column adapter uses behavioral counts, not demographic proxy | unit | `pytest tests/test_evaluate_twibot20.py -x` | ✅ exists but 4 tests FAILING — need update |
| FEAT-02 | submission_num == original_count per account | unit | `pytest tests/test_evaluate_twibot20.py -x` | ❌ Wave 0 — new assertion needed |
| FEAT-02 | subreddit_list == list of @usernames (not [None]*N) | unit | same | ❌ Wave 0 |
| FEAT-03 | _RATIO_CAP reviewed; decision documented in code comment | manual + smoke | `python evaluate_twibot20.py test.json` (requires real data) | manual only |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_twibot20_io.py tests/test_evaluate_twibot20.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_twibot20_io.py` — add `test_parse_tweet_types_*` functions (FEAT-01):
  - `test_parse_tweet_types_rt_counted` — RT prefix classified correctly
  - `test_parse_tweet_types_mt_counted` — MT prefix classified correctly
  - `test_parse_tweet_types_original_counted` — non-RT/MT tweet classified as original
  - `test_parse_tweet_types_case_insensitive` — `rt @user` and `Rt @user` both counted
  - `test_parse_tweet_types_username_extracted` — @handle extracted from RT tweet
  - `test_parse_tweet_types_no_at_token_skipped` — tweet with no @handle after RT prefix
  - `test_parse_tweet_types_deduplication` — same @handle from two RT tweets appears once
  - `test_parse_tweet_types_empty_messages` — empty list returns all zeros
- [ ] Fix 4 failing tests in `tests/test_evaluate_twibot20.py` that assume demographic proxy columns:
  - Update `_make_twibot_df()` to include tweet messages with RT/MT content
  - Update assertions that expect `followers_count`-based values to expect RT/MT counts
  - Confirm `_make_twibot_json()` synthetic records need only `"ID"` and `"label"` (no `"profile"` key needed after refactor)

---

## Security Domain

This phase performs no authentication, no user input from network sources, no cryptography, no
access control, and no external data ingestion at runtime. Input is a local file path to a JSON
file on disk, loaded with the existing `_detect_encoding()` + `json.load()` pattern. No ASVS
categories apply beyond the baseline that already governs the project.

---

## Open Questions

1. **Should `parse_tweet_types()` be public or private?**
   - What we know: `_detect_encoding()` is private but imported explicitly in evaluate_twibot20.py
     (`from twibot20_io import ... _detect_encoding`). The test file currently imports only public
     symbols from `twibot20_io`.
   - What's unclear: Whether tests for `parse_tweet_types()` should import it directly (requires
     public or explicit import) or test it indirectly through `run_inference()`.
   - Recommendation: Make it public (`parse_tweet_types`, no underscore prefix) so unit tests can
     import it cleanly. It is a meaningful public API for any caller that wants tweet statistics.

2. **Should `account_id` extraction move into load_accounts()?**
   - What we know: `load_accounts()` does not currently store the `"ID"` field; `run_inference()`
     re-reads the JSON to get it. After Phase 8, `r["profile"]` fields are no longer needed from
     the re-read — only `r["ID"]` remains.
   - What's unclear: Whether the planner wants to eliminate the `raw` re-read entirely by adding
     `"id"` to `load_accounts()`, or keep the minimal re-read.
   - Recommendation: Keep the `raw` re-read as-is (one `json.load()`, negligible cost) and only
     remove the `r["profile"]` accesses. Moving `"ID"` into `load_accounts()` is a valid cleanup
     but out of the stated D-04/D-05 scope.

3. **_RATIO_CAP value with tweet-count distributions**
   - What we know: With behavioral counts (RT, MT, original), the maximum realistic count per
     account in TwiBot-20 is bounded by the Twitter 3200-tweet API limit. Ratio
     `original/(RT+eps)` with 1000 original and 0 RT = 1000/eps ≈ 1e9 — massive. Cap is still
     needed but 1000.0 may be low (some accounts have few RTs but many originals).
   - What's unclear: The actual distribution. Need empirical check.
   - Recommendation: Keep 1000.0 as the initial value. The executor should print the 95th
     percentile of the four ratio columns before capping and document whether 1000.0 is
     sufficient or needs adjustment.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | `dict.fromkeys(list)` deduplication preserves insertion order in Python 3.13 | Code Examples | Low — dict ordering is guaranteed since Python 3.7; Python 3.13 inherits this |
| A2 | Twitter 3200-tweet API limit bounds TwiBot-20 tweet counts per account | Open Questions Q3 | Low — TwiBot-20 was collected via API; accounts with >3200 tweets would only show 3200 |
| A3 | The `"ID"` field is always present in every TwiBot-20 JSON record | Pitfall 2 | Medium — if any record lacks `"ID"`, `account_id` extraction crashes; validate() should assert this |

---

## Sources

### Primary (HIGH confidence)
- `twibot20_io.py` — verified load_accounts(), validate(), _detect_encoding() patterns directly
- `evaluate_twibot20.py` — verified current column adapter (lines 84–131), monkey-patch pattern, _RATIO_CAP = 1000.0
- `features_stage1.py` — verified column layout (indices 0–9), np.nan_to_num call
- `tests/test_twibot20_io.py` — verified 17 green tests, _make_record() fixture
- `tests/test_evaluate_twibot20.py` — verified 4 failing tests and root cause (KeyError: 'profile')
- `.planning/REQUIREMENTS.md` — FEAT-01, FEAT-02, FEAT-03 definitions
- `08-CONTEXT.md` — all D-01 through D-12 decisions

### Secondary (MEDIUM confidence)
- `.planning/codebase/CONVENTIONS.md` — snake_case, verb-prefixed functions, Google-style docstrings

### Tertiary (LOW confidence)
- None.

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new dependencies; pure stdlib + existing project libraries
- Architecture: HIGH — codebase fully read; integration points confirmed by grep and file inspection
- Pitfalls: HIGH — root cause of 4 failing tests confirmed by running pytest; other pitfalls derived from code inspection
- Test gaps: HIGH — test file read in full; failing tests identified precisely

**Research date:** 2026-04-17
**Valid until:** 2026-05-17 (stable Python project, no fast-moving dependencies)
