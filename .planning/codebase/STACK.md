# Technology Stack

**Analysis Date:** 2026-03-18

## Languages

**Primary:**
- Python 3.x - Core implementation language used for all modules
- NumPy/Pandas operations - Used for numerical computing and data manipulation

## Runtime

**Environment:**
- Python 3 (version not explicitly specified in codebase)

**Package Manager:**
- pip (implied by dependency usage)
- Lockfile: Not detected

## Frameworks

**Core ML/ML Ops:**
- scikit-learn (sklearn) - Machine learning algorithms, model calibration, and evaluation
- LightGBM - Gradient boosting classifier (primary choice when available)
- sentence-transformers (SentenceTransformer) - Text embedding and representation learning

**Fallback:**
- HistGradientBoostingClassifier - Used when LightGBM not available

**Data Processing:**
- pandas - DataFrame operations and tabular data management
- NumPy - Numerical arrays and matrix operations
- PyTorch - Graph tensor storage (edge_index.pt, edge_type.pt, edge_weight.pt loaded via `torch.load()`)

## Key Dependencies

**Critical:**
- pandas [version unknown] - Data loading and manipulation for accounts, edges, splits
- numpy [version unknown] - Numerical computations, matrix operations, array handling
- scikit-learn [version unknown] - Logistic regression, calibration, stratified splitting, covariance estimation
- sentence-transformers [version unknown] - Text encoding via SentenceTransformer model (default: "all-MiniLM-L6-v2")
- lightgbm [version unknown] - Primary gradient boosting backend (fallback: sklearn's HistGradientBoostingClassifier)
- torch [version unknown] - Loading and manipulating PyTorch tensor files (.pt format)

**Feature Extraction:**
- LedoitWolf covariance estimator (from sklearn.covariance) - Shrinkage-based covariance for Mahalanobis distance calculation

## Configuration

**Environment:**
- No explicit .env file detected
- Hardcoded seed: `SEED = 42` in `main.py`
- Stage thresholds configured via `StageThresholds` dataclass in `botdetector_pipeline.py`

**Build:**
- No build configuration files detected
- No setup.py or pyproject.toml present

**Model Configuration:**
- `FeatureConfig` dataclass defines:
  - `stage1_numeric_cols`: List of stage 1 feature columns (must be configured)
  - `max_messages_per_account`: 50 (default)
  - `max_chars_per_message`: 500 (default)

**Stage-Specific Settings:**
- `StageThresholds` controls routing decisions:
  - S1 confidence thresholds: `s1_bot=0.98`, `s1_human=0.02`
  - S2 AMR gating thresholds: `s2a_bot=0.95`, `s2a_human=0.05`
  - Novelty triggers: `n1_max_for_exit=3.0`, `n2_trigger=3.0`
  - Stage 3 routing: `s12_bot=0.98`, `s12_human=0.02`, `novelty_force_stage3=3.5`

## Platform Requirements

**Development:**
- Windows 10 (observed platform)
- Python 3.x runtime
- RAM: High (graph neural network embeddings, matrix operations)
- No specific GPU requirement detected (CPU operations assumed)

**Production:**
- Python 3.x environment
- Access to model files: `edge_index.pt`, `edge_type.pt`, `edge_weight.pt`
- Data files: `Users.csv`, `user_post_comment.json`
- Approximately 80-373 MB for pre-computed tensor files

---

*Stack analysis: 2026-03-18*
