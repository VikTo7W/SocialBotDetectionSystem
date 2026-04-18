# Architecture: Twitter-Native TwiBot-20 Cascade (v1.4)

**Domain:** Supervised cascade training on TwiBot-20 — Twitter-native feature extraction and a second TrainedSystem artifact
**Researched:** 2026-04-18
**Milestone:** v1.4 Twitter-Native Supervised Baseline
**Supersedes:** v1.2 ARCHITECTURE.md (zero-shot Reddit cascade on TwiBot-20)
**Confidence:** HIGH (all integration points verified against live codebase)

---

## Context: What Changed from v1.2 to v1.4

v1.2 architecture solved: "how do we run the Reddit-trained cascade on TwiBot-20 zero-shot?"
Answer: monkey-patch `extract_stage1_matrix` to clamp ratios; tolerate missingness in Stage 2 timestamps.

v1.4 architecture solves: "how do we train a *new* cascade natively on TwiBot-20 with no Reddit
mappings, no imputing, and no zero-fill — and keep the Reddit cascade completely untouched?"

The architectural implication is a second *training path*, not just a second evaluation path.

---

## The Integration Contract (Unchanged Core)

`TrainedSystem` is the universal container. Any cascade — Reddit-trained or TwiBot-trained — is a
`TrainedSystem` object. `predict_system()` and `evaluate_s3()` accept any `TrainedSystem` paired
with a compatible DataFrame. The challenge is producing that compatible DataFrame using only
Twitter-native fields — not re-using the Reddit column schema.

The key insight: `train_system()` in `botdetector_pipeline.py` takes:

```
S1: pd.DataFrame  —  stage model training split
S2: pd.DataFrame  —  meta-learner training split (OOF stacking)
edges_S1, edges_S2: pd.DataFrame  —  intra-split edge subsets
cfg: FeatureConfig
th: StageThresholds
```

It calls `extract_stage1_matrix(S1)`, `extract_stage2_features(S1, embedder)`, and
`build_graph_features_nodeidx(S1, edges_S1, nodes_total)` internally. If those three feature
functions accept TwiBot-20 DataFrames and return the same array shapes as before, `train_system()`
runs unchanged.

Therefore: the architecture for v1.4 is entirely about building three Twitter-native feature
extractors and a new training entry point. Every inference and evaluation component is reused as-is.

---

## Component Map: New vs Reused vs Modified

### New Components (must be built)

| Component | File | Purpose |
|-----------|------|---------|
| Twitter-native Stage 1 extractor | `features_stage1_twitter.py` | Replaces Reddit column schema with Twitter-native account metadata |
| Twitter-native Stage 2 extractor | `features_stage2_twitter.py` | Tweet timelines without Reddit temporal assumptions; no timestamp sentinel fallback |
| Twitter-native Stage 3 extractor | No new file needed — see graph section below | Graph features are already format-agnostic via `build_graph_features_nodeidx` |
| TwiBot-20 training entry point | `train_twibot20.py` | Drives train/val/test split of TwiBot-20 train.json, trains cascade, saves artifact |
| TwiBot-20 native evaluation | `evaluate_twibot20_native.py` | Runs the TwiBot-native `TrainedSystem` on TwiBot-20 test.json |

### Reused Without Modification

| Component | File | Why Reusable |
|-----------|------|-------------|
| `train_system()` | `botdetector_pipeline.py` | Accepts any DataFrames + feature arrays; platform-agnostic after features are extracted |
| `predict_system()` | `botdetector_pipeline.py` | Same as above — only reads `TrainedSystem` fields and calls feature extractors |
| `TrainedSystem` dataclass | `botdetector_pipeline.py` | Universal cascade container; no platform-specific fields |
| `StageThresholds` | `botdetector_pipeline.py` | Threshold values have no platform semantics |
| `MahalanobisNovelty` | `botdetector_pipeline.py` | Fit on Twitter-native features; same math |
| `Stage1MetadataModel`, `Stage2BaseContentModel`, `Stage3StructuralModel` | `botdetector_pipeline.py` | Same LightGBM + CalibratedClassifierCV pattern; platform-agnostic |
| `AMRDeltaRefiner`, `Stage2LSTMRefiner` | `botdetector_pipeline.py` | Take embedding arrays — platform-agnostic |
| `gate_amr()`, `gate_stage3()` | `botdetector_pipeline.py` | Operate on probability/novelty scores — platform-agnostic |
| `oof_meta12_predictions()` | `botdetector_pipeline.py` | Pure numpy — platform-agnostic |
| `build_graph_features_nodeidx()` | `botdetector_pipeline.py` | Takes `{src, dst, etype, weight}` DataFrame — already platform-agnostic |
| `evaluate_s3()` | `evaluate.py` | Operates on `predict_system()` output — platform-agnostic |
| `calibrate_thresholds()` | `calibrate.py` | Operates on `TrainedSystem` + S2 DataFrame — platform-agnostic |
| `twibot20_io.load_accounts()` | `twibot20_io.py` | Already loads TwiBot-20 JSON; returns `messages` list |
| `twibot20_io.build_edges()` | `twibot20_io.py` | Already builds `{src, dst, etype, weight}` edge DataFrame |
| `twibot20_io.parse_tweet_types()` | `twibot20_io.py` | RT/MT/original classification; will be used in native Stage 1 |
| `TextEmbedder` | `botdetector_pipeline.py` | Wraps sentence-transformers — text-input, platform-agnostic |

### Modified

| Component | File | Change |
|-----------|------|--------|
| `main.py` | `main.py` | Remove online novelty recalibration path (v1.4 requirement); Reddit cascade training unchanged |
| `ablation_tables.py` | `ablation_tables.py` | Add a comparison table function: Reddit-trained-on-TwiBot (F1=0.0) vs TwiBot-trained-on-TwiBot |

### Must NOT Be Touched

| Component | Constraint |
|-----------|-----------|
| `trained_system_v12.joblib` | Immutable artifact — the Reddit-trained cascade |
| `features_stage1.py` | Reddit-native extractor; do not add Twitter branches here |
| `features_stage2.py` | Reddit-native extractor; same constraint |
| `evaluate_twibot20.py` | Zero-shot evaluation script for Reddit cascade; frozen at v1.3 |
| All existing v1.3 artifacts in `.planning/workstreams/milestone/phases/12-*` | Paper evidence artifacts |

---

## Twitter-Native Feature Design

### Stage 1: Account Metadata (`features_stage1_twitter.py`)

The Reddit Stage 1 extractor (`features_stage1.py`) uses these columns:
`username`, `submission_num`, `comment_num_1`, `comment_num_2`, `subreddit_list`

These are Reddit-specific proxies. The TwiBot-20 loader in `twibot20_io.py` already populates
genuine Twitter equivalents in `load_accounts()`:

| TwiBot-20 field | Semantics | Stage 1 feature |
|-----------------|-----------|-----------------|
| `screen_name` | Twitter handle | `name_len` (len of screen_name) |
| `statuses_count` | Total tweets published (API-capped at 3200) | `tweet_count` |
| `followers_count` | Follower count | `followers_count` |
| `friends_count` | Following count | `friends_count` |
| `followers_count / (friends_count + eps)` | Follow ratio | `follow_ratio` |
| tweet parse: RT count | From `parse_tweet_types()` via messages | `rt_count` |
| tweet parse: MT count | From `parse_tweet_types()` | `mt_count` |
| tweet parse: original count | From `parse_tweet_types()` | `orig_count` |
| `rt_count / (total_tweets + eps)` | RT fraction | `rt_frac` |
| `orig_count / (total_tweets + eps)` | Original content fraction | `orig_frac` |
| `len(domain_list)` | Number of topical domains | `domain_count` |

Do NOT import `features_stage1.py` or re-use any of its logic. Build a standalone function:

```python
# features_stage1_twitter.py
def extract_stage1_matrix_twitter(df: pd.DataFrame) -> np.ndarray:
    """
    Stage 1 features from TwiBot-20 account metadata.
    Input df must have columns produced by twibot20_io.load_accounts():
      screen_name, statuses_count, followers_count, friends_count,
      messages (list of dicts), domain_list (list of str).
    Returns ndarray shape (N, 11) — all float32.
    """
```

The output column count (11) is an example; the exact count does not need to match Reddit Stage 1's
10 columns. `train_system()` passes arrays to `Stage1MetadataModel.fit()` which is size-agnostic.
`MahalanobisNovelty.fit()` is also size-agnostic. The only constraint is that train-time and
inference-time feature extractors produce identically-shaped arrays for the same split — which is
guaranteed by calling the same function in both places.

The function must call `parse_tweet_types()` from `twibot20_io` to obtain RT/MT/original breakdown,
since `messages` is a list of dicts with `{"text": str, "ts": None, "kind": "tweet"}` — not raw
text strings.

### Stage 2: Tweet Content and Temporal (`features_stage2_twitter.py`)

The Reddit Stage 2 extractor (`features_stage2.py`) is structurally reusable because it reads
`messages[].text` and `messages[].ts`. TwiBot-20's `messages` already has this exact shape from
`twibot20_io.load_accounts()`.

However, two Reddit-specific assumptions must be replaced:

1. **Timestamp sentinel**: `features_stage2.py` uses `_MISSING_TEMPORAL_SENTINEL = -1.0` when
   tweets exist but all timestamps are None. In TwiBot-20, timestamps in `messages[].ts` are always
   `None` (the loader sets `"ts": None` unconditionally). This is a systematic difference, not
   missing data: TwiBot-20 simply does not expose tweet timestamps in the native JSON. The Twitter-
   native Stage 2 extractor must handle this cleanly — compute content/linguistic features only
   (embedding pool, linguistic aggregate, cross-message similarity), set temporal features to 0.0
   explicitly (not the sentinel), and omit timestamp-derived features entirely from the output vector.
   This is correct because the novelty scorer (Mahalanobis) is fit on the training set, which has
   the same zero-temporal structure — so it is not OOD for this model.

2. **No sentinel cross-contamination**: the sentinel values from `features_stage2.py` (-1.0 for
   temporal features) will confuse a model trained natively on TwiBot-20. Do not import or reuse
   `_MISSING_TEMPORAL_SENTINEL` from `features_stage2.py`.

Recommended output vector for Twitter Stage 2 (per account):

```
[embedding_pool (384-d), ling_pool (4-d), cross_msg_sim_mean (1), near_dup_frac (1)]
= 390 dimensions
```

Temporal features are omitted because they are never available in TwiBot-20. This is a deliberate
design choice, not a workaround — the paper should report the feature set explicitly.

```python
# features_stage2_twitter.py
def extract_stage2_features_twitter(df: pd.DataFrame, embedder, max_msgs: int = 50, max_chars: int = 500) -> np.ndarray:
    """
    Stage 2 features from TwiBot-20 tweet timelines.
    Uses df['messages'] list of dicts with 'text' key.
    Timestamps are not present in TwiBot-20 — temporal features are omitted.
    Output shape: (N, 390) — float32.
    """
```

### Stage 3: Graph Structure (no new file required)

`build_graph_features_nodeidx()` already accepts `{src, dst, etype, weight}` DataFrames and is
platform-agnostic. `twibot20_io.build_edges()` already produces this exact format (etype=0 for
following, etype=1 for follower, weight=log1p(1.0)). No new graph feature extractor is needed.

Two edge types (following=0, follower=1) are already separated in `build_edges()`, unlike the v1.2
zero-shot path which used only etype=0. The TwiBot-native cascade will have real per-type degree
features for both following and follower edges. Per-type[2] features (etype=2) will be zero — this
is not a problem since the Stage 3 model is trained on this same structure.

---

## TwiBot-20 Train/Val/Test Split

TwiBot-20 ships canonical splits: `train.json`, `val.json`, `test.json`. For the supervised
baseline:

- **Stage model training (S1):** subset of `train.json`
- **Meta-learner OOF training (S2):** separate subset of `train.json`
- **Threshold calibration:** `val.json` (the canonical validation split)
- **Final evaluation (S3):** `test.json` (held out until final metrics)

Recommended split of `train.json`:

```
train.json  →  stratified 80/20 split  →  S1 (80%)  +  S2 (20%)
val.json    →  calibrate_thresholds()
test.json   →  final evaluate_s3()
```

This mirrors the Reddit cascade's S1/S2/S3 discipline. Using the canonical `val.json` for threshold
calibration instead of another `train.json` slice has two advantages: (1) it respects the original
split boundaries, preventing any possibility of leakage between calibration and test sets; (2) it
keeps the evaluation setup comparable to published TwiBot-20 baselines that use the same split.

OOF stacking discipline for meta-learners:
- `oof_meta12_predictions()` runs 5-fold CV entirely within S2 (the 20% slice of `train.json`)
- The final `meta12` and `meta123` are trained on all of S2
- Threshold calibration runs on `val.json` (never on S2 or test.json)
- `evaluate_s3()` runs on `test.json`

This is the same OOF stacking regime as the Reddit cascade. No changes to `oof_meta12_predictions()`
or `calibrate_thresholds()` are needed.

---

## Data Flow: TwiBot-20 Native Training Path

```
TwiBot-20 files on disk
  train.json   val.json   test.json
        |
        v
twibot20_io.load_accounts(train.json)    ->  train_df  (N_train accounts)
twibot20_io.build_edges(train_df, train.json)  ->  train_edges_df
        |
        | stratified 80/20 split (SEED=42)
        v
  S1 (80% of train_df)   S2 (20% of train_df)
  edges_S1 (intra-S1)    edges_S2 (intra-S2)
        |
        v
train_system(S1, S2, edges_S1, edges_S2, ...)
  |-- Stage 1:  extract_stage1_matrix_twitter(S1)      [features_stage1_twitter.py]
  |-- Stage 2a: extract_stage2_features_twitter(S1, embedder) [features_stage2_twitter.py]
  |-- Stage 2b: extract_amr_embeddings_for_accounts(S1, ...)  [botdetector_pipeline.py — unchanged]
  |-- Stage 3:  build_graph_features_nodeidx(S1, edges_S1, nodes_total) [botdetector_pipeline.py — unchanged]
  |-- OOF meta12 on S2
  |-- meta123 training on S2
  v
TrainedSystem (TwiBot-native)
        |
        v
calibrate_thresholds(system, val_df, val_edges_df, ...)  [calibrate.py — unchanged]
        |
        v
predict_system(system, test_df, test_edges_df, ...)  [botdetector_pipeline.py — unchanged]
        |
        v
evaluate_s3(results, y_true)  [evaluate.py — unchanged]
        |
        v
joblib.dump(system, "trained_system_twibot20.joblib")
```

The three injections of Twitter-native feature extractors happen inside `train_system()`, which calls:
- `extract_stage1_matrix(S1)` — need to make this call use the Twitter extractor
- `extract_stage2_features(S2, embedder)` — same

This is the only structural tension: `train_system()` currently imports `extract_stage1_matrix`
from `features_stage1` and `extract_stage2_features` from `features_stage2` via module-level imports
in `botdetector_pipeline.py`.

**Resolution:** `train_twibot20.py` passes the Twitter-native extractor functions as arguments to
`train_system()`, OR it monkey-patches `botdetector_pipeline.extract_stage1_matrix` before calling
`train_system()` (the same pattern `evaluate_twibot20.py` already uses for `bp.extract_stage1_matrix`).

The monkey-patch pattern is already established and safe (the Reddit cascade's `main.py` and
`evaluate_twibot20.py` coexist). However, a cleaner long-term design is to accept extractor
callables as parameters to `train_system()`. Given the v1.4 constraint of not modifying
`botdetector_pipeline.py` significantly, the monkey-patch approach is preferred for v1.4.

Concretely in `train_twibot20.py`:

```python
import botdetector_pipeline as bp
from features_stage1_twitter import extract_stage1_matrix_twitter
from features_stage2_twitter import extract_stage2_features_twitter

bp.extract_stage1_matrix = extract_stage1_matrix_twitter
bp.extract_stage2_features = extract_stage2_features_twitter
try:
    sys = train_system(S1, S2, edges_S1, edges_S2, ...)
finally:
    bp.extract_stage1_matrix = _orig_s1
    bp.extract_stage2_features = _orig_s2
```

This is safe because `train_twibot20.py` is a standalone entry point that is never imported by
`main.py` or `evaluate_twibot20.py`. The patch is scoped to the process and the try/finally block.

---

## New Entry Point: `train_twibot20.py`

```python
# train_twibot20.py — new file
"""
Train a Twitter-native cascade on TwiBot-20 train.json.
Evaluate on test.json. Save as trained_system_twibot20.joblib.

The Reddit cascade (trained_system_v12.joblib) is never loaded or modified.

Usage:
    python train_twibot20.py <train_json> <val_json> <test_json> [output_path]

Defaults:
    train_json   = "train.json"
    val_json     = "val.json"
    test_json    = "test.json"
    output_path  = "trained_system_twibot20.joblib"
"""
```

Responsibilities:
1. Load train.json, val.json, test.json via `twibot20_io.load_accounts()`
2. Build edges for each split via `twibot20_io.build_edges()`
3. Split train into S1/S2 (stratified 80/20)
4. Intra-split edge filtering via `filter_edges_for_split()` (copy from `main.py` — do not import
   from `main.py` to avoid triggering BotSim-24 imports)
5. Monkey-patch `botdetector_pipeline.extract_stage1_matrix` and `extract_stage2_features`
6. Call `train_system()`
7. Restore original extractors
8. Call `calibrate_thresholds()` on val split
9. Call `predict_system()` + `evaluate_s3()` on test split
10. Save `TrainedSystem` as `trained_system_twibot20.joblib`
11. Save metrics to `metrics_twibot20_native.json`

`filter_edges_for_split()` is currently defined locally in `main.py` (not exported). Copy the
two-liner into `train_twibot20.py` to avoid coupling:

```python
def filter_edges_for_split(edges_df: pd.DataFrame, node_ids: np.ndarray) -> pd.DataFrame:
    node_set = set(node_ids.tolist())
    m = edges_df["src"].isin(node_set) & edges_df["dst"].isin(node_set)
    return edges_df[m].reset_index(drop=True)
```

---

## New Entry Point: `evaluate_twibot20_native.py`

Separate from the existing `evaluate_twibot20.py` (which runs the Reddit cascade zero-shot).
This file runs the TwiBot-native cascade on test.json.

```python
# evaluate_twibot20_native.py — new file
"""
Run the TwiBot-native cascade on TwiBot-20 test.json.
Loads trained_system_twibot20.joblib (produced by train_twibot20.py).
Does NOT load or reference trained_system_v12.joblib.

Usage:
    python evaluate_twibot20_native.py <test_json> [model_path] [output_dir]
"""
```

Unlike `evaluate_twibot20.py` (which monkey-patches Stage 1 to clamp ratios for zero-shot
compatibility), `evaluate_twibot20_native.py` must monkey-patch to use the Twitter-native
extractors. The TwiBot-native `TrainedSystem` was trained with those extractors — calling the
Reddit extractors at inference time would be a feature mismatch and must be prevented.

The pattern is identical to the training entry point:

```python
bp.extract_stage1_matrix = extract_stage1_matrix_twitter
bp.extract_stage2_features = extract_stage2_features_twitter
try:
    results = predict_system(sys, test_df, test_edges_df, nodes_total=len(test_df))
finally:
    bp.extract_stage1_matrix = _orig_s1
    bp.extract_stage2_features = _orig_s2
```

---

## Paper Comparison Table

The v1.4 paper contribution is a direct comparison:

| System | Trained on | Evaluated on | F1 | AUC |
|--------|-----------|--------------|-----|-----|
| Reddit cascade (v1.3) | BotSim-24 | TwiBot-20 test | 0.0 | 0.5964 |
| TwiBot cascade (v1.4) | TwiBot-20 train | TwiBot-20 test | TBD | TBD |

This table is built from:
- Row 1: already in `metrics_twibot20_comparison.json` (Phase 12 artifact, static condition)
- Row 2: produced by `evaluate_twibot20_native.py` → `metrics_twibot20_native.json`

Add a function to `ablation_tables.py`:

```python
def generate_platform_comparison_table(
    reddit_metrics: dict,  # from metrics_twibot20_comparison.json, conditions.static.overall
    twibot_metrics: dict,  # from metrics_twibot20_native.json, overall
) -> str:
    """Return LaTeX tabular string comparing Reddit-trained vs TwiBot-trained on TwiBot-20 test."""
```

---

## Artifact Naming Convention

| Artifact | Description |
|----------|-------------|
| `trained_system_v12.joblib` | Reddit-native cascade (frozen, do not overwrite) |
| `trained_system_twibot20.joblib` | TwiBot-native cascade (new, produced by `train_twibot20.py`) |
| `metrics_twibot20_native.json` | Evaluation metrics for TwiBot-native cascade on test.json |

Do not name the new artifact `trained_system.joblib` — that name is reserved for the active Reddit
artifact and is referenced by `evaluate_twibot20.py`.

---

## Build Order (dependency-ordered)

```
Phase 1: Twitter-native feature extractors (no dependencies on new code)
  a. features_stage1_twitter.py
       - extract_stage1_matrix_twitter(df) -> ndarray
       - Uses: twibot20_io.parse_tweet_types(), df columns from load_accounts()
       - No imports from features_stage1.py
  b. features_stage2_twitter.py
       - extract_stage2_features_twitter(df, embedder) -> ndarray
       - Omits temporal features (timestamps always None in TwiBot-20)
       - No imports from features_stage2.py

Phase 2: Unit tests for new extractors (independent of Phase 3+)
       - Smoke test: single-account input produces correct shape
       - No-messages case: returns zero vector of correct shape
       - All-RT account: rt_frac=1.0, orig_frac=0.0
       - Stage 2 with embedder: output dim = 384 + 4 + 2 = 390

Phase 3: train_twibot20.py (depends on Phase 1 and existing pipeline)
       - Monkey-patch pattern: patch → train_system() → restore
       - S1/S2 split of train.json
       - Intra-split edge filtering (local copy of filter_edges_for_split)
       - calibrate_thresholds() on val.json
       - evaluate_s3() on test.json
       - Save trained_system_twibot20.joblib
       - Save metrics_twibot20_native.json

Phase 4: evaluate_twibot20_native.py (depends on Phase 3 artifact)
       - Thin wrapper: load artifact, monkey-patch, predict_system(), evaluate_s3()
       - Confirm metrics match Phase 3 output (regression check)

Phase 5: ablation_tables.py — platform comparison table (depends on Phase 3+4 metrics)
       - generate_platform_comparison_table(reddit_metrics, twibot_metrics) -> LaTeX
       - Reads from Phase 12 artifact (reddit) and metrics_twibot20_native.json (twibot)

Phase 6: Remove online novelty recalibration from Reddit cascade (independent, can be done earlier)
       - Locate and remove the chunked online-calibration path in evaluate_twibot20.py
         (the window-based threshold recalibration loop)
       - main.py is unaffected (online recalibration was only in evaluate_twibot20.py)
       - Update evaluate_twibot20.py to always use online_calibration=False
       - Re-run Phase 12 evaluation to regenerate artifacts if needed
```

Phase 1 and Phase 6 can run in parallel (no dependencies between them). Phases 2, 3, 4, 5 must
run sequentially. Phase 6 can run at any point before or after Phases 1-5.

---

## OOF Stacking Discipline (explicit confirmation)

The OOF contract from v1.0 is preserved unchanged for the TwiBot-native cascade:

1. Stage 1, Stage 2a, Stage 2b, Stage 3 models are all fit on S1 only.
2. `oof_meta12_predictions()` runs 5-fold CV within S2 to produce leakage-free p12 OOF predictions.
3. `meta12` is trained on all of S2 (after OOF predictions are available).
4. Stage 3 routing on S2 uses the OOF p12 (not the final meta12's predictions).
5. `meta123` is trained on S2 using the OOF p12 → z12 and Stage 3 outputs.
6. Threshold calibration uses `val.json` — a set that S2 never sees.
7. Final evaluation uses `test.json` — a set that val and S2 never see.

None of these steps require changes to `botdetector_pipeline.py`. The S1/S2 split of `train.json`
must be stratified by label (same as Reddit cascade's shuffled split).

---

## Anti-Patterns to Avoid

### Anti-Pattern 1: Importing Reddit feature extractors in Twitter code
**What goes wrong:** `features_stage1_twitter.py` imports `extract_stage1_matrix` from
`features_stage1.py` as a base, then overrides columns. Any change to the Reddit extractor
could silently affect TwiBot training.
**Instead:** Build `features_stage1_twitter.py` as a standalone module. Zero imports from
`features_stage1.py` or `features_stage2.py`.

### Anti-Pattern 2: Using the timestamp sentinel in Twitter Stage 2
**What goes wrong:** `features_stage2.py` sets temporal features to `-1.0` when timestamps are
missing. If `features_stage2_twitter.py` replicates this, the Stage 2 model is trained on `-1.0`
sentinel values and the Mahalanobis novelty model is calibrated to those values. At inference time,
any account with actual timestamps (possible in future Twitter datasets) would be OOD. More
immediately, the paper's feature description would need to explain an implementation artifact.
**Instead:** Omit temporal features entirely. The output vector is shorter but honest.

### Anti-Pattern 3: Calling train_system() without restoring extractors
**What goes wrong:** If `train_twibot20.py` patches `botdetector_pipeline.extract_stage1_matrix`
and then crashes inside `train_system()`, the module-level extractor stays patched for the rest
of the process. If another script imports `botdetector_pipeline` in the same process, it sees
the Twitter extractor.
**Instead:** Always use try/finally to restore the original extractor references.

### Anti-Pattern 4: Saving the TwiBot artifact as trained_system.joblib
**What goes wrong:** `evaluate_twibot20.py` (the zero-shot Reddit script) defaults to loading
`trained_system_v12.joblib` but also references `trained_system.joblib` as a fallback in some
paths. Overwriting it breaks the v1.3 zero-shot evaluation reproducibility.
**Instead:** Always save as `trained_system_twibot20.joblib`. Never write to `trained_system.joblib`
from `train_twibot20.py`.

### Anti-Pattern 5: Running calibrate_thresholds() on test.json
**What goes wrong:** Threshold calibration on the test set is a form of leakage — the thresholds
are tuned to the exact distribution being evaluated.
**Instead:** Calibrate on `val.json` exclusively. Evaluate on `test.json` with the calibrated
thresholds without further tuning.

---

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| TwiBot-20 train.json label imbalance differs from val/test | Medium | Log class distribution of each split; use `class_weight="balanced"` in all LightGBM and LogisticRegression calls (already the default in the pipeline) |
| Stage 2 output dimension (390) does not match Reddit Stage 2 (391) | Low | Dimensions need not match — each `TrainedSystem` carries its own model weights; there is no shared weight between Reddit and TwiBot cascades |
| Monkey-patch not thread-safe if ever parallelized | Low | Both entry points are `__main__` scripts; no concurrent imports |
| TwiBot-20 accounts with zero tweets | Medium | `extract_stage2_features_twitter` must return a zero embedding vector (not crash) for empty `messages` lists — same handling as `features_stage2.py` |
| val.json too small for reliable calibration | Medium | TwiBot-20 val split has ~2628 accounts — sufficient for Optuna TPE with 50-100 trials; use fewer trials than Reddit cascade (8-50 range) |
| Stage 3 neighbor sparsity in TwiBot-20 train split | Medium | `build_edges()` already drops cross-set edges (edges referencing accounts not in the current JSON file); intra-split filtering via `filter_edges_for_split` further restricts to within-split edges; result may be a sparse graph — this is correct and expected |

---

## Summary: What to Build, What to Reuse, What to Leave Alone

**Build (4 new files, 1 new function):**
- `features_stage1_twitter.py` — Twitter-native Stage 1 extractor (11 features, no Reddit columns)
- `features_stage2_twitter.py` — Twitter-native Stage 2 extractor (390-d, no temporal sentinel)
- `train_twibot20.py` — Full cascade training entry point for TwiBot-20
- `evaluate_twibot20_native.py` — Inference + evaluation entry point for TwiBot-native cascade
- `ablation_tables.generate_platform_comparison_table()` — Paper comparison table

**Reuse unchanged (14 components):**
`train_system`, `predict_system`, `TrainedSystem`, `StageThresholds`, `MahalanobisNovelty`,
`Stage1/2/3 model classes`, `AMRDeltaRefiner`, `Stage2LSTMRefiner`, routing gates, `oof_meta12_predictions`,
`build_graph_features_nodeidx`, `evaluate_s3`, `calibrate_thresholds`, `twibot20_io` (both functions)

**Modify (2 files):**
- `main.py` — Remove online novelty recalibration block
- `ablation_tables.py` — Add one new comparison table function

**Leave alone (immutable):**
`features_stage1.py`, `features_stage2.py`, `evaluate_twibot20.py`, `trained_system_v12.joblib`,
all Phase 12 paper artifacts

---

*Architecture analysis: 2026-04-18*
*Milestone: v1.4 Twitter-Native Supervised Baseline*
