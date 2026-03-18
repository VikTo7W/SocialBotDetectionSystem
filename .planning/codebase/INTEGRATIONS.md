# External Integrations

**Analysis Date:** 2026-03-18

## APIs & External Services

**Text Embeddings:**
- Hugging Face sentence-transformers - Text embedding via pre-trained models
  - SDK/Client: `sentence_transformers.SentenceTransformer`
  - Default model: "all-MiniLM-L6-v2" (384-dimensional embeddings)
  - Auth: None required (uses public models)
  - Usage: `TextEmbedder` class in `botdetector_pipeline.py` wraps model loading and inference

**AMR Parsing (Placeholder):**
- Currently stubbed via `amr_linearize_stub()` in `botdetector_pipeline.py`
- Function returns original text (not implemented)
- Integration point: `extract_amr_embeddings_for_accounts()` expects real AMR parsing to replace stub

## Data Storage

**Databases:**
- None detected - System uses local file storage only

**File Storage:**
- Local filesystem only
- Input data files:
  - `Users.csv` - User metadata (CSV format, ~278 KB)
  - `user_post_comment.json` - Posts and comments (JSON format, ~80 MB)
- Pre-computed graph tensors (PyTorch .pt format):
  - `edge_index.pt` - Edge source/destination pairs (~373 KB)
  - `edge_type.pt` - Edge type classifications (~373 KB)
  - `edge_weight.pt` - Edge weights (~373 KB)

**Caching:**
- None detected - Models loaded into memory per session
- No persistent model storage beyond PyTorch tensor files

## Authentication & Identity

**Auth Provider:**
- None - System is self-contained
- No API keys or credentials required (sentence-transformers uses public models)

**User/Account Identification:**
- Reddit user IDs (from dataset)
- Parsed from `Users.csv` → `user_post_comment.json` mapping
- Local dataset contains binary labels: human (0) or bot (1)

## Monitoring & Observability

**Error Tracking:**
- None detected

**Logs:**
- Console output via `print()` statements
- Locations:
  - `main.py` line 38: Account label distribution
  - `main.py` lines 57: Split sizes (S1, S2, S3)
  - `main.py` line 104: Predictions on S3 test set
  - `main.py` line 111: Classification report metrics

**Metrics:**
- sklearn.metrics.classification_report for F1/precision/recall
- Custom metrics computed in model predict methods: entropy, novelty scores

## CI/CD & Deployment

**Hosting:**
- Not detected - Standalone Python application

**CI Pipeline:**
- Not detected - No automated testing/deployment infrastructure

**Execution Model:**
- Single-machine script execution
- Entry point: `main.py` orchestrates full pipeline
- Training and inference in-process (no distributed computing)

## Environment Configuration

**Required files (input):**
- `Users.csv` - User metadata (path: project root, referenced in `main.py` line 19)
- `user_post_comment.json` - Posts/comments data (path: project root, referenced in `main.py` line 22)
- `edge_index.pt` - Graph connectivity (path: project root, loaded line 63)
- `edge_type.pt` - Edge types (path: project root, loaded line 64)
- `edge_weight.pt` - Edge weights (path: project root, loaded line 65)

**Required Python packages:**
- pandas, numpy, torch, scikit-learn, lightgbm, sentence-transformers

**Secrets location:**
- None detected - No credentials or secrets management

**Python path configuration:**
- Modules imported locally (same directory):
  - `botsim24_io` - I/O utilities (`botsim24_io.py`)
  - `botdetector_pipeline` - Core pipeline (`botdetector_pipeline.py`)
  - `features_stage1` - Stage 1 feature extraction (`features_stage1.py`)
  - `features_stage2` - Stage 2 feature extraction (`features_stage2.py`)

## Webhooks & Callbacks

**Incoming:**
- None detected

**Outgoing:**
- None detected

## Data Flow & Integration Points

**Input Pipeline:**

1. `load_users_csv("Users.csv")` → User metadata, labels (human/bot classification)
2. `load_user_post_comment_json("user_post_comment.json")` → Posts, comments, temporal data
3. `build_account_table()` → Unified account DataFrame with messages, metadata
4. Load graph tensors via `torch.load()` → Edge connectivity and weights
5. `filter_edges_for_split()` → Filter graph for train/test splits

**Feature Extraction Pipeline:**

1. `extract_stage1_matrix()` - Metadata features (profile counts, ratios)
2. `extract_stage2_features()` - Text embeddings + linguistic features
3. `build_graph_features_nodeidx()` - Structural features (degree, weights)
4. `extract_amr_embeddings_for_accounts()` - AMR parsing and embeddings (currently stubbed)

**Model Output:**

`predict_system()` returns DataFrame with per-account predictions:
- `account_id`, `p1`, `n1` (stage 1)
- `p2`, `n2` (stage 2)
- `amr_used` (routing flag)
- `p12`, `stage3_used` (combined prediction)
- `p3`, `n3` (stage 3)
- `p_final` (final bot probability)

---

*Integration audit: 2026-03-18*
