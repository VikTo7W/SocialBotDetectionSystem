# Codebase Concerns

**Analysis Date:** 2026-03-18

## Tech Debt

### AMR Parsing Stub Implementation

**Issue:** AMR (Abstract Meaning Representation) parsing is not implemented—currently a pass-through stub that returns input text unchanged.

**Files:** `botdetector_pipeline.py:123-128`
```python
def amr_linearize_stub(text: str) -> str:
    """Replace this with actual AMR parsing + linearization. For now it's a stub that returns the original text."""
    return text
```

**Impact:** Stage 2 AMR delta refinement (`AMRDeltaRefiner`) trains on non-meaningful representations. AMR embeddings are computed on raw text rather than semantic graph linearizations, potentially degrading semantic understanding of accounts. The system cannot leverage structured semantic features for distinguishing sophisticated bot behavior.

**Fix approach:** Integrate a real AMR parser (e.g., `amrlib`, `ibm-transition-amr`) to parse social media text into AMR graphs, linearize them, and pass linearized representations to the embedder. This requires:
1. Installing AMR parser + model weights
2. Error handling for unparseable text
3. Performance optimization (AMR parsing is slow; consider caching or batch processing)

---

### Hardcoded Embedding Dimension

**Issue:** Embedding dimension hardcoded in two places, both assuming sentence-transformers MiniLM model (384 dims).

**Files:**
- `botdetector_pipeline.py:641`: `H_amr = np.zeros((len(df), 384), dtype=np.float32)  # if MiniLM; adjust if needed`
- `features_stage2.py:63`: `probe_dim = 384`

**Impact:** If embedding model changes (e.g., to a larger model like `all-mpnet-base-v2` with 768 dims), Stage 2 initialization will fail silently, creating dimension mismatches and silent NaN propagation. Memory allocation might be too small or too large.

**Fix approach:** Query embedding dimension dynamically:
```python
# Determine dimension from first batch
sample_emb = embedder.encode(["test"])
embedding_dim = sample_emb.shape[1]
```
Store this in `FeatureConfig` or as a model attribute to ensure consistency across all stages.

---

### Bare Exception Handling

**Issue:** Two broad exception handlers that catch all errors indiscriminately.

**Files:**
- `botdetector_pipeline.py:17-21`: LightGBM import fallback
- `botsim24_io.py:20-24`: DateTime parsing

**Impact:**
- LightGBM fallback silently accepts any error (network, permission denied, out of memory) and falls back to slower HistGradientBoostingClassifier
- DateTime parsing silently returns None for any parse error, including legitimate data issues that should be logged for debugging

**Fix approach:** Catch specific exceptions:
```python
try:
    import lightgbm as lgb
    HAS_LGB = True
except ImportError:  # Specific to missing module
    HAS_LGB = False
    from sklearn.ensemble import HistGradientBoostingClassifier
```

For datetime:
```python
except ValueError as e:  # Specific to parse failure
    logger.warning(f"Failed to parse datetime '{dt_str}': {e}")
    return None
```

---

## Known Bugs

### Configuration Parameter Not Passed to extract_stage1_matrix

**Issue:** `main.py:96` passes `cfg=None` to `train_system()`, but `extract_stage1_matrix()` signature in `botdetector_pipeline.py:630` expects it as a parameter.

**Files:**
- `main.py:96`: `cfg=None`
- `botdetector_pipeline.py:630`: `X1 = extract_stage1_matrix(df, cfg)`
- BUT: `features_stage1.py:5` signature is `extract_stage1_matrix(df: pd.DataFrame)` (no cfg param)

**Impact:** Inconsistent function signatures. Current `features_stage1.py` implementation doesn't use cfg, so it works, but `botdetector_pipeline.py:630` passes cfg anyway. This creates confusion about which columns are being used and makes future refactoring risky.

**Fix approach:**
1. Update `botdetector_pipeline.py:630` to remove cfg parameter: `X1 = extract_stage1_matrix(df)`
2. OR add cfg to `features_stage1.py` and select columns dynamically
3. Document the fixed Stage 1 columns clearly

---

### Stage 3 Disabled by Default Without Warning

**Issue:** `main.py:85-88` disables Stage 3 routing by setting impossible thresholds:
```python
th.s12_human = 1.0
th.s12_bot = 0.0
th.novelty_force_stage3 = 1e9
```

**Impact:** Stage 3 (structural features from graph) never activates in the main pipeline. Meta123 model trains but never predicts on S3. Final predictions only use Stage 1 + Stage 2, ignoring graph structure completely. This is intentional (per comment "Disable Stage 3 routing safely") but easily missed by future developers.

**Fix approach:**
1. Add explicit flag `enable_stage3 = False` to config
2. Add logging warning: `logger.warning("Stage 3 disabled in routing thresholds")`
3. Document in README why Stage 3 is disabled (e.g., incomplete graph coverage)

---

### Dimension Mismatch Risk in extract_stage2_features

**Issue:** `features_stage2.py:57-64` detects embedding dimension dynamically, but if first account has no text to embed, falls back to hardcoded 384. Subsequent accounts must all have same dimension.

**Files:** `features_stage2.py:55-64`

**Impact:** If first account is empty and uses fallback 384, but second account encodes with embedder returning 768 dims, stack operation will fail with shape mismatch. This is a fragile edge case.

**Fix approach:**
```python
# Determine from embedder directly, not from first batch
embedding_dim = embedder.model.get_sentence_embedding_dimension()
```
Or validate all embeddings have same shape:
```python
assert emb.shape[1] == probe_dim, f"Dimension mismatch: got {emb.shape[1]}, expected {probe_dim}"
```

---

## Security Considerations

### No Input Validation on DataFrames

**Issue:** Pipeline functions assume well-formed DataFrames without validation.

**Files:**
- `botdetector_pipeline.py`: `train_system()`, `predict_system()`
- `features_stage1.py`: `extract_stage1_matrix()`
- `features_stage2.py`: `extract_stage2_features()`

**Impact:**
- Missing required columns raise unhelpful KeyError
- NaN/inf values propagate silently through pipeline (some handling with `np.nan_to_num` but not comprehensive)
- Malformed edge DataFrames could cause numpy indexing errors
- No bounds checking on account IDs or node indices

**Fix approach:** Add schema validation at entry points:
```python
def validate_accounts_df(df):
    required = {"account_id", "label", "username", "messages", "node_idx"}
    missing = required - set(df.columns)
    if missing:
        raise ValueError(f"Missing columns: {missing}")
```

---

### No Rate Limiting or Resource Bounds on Text Embedding

**Issue:** `extract_stage2_features()` encodes all messages for all accounts in one batch without memory or computation time limits.

**Files:** `features_stage2.py:56`

**Impact:**
- Single account with 1000+ messages (due to data corruption) could cause OOM
- Large batch encoding can timeout or hang
- No progress indication for long-running embedding jobs

**Fix approach:**
1. Enforce stricter limits on messages per account (already configurable as `max_msgs=50`)
2. Add timeout wrapper around embedder calls
3. Log progress and memory usage for debugging

---

## Performance Bottlenecks

### Inefficient DataFrame Iteration

**Issue:** Multiple `iterrows()` loops on large DataFrames.

**Files:**
- `botdetector_pipeline.py:142`: Loop over accounts to build AMR texts
- `botsim24_io.py:108`: Loop over users to build account table
- `features_stage2.py:31`: Loop over accounts to extract features

**Impact:** `iterrows()` is known to be slow (creates Series objects for each row). On BotSim-24 (2907 accounts), this adds unnecessary overhead. Memory-inefficient for large datasets.

**Fix approach:** Use vectorized operations or `apply()`:
```python
# Instead of:
amr_texts = []
for _, r in df.iterrows():
    amr_texts.append(amr_linearize_stub(r.get(text_field) or ""))

# Use:
amr_texts = df[text_field].fillna("").apply(amr_linearize_stub).tolist()
```

---

### Matrix Inverse in Novelty Detection

**Issue:** `MahalanobisNovelty.fit()` computes matrix inverse directly.

**Files:** `botdetector_pipeline.py:54-59`
```python
cov = LedoitWolf().fit(X).covariance_
self.prec_ = np.linalg.inv(cov)
```

**Impact:**
- Matrix inversion is numerically unstable and slow for high-dimensional data
- No error handling for singular matrices
- Computing inverse then using it in `einsum()` is less stable than solving linear system

**Fix approach:** Use `np.linalg.solve()` or pre-compute Cholesky decomposition:
```python
from scipy.linalg import solve
# In score(): solve(cov, d.T).T instead of d @ inv(cov)
```

---

### Batch Encoding of All Text at Once

**Issue:** `extract_stage2_features()` calls `embedder.encode(texts)` where texts can be 50+ messages per account.

**Files:** `features_stage2.py:56`

**Impact:** Total text load for 2907 accounts × 50 messages × 500 chars = 72.6 MB of text, all embedded in one or few batches. Sentence-transformers batch size default is 32; with 2907 accounts, this triggers many back-and-forth passes to GPU/CPU.

**Fix approach:**
1. Increase batch size in embedder.encode() call
2. Consider hierarchical pooling (embed per message, then pool per account)
3. Profile embedding time with `time.perf_counter()` to validate improvement

---

## Fragile Areas

### edge_index.pt Coverage Unknown

**Issue:** Main pipeline loads `.pt` files (`edge_index.pt`, `edge_type.pt`, `edge_weight.pt`) but doesn't validate they cover all accounts.

**Files:** `main.py:63-74`

**Impact:**
- If edge files only cover subset of users, graph-based features (Stage 3) will be meaningless for uncovered nodes
- Silent failure: `build_graph_features_nodeidx()` will compute degrees as 0 for disconnected nodes
- Comment in `main.py:59-61` acknowledges uncertainty: "you said you're not sure if they're full graph"

**Fix approach:**
1. Add validation after loading edges:
```python
covered_nodes = set(edges_df["src"].unique()) | set(edges_df["dst"].unique())
missing = set(accounts["node_idx"]) - covered_nodes
if len(missing) > 0:
    logger.warning(f"Edge data missing {len(missing)} nodes ({100*len(missing)/len(accounts):.1f}%)")
```
2. Document edge file coverage expectations in README

---

### Threshold Tuning Not Documented

**Issue:** `StageThresholds` dataclass has many magic numbers without justification or tuning procedure.

**Files:** `botdetector_pipeline.py:155-171`

**Impact:** Thresholds (0.98 bot, 0.02 human, novelty=3.0, disagreement=4.0) appear arbitrary. No guidance on how to tune them. Changing one threshold might break decision logic downstream. Easy to introduce bugs when experimenting.

**Fix approach:**
1. Add docstrings to each threshold explaining its purpose
2. Create a tuning notebook or script that validates thresholds on validation set (S2)
3. Log which thresholds triggered routing for each sample (debugging)

---

### Missing Error Handling in Edge Filtering

**Issue:** `filter_edges_for_split()` silently drops edges between train/test splits without logging.

**Files:** `main.py:10-13`

**Impact:**
- If edge file is outdated and references deleted accounts, silent data loss
- No visibility into how many edges are lost
- Future data updates might silently degrade graph quality

**Fix approach:**
```python
def filter_edges_for_split(edges_df: pd.DataFrame, node_ids: np.ndarray) -> pd.DataFrame:
    node_set = set(node_ids.tolist())
    m = edges_df["src"].isin(node_set) & edges_df["dst"].isin(node_set)
    kept = m.sum()
    dropped = (~m).sum()
    logger.info(f"Edges: kept {kept}, dropped {dropped}")
    return edges_df[m].reset_index(drop=True)
```

---

## Scaling Limits

### In-Memory Adjacency Operations

**Issue:** Graph feature computation uses dense numpy arrays and aggregation via `np.add.at()`.

**Files:** `botdetector_pipeline.py:350-392`

**Impact:**
- For large graphs (>100k nodes), in-degree/out-degree arrays are dense [num_nodes_total] - wastes memory for sparse graphs
- Computing per-type degrees multiplies memory by n_types
- No sparse matrix support

**Current capacity:** BotSim-24 has ~2907 nodes, manageable
**Limit:** 100k+ nodes would require ~1GB+ for dense arrays alone

**Fix approach:** Use sparse adjacency for large graphs:
```python
from scipy.sparse import csr_matrix
adj = csr_matrix((w, (src, dst)), shape=(num_nodes, num_nodes))
in_deg = np.asarray(adj.sum(axis=0)).flatten()  # Column sums
```

---

### Single-Machine Training Only

**Issue:** No distributed training support. All data loaded into RAM, all models trained on single machine.

**Files:** `botdetector_pipeline.py`, `main.py`

**Impact:**
- BotSim-24: ~80MB JSON, fits in RAM ✓
- Larger datasets (>1M accounts): likely OOM
- Text embedding is slow on CPU; no multi-GPU support

**Scaling path:**
1. For data loading: Stream data in batches from disk/database
2. For embedding: Multi-GPU with `device_map="auto"` or distributed inference (Ray, vLLM)
3. For training: Use mini-batch training (online learning) instead of full batch

---

## Dependencies at Risk

### LightGBM Optional but Silently Falling Back

**Issue:** Code prefers LightGBM (faster, better params) but silently accepts sklearn's HistGradientBoostingClassifier if LightGBM unavailable.

**Files:** `botdetector_pipeline.py:17-22, 183-193, 225-235, 316-326`

**Impact:**
- Model quality variance: LightGBM with 400-600 estimators != sklearn's defaults
- Hyperparameters hardcoded for LGB (num_leaves=31, subsample=0.9); sklearn uses different semantics
- No logging of which was used → hard to debug result differences

**Fix approach:**
1. Make LightGBM required (add to requirements.txt)
2. OR add explicit `use_lgb` flag and log which backend is used
3. If using sklearn fallback, adjust hyperparameters to be equivalent

---

### Sentence-Transformers Download on First Run

**Issue:** `TextEmbedder.__init__()` downloads model weights on first instantiation.

**Files:** `botdetector_pipeline.py:91-93`

**Impact:**
- First pipeline run downloads ~350MB (all-MiniLM-L6-v2)
- No progress indication
- Network failure causes pipeline crash
- No local cache strategy for offline use

**Fix approach:**
1. Add explicit download step in setup/installation
2. Use environment variable for cache directory: `SENTENCE_TRANSFORMERS_HOME`
3. Catch download errors with helpful message:
```python
try:
    self.model = SentenceTransformer(model_name, device=device)
except Exception as e:
    raise RuntimeError(f"Failed to load embedder '{model_name}': {e}. Try downloading manually.")
```

---

## Missing Critical Features

### No Model Checkpointing

**Issue:** Trained models not saved or loaded. Must retrain every run.

**Files:** `main.py`, `botdetector_pipeline.py`

**Impact:**
- 5-10 minutes of training time per evaluation (estimate)
- Experimentation is slow
- Can't deploy without source code

**Fix approach:** Add save/load:
```python
import pickle
# After training
with open("model.pkl", "wb") as f:
    pickle.dump(sys, f)
# For inference
with open("model.pkl", "rb") as f:
    sys = pickle.load(f)
```

---

### No Prediction Confidence Intervals

**Issue:** System returns point probabilities with no uncertainty estimates.

**Files:** `botdetector_pipeline.py:617-696` (predict_system)

**Impact:**
- Can't distinguish high-confidence "bot" from uncertain "bot"
- No way to flag low-confidence predictions for human review
- Operations team has no metric for when to distrust model

**Fix approach:** Add prediction variance:
```python
# Use Platt scaling variance or ensemble disagreement
p_std = meta123.predict_proba(X) - p_final  # disagreement between stages
```

---

### No Monitoring or Logging

**Issue:** No logging throughout pipeline. Only prints to stdout.

**Files:** All files

**Impact:**
- Production runs leave no audit trail
- Can't debug failures without re-running
- No visibility into which thresholds triggered routing
- Can't measure inference latency

**Fix approach:** Add structured logging:
```python
import logging
logger = logging.getLogger(__name__)

# In predict_system():
logger.info(f"Stage 3 routed {stage3_mask.sum()}/{len(df)} accounts")
logger.debug(f"p_final range: [{p_final.min():.3f}, {p_final.max():.3f}]")
```

---

## Test Coverage Gaps

### No Unit Tests

**Issue:** Only one test file (`test.py`) which appears to be ad-hoc inspection, not unit tests.

**Files:** `test.py` (95 lines)

**Impact:**
- No regression detection when refactoring
- Bug fixes can't be validated with tests
- Feature extraction logic untested
- Model serialization not tested

**What's not tested:**
- `extract_stage1_matrix()` with edge cases (all NaN, missing columns, zero values)
- `extract_stage2_features()` with empty messages, malformed data
- `MahalanobisNovelty` with singular covariance
- Threshold routing logic with boundary conditions (p=0.5 exactly)
- OOF prediction consistency

**Priority:** High - these are critical data pipeline functions

**Fix approach:** Create `tests/` directory with pytest:
```python
def test_extract_stage1_matrix_missing_column():
    df = pd.DataFrame({"username": ["test"], "submission_num": [1.0]})  # missing columns
    with pytest.raises(KeyError):
        extract_stage1_matrix(df)
```

---

### No Integration Tests

**Issue:** No end-to-end validation of train → predict pipeline.

**Impact:**
- Dimension mismatches between train and prediction not caught until runtime
- Model serialization format changes break silently
- Edge cases in data processing (all humans, all bots) not tested

**Fix approach:** Create integration test:
```python
def test_train_predict_integration():
    # Minimal S1, S2, S3 splits
    sys = train_system(S1_mini, S2_mini, edges_mini, edges_mini, cfg, th)
    out = predict_system(sys, S3_mini, edges_mini)
    assert out["p_final"].shape == (len(S3_mini),)
    assert (out["p_final"] >= 0.0).all() and (out["p_final"] <= 1.0).all()
```

---

*Concerns audit: 2026-03-18*
