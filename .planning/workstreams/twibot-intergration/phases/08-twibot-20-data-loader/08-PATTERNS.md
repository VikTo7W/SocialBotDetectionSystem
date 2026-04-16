# Phase 8: TwiBot-20 Data Loader - Pattern Map

**Mapped:** 2026-04-16
**Files analyzed:** 2 (1 new source file + 1 new test file)
**Analogs found:** 2 / 2

---

## File Classification

| New File | Role | Data Flow | Closest Analog | Match Quality |
|----------|------|-----------|----------------|---------------|
| `twibot20_io.py` | utility / data-loader | file-I/O + transform | `botsim24_io.py` | exact (same role, same data flow, same output schema) |
| `tests/test_twibot20_io.py` | test | request-response (unit) | `tests/test_botsim24_io.py` + `tests/test_features_stage2.py` | exact (same project test conventions) |

---

## Pattern Assignments

### `twibot20_io.py` (data-loader, file-I/O + transform)

**Analog:** `botsim24_io.py`

---

**Imports pattern** (`botsim24_io.py` lines 2-10):
```python
from __future__ import annotations

import ast
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

import numpy as np
import pandas as pd
```

For `twibot20_io.py` the minimal required subset is (per RESEARCH.md — no datetime parsing needed):
```python
from __future__ import annotations

import json
from typing import Any, Dict, List

import numpy as np
import pandas as pd
```

---

**Core loader function pattern** (`botsim24_io.py` lines 100-183):

The `build_account_table` function is the structural template. Key conventions extracted:

```python
# Pattern: path-as-parameter, json.load, enumerate rows, append dicts, pd.DataFrame(rows)
def build_account_table(users_df: pd.DataFrame, upc: Dict[str, Any]) -> pd.DataFrame:
    rows = []
    for _, u in users_df.iterrows():
        uid = str(u["user_id"])
        entry = upc.get(uid, {})
        posts = entry.get("posts", []) or []   # <- "or []" guard for None

        messages = []
        for p in posts:
            txt = (p.get("posts") or "").strip()
            ts = _to_unix_seconds(p.get("created_utc", ""))
            if txt:
                messages.append({
                    "text": txt,
                    "ts": ts,
                    "kind": "post",          # <- explicit "kind" field
                    ...
                })

        rows.append({
            "label": int(u["label"]),        # <- label cast to int inline
            "messages": messages,
            ...
        })

    return pd.DataFrame(rows)
```

For `twibot20_io.py`, `load_accounts(path)` replaces this. The function reads a single JSON file
and iterates its records directly. The `or []` guard and `int(label)` inline cast are required
(D-01, D-08). The `kind` field is `"tweet"` (D-01). `ts=None` always (D-01):

```python
# Adapt of build_account_table pattern for single-JSON source:
def load_accounts(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rows = []
    for idx, record in enumerate(data):
        profile = record["profile"]
        tweets = record.get("tweet") or []                           # Pitfall 2 guard
        messages = [
            {"text": str(t), "ts": None, "kind": "tweet"}           # D-01
            for t in tweets if t
        ]
        rows.append({
            "node_idx": np.int32(idx),                               # D-04
            "screen_name": str(profile.get("screen_name", "") or "").strip(),  # Pitfall 1
            "statuses_count":  int(str(profile.get("statuses_count",  0) or 0).strip() or 0),
            "followers_count": int(str(profile.get("followers_count", 0) or 0).strip() or 0),
            "friends_count":   int(str(profile.get("friends_count",   0) or 0).strip() or 0),
            "created_at": str(profile.get("created_at", "") or "").strip(),    # D-02
            "messages": messages,
            "label": int(record["label"]),                           # D-08
        })
    df = pd.DataFrame(rows)
    df["node_idx"] = df["node_idx"].astype(np.int32)
    return df
```

**Note — DO NOT sort messages by ts** (contrast with `botsim24_io.py` lines 163-165 which do
`messages.sort(key=lambda m: m["ts"])`). For TwiBot-20, all `ts=None`; sorting is neither
possible nor needed. Insert messages in tweet-list order.

---

**Dtype enforcement pattern** (`botsim24_io.py` lines 68-70 in `load_users_csv`):
```python
# After DataFrame construction, enforce column dtypes in bulk
df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(np.float32)
```

For `edges_df`, the equivalent pattern using numpy arrays (preferred per RESEARCH.md):
```python
return pd.DataFrame({
    "src":    np.array(srcs,    dtype=np.int32),
    "dst":    np.array(dsts,    dtype=np.int32),
    "etype":  np.array(etypes,  dtype=np.int8),
    "weight": np.array(weights, dtype=np.float32),
})
```

---

**No-analog section — edge builder with ID remapping:**

There is no existing analog in the codebase for `build_edges()` (no other function does
string-ID → node_idx remapping + directed edge construction). Use RESEARCH.md Pattern 2
as the implementation template (lines 182-212 of 08-RESEARCH.md), verified against
`botdetector_pipeline.py`'s `build_graph_features_nodeidx` dtype expectations.

Key facts from data inspection (RESEARCH.md Code Examples):
- 154 in-set edges out of 20,814 total neighbor refs (0.7% retention)
- 116 etype-0 (following) edges, 38 etype-1 (follower) edges
- `record["ID"]` is the correct lookup key (equals `profile["id_str"].strip()`)
- Guard for empty `edges_df`: `if len(edges_df) > 0:` before `.max()` calls (Pitfall 5)

---

**Validation function pattern — print() style** (`botsim24_io.py` has no validate function;
the print() convention is established by `evaluate.py` and consistent with D-03):

```python
# No existing validate() analog in botsim24_io.py.
# Use print() per D-03 (consistent with codebase — no logging module used anywhere).
# Pattern: assert + print fraction
def validate(accounts_df: pd.DataFrame, edges_df: pd.DataFrame) -> None:
    required_cols = [...]
    missing = [c for c in required_cols if c not in accounts_df.columns]
    assert not missing, f"Missing columns: {missing}"
    n = len(accounts_df)
    if len(edges_df) > 0:                                 # Pitfall 5 guard
        assert int(edges_df["src"].max()) < n
        assert int(edges_df["dst"].max()) < n
    no_tweet_frac = accounts_df["messages"].map(len).eq(0).mean()
    print(f"[twibot20] accounts: {n}, edges: {len(edges_df)}")
    print(f"[twibot20] no-tweet fraction: {no_tweet_frac:.3f}")
```

For the no-neighbor fraction, the simplest correct approach is to store a module-level
variable `_no_neighbor_count` set inside `load_accounts()` and read it in `validate()`.
This avoids re-reading the file and avoids adding a column to `accounts_df`.

---

### `tests/test_twibot20_io.py` (test, unit)

**Primary analog:** `tests/test_botsim24_io.py`
**Secondary analog:** `tests/test_features_stage2.py`

---

**Module docstring + imports pattern** (`tests/test_botsim24_io.py` lines 1-9):
```python
"""
Tests for LEAK-04: character_setting must not appear in build_account_table output.
"""

import pandas as pd
import numpy as np
import pytest

from botsim24_io import build_account_table
```

For `test_twibot20_io.py`:
```python
"""
Tests for Phase 8: TwiBot-20 data loader.

Requirements covered:
  - TW-01: load_accounts() returns BotSim-24-compatible accounts_df
  - TW-02: build_edges() returns typed edges_df with in-set-only remapped IDs
  - TW-03: validate() asserts edge bounds and prints diagnostic fractions
"""

import json
import os
import tempfile

import numpy as np
import pandas as pd
import pytest

from twibot20_io import load_accounts, build_edges, validate
```

---

**Synthetic fixture pattern** (`tests/conftest.py` lines 62-101 and `tests/test_botsim24_io.py`
lines 14-40):

`test_botsim24_io.py` builds minimal in-memory DataFrames inline per test (no fixtures).
`conftest.py` uses a `_make_synthetic_dataframe` helper for heavier state.

For `test_twibot20_io.py`, the correct pattern is inline `tmp_path`-based fixture writing
(pytest built-in) to avoid coupling to the real `test.json` file on disk. Each test that
exercises file I/O writes a minimal JSON to a temp file:

```python
# Pattern: write minimal JSON to tmp_path, pass path to loader
def _write_test_json(records: list, tmp_path) -> str:
    path = os.path.join(str(tmp_path), "test.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f)
    return path

def _make_record(id_: str, screen_name: str, label: str = "0",
                 tweets=None, neighbor=None) -> dict:
    """Minimal valid TwiBot-20 record."""
    return {
        "ID": id_,
        "profile": {
            "screen_name": screen_name + " ",   # trailing space (Pitfall 1)
            "statuses_count": "10 ",
            "followers_count": "5 ",
            "friends_count": "3 ",
            "created_at": "Mon Apr 23 09:47:10 +0000 2012 ",
            "id_str": id_ + " ",
        },
        "tweet": tweets,
        "neighbor": neighbor,
        "domain": [],
        "label": label,
    }
```

---

**Test structure pattern** (`tests/test_features_stage2.py` lines 87-99):

Each test function is short, self-contained, names the requirement it covers, and uses a
clear assertion message:

```python
def test_no_identity_in_embeddings():
    """USERNAME:/PROFILE: strings must not be passed to the embedder."""
    rec = RecordingEmbedder()
    df = _make_single_account_df(...)
    extract_stage2_features(df, rec)
    flat = " ".join(rec.recorded_texts)
    assert "USERNAME:" not in flat, "Found 'USERNAME:' in encoded texts"
```

For `test_twibot20_io.py`, follow the same structure:
```python
def test_load_accounts_schema(tmp_path):
    """load_accounts() must return DataFrame with all 8 required columns."""
    path = _write_test_json([_make_record("001", "alice", label="0")], tmp_path)
    df = load_accounts(path)
    for col in ["node_idx", "screen_name", "statuses_count", "followers_count",
                "friends_count", "created_at", "messages", "label"]:
        assert col in df.columns, f"Missing required column: {col}"
```

---

**Edge case test pattern** (`tests/test_botsim24_io.py` lines 11-40 and
`tests/test_features_stage2.py` lines 126-133):

Tests for None/empty inputs are first-class tests, not afterthoughts:
```python
def test_amr_zero_for_no_messages():
    """Accounts with no messages must produce an all-zero AMR embedding."""
    rec = RecordingEmbedder()
    df = _make_single_account_df(messages=[])
    ...
    assert np.allclose(result[0], 0.0), "Zero-message account must yield zero AMR vector"
```

Map of edge case tests required for `test_twibot20_io.py` (from RESEARCH.md Validation
Architecture table, lines 421-430):

| Test name | What it exercises | Pitfall covered |
|-----------|-------------------|-----------------|
| `test_null_tweet_handled` | `tweet=None` → empty messages list | Pitfall 2 |
| `test_null_neighbor_no_rows` | `neighbor=None` → no edge rows | D-06 |
| `test_edges_in_set_only` | cross-set IDs dropped | D-06 |
| `test_validate_bounds_fail` | `AssertionError` when src.max() >= n | Pitfall 5 / D-07 |
| `test_trailing_whitespace_stripped` | screen_name has no trailing space | Pitfall 1 |

---

## Shared Patterns

### ts=None guard
**Source:** `features_stage2.py` line 49
**Apply to:** `twibot20_io.py` (context only — no guard needed in the loader itself, but
confirms the downstream consumer handles `ts=None` messages correctly)
```python
if m.get("ts") is not None:
    ts.append(float(m["ts"]))
```
All TwiBot-20 messages will have `ts=None`; they are included in embedding but excluded
from all temporal feature computations. No special handling needed in the loader.

### label cast to int inline
**Source:** `botsim24_io.py` line 181
**Apply to:** `twibot20_io.py` `load_accounts()`
```python
"label": int(u["label"]),
```
TwiBot-20 labels are strings `"0"` / `"1"` in JSON (D-08). Same `int()` cast applies.

### "or []" guard for None lists
**Source:** `botsim24_io.py` lines 113-114
**Apply to:** `twibot20_io.py` — tweet list AND neighbor following/follower lists
```python
posts = entry.get("posts", []) or []
```
Equivalent in twibot20_io.py:
```python
tweets = record.get("tweet") or []
for nid in (neighbor.get("following") or []):
```

### print() for diagnostic output (no logging module)
**Source:** Established codebase convention; confirmed by `evaluate.py` and D-03
**Apply to:** `twibot20_io.py` `validate()` function
No `import logging`. Use `print(f"[twibot20] ...")` with bracketed prefix matching the
module name, consistent with how `evaluate.py` outputs results.

### Defensive `.get(key, default)` for all profile fields
**Source:** `botsim24_io.py` lines 119-160 (all `entry.get(...)` calls)
**Apply to:** `twibot20_io.py` `load_accounts()` — all `profile.get(...)` calls
```python
profile.get("screen_name", "")
profile.get("statuses_count", 0)
```
Numeric fields default to `0` (Claude's Discretion — consistent with botsim24_io.py).

---

## No Analog Found

| File | Role | Data Flow | Reason |
|------|------|-----------|--------|
| `build_edges()` function inside `twibot20_io.py` | utility | transform | No existing function in the codebase performs string-Twitter-ID → node_idx remapping or directed edge construction from neighbor lists. Use RESEARCH.md Pattern 2 (lines 182-212) as the implementation template. |

---

## Metadata

**Analog search scope:** All `.py` files in repo root and `tests/`
**Files scanned:** 15 (all `.py` files in project)
**Key files read:**
- `/botsim24_io.py` — primary structural analog for `twibot20_io.py`
- `/tests/test_botsim24_io.py` — primary test structure analog
- `/tests/test_features_stage2.py` — secondary test structure analog (edge case patterns)
- `/tests/conftest.py` — shared fixture patterns, `_make_synthetic_dataframe` helper style
- `/features_stage2.py` lines 1-80 — ts=None guard at line 49 confirmed
**Pattern extraction date:** 2026-04-16
