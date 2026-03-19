"""
Phase 2 threshold calibration tests.

All 6 tests skip cleanly when calibrate.py does not exist (ImportError),
and will execute the full test body once calibrate.py is created in Plan 02.

Requirements covered:
    CALIB-01: calibrate_thresholds returns valid StageThresholds within bounds
    CALIB-02: metric switching and invalid metric error
    CALIB-03: calibrated thresholds persisted in system.th; reproducible under same seed
"""

import pytest
import numpy as np
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
