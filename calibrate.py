"""
Bayesian optimization of cascade routing thresholds on S2 validation data.
Uses Optuna TPESampler for sample-efficient search over 10 continuous threshold dimensions.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np
import optuna
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

_PRIMARY_TOL = 1e-12
_SECONDARY_TOL = 1e-12


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
    """Return smooth probability-sensitive tie-break metrics (lower is better)."""
    p_clipped = np.clip(np.asarray(p_final, dtype=np.float64), 1e-6, 1 - 1e-6)
    return float(log_loss(y_true, p_clipped)), float(brier_score_loss(y_true, p_clipped))


def _hash_array(values: np.ndarray) -> str:
    """Compact deterministic signature for comparing predictions and routing behavior."""
    arr = np.ascontiguousarray(values)
    return hashlib.md5(arr.view(np.uint8), usedforsecurity=False).hexdigest()


def _plateau_patience(n_trials: int) -> int:
    """Keep short test runs stable while cutting redundant longer runs."""
    return max(12, n_trials // 3)


def _is_better_trial(candidate: dict, incumbent: dict | None) -> bool:
    """Lexicographic comparison: maximize primary score, minimize smooth tie-breakers."""
    if incumbent is None:
        return True
    if candidate["primary_score"] > incumbent["primary_score"] + _PRIMARY_TOL:
        return True
    if incumbent["primary_score"] > candidate["primary_score"] + _PRIMARY_TOL:
        return False
    if candidate["secondary_log_loss"] < incumbent["secondary_log_loss"] - _SECONDARY_TOL:
        return True
    if incumbent["secondary_log_loss"] < candidate["secondary_log_loss"] - _SECONDARY_TOL:
        return False
    if candidate["secondary_brier"] < incumbent["secondary_brier"] - _SECONDARY_TOL:
        return True
    if incumbent["secondary_brier"] < candidate["secondary_brier"] - _SECONDARY_TOL:
        return False
    return candidate["trial_number"] < incumbent["trial_number"]


def build_calibration_report_summary(
    calibration_report: dict,
    *,
    top_k: int = 3,
) -> dict:
    """Build a compact winner-versus-alternatives summary from calibration_report_."""
    trials = list(calibration_report.get("trials", []))
    if not trials:
        raise ValueError("calibration_report must include at least one completed trial.")

    selected_trial_number = int(calibration_report["selected_trial_number"])
    selected = next(
        trial for trial in trials if int(trial["trial_number"]) == selected_trial_number
    )

    ranked = sorted(
        trials,
        key=lambda trial: (
            -float(trial["primary_score"]),
            float(trial["secondary_log_loss"]),
            float(trial["secondary_brier"]),
            int(trial["trial_number"]),
        ),
    )
    selected_rank = next(
        index for index, trial in enumerate(ranked, start=1)
        if int(trial["trial_number"]) == selected_trial_number
    )

    summary = {
        "metric": calibration_report["metric"],
        "requested_trials": int(calibration_report["requested_trials"]),
        "executed_trials": int(calibration_report["executed_trials"]),
        "stopped_early": bool(calibration_report["stopped_early"]),
        "plateau_patience": int(calibration_report["plateau_patience"]),
        "selected_trial": {
            "rank": selected_rank,
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
            "strategy": "hybrid",
            "primary_metric": calibration_report["metric"],
            "secondary_metrics": ["secondary_log_loss", "secondary_brier"],
            "plateau_guardrail": "patience-based early stop on no lexicographic improvement",
        },
        "alternatives": [],
    }

    for trial in ranked:
        if int(trial["trial_number"]) == selected_trial_number:
            continue
        summary["alternatives"].append(
            {
                "trial_number": int(trial["trial_number"]),
                "primary_score": float(trial["primary_score"]),
                "secondary_log_loss": float(trial["secondary_log_loss"]),
                "secondary_brier": float(trial["secondary_brier"]),
                "delta_vs_selected": {
                    "primary_score": float(trial["primary_score"]) - float(selected["primary_score"]),
                    "secondary_log_loss": float(trial["secondary_log_loss"])
                    - float(selected["secondary_log_loss"]),
                    "secondary_brier": float(trial["secondary_brier"])
                    - float(selected["secondary_brier"]),
                    "positive_predictions": int(trial["positive_predictions"])
                    - int(selected["positive_predictions"]),
                    "amr_usage_rate": float(trial["amr_usage_rate"])
                    - float(selected["amr_usage_rate"]),
                    "stage3_usage_rate": float(trial["stage3_usage_rate"])
                    - float(selected["stage3_usage_rate"]),
                },
                "behavior": {
                    "positive_predictions": int(trial["positive_predictions"]),
                    "amr_usage_rate": float(trial["amr_usage_rate"]),
                    "stage3_usage_rate": float(trial["stage3_usage_rate"]),
                },
            }
        )
        if len(summary["alternatives"]) >= top_k:
            break

    return summary


def write_calibration_report_artifact(
    calibration_report: dict,
    output_path: str | Path,
    *,
    top_k: int = 3,
) -> dict:
    """Write a compact JSON artifact for Phase 9 real-run calibration evidence."""
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
    n_trials: int = 200,
    seed: int = 42,
) -> StageThresholds:
    """
    Optimize StageThresholds on S2 using Bayesian optimization (Optuna TPESampler).
    Mutates system.th in-place and returns the selected StageThresholds.

    Args:
        system: Trained cascade system whose .th field will be updated.
        S2: Validation DataFrame with 'label' column and all feature columns.
        edges_S2: Edge DataFrame for S2 accounts (src, dst, weight, etype).
        nodes_total: Total number of nodes in the graph.
        metric: Optimization objective - one of "f1", "auc", "precision", "recall".
        n_trials: Number of Optuna trials (default 200).
        seed: Random seed for TPESampler reproducibility.

    Returns:
        StageThresholds with selected values. Also assigned to system.th.

    Raises:
        ValueError: If metric is not in METRIC_FNS.
    """
    if metric not in METRIC_FNS:
        raise ValueError(f"Unknown metric '{metric}'. Choose from: {list(METRIC_FNS)}")

    optuna.logging.enable_default_handler()
    optuna.logging.set_verbosity(optuna.logging.INFO)

    requested_trials = int(n_trials)
    patience = _plateau_patience(requested_trials)
    y_true = S2["label"].to_numpy()
    metric_fn = METRIC_FNS[metric]
    best_trial_info: dict | None = None
    plateau_counter = 0

    def objective(trial: optuna.trial.Trial) -> float:
        # Stage 1 thresholds
        s1_human = trial.suggest_float("s1_human", 0.001, 0.20)
        s1_bot = trial.suggest_float("s1_bot", 0.80, 0.999)

        # Stage 2a thresholds
        s2a_human = trial.suggest_float("s2a_human", 0.001, 0.30)
        s2a_bot = trial.suggest_float("s2a_bot", max(s2a_human + 0.05, 0.70), 0.999)

        # Stage 12 thresholds
        s12_human = trial.suggest_float("s12_human", 0.001, 0.30)
        s12_bot = trial.suggest_float("s12_bot", max(s12_human + 0.05, 0.70), 0.999)

        threshold_values = {
            "s1_bot": s1_bot,
            "s1_human": s1_human,
            "n1_max_for_exit": trial.suggest_float("n1_max_for_exit", 1.0, 6.0),
            "s2a_bot": s2a_bot,
            "s2a_human": s2a_human,
            "n2_trigger": trial.suggest_float("n2_trigger", 1.0, 6.0),
            "disagreement_trigger": trial.suggest_float("disagreement_trigger", 1.0, 8.0),
            "s12_bot": s12_bot,
            "s12_human": s12_human,
            "novelty_force_stage3": trial.suggest_float("novelty_force_stage3", 1.0, 6.0),
        }
        system.th = StageThresholds(**threshold_values)

        result = predict_system(system, S2, edges_S2, nodes_total=nodes_total)
        p_final = result["p_final"].to_numpy(dtype=np.float64)
        hard_predictions = (p_final >= 0.5).astype(np.uint8)
        score = metric_fn(y_true, p_final)
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

        trial.set_user_attr("primary_score", primary_score)
        trial.set_user_attr("secondary_log_loss", secondary_log_loss)
        trial.set_user_attr("secondary_brier", secondary_brier)
        trial.set_user_attr("positive_predictions", int(hard_predictions.sum()))
        trial.set_user_attr("amr_usage_rate", float(amr_used.mean()))
        trial.set_user_attr("stage3_usage_rate", float(stage3_used.mean()))
        trial.set_user_attr("label_signature", _hash_array(hard_predictions))
        trial.set_user_attr("routing_signature", _hash_array(np.column_stack([amr_used, stage3_used])))
        trial.set_user_attr("thresholds", threshold_values)
        return primary_score

    def plateau_callback(study: optuna.Study, trial: optuna.trial.FrozenTrial) -> None:
        nonlocal best_trial_info, plateau_counter

        current_info = {
            "trial_number": trial.number,
            "primary_score": float(trial.user_attrs["primary_score"]),
            "secondary_log_loss": float(trial.user_attrs["secondary_log_loss"]),
            "secondary_brier": float(trial.user_attrs["secondary_brier"]),
            "label_signature": trial.user_attrs["label_signature"],
            "routing_signature": trial.user_attrs["routing_signature"],
        }
        if _is_better_trial(current_info, best_trial_info):
            best_trial_info = current_info
            plateau_counter = 0
        else:
            plateau_counter += 1

        if requested_trials > patience and plateau_counter >= patience:
            study.set_user_attr("plateau_stop_trial", trial.number)
            study.set_user_attr("plateau_patience", patience)
            study.stop()

    sampler = optuna.samplers.TPESampler(seed=seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    study.optimize(objective, n_trials=requested_trials, n_jobs=1, callbacks=[plateau_callback])

    completed_trials = [t for t in study.trials if t.state == optuna.trial.TrialState.COMPLETE]
    if not completed_trials:
        raise RuntimeError("No completed Optuna trials were available for calibration.")

    ranked_trials = sorted(
        completed_trials,
        key=lambda t: (
            -float(t.user_attrs["primary_score"]),
            float(t.user_attrs["secondary_log_loss"]),
            float(t.user_attrs["secondary_brier"]),
            t.number,
        ),
    )
    selected_trial = ranked_trials[0]
    best_primary_score = float(selected_trial.user_attrs["primary_score"])
    best_primary_trials = [
        t
        for t in completed_trials
        if abs(float(t.user_attrs["primary_score"]) - best_primary_score) <= _PRIMARY_TOL
    ]
    best_label_signatures = {t.user_attrs["label_signature"] for t in best_primary_trials}
    best_routing_signatures = {t.user_attrs["routing_signature"] for t in best_primary_trials}
    stopped_early = len(completed_trials) < requested_trials

    best = selected_trial.user_attrs["thresholds"]
    best_th = StageThresholds(
        s1_bot=best["s1_bot"],
        s1_human=best["s1_human"],
        n1_max_for_exit=best["n1_max_for_exit"],
        s2a_bot=best["s2a_bot"],
        s2a_human=best["s2a_human"],
        n2_trigger=best["n2_trigger"],
        disagreement_trigger=best["disagreement_trigger"],
        s12_bot=best["s12_bot"],
        s12_human=best["s12_human"],
        novelty_force_stage3=best["novelty_force_stage3"],
    )
    system.th = best_th
    system.calibration_report_ = {
        "metric": metric,
        "requested_trials": requested_trials,
        "executed_trials": len(completed_trials),
        "stopped_early": stopped_early,
        "plateau_patience": patience,
        "best_primary_score": best_primary_score,
        "selected_trial_number": selected_trial.number,
        "selected_secondary_log_loss": float(selected_trial.user_attrs["secondary_log_loss"]),
        "selected_secondary_brier": float(selected_trial.user_attrs["secondary_brier"]),
        "best_tie_count": len(best_primary_trials),
        "best_tie_same_hard_predictions": len(best_label_signatures) == 1,
        "best_tie_same_routing": len(best_routing_signatures) == 1,
        "trials": [
            {
                "trial_number": t.number,
                "primary_score": float(t.user_attrs["primary_score"]),
                "secondary_log_loss": float(t.user_attrs["secondary_log_loss"]),
                "secondary_brier": float(t.user_attrs["secondary_brier"]),
                "positive_predictions": int(t.user_attrs["positive_predictions"]),
                "amr_usage_rate": float(t.user_attrs["amr_usage_rate"]),
                "stage3_usage_rate": float(t.user_attrs["stage3_usage_rate"]),
                "label_signature": t.user_attrs["label_signature"],
                "routing_signature": t.user_attrs["routing_signature"],
                "thresholds": dict(t.user_attrs["thresholds"]),
            }
            for t in completed_trials
        ],
    }

    print(
        f"[calibrate] Best {metric}: {best_primary_score:.4f} | "
        f"trials: {len(completed_trials)}/{requested_trials}"
    )
    print(
        "[calibrate] best-score ties: "
        f"{len(best_primary_trials)} | "
        f"same hard predictions: {len(best_label_signatures) == 1} | "
        f"same routing: {len(best_routing_signatures) == 1}"
    )
    print(
        "[calibrate] selected trial "
        f"{selected_trial.number} via secondary log-loss="
        f"{float(selected_trial.user_attrs['secondary_log_loss']):.6f}, "
        f"brier={float(selected_trial.user_attrs['secondary_brier']):.6f}"
    )
    if stopped_early:
        print(
            f"[calibrate] early stop triggered after {len(completed_trials)} trials "
            f"(patience={patience})"
        )
    print(f"[calibrate] Best thresholds: {best_th}")
    return best_th
