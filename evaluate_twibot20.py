"""evaluate_twibot20.py - Zero-shot Reddit-transfer inference on TwiBot-20.

Runs trained_system_v12.joblib on TwiBot-20 test.json without retraining.
Adapts TwiBot-20 columns to the BotSim-24 pipeline schema and applies
Stage 1 ratio clamping via monkey-patch.

Canonical command (REPRO-01):
    python evaluate_twibot20.py <test_json> <model_joblib> [output_dir]

Defaults:
    test_json    = "test.json"
    model_joblib = "trained_system_v12.joblib"
    output_dir   = ".planning/phases/16-comparative-paper-outputs-and-reddit-cleanup/"
                   "artifacts"

If output_dir does not exist, it is created (os.makedirs(..., exist_ok=True)).

Artifacts written to output_dir (maintained v1.4 contract):
    results_twibot20_reddit_transfer.json
        JSON array of N records (one per TwiBot-20 test account). Each record
        has 11 keys: account_id, p1, n1, p2, n2, amr_used, p12, stage3_used,
        p3, n3, p_final.

    metrics_twibot20_reddit_transfer.json
        JSON object produced by evaluate.evaluate_s3() on the maintained static
        Reddit-transfer baseline run. Shape:
        Shape:
            {
              "overall":   {"f1", "auc", "precision", "recall"},
              "per_stage": {"p1": {...}, "p2": {...}, "p12": {...}, "p_final": {...}},
              "routing":   {"pct_stage1_exit", "pct_stage2_exit",
                            "pct_stage3_exit", "pct_amr_triggered"}
            }
Historical Phase 12 helper functions for static-vs-recalibrated comparison are
retained below for archival/reporting compatibility, but the maintained v1.4
execution path no longer writes those artifacts by default.
"""
from __future__ import annotations

import dataclasses
import json
import os
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
PHASE12_EVIDENCE_DIR = os.path.join(
    ".planning",
    "workstreams",
    "milestone",
    "phases",
    "12-fresh-transfer-evidence-and-paper-outputs",
    "artifacts",
)
PHASE16_REDDIT_ARTIFACT_DIR = os.path.join(
    ".planning",
    "phases",
    "16-comparative-paper-outputs-and-reddit-cleanup",
    "artifacts",
)
DEFAULT_RESULTS_FILENAME = "results_twibot20_reddit_transfer.json"
DEFAULT_METRICS_FILENAME = "metrics_twibot20_reddit_transfer.json"
EXPECTED_OUTPUT_FILES = (
    DEFAULT_RESULTS_FILENAME,
    DEFAULT_METRICS_FILENAME,
)
_TRANSFER_MATERIALITY = 0.01


def list_expected_output_files() -> list[str]:
    """Return the stable Phase 12 fresh-evidence artifact filenames."""
    return list(EXPECTED_OUTPUT_FILES)


def classify_transfer_result(delta_f1: float, materiality: float = _TRANSFER_MATERIALITY) -> str:
    """Classify recalibration impact using the primary F1 delta."""
    if delta_f1 > materiality:
        return "improved"
    if delta_f1 < -materiality:
        return "worsened"
    return "no_material_change"


def build_transfer_evidence_summary(comparison: dict) -> dict:
    """Derive a compact, stable evidence summary from a comparison artifact."""
    static_overall = comparison["conditions"]["static"]["overall"]
    recal_overall = comparison["conditions"]["recalibrated"]["overall"]
    delta_overall = comparison["delta_overall"]
    return {
        "path": comparison["path"],
        "model_path": comparison["model_path"],
        "threshold": comparison["threshold"],
        "window_size": comparison["window_size"],
        "static_overall": static_overall,
        "recalibrated_overall": recal_overall,
        "delta_overall": delta_overall,
        "interpretation": classify_transfer_result(delta_overall["f1"]),
        "interpretation_basis": "f1_delta",
    }


def _print_expected_outputs(output_dir: str) -> None:
    """Print the maintained Reddit-transfer artifact set for the chosen output dir."""
    print(f"[twibot20] Writing Reddit-transfer artifacts to {output_dir}")
    for name in EXPECTED_OUTPUT_FILES:
        print(f"[twibot20]   - {os.path.join(output_dir, name)}")



def run_inference(
    path: str,
    model_path: str = "trained_system_v12.joblib",
    online_calibration: bool = False,
    window_size: int = 100,
) -> pd.DataFrame:
    """Run zero-shot inference on TwiBot-20 test accounts.

    The maintained v1.4 Reddit-transfer path uses ``online_calibration=False``.
    The recalibration branch remains available only for historical comparison
    helpers and archived Phase 12 evidence reproduction.

    When ``online_calibration`` is True, accounts are processed in
    chunks of ``window_size``. After each completed window, the three novelty
    routing thresholds (``n1_max_for_exit``, ``n2_trigger``,
    ``novelty_force_stage3``) are recomputed as the 75th percentile of the
    accumulated ``n1`` and ``n2`` novelty scores from prior chunks
    (CAL-01, CAL-02). When fewer than ``window_size`` accounts have been
    processed, the original trained thresholds are kept (CAL-03 cold start).
    The original ``sys.th`` object is never mutated past this function's
    return - a local copy is used internally and restored on exit (D-07).

    When ``online_calibration`` is False, the function calls ``predict_system``
    exactly once with the unmodified ``sys.th`` (pre-Phase-9 behavior),
    enabling Phase 10's before/after comparison.
    """
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
        if not online_calibration:
            results = predict_system(
                sys_loaded, df, edges_df, nodes_total=len(accounts_df)
            )
        else:
            original_th = sys_loaded.th
            current_th = dataclasses.replace(original_th)
            novelty_buffer: list[float] = []
            chunk_results: list[pd.DataFrame] = []
            try:
                for start in range(0, len(df), window_size):
                    end = start + window_size
                    chunk_df = df.iloc[start:end].reset_index(drop=True)
                    sys_loaded.th = current_th
                    chunk_out = predict_system(
                        sys_loaded, chunk_df, edges_df, nodes_total=len(accounts_df)
                    )
                    chunk_results.append(chunk_out)
                    novelty_buffer.extend(chunk_out["n1"].tolist())
                    novelty_buffer.extend(chunk_out["n2"].tolist())
                    full_window_complete = (end <= len(df)) and (len(novelty_buffer) >= 2 * window_size)
                    if full_window_complete:
                        p = float(np.percentile(novelty_buffer, 75))
                        current_th = dataclasses.replace(
                            current_th,
                            n1_max_for_exit=p,
                            n2_trigger=p,
                            novelty_force_stage3=p,
                        )
                        print(
                            f"[cal] window updated thresholds: "
                            f"n1_max={p:.3f} n2_trigger={p:.3f} "
                            f"novelty_force_stage3={p:.3f}"
                        )
                results = pd.concat(chunk_results, ignore_index=True)
            finally:
                sys_loaded.th = original_th
    finally:
        bp.extract_stage1_matrix = _orig_extract_stage1_matrix

    return results


def evaluate_twibot20(
    path: str = "test.json",
    model_path: str = "trained_system_v12.joblib",
    threshold: float = 0.5,
    online_calibration: bool = False,
    window_size: int = 100,
) -> dict:
    """Run zero-shot inference on TwiBot-20 and evaluate against ground truth."""
    results = run_inference(
        path,
        model_path,
        online_calibration=online_calibration,
        window_size=window_size,
    )
    accounts_df = load_accounts(path)
    y_true = accounts_df["label"].to_numpy()
    metrics = evaluate_s3(results, y_true, threshold)
    return metrics


def compare_twibot20_conditions(
    path: str = "test.json",
    model_path: str = "trained_system_v12.joblib",
    threshold: float = 0.5,
    window_size: int = 100,
) -> dict:
    """Compare static vs online-recalibrated TwiBot-20 evaluation metrics."""
    static_metrics = evaluate_twibot20(
        path,
        model_path,
        threshold=threshold,
        online_calibration=False,
        window_size=window_size,
    )
    recalibrated_metrics = evaluate_twibot20(
        path,
        model_path,
        threshold=threshold,
        online_calibration=True,
        window_size=window_size,
    )

    return build_comparison_artifact(
        path=path,
        model_path=model_path,
        threshold=threshold,
        window_size=window_size,
        static_metrics=static_metrics,
        recalibrated_metrics=recalibrated_metrics,
    )


def build_comparison_artifact(
    *,
    path: str,
    model_path: str,
    threshold: float,
    window_size: int,
    static_metrics: dict,
    recalibrated_metrics: dict,
) -> dict:
    """Build a stable static-vs-recalibrated comparison payload."""
    static_overall = static_metrics["overall"]
    recal_overall = recalibrated_metrics["overall"]
    deltas = {
        "f1": recal_overall["f1"] - static_overall["f1"],
        "auc": recal_overall["auc"] - static_overall["auc"],
        "precision": recal_overall["precision"] - static_overall["precision"],
        "recall": recal_overall["recall"] - static_overall["recall"],
    }
    return {
        "path": path,
        "model_path": model_path,
        "threshold": threshold,
        "window_size": window_size,
        "conditions": {
            "static": static_metrics,
            "recalibrated": recalibrated_metrics,
        },
        "delta_overall": deltas,
    }


def _print_comparison_summary(comparison: dict) -> None:
    """Print a compact before/after TwiBot comparison block."""
    static = comparison["conditions"]["static"]["overall"]
    recal = comparison["conditions"]["recalibrated"]["overall"]
    delta = comparison["delta_overall"]
    print("\n[twibot20] Comparison summary")
    print("metric        static    recalibrated    delta")
    for metric in ("f1", "auc", "precision", "recall"):
        print(
            f"{metric:<12}{static[metric]:>7.4f}    "
            f"{recal[metric]:>12.4f}    {delta[metric]:>+7.4f}"
        )


def _save_json(payload: dict | list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


if __name__ == "__main__":
    data_path = sys.argv[1] if len(sys.argv) > 1 else "test.json"
    model_path = sys.argv[2] if len(sys.argv) > 2 else "trained_system_v12.joblib"
    output_dir = sys.argv[3] if len(sys.argv) > 3 else PHASE16_REDDIT_ARTIFACT_DIR
    os.makedirs(output_dir, exist_ok=True)
    _print_expected_outputs(output_dir)

    results = run_inference(data_path, model_path, online_calibration=False)

    out_path = os.path.join(output_dir, DEFAULT_RESULTS_FILENAME)
    results.to_json(out_path, orient="records", indent=2)
    print(f"[twibot20] Saved {len(results)} inference results to {out_path}")

    accounts_df = load_accounts(data_path)
    y_true = accounts_df["label"].to_numpy()
    metrics = evaluate_s3(results, y_true)

    metrics_path = os.path.join(output_dir, DEFAULT_METRICS_FILENAME)
    _save_json(metrics, metrics_path)
    print(f"\n[twibot20] Saved evaluation metrics to {metrics_path}")

    bots = int((results["p_final"] >= 0.5).sum())
    print(f"[twibot20] Accounts: {len(results)} | Predicted bots (p_final>=0.5): {bots}")
    print(f"[twibot20] Stage 3 used: {results['stage3_used'].mean():.3f}")
    print(f"[twibot20] AMR used:     {results['amr_used'].mean():.3f}")
    print(f"[twibot20] p_final mean: {results['p_final'].mean():.4f}")
