# Stack Research: v1.2 TwiBot-20 Cross-Dataset Evaluation

**Milestone:** v1.2 — TwiBot-20 Cross-Dataset Evaluation
**Research date:** 2026-04-16
**Confidence:** HIGH — all conclusions derived from direct codebase analysis and stdlib verification

---

## Summary

**Zero new package dependencies are required.** The TwiBot-20 loader fits entirely within the existing stack. The only non-trivial addition is a timestamp parser for Twitter's legacy RFC 2822 date format (`"Mon Apr 06 15:28:43 +0000 2009"`), which is handled by Python's stdlib `email.utils.parsedate_to_datetime` — verified working on this system.

---

## Existing Stack (unchanged)

| Package | Installed version | Role in v1.2 |
|---------|------------------|--------------|
| `pandas` | 2.2.3 | `pd.read_csv` for `edge.csv` / `label.csv`; account table construction |
| `numpy` | 2.1.3 | Feature matrix assembly, zero-fill for missing fields |
| `joblib` | 1.4.2 | `joblib.load("trained_system_v12.joblib")` — load production artifact |
| `sentence-transformers` | 5.2.3 | Stage 2a embedding — reused as-is from loaded system |
| `torch` | 2.10.0+cpu | Tensor loading only — no change |
| `scikit-learn` | 1.6.1 | `evaluate_s3()` metrics — reused as-is |
| `networkx` | 3.4.2 | Already installed; NOT needed for v1.2 — `build_graph_features_nodeidx` uses raw numpy, not networkx |
| `json` | stdlib | `user.json` loading |
| `email.utils` | stdlib | Twitter RFC 2822 timestamp parsing — verified working |
| `datetime` | stdlib | Timestamp conversion to Unix seconds |

---

## What Changes: New Module `twibot20_io.py`

The v1.2 work is entirely a new data-loading module. It must produce a `pd.DataFrame` matching the schema that `predict_system()` and `evaluate_s3()` consume. No existing file needs modification.

### Required output schema (contract with existing pipeline)

```
account_id        str
label             int (0=human, 1=bot)
username          str           — used by Stage 1: name_len
submission_num    float32       — used by Stage 1 feature matrix
comment_num       float32       — Stage 1 (c1+c2 total fallback)
comment_num_1     float32       — Stage 1
comment_num_2     float32       — Stage 1
subreddit_list    list[str]     — Stage 1: sr_num = len(subreddit_list)
messages          list[dict]    — Stage 2: {text, ts, kind, score}
node_idx          int           — Stage 3: row index in TwiBot-20 user list
```

### Field mapping: TwiBot-20 → BotSim-24 account table

| BotSim-24 field | TwiBot-20 source | Mapping strategy | Notes |
|---|---|---|---|
| `account_id` | `user.id` (str) | Direct | Kept as string |
| `label` | `label.csv["label"]` | Direct (0/1) | Joined by user id |
| `username` | `user["screen_name"]` | Direct | Stage 1 uses `len(username)` only |
| `submission_num` | `user["statuses_count"]` | Direct | Total tweet count — closest approximation to post count |
| `comment_num_1` | `0.0` | Zero-fill | Twitter has no comment hierarchy |
| `comment_num_2` | `0.0` | Zero-fill | Same |
| `comment_num` | `0.0` | Zero-fill | No Reddit-style comment count |
| `subreddit_list` | `[]` | Empty list | No subreddit concept; `sr_num` = 0 |
| `messages[].text` | `tweet["full_text"]` | Direct | Fall back to `tweet["text"]` if `full_text` absent |
| `messages[].ts` | `tweet["created_at"]` | `email.utils.parsedate_to_datetime` | RFC 2822 → Unix seconds |
| `messages[].kind` | `"tweet"` | Constant | Informational only |
| `messages[].score` | `tweet.get("favorite_count", 0)` | Direct | Used nowhere in current feature code |
| `node_idx` | row position in loaded user list | `enumerate` | Stage 3 uses this as integer index into degree arrays |

### Graph edges (Stage 3)

`edge.csv` columns: `source_id`, `relation`, `target_id`

Relation strings need mapping to integer etype (the existing `build_graph_features_nodeidx` expects `etype` in {0, 1, 2}):

| TwiBot-20 relation | etype |
|---|---|
| `"following"` | 0 |
| `"followed_by"` / `"follower"` | 1 |
| any other (retweet, etc.) | 2 |

`weight` = 1.0 for all edges (TwiBot-20 has no edge weights).

Node ids in `edge.csv` are Twitter user id strings. They must be mapped to integer `node_idx` values via the same enumeration used to assign `node_idx` to accounts.

The resulting edges DataFrame must have columns: `src` (int32), `dst` (int32), `weight` (float32), `etype` (int8).

---

## What NOT to Add

| Package | Reason to exclude |
|---------|-------------------|
| `networkx` | Already installed but unnecessary — `build_graph_features_nodeidx` uses raw numpy indexing, not graph objects |
| `tweepy` | No live API calls; TwiBot-20 is a static JSON dump |
| `python-igraph` / `graph-tool` | Graph library overkill — degree aggregation done with `np.add.at` |
| `orjson` / `ujson` | stdlib `json` is sufficient for a one-time static load |
| `pyarrow` | Already installed but unnecessary — `edge.csv` is a standard CSV, `pd.read_csv` suffices |
| `tqdm` | No progress bars needed for a single-dataset load |
| `transformers` (HuggingFace) | Not needed — sentence-transformers wraps it and is already in the stack |
| Any retraining libraries | Zero-shot only; `trained_system_v12.joblib` is loaded and used as-is |

---

## Integration Points with Existing Pipeline

```
twibot20_io.load_twibot20(
    user_json_path,
    edge_csv_path,
    label_csv_path,
) -> (accounts_df: pd.DataFrame, edges_df: pd.DataFrame, num_nodes: int)
```

This output drops directly into `predict_system(sys, accounts_df, edges_df, num_nodes)` without any modification to the existing pipeline code.

`evaluate_s3(results, y_true)` receives `accounts_df["label"].to_numpy()` as `y_true` — no change needed.

---

## Timestamp Parsing: Verified Approach

Twitter's `created_at` field uses RFC 2822 format: `"Mon Apr 06 15:28:43 +0000 2009"`.

```python
from email.utils import parsedate_to_datetime

def _twitter_ts_to_unix(dt_str: str) -> float | None:
    if not dt_str or not isinstance(dt_str, str):
        return None
    try:
        return parsedate_to_datetime(dt_str).timestamp()
    except Exception:
        return None
```

Verified on this system: `parsedate_to_datetime("Mon Apr 06 15:28:43 +0000 2009")` returns a timezone-aware datetime correctly.

Do NOT use `datetime.strptime` with BotSim-24's `"%Y-%m-%d %H:%M:%S"` format — it will fail on Twitter dates. The existing `_to_unix_seconds` in `botsim24_io.py` is BotSim-24-only.

---

## Feature Gap Impact Assessment

The zero-filled fields affect Stage 1 feature quality but do not break the pipeline. Specifically:

| Feature dim | BotSim-24 value | TwiBot-20 value | Impact |
|---|---|---|---|
| `comment_num_1` (idx 2) | actual count | 0.0 | Stage 1 novelty will be high — Mahalanobis distance from training distribution increases |
| `comment_num_2` (idx 3) | actual count | 0.0 | Same |
| `sr_num` (idx 5) | subreddit count | 0 | Stage 1 ratios (post_sr) will use eps denominator |
| post/comment ratios (idx 6-9) | varied | 0 or inf-clamped | `np.nan_to_num` in `extract_stage1_matrix` handles inf/nan |

**High novelty scores on TwiBot-20 are expected and scientifically correct** — the accounts are out-of-distribution. The cascade's novelty-aware routing will force more accounts through Stage 2/3 than on BotSim-24. This is intentional behavior to document in the paper (cross-platform routing statistics).

---

## Sources

- `botdetector_pipeline.py`: `build_graph_features_nodeidx`, `predict_system`, `TrainedSystem` dataclass — direct inspection
- `features_stage1.py`: all 10 Stage 1 feature dimensions — direct inspection
- `features_stage2.py`: 397-dim vector construction — direct inspection
- `botsim24_io.py`: `build_account_table` account schema — direct inspection
- `evaluate.py`: `evaluate_s3` input contract — direct inspection
- Python stdlib `email.utils.parsedate_to_datetime` — verified working on this system
- TwiBot-20 schema: known from Feng et al. 2021 paper and GitHub; confirmed by `TwiBot-20 Seed Users.txt` presence in repo
