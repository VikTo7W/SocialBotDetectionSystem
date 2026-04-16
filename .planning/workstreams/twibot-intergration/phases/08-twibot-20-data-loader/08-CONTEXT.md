# Phase 8: TwiBot-20 Data Loader - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Load `test.json` (1183 records) into two BotSim-24-compatible structures:
1. `accounts_df` — per-account DataFrame with fixed column schema
2. `edges_df` — directed edge DataFrame with fixed schema for `build_graph_features_nodeidx`
3. `validate()` — asserts integrity constraints and prints diagnostic fractions

New file only: `twibot20_io.py`. Zero changes to any existing pipeline file.

</domain>

<decisions>
## Implementation Decisions

### messages List Structure
- **D-01:** Each tweet is stored as `{"text": str, "ts": None, "kind": "tweet"}` — full schema-compatible dict matching `botsim24_io.py`'s message format. Stage 2 feature extractor (`features_stage2.py`) already handles `ts=None` via `if m.get("ts") is not None`. The `kind` field aids debugging in Phase 9.

### created_at Representation
- **D-02:** Store `created_at` as a raw string exactly as it appears in `profile["created_at"]` (Twitter format: e.g. `"Mon Apr 23 09:47:10 +0000 2012"`). Parsing is unnecessary — the column is not used in temporal feature extraction for TwiBot-20 accounts.

### Validation Output
- **D-03:** Use `print()` statements — consistent with the existing codebase which uses no logging module. Validation output is visible when running `evaluate_twibot20.py` directly.

### Locked Schema (from REQUIREMENTS / ROADMAP)
- **D-04:** `accounts_df` columns: `node_idx` (int32, 0-indexed by row), `screen_name`, `statuses_count`, `followers_count`, `friends_count`, `created_at`, `messages`, `label` (int, 0 or 1)
- **D-05:** `edges_df` schema: `{src: int32, dst: int32, etype: int8, weight: float32}` — `"following"` → etype 0, `"follower"` → etype 1, weight = `log1p(1.0)` for all edges; accounts with `neighbor: None` contribute no rows
- **D-06:** ID remapping: string Twitter IDs from `neighbor.following` / `neighbor.follower` remapped to zero-indexed `node_idx` integers using only IDs present in the evaluation set; IDs not in the set are silently dropped (no cross-set edges)
- **D-07:** Validation asserts: `edges_df["src"].max() < len(accounts_df)` and `edges_df["dst"].max() < len(accounts_df)`; prints no-neighbor fraction (~9.2% from data inspection) and no-tweet fraction
- **D-08:** Label parsing: `record["label"]` is string `"0"` or `"1"` → cast to int inline

### Claude's Discretion
- Internal ID→node_idx mapping implementation (dict lookup is fine)
- How to handle profiles with missing/None values for `statuses_count`, `followers_count`, `friends_count` (default to 0 or None — Claude decides)
- Whether `validate()` is a standalone function or a method — standalone is consistent with `botsim24_io.py` pattern

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### TwiBot-20 Data Format
- `test.json` — 1183 records; each record: `{ID, profile, tweet, neighbor, domain, label}`
  - `profile`: full Twitter profile dict — relevant keys: `screen_name`, `statuses_count`, `followers_count`, `friends_count`, `created_at`
  - `tweet`: list of plain strings (no timestamps, no metadata)
  - `neighbor`: dict `{following: [str IDs], follower: [str IDs]}` or `None` (~9.2% are None)
  - `label`: string `"0"` (human) or `"1"` (bot)

### Existing Analog
- `botsim24_io.py` — direct structural analog; same path-as-parameter pattern, same messages list structure

### Feature Extractors (downstream compatibility)
- `features_stage1.py` — reads `username`, `submission_num`, `comment_num_1`, `comment_num_2`, `subreddit_list`, `messages`; TwiBot-20 accounts zero-fill these Reddit-specific columns in Phase 9
- `features_stage2.py` — reads `messages` as list of dicts; uses `m.get("text")` and `m.get("ts")` (None ts already handled)

### Requirements
- `.planning/workstreams/twibot-intergration/REQUIREMENTS.md` — TW-01, TW-02, TW-03 define exact success criteria for this phase

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `botsim24_io.py:_to_unix_seconds()` — datetime parsing utility (not needed for this phase since created_at stays as raw string, but pattern is established)
- `botsim24_io.py:build_account_table()` — structural template for the new loader function

### Established Patterns
- All I/O functions take file paths as parameters (not hardcoded)
- `messages` list is built with explicit dict keys including `text`, `ts`, `kind`
- Labels are `int` (0 or 1), not string
- DataFrames use explicit dtype assignments for numeric columns

### Integration Points
- Phase 9 (`evaluate_twibot20.py`) will call `twibot20_io.load_accounts()` and `twibot20_io.build_edges()` — these are the primary consumers
- `build_graph_features_nodeidx(n_types=3)` consumes `edges_df` — schema must be drop-in compatible

</code_context>

<specifics>
## Specific Ideas

No specific references or "I want it like X" moments — requirements fully captured in decisions above.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 08-twibot-20-data-loader*
*Context gathered: 2026-04-16*
