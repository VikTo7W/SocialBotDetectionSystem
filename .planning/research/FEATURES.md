# Feature Landscape: Twitter-Native Features for TwiBot-20 Cascade Stages

**Domain:** Twitter bot detection — supervised cascade trained on TwiBot-20
**Researched:** 2026-04-18
**Milestone:** v1.4 Twitter-Native Supervised Baseline
**Overall confidence:** HIGH — all features code-verified against twibot20_io.py and TwiBot-20 schema

---

## Data Availability Audit

The following fields are genuinely present in TwiBot-20 records as loaded by `twibot20_io.load_accounts()`:

| Field | TwiBot-20 Source | Type | Notes |
|-------|-----------------|------|-------|
| `screen_name` | `profile.screen_name` | str | Always present; may be empty string |
| `statuses_count` | `profile.statuses_count` | int | Lifetime tweet count from Twitter API |
| `followers_count` | `profile.followers_count` | int | Snapshot at collection time |
| `friends_count` | `profile.friends_count` | int | Accounts this user follows |
| `created_at` | `profile.created_at` | str | RFC 2822 format: "Mon Apr 06 15:28:43 +0000 2009" |
| `messages` | `tweet[]` | list[dict] | Text strings, ts=None (timestamps absent) |
| `domain_list` | `domain[]` | list[str] | Topic domains the user tweets about |
| `neighbor.following` | `neighbor.following[]` | list[str] | Screen names of accounts followed |
| `neighbor.follower` | `neighbor.follower[]` | list[str] | Screen names of followers |

**Permanently absent — no imputing permitted:**
- Tweet timestamps (ts=None for all records in current loader)
- Profile description / bio text (excluded from project scope after leakage audit)
- Retweet counts, like counts, reply counts per tweet
- Verified status, geo, language fields

---

## Stage 1: Metadata Features

**Purpose:** Fast first-pass classifier on numeric profile metadata. Exits confident accounts; routes uncertain ones to Stage 2.

**Input:** `accounts_df` profile fields only — no tweet content, no graph.

### Table Stakes (must-have for meaningful Stage 1)

| Feature Name | Source Field | Formula | Signal Rationale | Requires Timestamps |
|---|---|---|---|---|
| `screen_name_len` | `screen_name` | `len(screen_name)` | Bots often use generated names (long, random suffixes) | No |
| `statuses_count` | `statuses_count` | raw int | Bots typically have very high or very low post volume | No |
| `followers_count` | `followers_count` | raw int | Bots often have near-zero followers | No |
| `friends_count` | `friends_count` | raw int | Follow-spam bots have very high friends_count | No |
| `follower_friend_ratio` | `followers_count`, `friends_count` | `followers / (friends + 1)` | Key Twitter bot signal: bots follow many, are followed by few. Ratio << 1 is suspicious | No |
| `account_age_days` | `created_at` | `(now - parse(created_at)).days` | New accounts, especially mass-created, are bots. Requires RFC 2822 parser | No (wall clock only) |
| `statuses_per_day` | `statuses_count`, `created_at` | `statuses_count / max(age_days, 1)` | Implausibly high tweet rate flags automation | No (wall clock only) |
| `domain_count` | `domain_list` | `len(domain_list)` | Topical breadth; spam bots may have 0 or 1 domain | No |
| `has_tweets` | `messages` | `int(len(messages) > 0)` | Accounts with no tweet content are suspicious | No |
| `tweet_count_loaded` | `messages` | `len(messages)` | Local window count (API cap 3200); supplements statuses_count | No |

### Differentiators (high value, Twitter-specific)

| Feature Name | Source Field | Formula | Signal Rationale | Requires Timestamps |
|---|---|---|---|---|
| `rt_fraction` | `messages` | `rt_count / max(total_tweets, 1)` | High RT fraction with zero original content = pure amplification bot | No |
| `mt_fraction` | `messages` | `mt_count / max(total_tweets, 1)` | Modified tweet pattern is a weaker but real signal | No |
| `unique_rt_targets` | `messages` | `len(set(rt_mt_usernames))` | Bots retweeting a single account reveal coordination | No |
| `rt_concentration` | `messages` | `1 / max(unique_rt_targets, 1)` if `rt_count > 0` else 0 | Inverse diversity of retweet targets; high = concentrated amplification | No |
| `screen_name_digit_frac` | `screen_name` | `sum(c.isdigit() for c in name) / max(len(name), 1)` | Bot-generated names often end in random digit sequences | No |

### Anti-Features (do NOT include in Stage 1)

| Anti-Feature | Why Avoid |
|---|---|
| Profile description text | Permanently excluded after leakage audit in v1.1 |
| `verified` status | Not present in TwiBot-20 profile fields via current loader |
| Any Stage 2 or Stage 3 signal | Stage boundary discipline — no content or graph at Stage 1 |
| Zero-filling absent Reddit analogs | This is the native Twitter path; no Reddit mappings permitted |

**Implementation note:** `account_age_days` requires parsing `created_at` with `"%a %b %d %H:%M:%S +0000 %Y"` (RFC 2822). Do not reuse `botsim24_io._to_unix_seconds()`. Use `email.utils.parsedate_to_datetime` or `datetime.strptime` with the Twitter-specific format string. If `created_at` is empty or unparseable, the field is genuinely missing — do not impute; drop the record or use a missingness indicator column.

**Expected Stage 1 dimensionality:** 15 features (10 table stakes + 5 differentiators).

**Expected AUC on TwiBot-20:** 0.72–0.82. follower/friend ratio and statuses_per_day are among the strongest known signals in the Twitter bot detection literature; platform-matched training should yield substantially better Stage 1 AUC than the Reddit-trained system (which achieved 0.50–0.58 via zero-shot transfer).

---

## Stage 2a: Content Features

**Purpose:** Semantic and linguistic classifier on tweet timeline content. Activated for accounts that Stage 1 cannot classify confidently.

**Input:** `messages` list (tweet text strings). Timestamps are absent (ts=None throughout).

### Table Stakes

| Feature Name | Source Field | Formula | Signal Rationale | Requires Timestamps |
|---|---|---|---|---|
| `emb_pool` (384-dim) | `messages[].text` | MiniLM mean-pooled embedding over up to 50 tweets | Semantic content fingerprint; bot-generated text clusters in embedding space | No |
| `char_len_mean` | `messages[].text` | mean `len(text)` across tweets | Bots often use template-length messages | No |
| `char_len_std` | `messages[].text` | std `len(text)` across tweets | Low std = template repetition | No |
| `uniq_token_ratio` | `messages[].text` | mean per-tweet `len(set(tokens)) / len(tokens)` | Low lexical diversity is a bot signal | No |
| `punct_ratio` | `messages[].text` | mean punctuation chars / total chars | Bots often have abnormally high or low punctuation | No |
| `digit_ratio` | `messages[].text` | mean digit chars / total chars | High digit ratio in content (e.g., phone/promo spam) | No |
| `cross_msg_sim_mean` | `messages[].text` | mean off-diagonal cosine sim of tweet embeddings | Repeated near-duplicate messages = automation | No |
| `near_dup_frac` | `messages[].text` | fraction of tweet pairs with cosine sim > 0.9 | Explicit near-duplicate detection | No |
| `rt_frac_content` | `messages[].text` | `rt_count / max(total, 1)` | Reinforces Stage 1 signal from content perspective | No |

### Differentiators

| Feature Name | Source Field | Formula | Signal Rationale | Requires Timestamps |
|---|---|---|---|---|
| `hashtag_density` | `messages[].text` | mean `count('#') / max(len(text), 1)` per tweet | Bot content often hashtag-saturated | No |
| `mention_density` | `messages[].text` | mean `count('@') / max(len(text), 1)` per tweet | High mention density without replies = spam pattern | No |
| `url_frac` | `messages[].text` | fraction of tweets containing "http" | Pure link-sharing bots have near-100% URL fraction | No |
| `unique_domain_count` | `domain_list` | `len(domain_list)` | Already in Stage 1 but domain diversity reinforces content signals | No |
| `original_tweet_frac` | `messages[].text` | `original_count / max(total, 1)` | Accounts with zero original content are strong bot candidates | No |

### Features Requiring Timestamps — Absent in TwiBot-20 (DO NOT USE)

| Feature | Why Absent | Status |
|---|---|---|
| `cv_intervals` | Requires consecutive tweet timestamps | BLOCKED — ts=None |
| `rate` (tweets/sec) | Requires timestamp span | BLOCKED — ts=None |
| `delta_mean`, `delta_std` | Requires inter-tweet intervals | BLOCKED — ts=None |
| `hour_entropy` | Requires hour-of-day from UTC timestamps | BLOCKED — ts=None |

**Critical:** The existing `extract_stage2_features()` in `features_stage2.py` uses `_MISSING_TEMPORAL_SENTINEL = -1.0` to flag these as absent. For the Twitter-native path, these four dimensions must be dropped entirely from the feature vector — the sentinel approach was designed for zero-shot transfer compatibility with a Reddit-trained model, not for a fresh Twitter-native model. Training on sentinel values would leak the "no timestamp" missingness pattern as a spurious bot signal.

**Expected Stage 2a dimensionality:** 384 (embeddings) + 9 (content/linguistic) = 393 features. Drop the 7 temporal columns entirely.

**Expected AUC contribution:** 0.78–0.88 platform-matched. Content-based bot detection with matched training data typically achieves strong separation on Twitter.

---

## Stage 2b: AMR Delta Refiner

**Purpose:** Incremental logit correction for uncertain/novel accounts after Stage 2a.

**Input:** Most recent tweet embedding (single tweet, not pooled).

**Twitter-native status:** No change to mechanism. The AMR refiner applies to the most recent message text embedding. For TwiBot-20, this is the last entry in `messages[]`. If `messages` is empty, zero-vector input is used (same behavior as Reddit path).

**Timestamp dependency:** None. AMR refinement is embedding-only.

**Note:** The AMR refiner is a learned delta-logit updater. It trains on Stage 2a residuals. As long as tweet text is present, the mechanism transfers to Twitter natively.

---

## Stage 3: Graph / Structural Features

**Purpose:** Network structure classifier for accounts where Stage 1 + Stage 2 combined score is still uncertain or novel.

**Input:** `edges_df` built from `neighbor.following` and `neighbor.follower` lists via `twibot20_io.build_edges()`.

### Available Graph Features (from `build_graph_features_nodeidx`)

The current implementation computes 6 global + 4 per edge type features. With 2 TwiBot-20 edge types (etype=0: following, etype=1: follower), this yields 6 + 8 = 14 features. The third edge type from the Reddit path (etype=2) produces all-zeros and should be dropped in the Twitter-native path to avoid zero-padding a feature that has no Twitter analog.

| Feature | Edge Type | Formula | Signal Rationale |
|---|---|---|---|
| `in_deg` | global | count of edges pointing to node | Follower count from graph (may differ from profile snapshot) |
| `out_deg` | global | count of edges from node | Following count from graph |
| `total_deg` | global | `in_deg + out_deg` | Total network activity |
| `in_w` | global | sum of inbound edge weights | With log1p(1.0) weights, proportional to in_deg |
| `out_w` | global | sum of outbound edge weights | Proportional to out_deg |
| `total_w` | global | `in_w + out_w` | Total weighted degree |
| `in_deg_t0` | etype=0 (following edges) | in-degree from following edges | Accounts followed by this node in the subset |
| `out_deg_t0` | etype=0 | out-degree from following edges | How many this node follows |
| `in_w_t0` | etype=0 | weighted in-degree | Same signal, weighted |
| `out_w_t0` | etype=0 | weighted out-degree | Same signal, weighted |
| `in_deg_t1` | etype=1 (follower edges) | in-degree from follower edges | Accounts following this node |
| `out_deg_t1` | etype=1 | out-degree from follower edges | Same from opposite direction |
| `in_w_t1` | etype=1 | weighted in-degree | Weighted version |
| `out_w_t1` | etype=1 | weighted out-degree | Weighted version |

**Recommended dimensionality for Twitter-native Stage 3:** 14 (drop etype=2 all-zero columns).

### Twitter-Native Graph Signal Rationale

TwiBot-20 edges are follow-graph links, not content interactions. The bot signal direction is different from BotSim-24 but is well-defined:

- **Follow-spam bots:** Very high `out_deg` (following thousands), very low `in_deg` (few real followers). `in_deg / out_deg` << 1.
- **Coordinated inauthentic accounts:** Unusual clustering — bots follow each other creating dense subgraphs within the evaluation split. In-degree spikes from other bots.
- **Organic human accounts:** `in_deg` and `out_deg` are correlated and moderate; power-law degree distribution with organic variation.

The follow-graph features are **weaker** for cross-split detection (edges cross-set boundaries are silently dropped in `build_edges`) but are **valid** for same-split supervised training.

### Anti-Features for Stage 3

| Anti-Feature | Why Avoid |
|---|---|
| Edge weight variation | All TwiBot-20 edges have weight=log1p(1.0) — weight features are redundant with degree features. Consider dropping weight columns or using degree-only. |
| etype=2 columns | No third edge type exists in TwiBot-20; training on all-zero columns wastes capacity and may cause LightGBM to waste splits |
| Graph features from cross-split neighbors | `build_edges()` already drops cross-set IDs; no action needed |

---

## Feature Dependency Map

```
Stage 1 (metadata only)
  statuses_count          <-- profile.statuses_count
  followers_count         <-- profile.followers_count
  friends_count           <-- profile.friends_count
  follower_friend_ratio   <-- followers / (friends + 1)
  screen_name_len         <-- len(profile.screen_name)
  screen_name_digit_frac  <-- profile.screen_name
  account_age_days        <-- parse(profile.created_at)   [RFC 2822 parser required]
  statuses_per_day        <-- statuses_count / account_age_days
  domain_count            <-- len(domain_list)
  has_tweets              <-- len(messages) > 0
  tweet_count_loaded      <-- len(messages)
  rt_fraction             <-- parse_tweet_types(messages).rt_count
  mt_fraction             <-- parse_tweet_types(messages).mt_count
  original_tweet_frac     <-- parse_tweet_types(messages).original_count
  unique_rt_targets       <-- len(parse_tweet_types(messages).rt_mt_usernames)
  rt_concentration        <-- derived from unique_rt_targets, rt_count

Stage 2a (tweet content, no timestamps)
  emb_pool (384)          <-- MiniLM.encode(messages[].text)
  char_len_mean/std       <-- len(msg.text)
  uniq_token_ratio        <-- token-level computation per tweet
  punct_ratio             <-- character-level per tweet
  digit_ratio             <-- character-level per tweet
  cross_msg_sim_mean      <-- embedding dot products (requires >= 2 tweets)
  near_dup_frac           <-- cosine sim > 0.9 threshold (requires >= 2 tweets)
  rt_frac_content         <-- parse_tweet_types already done in Stage 1 path
  hashtag_density         <-- count('#') per tweet
  mention_density         <-- count('@') per tweet
  url_frac                <-- 'http' in text per tweet
  original_tweet_frac     <-- (shared with Stage 1 computation)

  BLOCKED (absent timestamps):
    cv_intervals, rate, delta_mean, delta_std, hour_entropy

Stage 2b (AMR)
  last_tweet_embedding    <-- MiniLM.encode([messages[-1].text]) or zeros

Stage 3 (graph)
  14 degree/weight features <-- edges_df from build_edges(accounts_df, path)
  [drop etype=2 columns]
```

---

## MVP Feature Set Recommendation

For the v1.4 paper comparison, prioritize:

**Stage 1 MVP (15 features):**
1. `screen_name_len` — fast, no parsing
2. `statuses_count` — direct field
3. `followers_count` — direct field
4. `friends_count` — direct field
5. `follower_friend_ratio` — strongest Twitter bot signal
6. `account_age_days` — requires RFC 2822 parser; high value
7. `statuses_per_day` — derived from above two; automation rate
8. `domain_count` — direct field
9. `has_tweets` — binary flag
10. `tweet_count_loaded` — local window size
11. `rt_fraction` — requires `parse_tweet_types()`; already implemented
12. `original_tweet_frac` — derived from parse_tweet_types
13. `unique_rt_targets` — derived from parse_tweet_types
14. `rt_concentration` — derived
15. `screen_name_digit_frac` — character-level, no parsing

**Stage 2a MVP (393 features):**
- 384-dim MiniLM embedding pool
- char_len_mean, char_len_std (2)
- cross_msg_sim_mean, near_dup_frac (2)
- uniq_token_ratio, hashtag_density, mention_density, url_frac, original_tweet_frac (5)
- Drop all 7 temporal features entirely (no sentinel — fresh training)

**Stage 3 MVP (14 features):**
- global: in_deg, out_deg, total_deg, in_w, out_w, total_w (6)
- etype=0: in_deg_t0, out_deg_t0, in_w_t0, out_w_t0 (4)
- etype=1: in_deg_t1, out_deg_t1, in_w_t1, out_w_t1 (4)
- Drop etype=2 columns

**Defer:**
- `verified` status: not in current loader
- Per-tweet-level RNN/LSTM sequence features: complexity out of scope for v1.4
- URL domain diversity (requires URL parsing): moderate complexity, moderate value

---

## Missing Field Flag Table

| Field | Stage | Present in TwiBot-20 | Handling |
|---|---|---|---|
| Tweet timestamps | S2a temporal | NO (ts=None) | Drop temporal features entirely in native path |
| Profile description | S1 | NOT LOADED (leakage exclusion) | Excluded project-wide |
| Per-tweet engagement (likes, RTs, replies) | S1/S2a | NO | Not present in TwiBot-20 loader |
| Verified badge | S1 | NO | Not present in current loader |
| User language field | S1 | NO | Not in profile fields loaded |
| Geo/location | S1 | NO | Not in profile fields loaded |
| Edge type 2 | S3 | NO | Drop etype=2 columns from feature vector |
| Edge weights (varied) | S3 | UNIFORM only | Weight features degenerate; degree features carry the signal |

---

## Sources

- `twibot20_io.py` — field names, loader schema, `parse_tweet_types()` implementation (code-verified 2026-04-18)
- `features_stage1.py` — Reddit Stage 1 feature vector (10-dim reference baseline)
- `features_stage2.py` — Reddit Stage 2a feature vector (397-dim reference baseline)
- `botdetector_pipeline.py` — `build_graph_features_nodeidx()` Stage 3 implementation
- `.planning/research/FEATURES.md` (prior version, 2026-04-16) — zero-shot transfer analysis, Reddit-to-Twitter mapping document
- `.planning/PROJECT.md` — v1.4 constraints: no imputing, no zero-fill, no Reddit field analogs
