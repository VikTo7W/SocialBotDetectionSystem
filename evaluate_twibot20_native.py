from __future__ import annotations

import json
import os
import sys

import joblib
import pandas as pd

from cascade_pipeline import CascadePipeline
from evaluate import evaluate_s3
from train_twibot import (
    DEFAULT_TWIBOT_MODEL_PATH,
    PHASE15_ARTIFACT_DIR,
    load_accounts_with_ids,
)
from twibot20_io import build_edges

DEFAULT_RESULTS_FILENAME = "results_twibot20_native.json"
DEFAULT_METRICS_FILENAME = "metrics_twibot20_native.json"
DEFAULT_NATIVE_MODEL_PATH = DEFAULT_TWIBOT_MODEL_PATH


def _save_json(payload: dict | list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def run_inference_native(
    path: str,
    model_path: str = DEFAULT_NATIVE_MODEL_PATH,
) -> pd.DataFrame:
    accounts_df = load_accounts_with_ids(path)
    edges_df = build_edges(accounts_df, path)
    system = joblib.load(model_path)
    pipeline = CascadePipeline("twibot", cfg=system.cfg, embedder=system.embedder)
    return pipeline.predict(
        system,
        df=accounts_df,
        edges_df=edges_df,
        nodes_total=len(accounts_df),
    )


def evaluate_twibot20_native(
    path: str = "test.json",
    model_path: str = DEFAULT_NATIVE_MODEL_PATH,
    output_dir: str = PHASE15_ARTIFACT_DIR,
    threshold: float = 0.5,
) -> dict:
    os.makedirs(output_dir, exist_ok=True)
    results = run_inference_native(path, model_path=model_path)
    accounts_df = load_accounts_with_ids(path)
    metrics = evaluate_s3(results, accounts_df["label"].to_numpy(), threshold=threshold, verbose=False)

    results_path = os.path.join(output_dir, DEFAULT_RESULTS_FILENAME)
    metrics_path = os.path.join(output_dir, DEFAULT_METRICS_FILENAME)
    results.to_json(results_path, orient="records", indent=2)
    _save_json(metrics, metrics_path)

    return {
        "results": results,
        "metrics": metrics,
        "paths": {
            "results": results_path,
            "metrics": metrics_path,
            "model": model_path,
        },
    }


if __name__ == "__main__":
    data_path = sys.argv[1] if len(sys.argv) > 1 else "test.json"
    model_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_NATIVE_MODEL_PATH
    output_dir = sys.argv[3] if len(sys.argv) > 3 else PHASE15_ARTIFACT_DIR

    summary = evaluate_twibot20_native(
        path=data_path,
        model_path=model_path,
        output_dir=output_dir,
    )
    print(f"[twibot20-native] model: {summary['paths']['model']}")
    print(f"[twibot20-native] results: {summary['paths']['results']}")
    print(f"[twibot20-native] metrics: {summary['paths']['metrics']}")
