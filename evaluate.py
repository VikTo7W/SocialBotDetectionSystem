"""
Evaluation module for the S3 cascade bot detection system.

Provides evaluate_s3() which takes predict_system() output and ground truth
labels, then prints a complete paper-ready evaluation report:
  - Overall metrics (F1, AUC, precision, recall) — satisfies EVAL-01
  - Per-stage metrics table (p1, p2, p12, p_final) — satisfies EVAL-02
  - Routing statistics (exit percentages, AMR trigger rate) — satisfies EVAL-03
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, roc_auc_score, precision_score, recall_score


def _compute_metrics(y_true: np.ndarray, p: np.ndarray, threshold: float) -> dict:
    """
    Compute F1, AUC, precision, recall for a probability column vs ground truth.

    Args:
        y_true:    Ground truth labels (0/1), shape (n,).
        p:         Predicted probabilities, shape (n,).
        threshold: Classification cutoff.

    Returns:
        dict with keys "f1", "auc", "precision", "recall", all floats in [0, 1].
    """
    y_pred = (p >= threshold).astype(int)
    return {
        "f1":        float(f1_score(y_true, y_pred, zero_division=0)),
        "auc":       float(roc_auc_score(y_true, p)),
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall":    float(recall_score(y_true, y_pred, zero_division=0)),
    }


def _json_ready(value):
    if isinstance(value, dict):
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_json_ready(v) for v in value]
    if isinstance(value, tuple):
        return [_json_ready(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
    return value


def evaluate_s3(
    results: pd.DataFrame,
    y_true: np.ndarray,
    threshold: float = 0.5,
    verbose: bool = True,
) -> dict:
    """
    Evaluate cascade system output against ground truth labels.

    Prints a paper-ready report with three sections:
      1. Overall Metrics — p_final vs y_true (EVAL-01)
      2. Per-Stage Metrics — p1, p2, p12, p_final each vs y_true (EVAL-02)
      3. Routing Statistics — stage exit rates and AMR trigger rate (EVAL-03)

    Args:
        results:   DataFrame returned by predict_system(). Must contain columns:
                   account_id, p1, n1, p2, n2, amr_used, p12,
                   stage3_used, p3, n3, p_final.
        y_true:    Ground truth binary labels (0 = human, 1 = bot), shape (n,).
        threshold: Classification cutoff applied to all probability columns.
                   Default 0.5.

    Returns:
        dict with keys:
          "overall":   {"f1", "auc", "precision", "recall"}
          "per_stage": {"p1": {...}, "p2": {...}, "p12": {...}, "p_final": {...}}
          "routing":   {"pct_stage1_exit", "pct_stage2_exit",
                        "pct_stage3_exit", "pct_amr_triggered"}
        All metric values are floats; routing values are percentages in [0, 100].
    """
    y_true = np.asarray(y_true, dtype=int)
    n = len(results)

    # ------------------------------------------------------------------
    # 1. Overall metrics (EVAL-01)
    # ------------------------------------------------------------------
    p_final = results["p_final"].to_numpy(dtype=np.float64)
    overall = _compute_metrics(y_true, p_final, threshold)

    # ------------------------------------------------------------------
    # 2. Per-stage metrics (EVAL-02)
    # ------------------------------------------------------------------
    per_stage: dict = {}
    for col in ("p1", "p2", "p12", "p_final"):
        per_stage[col] = _compute_metrics(
            y_true, results[col].to_numpy(dtype=np.float64), threshold
        )

    # ------------------------------------------------------------------
    # 3. Routing statistics (EVAL-03)
    # ------------------------------------------------------------------
    amr_used = results["amr_used"].to_numpy(dtype=int)
    stage3_used = results["stage3_used"].to_numpy(dtype=int)

    # Stage 1 exit: no AMR, no Stage 3
    stage1_mask = (amr_used == 0) & (stage3_used == 0)
    # Stage 2 exit: used AMR but not Stage 3
    stage2_mask = (amr_used == 1) & (stage3_used == 0)
    # Stage 3 exit: routed to Stage 3 (regardless of AMR)
    stage3_mask = (stage3_used == 1)

    pct_stage1_exit  = float(100.0 * stage1_mask.sum() / n)
    pct_stage2_exit  = float(100.0 * stage2_mask.sum() / n)
    pct_stage3_exit  = float(100.0 * stage3_mask.sum() / n)
    pct_amr_triggered = float(100.0 * amr_used.sum() / n)

    routing = {
        "pct_stage1_exit":   pct_stage1_exit,
        "pct_stage2_exit":   pct_stage2_exit,
        "pct_stage3_exit":   pct_stage3_exit,
        "pct_amr_triggered": pct_amr_triggered,
    }

    # ------------------------------------------------------------------
    # 4. Print paper-ready report
    # ------------------------------------------------------------------
    if verbose:
        _print_report(overall, per_stage, routing)

    return {
        "overall":   overall,
        "per_stage": per_stage,
        "routing":   routing,
    }


def compare_stage2b_variants(
    reports_by_variant: dict[str, dict],
    *,
    primary_metric: str = "f1",
    baseline_variant: str = "amr",
    challenger_variant: str = "lstm",
    metric_margin: float = 0.01,
    auc_margin: float = 0.01,
) -> dict:
    """
    Compare two Stage 2b variants using both headline metrics and routing behavior.

    Returns a compact recommendation-ready summary that can stay neutral when the
    challenger is only different, not clearly better.
    """
    baseline = reports_by_variant[baseline_variant]
    challenger = reports_by_variant[challenger_variant]

    baseline_metric = float(baseline["overall"][primary_metric])
    challenger_metric = float(challenger["overall"][primary_metric])
    primary_delta = challenger_metric - baseline_metric

    baseline_auc = float(baseline["overall"]["auc"])
    challenger_auc = float(challenger["overall"]["auc"])
    auc_delta = challenger_auc - baseline_auc

    metric_deltas = {
        metric: float(challenger["overall"][metric] - baseline["overall"][metric])
        for metric in ("f1", "auc", "precision", "recall")
    }
    routing_deltas = {
        key: float(challenger["routing"][key] - baseline["routing"][key])
        for key in (
            "pct_stage1_exit",
            "pct_stage2_exit",
            "pct_stage3_exit",
            "pct_amr_triggered",
        )
    }

    if primary_delta >= metric_margin:
        recommendation = {
            "status": "challenger_better",
            "recommended_variant": challenger_variant,
            "rationale": (
                f"{challenger_variant} exceeds {baseline_variant} on {primary_metric} "
                f"by {primary_delta:.4f}, which clears the recommendation margin."
            ),
        }
    elif primary_delta <= -metric_margin:
        recommendation = {
            "status": "baseline_better",
            "recommended_variant": baseline_variant,
            "rationale": (
                f"{challenger_variant} trails {baseline_variant} on {primary_metric} "
                f"by {abs(primary_delta):.4f}, so the baseline remains preferred."
            ),
        }
    elif auc_delta >= auc_margin and primary_delta >= 0.0:
        recommendation = {
            "status": "challenger_better",
            "recommended_variant": challenger_variant,
            "rationale": (
                f"{primary_metric} is effectively tied, but {challenger_variant} improves AUC "
                f"by {auc_delta:.4f} without losing on the primary metric."
            ),
        }
    else:
        recommendation = {
            "status": "neutral_keep_baseline",
            "recommended_variant": baseline_variant,
            "rationale": (
                f"{challenger_variant} is not clearly better than {baseline_variant} on "
                f"{primary_metric} plus routing evidence, so the baseline stays recommended."
            ),
        }

    return {
        "policy": {
            "primary_metric": primary_metric,
            "baseline_variant": baseline_variant,
            "challenger_variant": challenger_variant,
            "metric_margin": float(metric_margin),
            "auc_margin": float(auc_margin),
            "evaluation_rule": "metric_plus_routing",
        },
        "variants": {
            baseline_variant: baseline,
            challenger_variant: challenger,
        },
        "overall_deltas": metric_deltas,
        "routing_deltas": routing_deltas,
        "recommendation": recommendation,
    }


def write_stage2b_comparison_artifact(summary: dict, path: str | Path) -> dict:
    """Write a compact JSON artifact for Phase 10 AMR-vs-LSTM comparison evidence."""
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(_json_ready(summary), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return summary


def _print_report(overall: dict, per_stage: dict, routing: dict) -> None:
    """Print formatted evaluation report to stdout."""

    # --- Section 1: Overall Metrics ---
    print("=== Overall Metrics (p_final) ===")
    print(f"F1:        {overall['f1']:.4f}")
    print(f"AUC:       {overall['auc']:.4f}")
    print(f"Precision: {overall['precision']:.4f}")
    print(f"Recall:    {overall['recall']:.4f}")
    print()

    # --- Section 2: Per-Stage Metrics ---
    print("=== Per-Stage Metrics ===")
    # Header
    header = f"{'Stage':<9}{'F1':>8}{'AUC':>9}{'Prec':>8}{'Recall':>9}"
    separator = f"{'-------':<9}{'------':>8}{'-------':>9}{'------':>8}{'--------':>9}"
    print(header)
    print(separator)
    for stage in ("p1", "p2", "p12", "p_final"):
        m = per_stage[stage]
        print(
            f"{stage:<9}{m['f1']:>8.4f}{m['auc']:>9.4f}"
            f"{m['precision']:>8.4f}{m['recall']:>9.4f}"
        )
    print()

    # --- Section 3: Routing Statistics ---
    print("=== Routing Statistics ===")
    print(
        f"Stage 1 only exit:  {routing['pct_stage1_exit']:>5.1f}%"
        f"  (no AMR, no Stage 3)"
    )
    print(
        f"Stage 2 exit:       {routing['pct_stage2_exit']:>5.1f}%"
        f"  (AMR used, no Stage 3)"
    )
    print(
        f"Stage 3 exit:       {routing['pct_stage3_exit']:>5.1f}%"
        f"  (routed to Stage 3)"
    )
    print(f"AMR trigger rate:   {routing['pct_amr_triggered']:>5.1f}%")
