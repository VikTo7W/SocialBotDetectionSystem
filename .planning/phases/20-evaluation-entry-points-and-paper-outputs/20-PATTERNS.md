# Phase 20: Evaluation Entry Points and Paper Outputs - Pattern Map

**Mapped:** 2026-04-19
**Files analyzed:** 8 new/modified files
**Analogs found:** 8 / 8

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|-------------------|------|-----------|----------------|---------------|
| `eval_botsim_native.py` | service (eval entry point) | batch, file-I/O | `evaluate_twibot20_native.py` | exact |
| `eval_reddit_twibot_transfer.py` | service (eval entry point) | batch, transform | `evaluate_twibot20.py` | exact |
| `eval_twibot_native.py` | service (eval entry point) | batch, file-I/O | `evaluate_twibot20_native.py` | exact |
| `generate_table5.py` | utility (paper driver) | batch, file-I/O | `ablation_tables.py` main() block | role-match |
| `ablation_tables.py` (modify: fix import) | utility | batch | `ablation_tables.py` itself | self |
| `tests/test_eval_botsim_native.py` | test | request-response | `tests/test_evaluate_twibot20_native.py` | exact |
| `tests/test_eval_reddit_twibot_transfer.py` | test | request-response | `tests/test_evaluate_twibot20_native.py` | role-match |
| `tests/test_eval_twibot_native.py` | test | request-response | `tests/test_evaluate_twibot20_native.py` | exact |
| `tests/test_paper_outputs.py` | test | request-response | `tests/test_evaluate.py` | role-match |

---

## Pattern Assignments

### `eval_botsim_native.py` (eval entry point, batch/file-I/O)

**Analog:** `evaluate_twibot20_native.py`

**Imports pattern** (`evaluate_twibot20_native.py` lines 1-18):
```python
from __future__ import annotations

import json
import os
import sys

import joblib
import pandas as pd

from cascade_pipeline import CascadePipeline
from evaluate import evaluate_s3
from train_botsim import (
    DEFAULT_BOTSIM_MODEL_PATH,
    SEED,
    filter_edges_for_split,
    load_botsim_accounts,
    load_botsim_edges,
    split_train_accounts,
)
```

**Additional imports for confusion matrix** (PAPER-01, from RESEARCH.md Pattern 3):
```python
import matplotlib
matplotlib.use("Agg")  # must precede pyplot import; headless-safe on Windows
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay
```

**BotSim split reconstruction pattern** (`train_botsim.py` lines 103-122 + lines 138-144):
```python
SEED = 42
DEFAULT_OUTPUT_DIR = "paper_outputs"

users, accounts = load_botsim_accounts()   # returns (users_df, accounts_df)
edges_df = load_botsim_edges()
_S1, _S2, S3 = split_train_accounts(accounts, seed=SEED)
edges_S3 = filter_edges_for_split(edges_df, S3["node_idx"].to_numpy())
nodes_total = len(users)
```

**Inference pattern** (`evaluate_twibot20_native.py` lines 29-42):
```python
def run_inference_botsim_native(
    model_path: str = DEFAULT_BOTSIM_MODEL_PATH,
) -> pd.DataFrame:
    users, accounts = load_botsim_accounts()
    edges_df = load_botsim_edges()
    _S1, _S2, S3 = split_train_accounts(accounts, seed=SEED)
    edges_S3 = filter_edges_for_split(edges_df, S3["node_idx"].to_numpy())
    system = joblib.load(model_path)
    pipeline = CascadePipeline("botsim", cfg=system.cfg, embedder=system.embedder)
    return pipeline.predict(
        system,
        df=S3,
        edges_df=edges_S3,
        nodes_total=len(users),
    ), S3
```

**Core evaluation + output pattern** (`evaluate_twibot20_native.py` lines 45-69):
```python
def evaluate_botsim_native(
    model_path: str = DEFAULT_BOTSIM_MODEL_PATH,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    threshold: float = 0.5,
) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    results, S3 = run_inference_botsim_native(model_path=model_path)
    y_true = S3["label"].to_numpy()
    metrics = evaluate_s3(results, y_true, threshold=threshold, verbose=True)

    metrics_path = os.path.join(output_dir, "metrics_botsim.json")
    _save_json(metrics, metrics_path)

    # PAPER-01: confusion matrix image
    _write_confusion_matrix(results, y_true, threshold,
                            os.path.join(output_dir, "confusion_matrix_botsim.png"),
                            title="BotSim-24 (native) confusion matrix")

    return {
        "metrics": metrics,
        "paths": {
            "metrics": metrics_path,
            "confusion_matrix": os.path.join(output_dir, "confusion_matrix_botsim.png"),
            "model": model_path,
        },
    }
```

**Confusion matrix writer** (shared helper, defined once, copied to all three entry points; from RESEARCH.md Pattern 3):
```python
def _write_confusion_matrix(results, y_true, threshold, output_path, title):
    y_pred = (results["p_final"].to_numpy() >= threshold).astype(int)
    disp = ConfusionMatrixDisplay.from_predictions(
        y_true, y_pred,
        display_labels=["human", "bot"],
        colorbar=False,
        cmap="Blues",
    )
    disp.ax_.set_title(title)
    disp.figure_.tight_layout()
    disp.figure_.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(disp.figure_)
```

**JSON persistence helper** (`evaluate_twibot20_native.py` lines 24-26):
```python
def _save_json(payload: dict | list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
```

**CLI entry point pattern** (`evaluate_twibot20_native.py` lines 72-84):
```python
if __name__ == "__main__":
    model_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BOTSIM_MODEL_PATH
    output_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT_DIR

    summary = evaluate_botsim_native(model_path=model_path, output_dir=output_dir)
    print(f"[botsim-native] model:          {summary['paths']['model']}")
    print(f"[botsim-native] metrics:        {summary['paths']['metrics']}")
    print(f"[botsim-native] confusion_matrix: {summary['paths']['confusion_matrix']}")
```

---

### `eval_reddit_twibot_transfer.py` (eval entry point, batch/transform)

**Analog:** `evaluate_twibot20.py`

**Imports pattern** (`evaluate_twibot20.py` lines 38-53):
```python
from __future__ import annotations

import json
import os
import sys

import joblib
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay

from cascade_pipeline import CascadePipeline
from evaluate import evaluate_s3
from train_botsim import DEFAULT_BOTSIM_MODEL_PATH
from twibot20_io import build_edges, load_accounts, parse_tweet_types
```

**Transfer adapter pattern** — DataFrame column rewrite (replaces monkey-patch; from `evaluate_twibot20.py` lines 160-175):
```python
_RATIO_CAP = 1000.0   # retain value from legacy; see FEAT-03 review in evaluate_twibot20.py

def _apply_transfer_adapter(accounts_df: pd.DataFrame) -> pd.DataFrame:
    """Rewrite TwiBot-20 columns to match BotSim-24 Stage 1 schema."""
    df = accounts_df.copy()
    tweet_stats = [parse_tweet_types(msgs) for msgs in df["messages"]]
    df["submission_num"] = [
        float(s["original_count"] + s["mt_count"] + s["rt_count"])
        for s in tweet_stats
    ]
    df["comment_num_1"] = [float(s["original_count"]) for s in tweet_stats]
    df["comment_num_2"] = [float(s["mt_count"]) for s in tweet_stats]
    df["subreddit_list"] = df["domain_list"].tolist()
    # NOTE: ratio clamping (_RATIO_CAP) is applied inside Stage 1 extraction;
    # if Stage1Extractor("botsim") reads named columns, this rewrite is sufficient.
    # Verify against features/stage1.py if Stage 1 F1 is suspiciously 0.0.
    return df
```

**Inference pattern** (adapted from `evaluate_twibot20_native.py` lines 29-42, using "botsim" dataset):
```python
def run_inference_transfer(
    path: str,
    model_path: str = DEFAULT_BOTSIM_MODEL_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    accounts_df = load_accounts(path)
    accounts_df = _apply_transfer_adapter(accounts_df)
    edges_df = build_edges(accounts_df, path)
    system = joblib.load(model_path)
    pipeline = CascadePipeline("botsim", cfg=system.cfg, embedder=system.embedder)
    results = pipeline.predict(
        system,
        df=accounts_df,
        edges_df=edges_df,
        nodes_total=len(accounts_df),
    )
    return results, accounts_df
```

**Evaluate + persist pattern** (same structure as `evaluate_twibot20_native.py` lines 45-69, with different filenames):
```python
DEFAULT_OUTPUT_DIR = "paper_outputs"

def evaluate_reddit_twibot_transfer(
    path: str = "test.json",
    model_path: str = DEFAULT_BOTSIM_MODEL_PATH,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    threshold: float = 0.5,
) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    results, accounts_df = run_inference_transfer(path, model_path=model_path)
    y_true = accounts_df["label"].to_numpy()
    metrics = evaluate_s3(results, y_true, threshold=threshold, verbose=True)

    metrics_path = os.path.join(output_dir, "metrics_reddit_transfer.json")
    _save_json(metrics, metrics_path)
    _write_confusion_matrix(
        results, y_true, threshold,
        os.path.join(output_dir, "confusion_matrix_reddit_transfer.png"),
        title="Reddit-transfer (TwiBot-20) confusion matrix",
    )
    return {
        "metrics": metrics,
        "paths": {
            "metrics": metrics_path,
            "confusion_matrix": os.path.join(output_dir, "confusion_matrix_reddit_transfer.png"),
            "model": model_path,
        },
    }
```

**Key anti-pattern to avoid** (`evaluate_twibot20.py` lines 230-235 and 274-275):
```python
# DO NOT do this — global state mutation:
bp.extract_stage1_matrix = _clamped_s1   # monkey-patch
try:
    results = predict_system(...)
finally:
    bp.extract_stage1_matrix = _orig_extract_stage1_matrix

# DO THIS instead: rewrite DataFrame columns before calling pipeline.predict()
df = _apply_transfer_adapter(accounts_df)
results = pipeline.predict(system, df=df, ...)
```

---

### `eval_twibot_native.py` (eval entry point, batch/file-I/O)

**Analog:** `evaluate_twibot20_native.py` (near-verbatim; only constants and output filenames change)

**Imports pattern** (`evaluate_twibot20_native.py` lines 1-18, updated constants):
```python
from __future__ import annotations

import json
import os
import sys

import joblib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay

from cascade_pipeline import CascadePipeline
from evaluate import evaluate_s3
from train_twibot import DEFAULT_TWIBOT_MODEL_PATH
from twibot20_io import build_edges
from train_twibot import load_accounts_with_ids

DEFAULT_OUTPUT_DIR = "paper_outputs"
```

**Inference pattern** (`evaluate_twibot20_native.py` lines 29-42, unchanged logic):
```python
def run_inference_twibot_native(
    path: str,
    model_path: str = DEFAULT_TWIBOT_MODEL_PATH,
) -> pd.DataFrame:
    accounts_df = load_accounts_with_ids(path)
    edges_df = build_edges(accounts_df, path)
    system = joblib.load(model_path)
    pipeline = CascadePipeline("twibot", cfg=system.cfg, embedder=system.embedder)
    return pipeline.predict(
        system,
        df=accounts_df,
        edges_df=edges_df,
        nodes_total=len(accounts_df),
    )
```

**Evaluate + persist pattern** (`evaluate_twibot20_native.py` lines 45-69, new filenames + confusion matrix):
```python
def evaluate_twibot_native(
    path: str = "test.json",
    model_path: str = DEFAULT_TWIBOT_MODEL_PATH,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    threshold: float = 0.5,
) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    results = run_inference_twibot_native(path, model_path=model_path)
    accounts_df = load_accounts_with_ids(path)
    y_true = accounts_df["label"].to_numpy()
    metrics = evaluate_s3(results, y_true, threshold=threshold, verbose=True)

    metrics_path = os.path.join(output_dir, "metrics_twibot_native.json")
    _save_json(metrics, metrics_path)
    _write_confusion_matrix(
        results, y_true, threshold,
        os.path.join(output_dir, "confusion_matrix_twibot_native.png"),
        title="TwiBot-20 native confusion matrix",
    )
    return {
        "metrics": metrics,
        "paths": {
            "metrics": metrics_path,
            "confusion_matrix": os.path.join(output_dir, "confusion_matrix_twibot_native.png"),
            "model": model_path,
        },
    }
```

**Compatibility shim note:** `evaluate_twibot20_native.py` should be reduced to a one-line re-export (same pattern used by `train_twibot20.py` lines 1-20):
```python
# evaluate_twibot20_native.py (demoted shim — same pattern as train_twibot20.py)
from eval_twibot_native import evaluate_twibot_native as evaluate_twibot20_native, run_inference_twibot_native as run_inference_native
```

---

### `generate_table5.py` (paper driver, batch/file-I/O)

**Analog:** `ablation_tables.py` `main()` block (lines 535-576) + `generate_cross_dataset_table()` (lines 192-229)

**Imports pattern** (from RESEARCH.md Pattern 5):
```python
from __future__ import annotations

import json
import os
import sys

from ablation_tables import generate_cross_dataset_table, save_latex

DEFAULT_BOTSIM_METRICS_PATH = os.path.join("paper_outputs", "metrics_botsim.json")
DEFAULT_REDDIT_TRANSFER_METRICS_PATH = os.path.join("paper_outputs", "metrics_reddit_transfer.json")
DEFAULT_TWIBOT_NATIVE_METRICS_PATH = os.path.join("paper_outputs", "metrics_twibot_native.json")
DEFAULT_TABLE5_OUTPUT_PATH = os.path.join("tables", "table5_cross_dataset.tex")
```

**Metrics loader pattern** (`ablation_tables.py` lines 310-312):
```python
def _load(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)
```

**Core Table 5 generation pattern** (`ablation_tables.py` lines 560-574):
```python
def generate_table5(
    botsim_metrics_path: str = DEFAULT_BOTSIM_METRICS_PATH,
    reddit_transfer_metrics_path: str = DEFAULT_REDDIT_TRANSFER_METRICS_PATH,
    twibot_native_metrics_path: str = DEFAULT_TWIBOT_NATIVE_METRICS_PATH,
    output_path: str = DEFAULT_TABLE5_OUTPUT_PATH,
) -> str:
    botsim_metrics = _load(botsim_metrics_path)
    reddit_transfer_metrics = _load(reddit_transfer_metrics_path)
    twibot_native_metrics = _load(twibot_native_metrics_path)

    df_t5 = generate_cross_dataset_table(
        botsim_metrics, reddit_transfer_metrics, twibot_native_metrics
    )
    save_latex(df_t5, output_path)
    print(f"[table5] Saved LaTeX to {output_path}")
    return output_path
```

**CLI entry point pattern** (`ablation_tables.py` lines 598):
```python
if __name__ == "__main__":
    botsim_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BOTSIM_METRICS_PATH
    reddit_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_REDDIT_TRANSFER_METRICS_PATH
    twibot_path = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_TWIBOT_NATIVE_METRICS_PATH
    out_path = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_TABLE5_OUTPUT_PATH
    generate_table5(botsim_path, reddit_path, twibot_path, out_path)
```

---

### `ablation_tables.py` (modify: fix broken import)

**Change:** Line 38 — fix `from main import filter_edges_for_split` to `from train_botsim import filter_edges_for_split`.

**Current broken line** (`ablation_tables.py` line 38):
```python
from main import filter_edges_for_split  # broken — main.py no longer exports this
```

**Fixed line:**
```python
from train_botsim import filter_edges_for_split
```

This is the only required change to `ablation_tables.py` for Phase 20 (the `main()` block's Table 5 section also references stale Phase 15/16 artifact paths, but those are bypassed by `generate_table5.py`; the import fix is the pre-requisite that unblocks `pytest tests/test_ablation_tables.py`).

---

### `tests/test_eval_botsim_native.py` (test, request-response)

**Analog:** `tests/test_evaluate_twibot20_native.py` (exact structure)

**Imports pattern** (`tests/test_evaluate_twibot20_native.py` lines 1-18):
```python
from __future__ import annotations

import json
import os
import shutil
from types import SimpleNamespace

import numpy as np
import pandas as pd

from eval_botsim_native import (
    DEFAULT_OUTPUT_DIR,
    evaluate_botsim_native,
    run_inference_botsim_native,
)
from train_botsim import DEFAULT_BOTSIM_MODEL_PATH, SEED
```

**Fake pipeline pattern** (`tests/test_evaluate_twibot20_native.py` lines 52-70):
```python
class FakePipeline:
    def __init__(self, dataset, cfg=None, embedder=None):
        seen["pipeline"] = {"dataset": dataset}

    def predict(self, system, df, edges_df, nodes_total=None):
        n = len(df)
        return pd.DataFrame({
            "account_id": df["account_id"].tolist() if "account_id" in df.columns else [f"acc_{i}" for i in range(n)],
            "p1": np.zeros(n), "n1": np.zeros(n),
            "p2": np.zeros(n), "n2": np.zeros(n),
            "amr_used": np.zeros(n, dtype=int),
            "p12": np.zeros(n),
            "stage3_used": np.zeros(n, dtype=int),
            "p3": np.zeros(n), "n3": np.zeros(n),
            "p_final": np.zeros(n),
        })
```

**Monkeypatch pattern for data loading** (`tests/test_evaluate_twibot20_native.py` lines 72-88):
```python
# Patch data loaders and CascadePipeline so no real data files are needed
monkeypatch.setattr("eval_botsim_native.load_botsim_accounts", lambda *a, **kw: (users_df, accounts_df))
monkeypatch.setattr("eval_botsim_native.load_botsim_edges", lambda *a, **kw: empty_edges_df)
monkeypatch.setattr("eval_botsim_native.split_train_accounts",
                    lambda df, seed=SEED: (df.iloc[:0], df.iloc[:0], df))
monkeypatch.setattr("eval_botsim_native.filter_edges_for_split", lambda e, ids: e)
monkeypatch.setattr("eval_botsim_native.joblib.load",
                    lambda path: (seen.__setitem__("model_path", path),
                                  SimpleNamespace(cfg=None, embedder=object()))[1])
monkeypatch.setattr("eval_botsim_native.CascadePipeline", FakePipeline)
```

**Contract assertions** (`tests/test_evaluate_twibot20_native.py` lines 196-202):
```python
# Assert model path default
assert seen["model_path"] == DEFAULT_BOTSIM_MODEL_PATH

# Assert split isolation: pipeline dataset is "botsim"
assert seen["pipeline"]["dataset"] == "botsim"

# Assert metrics JSON schema
assert set(summary["metrics"].keys()) == {"overall", "per_stage", "routing"}
assert os.path.exists(os.path.join(out_dir, "metrics_botsim.json"))
assert os.path.exists(os.path.join(out_dir, "confusion_matrix_botsim.png"))
```

---

### `tests/test_eval_reddit_twibot_transfer.py` (test, request-response)

**Analog:** `tests/test_evaluate_twibot20_native.py` with transfer-specific assertions

**Key difference from twibot-native test:** Must assert model path is `trained_system_botsim.joblib` (not `trained_system_twibot.joblib`) and pipeline dataset is `"botsim"`.

**Transfer adapter column-mapping test** (new; no direct analog in existing tests):
```python
def test_transfer_adapter_populates_botsim_columns(monkeypatch):
    """Verify _apply_transfer_adapter adds submission_num, comment_num_1/2, subreddit_list."""
    accounts_df = _make_twibot_accounts_df()  # has "messages" and "domain_list"
    result = _apply_transfer_adapter(accounts_df)
    assert "submission_num" in result.columns
    assert "comment_num_1" in result.columns
    assert "comment_num_2" in result.columns
    assert "subreddit_list" in result.columns
```

---

### `tests/test_eval_twibot_native.py` (test, request-response)

**Analog:** `tests/test_evaluate_twibot20_native.py` (near-verbatim; update module name and model path constant)

**Imports (replace module under test):**
```python
from eval_twibot_native import (
    DEFAULT_OUTPUT_DIR,
    evaluate_twibot_native,
    run_inference_twibot_native,
)
from train_twibot import DEFAULT_TWIBOT_MODEL_PATH
```

**Key assertion difference from botsim test** (`tests/test_evaluate_twibot20_native.py` line 92-94):
```python
assert seen["model_path"] == DEFAULT_TWIBOT_MODEL_PATH
assert seen["pipeline"]["dataset"] == "twibot"
assert DEFAULT_TWIBOT_MODEL_PATH != "trained_system_v12.joblib"   # guard against legacy regression
```

---

### `tests/test_paper_outputs.py` (test, request-response)

**Analog:** `tests/test_evaluate.py` structure; `ablation_tables.py` `generate_cross_dataset_table()` (lines 192-229) for expected output shape

**Imports pattern:**
```python
from __future__ import annotations

import json
import os
import shutil
import tempfile

import pandas as pd
import pytest

from ablation_tables import generate_cross_dataset_table, save_latex
from generate_table5 import generate_table5, DEFAULT_TABLE5_OUTPUT_PATH
```

**Fixture: minimal metrics dict** (matches schema from `evaluate.py` lines 131-136):
```python
def _minimal_metrics():
    return {
        "overall": {"f1": 0.8, "auc": 0.85, "precision": 0.75, "recall": 0.85},
        "per_stage": {
            "p1": {"f1": 0.7, "auc": 0.75, "precision": 0.65, "recall": 0.75},
            "p2": {"f1": 0.7, "auc": 0.75, "precision": 0.65, "recall": 0.75},
            "p12": {"f1": 0.75, "auc": 0.80, "precision": 0.70, "recall": 0.80},
            "p_final": {"f1": 0.8, "auc": 0.85, "precision": 0.75, "recall": 0.85},
        },
        "routing": {
            "pct_stage1_exit": 60.0,
            "pct_stage2_exit": 20.0,
            "pct_stage3_exit": 20.0,
            "pct_amr_triggered": 25.0,
        },
    }
```

**Table 5 column header assertion** (from `ablation_tables.py` lines 214-229):
```python
def test_generate_cross_dataset_table_column_headers():
    df = generate_cross_dataset_table(
        _minimal_metrics(), _minimal_metrics(), _minimal_metrics()
    )
    assert list(df.columns) == [
        "Metric",
        "BotSim-24 (Reddit, in-dist.)",
        "TwiBot-20 (Reddit transfer)",
        "TwiBot-20 (TwiBot-native)",
    ]
    assert len(df) == 4
```

**File write assertion for generate_table5:**
```python
def test_generate_table5_writes_tex_file(tmp_path, monkeypatch):
    # Write three minimal metrics JSON files
    botsim_path = str(tmp_path / "metrics_botsim.json")
    reddit_path = str(tmp_path / "metrics_reddit_transfer.json")
    twibot_path = str(tmp_path / "metrics_twibot_native.json")
    out_path = str(tmp_path / "table5_cross_dataset.tex")
    for p in (botsim_path, reddit_path, twibot_path):
        with open(p, "w") as f:
            json.dump(_minimal_metrics(), f)

    result_path = generate_table5(botsim_path, reddit_path, twibot_path, out_path)
    assert result_path == out_path
    assert os.path.exists(out_path)
    content = open(out_path).read()
    assert "BotSim-24" in content
```

---

## Shared Patterns

### Matplotlib Non-Interactive Backend
**Source:** RESEARCH.md Pattern 3, Pitfall 3
**Apply to:** `eval_botsim_native.py`, `eval_reddit_twibot_transfer.py`, `eval_twibot_native.py`
```python
import matplotlib
matplotlib.use("Agg")   # must appear before any pyplot import; headless-safe on Windows
import matplotlib.pyplot as plt
```

### Confusion Matrix Writer
**Source:** RESEARCH.md Pattern 3
**Apply to:** All three eval entry points (copy verbatim as `_write_confusion_matrix()` helper)
```python
from sklearn.metrics import ConfusionMatrixDisplay

def _write_confusion_matrix(results, y_true, threshold, output_path, title):
    y_pred = (results["p_final"].to_numpy() >= threshold).astype(int)
    disp = ConfusionMatrixDisplay.from_predictions(
        y_true, y_pred,
        display_labels=["human", "bot"],
        colorbar=False,
        cmap="Blues",
    )
    disp.ax_.set_title(title)
    disp.figure_.tight_layout()
    disp.figure_.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(disp.figure_)
```

### JSON Persistence Helper
**Source:** `evaluate_twibot20_native.py` lines 24-26 (also duplicated in `evaluate_twibot20.py` lines 377-379)
**Apply to:** All three eval entry points
```python
def _save_json(payload: dict | list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
```

### Metrics Schema
**Source:** `evaluate.py` lines 131-136 (return dict structure), confirmed by `evaluate_twibot20_native.py` test lines 183-190
**Apply to:** All test fixtures and assertions
```json
{
  "overall":   {"f1": ..., "auc": ..., "precision": ..., "recall": ...},
  "per_stage": {"p1": {...}, "p2": {...}, "p12": {...}, "p_final": {...}},
  "routing":   {"pct_stage1_exit": ..., "pct_stage2_exit": ...,
                "pct_stage3_exit": ..., "pct_amr_triggered": ...}
}
```

### CascadePipeline Instantiation
**Source:** `evaluate_twibot20_native.py` lines 35-42
**Apply to:** All three eval entry points
```python
system = joblib.load(model_path)
pipeline = CascadePipeline("<dataset>", cfg=system.cfg, embedder=system.embedder)
results = pipeline.predict(
    system,
    df=<accounts_df>,
    edges_df=<edges_df>,
    nodes_total=<node_count>,
)
```

### Output Directory Contract
**Source:** `evaluate_twibot20_native.py` line 51
**Apply to:** All three eval entry points
```python
os.makedirs(output_dir, exist_ok=True)
```

### LaTeX Export
**Source:** `ablation_tables.py` lines 375-388
**Apply to:** `generate_table5.py`
```python
def save_latex(df: pd.DataFrame, path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    latex = df.to_latex(index=False, escape=False, float_format="%.4f")
    with open(path, "w") as f:
        f.write(latex)
```

---

## No Analog Found

All files have analogs in the codebase. No files require fallback to pure RESEARCH.md patterns.

---

## Metadata

**Analog search scope:**
- `C:\Users\dzeni\PycharmProjects\SocialBotDetectionSystem\evaluate_twibot20_native.py`
- `C:\Users\dzeni\PycharmProjects\SocialBotDetectionSystem\evaluate_twibot20.py`
- `C:\Users\dzeni\PycharmProjects\SocialBotDetectionSystem\evaluate.py`
- `C:\Users\dzeni\PycharmProjects\SocialBotDetectionSystem\ablation_tables.py`
- `C:\Users\dzeni\PycharmProjects\SocialBotDetectionSystem\train_botsim.py`
- `C:\Users\dzeni\PycharmProjects\SocialBotDetectionSystem\tests\test_evaluate_twibot20_native.py`
- `C:\Users\dzeni\PycharmProjects\SocialBotDetectionSystem\tests\test_evaluate.py`

**Files scanned:** 7 primary + 2 supporting (`train_twibot20.py`, `train_botsim.py`)
**Pattern extraction date:** 2026-04-19
