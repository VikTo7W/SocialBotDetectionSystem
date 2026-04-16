# Phase 8: TwiBot-20 Data Loader - Research

**Researched:** 2026-04-16
**Domain:** Data loading, schema mapping, graph edge construction (Python/pandas/numpy)
**Confidence:** HIGH

---

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Each tweet stored as `{"text": str, "ts": None, "kind": "tweet"}` — full schema-compatible dict matching `botsim24_io.py` message format. Stage 2 feature extractor handles `ts=None` via `if m.get("ts") is not None`.
- **D-02:** Store `created_at` as a raw string exactly as it appears in `profile["created_at"]` (Twitter format, e.g. `"Mon Apr 23 09:47:10 +0000 2012 "`). No parsing.
- **D-03:** Use `print()` statements for validation output — consistent with existing codebase.
- **D-04:** `accounts_df` columns: `node_idx` (int32, 0-indexed by row), `screen_name`, `statuses_count`, `followers_count`, `friends_count`, `created_at`, `messages`, `label` (int, 0 or 1).
- **D-05:** `edges_df` schema: `{src: int32, dst: int32, etype: int8, weight: float32}` — `"following"` → etype 0, `"follower"` → etype 1, weight = `log1p(1.0)` for all edges; accounts with `neighbor: None` contribute no rows.
- **D-06:** ID remapping: string Twitter IDs from `neighbor.following` / `neighbor.follower` remapped to zero-indexed `node_idx` integers using only IDs present in the evaluation set; IDs not in the set are silently dropped.
- **D-07:** Validation asserts: `edges_df["src"].max() < len(accounts_df)` and `edges_df["dst"].max() < len(accounts_df)`; prints no-neighbor fraction and no-tweet fraction.
- **D-08:** Label parsing: `record["label"]` is string `"0"` or `"1"` → cast to `int` inline.

### Claude's Discretion

- Internal ID→node_idx mapping implementation (dict lookup is fine).
- How to handle profiles with missing/None values for `statuses_count`, `followers_count`, `friends_count` (default to 0 or None).
- Whether `validate()` is a standalone function or a method — standalone is consistent with `botsim24_io.py` pattern.

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| TW-01 | Load TwiBot-20 accounts from `test.json` into a BotSim-24-compatible DataFrame — profile fields mapped to metadata columns, tweet list used as messages, label parsed as int, node_idx (int32, 0-indexed) assigned by row | Data inspection confirmed field types, whitespace quirks, and None patterns; `botsim24_io.py` provides exact structural template |
| TW-02 | Build `edges_df` from `neighbor.following` / `neighbor.follower` — string IDs remapped to node_idx, etype 0/1, weight `log1p(1.0)`, `neighbor: None` → no rows; schema `{src: int32, dst: int32, etype: int8, weight: float32}` | Data inspection confirms 154 in-set edges from 20,814 total neighbor refs; edge construction logic verified against `build_graph_features_nodeidx` expectations |
| TW-03 | Validate data integrity — assert edge bounds, log no-neighbor and no-tweet fractions | Confirmed 109/1183 no-neighbor (9.2%), 10/1183 no-tweet (tweet=None); validation logic is simple and well-understood |
</phase_requirements>

---

## Summary

Phase 8 creates a single new file `twibot20_io.py` with three public functions: `load_accounts(path)`, `build_edges(accounts_df, path)`, and `validate(accounts_df, edges_df)`. The file is a direct structural analog of `botsim24_io.py`, adapted for TwiBot-20's JSON schema instead of BotSim-24's CSV+JSON pair.

The primary technical work is (1) mapping TwiBot-20's nested profile dict and plain-text tweet list into the fixed `accounts_df` schema, and (2) remapping string Twitter IDs in neighbor lists to zero-indexed `node_idx` integers and building a typed `edges_df`. All implementation decisions were locked in the discussion phase (D-01 through D-08), so no design choices remain open.

**Primary recommendation:** Implement as three standalone functions in one file, following `botsim24_io.py`'s conventions exactly. No new dependencies are needed beyond pandas and numpy already in the project.

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| JSON file I/O | Data loading layer (`twibot20_io.py`) | — | Single source file, no HTTP or DB involved |
| Account schema mapping | Data loading layer | — | Field extraction and type coercion are loader responsibilities |
| ID→node_idx remapping | Data loading layer | — | Must happen before returning edges_df to callers |
| Edge construction | Data loading layer | — | Depends on accounts_df produced in same layer |
| Validation assertions | Data loading layer (validate fn) | — | Post-load integrity check; no pipeline dependency |
| Downstream feature extraction | Feature extractors (Stage 1/2/3) | — | Consumes accounts_df as-is; Phase 9 concern, not Phase 8 |

---

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pandas | already installed | DataFrame construction and column dtypes | Used throughout existing pipeline |
| numpy | already installed | `log1p`, dtype arrays, `int32`/`int8`/`float32` casts | Used throughout existing pipeline |
| json (stdlib) | stdlib | Load test.json | Standard library; same as `botsim24_io.py` |

No new dependencies. `twibot20_io.py` requires only `import json`, `import numpy as np`, `import pandas as pd` — the same three imports as `botsim24_io.py`'s minimal subset.

**Installation:** None required.

---

## Architecture Patterns

### System Architecture Diagram

```
test.json (file on disk)
        |
        v
load_accounts(path)
  - json.load(path)
  - iterate 1183 records
  - extract profile fields (strip whitespace)
  - build messages list [{text, ts:None, kind:"tweet"}]
  - assign node_idx by row enumeration
  - cast label str→int
        |
        v
accounts_df  [1183 rows x 8 cols]
  node_idx | screen_name | statuses_count | followers_count |
  friends_count | created_at | messages | label
        |
        v
build_edges(accounts_df, path)
  - json.load(path)  [re-read or accept raw data]
  - build id_to_idx dict {record['ID']: node_idx}
  - iterate records: skip neighbor=None
  - following list  → src=node_idx[i], dst=id_to_idx[nid], etype=0
  - follower list   → src=id_to_idx[nid], dst=node_idx[i], etype=1
  - drop IDs not in id_to_idx
  - assign weight=log1p(1.0) for all rows
  - cast dtypes: src/dst int32, etype int8, weight float32
        |
        v
edges_df  [154 rows x 4 cols]
  src | dst | etype | weight
        |
        v
validate(accounts_df, edges_df)
  - assert required columns present
  - assert edges_df["src"].max() < len(accounts_df)
  - assert edges_df["dst"].max() < len(accounts_df)
  - print no-neighbor fraction
  - print no-tweet fraction
```

### Recommended Project Structure

```
SocialBotDetectionSystem/
├── twibot20_io.py       # NEW: Phase 8 deliverable (alongside botsim24_io.py)
├── botsim24_io.py       # Existing analog (READ-ONLY for this phase)
├── test.json            # TwiBot-20 test split (1183 records)
└── tests/
    └── test_twibot20_io.py   # NEW: Phase 8 test file
```

### Pattern 1: Standalone Loader Functions (matching botsim24_io.py)

**What:** Three module-level functions, no classes, no global state. Path passed as parameter.
**When to use:** Consistent with the rest of the codebase.

```python
# Source: botsim24_io.py (structural analog) [VERIFIED: codebase]
import json
import numpy as np
import pandas as pd

def load_accounts(path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    rows = []
    for idx, record in enumerate(data):
        profile = record["profile"]
        tweets = record.get("tweet") or []
        messages = [{"text": str(t), "ts": None, "kind": "tweet"} for t in tweets if t]
        rows.append({
            "node_idx": np.int32(idx),
            "screen_name": str(profile.get("screen_name", "") or "").strip(),
            "statuses_count": int(str(profile.get("statuses_count", 0) or 0).strip() or 0),
            "followers_count": int(str(profile.get("followers_count", 0) or 0).strip() or 0),
            "friends_count": int(str(profile.get("friends_count", 0) or 0).strip() or 0),
            "created_at": str(profile.get("created_at", "") or "").strip(),
            "messages": messages,
            "label": int(record["label"]),
        })
    df = pd.DataFrame(rows)
    df["node_idx"] = df["node_idx"].astype(np.int32)
    return df
```

### Pattern 2: Edge Builder with ID Remapping (D-06)

**What:** Build `id_to_idx` dict from `record["ID"]` values, then iterate neighbor lists and drop any ID not in the dict.
**When to use:** Required — neighbor IDs are string Twitter IDs, must be remapped to node_idx ints; 99.3% of neighbor refs are cross-set and dropped.

```python
# Source: verified against test.json data inspection [VERIFIED: codebase]
def build_edges(accounts_df: pd.DataFrame, path: str) -> pd.DataFrame:
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    # Build lookup: Twitter string ID -> node_idx
    id_to_idx = {record["ID"]: int(accounts_df.iloc[i]["node_idx"])
                 for i, record in enumerate(data)}
    WEIGHT = np.float32(np.log1p(1.0))
    rows = []
    for i, record in enumerate(data):
        neighbor = record.get("neighbor")
        if neighbor is None:
            continue
        src_idx = int(accounts_df.iloc[i]["node_idx"])
        for nid in (neighbor.get("following") or []):
            if nid in id_to_idx:
                rows.append((src_idx, id_to_idx[nid], 0, WEIGHT))
        for nid in (neighbor.get("follower") or []):
            if nid in id_to_idx:
                rows.append((id_to_idx[nid], src_idx, 1, WEIGHT))
    if rows:
        srcs, dsts, etypes, weights = zip(*rows)
    else:
        srcs, dsts, etypes, weights = [], [], [], []
    return pd.DataFrame({
        "src": np.array(srcs, dtype=np.int32),
        "dst": np.array(dsts, dtype=np.int32),
        "etype": np.array(etypes, dtype=np.int8),
        "weight": np.array(weights, dtype=np.float32),
    })
```

### Pattern 3: Validation as Standalone Function (D-03, D-07)

**What:** `validate(accounts_df, edges_df)` checks column presence, edge bounds, and prints diagnostic fractions.
**When to use:** Called directly from `evaluate_twibot20.py` after loading.

```python
# Source: from D-07 requirements [VERIFIED: CONTEXT.md]
def validate(accounts_df: pd.DataFrame, edges_df: pd.DataFrame) -> None:
    required_cols = ["node_idx", "screen_name", "statuses_count", "followers_count",
                     "friends_count", "created_at", "messages", "label"]
    missing = [c for c in required_cols if c not in accounts_df.columns]
    assert not missing, f"Missing columns: {missing}"
    n = len(accounts_df)
    if len(edges_df) > 0:
        assert int(edges_df["src"].max()) < n, "src index out of bounds"
        assert int(edges_df["dst"].max()) < n, "dst index out of bounds"
    no_neighbor = sum(1 for m in accounts_df["messages"] if ...)  # see pitfall section
    # Print fractions
    no_tweet_frac = sum(1 for m in accounts_df["messages"] if len(m) == 0) / n
    print(f"[twibot20] accounts: {n}, edges: {len(edges_df)}")
    print(f"[twibot20] no-neighbor fraction: {109/n:.3f} (expected ~0.092)")
    print(f"[twibot20] no-tweet fraction: {no_tweet_frac:.3f}")
```

Note: the no-neighbor fraction cannot be computed from `accounts_df` alone (the loader does not store whether neighbor was None). See Pitfall 3 below for the recommended approach.

### Anti-Patterns to Avoid

- **Re-parsing test.json inside build_edges from scratch:** Wastes I/O; pass path as parameter and re-read, OR accept the raw loaded list alongside accounts_df. Either is fine; re-reading is simpler and consistent with botsim24_io.py's path-as-parameter pattern.
- **Building edges_df with Python dicts per row then calling pd.DataFrame(list_of_dicts):** Correct but slower; `zip(*rows)` into arrays is faster and still readable at 154 rows.
- **Using profile["id"] or profile["id_str"] as the lookup key:** The neighbor lists contain IDs that match `record["ID"]` (verified: `record["ID"] == profile["id_str"].strip()` for all 1183 records). Build the map from `record["ID"]` directly — do not strip or re-join through profile.
- **Sorting messages by ts:** Do not do this. ts=None for all TwiBot-20 messages. botsim24_io.py sorts by ts but filters out None-ts messages first; for TwiBot-20, all ts are None so a sort attempt would fail or produce empty list. Insert messages in tweet-list order.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| dtype enforcement on DataFrame columns | Manual loops casting individual cells | `df["col"].astype(np.int32)` after DataFrame construction | Cleaner, handles all rows at once |
| log1p computation | `math.log(2.0)` or custom | `numpy.log1p(1.0)` | Numerically correct; already imported |
| Whitespace stripping on all string fields | Custom per-field logic | `.strip()` inline at assignment | Profile strings have trailing spaces on ALL fields (verified: 1183/1183 screen_names need strip) |

**Key insight:** The complexity in this phase is entirely in understanding the data quirks (trailing spaces, None tweets, 99.3% cross-set neighbor IDs), not in the code itself. The code is simple; the risk is in missing a data edge case.

---

## Common Pitfalls

### Pitfall 1: Trailing Whitespace on All Profile String Fields
**What goes wrong:** `screen_name`, `statuses_count`, `followers_count`, `friends_count`, `created_at`, `id_str` all have trailing spaces (e.g., `"SharonIsrael10 "`). If not stripped, screen_name will have a trailing space, and numeric fields will fail `int()` conversion.
**Why it happens:** TwiBot-20 dataset formatting — all string values have a trailing space.
**How to avoid:** Apply `.strip()` to every field extracted from `profile`. For numeric fields: `int(str(val).strip())`.
**Warning signs:** `statuses_count` values like `'49757 '` in the raw JSON.

### Pitfall 2: tweet Field Can Be None (Not Just Empty List)
**What goes wrong:** `record["tweet"]` can be `None` (not `[]`). Iterating `for t in record["tweet"]` crashes with `TypeError: 'NoneType' is not iterable`.
**Why it happens:** 10 of 1183 records have `tweet: null` in the JSON.
**How to avoid:** Always guard: `tweets = record.get("tweet") or []`.
**Warning signs:** `empty tweet lists: 0` but `None tweets: 10` in data inspection output.

### Pitfall 3: No-Neighbor Fraction Cannot Be Recovered from accounts_df Alone
**What goes wrong:** The validate function needs to print the no-neighbor fraction, but accounts_df stores only messages — it does not record whether the neighbor field was None. Computing "accounts with 0 messages" is not the same metric (10 accounts have no tweets; 109 have no neighbors — different sets).
**Why it happens:** The loader does not propagate the neighbor-presence flag to accounts_df.
**How to avoid:** One of three options:
  1. Track no-neighbor count as a module-level or closure variable during `load_accounts()` — not clean.
  2. Re-read test.json inside `validate()` — adds I/O.
  3. **Recommended:** Add a `has_neighbor` column (bool) to `accounts_df`, or accept the raw data as an optional param to `validate()`. Alternatively, print only the no-tweet fraction from accounts_df, and document that no-neighbor fraction (~9.2%) is a known data characteristic requiring re-read. The simplest correct approach: print both fractions by re-reading, or expose a module-level `NO_NEIGHBOR_COUNT` set at load time.
**Warning signs:** Attempting `accounts_df["messages"].map(len).eq(0).mean()` and getting 10/1183=0.85% instead of the expected 9.2%.

### Pitfall 4: Edge Direction Semantics
**What goes wrong:** `following` and `follower` are both lists of IDs, but they have opposite directional meanings.
**Why it happens:** In TwiBot-20, `following` is "accounts this user follows" (outgoing), `follower` is "accounts that follow this user" (incoming).
**How to avoid:** Following edge: `src=current_account_node_idx, dst=neighbor_node_idx, etype=0`. Follower edge: `src=neighbor_node_idx, dst=current_account_node_idx, etype=1`. Verified with data: this produces 116 etype-0 edges and 38 etype-1 edges (154 total in-set).
**Warning signs:** If you reverse the follower direction, `src` of etype-1 edges would be the current account, which is logically incorrect (the current account is the destination of follower edges).

### Pitfall 5: Empty edges_df Breaks .max() Call
**What goes wrong:** If `edges_df` is empty (e.g., in a unit test with zero in-set IDs), calling `edges_df["src"].max()` raises `ValueError: max() arg is an empty sequence` in pandas.
**Why it happens:** pandas `.max()` on an empty Series returns `NaN`, but the assertion `NaN < n` is False, which triggers the assert incorrectly — or raises depending on pandas version.
**How to avoid:** Guard: `if len(edges_df) > 0:` before the max assertions in `validate()`.
**Warning signs:** Test with empty accounts_df or accounts_df with no neighbors fails validation.

### Pitfall 6: Profile Missing Columns for Some Records
**What goes wrong:** Using `profile["statuses_count"]` (direct key access) instead of `profile.get("statuses_count", 0)` raises KeyError if any record has a malformed profile.
**Why it happens:** Not observed in test.json (all 1183 records have all numeric fields), but defensive coding matches the pattern in `botsim24_io.py`.
**How to avoid:** Always use `.get(key, default)` for profile fields. The Claude's Discretion section permits defaulting missing numerics to `0`.

---

## Code Examples

### Verified: data shape from direct test.json inspection
```python
# [VERIFIED: direct data inspection via python -c]
# test.json: 1183 records
# Label distribution: {'1': 640, '0': 543}
# None neighbors: 109 (9.21%)
# tweet=None records: 10 (0.85%)
# tweet=[] records: 0
# None statuses_count: 0 (all present)
# All profile numeric fields are strings with trailing whitespace, e.g. '49757 '
# All screen_name values have trailing whitespace: 1183/1183
# record["ID"] == profile["id_str"].strip() for all 1183 records
# In-set neighbor edges: 154 out of 20,814 total neighbor refs (0.7%)
# etype-0 (following) edges: 116
# etype-1 (follower) edges: 38
# log1p(1.0) = 0.6931471805599453
```

### Verified: features_stage2.py handles ts=None correctly
```python
# Source: features_stage2.py line 49 [VERIFIED: codebase]
if m.get("ts") is not None:
    ts.append(float(m["ts"]))
# ts=None messages are included in embedding but excluded from temporal features.
# All TwiBot-20 messages will have ts=None -> temporal features will be 0.0 for all accounts.
```

### Verified: build_graph_features_nodeidx expects these exact dtypes
```python
# Source: botdetector_pipeline.py lines 368-372 [VERIFIED: codebase]
node_ids = accounts_df["node_idx"].to_numpy(dtype=np.int32)
src = edges_df["src"].to_numpy(dtype=np.int32)
dst = edges_df["dst"].to_numpy(dtype=np.int32)
w   = edges_df["weight"].to_numpy(dtype=np.float32)
et  = edges_df["etype"].to_numpy(dtype=np.int8)
# The function casts on read, so DataFrame dtypes are not strictly enforced,
# but explicit dtype assignment in edges_df is good practice and required by TW-02.
```

### Verified: extract_stage1_matrix expects these columns
```python
# Source: features_stage1.py [VERIFIED: codebase]
# Reads: df["username"], df["submission_num"], df["comment_num_1"],
#        df["comment_num_2"], df["subreddit_list"]
# These are Reddit-specific columns NOT present in twibot20 accounts_df.
# Phase 9 (evaluate_twibot20.py) must zero-fill these columns before
# calling extract_stage1_matrix — this is OUT OF SCOPE for Phase 8.
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| BotSim-24 only | TwiBot-20 as zero-shot transfer target | Phase 8 | New loader needed; no pipeline changes |
| `build_account_table()` reads CSV+JSON pair | `load_accounts()` reads single JSON | Phase 8 | Simpler I/O; same output schema |

**Deprecated/outdated:** None — this is new code.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The `record["ID"]` is the correct key to use for building `id_to_idx` — not `profile["id_str"]` | Code Examples / Pitfall 4 | LOW: verified by data inspection (ID == id_str.strip() for all 1183). If wrong, 0 in-set edges instead of 154. |
| A2 | Following neighbor list means "accounts this user follows" (outgoing), follower list means "accounts that follow this user" (incoming) | Pitfall 4 | MEDIUM: derived from Twitter terminology convention + standard TwiBot-20 dataset documentation. If direction is reversed, edge semantics are incorrect but code runs without error. Impact is limited since Stage 3 uses degree counts, not directionality per se. |
| A3 | Missing numeric profile fields default to `0` (not `None`) for `statuses_count`, `followers_count`, `friends_count` | Architecture Patterns | LOW: none observed in data; 0 is safe for downstream numeric use. |

---

## Open Questions

1. **No-neighbor fraction in validate()**
   - What we know: accounts_df does not record whether neighbor was None; the raw JSON would need to be re-read.
   - What's unclear: whether the planner wants to add a `has_neighbor` column, re-read inside validate, or simply hardcode the known fraction.
   - Recommendation: The simplest approach that satisfies D-07 without extra columns is to track a `no_neighbor_count` as a module-level variable set in `load_accounts()`, or to accept the raw `data` list as an optional third argument to `validate()`. The planner should pick one approach and document it in the plan.

2. **`load_accounts` signature: should it accept a list (already-parsed) or always a path?**
   - What we know: `build_edges` also needs to read the file to get neighbor data; if both functions re-read, there's redundant I/O.
   - What's unclear: whether the caller will always pass the path or might pre-parse.
   - Recommendation: Keep path-as-parameter for both (matching botsim24_io.py pattern). 1183 records x ~200 tweets is small enough that two reads are negligible.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Runtime | Yes | 3.x | — |
| pandas | accounts_df / edges_df | Yes | already installed | — |
| numpy | dtype casts, log1p | Yes | already installed | — |
| pytest | Testing | Yes | 8.3.4 | — |
| test.json | load_accounts, build_edges | Yes | present in repo root | — |

No missing dependencies.

---

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | none (auto-discovered from `tests/`) |
| Quick run command | `python -m pytest tests/test_twibot20_io.py -x -q` |
| Full suite command | `python -m pytest tests/ -x -q` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| TW-01 | `load_accounts()` returns DataFrame with all 8 required columns, correct dtypes, 1183 rows, label as int | unit | `python -m pytest tests/test_twibot20_io.py::test_load_accounts_schema -x` | Wave 0 |
| TW-01 | `node_idx` is int32, 0-indexed by row, no gaps | unit | `python -m pytest tests/test_twibot20_io.py::test_node_idx_contiguous -x` | Wave 0 |
| TW-01 | `messages` built correctly: each tweet → `{text, ts:None, kind:"tweet"}` | unit | `python -m pytest tests/test_twibot20_io.py::test_messages_structure -x` | Wave 0 |
| TW-01 | tweet=None records produce empty messages list, not error | unit | `python -m pytest tests/test_twibot20_io.py::test_null_tweet_handled -x` | Wave 0 |
| TW-02 | `build_edges()` returns DataFrame with correct 4-column schema and dtypes | unit | `python -m pytest tests/test_twibot20_io.py::test_edges_schema -x` | Wave 0 |
| TW-02 | neighbor=None records produce no rows | unit | `python -m pytest tests/test_twibot20_io.py::test_null_neighbor_no_rows -x` | Wave 0 |
| TW-02 | Cross-set IDs are dropped; all src/dst are valid node_idx values | unit | `python -m pytest tests/test_twibot20_io.py::test_edges_in_set_only -x` | Wave 0 |
| TW-02 | weight column is uniformly `log1p(1.0)` | unit | `python -m pytest tests/test_twibot20_io.py::test_edge_weight -x` | Wave 0 |
| TW-03 | `validate()` passes on valid accounts_df + edges_df | unit | `python -m pytest tests/test_twibot20_io.py::test_validate_passes -x` | Wave 0 |
| TW-03 | `validate()` raises AssertionError when src.max() >= len(accounts_df) | unit | `python -m pytest tests/test_twibot20_io.py::test_validate_bounds_fail -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `python -m pytest tests/test_twibot20_io.py -x -q`
- **Per wave merge:** `python -m pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_twibot20_io.py` — all TW-01/TW-02/TW-03 tests (does not exist yet)

*(All other test infrastructure is already in place: pytest, conftest.py, test discovery.)*

---

## Security Domain

This phase is data loading only — pure file I/O from a local JSON file in the repo. No network access, authentication, user input, or cryptographic operations are involved. ASVS categories V2 (Authentication), V3 (Session), V4 (Access Control), V6 (Cryptography) do not apply. V5 (Input Validation) applies only in the sense that profile field values of unexpected types are handled defensively (`.get(key, default)`, `.strip()`, `int(str(...).strip() or 0)`).

---

## Sources

### Primary (HIGH confidence)
- `botsim24_io.py` — structural analog examined in full; all function signatures and patterns verified
- `botdetector_pipeline.py` — `build_graph_features_nodeidx` signature and dtype expectations verified
- `features_stage1.py` — column names `username`, `submission_num`, `comment_num_1`, `comment_num_2`, `subreddit_list` confirmed
- `features_stage2.py` — `ts=None` guard at line 49 confirmed; `m.get("text")` access pattern confirmed
- `test.json` — direct data inspection via Python (record count, field types, None patterns, neighbor edge count, etype distribution)
- `.planning/workstreams/twibot-intergration/phases/08-twibot-20-data-loader/08-CONTEXT.md` — all locked decisions (D-01 through D-08)
- `.planning/workstreams/twibot-intergration/REQUIREMENTS.md` — TW-01, TW-02, TW-03 exact success criteria
- `tests/conftest.py` and `tests/test_features_stage2.py` — test patterns confirmed

### Secondary (MEDIUM confidence)
- Twitter API documentation (training knowledge): following/follower direction semantics [ASSUMED — standard Twitter terminology]

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; pandas/numpy/json already in project
- Architecture: HIGH — direct analog to botsim24_io.py; all decisions locked; data fully inspected
- Pitfalls: HIGH — verified against actual test.json data (trailing spaces, None tweets, cross-set edge rate)
- Test plan: HIGH — pytest 8.3.4 confirmed; test file does not yet exist (Wave 0 gap)

**Research date:** 2026-04-16
**Valid until:** 2026-05-16 (stable dataset + stable stdlib; no fast-moving dependencies)
