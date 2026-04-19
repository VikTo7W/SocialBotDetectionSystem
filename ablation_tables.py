"""
ablation_tables.py — Generate all paper ablation tables.

Produces:
  Table 1: Leakage audit — v1.0 (leaky) vs v1.1 (clean) S3 metrics
  Table 2: Stage contribution — p1, p12, p_final cascade stages
  Table 3: Routing efficiency — stage exit percentages and AMR trigger rate
  Table 4: Stage 1 feature group ablation — baseline vs masked variants
  Table 5: Cross-dataset comparison — BotSim-24 plus Reddit-transfer vs TwiBot-native
  Table 5 (stage2b): Stage 2b variant comparison — AMR vs LSTM overall metrics
  Table 6 (stage2b): Stage 2b routing comparison — AMR vs LSTM routing behavior

Usage:
    python ablation_tables.py

Requires:
    - trained_system_v12.joblib (v1.2 trained system)
    - .planning/workstreams/stage2b-lstm-version/phases/10-evaluation-and-baseline-comparison/10-real-run-variant-comparison.json
    - results_v10.json (v1.0 S3 metrics from git worktree retrain)
    - Users.csv, user_post_comment.json, edge_index.pt, edge_type.pt, edge_weight.pt
    - Phase 20 maintained paper outputs (run eval_reddit_twibot_transfer.py and eval_twibot_native.py first)
"""

import json
import os
import warnings

import joblib
import numpy as np
import pandas as pd
import torch
from sklearn.model_selection import train_test_split

from data_io import load_users_csv, load_user_post_comment_json, build_account_table
from cascade_pipeline import predict_system, Stage1Extractor
from evaluate import evaluate_s3
from train_botsim import filter_edges_for_split

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Feature group column indices for Stage 1 masking (Table 4)
# Column order from extract_stage1_matrix:
#   0: name_len, 1: post_num, 2: c1, 3: c2, 4: c_total,
#   5: sr_num, 6: post_c1, 7: post_c2, 8: post_ct, 9: post_sr
# ---------------------------------------------------------------------------

FEATURE_GROUPS = {
    "username_length":     [0],
    "post_count":          [1],
    "comment_counts":      [2, 3, 4],
    "subreddit_breadth":   [5],
    "post_comment_ratios": [6, 7, 8, 9],
}

PHASE16_ARTIFACT_DIR = os.path.join(
    ".planning",
    "phases",
    "16-comparative-paper-outputs-and-reddit-cleanup",
    "artifacts",
)
DEFAULT_REDDIT_TRANSFER_METRICS_PATH = os.path.join(
    PHASE16_ARTIFACT_DIR,
    "metrics_twibot20_reddit_transfer.json",
)
DEFAULT_NATIVE_METRICS_PATH = os.path.join(
    ".planning",
    "phases",
    "15-twibot-cascade-training-and-evaluation",
    "artifacts",
    "metrics_twibot20_native.json",
)
DEFAULT_COMPARISON_PATH = os.path.join(
    PHASE16_ARTIFACT_DIR,
    "metrics_twibot20_reddit_vs_native.json",
)


# ---------------------------------------------------------------------------
# Table builders
# ---------------------------------------------------------------------------

def build_table1(v10_metrics: dict, v12_overall: dict) -> pd.DataFrame:
    """
    Table 1 — Leakage Audit: side-by-side comparison of v1.0 and v1.1 S3 metrics.

    Args:
        v10_metrics:  Dict with keys auc, f1, precision, recall (from results_v10.json).
        v12_overall:  Overall metrics dict from evaluate_s3()["overall"].

    Returns:
        DataFrame with columns ["Metric", "v1.0 (leaky)", "v1.1 (clean)"] and 4 rows.
    """
    return pd.DataFrame({
        "Metric": ["F1", "AUC-ROC", "Precision", "Recall"],
        "v1.0 (leaky)": [
            v10_metrics["f1"],
            v10_metrics["auc"],
            v10_metrics["precision"],
            v10_metrics["recall"],
        ],
        "v1.1 (clean)": [
            v12_overall["f1"],
            v12_overall["auc"],
            v12_overall["precision"],
            v12_overall["recall"],
        ],
    })


def build_table2(per_stage: dict) -> pd.DataFrame:
    """
    Table 2 — Stage Contribution: p1, p12, p_final rows (p2 excluded — not a cascade stage).

    Args:
        per_stage:  Dict from evaluate_s3()["per_stage"] with keys p1, p2, p12, p_final.

    Returns:
        DataFrame with columns ["Stage", "F1", "AUC-ROC", "Precision", "Recall"] and 3 rows.
    """
    rows = []
    for stage_key, label in [
        ("p1",      "Stage 1 only"),
        ("p12",     "Stage 1+2"),
        ("p_final", "Full cascade"),
    ]:
        m = per_stage[stage_key]
        rows.append({
            "Stage":     label,
            "F1":        m["f1"],
            "AUC-ROC":   m["auc"],
            "Precision": m["precision"],
            "Recall":    m["recall"],
        })
    return pd.DataFrame(rows)


def build_table3(routing: dict) -> pd.DataFrame:
    """
    Table 3 — Routing Efficiency: stage exit percentages and AMR trigger rate.

    Args:
        routing:  Dict from evaluate_s3()["routing"].

    Returns:
        DataFrame with columns ["Exit Point", "% Accounts"] and 4 rows.
        Note: first three rows sum to 100.0 (exhaustive partition of accounts).
    """
    return pd.DataFrame([
        {"Exit Point": "Stage 1 exit",     "% Accounts": routing["pct_stage1_exit"]},
        {"Exit Point": "Stage 2 exit",     "% Accounts": routing["pct_stage2_exit"]},
        {"Exit Point": "Stage 3 exit",     "% Accounts": routing["pct_stage3_exit"]},
        {"Exit Point": "AMR trigger rate", "% Accounts": routing["pct_amr_triggered"]},
    ])


def build_table4(group_metrics: dict) -> pd.DataFrame:
    """
    Table 4 — Stage 1 Feature Group Ablation: baseline then 5 masked groups.

    Args:
        group_metrics:  Dict mapping group name to metrics dict (f1, auc, precision, recall).
                        Must contain: all_features, username_length, post_count,
                        comment_counts, subreddit_breadth, post_comment_ratios.

    Returns:
        DataFrame with columns ["Group", "F1", "AUC-ROC", "Precision", "Recall"] and 6 rows.
        First row is the baseline (all_features).
    """
    ORDER = [
        "all_features",
        "username_length",
        "post_count",
        "comment_counts",
        "subreddit_breadth",
        "post_comment_ratios",
    ]
    rows = []
    for group in ORDER:
        m = group_metrics[group]
        rows.append({
            "Group":     group,
            "F1":        m["f1"],
            "AUC-ROC":   m["auc"],
            "Precision": m["precision"],
            "Recall":    m["recall"],
        })
    return pd.DataFrame(rows)


def generate_cross_dataset_table(
    botsim24_metrics: dict,
    reddit_transfer_metrics: dict,
    twibot20_native_metrics: dict,
) -> pd.DataFrame:
    """
    Table 5 — Cross-Dataset Comparison: BotSim-24 vs Reddit transfer vs TwiBot native.

    Both inputs are full evaluate_s3() return dicts with keys "overall", "per_stage", "routing".
    This function reads metrics["overall"] for the table rows (per D-06, D-07).

    Args:
        botsim24_metrics: evaluate_s3() return dict for BotSim-24 S3 test set.
        reddit_transfer_metrics: evaluate_s3() return dict for the Reddit-trained zero-shot TwiBot run.
        twibot20_native_metrics: evaluate_s3() return dict for the TwiBot-native supervised run.

    Returns:
        DataFrame with BotSim-24, Reddit-transfer, and TwiBot-native columns.
    """
    bs = botsim24_metrics["overall"]
    reddit_transfer = reddit_transfer_metrics["overall"]
    native = twibot20_native_metrics["overall"]
    return pd.DataFrame({
        "Metric": ["F1", "AUC-ROC", "Precision", "Recall"],
        "BotSim-24 (Reddit, in-dist.)": [bs["f1"], bs["auc"], bs["precision"], bs["recall"]],
        "TwiBot-20 (Reddit transfer)": [
            reddit_transfer["f1"],
            reddit_transfer["auc"],
            reddit_transfer["precision"],
            reddit_transfer["recall"],
        ],
        "TwiBot-20 (TwiBot-native)": [
            native["f1"],
            native["auc"],
            native["precision"],
            native["recall"],
        ],
    })


def load_twibot20_comparison(path: str) -> dict:
    """Load the persisted Phase 10 TwiBot comparison artifact."""
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def classify_transfer_result(delta_f1: float, materiality: float = 0.01) -> str:
    """Classify whether the TwiBot-native baseline materially improves over Reddit transfer."""
    if delta_f1 > materiality:
        return "improved"
    if delta_f1 < -materiality:
        return "worsened"
    return "no_material_change"


def build_reddit_vs_native_comparison_artifact(
    *,
    reddit_transfer_metrics: dict,
    twibot20_native_metrics: dict,
    reddit_metrics_path: str,
    native_metrics_path: str,
    reddit_model_path: str = "trained_system_v12.joblib",
    native_model_path: str = "trained_system_twibot20.joblib",
    threshold: float = 0.5,
) -> dict:
    """Build the stable v1.4 Reddit-transfer vs TwiBot-native comparison payload."""
    reddit_overall = reddit_transfer_metrics["overall"]
    native_overall = twibot20_native_metrics["overall"]
    return {
        "comparison_type": "reddit_transfer_vs_twibot_native",
        "threshold": threshold,
        "sources": {
            "reddit_transfer_metrics_path": reddit_metrics_path,
            "twibot_native_metrics_path": native_metrics_path,
            "reddit_model_path": reddit_model_path,
            "twibot_native_model_path": native_model_path,
        },
        "conditions": {
            "reddit_transfer": reddit_transfer_metrics,
            "twibot_native": twibot20_native_metrics,
        },
        "delta_overall": {
            "f1": native_overall["f1"] - reddit_overall["f1"],
            "auc": native_overall["auc"] - reddit_overall["auc"],
            "precision": native_overall["precision"] - reddit_overall["precision"],
            "recall": native_overall["recall"] - reddit_overall["recall"],
        },
    }


def build_transfer_result_interpretation(comparison: dict) -> str:
    """Build a concise milestone-facing interpretation from the v1.4 comparison metrics."""
    delta = comparison["delta_overall"]
    verdict = classify_transfer_result(delta["f1"])
    reddit_transfer = comparison["conditions"]["reddit_transfer"]["overall"]
    native = comparison["conditions"]["twibot_native"]["overall"]
    return (
        f"Comparison result: {verdict}.\n"
        f"Primary basis: F1 delta = {delta['f1']:+.4f} "
        f"(Reddit transfer {reddit_transfer['f1']:.4f} -> "
        f"TwiBot-native {native['f1']:.4f}).\n"
        f"AUC delta = {delta['auc']:+.4f}, "
        f"precision delta = {delta['precision']:+.4f}, "
        f"recall delta = {delta['recall']:+.4f}.\n"
        f"Source artifact: {comparison.get('comparison_type', 'unknown')}."
    )


def write_transfer_result_interpretation(comparison: dict, path: str) -> None:
    """Persist the transfer-result interpretation alongside the paper outputs."""
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    text = build_transfer_result_interpretation(comparison)
    with open(path, "w", encoding="utf-8") as f:
        f.write(text + "\n")


def _load_metrics(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def _load_or_build_phase16_comparison(
    comparison_path: str,
    reddit_metrics_path: str,
    native_metrics_path: str,
) -> dict | None:
    if os.path.exists(comparison_path):
        return load_twibot20_comparison(comparison_path)
    if not (os.path.exists(reddit_metrics_path) and os.path.exists(native_metrics_path)):
        return None

    comparison = build_reddit_vs_native_comparison_artifact(
        reddit_transfer_metrics=_load_metrics(reddit_metrics_path),
        twibot20_native_metrics=_load_metrics(native_metrics_path),
        reddit_metrics_path=reddit_metrics_path,
        native_metrics_path=native_metrics_path,
    )
    os.makedirs(os.path.dirname(comparison_path), exist_ok=True)
    with open(comparison_path, "w", encoding="utf-8") as f:
        json.dump(comparison, f, indent=2)
    return comparison


def build_table5(variant_comparison: dict) -> pd.DataFrame:
    """Stage 2b variant comparison on overall metrics (supplementary)."""
    rows = []
    for variant in ("amr", "lstm"):
        overall = variant_comparison["variants"][variant]["overall"]
        rows.append(
            {
                "Variant": variant.upper(),
                "F1": overall["f1"],
                "AUC-ROC": overall["auc"],
                "Precision": overall["precision"],
                "Recall": overall["recall"],
            }
        )
    return pd.DataFrame(rows)


def build_table6(variant_comparison: dict) -> pd.DataFrame:
    """Stage 2b variant routing comparison (supplementary)."""
    rows = []
    for variant in ("amr", "lstm"):
        routing = variant_comparison["variants"][variant]["routing"]
        rows.append(
            {
                "Variant": variant.upper(),
                "Stage 1 Exit %": routing["pct_stage1_exit"],
                "Stage 2 Exit %": routing["pct_stage2_exit"],
                "Stage 3 Exit %": routing["pct_stage3_exit"],
                "Stage 2b Route %": routing["pct_amr_triggered"],
            }
        )
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# LaTeX export
# ---------------------------------------------------------------------------

def save_latex(df: pd.DataFrame, path: str) -> None:
    """
    Write a DataFrame as a LaTeX tabular to a file.

    Args:
        df:    DataFrame to export.
        path:  Output file path. Parent directories are created if needed.
    """
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)
    latex = df.to_latex(index=False, escape=False, float_format="%.4f")
    with open(path, "w") as f:
        f.write(latex)


# ---------------------------------------------------------------------------
# Masked predict helper for Table 4
# ---------------------------------------------------------------------------

def masked_predict(sys_obj, S3, edges_S3, nodes_total, mask_cols):
    """
    Run predict_system with specific Stage 1 feature columns zeroed at inference time.

    Monkey-patches `botdetector_pipeline.extract_stage1_matrix` so the shared
    pipeline sees a masked Stage 1 feature matrix at inference time.

    Args:
        sys_obj:     Trained system (TrainedSystem from botdetector_pipeline).
        S3:          Test split DataFrame.
        edges_S3:    Edge DataFrame filtered for S3 node_idx set.
        nodes_total: Total number of nodes in the full graph.
        mask_cols:   List of column indices to zero in the Stage 1 feature matrix.

    Returns:
        DataFrame returned by predict_system() with masked features.
    """
    import cascade_pipeline as bp

    def _masked_extract(df):
        X = Stage1Extractor("botsim").extract(df)
        X = X.copy()
        X[:, mask_cols] = 0.0
        return X

    original = bp.extract_stage1_matrix
    bp.extract_stage1_matrix = _masked_extract
    try:
        out = predict_system(sys_obj, df=S3, edges_df=edges_S3, nodes_total=nodes_total)
    finally:
        bp.extract_stage1_matrix = original
    return out


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def main():
    SEED = 42
    variant_artifact = (
        ".planning/workstreams/stage2b-lstm-version/phases/"
        "10-evaluation-and-baseline-comparison/10-real-run-variant-comparison.json"
    )

    # 1. Load data and reconstruct S3 split (same maintained BotSim split as train_botsim.py)
    users = load_users_csv("Users.csv")
    users["node_idx"] = np.arange(len(users), dtype=np.int32)
    users["user_id"] = users["user_id"].astype(str)
    upc = load_user_post_comment_json("user_post_comment.json")
    accounts = build_account_table(users, upc)
    assert "character_setting" not in accounts.columns, (
        "character_setting must not appear in account table -- it is a target leak"
    )
    accounts["account_id"] = accounts["account_id"].astype(str)
    accounts = accounts.merge(
        users[["user_id", "node_idx"]],
        left_on="account_id",
        right_on="user_id",
        how="left",
    )
    accounts.drop(columns=["user_id"], inplace=True)
    accounts["node_idx"] = accounts["node_idx"].astype(np.int32)
    accounts = accounts.sample(frac=1.0, random_state=SEED).reset_index(drop=True)

    _S_temp, S3 = train_test_split(
        accounts,
        test_size=0.15,
        stratify=accounts["label"],
        shuffle=True,
        random_state=SEED,
    )

    # Edge loading
    edge_index = torch.load("edge_index.pt", map_location="cpu").numpy()
    edge_type = torch.load("edge_type.pt", map_location="cpu").numpy()
    edge_w = (
        torch.load("edge_weight.pt", map_location="cpu")
        .numpy()
        .reshape(-1)
        .astype(np.float32)
    )
    edges_df = pd.DataFrame({
        "src":    edge_index[:, 0].astype(np.int32),
        "dst":    edge_index[:, 1].astype(np.int32),
        "etype":  edge_type.astype(np.int8),
        "weight": edge_w,
    })
    edges_df["weight"] = np.log1p(edges_df["weight"])
    edges_S3 = filter_edges_for_split(edges_df, S3["node_idx"].to_numpy())
    nodes_total = len(users)

    # 2. Load v1.2 system and run baseline evaluation
    print("Loading trained_system_v12.joblib...")
    sys_v12 = joblib.load("trained_system_v12.joblib")
    print("Running baseline predict_system on S3...")
    out = predict_system(sys_v12, df=S3, edges_df=edges_S3, nodes_total=nodes_total)
    y_true = S3["label"].to_numpy()
    report = evaluate_s3(out, y_true)

    # 3. Table 1 — Leakage Audit (v1.0 vs v1.1)
    with open("results_v10.json") as f:
        v10_metrics = json.load(f)
    df_t1 = build_table1(v10_metrics, report["overall"])
    print("\n=== Table 1: Leakage Audit ===")
    print(df_t1.to_string(index=False))

    # 4. Table 2 — Stage Contribution
    df_t2 = build_table2(report["per_stage"])
    print("\n=== Table 2: Stage Contribution ===")
    print(df_t2.to_string(index=False))

    # 5. Table 3 — Routing Efficiency
    df_t3 = build_table3(report["routing"])
    print("\n=== Table 3: Routing Efficiency ===")
    print(df_t3.to_string(index=False))

    # 6. Table 4 — Stage 1 Feature Group Ablation
    print("\n=== Table 4: Feature Group Ablation ===")
    group_metrics = {}
    # Baseline (no masking)
    group_metrics["all_features"] = report["overall"]
    # Masked variants
    for group_name, cols in FEATURE_GROUPS.items():
        print(f"  Running masked predict: zeroing {group_name} (cols {cols})...")
        masked_out = masked_predict(sys_v12, S3, edges_S3, nodes_total, cols)
        masked_report = evaluate_s3(masked_out, y_true)
        group_metrics[group_name] = masked_report["overall"]
    df_t4 = build_table4(group_metrics)
    print(df_t4.to_string(index=False))

    # 7. Export Tables 1–4 to LaTeX
    os.makedirs("tables", exist_ok=True)
    save_latex(df_t1, "tables/table1_leakage_audit.tex")
    save_latex(df_t2, "tables/table2_stage_contribution.tex")
    save_latex(df_t3, "tables/table3_routing_efficiency.tex")
    save_latex(df_t4, "tables/table4_feature_group_ablation.tex")

    # 8. Table 5 — Cross-Dataset Comparison (Phase 16)
    metrics_twibot20_path = os.environ.get(
        "TWIBOT_COMPARISON_PATH",
        DEFAULT_COMPARISON_PATH,
    )
    reddit_metrics_path = os.environ.get(
        "TWIBOT_REDDIT_METRICS_PATH",
        DEFAULT_REDDIT_TRANSFER_METRICS_PATH,
    )
    native_metrics_path = os.environ.get(
        "TWIBOT_NATIVE_METRICS_PATH",
        DEFAULT_NATIVE_METRICS_PATH,
    )
    table5_output_path = os.environ.get(
        "TABLE5_OUTPUT_PATH", "tables/table5_cross_dataset.tex"
    )
    interpretation_output_path = os.environ.get(
        "TABLE5_INTERPRETATION_PATH", "tables/table5_transfer_interpretation.txt"
    )
    print(f"[table5] Comparison artifact path: {metrics_twibot20_path}")
    twibot20_comparison = _load_or_build_phase16_comparison(
        metrics_twibot20_path,
        reddit_metrics_path,
        native_metrics_path,
    )
    if twibot20_comparison is not None:
        df_t5 = generate_cross_dataset_table(
            report,
            twibot20_comparison["conditions"]["reddit_transfer"],
            twibot20_comparison["conditions"]["twibot_native"],
        )
        print("\n=== Table 5: Cross-Dataset Comparison ===")
        print(df_t5.to_string(index=False))
        save_latex(df_t5, table5_output_path)
        write_transfer_result_interpretation(
            twibot20_comparison, interpretation_output_path
        )
        print(f"[table5] Saved LaTeX to {table5_output_path}")
        print(f"[table5] Saved interpretation to {interpretation_output_path}")
        print("\nAll 5 tables exported to tables/*.tex")
    else:
        print(f"\n[SKIP] Table 5: {metrics_twibot20_path} not found.")
        print(
            "Run 'python eval_reddit_twibot_transfer.py' and "
            "'python eval_twibot_native.py' first to generate Reddit-transfer "
            "and TwiBot-native metrics."
        )
        print("\n4 tables exported to tables/*.tex (Table 5 skipped)")

    # 9. Stage 2b supplementary tables (optional — requires variant comparison artifact)
    if os.path.exists(variant_artifact):
        with open(variant_artifact, encoding="utf-8") as f:
            variant_comparison = json.load(f)
        df_s2b_5 = build_table5(variant_comparison)
        df_s2b_6 = build_table6(variant_comparison)
        print("\n=== Stage 2b Variant Comparison ===")
        print(df_s2b_5.to_string(index=False))
        print("\n=== Stage 2b Routing Comparison ===")
        print(df_s2b_6.to_string(index=False))
        save_latex(df_s2b_5, "tables/table5_stage2b_variant_comparison.tex")
        save_latex(df_s2b_6, "tables/table6_stage2b_routing_comparison.tex")


if __name__ == "__main__":
    main()
