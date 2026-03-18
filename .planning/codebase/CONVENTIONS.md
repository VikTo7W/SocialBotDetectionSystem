# Coding Conventions

**Analysis Date:** 2026-03-18

## Naming Patterns

**Files:**
- Lowercase with underscores: `botdetector_pipeline.py`, `botsim24_io.py`, `features_stage1.py`
- Descriptive module names indicating purpose and stage

**Functions:**
- Lowercase with underscores (snake_case): `sigmoid()`, `extract_stage1_matrix()`, `filter_edges_for_split()`
- Verb-prefixed for clarity: `extract_*`, `build_*`, `train_*`, `predict_*`, `gate_*`, `parse_*`, `load_*`
- Private helper methods use underscore prefix: `_to_unix_seconds()` in `botsim24_io.py`

**Variables:**
- Lowercase with underscores: `node_ids`, `edge_index`, `embedder`, `accounts_df`
- Single letters acceptable for mathematical operations: `X` (features), `y` (labels), `h` (embeddings), `z` (logits)
- Matrix dimensions prefixed clearly: `X1_tr` (stage 1 training features), `X2_S2` (stage 2 validation features)
- Descriptive abbreviations for common concepts: `out1` (stage 1 output), `p2a` (stage 2a probability), `z1` (stage 1 logit)

**Types/Classes:**
- PascalCase: `MahalanobisNovelty`, `TextEmbedder`, `Stage1MetadataModel`, `Stage2BaseContentModel`, `AMRDeltaRefiner`, `Stage3StructuralModel`, `StageThresholds`, `FeatureConfig`, `TrainedSystem`
- Dataclasses decorated: `@dataclass` used for configuration objects and result containers

**Constants:**
- Uppercase with underscores: `SEED = 42`, `DATETIME_FMT = "%Y-%m-%d %H:%M:%S"`
- Logical grouping in sections (e.g., stage thresholds grouped in `StageThresholds` dataclass)

## Code Style

**Formatting:**
- No explicit linter configuration detected in codebase
- Import organization follows PEP 8 convention: standard library → third-party → local
- 4-space indentation (Python standard)
- Line length appears to follow convention (no evidence of auto-wrapping tools)

**Type Hints:**
- Comprehensive type annotations throughout: `def fit(self, X: np.ndarray, y: np.ndarray) -> "Stage1MetadataModel"`
- Return type annotations use forward references for self-type: `-> "MahalanobisNovelty"`
- Complex types use `typing` module: `Optional[T]`, `Dict[str, Any]`, `List[str]`, `Tuple`
- NumPy/pandas types explicitly annotated: `np.ndarray`, `pd.DataFrame`

**Docstring Style:**
- Google-style docstrings with triple quotes
- Located immediately after function/class definition
- Include purpose description and parameter notes in prose
- Example from `botsim24_io.py`:
  ```python
  def parse_subreddits(x: Any) -> List[str]:
      """
      README says Users.csv has a 'subreddit' column describing communities participated in.
      Format isn't specified, so we handle:
        - JSON-like lists: "['news','politics']"
        - comma-separated: "news,politics"
        - single string: "news"
        - missing -> []
      """
  ```

## Import Organization

**Order:**
1. `from __future__ import annotations` (when used for forward references)
2. Standard library imports: `json`, `ast`, `datetime`, `dataclasses`
3. Scientific/data library imports: `numpy`, `pandas`
4. ML library imports: `sklearn`, `lightgbm`, `sentence_transformers`, `torch`
5. Local module imports: `from botsim24_io import ...`, `from features_stage1 import ...`

**Path Aliases:**
- No path aliases (no `@` or `jsconfig` style imports) - direct relative imports used
- All imports are explicit relative: `from botsim24_io import load_users_csv`

**Redundant Imports:**
- Allowed when different: multiple imports of same module at different points is acceptable (e.g., pandas imported twice in `main.py`)

## Error Handling

**Patterns:**
- Optional imports wrapped in try/except for graceful degradation:
  ```python
  try:
      import lightgbm as lgb
      HAS_LGB = True
  except Exception:
      HAS_LGB = False
      from sklearn.ensemble import HistGradientBoostingClassifier
  ```
- Explicit runtime checks before using unfitted models: `if self.cal is None: raise RuntimeError("Stage1 not fitted.")`
- Validation with assertions in main execution: `assert accounts["node_idx"].isna().sum() == 0, "..."`
- Silent handling (try/except with pass) for data parsing robustness:
  ```python
  try:
      v = ast.literal_eval(s)
      if isinstance(v, (list, tuple)):
          return [str(t).strip() for t in v if str(t).strip()]
  except Exception:
      pass
  ```

**Exception Types:**
- `RuntimeError` for state violations (model not fitted)
- Bare `Exception` catch for robustness in I/O and parsing (e.g., JSON literal parsing)
- Assertions for invariant checking in data preprocessing

## Logging

**Framework:** `print()` statements only - no logging module used

**Patterns:**
- Simple stdout printing for progress: `print(accounts["label"].value_counts())`
- Informational prints during training: `print("S1:", len(S1), "S2:", len(S2), "S3:", len(S3))`
- Diagnostic output without timestamps or levels
- No structured logging or log levels implemented

**When to Log:**
- Data shape summaries before processing
- Dataset split sizes
- Model training results
- Inference outputs for verification

## Comments

**When to Comment:**
- Inline comments for non-obvious logic: `# Treat as UTC (dataset uses created_utc strings)`
- Stage description comments: `# Stage 1 early exits`, `# Stage 2 AMR gate`
- TODO/notes inline: `# (Optional but recommended)`, `# if your updated train_system...`
- Section headers for major logical blocks: `# ---- Stage 1 training on S1`, `# ---- OOF stacking for meta12 on S2`

**JSDoc/TSDoc:**
- Not applicable (Python project, not TypeScript/JavaScript)
- Docstrings provide this documentation role

**Inline Comments:**
- Sparse but present for mathematical operations: `# Mahalanobis squared distance`, `# gradients for logistic loss`
- Data flow explanation: `# you likely have .pt edge files somewhere; but you said you're not sure if they're full graph`

## Function Design

**Size:**
- Small utility functions (< 10 lines): `sigmoid()`, `logit()`, `entropy_from_p()`
- Medium core functions (15-40 lines): feature extraction functions, novelty scoring
- Large orchestration functions (50+ lines): `train_system()`, `predict_system()`, `build_graph_features_nodeidx()`
- Training/prediction pipelines intentionally large to keep orchestration logic together

**Parameters:**
- Explicit parameter passing preferred over globals
- Configuration objects passed as arguments: `cfg: FeatureConfig`, `th: StageThresholds`
- NumPy/pandas objects passed by reference
- Default parameters for configurable behavior: `use_isotonic: bool = False`, `n_splits: int = 5`, `random_state: int = 42`

**Return Values:**
- Single return for simple operations: functions return `np.ndarray` or `pd.DataFrame`
- Dictionary returns for multi-output stages: `{"p1": p, "u1": u, "n1": n, "z1": logit(p)}`
- Dataclass/object returns for complex state: `return TrainedSystem(...)`
- NumPy/pandas for numerical operations; dictionaries for semantic grouping of related outputs

## Module Design

**Exports:**
- No `__all__` declarations - all top-level functions are implicitly public
- Modules are functional (functions and classes) rather than object-oriented

**Barrel Files:**
- Not used - each module imports explicitly what it needs
- Direct imports from specific modules: `from botsim24_io import load_users_csv, load_user_post_comment_json`

**Organization by Concern:**
- `botsim24_io.py`: Data loading and account table construction
- `features_stage1.py`: Metadata feature extraction
- `features_stage2.py`: Content/linguistic/temporal feature extraction
- `botdetector_pipeline.py`: Model classes, training, and inference logic
- `main.py`: Entry point orchestrating full pipeline

## Class Design Patterns

**Sklearn-compatible Classes:**
- Models follow sklearn API: `.fit()` → `.predict()` pattern
- Example: `Stage1MetadataModel.fit(X, y)` → `Stage1MetadataModel.predict(X)`
- Calibrated classifiers wrapped: `CalibratedClassifierCV` for probability outputs

**Dataclass Usage:**
- Configuration objects use `@dataclass`: `FeatureConfig`, `StageThresholds`, `TrainedSystem`
- Immutable configuration preferred over mutable state
- Type-safe configuration container instead of dicts

**Novelty Scoring:**
- Custom class for state management: `MahalanobisNovelty` with fitted state (`mu_`, `prec_`)
- `Optional[np.ndarray]` fields to track fitted state

## Conventions Summary

**Key Principles:**
- Type hints are mandatory for functions
- Descriptive names with semantic prefixes (stage, gate, extract, build, train, predict)
- Docstrings explain purpose and data flow; inline comments explain "why"
- Configuration via dataclass parameters rather than magic numbers
- Error handling via assertions and RuntimeError for state violations
- Print-based progress reporting (no structured logging)
- Sklearn-compatible ML class interfaces

---

*Convention analysis: 2026-03-18*
