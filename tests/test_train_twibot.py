from __future__ import annotations

import json
import os
import shutil
import tempfile
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

from cascade_pipeline import StageThresholds
from cascade_pipeline import CascadePipeline
from train_twibot import (
    DEFAULT_TWIBOT_MODEL_PATH,
    ensure_safe_model_output_path,
    filter_edges_for_split,
    list_expected_output_files,
    split_train_accounts,
    train_twibot,
)


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
        "tweet": [f"tweet {idx}", f"RT @acct{idx}: echo {idx}"],
        "domain": ["Politics"],
        "neighbor": {"following": [], "follower": []},
    }


def test_split_train_accounts_is_deterministic():
    df = pd.DataFrame({
        "account_id": [f"tw_{i:03d}" for i in range(10)],
        "label": [0, 1] * 5,
    })

    S1_a, S2_a = split_train_accounts(df, seed=42)
    S1_b, S2_b = split_train_accounts(df, seed=42)

    assert len(S1_a) == 8
    assert len(S2_a) == 2
    assert S1_a["account_id"].tolist() == S1_b["account_id"].tolist()
    assert S2_a["account_id"].tolist() == S2_b["account_id"].tolist()


def test_filter_edges_for_split_keeps_only_internal_edges():
    edges = pd.DataFrame({
        "src": np.array([0, 0, 1, 2], dtype=np.int32),
        "dst": np.array([1, 2, 2, 3], dtype=np.int32),
        "etype": np.array([0, 0, 1, 1], dtype=np.int8),
        "weight": np.array([1.0, 1.0, 1.0, 1.0], dtype=np.float32),
    })

    filtered = filter_edges_for_split(edges, np.array([0, 1, 2], dtype=np.int32))

    assert len(filtered) == 3
    assert filtered["dst"].max() == 2


def test_cascade_pipeline_exposes_dataset_aware_surface():
    pipeline = CascadePipeline("twibot")
    assert pipeline.dataset == "twibot"
    assert pipeline.cfg.stage1_numeric_cols


def test_protected_model_artifacts_are_rejected():
    with pytest.raises(ValueError):
        ensure_safe_model_output_path("trained_system_v12.joblib")

    assert ensure_safe_model_output_path(DEFAULT_TWIBOT_MODEL_PATH) == DEFAULT_TWIBOT_MODEL_PATH


def test_train_twibot_uses_dev_for_calibration_and_separate_artifact(monkeypatch):
    temp_dir = ".phase19_twibot_test"
    try:
        os.makedirs(temp_dir, exist_ok=True)
        train_path = "train.json"
        dev_path = "dev.json"
        test_path = "test.json"
        out_dir = os.path.join(temp_dir, "artifacts")
        model_path = os.path.join(temp_dir, DEFAULT_TWIBOT_MODEL_PATH)
        train_df = pd.DataFrame(
            {
                "account_id": [f"tw_{i:03d}" for i in range(10)],
                "node_idx": np.arange(10, dtype=np.int32),
                "label": [i % 2 for i in range(10)],
            }
        )
        dev_df = pd.DataFrame(
            {
                "account_id": [f"tw_{100 + i:03d}" for i in range(4)],
                "node_idx": np.arange(4, dtype=np.int32),
                "label": [i % 2 for i in range(4)],
            }
        )
        test_df = pd.DataFrame(
            {
                "account_id": [f"tw_{200 + i:03d}" for i in range(4)],
                "node_idx": np.arange(4, dtype=np.int32),
                "label": [i % 2 for i in range(4)],
            }
        )

        fake_system = SimpleNamespace(
            th=StageThresholds(),
            calibration_report_={"selected_trial_number": 0, "trials": [{"trial_number": 0, "primary_score": 0.5, "secondary_log_loss": 0.2, "secondary_brier": 0.1, "positive_predictions": 2, "amr_usage_rate": 0.5, "stage3_usage_rate": 0.5, "label_signature": "single_trial", "routing_signature": "single_trial", "thresholds": {"s1_bot": 0.98, "s1_human": 0.02, "n1_max_for_exit": 3.0, "s2a_bot": 0.95, "s2a_human": 0.05, "n2_trigger": 3.0, "disagreement_trigger": 4.0, "s12_bot": 0.98, "s12_human": 0.02, "novelty_force_stage3": 3.5}}], "metric": "f1", "requested_trials": 1, "executed_trials": 1, "stopped_early": False, "plateau_patience": 1, "best_primary_score": 0.5, "selected_secondary_log_loss": 0.2, "selected_secondary_brier": 0.1, "best_tie_count": 1, "best_tie_same_hard_predictions": True, "best_tie_same_routing": True},
            embedder=object(),
            cfg=None,
        )

        captured = {}

        class FakePipeline:
            def __init__(self, dataset, cfg=None, random_state=42, embedder=None):
                captured["pipeline_init"] = {
                    "dataset": dataset,
                    "cfg": cfg,
                    "random_state": random_state,
                }

            def fit(self, **kwargs):
                captured["train_system"] = kwargs
                return fake_system

            def predict(self, system, df, edges_df, nodes_total=None):
                captured["predict"] = {
                    "account_ids": df["account_id"].tolist(),
                    "nodes_total": nodes_total,
                }
                n = len(df)
                return pd.DataFrame({
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
                })

        def fake_calibrate_thresholds(**kwargs):
            captured["calibrate"] = kwargs
            return fake_system.th

        def fake_evaluate_s3(results, y_true, threshold=0.5, verbose=True):
            return {
                "overall": {"f1": 0.1, "auc": 0.2, "precision": 0.3, "recall": 0.4},
                "per_stage": {"p1": {}, "p2": {}, "p12": {}, "p_final": {}},
                "routing": {"pct_stage1_exit": 50.0, "pct_stage2_exit": 25.0, "pct_stage3_exit": 25.0, "pct_amr_triggered": 0.0},
            }

        dumped = {}

        monkeypatch.setattr("train_twibot.CascadePipeline", FakePipeline)
        monkeypatch.setattr("train_twibot.calibrate_thresholds", fake_calibrate_thresholds)
        monkeypatch.setattr("train_twibot.evaluate_s3", fake_evaluate_s3)
        monkeypatch.setattr("train_twibot.joblib.dump", lambda system, path: dumped.setdefault("path", path))
        monkeypatch.setattr(
            "train_twibot.load_accounts_with_ids",
            lambda path: {"train.json": train_df, "dev.json": dev_df, "test.json": test_df}[path].copy(),
        )
        monkeypatch.setattr(
            "train_twibot.build_edges",
            lambda df, path: pd.DataFrame(
                {
                    "src": np.array([], dtype=np.int32),
                    "dst": np.array([], dtype=np.int32),
                    "etype": np.array([], dtype=np.int8),
                    "weight": np.array([], dtype=np.float32),
                }
            ),
        )

        summary = train_twibot(
            train_path=train_path,
            dev_path=dev_path,
            test_path=test_path,
            model_output_path=model_path,
            output_dir=out_dir,
            calibrate_trials=3,
        )

        assert captured["pipeline_init"]["dataset"] == "twibot"
        assert captured["calibrate"]["S2"]["account_id"].tolist() == [f"tw_{100 + i:03d}" for i in range(4)]
        assert captured["calibrate"]["n_trials"] == 1
        assert dumped["path"] == model_path
        assert summary["paths"]["model"] == model_path
        assert os.path.exists(os.path.join(out_dir, "metrics_twibot20_native.json"))
        assert os.path.exists(os.path.join(out_dir, "results_twibot20_native.json"))
        assert os.path.exists(os.path.join(out_dir, "calibration_twibot20_native.json"))
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)


def test_expected_output_files_are_stable():
    assert list_expected_output_files() == [
        "metrics_twibot20_native.json",
        "results_twibot20_native.json",
        "calibration_twibot20_native.json",
    ]
