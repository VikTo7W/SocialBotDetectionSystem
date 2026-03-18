# Testing Patterns

**Analysis Date:** 2026-03-18

## Test Framework

**Status:**
- No formal testing framework configured or in use
- No pytest, unittest, or similar test runner dependencies
- Single test file `test.py` exists but contains inspection utilities, not test cases

**Testing Approach:**
- Manual testing via script execution
- Validation through assertion statements in main execution
- Integration testing through running full pipeline in `main.py`

## Test File Organization

**Location:**
- `test.py` located at project root alongside main execution scripts
- Not following standard test directory structure (`tests/`, `test_*.py` naming)

**Current Test File:**
- `test.py` contains `inspect_pt()` utility function for diagnosing PyTorch tensor files
- Purpose: Debug/inspect saved `.pt` files (edge_index, edge_type, edge_weight)
- Not automated test suite

**Naming Convention:**
- Main orchestration: `main.py`
- Utility inspection: `test.py`
- Feature extraction modules: `features_stage*.py`
- Data I/O: `botsim24_io.py`
- Pipeline logic: `botdetector_pipeline.py`

## Testing Strategy

**Current Approach:**
- **Integration Testing Only**: Full pipeline executed end-to-end in `main.py`
- **Assertion-based Validation**: Single assertion in pipeline:
  ```python
  assert accounts["node_idx"].isna().sum() == 0, "Some accounts have no node_idx mapping."
  ```
- **Manual Inspection**: `test.py` provides `inspect_pt()` for examining tensor data

## Data Validation

**Patterns:**
- CSV loading with type coercion and null handling:
  ```python
  df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(np.float32)
  ```
- Silent graceful degradation in parsing:
  ```python
  try:
      v = ast.literal_eval(s)
  except Exception:
      pass  # continue with alternative parsing
  ```
- Timestamp parsing with None fallback:
  ```python
  try:
      dt = datetime.strptime(dt_str, DATETIME_FMT).replace(tzinfo=timezone.utc)
      return dt.timestamp()
  except Exception:
      return None
  ```

## Model Validation

**Patterns Used:**
- Check fitted state before prediction:
  ```python
  if self.cal is None:
      raise RuntimeError("Stage1 not fitted.")
  ```
- Optional field None-checking:
  ```python
  if self.mu_ is None or self.prec_ is None:
      raise RuntimeError("Novelty model not fitted.")
  ```
- Numerical stability guards:
  ```python
  X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
  return np.sqrt(np.maximum(m2, 0.0))
  ```

## Feature Extraction Testing

**Implicit Validation:**
- Output shape consistency: `np.stack([...], axis=1)` ensures consistent column count
- Type enforcement: `astype(np.float32)` ensures uniform dtype
- NaN handling in ratios:
  ```python
  eps = 1e-6
  post_c1 = post_num / (c1 + eps)
  ```

**Example from `features_stage1.py`:**
```python
def extract_stage1_matrix(df: pd.DataFrame) -> np.ndarray:
    # All output columns constructed with type guarantees
    name_len = df["username"].fillna("").astype(str).map(len).to_numpy(dtype=np.float32)
    # ...
    X = np.nan_to_num(X, nan=0.0, posinf=0.0, neginf=0.0)
    return X  # Guaranteed: shape=(N, 10), dtype=float32, no NaNs
```

## Data Flow Testing (Integration)

**Pipeline Stages Tested via Main:**
1. Data loading: `load_users_csv()`, `load_user_post_comment_json()`, `build_account_table()`
2. Train/val/test splitting with stratification
3. Edge filtering for subset consistency
4. Feature extraction stages (S1, S2, S3)
5. Model training across stages
6. Out-of-fold meta model predictions
7. Final inference and output generation

**Execution Path in `main.py`:**
```python
if __name__ == "__main__":
    # Load and validate data
    users = load_users_csv("Users.csv")
    accounts = build_account_table(users, upc)
    assert accounts["node_idx"].isna().sum() == 0, "..."

    # Split data
    S1, S2, S3 = train_test_split(...)

    # Extract edges
    edges_S1 = filter_edges_for_split(edges_df, S1["node_idx"].to_numpy())
    edges_S2 = filter_edges_for_split(edges_df, S2["node_idx"].to_numpy())
    edges_S3 = filter_edges_for_split(edges_df, S3["node_idx"].to_numpy())

    # Train system
    sys = train_system(S1, S2, edges_S1, edges_S2, ...)

    # Evaluate
    out = predict_system(sys, df=S3, edges_df=edges_S3, ...)
    print(classification_report(y_true, y_pred, digits=4))
```

## Mocking Patterns

**Not Used:**
- No test mocks or fixtures
- Direct use of real data files: `Users.csv`, `user_post_comment.json`, `.pt` tensor files
- Embedder and models initialized with real weights/models

**Conditional Dependencies:**
```python
try:
    import lightgbm as lgb
    HAS_LGB = True
except Exception:
    HAS_LGB = False
    from sklearn.ensemble import HistGradientBoostingClassifier
```
- Graceful fallback if LightGBM unavailable

## Test Coverage

**Status:** Not measured - no coverage tools configured

**Implicit Coverage:**
- All major function paths executed in `main.py`
- Stage 1, Stage 2, Stage 3 models trained and evaluated
- AMR refinement applied when gated
- Meta12 and Meta123 models trained via OOF predictions
- Output generation and classification report printed

**Gaps:**
- No explicit error case testing
- No edge case coverage (empty inputs, all NaN values, single-sample datasets)
- No parameter sensitivity testing
- No unit tests for individual feature extraction functions
- No novelty scorer validation on known distributions

## Model Evaluation

**Metrics Computed:**
```python
from sklearn.metrics import classification_report

y_true = S3["label"].to_numpy()
y_pred = (out["p_final"].to_numpy() >= 0.5).astype(int)
print(classification_report(y_true, y_pred, digits=4))
```

**Output Format:**
- Precision, recall, F1-score per class (human/bot)
- Macro and weighted averages
- Support (number of samples per class)

## Data Splitting for Evaluation

**Pattern:** Stratified train/val/test with manual split workflow:
```python
from sklearn.model_selection import train_test_split

# Stage 1: Training set for stage models
S1, S2_and_S3 = train_test_split(
    accounts,
    test_size=0.30,
    stratify=accounts["label"],
    random_state=SEED
)

# Stage 2: Validation for meta models
S2, S3 = train_test_split(
    S2_and_S3,
    test_size=0.50,
    stratify=S2_and_S3["label"],
    random_state=SEED
)
```

**Rationale:**
- S1: Trains all stage models (1, 2a, 3)
- S2: Trains meta models with OOF predictions from S1-trained models
- S3: Final evaluation set, unseen during training

## Validation Patterns

**Data Type Validation:**
- `astype(dtype)` enforced throughout feature extraction
- `pd.to_numeric(..., errors="coerce")` in data loading

**Consistency Validation:**
- Graph node coverage: `filter_edges_for_split()` ensures edges only reference nodes in subset
- Feature dimension matching: NumPy stack operations fail loudly if shape mismatch

**Statistical Validation:**
- Label balance checked: `print(accounts["label"].value_counts())`
- Class weight handling: `LogisticRegression(..., class_weight="balanced")`

## Missing Test Infrastructure

**Not Present:**
- pytest configuration (`pytest.ini`, `pyproject.toml`)
- unittest base classes
- Fixtures or factories for test data
- Parametrized tests
- Continuous integration (no `.github/workflows/`, no `.gitlab-ci.yml`)
- Test dependency specification (no `requirements-dev.txt`)

**Recommendations for Future Testing:**
1. Unit tests for feature extraction functions with known input/output pairs
2. Integration tests for data loading with sample CSV/JSON files
3. Mocking of embedder for fast feature extraction tests
4. Parametrized tests for threshold variations
5. Edge case tests: empty dataframes, single samples, NaN handling
6. Reproducibility tests: same random_state yields identical results

## Debugging Utilities

**Included Tools:**
- `test.py::inspect_pt()`: Diagnostic function to examine PyTorch tensor files
  - Detects tensor shape and format (edge_index vs edge_list)
  - Infers number of nodes and edges
  - Handles dict-like saved objects
  - Identifies edge_type vs edge_weight tensors heuristically

**Example Usage:**
```python
def inspect_pt(path, max_print=5):
    obj = torch.load(path, map_location="cpu")
    if torch.is_tensor(obj):
        print(f"Tensor dtype: {obj.dtype}, shape: {obj.shape}")
        # ... further inspection
```

---

*Testing analysis: 2026-03-18*
