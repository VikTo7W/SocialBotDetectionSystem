from __future__ import annotations

import json
import os
import sys

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay

from cascade_pipeline import CascadePipeline
from evaluate import evaluate_s3
from train_botsim import DEFAULT_BOTSIM_MODEL_PATH
from data_io import build_edges, load_accounts, parse_tweet_types

DEFAULT_OUTPUT_DIR = "paper_outputs"
DEFAULT_TEST_JSON_PATH = "test.json"


def _save_json(payload: dict | list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def _write_confusion_matrix(results, y_true, threshold, output_path, title):
    y_pred = (results["p_final"].to_numpy() >= threshold).astype(int)
    disp = ConfusionMatrixDisplay.from_predictions(
        y_true,
        y_pred,
        display_labels=["human", "bot"],
        colorbar=False,
        cmap="Blues",
    )
    disp.ax_.set_title(title)
    disp.figure_.tight_layout()
    disp.figure_.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(disp.figure_)


def _apply_transfer_adapter(accounts_df: pd.DataFrame) -> pd.DataFrame:
    df = accounts_df.copy()
    tweet_stats = [parse_tweet_types(msgs) for msgs in df["messages"]]
    df["submission_num"] = [float(s["original_count"] + s["mt_count"] + s["rt_count"]) for s in tweet_stats]
    df["comment_num_1"] = [float(s["original_count"]) for s in tweet_stats]
    df["comment_num_2"] = [float(s["mt_count"]) for s in tweet_stats]
    df["subreddit_list"] = df["domain_list"].tolist()
    if "username" not in df.columns and "screen_name" in df.columns:
        df["username"] = df["screen_name"]
    if "account_id" not in df.columns:
        if "node_idx" in df.columns:
            df["account_id"] = df["node_idx"].astype(str)
        else:
            df["account_id"] = df.index.astype(str)
    return df


def run_inference_transfer(
    path: str,
    model_path: str = DEFAULT_BOTSIM_MODEL_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    accounts_df = load_accounts(path)
    adapted = _apply_transfer_adapter(accounts_df)
    edges_df = build_edges(adapted, path)
    system = joblib.load(model_path)
    pipeline = CascadePipeline("botsim", cfg=system.cfg, embedder=system.embedder)
    results = pipeline.predict(system, df=adapted, edges_df=edges_df, nodes_total=len(adapted))
    return results, adapted


def evaluate_reddit_twibot_transfer(
    path: str = DEFAULT_TEST_JSON_PATH,
    model_path: str = DEFAULT_BOTSIM_MODEL_PATH,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    threshold: float = 0.5,
) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    results, adapted = run_inference_transfer(path, model_path=model_path)
    y_true = adapted["label"].to_numpy()
    metrics = evaluate_s3(results, y_true, threshold=threshold, verbose=True)

    metrics_path = os.path.join(output_dir, "metrics_reddit_transfer.json")
    cm_path = os.path.join(output_dir, "confusion_matrix_reddit_transfer.png")

    _save_json(metrics, metrics_path)
    _write_confusion_matrix(
        results,
        y_true,
        threshold,
        cm_path,
        title="Reddit-transfer (TwiBot-20) confusion matrix",
    )

    return {
        "metrics": metrics,
        "paths": {
            "metrics": metrics_path,
            "confusion_matrix": cm_path,
            "model": model_path,
        },
    }


if __name__ == "__main__":
    data_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_TEST_JSON_PATH
    model_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_BOTSIM_MODEL_PATH
    output_dir = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_OUTPUT_DIR
    summary = evaluate_reddit_twibot_transfer(
        path=data_path,
        model_path=model_path,
        output_dir=output_dir,
    )
    print(f"[reddit-transfer] model:            {summary['paths']['model']}")
    print(f"[reddit-transfer] metrics:          {summary['paths']['metrics']}")
    print(f"[reddit-transfer] confusion_matrix: {summary['paths']['confusion_matrix']}")
