"""
Phase 2 threshold calibration tests.

All 6 tests skip cleanly when calibrate.py does not exist (ImportError),
and will execute the full test body once calibrate.py is created in Plan 02.

Requirements covered:
    CALIB-01: calibrate_thresholds returns valid StageThresholds within bounds
    CALIB-02: metric switching and invalid metric error
    CALIB-03: calibrated thresholds persisted in system.th; reproducible under same seed
"""

from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import botdetector_pipeline as bp
from botdetector_pipeline import StageThresholds


def _import_calibrate():
    """Try to import calibrate module; skip test if not available."""
    try:
        from calibrate import calibrate_thresholds
        return calibrate_thresholds
    except ImportError:
        pytest.skip("calibrate.py not yet implemented")


def test_calibrate_runs(minimal_system):
    """CALIB-01: calibrate_thresholds() completes and returns StageThresholds."""
    calibrate_thresholds = _import_calibrate()
    system, S2, edges_S2, nodes_total = minimal_system
    result = calibrate_thresholds(system, S2, edges_S2, nodes_total, metric="f1", n_trials=10, seed=42)
    assert isinstance(result, StageThresholds)


def test_threshold_bounds(minimal_system):
    """CALIB-01: Returned thresholds are within defined search bounds."""
    calibrate_thresholds = _import_calibrate()
    system, S2, edges_S2, nodes_total = minimal_system
    th = calibrate_thresholds(system, S2, edges_S2, nodes_total, metric="f1", n_trials=10, seed=42)
    assert 0.80 <= th.s1_bot <= 0.999
    assert 0.001 <= th.s1_human <= 0.20
    assert 1.0 <= th.n1_max_for_exit <= 6.0
    assert 0.70 <= th.s2a_bot <= 0.999
    assert 0.001 <= th.s2a_human <= 0.30
    assert 1.0 <= th.n2_trigger <= 6.0
    assert 1.0 <= th.disagreement_trigger <= 8.0
    assert 0.70 <= th.s12_bot <= 0.999
    assert 0.001 <= th.s12_human <= 0.30
    assert 1.0 <= th.novelty_force_stage3 <= 6.0
    # Ordering constraints
    assert th.s1_human < th.s1_bot
    assert th.s2a_human < th.s2a_bot
    assert th.s12_human < th.s12_bot


def test_metric_switching(minimal_system):
    """CALIB-02: All 4 metrics run without error."""
    calibrate_thresholds = _import_calibrate()
    system, S2, edges_S2, nodes_total = minimal_system
    for metric in ["f1", "auc", "precision", "recall"]:
        result = calibrate_thresholds(system, S2, edges_S2, nodes_total, metric=metric, n_trials=5, seed=42)
        assert isinstance(result, StageThresholds), f"Failed for metric={metric}"


def test_invalid_metric_raises(minimal_system):
    """CALIB-02: Invalid metric string raises ValueError."""
    calibrate_thresholds = _import_calibrate()
    system, S2, edges_S2, nodes_total = minimal_system
    with pytest.raises(ValueError, match="Unknown metric"):
        calibrate_thresholds(system, S2, edges_S2, nodes_total, metric="invalid_metric", n_trials=5, seed=42)


def test_th_persisted_in_system(minimal_system):
    """CALIB-03: After calibration, system.th matches the returned StageThresholds."""
    calibrate_thresholds = _import_calibrate()
    system, S2, edges_S2, nodes_total = minimal_system
    original_th = system.th
    returned_th = calibrate_thresholds(system, S2, edges_S2, nodes_total, metric="f1", n_trials=10, seed=42)
    assert system.th is returned_th  # same object
    assert system.th is not original_th  # different from original


def test_reproducibility(minimal_system):
    """CALIB-01/03: Same seed produces identical thresholds."""
    calibrate_thresholds = _import_calibrate()
    system, S2, edges_S2, nodes_total = minimal_system
    th1 = calibrate_thresholds(system, S2, edges_S2, nodes_total, metric="f1", n_trials=10, seed=42)
    # Save values
    vals1 = (th1.s1_bot, th1.s1_human, th1.n1_max_for_exit, th1.s2a_bot, th1.s2a_human,
             th1.n2_trigger, th1.disagreement_trigger, th1.s12_bot, th1.s12_human, th1.novelty_force_stage3)
    th2 = calibrate_thresholds(system, S2, edges_S2, nodes_total, metric="f1", n_trials=10, seed=42)
    vals2 = (th2.s1_bot, th2.s1_human, th2.n1_max_for_exit, th2.s2a_bot, th2.s2a_human,
             th2.n2_trigger, th2.disagreement_trigger, th2.s12_bot, th2.s12_human, th2.novelty_force_stage3)
    for v1, v2 in zip(vals1, vals2):
        assert v1 == v2, f"Reproducibility failed: {v1} != {v2}"


def test_calibration_report_contains_trial_diagnostics(minimal_system, capsys):
    """Phase 18: calibration stores deterministic diagnostics for the one maintained trial."""
    calibrate_thresholds = _import_calibrate()
    system, S2, edges_S2, nodes_total = minimal_system

    calibrate_thresholds(system, S2, edges_S2, nodes_total, metric="f1", n_trials=10, seed=42)
    report = system.calibration_report_

    assert report["metric"] == "f1"
    assert report["requested_trials"] == 1
    assert report["executed_trials"] == 1
    assert len(report["trials"]) == 1
    assert report["best_tie_count"] >= 1
    assert report["selected_trial_number"] == 0

    for trial in report["trials"]:
        assert "primary_score" in trial
        assert "secondary_log_loss" in trial
        assert "secondary_brier" in trial
        assert "positive_predictions" in trial
        assert "amr_usage_rate" in trial
        assert "stage3_usage_rate" in trial
        assert "label_signature" in trial
        assert "routing_signature" in trial
        assert "thresholds" in trial

    output = capsys.readouterr().out
    assert "single trial selected" in output


def test_report_summary_exposes_selected_and_alternatives(minimal_system):
    """Phase 18: compact summary should reflect the single maintained trial."""
    import calibrate as calibrate_module

    system, S2, edges_S2, nodes_total = minimal_system
    calibrate_module.calibrate_thresholds(system, S2, edges_S2, nodes_total, metric="f1", n_trials=12, seed=42)

    summary = calibrate_module.build_calibration_report_summary(system.calibration_report_, top_k=2)
    artifact_path = Path(".planning/workstreams/calibration-fix/phases/09-validation-and-selection-evidence/test-calibration-report.json")
    try:
        written = calibrate_module.write_calibration_report_artifact(
            system.calibration_report_,
            artifact_path,
            top_k=2,
        )

        assert summary == written
        assert artifact_path.exists()
        assert summary["selection_policy"]["strategy"] == "single_trial"
        assert summary["selected_trial"]["trial_number"] == system.calibration_report_["selected_trial_number"]
        assert "thresholds" in summary["selected_trial"]
        assert summary["alternatives"] == []
    finally:
        artifact_path.unlink(missing_ok=True)


def test_calibration_report_is_single_trial_even_when_more_trials_requested(minimal_system):
    """Phase 18: maintained calibration ignores higher requested trial counts."""
    calibrate_thresholds = _import_calibrate()
    system, S2, edges_S2, nodes_total = minimal_system

    calibrate_thresholds(system, S2, edges_S2, nodes_total, metric="f1", n_trials=40, seed=42)
    report = system.calibration_report_

    assert report["requested_trials"] == 1
    assert report["executed_trials"] == 1
    assert report["stopped_early"] is False
    assert report["best_tie_count"] == 1


def test_predict_system_uses_amr_branch_when_configured(minimal_system, monkeypatch):
    """Phase 9: prediction should honor the explicit AMR branch and ignore any LSTM object."""
    system, S2, edges_S2, nodes_total = minimal_system
    calls = {"amr": 0}
    original_refine = system.amr_refiner.refine

    def tracked_refine(z_base, h_amr):
        calls["amr"] += 1
        return original_refine(z_base, h_amr)

    monkeypatch.setattr(system.amr_refiner, "refine", tracked_refine)
    monkeypatch.setattr(bp, "gate_amr", lambda p2a, n2, z1, z2a, th: np.ones_like(p2a, dtype=bool))

    results = bp.predict_system(system, S2, edges_S2, nodes_total)

    assert calls["amr"] == 1
    assert results["amr_used"].eq(1).all()
    assert {"p1", "p2", "p12", "p_final", "stage3_used"}.issubset(results.columns)
