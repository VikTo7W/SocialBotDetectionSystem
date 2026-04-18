# Phase 17: Shared Feature Extraction Module - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Create a `features/` package and a `data_io.py` module that unify all feature extraction and data loading logic across BotSim-24 (Reddit) and TwiBot-20. Remove the LSTM Stage 2b code entirely. No pipeline, training, or evaluation logic is touched in this phase — that is Phase 18.

Files created/modified in this phase:
- `features/__init__.py`, `features/stage1.py`, `features/stage2.py`, `features/stage3.py` (new)
- `data_io.py` (new — merges botsim24_io.py + twibot20_io.py)
- `botdetector_pipeline.py` (LSTM code removed, graph feature builder moved out)
- Old feature files (`features_stage1.py`, `features_stage1_twitter.py`, etc.) — deleted or deprecated

</domain>

<decisions>
## Implementation Decisions

### Module Layout
- **D-01:** Feature extractors live in a `features/` package at project root: `features/__init__.py`, `features/stage1.py`, `features/stage2.py`, `features/stage3.py`
- **D-02:** `build_graph_features_nodeidx` moves from `botdetector_pipeline.py` into `features/stage3.py` — all extraction logic lives in features/, pipeline imports from there
- **D-03:** Data loading merges into a single `data_io.py` at project root with a `load_dataset(dataset, ...)` top-level dispatch function

### Extractor Interface
- **D-04:** One class per stage, constructed with a `dataset` parameter: `Stage1Extractor(dataset='botsim')` or `Stage1Extractor(dataset='twibot')` — class branches internally on the dataset param
- **D-05:** Main extraction method is `extract(df) -> np.ndarray` — consistent across all stages, caller passes a DataFrame, gets back a feature matrix
- **D-06:** Stage 2 extractor also accepts an `embedder` argument to `extract(df, embedder)` since embedding requires a model object

### LSTM Removal
- **D-07:** Full removal — delete `_Stage2LSTMNet`, `Stage2LSTMRefiner`, `build_lstm_sequences`, `normalize_stage2b_variant`, and the `stage2b_variant` / `stage2b_lstm` fields on `TrainedSystem`. AMR-only path, no variant switching infrastructure remains.

### Data I/O
- **D-08:** `load_dataset(dataset, ...)` is a top-level dispatch function in `data_io.py` — `load_dataset('botsim', ...)` and `load_dataset('twibot', ...)` route to the right internal loader
- **D-09:** Internal loaders (`_load_botsim(...)`, `_load_twibot(...)`) preserve all existing field names and return contracts from `botsim24_io.py` and `twibot20_io.py` so downstream code in the pipeline does not need to change field references in this phase

### Code Quality (from milestone QUAL requirements)
- **D-10:** Classes and methods throughout — no loose procedural extraction functions
- **D-11:** Comments lowercase, explain the why, used sparingly

### Claude's Discretion
- Internal branching style within each extractor class (if/elif vs dict dispatch vs separate private methods) — Claude picks what reads cleanest
- Whether `features/__init__.py` re-exports the extractor classes or stays empty
- Exact signature for Stage 3 extractor (edges_df shape, num_nodes_total default handling)

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing feature extractors (to be unified)
- `features_stage1.py` — Reddit Stage 1 procedural extractor
- `features_stage1_twitter.py` — TwiBot Stage 1 extractor with STAGE1_TWITTER_COLUMNS constant
- `features_stage2.py` — Reddit Stage 2 extractor (embeddings + linguistic + temporal)
- `features_stage2_twitter.py` — TwiBot Stage 2 extractor (embeddings + linguistic, no timestamp sentinel)
- `features_stage3_twitter.py` — TwiBot Stage 3 wrapper (delegates to pipeline)

### Pipeline (LSTM code to remove, graph builder to move)
- `botdetector_pipeline.py` — lines 179-230 (build_lstm_sequences), 324-369 (AMRDeltaRefiner), 372-461 (Stage2LSTMRefiner + _Stage2LSTMNet), 509-587 (build_graph_features_nodeidx), 657-668 (TrainedSystem fields: stage2b_lstm, stage2b_variant, normalize_stage2b_variant)

### Data loading (to merge into data_io.py)
- `botsim24_io.py` — Reddit data loader: load_users_csv, load_user_post_comment_json, build_account_table
- `twibot20_io.py` — TwiBot data loader: parse_tweet_types, load_twibot20_split, build_twibot20_account_table

### Requirements
- `.planning/REQUIREMENTS.md` — CORE-01, CORE-02, CORE-05 are the requirements for this phase

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AMRDeltaRefiner` class (botdetector_pipeline.py:324) — stays; only the LSTM classes are removed
- `extract_amr_embeddings_for_accounts` (botdetector_pipeline.py:141) — stays or moves to features/stage2.py as a method
- `build_graph_features_nodeidx` (botdetector_pipeline.py:509) — moves to features/stage3.py
- `MahalanobisNovelty` class — stays in botdetector_pipeline.py (it's a model, not an extractor)

### Established Patterns
- Existing extractors are procedural functions (`extract_stage1_matrix`, `extract_stage2_features`) — Phase 17 converts these to class methods
- BotSim-24 Stage 1 returns a plain `np.ndarray`; TwiBot Stage 1 has a named columns constant — the unified class should expose `columns` as a class attribute for both datasets
- Stage 2 Twitter extractor is already somewhat cleaner (uses `_select_texts`, `_simple_linguistic_features` as private helpers) — good model for the new class structure

### Integration Points
- `botdetector_pipeline.py` currently imports directly from `features_stage1.py`, `features_stage2.py` — those imports will change to `from features.stage1 import Stage1Extractor` etc. in Phase 18
- `train_twibot20.py` imports from Twitter-specific feature files — will change in Phase 19

</code_context>

<specifics>
## Specific Ideas

- The new `Stage2Extractor.extract(df, embedder)` should handle the dataset branching: BotSim-24 path uses the timestamp sentinel feature (`_MISSING_TEMPORAL_SENTINEL`), TwiBot path omits it — this branching is internal to the class
- `features/stage3.py` should expose both `build_graph_features_nodeidx` (the raw builder, kept for pipeline use) and `Stage3Extractor(dataset=...)` as a class wrapper — so the pipeline can import the builder directly if needed

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 17-shared-feature-extraction-module*
*Context gathered: 2026-04-18*
