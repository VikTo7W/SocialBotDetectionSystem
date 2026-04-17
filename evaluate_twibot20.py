"""
evaluate_twibot20.py - Zero-shot inference on TwiBot-20 test accounts.

Runs trained_system_v12.joblib on TwiBot-20 test.json without retraining.
Adapts TwiBot-20 columns to the BotSim-24 pipeline schema and applies
Stage 1 ratio clamping via monkey-patch.

Phase 10 imports run_inference() directly. The __main__ block also saves
results_twibot20.json for manual inspection.
"""
from __future__ import annotations

import json
import sys

import joblib
import numpy as np
import pandas as pd

import botdetector_pipeline as bp
from botdetector_pipeline import TrainedSystem, predict_system
from evaluate import evaluate_s3
from features_stage1 import extract_stage1_matrix as _orig_extract_stage1_matrix
from twibot20_io import _detect_encoding, build_edges, load_accounts, parse_tweet_types, validate

# FEAT-03 review (Phase 8): _RATIO_CAP retained at 1000.0.
# TwiBot-20 tweet counts are bounded by the Twitter 3200-tweet API limit.
# Ratio columns (post_c1/c2/ct/sr, indices 6-9) can blow up for accounts
# with near-zero denominators. Empirical 95p/99p are printed at adapter time
# (see run_inference logging). 1000.0 remains a conservative cap.
_RATIO_CAP = 1000.0



def run_inference(
    path: str,
    model_path: str = "trained_system_v12.joblib",
) -> pd.DataFrame:
    """Run zero-shot inference on TwiBot-20 test accounts."""
    accounts_df = load_accounts(path)
    edges_df = build_edges(accounts_df, path)
    validate(accounts_df, edges_df)

    sys_loaded: TrainedSystem = joblib.load(model_path)

    with open(path, "r", encoding=_detect_encoding(path)) as f:
        raw = json.load(f)

    df = accounts_df.copy()
    df["account_id"] = [r["ID"] for r in raw]
    df["username"] = df["screen_name"]

    # Revised transfer adapter:
    # - submission_num <- total tweet volume
    # - comment_num_1  <- authored tweets (non-RT / non-MT)
    # - comment_num_2  <- modified tweets (MT)
    # - subreddit_list <- TwiBot topical domains
    tweet_stats = [parse_tweet_types(msgs) for msgs in df["messages"]]
    df["submission_num"] = [
        float(s["original_count"] + s["mt_count"] + s["rt_count"])
        for s in tweet_stats
    ]
    df["comment_num_1"] = [float(s["original_count"]) for s in tweet_stats]
    df["comment_num_2"] = [float(s["mt_count"]) for s in tweet_stats]
    df["subreddit_list"] = df["domain_list"].tolist()

    n_accts = len(tweet_stats)
    total_rt = sum(s["rt_count"] for s in tweet_stats)
    total_mt = sum(s["mt_count"] for s in tweet_stats)
    total_orig = sum(s["original_count"] for s in tweet_stats)
    total_domains = sum(len(domains) for domains in df["subreddit_list"])
    zero_tweet_frac = (
        sum(
            1
            for s in tweet_stats
            if s["rt_count"] + s["mt_count"] + s["original_count"] == 0
        ) / n_accts
        if n_accts > 0
        else 0.0
    )
    timestamp_missing_frac = (
        sum(
            1
            for messages in df["messages"]
            if len(messages) > 0 and all(m.get("ts") is None for m in messages)
        ) / n_accts
        if n_accts > 0
        else 0.0
    )
    domain_mean = (total_domains / n_accts) if n_accts > 0 else 0.0
    print(f"[twibot20] tweet distribution: RT={total_rt}, MT={total_mt}, original={total_orig}")
    print(f"[twibot20] zero-tweet fraction: {zero_tweet_frac:.3f}")
    print(f"[twibot20] domain breadth: total={total_domains}, mean={domain_mean:.2f}")
    print(f"[twibot20] timestamp-missing fraction: {timestamp_missing_frac:.3f}")

    eps = 1e-6
    _post_num = np.asarray(df["submission_num"], dtype=np.float64)
    _c1 = np.asarray(df["comment_num_1"], dtype=np.float64)
    _c2 = np.asarray(df["comment_num_2"], dtype=np.float64)
    _ct = _c1 + _c2
    _sr = np.asarray(
        [len(x) if isinstance(x, list) else 0 for x in df["subreddit_list"]],
        dtype=np.float64,
    )
    _ratios = np.stack(
        [
            _post_num / (_c1 + eps),
            _post_num / (_c2 + eps),
            _post_num / (_ct + eps),
            _post_num / (_sr + eps),
        ],
        axis=1,
    )
    _ratios = np.nan_to_num(_ratios, nan=0.0, posinf=0.0, neginf=0.0)
    if _ratios.size > 0:
        _p95 = np.percentile(_ratios, 95)
        _p99 = np.percentile(_ratios, 99)
        print(f"[twibot20] ratio distribution (pre-cap) p95={_p95:.2f} p99={_p99:.2f}")

    def _clamped_s1(df_inner, *args, **kwargs):
        X = _orig_extract_stage1_matrix(df_inner)
        X[:, 6:10] = np.clip(X[:, 6:10], 0.0, _RATIO_CAP)
        return X

    bp.extract_stage1_matrix = _clamped_s1
    try:
        results = predict_system(
            sys_loaded, df, edges_df, nodes_total=len(accounts_df)
        )
    finally:
        bp.extract_stage1_matrix = _orig_extract_stage1_matrix

    return results


def evaluate_twibot20(
    path: str = "test.json",
    model_path: str = "trained_system_v12.joblib",
    threshold: float = 0.5,
) -> dict:
    """Run zero-shot inference on TwiBot-20 and evaluate against ground truth."""
    results = run_inference(path, model_path)
    accounts_df = load_accounts(path)
    y_true = accounts_df["label"].to_numpy()
    metrics = evaluate_s3(results, y_true, threshold)
    return metrics


if __name__ == "__main__":
    data_path = sys.argv[1] if len(sys.argv) > 1 else "test.json"
    model_path = sys.argv[2] if len(sys.argv) > 2 else "trained_system_v12.joblib"

    results = run_inference(data_path, model_path)

    out_path = "results_twibot20.json"
    results.to_json(out_path, orient="records", indent=2)
    print(f"[twibot20] Saved {len(results)} inference results to {out_path}")

    accounts_df = load_accounts(data_path)
    y_true = accounts_df["label"].to_numpy()
    metrics = evaluate_s3(results, y_true)

    metrics_path = "metrics_twibot20.json"
    with open(metrics_path, "w") as f:
        json.dump(metrics, f, indent=2)
    print(f"\n[twibot20] Saved evaluation metrics to {metrics_path}")

    bots = int((results["p_final"] >= 0.5).sum())
    print(f"[twibot20] Accounts: {len(results)} | Predicted bots (p_final>=0.5): {bots}")
    print(f"[twibot20] Stage 3 used: {results['stage3_used'].mean():.3f}")
    print(f"[twibot20] AMR used:     {results['amr_used'].mean():.3f}")
    print(f"[twibot20] p_final mean: {results['p_final'].mean():.4f}")
