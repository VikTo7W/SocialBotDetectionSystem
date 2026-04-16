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
from botdetector_pipeline import StageThresholds, Stage2LSTMRefiner


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
    """Phase 8: calibration stores deterministic diagnostics for each completed trial."""
    calibrate_thresholds = _import_calibrate()
    system, S2, edges_S2, nodes_total = minimal_system

    calibrate_thresholds(system, S2, edges_S2, nodes_total, metric="f1", n_trials=10, seed=42)
    report = system.calibration_report_

    assert report["metric"] == "f1"
    assert report["requested_trials"] == 10
    assert report["executed_trials"] == len(report["trials"])
    assert report["best_tie_count"] >= 1
    assert report["selected_trial_number"] >= 0

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
    assert "best-score ties" in output
    assert "selected trial" in output


def test_report_summary_exposes_selected_and_alternatives(minimal_system):
    """Phase 9: compact summary should explain the winner against nearby alternatives."""
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
        assert summary["selection_policy"]["strategy"] == "hybrid"
        assert summary["selected_trial"]["trial_number"] == system.calibration_report_["selected_trial_number"]
        assert "thresholds" in summary["selected_trial"]
        assert len(summary["alternatives"]) <= 2
        assert summary["alternatives"]
        for alternative in summary["alternatives"]:
            assert "delta_vs_selected" in alternative
            assert "behavior" in alternative
            assert "positive_predictions" in alternative["behavior"]
            assert "amr_usage_rate" in alternative["behavior"]
            assert "stage3_usage_rate" in alternative["behavior"]
    finally:
        artifact_path.unlink(missing_ok=True)


def test_secondary_metric_breaks_primary_score_ties(minimal_system, monkeypatch):
    """Phase 8: tied primary scores should be resolved by a smooth secondary metric."""
    import calibrate as calibrate_module

    system, S2, edges_S2, nodes_total = minimal_system
    base_labels = S2["label"].to_numpy(dtype=np.float64)
    base_probs = np.where(base_labels > 0.5, 0.7, 0.3)

    def tied_predict_system(sys_obj, df, edges_df, nodes_total=None):
        shift = (
            sys_obj.th.s1_bot
            + sys_obj.th.s2a_bot
            + sys_obj.th.s12_bot
            + sys_obj.th.novelty_force_stage3
        )
        offset = ((shift * 1000.0) % 17.0 - 8.0) * 0.005
        p_final = np.clip(base_probs + offset, 0.0, 1.0)
        n = len(df)
        return pd.DataFrame(
            {
                "p_final": p_final,
                "amr_used": np.zeros(n, dtype=np.int64),
                "stage3_used": np.zeros(n, dtype=np.int64),
            }
        )

    monkeypatch.setattr(calibrate_module, "predict_system", tied_predict_system)
    calibrate_module.calibrate_thresholds(system, S2, edges_S2, nodes_total, metric="f1", n_trials=12, seed=42)
    report = system.calibration_report_

    best_trials = [
        trial
        for trial in report["trials"]
        if abs(trial["primary_score"] - report["best_primary_score"]) <= 1e-12
    ]
    assert len(best_trials) > 1
    best_log_loss = min(trial["secondary_log_loss"] for trial in best_trials)
    selected = next(
        trial for trial in report["trials"] if trial["trial_number"] == report["selected_trial_number"]
    )
    assert selected["secondary_log_loss"] == best_log_loss


def test_plateau_guardrail_can_stop_early(minimal_system, monkeypatch):
    """Phase 8: clearly flat searches should stop early instead of exhausting all trials."""
    import calibrate as calibrate_module

    system, S2, edges_S2, nodes_total = minimal_system

    def flat_predict_system(sys_obj, df, edges_df, nodes_total=None):
        n = len(df)
        return pd.DataFrame(
            {
                "p_final": np.full(n, 0.5, dtype=np.float64),
                "amr_used": np.zeros(n, dtype=np.int64),
                "stage3_used": np.zeros(n, dtype=np.int64),
            }
        )

    monkeypatch.setattr(calibrate_module, "predict_system", flat_predict_system)
    calibrate_module.calibrate_thresholds(system, S2, edges_S2, nodes_total, metric="f1", n_trials=40, seed=42)
    report = system.calibration_report_

    assert report["stopped_early"] is True
    assert report["executed_trials"] < report["requested_trials"]
    assert report["best_tie_count"] == report["executed_trials"]


def test_lstm_stage2b_refiner_is_seed_reproducible(minimal_lstm_stage2b_inputs):
    """Phase 8: LSTM Stage 2b prototype should train deterministically under a fixed seed."""
    sequences = minimal_lstm_stage2b_inputs["sequences"]
    lengths = minimal_lstm_stage2b_inputs["lengths"]
    z_base = minimal_lstm_stage2b_inputs["z_base"]
    y = minimal_lstm_stage2b_inputs["y"]

    refiner_a = Stage2LSTMRefiner(hidden_dim=12, epochs=15, random_state=42)
    refiner_b = Stage2LSTMRefiner(hidden_dim=12, epochs=15, random_state=42)

    refiner_a.fit(sequences, lengths, z_base, y)
    refiner_b.fit(sequences, lengths, z_base, y)

    refined_a = refiner_a.refine(z_base, sequences, lengths)
    refined_b = refiner_b.refine(z_base, sequences, lengths)
    assert np.allclose(refined_a, refined_b), "LSTM Stage 2b prototype must be deterministic for the same seed"


def test_lstm_stage2b_refiner_preserves_z2_contract_with_zero_history(minimal_lstm_stage2b_inputs):
    """Phase 8: LSTM Stage 2b prototype must return stable refined logits even with zero-history rows."""
    sequences = minimal_lstm_stage2b_inputs["sequences"].copy()
    lengths = minimal_lstm_stage2b_inputs["lengths"].copy()
    z_base = minimal_lstm_stage2b_inputs["z_base"]
    y = minimal_lstm_stage2b_inputs["y"]

    refiner = Stage2LSTMRefiner(hidden_dim=12, epochs=15, random_state=42)
    refiner.fit(sequences, lengths, z_base, y)

    lengths[0] = 0
    sequences[0] = 0.0
    refined = refiner.refine(z_base, sequences, lengths)

    assert refined.shape == z_base.shape
    assert np.isfinite(refined).all()
    assert refined.dtype == np.float64
