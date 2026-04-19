# Phase 17: Shared Feature Extraction Module - Pattern Map

**Mapped:** 2026-04-18
**Files analyzed:** 9 (5 new, 4 modified)
**Analogs found:** 9 / 9

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `features/__init__.py` | package init | — | `tests/__init__.py` (empty package marker) | structural |
| `features/stage1.py` | extractor | transform | `features_stage1_twitter.py` | exact |
| `features/stage2.py` | extractor | transform | `features_stage2_twitter.py` | exact |
| `features/stage3.py` | extractor | transform | `features_stage3_twitter.py` + `botdetector_pipeline.py:509-551` | exact |
| `data_io.py` | I/O dispatch | batch | `botsim24_io.py` + `twibot20_io.py` | role-match |
| `botdetector_pipeline.py` (LSTM removal) | pipeline | request-response | self (deletion task) | exact |
| `tests/conftest.py` (fixture removal) | test fixture | — | self (deletion task) | exact |
| `tests/test_features_stage2.py` (import update) | test | — | self (import path change) | exact |
| `tests/test_features_stage1_twitter.py` (import update) | test | — | self (import path change) | exact |
| `tests/test_features_stage2_twitter.py` (import update) | test | — | self (import path change) | exact |
| `tests/test_features_stage3_twitter.py` (import update) | test | — | self (import path change) | exact |

---

## Pattern Assignments

### `features/__init__.py` (package init)

**Analog:** `tests/__init__.py` (empty file, zero bytes)

**Core pattern:** Empty file. The package marker needs no content. Per discretion in CONTEXT.md, re-exporting the three extractor classes is optional — leave empty unless the planner decides to re-export.

```python
# empty — presence of this file makes features/ a package
```

---

### `features/stage1.py` (extractor, transform)

**Analog:** `features_stage1_twitter.py` (primary — class structure with private helpers) and `features_stage1.py` (botsim body to inline)

**Imports pattern** (`features_stage1_twitter.py` lines 1-9, adapted):
```python
from __future__ import annotations

from email.utils import parsedate_to_datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from twibot20_io import parse_tweet_types
```

**Module constants** (`features_stage1_twitter.py` lines 11-12):
```python
_SECONDS_PER_DAY = 86400.0
_EPS = 1e-6
```

**Class attribute — columns constant** (`features_stage1_twitter.py` lines 14-29):
```python
STAGE1_TWITTER_COLUMNS = [
    "screen_name_len",
    "screen_name_digit_ratio",
    "statuses_count",
    "followers_count",
    "friends_count",
    "followers_friends_ratio",
    "account_age_days",
    "statuses_per_day",
    "tweet_count_loaded",
    "domain_count",
    "rt_fraction",
    "mt_fraction",
    "original_fraction",
    "unique_rt_mt_targets",
]
```

**Core class pattern** (synthesized from both analogs — private-method branching per RESEARCH.md):
```python
class Stage1Extractor:
    def __init__(self, dataset: str) -> None:
        if dataset not in {"botsim", "twibot"}:
            raise ValueError(f"unknown dataset: {dataset!r}")
        self.dataset = dataset

    def extract(self, df: pd.DataFrame) -> np.ndarray:
        if self.dataset == "botsim":
            return self._extract_botsim(df)
        return self._extract_twibot(df)
```

**BotSim body** (`features_stage1.py` lines 5-40 — copy verbatim as `_extract_botsim`):
```python
def _extract_botsim(self, df: pd.DataFrame) -> np.ndarray:
    name_len = df["username"].fillna("").astype(str).map(len).to_numpy(dtype=np.float32)
    post_num = df["submission_num"].to_numpy(dtype=np.float32)
    c1 = df["comment_num_1"].to_numpy(dtype=np.float32)
    c2 = df["comment_num_2"].to_numpy(dtype=np.float32)
    c_total = c1 + c2
    sr_num = df["subreddit_list"].map(lambda x: len(x) if isinstance(x, list) else 0).to_numpy(dtype=np.float32)
    eps = 1e-6
    post_c1 = post_num / (c1 + eps)
    post_c2 = post_num / (c2 + eps)
    post_ct = post_num / (c_total + eps)
    post_sr = post_num / (sr_num + eps)
    X = np.stack([name_len, post_num, c1, c2, c_total, sr_num, post_c1, post_c2, post_ct, post_sr], axis=1)
    return np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
```

**TwiBot body** (`features_stage1_twitter.py` lines 72-132 — copy verbatim as `_extract_twibot`):
- The full body of `extract_stage1_matrix_twitter` moves here unchanged, with `reference_time` as a parameter to `_extract_twibot(self, df, reference_time=None)`. The public `extract(df)` signature stays as `extract(df, reference_time=None)` to forward the kwarg.

**Private helpers** (`features_stage1_twitter.py` lines 32-69 — copy verbatim):
```python
def _safe_account_age_days(self, created_at: Any, reference_time: pd.Timestamp | None) -> float:
    # exact body from features_stage1_twitter._safe_account_age_days

def _tweet_breakdown(self, messages: List[Dict[str, Any]]) -> Dict[str, float]:
    # exact body from features_stage1_twitter._tweet_breakdown
```

Note: `_tweet_breakdown` calls `parse_tweet_types` imported from `twibot20_io` — that import must be kept at module top level.

**Output contracts:**
- botsim: `[N, 10]` float32 — 10 columns stacked via `np.stack`
- twibot: `[N, 14]` float32 — 14 columns in `STAGE1_TWITTER_COLUMNS` order
- Both paths end with `np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)`
- Empty twibot DataFrame returns `np.zeros((0, 14), dtype=np.float32)`

---

### `features/stage2.py` (extractor, transform)

**Analog:** `features_stage2_twitter.py` (primary — cleaner private-helper structure) and `features_stage2.py` (botsim body to inline)

**Imports pattern** (`features_stage2_twitter.py` lines 1-7, adapted):
```python
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd
```

**Module constants** (`features_stage2.py` lines 10-11 and `features_stage2_twitter.py` lines 8-9):
```python
_NEAR_DUP_SIM_THRESHOLD = 0.9
_MISSING_TEMPORAL_SENTINEL = -1.0   # botsim path only — marks "messages exist but timestamps absent"
```

**Column constants** (`features_stage2_twitter.py` lines 10-15):
```python
STAGE2_TWITTER_EMBEDDING_DIM = 384
STAGE2_TWITTER_COLUMNS = (
    [f"emb_{idx}" for idx in range(STAGE2_TWITTER_EMBEDDING_DIM)]
    + ["char_len_mean", "token_uniq_ratio_mean", "punct_ratio_mean", "digit_ratio_mean"]
    + ["message_count", "char_len_std", "cross_msg_sim_mean", "near_dup_frac", "nonempty_frac"]
)
```

**Core class pattern:**
```python
class Stage2Extractor:
    def __init__(self, dataset: str) -> None:
        if dataset not in {"botsim", "twibot"}:
            raise ValueError(f"unknown dataset: {dataset!r}")
        self.dataset = dataset

    def extract(self, df: pd.DataFrame, embedder) -> np.ndarray:
        if self.dataset == "botsim":
            return self._extract_botsim(df, embedder)
        return self._extract_twibot(df, embedder)
```

**BotSim body** (`features_stage2.py` lines 28-137 — copy verbatim as `_extract_botsim`):
- `probe_dim = None` initialization is outside the row loop (must be preserved exactly — see Pitfall 5 in RESEARCH.md)
- `_MISSING_TEMPORAL_SENTINEL` used in five positions: `rate`, `delta_mean`, `delta_std`, `cv_intervals`, `hour_entropy` when `temporal_missing` is True
- Returns `np.stack(rows, axis=0)` — no empty-case guard (botsim always has rows in practice; the twitter path has an explicit guard)

**TwiBot body** (`features_stage2_twitter.py` lines 39-114 — copy verbatim as `_extract_twibot`):
- Empty-case guard: `if not rows: return np.zeros((0, len(STAGE2_TWITTER_COLUMNS)), dtype=np.float32)`
- `probe_dim` initialization pattern identical to botsim but falls back to `STAGE2_TWITTER_EMBEDDING_DIM`
- No temporal features — omits `_MISSING_TEMPORAL_SENTINEL` entirely

**Private helpers** (`features_stage2_twitter.py` lines 18-36):
```python
def _simple_linguistic_features(self, text: str) -> np.ndarray:
    # exact body from features_stage2_twitter._simple_linguistic_features

def _select_texts(self, messages: List[Dict[str, Any]], max_msgs: int, max_chars: int) -> List[str]:
    # exact body from features_stage2_twitter._select_texts
```

Note: `_simple_linguistic_features` also exists in `features_stage2.py` as a module-level function (`simple_linguistic_features`) — the botsim body calls `simple_linguistic_features(...)` directly. When inlined as a class method, both `_extract_botsim` and `_extract_twibot` should call `self._simple_linguistic_features(...)`.

**AMR extraction** (`botdetector_pipeline.py` lines 141-169 — move into this class as `extract_amr`):
```python
def extract_amr(self, df: pd.DataFrame, embedder) -> np.ndarray:
    # exact body of extract_amr_embeddings_for_accounts, minus the cfg parameter
    # max_chars defaults to 500 (cfg.max_chars_per_message was 500)
```

**Output contracts:**
- botsim: `[N, 397]` float32 — layout documented in `tests/test_features_stage2.py` lines 12-23
- twibot: `[N, 393]` float32 — column list in `STAGE2_TWITTER_COLUMNS` (384 + 4 + 5 = 393)

---

### `features/stage3.py` (extractor, transform)

**Analog:** `features_stage3_twitter.py` (wrapper class pattern) + `botdetector_pipeline.py` lines 509-551 (graph builder body)

**Imports pattern** (`features_stage3_twitter.py` lines 1-4, adapted — no pipeline import):
```python
from __future__ import annotations

import numpy as np
import pandas as pd
```

**Constants** (`features_stage3_twitter.py` lines 8-33 — copy verbatim):
```python
STAGE3_TWITTER_COLUMNS = [
    "in_deg", "out_deg", "deg_total", "in_w", "out_w", "w_total",
    "following_in_deg", "following_out_deg", "following_in_w", "following_out_w",
    "follower_in_deg", "follower_out_deg", "follower_in_w", "follower_out_w",
    "type2_in_deg", "type2_out_deg", "type2_in_w", "type2_out_w",
]

TWITTER_NATIVE_EDGE_TYPES = {
    0: "following",
    1: "follower",
}
```

**Graph builder function** (`botdetector_pipeline.py` lines 509-551 — copy verbatim, no changes):
```python
def build_graph_features_nodeidx(
    accounts_df: pd.DataFrame,
    edges_df: pd.DataFrame,
    num_nodes_total: int,
    n_types: int = 3
) -> np.ndarray:
    node_ids = accounts_df["node_idx"].to_numpy(dtype=np.int32)
    src = edges_df["src"].to_numpy(dtype=np.int32)
    dst = edges_df["dst"].to_numpy(dtype=np.int32)
    w   = edges_df["weight"].to_numpy(dtype=np.float32)
    et  = edges_df["etype"].to_numpy(dtype=np.int8)

    in_deg  = np.zeros(num_nodes_total, dtype=np.float32)
    out_deg = np.zeros(num_nodes_total, dtype=np.float32)
    in_w    = np.zeros(num_nodes_total, dtype=np.float32)
    out_w   = np.zeros(num_nodes_total, dtype=np.float32)

    np.add.at(out_deg, src, 1.0)
    np.add.at(in_deg,  dst, 1.0)
    np.add.at(out_w,   src, w)
    np.add.at(in_w,    dst, w)

    feats = [in_deg, out_deg, in_deg + out_deg, in_w, out_w, in_w + out_w]

    for t in range(n_types):
        mask = (et == t)
        in_d_t  = np.zeros(num_nodes_total, dtype=np.float32)
        out_d_t = np.zeros(num_nodes_total, dtype=np.float32)
        in_w_t  = np.zeros(num_nodes_total, dtype=np.float32)
        out_w_t = np.zeros(num_nodes_total, dtype=np.float32)
        np.add.at(out_d_t, src[mask], 1.0)
        np.add.at(in_d_t,  dst[mask], 1.0)
        np.add.at(out_w_t, src[mask], w[mask])
        np.add.at(in_w_t,  dst[mask], w[mask])
        feats.extend([in_d_t, out_d_t, in_w_t, out_w_t])

    X_all = np.stack(feats, axis=1)
    return X_all[node_ids]
```

**Core class pattern** (wraps the builder, modeled on `features_stage3_twitter.extract_stage3_features_twitter`):
```python
class Stage3Extractor:
    def __init__(self, dataset: str) -> None:
        if dataset not in {"botsim", "twibot"}:
            raise ValueError(f"unknown dataset: {dataset!r}")
        self.dataset = dataset

    def extract(
        self,
        accounts_df: pd.DataFrame,
        edges_df: pd.DataFrame,
        num_nodes_total: int | None = None,
    ) -> np.ndarray:
        # num_nodes_total handling from features_stage3_twitter lines 49-53:
        if num_nodes_total is None:
            if len(accounts_df) == 0:
                num_nodes_total = 0
            else:
                num_nodes_total = int(accounts_df["node_idx"].max()) + 1
        return np.asarray(
            build_graph_features_nodeidx(accounts_df, edges_df, num_nodes_total, n_types=3),
            dtype=np.float32,
        )
```

Note: `build_graph_features_nodeidx` must be defined as a module-level function (not only a method) so `botdetector_pipeline.py` can import it directly: `from features.stage3 import build_graph_features_nodeidx`. This is required per RESEARCH.md symbol inventory and Pitfall 2.

**Output contract:**
- `[N, 18]` float32 for twibot with `n_types=3` — `STAGE3_TWITTER_COLUMNS` has 18 entries
- Formula: `6 + 4 * n_types` columns total

---

### `data_io.py` (I/O dispatch, batch)

**Analog:** `botsim24_io.py` (public function signatures to re-expose) + `twibot20_io.py` (public function signatures to re-expose)

**Imports pattern:**
```python
from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from botsim24_io import load_users_csv, load_user_post_comment_json, build_account_table
from twibot20_io import load_accounts, build_edges, validate
```

**Core dispatch pattern** (D-08 from CONTEXT.md):
```python
def load_dataset(dataset: str, **kwargs) -> Dict[str, Any]:
    if dataset == "botsim":
        return _load_botsim(**kwargs)
    if dataset == "twibot":
        return _load_twibot(**kwargs)
    raise ValueError(f"unknown dataset: {dataset!r}")
```

**BotSim internal loader** (wraps `botsim24_io` public API per D-09):
```python
def _load_botsim(
    users_csv_path: str,
    upc_json_path: str,
) -> Dict[str, Any]:
    users_df = load_users_csv(users_csv_path)
    upc = load_user_post_comment_json(upc_json_path)
    accounts_df = build_account_table(users_df, upc)
    return {"accounts_df": accounts_df}
```

**TwiBot internal loader** (wraps `twibot20_io` public API per D-09):
```python
def _load_twibot(
    json_path: str,
    run_validate: bool = False,
) -> Dict[str, Any]:
    accounts_df = load_accounts(json_path)
    edges_df = build_edges(accounts_df, json_path)
    if run_validate:
        validate(accounts_df, edges_df)
    return {"accounts_df": accounts_df, "edges_df": edges_df}
```

Note: `botsim24_io.py` and `twibot20_io.py` are NOT deleted in Phase 17. Their full logic stays in place; `data_io.py` imports and wraps their public functions only. Exact kwarg names for `_load_botsim` and `_load_twibot` are at implementer's discretion — they must cover the same parameters the old loaders required.

---

### `botdetector_pipeline.py` (LSTM removal, modification)

**Analog:** Self — this is a targeted deletion task.

**Symbols to delete** (exact line ranges from RESEARCH.md):

| Symbol | Lines (approx) | Deletion scope |
|--------|----------------|----------------|
| `extract_message_embedding_sequences_for_accounts` | 172-216 | full function |
| `_Stage2LSTMNet` | 372-391 | full class |
| `Stage2LSTMRefiner` | 394-460 | full class |
| `normalize_stage2b_variant` | 666-670 | full function |
| `apply_stage2b_refiner` | 673-707 | full function |
| `TrainedSystem.stage2b_lstm` field | line 662 | one field line |
| `TrainedSystem.stage2b_variant` field | line 663 | one field line |

**TrainedSystem before** (`botdetector_pipeline.py` lines 649-663):
```python
@dataclass
class TrainedSystem:
    cfg: FeatureConfig
    th: StageThresholds
    embedder: TextEmbedder
    stage1: Stage1MetadataModel
    stage2a: Stage2BaseContentModel
    amr_refiner: Optional[AMRDeltaRefiner]
    meta12: LogisticRegression
    stage3: Stage3StructuralModel
    meta123: LogisticRegression
    stage2b_lstm: Optional[Stage2LSTMRefiner] = None   # DELETE
    stage2b_variant: str = "amr"                       # DELETE
```

**TrainedSystem after** (last two fields removed — all others unchanged):
```python
@dataclass
class TrainedSystem:
    cfg: FeatureConfig
    th: StageThresholds
    embedder: TextEmbedder
    stage1: Stage1MetadataModel
    stage2a: Stage2BaseContentModel
    amr_refiner: Optional[AMRDeltaRefiner]
    meta12: LogisticRegression
    stage3: Stage3StructuralModel
    meta123: LogisticRegression
```

**`apply_stage2b_refiner` call sites to inline** (RESEARCH.md Pitfall 7). Both `train_system` and `predict_system` call `apply_stage2b_refiner`. Replace each call with:
```python
# inline replacement for apply_stage2b_refiner (AMR-only after LSTM removal)
h_amr = extract_amr_embeddings_for_accounts(df[route_mask], cfg, embedder)
z2[route_mask] = amr_refiner.refine(z2[route_mask], h_amr)
```

**Imports to clean** from `botdetector_pipeline.py` top-level (lines 1-31): Remove torch/nn imports if they were only used by LSTM classes. The `try/except` torch block (lines 16-25) existed for LSTM only — it can be removed. Verify `HAS_TORCH` is not used elsewhere after deletion.

---

### `main.py` (LSTM import cleanup, modification)

**Analog:** Self — import cleanup task.

**Imports to remove** (`main.py` lines 11-29):
```python
# DELETE these three from the botdetector_pipeline import block:
Stage2LSTMRefiner,
apply_stage2b_refiner,
extract_message_embedding_sequences_for_accounts,
```

**Usage sites in main.py** to remove or replace: grep for `Stage2LSTMRefiner`, `apply_stage2b_refiner`, `extract_message_embedding_sequences_for_accounts` in the file body and remove/replace per the AMR-inline pattern above.

---

### `tests/conftest.py` (fixture removal, modification)

**Analog:** Self — targeted deletion.

**Symbols to remove:**

1. Import of `Stage2LSTMRefiner` and `extract_message_embedding_sequences_for_accounts` from the `botdetector_pipeline` import block (lines 21-41):
```python
# DELETE from import block:
Stage2LSTMRefiner,
extract_message_embedding_sequences_for_accounts,
```

2. Delete entire `minimal_lstm_stage2b_inputs` fixture (lines 271-293):
```python
@pytest.fixture
def minimal_lstm_stage2b_inputs(minimal_system):
    """..."""
    # entire fixture body — DELETE
```

**`minimal_system` fixture** (lines 130-268): The `TrainedSystem(...)` construction at lines 256-266 passes no `stage2b_lstm` or `stage2b_variant` keyword args (they default to `None` and `"amr"`). After the dataclass fields are removed, the construction call remains valid as-is — no change needed to `minimal_system` body itself.

---

### Test files — import path updates

These are mechanical find-and-replace tasks. Pattern: old import -> new import.

**`tests/test_features_stage2.py`** (line 30):
```python
# OLD:
from features_stage2 import extract_stage2_features
# NEW:
from features.stage2 import Stage2Extractor
```
All calls `extract_stage2_features(df, embedder)` become `Stage2Extractor('botsim').extract(df, embedder)`.

**`tests/test_features_stage1_twitter.py`** (lines 4-7):
```python
# OLD:
from features_stage1_twitter import (
    STAGE1_TWITTER_COLUMNS,
    extract_stage1_matrix_twitter,
)
# NEW:
from features.stage1 import Stage1Extractor, STAGE1_TWITTER_COLUMNS
```
All calls `extract_stage1_matrix_twitter(df, reference_time=...)` become `Stage1Extractor('twibot').extract(df, reference_time=...)`.

**`tests/test_features_stage2_twitter.py`** (analogous to stage2 above):
```python
# OLD:
from features_stage2_twitter import extract_stage2_features_twitter, STAGE2_TWITTER_COLUMNS
# NEW:
from features.stage2 import Stage2Extractor, STAGE2_TWITTER_COLUMNS
```

**`tests/test_features_stage3_twitter.py`** (lines 4-7):
```python
# OLD:
from features_stage3_twitter import (
    STAGE3_TWITTER_COLUMNS,
    extract_stage3_features_twitter,
)
# NEW:
from features.stage3 import Stage3Extractor, STAGE3_TWITTER_COLUMNS, build_graph_features_nodeidx
```
All calls `extract_stage3_features_twitter(accounts_df, edges_df)` become `Stage3Extractor('twibot').extract(accounts_df, edges_df)`.

---

## Shared Patterns

### Dataset validation guard
**Apply to:** `Stage1Extractor.__init__`, `Stage2Extractor.__init__`, `Stage3Extractor.__init__`
**Source:** Synthesized from RESEARCH.md architectural pattern (lines 144-148)
```python
if dataset not in {"botsim", "twibot"}:
    raise ValueError(f"unknown dataset: {dataset!r}")
self.dataset = dataset
```

### probe_dim initialization (float32 embedding fallback)
**Apply to:** `Stage2Extractor._extract_botsim` and `Stage2Extractor._extract_twibot`
**Source:** `features_stage2.py` lines 35-76 and `features_stage2_twitter.py` lines 59-76
**Critical:** Do not simplify to a fixed constant — this pattern handles the edge case where all rows have empty message lists in test DataFrames.
```python
probe_dim = None
# ... inside row loop:
if nonempty_texts:
    embeddings = embedder.encode(nonempty_texts)
    if probe_dim is None:
        probe_dim = int(embeddings.shape[1])
    emb_pool = embeddings.mean(axis=0).astype(np.float32)
else:
    if probe_dim is None:
        probe_dim = 384   # or STAGE2_TWITTER_EMBEDDING_DIM for twibot
    emb_pool = np.zeros(probe_dim, dtype=np.float32)
```

### nan_to_num output sanitization
**Apply to:** Both paths in `Stage1Extractor`
**Source:** `features_stage1.py` line 39, `features_stage1_twitter.py` line 131
```python
return np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
```

### Missing-timestamp sentinel
**Apply to:** `Stage2Extractor._extract_botsim` only — twibot path has no timestamps
**Source:** `features_stage2.py` lines 11, 97-130
```python
_MISSING_TEMPORAL_SENTINEL = -1.0
# used when: len(messages) > 0 and len(ts) == 0 (messages exist but timestamps absent)
temporal_missing = len(messages) > 0 and len(ts) == 0
if temporal_missing:
    rate = _MISSING_TEMPORAL_SENTINEL
    delta_mean = _MISSING_TEMPORAL_SENTINEL
    delta_std = _MISSING_TEMPORAL_SENTINEL
    cv_intervals = _MISSING_TEMPORAL_SENTINEL
    hour_entropy = _MISSING_TEMPORAL_SENTINEL
```

### from __future__ import annotations
**Apply to:** All new Python files in `features/` and `data_io.py`
**Source:** `features_stage1_twitter.py` line 1, `features_stage2_twitter.py` line 1, `features_stage3_twitter.py` line 1, `twibot20_io.py` line 3
```python
from __future__ import annotations
```

### Comment style (D-11)
**Apply to:** All new and modified files
**Rule:** Comments are lowercase, explain the why, used sparingly. No docstrings with "Returns" / "Parameters" sections unless the function is exported public API.
**Source:** CONTEXT.md D-11; examples in `features_stage2.py` lines 59, 84-88 (`# keep last max_msgs`, `# When tweets exist but all timestamps are unavailable, use a dedicated sentinel...`)

---

## New Test Files Required (no analog exists yet)

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `tests/test_features_stage1.py` | test | transform | Covers `Stage1Extractor` botsim + twibot paths (CORE-01). No existing analog — Wave 0 gap. |
| `tests/test_data_io.py` | test | batch | Covers `load_dataset` dispatch for both datasets (CORE-01). No existing analog — Wave 0 gap. |
| `tests/test_lstm_removed.py` | test | — | Covers CORE-05: verifies `Stage2LSTMRefiner` raises `ImportError`, `TrainedSystem` has no LSTM fields. No existing analog — Wave 0 gap. |

For these new test files, model structure after `tests/test_features_stage1_twitter.py`:
- One `_account(...)` or `_make_df(...)` helper at module level that builds minimal test DataFrames
- Test functions named `test_<feature>_<condition>()` with a single `assert` per behavior
- `FakeEmbedder` / `NormalizedFakeEmbedder` pattern (copy from `tests/conftest.py` lines 46-68) rather than loading real sentence-transformers

---

## Metadata

**Analog search scope:** project root `*.py`, `tests/*.py`
**Files read:** `features_stage1.py`, `features_stage1_twitter.py`, `features_stage2.py`, `features_stage2_twitter.py`, `features_stage3_twitter.py`, `botdetector_pipeline.py` (lines 1-130, 130-260, 320-600, 640-720), `botsim24_io.py`, `twibot20_io.py`, `main.py`, `tests/conftest.py`, `tests/test_features_stage2.py`, `tests/test_features_stage1_twitter.py`, `tests/test_features_stage3_twitter.py`
**Pattern extraction date:** 2026-04-18
