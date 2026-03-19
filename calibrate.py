"""
Bayesian optimization of cascade routing thresholds on S2 validation data.
Uses Optuna TPESampler for sample-efficient search over 10 continuous threshold dimensions.
"""
from __future__ import annotations

import numpy as np
import optuna
from sklearn.metrics import f1_score, roc_auc_score, precision_score, recall_score

from botdetector_pipeline import StageThresholds, TrainedSystem, predict_system

METRIC_FNS = {
    "f1":        lambda y, p: f1_score(y, (p >= 0.5).astype(int), zero_division=0),
    "auc":       lambda y, p: roc_auc_score(y, p),
    "precision": lambda y, p: precision_score(y, (p >= 0.5).astype(int), zero_division=0),
    "recall":    lambda y, p: recall_score(y, (p >= 0.5).astype(int), zero_division=0),
}


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
    Mutates system.th in-place and returns the best StageThresholds found.

    Args:
        system: Trained cascade system whose .th field will be updated.
        S2: Validation DataFrame with 'label' column and all feature columns.
        edges_S2: Edge DataFrame for S2 accounts (src, dst, weight, etype).
        nodes_total: Total number of nodes in the graph.
        metric: Optimization objective — one of "f1", "auc", "precision", "recall".
        n_trials: Number of Optuna trials (default 200).
        seed: Random seed for TPESampler reproducibility.

    Returns:
        StageThresholds with optimized values. Also assigned to system.th.

    Raises:
        ValueError: If metric is not in METRIC_FNS.
    """
    if metric not in METRIC_FNS:
        raise ValueError(f"Unknown metric '{metric}'. Choose from: {list(METRIC_FNS)}")

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    y_true = S2["label"].to_numpy()
    metric_fn = METRIC_FNS[metric]

    def objective(trial):
        # Stage 1 thresholds — s1_human range [0.001, 0.20] never overlaps s1_bot [0.80, 0.999]
        s1_human = trial.suggest_float("s1_human", 0.001, 0.20)
        s1_bot = trial.suggest_float("s1_bot", 0.80, 0.999)

        # Stage 2a thresholds — enforce s2a_human < s2a_bot with dynamic lower bound
        s2a_human = trial.suggest_float("s2a_human", 0.001, 0.30)
        s2a_bot = trial.suggest_float("s2a_bot", max(s2a_human + 0.05, 0.70), 0.999)

        # Stage 12 thresholds — enforce s12_human < s12_bot with dynamic lower bound
        s12_human = trial.suggest_float("s12_human", 0.001, 0.30)
        s12_bot = trial.suggest_float("s12_bot", max(s12_human + 0.05, 0.70), 0.999)

        system.th = StageThresholds(
            s1_bot=s1_bot,
            s1_human=s1_human,
            n1_max_for_exit=trial.suggest_float("n1_max_for_exit", 1.0, 6.0),
            s2a_bot=s2a_bot,
            s2a_human=s2a_human,
            n2_trigger=trial.suggest_float("n2_trigger", 1.0, 6.0),
            disagreement_trigger=trial.suggest_float("disagreement_trigger", 1.0, 8.0),
            s12_bot=s12_bot,
            s12_human=s12_human,
            novelty_force_stage3=trial.suggest_float("novelty_force_stage3", 1.0, 6.0),
        )
        result = predict_system(system, S2, edges_S2, nodes_total=nodes_total)
        p_final = result["p_final"].to_numpy()
        score = metric_fn(y_true, p_final)
        return 0.0 if np.isnan(score) else float(score)

    sampler = optuna.samplers.TPESampler(seed=seed)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    study.optimize(objective, n_trials=n_trials, n_jobs=1)

    # Reconstruct best thresholds from study
    best = study.best_params
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
    system.th = best_th  # CALIB-03: persist in TrainedSystem
    print(f"[calibrate] Best {metric}: {study.best_value:.4f} | trials: {n_trials}")
    print(f"[calibrate] Best thresholds: {best_th}")
    return best_th
