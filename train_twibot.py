from __future__ import annotations

import json
import os
import sys

import joblib
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from calibrate import calibrate_thresholds, write_calibration_report_artifact
from cascade_pipeline import CascadePipeline, FeatureConfig, StageThresholds
from evaluate import evaluate_s3
from cascade_pipeline import STAGE1_TWITTER_COLUMNS
from data_io import _detect_encoding, build_edges, load_accounts

SEED = 42
DEFAULT_TWIBOT_MODEL_PATH = "trained_system_twibot.joblib"
PHASE15_ARTIFACT_DIR = os.path.join(
    ".planning",
    "phases",
    "15-twibot-cascade-training-and-evaluation",
    "artifacts",
)
DEFAULT_OUTPUT_FILES = (
    "metrics_twibot20_native.json",
    "results_twibot20_native.json",
    "calibration_twibot20_native.json",
)
_PROTECTED_MODEL_ARTIFACTS = {
    "trained_system.joblib",
    "trained_system_v11.joblib",
    "trained_system_v12.joblib",
    "trained_system_botsim.joblib",
    "trained_system_stage2b_amr.joblib",
    "trained_system_stage2b_lstm.joblib",
}

os.environ.setdefault("LOKY_MAX_CPU_COUNT", "8")
os.environ.setdefault("OMP_NUM_THREADS", "4")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "4")
os.environ.setdefault("MKL_NUM_THREADS", "4")


def _load_raw_records(path: str) -> list[dict]:
    with open(path, "r", encoding=_detect_encoding(path)) as f:
        return json.load(f)


def load_accounts_with_ids(path: str) -> pd.DataFrame:
    df = load_accounts(path).copy()
    raw = _load_raw_records(path)
    df["account_id"] = [str(record["ID"]) for record in raw]
    return df


def filter_edges_for_split(edges_df: pd.DataFrame, node_ids: np.ndarray) -> pd.DataFrame:
    node_set = set(np.asarray(node_ids).tolist())
    mask = edges_df["src"].isin(node_set) & edges_df["dst"].isin(node_set)
    return edges_df[mask].reset_index(drop=True)


def split_train_accounts(
    accounts_df: pd.DataFrame,
    *,
    seed: int = SEED,
    s2_fraction: float = 0.2,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    S1, S2 = train_test_split(
        accounts_df,
        test_size=s2_fraction,
        stratify=accounts_df["label"],
        shuffle=True,
        random_state=seed,
    )
    return S1.reset_index(drop=True), S2.reset_index(drop=True)


def ensure_safe_model_output_path(path: str) -> str:
    basename = os.path.basename(path)
    if basename in _PROTECTED_MODEL_ARTIFACTS:
        raise ValueError(f"Refusing to overwrite protected model artifact: {basename}")
    return path


def _save_json(payload: dict | list[dict], path: str) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)


def list_expected_output_files() -> list[str]:
    return list(DEFAULT_OUTPUT_FILES)


def train_twibot(
    train_path: str = "train.json",
    dev_path: str = "dev.json",
    test_path: str = "test.json",
    model_output_path: str = DEFAULT_TWIBOT_MODEL_PATH,
    output_dir: str = PHASE15_ARTIFACT_DIR,
    seed: int = SEED,
    calibrate_trials: int = 1,
) -> dict:
    _ = calibrate_trials
    model_output_path = ensure_safe_model_output_path(model_output_path)
    os.makedirs(output_dir, exist_ok=True)

    train_df = load_accounts_with_ids(train_path)
    dev_df = load_accounts_with_ids(dev_path)
    test_df = load_accounts_with_ids(test_path)

    train_edges = build_edges(train_df, train_path)
    dev_edges = build_edges(dev_df, dev_path)
    test_edges = build_edges(test_df, test_path)

    S1, S2 = split_train_accounts(train_df, seed=seed)
    edges_S1 = filter_edges_for_split(train_edges, S1["node_idx"].to_numpy())
    edges_S2 = filter_edges_for_split(train_edges, S2["node_idx"].to_numpy())

    cfg = FeatureConfig(stage1_numeric_cols=list(STAGE1_TWITTER_COLUMNS))
    pipeline = CascadePipeline("twibot", cfg=cfg, random_state=seed)
    system = pipeline.fit(
        S1=S1,
        S2=S2,
        edges_S1=edges_S1,
        edges_S2=edges_S2,
        th=StageThresholds(),
        nodes_total=len(train_df),
    )

    calibrate_thresholds(
        system=system,
        S2=dev_df,
        edges_S2=dev_edges,
        nodes_total=len(dev_df),
        metric="f1",
        n_trials=1,
        seed=seed,
    )

    results = pipeline.predict(
        system,
        df=test_df,
        edges_df=test_edges,
        nodes_total=len(test_df),
    )
    metrics = evaluate_s3(results, test_df["label"].to_numpy(), threshold=0.5, verbose=False)
    calibration_report = getattr(system, "calibration_report_", {})

    joblib.dump(system, model_output_path)

    results_path = os.path.join(output_dir, "results_twibot20_native.json")
    metrics_path = os.path.join(output_dir, "metrics_twibot20_native.json")
    calibration_path = os.path.join(output_dir, "calibration_twibot20_native.json")

    results.to_json(results_path, orient="records", indent=2)
    _save_json(metrics, metrics_path)
    if calibration_report:
        write_calibration_report_artifact(calibration_report, calibration_path)
    else:
        _save_json({}, calibration_path)

    return {
        "system": system,
        "metrics": metrics,
        "results": results,
        "paths": {
            "model": model_output_path,
            "results": results_path,
            "metrics": metrics_path,
            "calibration": calibration_path,
        },
        "splits": {
            "train": train_path,
            "dev": dev_path,
            "test": test_path,
            "s1_size": len(S1),
            "s2_size": len(S2),
        },
    }


if __name__ == "__main__":
    train_path = sys.argv[1] if len(sys.argv) > 1 else "train.json"
    dev_path = sys.argv[2] if len(sys.argv) > 2 else "dev.json"
    test_path = sys.argv[3] if len(sys.argv) > 3 else "test.json"
    model_output_path = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_TWIBOT_MODEL_PATH
    output_dir = sys.argv[5] if len(sys.argv) > 5 else PHASE15_ARTIFACT_DIR

    summary = train_twibot(
        train_path=train_path,
        dev_path=dev_path,
        test_path=test_path,
        model_output_path=model_output_path,
        output_dir=output_dir,
    )
    print(f"[twibot] model: {summary['paths']['model']}")
    print(f"[twibot] metrics: {summary['paths']['metrics']}")
    print(f"[twibot] results: {summary['paths']['results']}")
    print(f"[twibot] calibration: {summary['paths']['calibration']}")
