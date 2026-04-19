from __future__ import annotations

import json
import os
import sys

import joblib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from sklearn.metrics import ConfusionMatrixDisplay

from cascade_pipeline import CascadePipeline
from evaluate import evaluate_s3
from train_botsim import (
    DEFAULT_BOTSIM_MODEL_PATH,
    SEED,
    filter_edges_for_split,
    load_botsim_accounts,
    load_botsim_edges,
    split_train_accounts,
)

DEFAULT_OUTPUT_DIR = "paper_outputs"


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


def run_inference_botsim_native(
    model_path: str = DEFAULT_BOTSIM_MODEL_PATH,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    users, accounts = load_botsim_accounts()
    edges_df = load_botsim_edges()
    _s1, _s2, s3 = split_train_accounts(accounts, seed=SEED)
    edges_s3 = filter_edges_for_split(edges_df, s3["node_idx"].to_numpy())
    system = joblib.load(model_path)
    pipeline = CascadePipeline("botsim", cfg=system.cfg, embedder=system.embedder)
    results = pipeline.predict(
        system,
        df=s3,
        edges_df=edges_s3,
        nodes_total=len(users),
    )
    return results, s3


def evaluate_botsim_native(
    model_path: str = DEFAULT_BOTSIM_MODEL_PATH,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    threshold: float = 0.5,
) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    results, s3 = run_inference_botsim_native(model_path=model_path)
    y_true = s3["label"].to_numpy()
    metrics = evaluate_s3(results, y_true, threshold=threshold, verbose=True)

    metrics_path = os.path.join(output_dir, "metrics_botsim.json")
    cm_path = os.path.join(output_dir, "confusion_matrix_botsim.png")

    _save_json(metrics, metrics_path)
    _write_confusion_matrix(
        results,
        y_true,
        threshold,
        cm_path,
        title="BotSim-24 (native) confusion matrix",
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
    model_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BOTSIM_MODEL_PATH
    output_dir = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_OUTPUT_DIR
    summary = evaluate_botsim_native(model_path=model_path, output_dir=output_dir)
    print(f"[botsim-native] model:            {summary['paths']['model']}")
    print(f"[botsim-native] metrics:          {summary['paths']['metrics']}")
    print(f"[botsim-native] confusion_matrix: {summary['paths']['confusion_matrix']}")
