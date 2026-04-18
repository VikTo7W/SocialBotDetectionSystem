from __future__ import annotations

import json

import numpy as np
import pandas as pd

import botdetector_pipeline as bp
from evaluate_twibot20_native import (
    DEFAULT_METRICS_FILENAME,
    DEFAULT_RESULTS_FILENAME,
    evaluate_twibot20_native,
    run_inference_native,
)
from train_twibot20 import DEFAULT_NATIVE_MODEL_PATH


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


def test_run_inference_native_defaults_to_native_model_path(tmp_path, monkeypatch):
    test_path = tmp_path / "test.json"
    _write_split(test_path, [_record(0, 0), _record(1, 1)])

    seen = {}

    monkeypatch.setattr("evaluate_twibot20_native.joblib.load", lambda path: seen.setdefault("model_path", path) or object())
    monkeypatch.setattr(
        "evaluate_twibot20_native.predict_system",
        lambda system, df, edges_df, nodes_total=None: pd.DataFrame({
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
        }),
    )

    run_inference_native(str(test_path))

    assert seen["model_path"] == DEFAULT_NATIVE_MODEL_PATH
    assert DEFAULT_NATIVE_MODEL_PATH != "trained_system_v12.joblib"


def test_run_inference_native_restores_pipeline_extractors(tmp_path, monkeypatch):
    test_path = tmp_path / "test.json"
    _write_split(test_path, [_record(0, 0)])

    original_s1 = bp.extract_stage1_matrix
    original_s2 = bp.extract_stage2_features

    monkeypatch.setattr("evaluate_twibot20_native.joblib.load", lambda path: object())
    monkeypatch.setattr(
        "evaluate_twibot20_native.predict_system",
        lambda system, df, edges_df, nodes_total=None: pd.DataFrame({
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
        }),
    )

    run_inference_native(str(test_path))

    assert bp.extract_stage1_matrix is original_s1
    assert bp.extract_stage2_features is original_s2


def test_evaluate_twibot20_native_writes_schema_stable_artifacts(tmp_path, monkeypatch):
    test_path = tmp_path / "test.json"
    out_dir = tmp_path / "artifacts"
    _write_split(test_path, [_record(0, 0), _record(1, 1)])

    monkeypatch.setattr(
        "evaluate_twibot20_native.run_inference_native",
        lambda path, model_path=DEFAULT_NATIVE_MODEL_PATH: pd.DataFrame({
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

    summary = evaluate_twibot20_native(
        path=str(test_path),
        model_path="trained_system_twibot20.joblib",
        output_dir=str(out_dir),
    )

    assert set(summary["metrics"].keys()) == {"overall", "per_stage", "routing"}
    assert (out_dir / DEFAULT_RESULTS_FILENAME).exists()
    assert (out_dir / DEFAULT_METRICS_FILENAME).exists()


def test_native_evaluation_is_separate_from_legacy_zero_shot_path():
    assert DEFAULT_NATIVE_MODEL_PATH != "trained_system_v12.joblib"
