# Technology Stack: v1.4 Twitter-Native Supervised Cascade on TwiBot-20

**Project:** Social Bot Detection System — v1.4 Twitter-Native Supervised Baseline
**Researched:** 2026-04-18
**Confidence:** HIGH — derived from direct inspection of all production modules and the existing
installed package set documented in v1.2 research.

---

## Executive Summary

**Zero new pip dependencies are required.** Every capability needed for supervised training
on TwiBot-20 is already present in the installed environment. The work is entirely new
Python modules and revised feature-extraction logic, not new packages.

The critical distinction from v1.2 is purpose: v1.2 loaded a trained Reddit model and ran
zero-shot inference. v1.4 trains a new cascade from scratch using TwiBot-20 as the training
platform. This changes which feature columns exist and how `train_system()` is called, but
not what libraries are used.

---

## Installed Stack (unchanged — no additions needed)

These are the confirmed installed versions from v1.2 research. All v1.4 work stays within
this set.

| Package | Version | Role in v1.4 |
|---------|---------|--------------|
| `lightgbm` | 4.x (installed) | Stage 1, 2a, 3 base classifiers — no change |
| `scikit-learn` | 1.6.1 | LedoitWolf novelty, LogisticRegression meta-learners, CalibratedClassifierCV, StratifiedKFold OOF — no change |
| `sentence-transformers` | 5.2.3 | Tweet text embeddings in Stage 2a — reused as-is |
| `torch` | 2.10.0+cpu | Stage 2b LSTM refiner (optional path) — no change |
| `numpy` | 2.1.3 | Feature matrix assembly, graph degree arrays — no change |
| `pandas` | 2.2.3 | Account DataFrames, split construction — no change |
| `joblib` | 1.4.2 | Saving the new `trained_system_twibot.joblib` artifact — no change |
| `scikit-optimize` | (installed) | Bayesian threshold calibration — no change |
| `json` | stdlib | TwiBot-20 JSON loading (already in `twibot20_io.py`) |
| `email.utils` | stdlib | Twitter RFC 2822 `created_at` parsing for account age feature |
| `datetime` | stdlib | Account age calculation from parsed `created_at` |

---

## What Reuses the Existing Stack Without Modification

### Stage 2a content/temporal features — full reuse

`features_stage2.py::extract_stage2_features()` already handles Twitter tweet text correctly:

- Takes `df["messages"]` as `list[{"text": str, "ts": Optional[float], "kind": str}]`
- `twibot20_io.load_accounts()` already produces exactly this schema with `"ts": None`
- The sentinel path (`_MISSING_TEMPORAL_SENTINEL = -1.0`) already fires when messages exist
  but all timestamps are None — which is the exact TwiBot-20 condition
- `sentence-transformers` with `all-MiniLM-L6-v2` encodes Twitter tweet text identically to
  Reddit post text — the model is domain-agnostic by design
- Cross-message cosine similarity, near-duplicate fraction, char length stats, linguistic
  features all work on tweet text without modification

**No changes to `features_stage2.py`.**

### Stage 3 graph features — full reuse

`botdetector_pipeline.py::build_graph_features_nodeidx()` takes `(accounts_df, edges_df, num_nodes)`.
`twibot20_io.build_edges()` already produces the correct `src/dst/etype/weight` DataFrame
from TwiBot-20 neighbor lists. The degree aggregation uses `np.add.at` — no graph library,
no NetworkX, nothing new.

**No changes to `botdetector_pipeline.py::build_graph_features_nodeidx()`.**

### Meta-learners and OOF stacking — full reuse

`train_meta12()`, `train_meta123()`, `oof_meta12_predictions()`, `build_meta12_table()`,
`gate_amr()`, `gate_stage3()` all operate on numpy arrays and pandas DataFrames with no
platform-specific logic. They compose on top of whatever stage outputs they receive.

**No changes to meta-learner or routing functions.**

### Novelty scoring — full reuse

`MahalanobisNovelty` uses LedoitWolf shrinkage — calibrates to whatever training
distribution it is fit on. When trained on TwiBot-20 metadata, it will produce
Twitter-native novelty scores without modification.

**No changes to `MahalanobisNovelty`.**

---

## What Needs New Code (No New Libraries)

### 1. Twitter-native Stage 1 feature extractor — new function, same libraries

**Why new code:** `features_stage1.py::extract_stage1_matrix()` reads Reddit columns
(`submission_num`, `comment_num_1`, `comment_num_2`, `subreddit_list`, `username`).
TwiBot-20 has different native fields. The v1.2 adapter zero-filled missing fields and
clamped ratios — a workaround. v1.4 must use real Twitter fields directly.

**New function:** `extract_stage1_twibot(df)` using only columns present in TwiBot-20:

| Feature | Source column | Rationale |
|---------|--------------|-----------|
| `screen_name_len` | `screen_name` | Username length — bot names often numeric/random |
| `statuses_count` | `statuses_count` | Total tweet volume |
| `followers_count` | `followers_count` | Audience size |
| `friends_count` | `friends_count` | Following count |
| `followers_friends_ratio` | computed | Classic bot signal: bots follow many, few follow back |
| `statuses_per_follower` | computed | Activity rate relative to audience |
| `friends_to_followers_ratio` | computed | Inverse of above — high = aggressive following |
| `account_age_days` | `created_at` (RFC 2822) | Newer accounts skew bot; parsed via `email.utils` |
| `statuses_per_day` | computed | Activity rate over account lifetime |
| `domain_count` | `domain_list` | Topical breadth — direct TwiBot-20 field |

Implementation: pure numpy/pandas. `email.utils.parsedate_to_datetime` for `created_at`
(already verified working in v1.2 research).

**File:** New `features_stage1_twibot.py` or added function in `features_stage1.py`.
Using a separate file is preferred — it keeps the Reddit model's `extract_stage1_matrix`
untouched and removes any risk of breaking the existing `trained_system_v12.joblib` path.

### 2. TwiBot-20 train/val split construction — new utility, same libraries

**Why new code:** `train_system()` expects pre-split `S1` and `S2` DataFrames with
associated edge DataFrames. TwiBot-20 provides canonical `train.json`/`val.json`/`test.json`
splits. The natural mapping is:

- `S1` = first 60% of `train.json` (stage models trained here)
- `S2` = remaining 40% of `train.json` (meta-learner OOF trained here)
- `S3` = `test.json` (evaluation only)
- `val.json` = optional early-stopping or threshold tuning

The graph edge filtering must respect these splits: only edges where both endpoints are in
the same split contribute (existing `build_edges` drops cross-set IDs already, but split
filtering requires passing the right subset of accounts to `build_edges`).

**File:** New utility in the training script or `twibot20_io.py`. Uses pandas `.iloc` and
`twibot20_io.build_edges()` — no new libraries.

### 3. Supervised training entry point — new script, same libraries

A new `train_twibot.py` (or equivalent) that:

1. Loads `train.json` → accounts + edges
2. Splits into S1/S2 with graph-filtered edges per split
3. Calls `train_system(S1, S2, edges_S1, edges_S2, cfg, th, nodes_total=N)`
4. Saves result as `trained_system_twibot.joblib` (distinct from `trained_system_v12.joblib`)
5. Runs evaluation on `test.json` via a TwiBot-native `predict_system` call
6. Writes F1/AUC metrics to `metrics_twibot_native.json`

The `FeatureConfig.stage1_numeric_cols` parameter needs to point to the Twitter-native
column names. The rest of `train_system()` passes through `extract_stage1_matrix` via a
reference — override it by passing a custom extractor or by monkey-patching
`bp.extract_stage1_matrix` identically to how `evaluate_twibot20.py` already does.

**Recommended approach:** Pass the extractor explicitly rather than monkey-patching.
`train_system()` currently calls `extract_stage1_matrix` directly (imported at module level).
The cleanest solution is to add an `extractor_stage1` parameter to `train_system()` with
the Reddit extractor as default — this is backward compatible and avoids monkey-patching
in training code.

---

## What NOT to Add

| Package | Reason to exclude |
|---------|-------------------|
| `networkx` | Already installed but not needed — numpy `add.at` handles all degree aggregation |
| `tweepy` | No live Twitter API calls; TwiBot-20 is a static JSON dump |
| `python-igraph` / `graph-tool` | Overkill — no graph traversal, only degree counts |
| `transformers` (bare HuggingFace) | sentence-transformers already wraps it |
| `tqdm` | Not needed for a one-time training run |
| `orjson` | stdlib `json` is sufficient for static file loading |
| `pyarrow` | CSV/JSON loading already covered by pandas and json stdlib |
| `huggingface_hub` | sentence-transformers manages model downloads internally |
| Twitter-specific NLP libraries (`twokenize`, `ekphrasis`) | tweet text goes directly into `all-MiniLM-L6-v2`; Twitter-specific tokenization adds complexity with no validated benefit |
| `dgl` / `torch_geometric` | Graph neural networks are out of scope; Stage 3 uses hand-crafted degree features |

---

## sentence-transformers for Twitter Tweet Text — Verification

**Question:** Does `all-MiniLM-L6-v2` (the existing embedder) work well enough for Twitter
tweet text, which is shorter and noisier than Reddit posts?

**Assessment (MEDIUM confidence — reasoning from known properties, not benchmark):**

- `all-MiniLM-L6-v2` is a general-purpose sentence encoder trained on a diverse corpus
  including short texts. It is not Twitter-specific but is not Reddit-specific either.
- TwiBot-20 tweet text is plain UTF-8 strings stored as raw tweet text (no JSON metadata).
  The existing `twibot20_io.load_accounts` already extracts these correctly into the
  `messages` list.
- The cross-message cosine similarity features in `features_stage2.py` (near-duplicate
  fraction, mean cosine) are specifically valuable for detecting bot behaviour on Twitter
  (copy-paste tweet storms), so the feature design is well-matched.
- Twitter-specific models (BERTweet, TimeLMs-Twitter) would give marginally better semantic
  representations for tasks like sentiment or NER, but for bot detection the relevant signal
  is behavioural repetition, not semantic nuance. The existing embedder captures that.

**Decision:** Keep `all-MiniLM-L6-v2`. Switching models would require retraining both the
Reddit and TwiBot cascades and break the paper comparison. The value of platform-matched
training comes from training labels, not from changing the embedder.

---

## TwiBot-20 Data Format Confirmation

From `twibot20_io.py` direct inspection:

- Format: single JSON array per split file (`train.json`, `val.json`, `test.json`)
- Each record: `{"ID": str, "profile": {...}, "tweet": [str, ...], "neighbor": {"following": [...], "follower": [...]}, "domain": [...], "label": 0|1}`
- `tweet` field: list of raw tweet text strings (no timestamp, no metadata)
- `neighbor` field: dict of Twitter ID string lists; may be `null`
- `profile` fields available: `screen_name`, `statuses_count`, `followers_count`, `friends_count`, `created_at`, and others

**Consequence for timestamps:** All temporal features in Stage 2a will use the sentinel
path (`_MISSING_TEMPORAL_SENTINEL = -1.0`) because tweet timestamps are absent from
TwiBot-20. This is a known data limitation, not a code problem. The sentinel is already
handled correctly in `features_stage2.py`.

---

## Integration Points Summary

```
train.json
  └─ twibot20_io.load_accounts()        → accounts_df (with statuses_count, followers_count, etc.)
  └─ twibot20_io.build_edges()          → edges_df (src, dst, etype, weight)

features_stage1_twibot.extract_stage1_twibot(accounts_df)
  → X1: [screen_name_len, statuses_count, followers_count, friends_count,
          followers_friends_ratio, statuses_per_follower, friends_to_followers_ratio,
          account_age_days, statuses_per_day, domain_count]   shape: (N, 10)

features_stage2.extract_stage2_features(accounts_df, embedder)
  → X2: [emb_pool (384), ling (4), temporal (7), sim (2)]   shape: (N, 397)
  (temporal dims use sentinel -1.0; this is correct behavior for TwiBot-20)

botdetector_pipeline.build_graph_features_nodeidx(accounts_df, edges_df, N)
  → X3: [in_deg, out_deg, total_deg, in_w, out_w, total_w, + per-etype (12)]   shape: (N, 18)

botdetector_pipeline.train_system(S1, S2, edges_S1, edges_S2, cfg, th, ...)
  → TrainedSystem  →  saved as trained_system_twibot.joblib
```

---

## Sources

- `twibot20_io.py`: direct inspection — field extraction, neighbor parsing, message schema
- `features_stage1.py`: direct inspection — existing Reddit feature dimensions
- `features_stage2.py`: direct inspection — sentinel path, tweet text handling, embedding pipeline
- `botdetector_pipeline.py`: direct inspection — `build_graph_features_nodeidx`, `train_system`, `TrainedSystem`, `predict_system`
- `evaluate_twibot20.py`: direct inspection — monkey-patch pattern, v1.2 adapter approach
- `.planning/research/STACK.md` (v1.2): confirmed installed package versions and stdlib verification
- `PROJECT.md`: v1.4 scope definition, out-of-scope constraints
