from __future__ import annotations

import os
import shutil
import tempfile
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from cascade_pipeline import StageThresholds
from train_botsim import (
    DEFAULT_BOTSIM_MODEL_PATH,
    ensure_safe_model_output_path,
    split_train_accounts,
    train_botsim,
)


def _fake_users_df(n: int = 12) -> pd.DataFrame:
    return pd.DataFrame(
        {
            "user_id": [f"user_{i}" for i in range(n)],
            "name": [f"name_{i}" for i in range(n)],
            "description": [""] * n,
            "submission_num": [1.0] * n,
            "comment_num": [1.0] * n,
            "comment_num_1": [1.0] * n,
            "comment_num_2": [1.0] * n,
            "subreddit": ["news"] * n,
        }
    )


def _fake_accounts_df(n: int = 12) -> pd.DataFrame:
    labels = [0, 1] * (n // 2)
    return pd.DataFrame(
        {
            "account_id": [f"user_{i}" for i in range(n)],
            "label": labels,
            "username": [f"name_{i}" for i in range(n)],
            "profile": [""] * n,
            "subreddit_list": [["news"]] * n,
            "submission_num": np.ones(n, dtype=np.float32),
            "comment_num": np.ones(n, dtype=np.float32),
            "comment_num_1": np.ones(n, dtype=np.float32),
            "comment_num_2": np.ones(n, dtype=np.float32),
            "messages": [[{"text": "hello", "ts": 1.0, "kind": "post"}]] * n,
        }
    )


class _FakeTensor:
    def __init__(self, value):
        self._value = np.asarray(value)

    def numpy(self):
        return self._value


def test_split_train_accounts_is_deterministic():
    df = pd.DataFrame(
        {
            "account_id": [f"user_{i}" for i in range(20)],
            "label": [0, 1] * 10,
        }
    )

    S1_a, S2_a, S3_a = split_train_accounts(df, seed=42)
    S1_b, S2_b, S3_b = split_train_accounts(df, seed=42)

    assert S1_a["account_id"].tolist() == S1_b["account_id"].tolist()
    assert S2_a["account_id"].tolist() == S2_b["account_id"].tolist()
    assert S3_a["account_id"].tolist() == S3_b["account_id"].tolist()


def test_protected_model_artifacts_are_rejected():
    with pytest.raises(ValueError):
        ensure_safe_model_output_path("trained_system_twibot.joblib")

    assert ensure_safe_model_output_path(DEFAULT_BOTSIM_MODEL_PATH) == DEFAULT_BOTSIM_MODEL_PATH


def test_train_botsim_uses_shared_pipeline_and_writes_botsim_artifact(monkeypatch):
    temp_dir = tempfile.mkdtemp(dir=".")
    try:
        model_path = os.path.join(temp_dir, DEFAULT_BOTSIM_MODEL_PATH)
        fake_users = _fake_users_df()
        fake_accounts = _fake_accounts_df()
        fake_system = SimpleNamespace(th=StageThresholds(), calibration_report_={}, embedder=object(), cfg=None)
        captured = {}
    
        class FakePipeline:
            def __init__(self, dataset, cfg=None, random_state=42, embedder=None):
                captured["pipeline_init"] = {
                    "dataset": dataset,
                    "random_state": random_state,
                }
    
            def fit(self, **kwargs):
                captured["fit"] = kwargs
                return fake_system
    
            def predict(self, system, df, edges_df, nodes_total=None):
                captured["predict"] = {
                    "rows": len(df),
                    "nodes_total": nodes_total,
                }
                n = len(df)
                return pd.DataFrame(
                    {
                        "account_id": df["account_id"].tolist(),
                        "p1": np.full(n, 0.4),
                        "n1": np.full(n, 1.0),
                        "p2": np.full(n, 0.5),
                        "n2": np.full(n, 1.0),
                        "amr_used": np.zeros(n, dtype=int),
                        "p12": np.full(n, 0.45),
                        "stage3_used": np.zeros(n, dtype=int),
                        "p3": np.full(n, 0.5),
                        "n3": np.zeros(n),
                        "p_final": np.full(n, 0.46),
                    }
                )
    
        def fake_calibrate_thresholds(**kwargs):
            captured["calibrate"] = kwargs
            return fake_system.th
    
        def fake_evaluate_s3(results, y_true, threshold=0.5, verbose=True):
            return {
                "overall": {"f1": 0.1, "auc": 0.2, "precision": 0.3, "recall": 0.4},
                "per_stage": {"p1": {}, "p2": {}, "p12": {}, "p_final": {}},
                "routing": {
                    "pct_stage1_exit": 50.0,
                    "pct_stage2_exit": 25.0,
                    "pct_stage3_exit": 25.0,
                    "pct_amr_triggered": 0.0,
                },
            }
    
        dumped = {}
    
        monkeypatch.setattr("train_botsim.load_users_csv", lambda path: fake_users)
        monkeypatch.setattr("train_botsim.load_user_post_comment_json", lambda path: {})
        monkeypatch.setattr("train_botsim.build_account_table", lambda users_df, upc: fake_accounts.copy())
        monkeypatch.setattr(
            "train_botsim.torch.load",
            lambda path, map_location=None: _FakeTensor(
                {
                    "edge_index.pt": np.array([[0, 1], [1, 2]], dtype=np.int32),
                    "edge_type.pt": np.array([0, 1], dtype=np.int8),
                    "edge_weight.pt": np.array([1.0, 1.0], dtype=np.float32),
                }[path]
            ),
        )
        monkeypatch.setattr("train_botsim.CascadePipeline", FakePipeline)
        monkeypatch.setattr("train_botsim.calibrate_thresholds", fake_calibrate_thresholds)
        monkeypatch.setattr("train_botsim.evaluate_s3", fake_evaluate_s3)
        monkeypatch.setattr("train_botsim.joblib.dump", lambda system, path: dumped.setdefault("path", path))
    
        summary = train_botsim(
            users_path="Users.csv",
            interactions_path="user_post_comment.json",
            edge_index_path="edge_index.pt",
            edge_type_path="edge_type.pt",
            edge_weight_path="edge_weight.pt",
            model_output_path=model_path,
        )
    
        assert captured["pipeline_init"]["dataset"] == "botsim"
        assert captured["calibrate"]["n_trials"] == 1
        assert dumped["path"] == model_path
        assert summary["paths"]["model"] == model_path
        assert summary["splits"]["s1_size"] > 0
        assert summary["splits"]["s2_size"] > 0
        assert summary["splits"]["s3_size"] > 0
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)
