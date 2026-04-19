from __future__ import annotations

import json
import os
from types import SimpleNamespace

import numpy as np
import pandas as pd

from eval_twibot_native import (
    DEFAULT_OUTPUT_DIR,
    evaluate_twibot_native,
    run_inference_twibot_native,
)
from train_twibot import DEFAULT_TWIBOT_MODEL_PATH


def _make_accounts_df() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "account_id": ["tw_000", "tw_001"],
            "node_idx": np.array([0, 1], dtype=np.int32),
            "label": [0, 1],
            "screen_name": ["u0", "u1"],
            "statuses_count": [10, 11],
            "followers_count": [5, 6],
            "friends_count": [3, 4],
            "created_at": [
                "Mon Apr 23 09:47:10 +0000 2012",
                "Mon Apr 23 09:47:10 +0000 2012",
            ],
            "messages": [[{"text": "hi", "ts": None}], [{"text": "hello", "ts": None}]],
            "domain_list": [["Politics"], ["Sports"]],
        }
    )


class FakePipeline:
    def __init__(self, dataset, cfg=None, embedder=None):
        self.seen = {"dataset": dataset, "cfg": cfg, "embedder": embedder}

    def predict(self, system, df, edges_df, nodes_total=None):
        return pd.DataFrame(
            {
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
            }
        )


def test_run_inference_twibot_native_defaults_to_twibot_model_path(monkeypatch):
    seen = {}
    accounts_df = _make_accounts_df()
    empty_edges_df = pd.DataFrame(
        {
            "src": np.array([], dtype=np.int32),
            "dst": np.array([], dtype=np.int32),
            "etype": np.array([], dtype=np.int8),
            "weight": np.array([], dtype=np.float32),
        }
    )

    class SeenPipeline(FakePipeline):
        def __init__(self, dataset, cfg=None, embedder=None):
            super().__init__(dataset, cfg=cfg, embedder=embedder)
            seen["pipeline"] = self.seen

    monkeypatch.setattr("eval_twibot_native.load_accounts_with_ids", lambda path: accounts_df.copy())
    monkeypatch.setattr("eval_twibot_native.build_edges", lambda df, path: empty_edges_df)
    monkeypatch.setattr(
        "eval_twibot_native.joblib.load",
        lambda path: (seen.__setitem__("model_path", path), SimpleNamespace(cfg=None, embedder=object()))[1],
    )
    monkeypatch.setattr("eval_twibot_native.CascadePipeline", SeenPipeline)

    run_inference_twibot_native("test.json")

    assert seen["model_path"] == DEFAULT_TWIBOT_MODEL_PATH
    assert seen["pipeline"]["dataset"] == "twibot"
    assert DEFAULT_TWIBOT_MODEL_PATH != "trained_system_v12.joblib"


def test_run_inference_twibot_native_uses_shared_pipeline_predict(monkeypatch):
    seen = {}
    accounts_df = _make_accounts_df()
    empty_edges_df = pd.DataFrame(
        {
            "src": np.array([], dtype=np.int32),
            "dst": np.array([], dtype=np.int32),
            "etype": np.array([], dtype=np.int8),
            "weight": np.array([], dtype=np.float32),
        }
    )

    class SeenPipeline(FakePipeline):
        def __init__(self, dataset, cfg=None, embedder=None):
            super().__init__(dataset, cfg=cfg, embedder=embedder)
            seen["init"] = self.seen

        def predict(self, system, df, edges_df, nodes_total=None):
            seen["rows"] = len(df)
            return super().predict(system, df, edges_df, nodes_total=nodes_total)

    monkeypatch.setattr("eval_twibot_native.load_accounts_with_ids", lambda path: accounts_df.copy())
    monkeypatch.setattr("eval_twibot_native.build_edges", lambda df, path: empty_edges_df)
    monkeypatch.setattr("eval_twibot_native.joblib.load", lambda path: SimpleNamespace(cfg=None, embedder=object()))
    monkeypatch.setattr("eval_twibot_native.CascadePipeline", SeenPipeline)

    run_inference_twibot_native("test.json")

    assert seen["init"]["dataset"] == "twibot"
    assert seen["rows"] == len(accounts_df)


def test_evaluate_twibot_native_writes_metrics_and_confusion_matrix(monkeypatch, tmp_path):
    results_df = pd.DataFrame(
        {
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
        }
    )
    accounts_df = _make_accounts_df()

    def _fake_cm_writer(results, y_true, threshold, output_path, title):
        with open(output_path, "wb") as f:
            f.write(b"PNG")

    monkeypatch.setattr("eval_twibot_native.run_inference_twibot_native", lambda path, model_path=DEFAULT_TWIBOT_MODEL_PATH: results_df)
    monkeypatch.setattr("eval_twibot_native.load_accounts_with_ids", lambda path: accounts_df.copy())
    monkeypatch.setattr(
        "eval_twibot_native.evaluate_s3",
        lambda results, y_true, threshold=0.5, verbose=False: {
            "overall": {"f1": 0.5, "auc": 0.6, "precision": 0.7, "recall": 0.8},
            "per_stage": {"p1": {}, "p2": {}, "p12": {}, "p_final": {}},
            "routing": {
                "pct_stage1_exit": 50.0,
                "pct_stage2_exit": 0.0,
                "pct_stage3_exit": 50.0,
                "pct_amr_triggered": 50.0,
            },
        },
    )
    monkeypatch.setattr("eval_twibot_native._write_confusion_matrix", _fake_cm_writer)

    summary = evaluate_twibot_native(output_dir=str(tmp_path))
    metrics_path = os.path.join(str(tmp_path), "metrics_twibot_native.json")
    cm_path = os.path.join(str(tmp_path), "confusion_matrix_twibot_native.png")

    assert os.path.exists(metrics_path)
    assert os.path.exists(cm_path)
    assert os.path.getsize(cm_path) > 0
    with open(metrics_path, encoding="utf-8") as f:
        payload = json.load(f)
    assert set(payload.keys()) == {"overall", "per_stage", "routing"}
    assert summary["paths"]["metrics"] == metrics_path


def test_evaluate_twibot_native_summary_paths_schema(monkeypatch, tmp_path):
    monkeypatch.setattr(
        "eval_twibot_native.run_inference_twibot_native",
        lambda path, model_path=DEFAULT_TWIBOT_MODEL_PATH: pd.DataFrame(
            {
                "account_id": ["tw_000"],
                "p1": [0.0],
                "n1": [0.0],
                "p2": [0.0],
                "n2": [0.0],
                "amr_used": [0],
                "p12": [0.0],
                "stage3_used": [0],
                "p3": [0.0],
                "n3": [0.0],
                "p_final": [0.0],
            }
        ),
    )
    monkeypatch.setattr("eval_twibot_native.load_accounts_with_ids", lambda path: _make_accounts_df().iloc[:1].copy())
    monkeypatch.setattr(
        "eval_twibot_native.evaluate_s3",
        lambda results, y_true, threshold=0.5, verbose=False: {
            "overall": {},
            "per_stage": {"p1": {}, "p2": {}, "p12": {}, "p_final": {}},
            "routing": {},
        },
    )
    monkeypatch.setattr(
        "eval_twibot_native._write_confusion_matrix",
        lambda results, y_true, threshold, output_path, title: open(output_path, "wb").write(b"PNG"),
    )

    summary = evaluate_twibot_native(output_dir=str(tmp_path))

    assert set(summary["paths"].keys()) == {"metrics", "confusion_matrix", "model"}


def test_twibot_native_does_not_use_botsim_artifact():
    assert DEFAULT_TWIBOT_MODEL_PATH == "trained_system_twibot.joblib"
