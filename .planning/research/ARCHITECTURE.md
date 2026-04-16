# Architecture: TwiBot-20 Cross-Dataset Loader Integration

**Domain:** Cross-dataset evaluation — TwiBot-20 (Twitter) loader for a BotSim-24-trained Reddit cascade
**Researched:** 2026-04-16
**Milestone:** v1.2 TwiBot-20 Cross-Dataset Evaluation
**Confidence:** HIGH (codebase verified; TwiBot-20 format from training knowledge, confidence MEDIUM for
              exact field names — flag for verification when actual files are in hand)

---

## The Integration Contract

The cascade pipeline has one intake boundary: `build_account_table()`. It returns a DataFrame whose columns
are consumed directly by `extract_stage1_matrix()` and `extract_stage2_features()`. Everything downstream
(stages, gates, meta-learners) is format-agnostic beyond that boundary.

**Goal:** produce a `build_twibot20_account_table()` whose output is structurally identical to
`build_account_table()` output. Once that contract is satisfied, `predict_system()` and `evaluate_s3()`
run unchanged.

---

## Internal Account Format (the target)

The following columns are the exact contract that all feature extractors expect. Every column must be
present with compatible dtype.

| Column | Dtype | Source in BotSim-24 | Notes |
|--------|-------|---------------------|-------|
| `account_id` | str | `Users.csv:user_id` | Used only for join and output; no stage extracts from it |
| `label` | int (0/1) | row-order rule in Users.csv | 0 = human, 1 = bot |
| `username` | str | `Users.csv:name` | Length used in Stage 1 (`extract_stage1_matrix:name_len`) |
| `profile` | str | `Users.csv:description` | NOT used by any feature extractor (dropped after v1.1 leakage fix); keep for schema parity |
| `subreddit_list` | list[str] | `Users.csv:subreddit` | Length → `sr_num` in Stage 1 |
| `submission_num` | float32 | `Users.csv:submission_num` | Stage 1 feature |
| `comment_num` | float32 | `Users.csv:comment_num` | Stage 1 feature |
| `comment_num_1` | float32 | `Users.csv:comment_num_1` | Stage 1 feature |
| `comment_num_2` | float32 | `Users.csv:comment_num_2` | Stage 1 feature |
| `messages` | list[dict] | `user_post_comment.json` | Entire Stage 2 input |
| `node_idx` | int32 | assigned by `main.py` after build | Stage 3 edge lookup; must be integer index into edges arrays |

Each message dict in `messages` must contain:

| Key | Dtype | Required by Stage 2 |
|-----|-------|---------------------|
| `text` | str | Embedding and linguistic features |
| `ts` | float or None | Temporal features (rate, deltas, hour entropy) |
| `kind` | str | Not currently extracted; carry anyway for debugging |
| any extra keys | — | Ignored by extractors |

---

## TwiBot-20 Source Format (what the loader receives)

TwiBot-20 ships three files:

**`user.json`** — list of user objects. Each object contains:
- `id` — Twitter user ID string (maps to account_id)
- `name` — display name (maps to username)
- `screen_name` — handle (@username)
- `description` — bio text (maps to profile; not used after v1.1)
- `followers_count`, `friends_count` (following), `listed_count`, `favourites_count`,
  `statuses_count` — numeric activity counts
- `created_at` — ISO-8601 or Twitter date string
- `tweet` — list of tweet objects embedded in the user record (the main content source)
  - each tweet: `id_str`, `full_text` or `text`, `created_at`, `retweet_count`, `favorite_count`

**`edge.csv`** — CSV with columns (order may vary, check header):
- `source_id` — follower user ID
- `target_id` — followee user ID
- (no weight or type column by default — all edges are follow-relationship, single type)

**`label.csv`** — CSV with columns:
- `id` — user ID
- `label` — "bot" or "human" string (must be mapped to int 1/0)

---

## Feature Gap Analysis: TwiBot-20 → BotSim-24 Contract

### Stage 1 (`extract_stage1_matrix`)

| BotSim-24 field | TwiBot-20 mapping | Gap? |
|-----------------|------------------|------|
| `username` (length) | `name` or `screen_name` in user.json | None — direct map |
| `submission_num` | `statuses_count` (total tweets ever) | Approximate — statuses_count includes all tweets, not just original posts |
| `comment_num_1` | No direct equivalent | Set to 0.0 — replies are not separated from tweets in TwiBot-20 |
| `comment_num_2` | No direct equivalent | Set to 0.0 |
| `comment_num` | 0.0 (same reason) | Approximation accepted for zero-shot |
| `subreddit_list` (length) | Not applicable — Twitter has no subreddits | Set to empty list `[]`; sr_num will be 0 |

The Stage 1 model was trained on BotSim-24 distributions. Zero-valued comment counts and subreddit count
will create OOD inputs — the Mahalanobis novelty scorer will register high novelty for most TwiBot-20
accounts. This is expected and correct: novelty forces cascade escalation, which is the right behavior
for OOD inputs.

### Stage 2 (`extract_stage2_features`)

| BotSim-24 source | TwiBot-20 mapping | Gap? |
|-----------------|------------------|------|
| `messages[].text` (posts/comments) | tweet `full_text` or `text` | None — direct map |
| `messages[].ts` (Unix seconds) | tweet `created_at` (Twitter date string) | Parse required — convert Twitter date format to Unix seconds |
| `messages[].kind` | "tweet" | None — kind is not extracted |
| Score/upvote_ratio/num_comments | `retweet_count`, `favorite_count` in tweet | Carried in message dict; not currently extracted by features_stage2.py |

Content signal is structurally equivalent: both are free-text posts with timestamps. Stage 2 should
generalize reasonably — content style (repetition, temporal patterns) transfers across platforms.

### Stage 3 (`build_graph_features_nodeidx`)

| BotSim-24 source | TwiBot-20 mapping | Gap? |
|-----------------|------------------|------|
| `edge_index.pt` shape [E,2] | `edge.csv` columns source_id, target_id | Format conversion required |
| `edge_type.pt` values 0/1/2 | Only follow edges — single type | All edges get etype=0 |
| `edge_weight.pt` continuous weight | No weight in edge.csv | Default weight=1.0 for all edges |
| node integer indices | Must be created from ID-to-index mapping | No gap in logic; requires explicit index assignment |

Stage 3 graph features (per-type degree, weighted degree) were trained on BotSim-24 edge semantics
(3 edge types, continuous weights). On TwiBot-20 (single type, binary weight), all per-type[1] and
per-type[2] features will be zero, and weighted degrees equal unweighted degrees. The trained Stage 3
model will be OOD on this input. Mahalanobis novelty will flag this — Stage 3 will either not contribute
or contribute noise. The zero-shot expectation is that Stage 3 degrades; this should be reported as-is
in the paper as a cross-platform generalization finding.

---

## New Components Required

### 1. `twibot20_io.py` — New file (mirrors `botsim24_io.py`)

This file is the only new module. It must implement:

```python
def _parse_twitter_date(dt_str: str) -> Optional[float]:
    """Parse Twitter's 'Thu Oct 08 12:34:56 +0000 2020' format to Unix seconds."""

def load_twibot20_users(path: str) -> List[Dict]:
    """Load user.json — returns raw list of user objects."""

def load_twibot20_labels(path: str) -> Dict[str, int]:
    """Load label.csv — returns {user_id: 0/1} mapping."""

def load_twibot20_edges(path: str) -> pd.DataFrame:
    """Load edge.csv — returns DataFrame with columns: src, dst, etype, weight.
    All edges: etype=0, weight=1.0. src/dst are integer node indices
    (requires the id-to-index map produced by build_twibot20_account_table)."""

def build_twibot20_account_table(
    users: List[Dict],
    labels: Dict[str, int],
    max_tweets: int = 200,
) -> pd.DataFrame:
    """
    Converts TwiBot-20 user.json + label.csv into the internal account format.
    Output columns match build_account_table() exactly:
      account_id, label, username, profile, subreddit_list,
      submission_num, comment_num, comment_num_1, comment_num_2, messages
    node_idx is NOT assigned here — assigned by evaluate_twibot20.py after the call.
    """
```

`load_twibot20_edges` depends on the id-to-index map, so it must be called after
`build_twibot20_account_table`. The call sequence in the evaluation script is:

```
accounts_tb20 = build_twibot20_account_table(users, labels)
accounts_tb20["node_idx"] = np.arange(len(accounts_tb20), dtype=np.int32)
id_to_idx = dict(zip(accounts_tb20["account_id"], accounts_tb20["node_idx"]))
edges_tb20 = load_twibot20_edges("edge.csv", id_to_idx)
```

### 2. `evaluate_twibot20.py` — New evaluation entry point script

A new top-level script (not a function in an existing module) that:

1. Loads `trained_system_v12.joblib` — zero-shot, no retraining
2. Calls `twibot20_io` to build the account table and edges DataFrame
3. Calls `predict_system(sys, accounts_tb20, edges_tb20, nodes_total=len(accounts_tb20))`
4. Calls `evaluate_s3(results, y_true)` — reused unchanged
5. Calls `generate_cross_dataset_table(results_botsim, results_twibot)` — new function (see below)

This script is separate from `main.py` to preserve the existing BotSim-24 training pipeline untouched.

### 3. Cross-dataset LaTeX table (in `ablation_tables.py` or new `cross_dataset_tables.py`)

A single new function `generate_cross_dataset_table(botsim_metrics, twibot_metrics)` that produces:

| Dataset | F1 | AUC | Precision | Recall | Stage 1 exit % | AMR trigger % | Stage 3 exit % |
|---------|----|-----|-----------|--------|----------------|---------------|----------------|
| BotSim-24 (S3) | — | — | — | — | — | — | — |
| TwiBot-20 (zero-shot) | — | — | — | — | — | — | — |

This can go in `ablation_tables.py` as an additional function, or in a separate `cross_dataset_tables.py`
if the file is already large. Preference: add to `ablation_tables.py` to keep table generation centralized.

---

## Existing Components: No Modification Required

| Component | Status | Rationale |
|-----------|--------|-----------|
| `botdetector_pipeline.py:predict_system` | Unchanged | Accepts any DataFrame + edges_df matching internal format |
| `botdetector_pipeline.py:build_graph_features_nodeidx` | Unchanged | Works on integer node indices — format-agnostic |
| `botdetector_pipeline.py:extract_amr_embeddings_for_accounts` | Unchanged | Operates on `messages[-1].text` — same in TwiBot-20 |
| `features_stage1.py:extract_stage1_matrix` | Unchanged | Reads named columns; zero-filled gaps return zeros gracefully |
| `features_stage2.py:extract_stage2_features` | Unchanged | Reads `messages[].text` and `messages[].ts` — same contract |
| `evaluate.py:evaluate_s3` | Unchanged | Operates on `predict_system()` output DataFrame — format-agnostic |
| `botsim24_io.py` | Unchanged | BotSim-24 pipeline untouched |
| `main.py` | Unchanged | Training pipeline untouched |
| `trained_system_v12.joblib` | Unchanged | Zero-shot: load and run, no retrain |

---

## Data Flow: TwiBot-20 Evaluation Path

```
TwiBot-20 files on disk
  user.json  edge.csv  label.csv
        |
        v
twibot20_io.py
  load_twibot20_users(user.json)       -> raw user list
  load_twibot20_labels(label.csv)      -> {id: 0/1}
  build_twibot20_account_table(...)    -> accounts_tb20 DataFrame
        |
        | (assign node_idx = arange)
        | (build id_to_idx map)
        v
  load_twibot20_edges(edge.csv, id_to_idx)  -> edges_tb20 DataFrame
        |
        v
evaluate_twibot20.py
  joblib.load("trained_system_v12.joblib")  -> sys (TrainedSystem)
        |
        v
predict_system(sys, accounts_tb20, edges_tb20, nodes_total)
  |-- Stage 1: extract_stage1_matrix(accounts_tb20)
  |     [submission_num=statuses_count, comment_num*=0.0, sr_num=0 -> high novelty expected]
  |-- Stage 2: extract_stage2_features(accounts_tb20, sys.embedder)
  |     [messages from tweets - structurally equivalent]
  |-- Stage 2b AMR: extract_amr_embeddings_for_accounts(...)
  |     [uses messages[-1].text - same contract]
  |-- Stage 3: build_graph_features_nodeidx(accounts_tb20, edges_tb20, nodes_total)
  |     [single etype=0, weight=1.0 -> per-type[1,2] features all zero -> OOD, high novelty]
  v
results DataFrame (p1, p2, p12, p3, p_final, amr_used, stage3_used, ...)
        |
        v
evaluate_s3(results, y_true)           -> metrics dict (F1, AUC, precision, recall, routing stats)
        |
        v
generate_cross_dataset_table(botsim_metrics, twibot_metrics)  -> LaTeX string
```

---

## Stage 3 Graph Handling: edge.csv vs PyTorch Tensors

BotSim-24 stores edges as three `.pt` tensors (`edge_index.pt`, `edge_type.pt`, `edge_weight.pt`)
loaded in `main.py` and converted to a `pd.DataFrame` with columns `{src, dst, etype, weight}`.
`build_graph_features_nodeidx` operates on that DataFrame — it never touches `.pt` files directly.

TwiBot-20 ships `edge.csv`. The loader must produce the same DataFrame schema:

```python
# Inside load_twibot20_edges(path, id_to_idx):
df = pd.read_csv(path)                          # columns: source_id, target_id (verify header)
df = df[df["source_id"].isin(id_to_idx) & df["target_id"].isin(id_to_idx)]
edges = pd.DataFrame({
    "src":    df["source_id"].map(id_to_idx).astype(np.int32),
    "dst":    df["target_id"].map(id_to_idx).astype(np.int32),
    "etype":  np.zeros(len(df), dtype=np.int8),      # all follow edges = type 0
    "weight": np.ones(len(df),  dtype=np.float32),   # no weight in TwiBot-20
})
return edges.dropna().reset_index(drop=True)
```

No change to `build_graph_features_nodeidx` is needed. The `n_types=3` parameter still iterates types
0/1/2, but types 1 and 2 will have zero-count masks, producing all-zero feature columns for those
positions — which is the correct representation of "no edges of this type."

---

## `node_idx` Assignment for TwiBot-20

In BotSim-24, `node_idx` maps to positions in the `.pt` tensor arrays, which encode a global node space
from the original graph construction. TwiBot-20 has no pre-existing global node space.

Solution: assign `node_idx = np.arange(len(accounts_tb20))` sequentially after building the account
table. Pass `nodes_total = len(accounts_tb20)` to `predict_system`. The edge loader uses the same
id-to-index map, so src/dst indices are consistent with node_idx values.

This is exactly the same pattern `main.py` uses for BotSim-24:
```python
users["node_idx"] = np.arange(len(users), dtype=np.int32)
```

---

## evaluate_s3() Reuse Analysis

`evaluate_s3()` takes `(results: pd.DataFrame, y_true: np.ndarray, threshold: float)`. It reads columns
`p1, p2, p12, p_final, amr_used, stage3_used, p3, n1, n2, n3`. These are all produced by
`predict_system()`. The function is completely dataset-agnostic.

**Verdict: evaluate_s3() is fully reusable without modification.**

The only new evaluation code needed is `generate_cross_dataset_table()` for the side-by-side paper
comparison. `evaluate_s3()` returns a dict; that dict is the input to the comparison function.

---

## Build Order (considering dependencies)

```
Step 1: twibot20_io.py — no dependencies on other new code
  - _parse_twitter_date()
  - load_twibot20_users()
  - load_twibot20_labels()
  - build_twibot20_account_table()       [does NOT call load_twibot20_edges]
  - load_twibot20_edges(path, id_to_idx) [called after account table built]

Step 2: Unit tests for twibot20_io.py — independent, can proceed before Step 3
  - Test that output columns match internal format contract exactly
  - Test _parse_twitter_date() with known inputs
  - Test label mapping ("bot"->1, "human"->0)
  - Test edge ID filtering (edges referencing unknown IDs are dropped)

Step 3: evaluate_twibot20.py — depends on Step 1 (twibot20_io) and trained_system_v12.joblib
  - Load trained system
  - Build account table and edges
  - Call predict_system (no change)
  - Call evaluate_s3 (no change)
  - Print metrics

Step 4: generate_cross_dataset_table() in ablation_tables.py — depends on Step 3 output format
  - Add function to existing ablation_tables.py
  - Input: two metrics dicts from evaluate_s3()
  - Output: LaTeX table string

Step 5: End-to-end run — depends on Steps 1-4 and actual TwiBot-20 data files on disk
  - Run evaluate_twibot20.py
  - Collect paper metrics
  - Generate LaTeX table
```

Steps 1 and 2 can proceed as soon as data file format is confirmed. Steps 3 and 4 are sequential.
Step 5 requires actual TwiBot-20 data files.

---

## Separate Evaluation Entry Point: Required

A separate `evaluate_twibot20.py` script is the correct choice (not modifying `main.py`) for these
reasons:

1. `main.py` handles training + evaluation of BotSim-24. Mixing in TwiBot-20 inference adds complexity
   and risks touching the training path.
2. `trained_system_v12.joblib` is a pre-built artifact — the evaluation script only needs
   `joblib.load`, not the full training imports.
3. The no-retrain constraint is enforced architecturally: there is no `train_system()` call in the
   evaluation script, making accidental retraining impossible.
4. Separate script makes it easy to run cross-dataset evaluation independently and produce metrics
   for a specific paper section without affecting the main experiment reproducibility.

---

## OOD Behavior Expectations (paper framing)

The cascade's novelty-aware routing will behave differently on TwiBot-20:

- **Stage 1:** High novelty expected for most TwiBot-20 accounts due to zero-filled comment counts and
  subreddit count. This will trigger Stage 3 routing (novelty_force_stage3 threshold).
- **Stage 3:** OOD input (single edge type, binary weights vs. 3 types + continuous weights).
  Stage 3 Mahalanobis scores will be very high. The model may produce unreliable p3.
- **p_final:** meta123 combines z12 and z3; if z3 is noisy, p_final quality depends on how much weight
  meta123 places on z12 vs z3.

This is not a failure mode — it is the correct description of zero-shot cross-platform transfer. The
paper framing should present Stage 1+2 as the primary generalization signal and Stage 3 as expected
degradation due to graph structure domain shift.

If the novelty-driven Stage 3 routing floods the system (all accounts routed to Stage 3) and
Stage 3 performs poorly, consider running a second evaluation variant with Stage 3 routing disabled
(th.s12_human=1.0, th.novelty_force_stage3=1e9) to isolate Stage 1+2 cross-platform performance.
This is a single threshold override, no retraining required.

---

## Risk Register

| Risk | Severity | Mitigation |
|------|----------|------------|
| Twitter date format differs from expected (multiple formats in dataset) | Medium | Parse with multiple format strings; fall back to dateutil.parser; log unparseable counts |
| edge.csv column names differ from assumed (source_id/target_id) | Low | Read header first; assert expected columns; add fallback column name guesses |
| TwiBot-20 user IDs are integers in some files, strings in others | Medium | Cast all IDs to str at load time; same pattern as botsim24_io.py |
| User in label.csv not present in user.json (or vice versa) | Low | Filter account table to intersection of both; log dropped count |
| Stage 3 graph is extremely large (TwiBot-20 has ~230K users in full dataset) | High | TwiBot-20 has subsets (TwiBot-20-Subet); use subset. If full dataset, build_graph_features_nodeidx runs on batch, not full graph — still fine since we only look up node_ids from accounts_tb20 |
| `messages` list is empty for many accounts (no tweets in user.json) | Medium | Stage 2 handles empty messages gracefully (returns zeros). Stage 1 not affected. Log zero-message rate. |

---

*Architecture analysis: 2026-04-16*
*Milestone: v1.2 TwiBot-20 Cross-Dataset Evaluation*
