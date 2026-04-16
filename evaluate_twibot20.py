"""
evaluate_twibot20.py — Zero-shot inference on TwiBot-20 test accounts.

Runs trained_system_v12.joblib on TwiBot-20 test.json without retraining.
Adapts TwiBot-20 columns to BotSim-24 pipeline schema (D-02, D-03, D-07).
Applies Stage 1 ratio clamping via monkey-patch (TW-05, D-04).

Note: All temporal features (cv_intervals, rate, delta_mean, delta_std,
hour_entropy) are zero for all TwiBot-20 accounts — tweets are plain strings
with ts=None. This is expected behavior, not an error (D-08).

Phase 10 imports run_inference() directly. The __main__ block also saves
results_twibot20.json (records-oriented) for manual inspection (D-06).
"""
from __future__ import annotations

import json
import sys

import joblib
import numpy as np
import pandas as pd

from twibot20_io import load_accounts, build_edges, validate
from features_stage1 import extract_stage1_matrix as _orig_extract_stage1_matrix
import botdetector_pipeline as bp
from botdetector_pipeline import predict_system, TrainedSystem
from evaluate import evaluate_s3


def run_inference(
    path: str,
    model_path: str = "trained_system_v12.joblib",
) -> pd.DataFrame:
    """Run zero-shot inference on TwiBot-20 test accounts.

    Adapts TwiBot-20 columns to BotSim-24 pipeline schema, applies Stage 1
    ratio clamping via monkey-patch (TW-05), and returns the full inference
    results DataFrame.

    Note: All temporal features (cv_intervals, rate, delta_mean, delta_std,
    hour_entropy) are zero for all TwiBot-20 accounts because tweets are
    plain strings with no per-tweet timestamps (ts=None). This is expected
    and documented, not an error (D-08).

    Args:
        path: Path to TwiBot-20 test.json.
        model_path: Path to joblib model artifact
            (default: trained_system_v12.joblib).

    Returns:
        pd.DataFrame with columns: account_id, p1, n1, p2, n2, amr_used,
        p12, stage3_used, p3, n3, p_final.
    """
    # Step 1 — Load data (Phase 8 layer)
    accounts_df = load_accounts(path)
    edges_df = build_edges(accounts_df, path)
    validate(accounts_df, edges_df)

    # Step 2 — Load model
    sys_loaded: TrainedSystem = joblib.load(model_path)

    # Step 3 — Column adapter (TwiBot-20 -> BotSim-24 pipeline schema)
    # Re-read JSON to extract stable Twitter user ID strings (D-07).
    # load_accounts() iterates data in JSON array order; this re-read uses the
    # same order, so [r["ID"] for r in raw] aligns with accounts_df rows exactly.
    with open(path, "r", encoding="utf-8") as f:
        raw = json.load(f)

    df = accounts_df.copy()
    df["account_id"]     = [r["ID"] for r in raw]                   # D-07
    df["username"]       = df["screen_name"]                         # D-03
    df["submission_num"] = df["statuses_count"].astype(float)        # D-02
    df["comment_num_1"]  = 0.0                                       # D-03
    df["comment_num_2"]  = 0.0                                       # D-03
    df["subreddit_list"] = [[] for _ in range(len(df))]              # D-03

    # Step 4 — Stage 1 ratio clamping via monkey-patch (TW-05, D-04)
    # predict_system() calls bp.extract_stage1_matrix() internally (line 647).
    # Pre-clipping X1 before the call would have no effect. Instead, we
    # temporarily replace bp.extract_stage1_matrix with a clamped wrapper and
    # restore the original in a finally block (T-09-01 mitigation).
    def _clamped_s1(df_inner, *args, **kwargs):
        X = _orig_extract_stage1_matrix(df_inner)
        X[:, 6:10] = np.clip(X[:, 6:10], 0.0, 50.0)  # clamp post_c1/c2/ct/sr
        return X

    bp.extract_stage1_matrix = _clamped_s1
    try:
        results = predict_system(
            sys_loaded, df, edges_df, nodes_total=len(accounts_df)
        )
    finally:
        bp.extract_stage1_matrix = _orig_extract_stage1_matrix  # always restore (T-09-01)

    return results


def evaluate_twibot20(
    path: str = "test.json",
    model_path: str = "trained_system_v12.joblib",
    threshold: float = 0.5,
) -> dict:
    """Run zero-shot inference on TwiBot-20 and evaluate against ground truth.

    Calls run_inference() then evaluate_s3(). The evaluate_s3() call prints
    the paper-ready report to stdout (same format as main.py).

    Note: All temporal features are zero for TwiBot-20 accounts (plain-text
    tweets, no timestamps). This is expected and documented (D-08).

    Args:
        path: Path to TwiBot-20 test.json.
        model_path: Path to trained model joblib.
        threshold: Classification cutoff (default 0.5).

    Returns:
        dict from evaluate_s3(): {"overall": {...}, "per_stage": {...}, "routing": {...}}
    """
    results = run_inference(path, model_path)
    accounts_df = load_accounts(path)
    y_true = accounts_df["label"].to_numpy()
    metrics = evaluate_s3(results, y_true, threshold)
    return metrics


if __name__ == "__main__":
    data_path  = sys.argv[1] if len(sys.argv) > 1 else "test.json"
    model_path = sys.argv[2] if len(sys.argv) > 2 else "trained_system_v12.joblib"

    # Run inference once
    results = run_inference(data_path, model_path)

    # Save inference results (Phase 9 output, preserved)
    out_path = "results_twibot20.json"
    results.to_json(out_path, orient="records", indent=2)
    print(f"[twibot20] Saved {len(results)} inference results to {out_path}")

    # Evaluate against ground truth (prints paper-ready report via evaluate_s3)
    accounts_df = load_accounts(data_path)
    y_true = accounts_df["label"].to_numpy()
    metrics = evaluate_s3(results, y_true)

    # Save metrics for cross-dataset table (Phase 10 output)
    metrics_path = "metrics_twibot20.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n[twibot20] Saved evaluation metrics to {metrics_path}")

    # Summary stats
    bots = int((results["p_final"] >= 0.5).sum())
    print(f"[twibot20] Accounts: {len(results)} | Predicted bots (p_final>=0.5): {bots}")
    print(f"[twibot20] Stage 3 used: {results['stage3_used'].mean():.3f}")
    print(f"[twibot20] AMR used:     {results['amr_used'].mean():.3f}")
    print(f"[twibot20] p_final mean: {results['p_final'].mean():.4f}")
