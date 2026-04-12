# Feature Landscape: Stage 2 Leakage-Free Content Features

**Domain:** Social bot detection — Reddit (BotSim-24), content/behavioral feature design
**Researched:** 2026-04-12
**Milestone:** v1.1 Feature Leakage Audit & Fix

---

## The Leakage Problem (Context for Every Decision Below)

The current `extract_stage2_features()` appends two strings to the embedding pool:

- `"USERNAME: <username>"`
- `"PROFILE: <profile_description>"`

These are mean-pooled together with message-text embeddings before being fed to Stage 2a. The AMR delta refiner (`extract_amr_embeddings_for_accounts`) also embeds `text_field="profile"` directly.

In BotSim-24, bot profile descriptions may be AI-generated or follow templates while human descriptions are organic. A sentence-transformer embedding of profile text is therefore trivially separable. The result is near-perfect Stage 2a AUC (97–100%), which is not a real signal.

**Rule:** Any replacement feature must be derivable solely from the account's behavioral trace (post/comment text and timestamps) without encoding identity strings or text fields the dataset-generation process filled differently for bots vs. humans.

---

## Table Stakes

Features expected in a Stage 2 content/behavioral classifier.

| Feature Group | Why Expected | Complexity | Notes |
|--------------|--------------|------------|-------|
| Message-text embeddings (content only) | Core semantic representation of what the account posts | Low — already done | Remove username/profile from encoding pool; embed message texts only |
| Lexical diversity (type/token ratio) | Bots reuse vocabulary; low diversity is a known signal | Low — word-count arithmetic | Already partially implemented (uniq_ratio); enrichable |
| Repetition rate across messages | Bots often post near-identical content; copy-paste spam | Medium — pairwise similarity | Cross-message similarity not currently implemented |
| Temporal rhythm features | Bot posting patterns cluster at machine-like cadences | Low — already partially done | rate/delta_mean/delta_std exist; add coefficient of variation |
| Message length distribution | Bots often use uniform or extremely short/long messages | Low — per-account stats | Mean, std of message character counts not currently computed |
| Punctuation and capitalization patterns | Templated bot text has distinctive surface patterns | Low — character-level counts | Partly implemented; expand to ALL-CAPS ratio, exclamation density |

## Differentiators

| Feature Group | Value Proposition | Complexity | Notes |
|--------------|-------------------|------------|-------|
| Cross-message cosine similarity (mean pairwise) | Directly measures copy-paste/template reuse across posts | Medium | Embed each message, compute mean pairwise cosine; high = low diversity |
| Coefficient of variation of inter-post intervals | Machine regularity: bots have low CV (uniform timing), humans are bursty | Low — one arithmetic step | CV = delta_std / max(delta_mean, 1e-9) |
| Entropy of posting hour-of-day distribution | Bots post round-the-clock uniformly; humans cluster in waking hours | Low — histogram over hour bins | Requires Unix ts → hour conversion; no additional data needed |
| Fraction of posts that are near-duplicates (sim > 0.9) | Hard threshold duplicate rate; more interpretable than mean similarity | Medium — shares pass with cross-message similarity | Computable in same pass as cross-message similarity |
| Aggregate type/token ratio | Normalized vocabulary richness across all messages concatenated | Low | More stable than per-message uniq_ratio for short messages |

## Anti-Features

Features to explicitly NOT include in the leakage-free Stage 2.

| Anti-Feature | Why Avoid | What to Do Instead |
|-------------|-----------|-------------------|
| Username text embedding | Username in BotSim-24 encodes bot identity directly | Drop from texts list; username length is already in Stage 1 as numeric |
| Profile/description text embedding | Root cause of current leakage; bot profiles are AI-generated | Drop from texts list entirely |
| Profile text as AMR input | Amplifies the same leakage through the AMR refiner | Replace with representative message text (longest or most recent post) |
| Any Users.csv field varying by dataset construction | Trivially discriminative by label assignment process | Audit all columns; only use fields that exist for real Reddit accounts |

## Feature Dependencies

```
Message texts (from user_post_comment.json messages[].text)
  --> message-text-only embeddings (mean pool)          [KEEP, strip username/profile]
  --> per-message linguistic features (aggregate)       [KEEP, already implemented]
  --> cross-message cosine similarity                   [ADD, requires per-message embeddings]
  --> near-duplicate fraction                           [ADD, derived from cross-message similarity]
  --> message length distribution stats                 [ADD, low complexity]
  --> aggregate type/token ratio                        [ADD, low complexity]

Timestamps (from user_post_comment.json messages[].ts)
  --> posting rate, delta_mean, delta_std               [KEEP, already implemented]
  --> coefficient of variation of inter-post deltas     [ADD, one arithmetic step]
  --> entropy of hour-of-day distribution               [ADD, requires ts -> hour conversion]
```

Cross-message similarity and near-duplicate fraction share a single embedding pass — compute together.

## MVP Recommendation

**Phase 1 — remove leaky inputs (immediate fix):**
1. Strip `username` and `profile` from the `texts` list in `extract_stage2_features`
2. Remove `text_field="profile"` from AMR extractor; replace with representative message text
3. Add CV of inter-post deltas (one arithmetic line over existing `ts` array)
4. Add mean and std of message character lengths (no new data source)
5. Add posting hour-of-day entropy using existing `ts` values

**Phase 2 — add cross-message similarity (differentiator):**
6. Compute mean pairwise cosine similarity and near-duplicate fraction after per-message encoding; append as two scalar features

## Expected Outcome

AUC expected to drop from 97–100% to realistic 70–85% range typical for content-only Stage 2 classifiers. This is not a failure — it is the correct result. Near-perfect Stage 2a with profile text means the stage was detecting data-generation artifacts, not bot behavior.
