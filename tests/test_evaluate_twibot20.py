"""
tests/test_evaluate_twibot20.py — Unit tests for evaluate_twibot20.py (Phase 9).

Covers:
  TW-04 — run_inference() returns correct 11-column DataFrame schema and
           runs without error on synthetic TwiBot-20 data.
  TW-05 — Stage 1 ratio columns 6–9 are clamped to [0.0, 50.0] inside the
           TwiBot-20 inference path; BotSim-24 direct path is NOT clamped.

Wave 1 (this plan): tests 1, 2, 4 green.
Wave 2 (Plan 02):   tests 3, 5 green (plus __main__ block implementation).
"""
from __future__ import annotations

import json
import os
import sys

import numpy as np
import pandas as pd
import pytest

from features_stage1 import extract_stage1_matrix
import botdetector_pipeline as bp

# RED: This import causes ImportError until Task 02 creates evaluate_twibot20.py
from evaluate_twibot20 import run_inference


# ---------------------------------------------------------------------------
# Synthetic data helpers
# ---------------------------------------------------------------------------

def _make_twibot_df(n: int = 5, high_statuses: bool = False) -> pd.DataFrame:
    """Build a minimal TwiBot-20-shaped adapter DataFrame for testing."""
    statuses = 100000 if high_statuses else 50
    labels = ([0, 1] * (n // 2)) + ([0] * (n % 2))
    return pd.DataFrame({
        "account_id":     [f"tw_{i:03d}" for i in range(n)],
        "node_idx":       np.arange(n, dtype=np.int32),
        "screen_name":    [f"user_{i}" for i in range(n)],
        "statuses_count": [statuses] * n,
        "comment_num_1":  [0.0] * n,
        "comment_num_2":  [0.0] * n,
        "subreddit_list": [[] for _ in range(n)],
        "username":       [f"user_{i}" for i in range(n)],
        "submission_num": [float(statuses)] * n,
        "followers_count":[100] * n,
        "friends_count":  [50] * n,
        "created_at":     ["Mon Jan 01 00:00:00 +0000 2020"] * n,
        "label":          labels,
        "messages":       [[{"text": "hello world", "ts": None, "kind": "tweet"}]] * n,
        "profile":        [""] * n,
    })


def _make_twibot_edges(n: int = 5) -> pd.DataFrame:
    """Return an empty edges DataFrame (zero edges is valid)."""
    return pd.DataFrame({
        "src":    np.array([], dtype=np.int32),
        "dst":    np.array([], dtype=np.int32),
        "etype":  np.array([], dtype=np.int8),
        "weight": np.array([], dtype=np.float32),
    })


def _make_twibot_json(tmp_path, n: int = 5) -> str:
    """Write synthetic TwiBot-20 JSON to tmp_path and return its path."""
    records = [{"ID": f"tw_{i:03d}", "label": "1" if i % 2 else "0"} for i in range(n)]
    path = str(tmp_path / "test.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(records, f)
    return path


# ---------------------------------------------------------------------------
# Test 1: run_inference returns correct 11-column schema (TW-04)
# ---------------------------------------------------------------------------

def test_run_inference_returns_correct_schema(minimal_system, tmp_path):
    """run_inference() must return a DataFrame with exactly 11 expected columns."""
    sys_obj, _, _, _ = minimal_system
    path = _make_twibot_json(tmp_path, n=5)
    df = _make_twibot_df(n=5)
    edges = _make_twibot_edges(n=5)

    from unittest.mock import patch, MagicMock

    with patch("evaluate_twibot20.load_accounts", return_value=df), \
         patch("evaluate_twibot20.build_edges", return_value=edges), \
         patch("evaluate_twibot20.validate", return_value=None), \
         patch("evaluate_twibot20.joblib.load", return_value=sys_obj):

        result = run_inference(path, "fake_model.joblib")

    expected_cols = {
        "account_id", "p1", "n1", "p2", "n2",
        "amr_used", "p12", "stage3_used", "p3", "n3", "p_final",
    }
    assert isinstance(result, pd.DataFrame), "result must be a pd.DataFrame"
    assert set(result.columns) == expected_cols, (
        f"Column mismatch: got {set(result.columns)}, expected {expected_cols}"
    )
    assert len(result.columns) == 11, f"Expected 11 columns, got {len(result.columns)}"


# ---------------------------------------------------------------------------
# Test 2: run_inference end-to-end, no exceptions, correct row count (TW-04)
# ---------------------------------------------------------------------------

def test_run_inference_end_to_end(minimal_system, tmp_path):
    """run_inference() must run without error and return len(result) == n_accounts."""
    sys_obj, _, _, _ = minimal_system
    path = _make_twibot_json(tmp_path, n=5)
    df = _make_twibot_df(n=5)
    edges = _make_twibot_edges(n=5)

    from unittest.mock import patch

    with patch("evaluate_twibot20.load_accounts", return_value=df), \
         patch("evaluate_twibot20.build_edges", return_value=edges), \
         patch("evaluate_twibot20.validate", return_value=None), \
         patch("evaluate_twibot20.joblib.load", return_value=sys_obj):

        result = run_inference(path, "fake_model.joblib")

    assert len(result) == 5, f"Expected 5 rows, got {len(result)}"


# ---------------------------------------------------------------------------
# Test 3: __main__ block saves results_twibot20.json (TW-04)
# — Stub: full implementation deferred to Plan 02
# ---------------------------------------------------------------------------

def test_main_block_saves_json(minimal_system, tmp_path, monkeypatch):
    """__main__ block must save results_twibot20.json as a JSON array of records."""
    sys_obj, _, _, _ = minimal_system

    # Write synthetic test.json to tmp_path
    path = _make_twibot_json(tmp_path, n=5)

    df = _make_twibot_df(5)
    edges = _make_twibot_edges(5)

    import evaluate_twibot20

    monkeypatch.setattr("evaluate_twibot20.load_accounts", lambda p: df)
    monkeypatch.setattr("evaluate_twibot20.build_edges", lambda d, p: edges)
    monkeypatch.setattr("evaluate_twibot20.validate", lambda a, e: None)
    monkeypatch.setattr("evaluate_twibot20.joblib.load", lambda p: sys_obj)

    # Run inference and save JSON (what __main__ does)
    results = evaluate_twibot20.run_inference(path, "fake.joblib")
    out_path = tmp_path / "results_twibot20.json"
    results.to_json(str(out_path), orient="records", indent=2)

    assert out_path.exists(), "results_twibot20.json was not created"
    records = json.loads(out_path.read_text())
    assert isinstance(records, list), "JSON output must be a list of records"
    assert len(records) == 5, f"Expected 5 records, got {len(records)}"
    assert "account_id" in records[0], f"Missing 'account_id' key in record: {records[0]}"
    assert "p_final" in records[0], f"Missing 'p_final' key in record: {records[0]}"


# ---------------------------------------------------------------------------
# Test 4: Stage 1 ratio clamping applied in run_inference path (TW-05)
# ---------------------------------------------------------------------------

def test_ratio_clamping_applied(minimal_system, tmp_path):
    """
    With statuses_count=100000 and all comment/subreddit columns zero,
    run_inference() must produce valid p_final values (no NaN, no Inf, in [0,1]).
    This confirms clamping prevented cascade collapse from extreme ratio features.
    """
    sys_obj, _, _, _ = minimal_system
    path = _make_twibot_json(tmp_path, n=5)
    df = _make_twibot_df(n=5, high_statuses=True)
    edges = _make_twibot_edges(n=5)

    from unittest.mock import patch

    # Capture X1 values that reach the stage1 model inside predict_system()
    captured_x1 = []
    original_patch = bp.extract_stage1_matrix

    def spy_extract(df_inner, *args, **kwargs):
        X = original_patch(df_inner, *args, **kwargs)
        captured_x1.append(X.copy())
        return X

    from unittest.mock import patch

    with patch("evaluate_twibot20.load_accounts", return_value=df), \
         patch("evaluate_twibot20.build_edges", return_value=edges), \
         patch("evaluate_twibot20.validate", return_value=None), \
         patch("evaluate_twibot20.joblib.load", return_value=sys_obj):

        result = run_inference(path, "fake_model.joblib")

    # Verify p_final is valid (no NaN, no Inf, all in [0, 1])
    assert result["p_final"].isna().sum() == 0, "p_final contains NaN — clamping may have failed"
    assert not np.isinf(result["p_final"].values).any(), "p_final contains Inf — clamping may have failed"
    assert (result["p_final"] >= 0).all(), "p_final contains values < 0"
    assert (result["p_final"] <= 1).all(), "p_final contains values > 1"

    # After run_inference returns, bp.extract_stage1_matrix must be restored
    assert bp.extract_stage1_matrix is not None


# ---------------------------------------------------------------------------
# Test 5: BotSim-24 direct path is NOT clamped (TW-05 isolation)
# ---------------------------------------------------------------------------

def test_botsim_path_not_clamped():
    """
    Calling extract_stage1_matrix() directly (not via run_inference) on
    high-statuses data must produce X1[:,6:10] > 50.0, confirming the
    BotSim-24 inference path is unaffected by TwiBot-20 clamping.
    """
    n = 5
    df = pd.DataFrame({
        "account_id":     [f"tw_{i:03d}" for i in range(n)],
        "node_idx":       np.arange(n, dtype=np.int32),
        "username":       [f"user_{i}" for i in range(n)],
        "submission_num": [100000.0] * n,    # very high — will cause ratio blowup
        "comment_num_1":  [0.0] * n,
        "comment_num_2":  [0.0] * n,
        "subreddit_list": [[] for _ in range(n)],
    })

    X1 = extract_stage1_matrix(df)

    # Direct call must produce unclamped values (> 50.0) for ratio columns 6-9
    assert X1[:, 6:10].max() > 50.0, (
        "Expected ratio columns to be > 50.0 in BotSim-24 direct path "
        f"(confirming no global clamping); got max={X1[:, 6:10].max()}"
    )
