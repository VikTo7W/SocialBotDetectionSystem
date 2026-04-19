from __future__ import annotations

import json
import os
import shutil
import tempfile
from types import SimpleNamespace

import numpy as np
import pandas as pd

from evaluate_twibot20_native import (
    DEFAULT_METRICS_FILENAME,
    DEFAULT_RESULTS_FILENAME,
    evaluate_twibot20_native,
    run_inference_native,
)
from train_twibot import DEFAULT_TWIBOT_MODEL_PATH


def _write_split(path, records):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f)


def _record(idx: int, label: int) -> dict:
    return {
        "ID": f"tw_{idx:03d}",
        "label": str(label),
        "profile": {
            "screen_name": f"user_{idx}",
            "statuses_count": "10",
            "followers_count": "5",
            "friends_count": "3",
            "created_at": "Mon Apr 23 09:47:10 +0000 2012",
        },
        "tweet": [f"tweet {idx}"],
        "domain": ["Politics"],
        "neighbor": {"following": [], "follower": []},
    }


def test_run_inference_native_defaults_to_native_model_path(monkeypatch):
    seen = {}
    accounts_df = pd.DataFrame(
        {
            "account_id": ["tw_000", "tw_001"],
            "node_idx": np.array([0, 1], dtype=np.int32),
            "label": [0, 1],
        }
    )

    class FakePipeline:
        def __init__(self, dataset, cfg=None, embedder=None):
            seen["pipeline"] = {"dataset": dataset, "cfg": cfg, "embedder": embedder}

        def predict(self, system, df, edges_df, nodes_total=None):
            return pd.DataFrame({
                "account_id": df["account_id"].tolist(),
                "p1": np.zeros(len(df)),
                "n1": np.zeros(len(df)),
                "p2": np.zeros(len(df)),
                "n2": np.zeros(len(df)),
                "amr_used": np.zeros(len(df), dtype=int),
                "p12": np.zeros(len(df)),
                "stage3_used": np.zeros(len(df), dtype=int),
                "p3": np.zeros(len(df)),
                "n3": np.zeros(len(df)),
                "p_final": np.zeros(len(df)),
            })

    monkeypatch.setattr("evaluate_twibot20_native.load_accounts_with_ids", lambda path: accounts_df.copy())
    monkeypatch.setattr(
        "evaluate_twibot20_native.build_edges",
        lambda df, path: pd.DataFrame(
            {
                "src": np.array([], dtype=np.int32),
                "dst": np.array([], dtype=np.int32),
                "etype": np.array([], dtype=np.int8),
                "weight": np.array([], dtype=np.float32),
            }
        ),
    )
    monkeypatch.setattr(
        "evaluate_twibot20_native.joblib.load",
        lambda path: (seen.__setitem__("model_path", path), SimpleNamespace(cfg=None, embedder=object()))[1],
    )
    monkeypatch.setattr("evaluate_twibot20_native.CascadePipeline", FakePipeline)

    run_inference_native("test.json")

    assert seen["model_path"] == DEFAULT_TWIBOT_MODEL_PATH
    assert seen["pipeline"]["dataset"] == "twibot"
    assert DEFAULT_TWIBOT_MODEL_PATH != "trained_system_v12.joblib"


def test_run_inference_native_uses_shared_pipeline_predict(monkeypatch):
    seen = {}
    accounts_df = pd.DataFrame(
        {
            "account_id": ["tw_000"],
            "node_idx": np.array([0], dtype=np.int32),
            "label": [0],
        }
    )

    class FakePipeline:
        def __init__(self, dataset, cfg=None, embedder=None):
            seen["init"] = {"dataset": dataset}

        def predict(self, system, df, edges_df, nodes_total=None):
            seen["predict"] = {"rows": len(df), "nodes_total": nodes_total}
            return pd.DataFrame({
                "account_id": df["account_id"].tolist(),
                "p1": [0.1],
                "n1": [0.0],
                "p2": [0.2],
                "n2": [0.0],
                "amr_used": [0],
                "p12": [0.2],
                "stage3_used": [0],
                "p3": [0.5],
                "n3": [0.0],
                "p_final": [0.2],
            })

    monkeypatch.setattr("evaluate_twibot20_native.load_accounts_with_ids", lambda path: accounts_df.copy())
    monkeypatch.setattr(
        "evaluate_twibot20_native.build_edges",
        lambda df, path: pd.DataFrame(
            {
                "src": np.array([], dtype=np.int32),
                "dst": np.array([], dtype=np.int32),
                "etype": np.array([], dtype=np.int8),
                "weight": np.array([], dtype=np.float32),
            }
        ),
    )
    monkeypatch.setattr(
        "evaluate_twibot20_native.joblib.load",
        lambda path: SimpleNamespace(cfg=None, embedder=object()),
    )
    monkeypatch.setattr("evaluate_twibot20_native.CascadePipeline", FakePipeline)

    result = run_inference_native("test.json")

    assert seen["init"]["dataset"] == "twibot"
    assert seen["predict"]["rows"] == 1
    assert result["account_id"].tolist() == ["tw_000"]


def test_evaluate_twibot20_native_writes_schema_stable_artifacts(monkeypatch):
    temp_dir = ".phase19_eval_test"
    try:
        os.makedirs(temp_dir, exist_ok=True)
        test_path = "test.json"
        out_dir = os.path.join(temp_dir, "artifacts")
        accounts_df = pd.DataFrame(
            {
                "account_id": ["tw_000", "tw_001"],
                "node_idx": np.array([0, 1], dtype=np.int32),
                "label": [0, 1],
            }
        )

        monkeypatch.setattr(
            "evaluate_twibot20_native.run_inference_native",
            lambda path, model_path=DEFAULT_TWIBOT_MODEL_PATH: pd.DataFrame({
                "account_id": ["tw_000", "tw_001"],
                "p1": [0.1, 0.9],
                "n1": [0.0, 0.0],
                "p2": [0.2, 0.8],
                "n2": [0.0, 0.0],
                "amr_used": [0, 1],
                "p12": [0.2, 0.8],
                "stage3_used": [0, 1],
                "p3": [0.5, 0.7],
                "n3": [0.0, 0.0],
                "p_final": [0.2, 0.8],
            }),
        )
        monkeypatch.setattr(
            "evaluate_twibot20_native.evaluate_s3",
            lambda results, y_true, threshold=0.5, verbose=False: {
                "overall": {"f1": 0.5, "auc": 0.6, "precision": 0.7, "recall": 0.8},
                "per_stage": {"p1": {}, "p2": {}, "p12": {}, "p_final": {}},
                "routing": {"pct_stage1_exit": 50.0, "pct_stage2_exit": 0.0, "pct_stage3_exit": 50.0, "pct_amr_triggered": 50.0},
            },
        )
        monkeypatch.setattr("evaluate_twibot20_native.load_accounts_with_ids", lambda path: accounts_df.copy())

        summary = evaluate_twibot20_native(
            path=test_path,
            model_path="trained_system_twibot.joblib",
            output_dir=out_dir,
        )

        assert set(summary["metrics"].keys()) == {"overall", "per_stage", "routing"}
        assert os.path.exists(os.path.join(out_dir, DEFAULT_RESULTS_FILENAME))
        assert os.path.exists(os.path.join(out_dir, DEFAULT_METRICS_FILENAME))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_native_evaluation_is_separate_from_legacy_zero_shot_path():
    assert DEFAULT_TWIBOT_MODEL_PATH != "trained_system_v12.joblib"
