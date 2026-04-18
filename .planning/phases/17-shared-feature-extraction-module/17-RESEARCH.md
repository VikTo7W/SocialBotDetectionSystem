# Phase 17: Shared Feature Extraction Module - Research

**Researched:** 2026-04-18
**Domain:** Python package refactoring — procedural-to-class extraction, code unification
**Confidence:** HIGH

## Summary

Phase 17 is a pure code-reorganization phase. No new algorithms are introduced. The goal is to
convert five procedural feature extractor files (`features_stage1.py`, `features_stage1_twitter.py`,
`features_stage2.py`, `features_stage2_twitter.py`, `features_stage3_twitter.py`) into a single
`features/` package with three class-based modules (`stage1.py`, `stage2.py`, `stage3.py`), each
parameterized by `dataset='botsim'|'twibot'`. Simultaneously, two data-loading modules
(`botsim24_io.py`, `twibot20_io.py`) are unified into a single `data_io.py` with a top-level
dispatch function. The LSTM Stage 2b path is fully deleted from `botdetector_pipeline.py`.

The codebase has no CLAUDE.md, no `.claude/skills/` directory, and no framework-level
library research is needed — all dependencies (`numpy`, `pandas`, `sentence-transformers`)
are already installed and in use. The research value here is a precise inventory of every
symbol that moves, every import that breaks, every test that must be updated, and every
pitfall in the conversion from procedural code to classes.

**Primary recommendation:** Read every source file before writing a single line; the
conversion is mechanical but the output contract of each extractor is precisely documented
in existing tests. Any divergence from the exact dtype, shape, or column order documented
in those tests will silently corrupt trained models.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

- **D-01:** Feature extractors live in a `features/` package at project root: `features/__init__.py`, `features/stage1.py`, `features/stage2.py`, `features/stage3.py`
- **D-02:** `build_graph_features_nodeidx` moves from `botdetector_pipeline.py` into `features/stage3.py` — all extraction logic lives in features/, pipeline imports from there
- **D-03:** Data loading merges into a single `data_io.py` at project root with a `load_dataset(dataset, ...)` top-level dispatch function
- **D-04:** One class per stage, constructed with a `dataset` parameter: `Stage1Extractor(dataset='botsim')` or `Stage1Extractor(dataset='twibot')` — class branches internally on the dataset param
- **D-05:** Main extraction method is `extract(df) -> np.ndarray` — consistent across all stages, caller passes a DataFrame, gets back a feature matrix
- **D-06:** Stage 2 extractor also accepts an `embedder` argument to `extract(df, embedder)` since embedding requires a model object
- **D-07:** Full LSTM removal — delete `_Stage2LSTMNet`, `Stage2LSTMRefiner`, `build_lstm_sequences`, `normalize_stage2b_variant`, and the `stage2b_variant` / `stage2b_lstm` fields on `TrainedSystem`. AMR-only path, no variant switching infrastructure remains.
- **D-08:** `load_dataset(dataset, ...)` is a top-level dispatch function in `data_io.py` — `load_dataset('botsim', ...)` and `load_dataset('twibot', ...)` route to the right internal loader
- **D-09:** Internal loaders (`_load_botsim(...)`, `_load_twibot(...)`) preserve all existing field names and return contracts from `botsim24_io.py` and `twibot20_io.py` so downstream code in the pipeline does not need to change field references in this phase
- **D-10:** Classes and methods throughout — no loose procedural extraction functions
- **D-11:** Comments lowercase, explain the why, used sparingly

### Claude's Discretion

- Internal branching style within each extractor class (if/elif vs dict dispatch vs separate private methods) — Claude picks what reads cleanest
- Whether `features/__init__.py` re-exports the extractor classes or stays empty
- Exact signature for Stage 3 extractor (edges_df shape, num_nodes_total default handling)

### Deferred Ideas (OUT OF SCOPE)

None — discussion stayed within phase scope.
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| CORE-01 | A dataset parameter (`botsim` / `twibot`) controls which feature extractors, data loaders, and split logic are used throughout the pipeline — no dataset-specific branches embedded in shared code | Satisfied by D-04: one class per stage with internal dataset branching; satisfied by D-08: `load_dataset()` dispatch |
| CORE-02 | All feature extractor classes live in one module (`features/`), with Stage 1, 2a, 2b, and 3 extractors accepting a dataset parameter | Satisfied by D-01 + D-04: `features/stage1.py`, `features/stage2.py`, `features/stage3.py` each accept `dataset=` |
| CORE-05 | Stage 2b retains only the AMR embedding delta-logit path; the LSTM path is removed entirely | Satisfied by D-07: full deletion of `_Stage2LSTMNet`, `Stage2LSTMRefiner`, `build_lstm_sequences`, `normalize_stage2b_variant`, and `TrainedSystem` LSTM fields |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Stage 1 feature extraction | `features/stage1.py` | — | All metadata feature logic moves here; pipeline imports the class |
| Stage 2a feature extraction | `features/stage2.py` | — | Embedding + linguistic + temporal logic moves here |
| Stage 2b AMR delta | `features/stage2.py` | `botdetector_pipeline.py` (`AMRDeltaRefiner`) | AMR embedding extraction moves to Stage2Extractor; the refiner model stays in the pipeline |
| Stage 3 graph feature extraction | `features/stage3.py` | — | `build_graph_features_nodeidx` moves here; pipeline imports it |
| Data loading / dispatch | `data_io.py` | — | New top-level module; `botsim24_io.py` and `twibot20_io.py` internal logic stays intact but is wrapped |
| LSTM removal | `botdetector_pipeline.py` | `conftest.py`, `main.py` | Dead code deletion; LSTM fixture in conftest.py must be removed too |
| TrainedSystem dataclass | `botdetector_pipeline.py` | — | Drop LSTM fields; AMR-only path |

## Standard Stack

No new dependencies. All libraries are already installed. [VERIFIED: project imports]

| Library | Current Use | Phase 17 Use |
|---------|-------------|--------------|
| `numpy` | All feature math | Unchanged |
| `pandas` | DataFrame I/O | Unchanged |
| `sentence-transformers` | Embedding in Stage 2 | Unchanged |
| `pytest` | Test suite | Tests must be updated for new import paths |

## Architecture Patterns

### System Architecture Diagram

```
Data sources (Users.csv / train.json)
         |
         v
   data_io.load_dataset(dataset, ...)
         |
    +----+----+
    |         |
_load_botsim  _load_twibot
    |         |
    +----+----+
         |
    accounts_df + edges_df
         |
         v
Stage1Extractor(dataset=...).extract(df)
         |
         v
Stage2Extractor(dataset=...).extract(df, embedder)
         |
         v  [AMR gate -> AMRDeltaRefiner.refine()]
Stage3Extractor(dataset=...).extract(accounts_df, edges_df)
         |
         v
botdetector_pipeline.py  (imports from features.*, unchanged cascade logic)
```

### Recommended Project Structure

```
features/
├── __init__.py          # empty or re-exports Stage1/2/3Extractor
├── stage1.py            # Stage1Extractor(dataset='botsim'|'twibot')
├── stage2.py            # Stage2Extractor(dataset='botsim'|'twibot')
└── stage3.py            # Stage3Extractor + build_graph_features_nodeidx

data_io.py               # load_dataset(), _load_botsim(), _load_twibot()

botdetector_pipeline.py  # LSTM code deleted; imports updated in Phase 18
botsim24_io.py           # kept as-is (Phase 17 does NOT delete it)
twibot20_io.py           # kept as-is (Phase 17 does NOT delete it)
```

Note: `botsim24_io.py` and `twibot20_io.py` are NOT deleted in Phase 17.
Their internal logic is wrapped by `data_io.py`'s private functions. Deletion
happens when Phase 18 updates pipeline imports.

### Pattern: Class wrapping procedural function, branching on dataset

```python
# [VERIFIED: codebase inspection]
class Stage1Extractor:
    def __init__(self, dataset: str) -> None:
        if dataset not in {"botsim", "twibot"}:
            raise ValueError(f"unknown dataset: {dataset!r}")
        self.dataset = dataset

    def extract(self, df: pd.DataFrame) -> np.ndarray:
        if self.dataset == "botsim":
            return self._extract_botsim(df)
        return self._extract_twibot(df)

    def _extract_botsim(self, df: pd.DataFrame) -> np.ndarray:
        # exact body from features_stage1.extract_stage1_matrix
        ...

    def _extract_twibot(self, df: pd.DataFrame) -> np.ndarray:
        # exact body from features_stage1_twitter.extract_stage1_matrix_twitter
        ...
```

The private-method branching style (vs if/elif inline) is Claude's discretion per
the CONTEXT.md, but private methods are cleaner for functions of this size.

### Anti-Patterns to Avoid

- **Merging the botsim and twibot feature vectors into one path:** The two datasets have
  different column schemas. The class must branch and return dataset-appropriate arrays.
  Do not try to share a single numpy stack across both paths.
- **Moving botsim24_io / twibot20_io public API in Phase 17:** Those files are still
  imported by `main.py`, `train_twibot20.py`, and existing tests. Phase 17 wraps them;
  Phase 18 updates the pipeline imports.
- **Changing output dtypes or column counts:** Every existing test pins the exact shape
  (e.g., Stage 2 botsim = 397 dims, Stage 2 twibot = 393 dims). The class wrapper must
  produce identical output.
- **Importing features_stage*.py from within features/:** The new `features/` package
  should copy/inline the logic, not import from the old files. Importing from old files
  defeats the consolidation and leaves the old files as implicit dependencies.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Dataset dispatch | ad-hoc string matching | Simple if/elif on validated `dataset` param | Already all the abstraction needed; no registry pattern warranted |
| Output contract verification | custom assertion logic | Existing pytest test suite | Tests already pin shape, dtype, and sentinel values precisely |

## Symbol Inventory (Complete)

This is the authoritative list of what moves, what is deleted, and what stays.

### Symbols that MOVE into `features/`

| From file | Symbol | Moves to |
|-----------|--------|----------|
| `features_stage1.py` | `extract_stage1_matrix` | `features/stage1.py` as `Stage1Extractor._extract_botsim` |
| `features_stage1_twitter.py` | `extract_stage1_matrix_twitter` | `features/stage1.py` as `Stage1Extractor._extract_twibot` |
| `features_stage1_twitter.py` | `STAGE1_TWITTER_COLUMNS` | `features/stage1.py` (class attribute) |
| `features_stage1_twitter.py` | `_safe_account_age_days` | `features/stage1.py` (private helper) |
| `features_stage1_twitter.py` | `_tweet_breakdown` | `features/stage1.py` (private helper) |
| `features_stage1_twitter.py` | `_SECONDS_PER_DAY`, `_EPS` | `features/stage1.py` (module constants) |
| `features_stage2.py` | `extract_stage2_features` | `features/stage2.py` as `Stage2Extractor._extract_botsim` |
| `features_stage2.py` | `simple_linguistic_features` | `features/stage2.py` (private helper `_simple_linguistic_features`) |
| `features_stage2.py` | `_NEAR_DUP_SIM_THRESHOLD`, `_MISSING_TEMPORAL_SENTINEL` | `features/stage2.py` (module constants) |
| `features_stage2_twitter.py` | `extract_stage2_features_twitter` | `features/stage2.py` as `Stage2Extractor._extract_twibot` |
| `features_stage2_twitter.py` | `STAGE2_TWITTER_COLUMNS`, `STAGE2_TWITTER_EMBEDDING_DIM` | `features/stage2.py` (class attributes / module constants) |
| `features_stage2_twitter.py` | `_select_texts` | `features/stage2.py` (private helper) |
| `features_stage3_twitter.py` | `extract_stage3_features_twitter` | `features/stage3.py` as `Stage3Extractor._extract_twibot` |
| `features_stage3_twitter.py` | `STAGE3_TWITTER_COLUMNS`, `TWITTER_NATIVE_EDGE_TYPES` | `features/stage3.py` |
| `botdetector_pipeline.py` | `build_graph_features_nodeidx` | `features/stage3.py` (also re-exported for backward compat in Phase 18) |

### Symbols that are DELETED from `botdetector_pipeline.py`

| Symbol | Lines (approx) | Reason |
|--------|----------------|--------|
| `extract_message_embedding_sequences_for_accounts` | 172-216 | LSTM support only |
| `_Stage2LSTMNet` | 372-391 | LSTM removed |
| `Stage2LSTMRefiner` | 394-460 | LSTM removed |
| `normalize_stage2b_variant` | 666-670 | LSTM variant switching removed |
| `apply_stage2b_refiner` | 673-707 | LSTM variant switching removed; AMR path inlined |
| `TrainedSystem.stage2b_lstm` field | 662 | LSTM removed |
| `TrainedSystem.stage2b_variant` field | 663 | LSTM variant switching removed |

Note: `extract_amr_embeddings_for_accounts` (lines 141-169) stays in
`botdetector_pipeline.py` OR moves to `features/stage2.py`. The CONTEXT.md says
"stays or moves" — the decision is Claude's discretion. Moving it to `features/stage2.py`
as a method of `Stage2Extractor` is cleaner since it is extraction logic.

### Symbols that STAY in `botdetector_pipeline.py`

- `AMRDeltaRefiner` — model, not extractor
- `MahalanobisNovelty` — model
- `Stage1MetadataModel`, `Stage2BaseContentModel`, `Stage3StructuralModel` — models
- `TrainedSystem` (minus LSTM fields) — dataclass
- All gate functions, meta training, OOF logic
- `sigmoid`, `logit`, `entropy_from_p`, `TextEmbedder`, `FeatureConfig`, `StageThresholds`

### Symbols that move to `data_io.py`

| From file | Symbol | Role in data_io.py |
|-----------|--------|---------------------|
| `botsim24_io.py` | `load_users_csv`, `load_user_post_comment_json`, `build_account_table` | wrapped by `_load_botsim()` |
| `twibot20_io.py` | `load_accounts`, `build_edges`, `validate` | wrapped by `_load_twibot()` |

The internal helpers (`parse_subreddits`, `_to_unix_seconds`, `_detect_encoding`, etc.)
stay in the original files since `_load_botsim`/`_load_twibot` will call the original
public functions rather than copy their internals. [VERIFIED: D-09 intent]

## Output Contract Reference

Critical: the class `extract()` output shapes MUST be preserved exactly.

| Extractor | Dataset | Output shape | Key constraint |
|-----------|---------|-------------|----------------|
| `Stage1Extractor.extract(df)` | botsim | `[N, 10]` float32 | 10 columns per `features_stage1.py` stack |
| `Stage1Extractor.extract(df)` | twibot | `[N, 14]` float32 | `STAGE1_TWITTER_COLUMNS` has 14 entries |
| `Stage2Extractor.extract(df, embedder)` | botsim | `[N, 397]` float32 | 384 emb + 4 ling + 7 temporal + 2 sim = 397 |
| `Stage2Extractor.extract(df, embedder)` | twibot | `[N, 393]` float32 | 384 emb + 4 ling + 5 extras (no temporal) = 393 |
| `Stage3Extractor.extract(accounts_df, edges_df)` | twibot | `[N, 18]` float32 | `STAGE3_TWITTER_COLUMNS` has 18 entries |
| `build_graph_features_nodeidx(...)` | any | `[N, 6 + 4*n_types]` float32 | n_types=3 → 18 cols |

The botsim Stage 2 vector layout documented in `tests/test_features_stage2.py`:
- `[0..383]` emb_pool (384-dim)
- `[384..387]` ling_pool (4-dim)
- `[388]` rate, `[389]` delta_mean, `[390]` delta_std, `[391]` cv_intervals
- `[392]` char_len_mean, `[393]` char_len_std, `[394]` hour_entropy
- `[395]` cross_msg_sim_mean, `[396]` near_dup_frac

The twibot Stage 2 column list per `STAGE2_TWITTER_COLUMNS`:
- 384 `emb_*` + `char_len_mean`, `token_uniq_ratio_mean`, `punct_ratio_mean`, `digit_ratio_mean`
- `message_count`, `char_len_std`, `cross_msg_sim_mean`, `near_dup_frac`, `nonempty_frac`

**The two Stage 2 paths are NOT compatible** — different column counts, different
temporal handling. Dataset branching inside the class is mandatory.

## Import Chain Impact

### Files whose imports change in Phase 17

| File | Old import | New import |
|------|-----------|------------|
| `features_stage3_twitter.py` | `from botdetector_pipeline import build_graph_features_nodeidx` | Replaced by inlining `build_graph_features_nodeidx` in `features/stage3.py` |

Note: `botdetector_pipeline.py` currently imports `from features_stage1 import ...` and
`from features_stage2 import ...`. These imports are NOT changed in Phase 17 — that is
Phase 18's job. The new `features/` package is created alongside the old files.

### Files that import LSTM symbols (must be sanitized)

| File | LSTM symbols imported |
|------|----------------------|
| `main.py` | `Stage2LSTMRefiner`, `apply_stage2b_refiner`, `extract_message_embedding_sequences_for_accounts` |
| `botdetector_pipeline.py` | defines them (source of deletion) |
| `tests/conftest.py` | `Stage2LSTMRefiner`, `extract_message_embedding_sequences_for_accounts` |
| `tests/conftest.py` | `minimal_lstm_stage2b_inputs` fixture (entire fixture must be removed) |

All four of these files must be touched in Phase 17 (to remove LSTM imports/usage).
`main.py` will fail at import time if LSTM symbols are deleted without cleaning up main.py.

## Common Pitfalls

### Pitfall 1: Broken imports cause silent runtime failures, not syntax errors

**What goes wrong:** `main.py` imports `Stage2LSTMRefiner` at the top level. If the symbol
is deleted from `botdetector_pipeline.py` without updating `main.py`, the entire script
fails at import time — not when the LSTM code path is exercised.

**Why it happens:** Python's top-level import runs unconditionally.

**How to avoid:** After deleting LSTM symbols, immediately grep for all their usages
across the repo and remove or replace each reference before running any tests.

**Warning signs:** `ImportError: cannot import name 'Stage2LSTMRefiner'` in test output.

### Pitfall 2: `features_stage3_twitter.py` imports from `botdetector_pipeline.py`

**What goes wrong:** `features_stage3_twitter.py` does
`from botdetector_pipeline import build_graph_features_nodeidx`. After Phase 17,
`build_graph_features_nodeidx` lives in `features/stage3.py`. If `features_stage3_twitter.py`
is not updated (or deprecated), tests that import from it will get the stale copy or fail.

**How to avoid:** When writing `features/stage3.py`, also update (or mark deprecated)
`features_stage3_twitter.py`. Since Phase 17 context says old files are "deleted or
deprecated," this file should import from `features.stage3` rather than from the pipeline.

### Pitfall 3: `conftest.py` LSTM fixture creates a `TrainedSystem` with LSTM fields

**What goes wrong:** `conftest.py` constructs `TrainedSystem(...)` without positional
LSTM args (fields default to `None`), but it also has the `minimal_lstm_stage2b_inputs`
fixture that imports `Stage2LSTMRefiner`. After LSTM deletion, `conftest.py` will fail
to import, breaking every test.

**How to avoid:** The `minimal_lstm_stage2b_inputs` fixture must be deleted from
`conftest.py`. Also verify `TrainedSystem` no longer has `stage2b_lstm` / `stage2b_variant`
fields so the existing `minimal_system` fixture construction still works.

### Pitfall 4: `_MISSING_TEMPORAL_SENTINEL` is a behavioral constant, not a magic number

**What goes wrong:** The sentinel value `-1.0` appears in Stage 2 botsim path to
distinguish "messages exist but all timestamps are missing" from "no messages." If this
is accidentally omitted or set to `0.0` during the class conversion, zero-shot transfer
accuracy drops silently.

**How to avoid:** Copy `_MISSING_TEMPORAL_SENTINEL = -1.0` verbatim. Verify it is used in
the three temporal feature positions (`rate`, `delta_mean`, `delta_std`) and `cv_intervals`
and `hour_entropy` when `temporal_missing` is True.

### Pitfall 5: Stage 2 botsim `probe_dim` initialization across rows

**What goes wrong:** The botsim Stage 2 loop initializes `probe_dim = None` outside the
row loop and sets it on first successful encode call. If all rows have empty messages
(e.g., in small test DataFrames), `probe_dim` falls back to 384. This logic must be
preserved exactly when moving to the class method body.

**How to avoid:** Copy the probe_dim initialization pattern verbatim; do not simplify
it to a fixed constant even though 384 is always the effective value.

### Pitfall 6: `twibot20_io.parse_tweet_types` is called from `features_stage1_twitter.py`

**What goes wrong:** `features_stage1_twitter.py` imports `parse_tweet_types` from
`twibot20_io`. After moving the Stage 1 logic into `features/stage1.py`, that import
must also move there: `from twibot20_io import parse_tweet_types` in `features/stage1.py`.

**How to avoid:** Check all imports in each source file before copying its body.

### Pitfall 7: `apply_stage2b_refiner` still used in `botdetector_pipeline.py` train and predict paths

**What goes wrong:** Both `train_system` and `predict_system` call `apply_stage2b_refiner`.
Deleting this function without inlining the AMR-only path into both callers will break
training and inference.

**How to avoid:** Replace both call sites with the inlined AMR path:
```python
# inline replacement for apply_stage2b_refiner (AMR-only)
h_amr = extract_amr_embeddings_for_accounts(df[route_mask], cfg, embedder)
z2[route_mask] = amr_refiner.refine(z2[route_mask], h_amr)
```
Then delete `apply_stage2b_refiner` and `normalize_stage2b_variant`.

## Runtime State Inventory

This is a refactor/rename-class phase. Checking all five categories:

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | `trained_system.joblib`, `trained_system_stage2b_amr.joblib`, `trained_system_stage2b_lstm.joblib` at repo root — these contain pickled `TrainedSystem` objects with `stage2b_lstm` and `stage2b_variant` fields | These artifacts are stale pre-v1.5. Phase 19 will retrain and overwrite them. No migration needed — they are ignored in v1.5 (new artifact names are `trained_system_botsim.joblib` / `trained_system_twibot.joblib`). |
| Live service config | None — no running services, no n8n, no external config stores | None |
| OS-registered state | None — no scheduled tasks, no pm2, no launchd plists | None |
| Secrets/env vars | None — no secret keys reference stage class names | None |
| Build artifacts | `__pycache__/` directories throughout repo — will cache old `.pyc` files from deleted modules | Python regenerates these automatically; no manual action needed |

**Stale joblib artifacts:** the three `.joblib` files at repo root contain pickled
`TrainedSystem` objects that include `stage2b_lstm` and `stage2b_variant` fields. After
Phase 17 removes those fields from the `TrainedSystem` dataclass, loading these old
artifacts with `joblib.load` will produce objects with unexpected attributes (Python
dataclasses don't enforce field presence on unpickled objects, so this is a silent
mismatch, not an error). Since Phase 19 retrains from scratch, this is not a blocker —
but tests that load these artifacts (none appear in the test suite) would be affected.

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python (bash) | All | ✓ | 3.x (Windows) | — |
| pytest | Test suite | ✓ | installed (tests/ present) | — |
| numpy | All extractors | ✓ | installed | — |
| pandas | All extractors | ✓ | installed | — |

No new dependencies are introduced. All required tools are available. [VERIFIED: codebase inspection]

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest |
| Config file | none detected (no pytest.ini / pyproject.toml) |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -q` |
| Known Windows friction | `tmp_path` cleanup permissions (pre-existing, does not affect production code) |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|--------------|
| CORE-01 | `Stage1Extractor('botsim').extract(df)` and `Stage1Extractor('twibot').extract(df)` return correct shapes | unit | `pytest tests/test_features_stage1.py -x` | ❌ Wave 0 |
| CORE-01 | `load_dataset('botsim', ...)` and `load_dataset('twibot', ...)` dispatch correctly | unit | `pytest tests/test_data_io.py -x` | ❌ Wave 0 |
| CORE-02 | `Stage2Extractor('botsim').extract(df, embedder)` returns 397-dim array | unit | `pytest tests/test_features_stage2.py -x` | ✅ (must update import) |
| CORE-02 | `Stage2Extractor('twibot').extract(df, embedder)` returns 393-dim array | unit | `pytest tests/test_features_stage2_twitter.py -x` | ✅ (must update import) |
| CORE-02 | `Stage3Extractor` produces same output as old `extract_stage3_features_twitter` | unit | `pytest tests/test_features_stage3_twitter.py -x` | ✅ (must update import) |
| CORE-05 | `Stage2LSTMRefiner` import raises `ImportError` from `botdetector_pipeline` | unit | `pytest tests/test_lstm_removed.py -x` | ❌ Wave 0 |
| CORE-05 | `TrainedSystem` has no `stage2b_lstm` or `stage2b_variant` field | unit | `pytest tests/test_lstm_removed.py -x` | ❌ Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -q`
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps

- [ ] `tests/test_features_stage1.py` — covers CORE-01 (Stage1Extractor botsim + twibot paths)
- [ ] `tests/test_data_io.py` — covers CORE-01 (load_dataset dispatch, both datasets)
- [ ] `tests/test_lstm_removed.py` — covers CORE-05 (import check, TrainedSystem field check)
- [ ] Update `tests/conftest.py` — remove `minimal_lstm_stage2b_inputs` fixture and LSTM imports
- [ ] Update `tests/test_features_stage2.py` — change `from features_stage2 import ...` to `from features.stage2 import Stage2Extractor`
- [ ] Update `tests/test_features_stage2_twitter.py` — same pattern
- [ ] Update `tests/test_features_stage1_twitter.py` — update to use `Stage1Extractor('twibot')`
- [ ] Update `tests/test_features_stage3_twitter.py` — update to use `Stage3Extractor` or `build_graph_features_nodeidx` from `features.stage3`

## Security Domain

No authentication, no network I/O, no user input, no cryptography introduced or modified.
This phase is pure code reorganization within a local Python project. ASVS categories do
not apply. [ASSUMED — no CLAUDE.md found with security directives]

## Open Questions

1. **`extract_amr_embeddings_for_accounts` — stays in pipeline or moves to features/stage2.py?**
   - What we know: CONTEXT.md says "stays or moves to features/stage2.py as a method"
   - What's unclear: If it moves, `botdetector_pipeline.py` must import from `features.stage2`, which Phase 18 is supposed to handle
   - Recommendation: Move it to `Stage2Extractor` as a method `extract_amr(df, embedder)` in Phase 17 since all AMR extraction logic is extraction, not pipeline. Update the single call site in `botdetector_pipeline.py` immediately (it is a small, localized change).

2. **Should the old `features_stage*.py` files be deleted in Phase 17 or just deprecated?**
   - What we know: CONTEXT.md says "deleted or deprecated." `botdetector_pipeline.py` still imports from `features_stage1.py` and `features_stage2.py` — those imports are Phase 18's job.
   - What's unclear: Deleting the old files in Phase 17 would break `botdetector_pipeline.py` imports before Phase 18 fixes them.
   - Recommendation: Deprecate (add a `# deprecated: use features.stage1` comment at the top) rather than delete in Phase 17. Full deletion happens in Phase 18 alongside import updates.

## Sources

### Primary (HIGH confidence)

- `features_stage1.py` — verified: 10-column botsim Stage 1 matrix
- `features_stage1_twitter.py` — verified: 14-column twibot Stage 1 matrix, `STAGE1_TWITTER_COLUMNS`
- `features_stage2.py` — verified: 397-dim botsim Stage 2 vector, `_MISSING_TEMPORAL_SENTINEL`
- `features_stage2_twitter.py` — verified: 393-dim twibot Stage 2 vector, `STAGE2_TWITTER_COLUMNS`
- `features_stage3_twitter.py` — verified: 18-column Stage 3 wrapper, imports from pipeline
- `botdetector_pipeline.py` — verified: exact lines for LSTM classes, `build_graph_features_nodeidx`, `TrainedSystem` dataclass fields
- `botsim24_io.py` — verified: `load_users_csv`, `load_user_post_comment_json`, `build_account_table`
- `twibot20_io.py` — verified: `load_accounts`, `build_edges`, `parse_tweet_types`
- `tests/conftest.py` — verified: LSTM fixture, `minimal_system` construction
- `tests/test_features_stage2.py` — verified: exact Stage 2 column layout comment
- `.planning/phases/17-shared-feature-extraction-module/17-CONTEXT.md` — locked decisions D-01 through D-11

### Secondary (MEDIUM confidence)

- `.planning/REQUIREMENTS.md` — CORE-01, CORE-02, CORE-05 descriptions

## Metadata

**Confidence breakdown:**
- Symbol inventory: HIGH — read every source file
- Output contracts: HIGH — read existing tests and source code
- Import impact: HIGH — traced all import chains manually
- Test gap list: HIGH — inventoried existing test files
- LSTM deletion scope: HIGH — read all LSTM class definitions and every call site

**Research date:** 2026-04-18
**Valid until:** Indefinite — this is a pure codebase analysis, not API/library research
