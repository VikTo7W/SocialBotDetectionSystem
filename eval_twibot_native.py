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
from train_twibot import DEFAULT_TWIBOT_MODEL_PATH, load_accounts_with_ids
from data_io import build_edges

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


def run_inference_twibot_native(
    path: str,
    model_path: str = DEFAULT_TWIBOT_MODEL_PATH,
) -> pd.DataFrame:
    accounts_df = load_accounts_with_ids(path)
    edges_df = build_edges(accounts_df, path)
    system = joblib.load(model_path)
    pipeline = CascadePipeline("twibot", cfg=system.cfg, embedder=system.embedder)
    return pipeline.predict(system, df=accounts_df, edges_df=edges_df, nodes_total=len(accounts_df))


def evaluate_twibot_native(
    path: str = DEFAULT_TEST_JSON_PATH,
    model_path: str = DEFAULT_TWIBOT_MODEL_PATH,
    output_dir: str = DEFAULT_OUTPUT_DIR,
    threshold: float = 0.5,
) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    results = run_inference_twibot_native(path, model_path=model_path)
    accounts_df = load_accounts_with_ids(path)
    y_true = accounts_df["label"].to_numpy()
    metrics = evaluate_s3(results, y_true, threshold=threshold, verbose=True)

    metrics_path = os.path.join(output_dir, "metrics_twibot_native.json")
    cm_path = os.path.join(output_dir, "confusion_matrix_twibot_native.png")

    _save_json(metrics, metrics_path)
    _write_confusion_matrix(
        results,
        y_true,
        threshold,
        cm_path,
        title="TwiBot-20 native confusion matrix",
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
    model_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_TWIBOT_MODEL_PATH
    output_dir = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_OUTPUT_DIR
    summary = evaluate_twibot_native(
        path=data_path,
        model_path=model_path,
        output_dir=output_dir,
    )
    print(f"[twibot-native] model:            {summary['paths']['model']}")
    print(f"[twibot-native] metrics:          {summary['paths']['metrics']}")
    print(f"[twibot-native] confusion_matrix: {summary['paths']['confusion_matrix']}")
