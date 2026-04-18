from __future__ import annotations

import json
from types import SimpleNamespace

import numpy as np
import pandas as pd
import pytest

import botdetector_pipeline as bp
from botdetector_pipeline import StageThresholds
from train_twibot20 import (
    DEFAULT_NATIVE_MODEL_PATH,
    ensure_safe_model_output_path,
    filter_edges_for_split,
    list_expected_output_files,
    native_feature_overrides,
    split_train_accounts,
    train_twibot20,
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


def test_native_feature_overrides_restore_pipeline_symbols():
    original_s1 = bp.extract_stage1_matrix
    original_s2 = bp.extract_stage2_features

    with native_feature_overrides():
        assert bp.extract_stage1_matrix is not original_s1
        assert bp.extract_stage2_features is not original_s2

    assert bp.extract_stage1_matrix is original_s1
    assert bp.extract_stage2_features is original_s2


def test_protected_model_artifacts_are_rejected():
    with pytest.raises(ValueError):
        ensure_safe_model_output_path("trained_system_v12.joblib")

    assert ensure_safe_model_output_path(DEFAULT_NATIVE_MODEL_PATH) == DEFAULT_NATIVE_MODEL_PATH


def test_train_twibot20_uses_dev_for_calibration_and_separate_artifact(tmp_path, monkeypatch):
    train_path = tmp_path / "train.json"
    dev_path = tmp_path / "dev.json"
    test_path = tmp_path / "test.json"
    out_dir = tmp_path / "artifacts"
    model_path = tmp_path / "trained_system_twibot20.joblib"

    _write_split(train_path, [_record(i, i % 2) for i in range(10)])
    _write_split(dev_path, [_record(100 + i, i % 2) for i in range(4)])
    _write_split(test_path, [_record(200 + i, i % 2) for i in range(4)])

    fake_system = SimpleNamespace(
        th=StageThresholds(),
        calibration_report_={"selected_trial_number": 1, "trials": [{"trial_number": 1, "primary_score": 0.5, "secondary_log_loss": 0.2, "secondary_brier": 0.1, "positive_predictions": 2, "amr_usage_rate": 0.5, "stage3_usage_rate": 0.5, "label_signature": "abc", "routing_signature": "def", "thresholds": {"s1_bot": 0.98, "s1_human": 0.02, "n1_max_for_exit": 3.0, "s2a_bot": 0.95, "s2a_human": 0.05, "n2_trigger": 3.0, "disagreement_trigger": 4.0, "s12_bot": 0.98, "s12_human": 0.02, "novelty_force_stage3": 3.5}}], "metric": "f1", "requested_trials": 1, "executed_trials": 1, "stopped_early": False, "plateau_patience": 1, "best_primary_score": 0.5, "selected_secondary_log_loss": 0.2, "selected_secondary_brier": 0.1, "best_tie_count": 1, "best_tie_same_hard_predictions": True, "best_tie_same_routing": True},
        embedder=object(),
        cfg=None,
        stage2b_variant="amr",
    )

    captured = {}

    def fake_train_system(**kwargs):
        captured["train_system"] = kwargs
        return fake_system

    def fake_calibrate_thresholds(**kwargs):
        captured["calibrate"] = kwargs
        return fake_system.th

    def fake_predict_system(system, df, edges_df, nodes_total=None):
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

    def fake_evaluate_s3(results, y_true, threshold=0.5, verbose=True):
        return {
            "overall": {"f1": 0.1, "auc": 0.2, "precision": 0.3, "recall": 0.4},
            "per_stage": {"p1": {}, "p2": {}, "p12": {}, "p_final": {}},
            "routing": {"pct_stage1_exit": 50.0, "pct_stage2_exit": 25.0, "pct_stage3_exit": 25.0, "pct_amr_triggered": 0.0},
        }

    dumped = {}

    monkeypatch.setattr("train_twibot20.train_system", fake_train_system)
    monkeypatch.setattr("train_twibot20.calibrate_thresholds", fake_calibrate_thresholds)
    monkeypatch.setattr("train_twibot20.predict_system", fake_predict_system)
    monkeypatch.setattr("train_twibot20.evaluate_s3", fake_evaluate_s3)
    monkeypatch.setattr("train_twibot20.joblib.dump", lambda system, path: dumped.setdefault("path", path))

    summary = train_twibot20(
        train_path=str(train_path),
        dev_path=str(dev_path),
        test_path=str(test_path),
        model_output_path=str(model_path),
        output_dir=str(out_dir),
        calibrate_trials=3,
    )

    assert captured["calibrate"]["S2"]["account_id"].tolist() == [f"tw_{100 + i:03d}" for i in range(4)]
    assert dumped["path"] == str(model_path)
    assert summary["paths"]["model"] == str(model_path)
    assert (out_dir / "metrics_twibot20_native.json").exists()
    assert (out_dir / "results_twibot20_native.json").exists()
    assert (out_dir / "calibration_twibot20_native.json").exists()


def test_expected_output_files_are_stable():
    assert list_expected_output_files() == [
        "metrics_twibot20_native.json",
        "results_twibot20_native.json",
        "calibration_twibot20_native.json",
    ]
