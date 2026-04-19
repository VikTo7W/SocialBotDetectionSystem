from __future__ import annotations

import json
import os
from types import SimpleNamespace

import numpy as np
import pandas as pd

from eval_reddit_twibot_transfer import (
    DEFAULT_OUTPUT_DIR,
    _apply_transfer_adapter,
    evaluate_reddit_twibot_transfer,
    run_inference_transfer,
)
from train_botsim import DEFAULT_BOTSIM_MODEL_PATH
from train_twibot import DEFAULT_TWIBOT_MODEL_PATH


def _make_twibot_accounts_df():
    return pd.DataFrame(
        {
            "account_id": ["tw_000", "tw_001"],
            "username": ["u0", "u1"],
            "screen_name": ["u0", "u1"],
            "node_idx": np.array([0, 1], dtype=np.int32),
            "label": [0, 1],
            "messages": [
                [{"text": "hi", "ts": None}],
                [{"text": "RT @a: hello", "ts": None}, {"text": "MT hi", "ts": None}],
            ],
            "domain_list": [["Politics"], ["Sports", "Tech"]],
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


def test_transfer_adapter_populates_botsim_columns():
    accounts_df = _make_twibot_accounts_df()
    adapted = _apply_transfer_adapter(accounts_df)

    for column in ("submission_num", "comment_num_1", "comment_num_2", "subreddit_list"):
        assert column in adapted.columns
        assert len(adapted[column]) == len(accounts_df)


def test_transfer_adapter_does_not_mutate_input():
    accounts_df = _make_twibot_accounts_df()
    _apply_transfer_adapter(accounts_df)
    assert "submission_num" not in accounts_df.columns


def test_transfer_adapter_adds_account_id_when_missing():
    accounts_df = _make_twibot_accounts_df().drop(columns=["account_id"])
    adapted = _apply_transfer_adapter(accounts_df)
    assert "account_id" in adapted.columns
    assert adapted["account_id"].tolist() == ["0", "1"]


def test_run_inference_transfer_uses_botsim_model_path(monkeypatch):
    seen = {}
    accounts_df = _make_twibot_accounts_df()
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

    monkeypatch.setattr("eval_reddit_twibot_transfer.load_accounts", lambda path: accounts_df.copy())
    monkeypatch.setattr("eval_reddit_twibot_transfer.build_edges", lambda df, path: empty_edges_df)
    monkeypatch.setattr(
        "eval_reddit_twibot_transfer.joblib.load",
        lambda path: (seen.__setitem__("model_path", path), SimpleNamespace(cfg=None, embedder=object()))[1],
    )
    monkeypatch.setattr("eval_reddit_twibot_transfer.CascadePipeline", SeenPipeline)

    run_inference_transfer("test.json")

    assert seen["model_path"] == DEFAULT_BOTSIM_MODEL_PATH
    assert seen["pipeline"]["dataset"] == "botsim"
    assert DEFAULT_BOTSIM_MODEL_PATH != DEFAULT_TWIBOT_MODEL_PATH
    assert DEFAULT_BOTSIM_MODEL_PATH != "trained_system_v12.joblib"


def test_evaluate_reddit_transfer_writes_metrics_and_confusion_matrix(monkeypatch, tmp_path):
    adapted = _make_twibot_accounts_df()
    results_df = pd.DataFrame(
        {
            "account_id": adapted["account_id"].tolist(),
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

    def _fake_cm_writer(results, y_true, threshold, output_path, title):
        with open(output_path, "wb") as f:
            f.write(b"PNG")

    monkeypatch.setattr("eval_reddit_twibot_transfer.run_inference_transfer", lambda path, model_path=DEFAULT_BOTSIM_MODEL_PATH: (results_df, adapted))
    monkeypatch.setattr(
        "eval_reddit_twibot_transfer.evaluate_s3",
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
    monkeypatch.setattr("eval_reddit_twibot_transfer._write_confusion_matrix", _fake_cm_writer)

    summary = evaluate_reddit_twibot_transfer(output_dir=str(tmp_path))
    metrics_path = os.path.join(str(tmp_path), "metrics_reddit_transfer.json")
    cm_path = os.path.join(str(tmp_path), "confusion_matrix_reddit_transfer.png")

    assert os.path.exists(metrics_path)
    assert os.path.exists(cm_path)
    assert os.path.getsize(cm_path) > 0
    with open(metrics_path, encoding="utf-8") as f:
        payload = json.load(f)
    assert set(payload.keys()) == {"overall", "per_stage", "routing"}
    assert summary["paths"]["metrics"] == metrics_path


def test_eval_reddit_twibot_transfer_does_not_monkeypatch_bp_extract_stage1_matrix(monkeypatch):
    import cascade_pipeline as bp

    before = bp.extract_stage1_matrix
    adapted = _make_twibot_accounts_df()
    results_df = pd.DataFrame(
        {
            "account_id": adapted["account_id"].tolist(),
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

    monkeypatch.setattr("eval_reddit_twibot_transfer.run_inference_transfer", lambda path, model_path=DEFAULT_BOTSIM_MODEL_PATH: (results_df, adapted))
    monkeypatch.setattr(
        "eval_reddit_twibot_transfer.evaluate_s3",
        lambda results, y_true, threshold=0.5, verbose=False: {
            "overall": {},
            "per_stage": {"p1": {}, "p2": {}, "p12": {}, "p_final": {}},
            "routing": {},
        },
    )
    monkeypatch.setattr(
        "eval_reddit_twibot_transfer._write_confusion_matrix",
        lambda results, y_true, threshold, output_path, title: open(output_path, "wb").write(b"PNG"),
    )

    evaluate_reddit_twibot_transfer(output_dir=os.getcwd())

    assert bp.extract_stage1_matrix is before
    os.remove(os.path.join(os.getcwd(), "metrics_reddit_transfer.json"))
    os.remove(os.path.join(os.getcwd(), "confusion_matrix_reddit_transfer.png"))
