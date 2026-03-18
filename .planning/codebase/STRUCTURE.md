# Codebase Structure

**Analysis Date:** 2026-03-18

## Directory Layout

```
C:\Users\dzeni\PycharmProjects\SocialBotDetectionSystem/
├── main.py                          # Entry point: orchestrates train/predict pipeline
├── botdetector_pipeline.py          # Core: stage models, meta-learners, routing logic
├── botsim24_io.py                   # Data loading: CSV/JSON parsing, account table construction
├── features_stage1.py               # Feature extraction: metadata features
├── features_stage2.py               # Feature extraction: content + temporal + linguistic
├── test.py                          # Utilities: inspection script for PyTorch tensor files
├── Users.csv                        # Data: Account metadata (1907 human, 1000 bot)
├── user_post_comment.json           # Data: Posts/comments for each user (80MB)
├── edge_index.pt                    # Data: Graph edges [E, 2] in PyTorch format
├── edge_type.pt                     # Data: Edge types [E] per edge
├── edge_weight.pt                   # Data: Edge weights [E, 1]
├── BotSim-24-Dataset/               # Documentation: dataset README
│   └── Readme.md
└── .planning/                       # Planning documents (generated)
    └── codebase/
        ├── ARCHITECTURE.md
        └── STRUCTURE.md
```

## Directory Purposes

**Project Root:**
- Purpose: Top-level Python project containing bot detection system
- Contains: Python modules, data files, trained models (via torch.load)
- Key files: `main.py`, `botdetector_pipeline.py`

**BotSim-24-Dataset:**
- Purpose: Dataset documentation and specification
- Contains: Single Readme.md describing data format and labels
- Generated: No (committed)
- Committed: Yes

**.planning/codebase/:**
- Purpose: Codebase analysis documents for GSD orchestrator
- Contains: ARCHITECTURE.md, STRUCTURE.md, (TESTING.md, CONVENTIONS.md on quality focus)
- Generated: Yes (by mapping command)
- Committed: Yes (as reference)

## Key File Locations

**Entry Points:**
- `main.py`: Orchestrates full training and evaluation pipeline; loads data, creates splits, calls train_system()/predict_system()

**Configuration:**
- `botdetector_pipeline.py`: StageThresholds dataclass (lines 155-171) defines all routing parameters
- `botdetector_pipeline.py`: FeatureConfig dataclass (lines 75-83) defines embedding and text limits

**Core Logic:**
- `botdetector_pipeline.py`: Stage models (Stage1MetadataModel, Stage2BaseContentModel, Stage3StructuralModel) with fit/predict
- `botdetector_pipeline.py`: Meta-learners (train_meta12, train_meta123) with OOF stacking
- `botdetector_pipeline.py`: Routing gates (gate_amr, gate_stage3) for conditional processing
- `botdetector_pipeline.py`: Orchestration functions (train_system, predict_system)

**Feature Extraction:**
- `features_stage1.py`: extract_stage1_matrix() - metadata ratios from account data
- `features_stage2.py`: extract_stage2_features() - embeddings, linguistic, temporal from messages
- `botdetector_pipeline.py`: build_graph_features_nodeidx() - structural features from edges

**Data I/O:**
- `botsim24_io.py`: load_users_csv() - parse Users.csv into DataFrame with labels
- `botsim24_io.py`: load_user_post_comment_json() - deserialize 80MB JSON
- `botsim24_io.py`: build_account_table() - merge users and posts/comments into unified format

**Testing & Utilities:**
- `test.py`: inspect_pt() - inspect PyTorch tensor files for shape, dtype, ranges

**Data Files:**
- `Users.csv`: 2907 accounts (1907 human=0, 1000 bot=1) with metadata
- `user_post_comment.json`: Posts and comments keyed by user_id
- `edge_index.pt`, `edge_type.pt`, `edge_weight.pt`: Graph topology (uncertainty about completeness)

## Naming Conventions

**Files:**
- Python modules: lowercase with underscores (`botdetector_pipeline.py`, `botsim24_io.py`, `features_stage1.py`)
- Data files: descriptive names matching source (Users.csv, user_post_comment.json)
- Artifact files: descriptive names with extension (edge_index.pt, edge_type.pt, edge_weight.pt)

**Directories:**
- Mixed case for external datasets (BotSim-24-Dataset)
- Lowercase for system directories (.planning, .git, __pycache__)

**Functions:**
- snake_case: `load_users_csv()`, `extract_stage1_matrix()`, `predict_system()`
- Descriptive action verbs: load, extract, train, predict, build, gate

**Classes:**
- PascalCase: `Stage1MetadataModel`, `Stage2BaseContentModel`, `MahalanobisNovelty`
- Pattern suffix convention: Model, Refiner (classes that train/predict)

**Variables:**
- snake_case: `edge_index`, `p1`, `z2a`, `amr_mask`, `stage3_used`
- Short abbreviations for model outputs: p (probability), u (uncertainty), n (novelty), z (logit)
- Suffixes indicating source stage: p1, z1 (Stage 1), p2a (Stage 2 base), p3 (Stage 3), p_final (combined)

**Types:**
- Numpy arrays: np.ndarray (feature matrices, scores)
- Pandas DataFrames: pd.DataFrame (tabular data: accounts, edges, meta tables)
- Tensors: torch.Tensor (loaded from .pt files)

## Where to Add New Code

**New Feature (e.g., additional metadata feature):**
- Primary code: Add to `features_stage1.py` (if metadata) or `features_stage2.py` (if content)
- Modify `extract_stage1_matrix()` or `extract_stage2_features()` to include new feature
- Tests: Add cases to test.py or create new test_features.py

**New Stage (e.g., Stage 4):**
- Implementation:
  - Create stage class in `botdetector_pipeline.py` following Stage3StructuralModel pattern
  - Add feature extraction function (e.g., `build_stage4_features()`)
  - Add gating function (e.g., `gate_stage4()`)
  - Update `train_system()` to train new stage on S1
  - Update `predict_system()` to apply new stage with routing
  - Update meta-learner training in `train_system()` (add stage 4 outputs to meta table)

**New Model Type:**
- Use existing class structure (Stage*Model, Meta-learner) as template
- Ensure fit() and predict() interface matches (accept numpy arrays, return dict or probabilities)
- Integrate novelty scoring (MahalanobisNovelty) if stage-specific detection is needed

**Data Loading Enhancement:**
- Location: `botsim24_io.py`
- Add parsing function similar to `load_users_csv()` or `load_user_post_comment_json()`
- Call from `main.py` in the data loading section (lines 15-23)

**Configuration Addition:**
- Add field to `StageThresholds` dataclass (botdetector_pipeline.py lines 155-171) for new threshold
- Or extend `FeatureConfig` (botdetector_pipeline.py lines 75-83) for embedding/text settings
- Override in `main.py` before calling `train_system()`

**Utilities & Helpers:**
- Shared math helpers: Add to `botdetector_pipeline.py` (e.g., sigmoid, logit, entropy_from_p)
- Feature helpers: Add to feature_stage*.py files
- I/O helpers: Add to `botsim24_io.py`
- Inspection/debugging: Add functions to `test.py`

## Special Directories

**.planning/codebase/:**
- Purpose: Holds architecture/structure/conventions documents for GSD orchestrator
- Generated: Yes (by `/gsd:map-codebase` command)
- Committed: Yes (these are reference documents)

**__pycache__/:**
- Purpose: Python bytecode cache (system-generated)
- Generated: Yes
- Committed: No (in .gitignore)

**.git/:**
- Purpose: Git repository metadata
- Generated: Yes (by git init)
- Committed: Yes (system)

**.idea/:**
- Purpose: PyCharm IDE settings and metadata
- Generated: Yes (by PyCharm)
- Committed: Usually not (in .gitignore)

**BotSim-24-Dataset/:**
- Purpose: External dataset documentation reference
- Generated: No
- Committed: Yes

## Import Patterns

**Standard library imports:**
```python
from __future__ import annotations  # Type hints forward-compatibility
from dataclasses import dataclass
from typing import Dict, Any, Optional, Tuple, List
import json, ast, datetime, timezone
```

**Third-party data/ML:**
```python
import numpy as np
import pandas as pd
import torch
from sklearn.base import BaseEstimator
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.covariance import LedoitWolf
from sklearn.model_selection import train_test_split, StratifiedKFold
try:
    import lightgbm as lgb
except ImportError:
    pass  # fallback to sklearn
from sentence_transformers import SentenceTransformer
```

**Local module imports:**
```python
from botsim24_io import load_users_csv, load_user_post_comment_json, build_account_table
from botdetector_pipeline import StageThresholds, train_system, predict_system
from features_stage1 import extract_stage1_matrix
from features_stage2 import extract_stage2_features
```

## File Dependencies Graph

```
main.py
  ├─> botsim24_io.py (load data)
  ├─> botdetector_pipeline.py
  │   ├─> features_stage1.py (extract_stage1_matrix)
  │   ├─> features_stage2.py (extract_stage2_features)
  │   ├─> sklearn (classifiers, calibration, novelty)
  │   ├─> lightgbm (optional base learner)
  │   └─> sentence_transformers (TextEmbedder)
  └─> sklearn.metrics (evaluation)

test.py
  └─> torch (tensor inspection)
```

## Configuration Sources

**In Code:**
- `StageThresholds` defaults hardcoded (botdetector_pipeline.py lines 156-171)
- `FeatureConfig` defaults hardcoded (botdetector_pipeline.py lines 81-82)
- Random seed: SEED=42 in main.py line 16

**Runtime Overrides:**
- Thresholds modified in main.py lines 86-88 (example: disabling Stage 3)
- FeatureConfig can be passed to train_system() (currently None in main.py line 96)

**Data Files:**
- Hardcoded paths in main.py: "Users.csv", "user_post_comment.json", "edge_index.pt", etc.
- No environment variables or config files used

---

*Structure analysis: 2026-03-18*
