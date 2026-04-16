# Feature Mapping: TwiBot-20 → BotSim-24 Feature Vector

**Project:** SocialBotDetectionSystem v1.2 — TwiBot-20 Cross-Dataset Evaluation
**Research date:** 2026-04-16
**Confidence:** HIGH (code-verified against actual extractors) | MEDIUM for TwiBot-20 schema (Twitter API v1.1 docs)

---

## Feature Space Overview

The cascade uses 3 independent feature spaces across stages:

| Stage | Dims | Source |
|-------|------|--------|
| Stage 1 | 10 | Users.csv numeric fields |
| Stage 2a | 397 | MiniLM (384) + linguistic (4) + temporal (7) + cross-msg (2) |
| Stage 3 | 18 | PyTorch edge tensors (6 global + 4×3 per-type) |

---

## Stage 1 Feature Mapping (10-dim)

| Index | Feature | BotSim-24 Source | TwiBot-20 Mapping | Category |
|-------|---------|-----------------|-------------------|----------|
| 0 | name_len | len(username) | `len(user.screen_name)` | **Direct** |
| 1 | post_num | submission count | `user.statuses_count` | **Approximation** (lifetime vs window) |
| 2 | comment_num_1 | comment type 1 count | No equivalent | **Zero-fill** |
| 3 | comment_num_2 | comment type 2 count | No equivalent | **Zero-fill** |
| 4 | c_total | total comments | No equivalent | **Zero-fill** |
| 5 | sr_num | subreddit count | No equivalent | **Zero-fill** |
| 6 | post_c1 | post_num / comment_num_1 | Degenerate: div by zero | **Clamp to [0, 50]** |
| 7 | post_c2 | post_num / comment_num_2 | Degenerate: div by zero | **Clamp to [0, 50]** |
| 8 | post_ct | post_num / c_total | Degenerate: div by zero | **Clamp to [0, 50]** |
| 9 | post_sr | post_num / sr_num | Degenerate: div by zero | **Clamp to [0, 50]** |

**CRITICAL:** Without clamping indices 6–9, every TwiBot-20 account gets astronomical Mahalanobis novelty scores, routing 100% to Stage 3 regardless of confidence. Clamping must happen in the TwiBot-20 inference path only — not inside `extract_stage1_matrix()` — to preserve BotSim-24 behavior.

**Effective Stage 1 signal on TwiBot-20: 2 of 10 features.** Expected AUC: 0.50–0.58.

---

## Stage 2a Feature Mapping (397-dim)

### Subgroup A: MiniLM Embeddings (indices 0–383, 384-dim)
**Category: Approximation (MEDIUM-HIGH)**
MiniLM embedding space is platform-agnostic. Twitter text is shorter, RT-heavy, @/# dense. Semantic separation between templated bot content and organic human text partially transfers. Most TwiBot-20 accounts will show elevated Stage 2a novelty, triggering AMR refinement broadly — expected OOD behavior.

### Subgroup B: Linguistic Aggregates (indices 384–387, 4-dim)
**Category: Direct (HIGH)**
`length`, `uniq_ratio`, `punct_ratio`, `digit_ratio` — computed from raw text. No platform-specific fields. Twitter @mentions and #hashtags shift distributions but the bot signal direction (lower diversity, more repetition) holds cross-platform.

### Subgroup C: Temporal Features (indices 388–394, 7-dim)
**Category: Direct — HARD BLOCKER on timestamp format**
- `rate`, `delta_mean`, `delta_std`, `cv_intervals`, `char_len_mean`, `char_len_std`, `hour_entropy`
- **BLOCKER:** `botsim24_io._to_unix_seconds()` hardcodes `"%Y-%m-%d %H:%M:%S"`. Twitter `created_at` is RFC 2822: `"Thu Apr 06 15:28:43 +0000 2017"`. Silent `except Exception: return None` zeros every timestamp → all 7 features = 0 for all accounts.
- **Fix:** `_parse_twitter_timestamp(s)` using `email.utils.parsedate_to_datetime`. Never reuse `_to_unix_seconds` for TwiBot-20.
- Conditional on tweet timeline ≥ 2 tweets for delta features.

### Subgroup D: Cross-Message Similarity (indices 395–396, 2-dim)
**Category: Direct — conditional on timeline (HIGH if multiple tweets)**
`cross_msg_sim_mean`, `near_dup_frac` — requires ≥ 2 tweets. Defaults to 0 otherwise.

---

## Stage 2b: AMR Delta Refiner
**Category: Approximation (MEDIUM)**
Uses MiniLM embedding of most recent message text as anchor. TwiBot-20 mapping: most recent tweet `full_text`, or `user.tweet.full_text` if single tweet only, or zero vector if no tweet data. Delta correction less calibrated for Twitter text but mechanism is valid.

---

## Stage 3 Feature Mapping (18-dim)

BotSim-24: 3 edge types (interaction-based), weights 1–835 (counts), 46,518 edges over 2,907 nodes.
TwiBot-20: 2 edge types (follow/follower), binary weights, ~229,580 nodes.

| Feature Group | BotSim-24 | TwiBot-20 | Category |
|---------------|-----------|-----------|----------|
| in_deg, out_deg (global) | interaction graph | "following"/"followers" mapped to etype 0/1 | **Approximation (LOW)** |
| in_w, out_w (global) | weighted interaction | weight=1.0 all edges | **Degenerate** (weighted = unweighted) |
| per-type 0 degrees×4 | edge type 0 | "following" edges | **Approximation (LOW)** |
| per-type 1 degrees×4 | edge type 1 | "followers" edges | **Approximation (LOW)** |
| per-type 2 degrees×4 | edge type 2 | **Missing** — no TwiBot-20 equivalent | **Zero** |

**Semantic mismatch:** BotSim-24 edges = content interaction (reply/comment). TwiBot-20 edges = social follow links. Bot signature fundamentally differs:
- BotSim-24 bots: dense interaction with target content → detectable via in-degree structure
- TwiBot-20 bots: follow-spam → high out-degree (following many), low in-degree (few followers)

**Consider reporting cascade both with and without Stage 3 for TwiBot-20.** If Stage 3 hurts AUC, that is a paper-worthy finding about structural feature transferability limits.

---

## Complete Missing-Feature Summary

| Feature | Stage | Status | Handling | Impact |
|---------|-------|--------|----------|--------|
| comment_num_1/2 | S1 | No equivalent | Zero-fill | Moderate |
| sr_num | S1 | No equivalent | Zero-fill | High — community diversity absent |
| Ratio features ×4 | S1 | Degenerate (div-by-0) | Clamp to [0, 50] | **CRITICAL** — routing collapses without |
| Timestamp format | S2 temporal | Format mismatch | Twitter-specific parser | **BLOCKER** |
| Tweet timeline | S2 temporal/sim | Conditional | tweet.json if present; else zero | High if absent |
| Edge type 2 | S3 | Not present in TwiBot-20 | Zero naturally | Moderate |
| Edge weights | S3 | Binary only | weight=1.0 | Moderate |

---

## Zero-Shot Performance Expectations

| Component | Expected AUC on TwiBot-20 | Reason |
|-----------|--------------------------|--------|
| Stage 1 | 0.50–0.58 | 8/10 features zero or degenerate |
| Stage 2a | 0.65–0.75 | Embedding transfer + domain shift |
| Stage 3 | 0.55–0.65 | Follow-graph vs. interaction-graph mismatch |
| Overall cascade | 0.65–0.80 | Dominated by Stage 2a |

Literature: cross-dataset zero-shot bot detection typically shows 10–25 AUC point drops. 0.65–0.80 overall AUC quantifies the Reddit-to-Twitter domain gap and is a publishable result.

---

## Actionable Loader Requirements

1. `_parse_twitter_timestamp(s)` using `"%a %b %d %H:%M:%S +0000 %Y"` — separate from `botsim24_io._to_unix_seconds()`
2. Map `user.screen_name` → `username`, `user.statuses_count` → `submission_num`
3. Set `comment_num_1=0.0`, `comment_num_2=0.0`, `subreddit_list=[]`
4. Extract tweet timeline from `tweet.json` if present; fall back to single `user.tweet`; fall back to `messages=[]`
5. After `extract_stage1_matrix()`, clamp columns 6–9 to `[0.0, 50.0]` in TwiBot-20 inference path only
6. Build contiguous `node_idx` from label.csv user IDs; map edge.csv "following"→0, "followers"→1, weight=1.0
7. Report mean n1/n2/n3 novelty scores and escalation rates in paper table
