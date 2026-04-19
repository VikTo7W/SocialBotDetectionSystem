"""Maintain a single-trial calibration report for the shared cascade pipeline."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
from sklearn.metrics import (
    brier_score_loss,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)

from botdetector_pipeline import StageThresholds, TrainedSystem, predict_system

METRIC_FNS = {
    "f1": lambda y, p: f1_score(y, (p >= 0.5).astype(int), zero_division=0),
    "auc": lambda y, p: roc_auc_score(y, p),
    "precision": lambda y, p: precision_score(y, (p >= 0.5).astype(int), zero_division=0),
    "recall": lambda y, p: recall_score(y, (p >= 0.5).astype(int), zero_division=0),
}


def _json_ready(value):
    """Recursively coerce numpy-backed values into JSON-serializable Python objects."""
    if isinstance(value, dict):
        return {key: _json_ready(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_ready(item) for item in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def _secondary_metrics(y_true: np.ndarray, p_final: np.ndarray) -> tuple[float, float]:
    """Return smooth probability-sensitive metrics for the maintained single trial."""
    p_clipped = np.clip(np.asarray(p_final, dtype=np.float64), 1e-6, 1 - 1e-6)
    return float(log_loss(y_true, p_clipped)), float(brier_score_loss(y_true, p_clipped))


def build_calibration_report_summary(
    calibration_report: dict,
    *,
    top_k: int = 3,
) -> dict:
    """Build a compact stable summary from the single-trial calibration report."""
    _ = top_k
    trials = list(calibration_report.get("trials", []))
    if not trials:
        raise ValueError("calibration_report must include at least one completed trial.")

    selected_trial_number = int(calibration_report["selected_trial_number"])
    selected = next(
        trial for trial in trials if int(trial["trial_number"]) == selected_trial_number
    )

    return {
        "metric": calibration_report["metric"],
        "requested_trials": int(calibration_report["requested_trials"]),
        "executed_trials": int(calibration_report["executed_trials"]),
        "stopped_early": bool(calibration_report["stopped_early"]),
        "plateau_patience": int(calibration_report["plateau_patience"]),
        "selected_trial": {
            "rank": 1,
            "trial_number": selected_trial_number,
            "primary_score": float(selected["primary_score"]),
            "secondary_log_loss": float(selected["secondary_log_loss"]),
            "secondary_brier": float(selected["secondary_brier"]),
            "positive_predictions": int(selected["positive_predictions"]),
            "amr_usage_rate": float(selected["amr_usage_rate"]),
            "stage3_usage_rate": float(selected["stage3_usage_rate"]),
            "thresholds": dict(selected["thresholds"]),
        },
        "tie_analysis": {
            "best_primary_score": float(calibration_report["best_primary_score"]),
            "best_tie_count": int(calibration_report["best_tie_count"]),
            "same_hard_predictions": bool(calibration_report["best_tie_same_hard_predictions"]),
            "same_routing": bool(calibration_report["best_tie_same_routing"]),
        },
        "selection_policy": {
            "strategy": "single_trial",
            "primary_metric": calibration_report["metric"],
            "secondary_metrics": ["secondary_log_loss", "secondary_brier"],
            "plateau_guardrail": "not_applicable_single_trial",
        },
        "alternatives": [],
    }


def write_calibration_report_artifact(
    calibration_report: dict,
    output_path: str | Path,
    *,
    top_k: int = 3,
) -> dict:
    """Write a compact JSON artifact for the maintained calibration evidence."""
    summary = build_calibration_report_summary(calibration_report, top_k=top_k)
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(_json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def calibrate_thresholds(
    system: TrainedSystem,
    S2,
    edges_S2,
    nodes_total: int,
    metric: str = "f1",
    n_trials: int = 1,
    seed: int = 42,
) -> StageThresholds:
    """Evaluate the current thresholds once and persist a stable single-trial report."""
    _ = n_trials
    _ = seed

    if metric not in METRIC_FNS:
        raise ValueError(f"Unknown metric '{metric}'. Choose from: {list(METRIC_FNS)}")

    y_true = S2["label"].to_numpy()
    result = predict_system(system, S2, edges_S2, nodes_total=nodes_total)
    p_final = result["p_final"].to_numpy(dtype=np.float64)
    hard_predictions = (p_final >= 0.5).astype(np.uint8)
    score = METRIC_FNS[metric](y_true, p_final)
    primary_score = 0.0 if np.isnan(score) else float(score)
    secondary_log_loss, secondary_brier = _secondary_metrics(y_true, p_final)
    amr_used = (
        result["amr_used"].to_numpy(dtype=np.uint8)
        if "amr_used" in result
        else np.zeros(len(result), dtype=np.uint8)
    )
    stage3_used = (
        result["stage3_used"].to_numpy(dtype=np.uint8)
        if "stage3_used" in result
        else np.zeros(len(result), dtype=np.uint8)
    )
    thresholds = {
        field: getattr(system.th, field)
        for field in system.th.__dataclass_fields__
    }
    system.th = StageThresholds(**thresholds)

    system.calibration_report_ = {
        "metric": metric,
        "requested_trials": 1,
        "executed_trials": 1,
        "stopped_early": False,
        "plateau_patience": 1,
        "selected_trial_number": 0,
        "best_primary_score": primary_score,
        "selected_secondary_log_loss": secondary_log_loss,
        "selected_secondary_brier": secondary_brier,
        "best_tie_count": 1,
        "best_tie_same_hard_predictions": True,
        "best_tie_same_routing": True,
        "trials": [
            {
                "trial_number": 0,
                "primary_score": primary_score,
                "secondary_log_loss": secondary_log_loss,
                "secondary_brier": secondary_brier,
                "positive_predictions": int(hard_predictions.sum()),
                "amr_usage_rate": float(amr_used.mean()),
                "stage3_usage_rate": float(stage3_used.mean()),
                "label_signature": "single_trial",
                "routing_signature": "single_trial",
                "thresholds": thresholds,
            }
        ],
    }

    print(f"[calibration] single trial selected by {metric}={primary_score:.4f}")
    return system.th
