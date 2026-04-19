"""
Phase 22 - Pipeline Surface Consolidation: red-test safety net.

This module pins CascadePipeline as the single maintained orchestration surface
and establishes parity assertions before ownership is consolidated in subsequent
plans. Tests here are intended to fail if:

  - CascadePipeline is replaced or sidelined as the maintained inference path
  - botdetector_pipeline.train_system / predict_system stop forwarding to CascadePipeline
  - Routing masks, output columns, or AMR-only behavior drift during helper relocation

These are Wave 0 (red-first) safety assertions; they should all be green by the
time Plan 22-02 begins moving helpers.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from cascade_pipeline import CascadePipeline
from botdetector_pipeline import (
    FeatureConfig,
    StageThresholds,
    TrainedSystem,
    gate_amr,
    gate_stage3,
    predict_system,
    train_system,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

EXPECTED_PREDICT_COLUMNS = [
    "account_id",
    "p1",
    "n1",
    "p2",
    "n2",
    "amr_used",
    "p12",
    "stage3_used",
    "p3",
    "n3",
    "p_final",
]


# ---------------------------------------------------------------------------
# Task 1: pin CascadePipeline as the maintained orchestration surface
# ---------------------------------------------------------------------------


class TestCascadePipelineIsMaintenedSurface:
    """CascadePipeline must be importable and expose the maintained fit/predict API."""

    def test_cascade_pipeline_is_importable_from_cascade_pipeline_module(self):
        # CascadePipeline must live in cascade_pipeline, not botdetector_pipeline
        import cascade_pipeline as cp_module
        assert hasattr(cp_module, "CascadePipeline"), (
            "CascadePipeline must be defined in cascade_pipeline.py"
        )

    def test_cascade_pipeline_has_fit_method(self):
        pipeline = CascadePipeline("botsim")
        assert callable(getattr(pipeline, "fit", None)), (
            "CascadePipeline must expose a fit() method"
        )

    def test_cascade_pipeline_has_predict_method(self):
        pipeline = CascadePipeline("botsim")
        assert callable(getattr(pipeline, "predict", None)), (
            "CascadePipeline must expose a predict() method"
        )

    def test_cascade_pipeline_botsim_instantiates(self):
        pipeline = CascadePipeline("botsim")
        assert pipeline.dataset == "botsim"

    def test_cascade_pipeline_twibot_instantiates(self):
        pipeline = CascadePipeline("twibot")
        assert pipeline.dataset == "twibot"
        assert pipeline.cfg.stage1_numeric_cols, (
            "twibot pipeline must have non-empty stage1_numeric_cols"
        )

    def test_cascade_pipeline_rejects_unknown_dataset(self):
        with pytest.raises(ValueError, match="unknown dataset"):
            CascadePipeline("reddit")

    def test_train_botsim_imports_cascade_pipeline_not_legacy(self):
        """train_botsim.py must import CascadePipeline, not botdetector_pipeline.train_system."""
        import train_botsim
        assert hasattr(train_botsim, "CascadePipeline"), (
            "train_botsim must import CascadePipeline directly"
        )

    def test_train_twibot_imports_cascade_pipeline_not_legacy(self):
        """train_twibot.py must import CascadePipeline, not botdetector_pipeline.train_system."""
        import train_twibot
        assert hasattr(train_twibot, "CascadePipeline"), (
            "train_twibot must import CascadePipeline directly"
        )


# ---------------------------------------------------------------------------
# Task 2: compatibility wrappers forward to CascadePipeline
# ---------------------------------------------------------------------------


class TestCompatibilityWrappersForwardToCascadePipeline:
    """train_system() and predict_system() must be explicit forwarding wrappers."""

    def test_train_system_is_importable_from_botdetector_pipeline(self):
        import botdetector_pipeline as bp
        assert hasattr(bp, "train_system"), (
            "botdetector_pipeline must still export train_system for compatibility"
        )

    def test_predict_system_is_importable_from_botdetector_pipeline(self):
        import botdetector_pipeline as bp
        assert hasattr(bp, "predict_system"), (
            "botdetector_pipeline must still export predict_system for compatibility"
        )

    def test_train_system_calls_cascade_pipeline_fit(self, synthetic_training_split, monkeypatch):
        """train_system() must delegate to CascadePipeline.fit(), not implement its own training.

        train_system() imports CascadePipeline locally, so we patch cascade_pipeline.CascadePipeline
        at module level -- which is the same name train_system() resolves at call time.
        """
        captured = {}
        data = synthetic_training_split

        # use a sentinel object as the returned system so we do not execute real ML code
        _sentinel_system = object()

        class FakePipeline:
            def __init__(self, dataset, cfg=None, random_state=42, embedder=None):
                captured["dataset"] = dataset

            def fit(self, S1, S2, edges_S1, edges_S2, th, nodes_total=None, embedder=None):
                captured["fit_called"] = True
                captured["fit_S1_len"] = len(S1)
                return _sentinel_system

        # train_system() uses `from cascade_pipeline import CascadePipeline` locally.
        # Patch cascade_pipeline.CascadePipeline so the local import resolves to FakePipeline.
        import cascade_pipeline as cp_module
        monkeypatch.setattr(cp_module, "CascadePipeline", FakePipeline)

        result = train_system(
            S1=data["S1"],
            S2=data["S2"],
            edges_S1=data["edges_S1"],
            edges_S2=data["edges_S2"],
            cfg=data["cfg"],
            th=data["th"],
        )

        assert captured.get("fit_called"), (
            "train_system() must delegate to CascadePipeline.fit()"
        )
        assert captured.get("dataset") in {"botsim", "twibot"}, (
            "train_system() must instantiate CascadePipeline with a recognized dataset"
        )
        assert result is _sentinel_system, (
            "train_system() must return the TrainedSystem produced by CascadePipeline.fit()"
        )

    def test_predict_system_calls_cascade_pipeline_predict(self, minimal_system, monkeypatch):
        """predict_system() must delegate to CascadePipeline.predict()."""
        captured = {}

        system, S2, edges_S2, nodes_total = minimal_system

        class FakePipeline:
            def __init__(self, dataset, cfg=None, random_state=42, embedder=None):
                captured["dataset"] = dataset

            def predict(self, system, df, edges_df, nodes_total=None):
                captured["predict_called"] = True
                n = len(df)
                return pd.DataFrame({
                    "account_id": df["account_id"].astype(str).values,
                    "p1": np.full(n, 0.4),
                    "n1": np.full(n, 1.0),
                    "p2": np.full(n, 0.5),
                    "n2": np.full(n, 1.0),
                    "amr_used": np.zeros(n, dtype=int),
                    "p12": np.full(n, 0.45),
                    "stage3_used": np.zeros(n, dtype=int),
                    "p3": np.full(n, 0.5),
                    "n3": np.zeros(n),
                    "p_final": np.full(n, 0.46),
                })

        import cascade_pipeline as cp_module
        original_cls = cp_module.CascadePipeline
        monkeypatch.setattr(cp_module, "CascadePipeline", FakePipeline)

        try:
            result = predict_system(system, S2, edges_S2, nodes_total)
        finally:
            monkeypatch.setattr(cp_module, "CascadePipeline", original_cls)

        assert captured.get("predict_called"), (
            "predict_system() must delegate to CascadePipeline.predict()"
        )
        assert isinstance(result, pd.DataFrame)

    def test_predict_system_output_matches_cascade_pipeline_output(self, minimal_system):
        """predict_system() output must match CascadePipeline.predict() output exactly."""
        system, S2, edges_S2, nodes_total = minimal_system

        pipeline = CascadePipeline("botsim", cfg=system.cfg, embedder=system.embedder)
        direct = pipeline.predict(system, S2, edges_S2, nodes_total=nodes_total)

        wrapped = predict_system(system, S2, edges_S2, nodes_total)

        assert list(direct.columns) == list(wrapped.columns), (
            "predict_system() must return same columns as CascadePipeline.predict()"
        )
        assert direct["account_id"].tolist() == wrapped["account_id"].tolist()
        np.testing.assert_allclose(
            direct["p_final"].to_numpy(),
            wrapped["p_final"].to_numpy(),
            rtol=1e-5,
            err_msg="predict_system() p_final must match CascadePipeline.predict() p_final",
        )


# ---------------------------------------------------------------------------
# Task 3: parity assertions - routing masks, prediction columns, AMR-only behavior
# ---------------------------------------------------------------------------


class TestPredictionOutputColumns:
    """CascadePipeline.predict() must always return exactly the required columns."""

    def test_predict_output_has_all_required_columns(self, minimal_system):
        system, S2, edges_S2, nodes_total = minimal_system
        pipeline = CascadePipeline("botsim", cfg=system.cfg, embedder=system.embedder)
        result = pipeline.predict(system, S2, edges_S2, nodes_total=nodes_total)

        for col in EXPECTED_PREDICT_COLUMNS:
            assert col in result.columns, f"predict() output missing required column: {col!r}"

    def test_predict_output_has_no_extra_columns(self, minimal_system):
        system, S2, edges_S2, nodes_total = minimal_system
        pipeline = CascadePipeline("botsim", cfg=system.cfg, embedder=system.embedder)
        result = pipeline.predict(system, S2, edges_S2, nodes_total=nodes_total)

        extra = [c for c in result.columns if c not in EXPECTED_PREDICT_COLUMNS]
        assert not extra, f"predict() returned unexpected extra columns: {extra}"

    def test_predict_output_row_count_matches_input(self, minimal_system):
        system, S2, edges_S2, nodes_total = minimal_system
        pipeline = CascadePipeline("botsim", cfg=system.cfg, embedder=system.embedder)
        result = pipeline.predict(system, S2, edges_S2, nodes_total=nodes_total)

        assert len(result) == len(S2), (
            f"predict() must return one row per input account: expected {len(S2)}, got {len(result)}"
        )

    def test_predict_output_account_ids_match_input(self, minimal_system):
        system, S2, edges_S2, nodes_total = minimal_system
        pipeline = CascadePipeline("botsim", cfg=system.cfg, embedder=system.embedder)
        result = pipeline.predict(system, S2, edges_S2, nodes_total=nodes_total)

        assert result["account_id"].tolist() == S2["account_id"].astype(str).tolist(), (
            "account_id column must match input account_id order"
        )

    def test_p_final_is_in_unit_interval(self, minimal_system):
        system, S2, edges_S2, nodes_total = minimal_system
        pipeline = CascadePipeline("botsim", cfg=system.cfg, embedder=system.embedder)
        result = pipeline.predict(system, S2, edges_S2, nodes_total=nodes_total)

        p_final = result["p_final"].to_numpy()
        assert np.all((p_final >= 0.0) & (p_final <= 1.0)), (
            "p_final values must all be in [0.0, 1.0]"
        )

    def test_p1_p2_p12_p3_are_in_unit_interval(self, minimal_system):
        system, S2, edges_S2, nodes_total = minimal_system
        pipeline = CascadePipeline("botsim", cfg=system.cfg, embedder=system.embedder)
        result = pipeline.predict(system, S2, edges_S2, nodes_total=nodes_total)

        for col in ("p1", "p2", "p12", "p3"):
            vals = result[col].to_numpy()
            assert np.all((vals >= 0.0) & (vals <= 1.0)), (
                f"{col!r} values must all be in [0.0, 1.0]"
            )


class TestRoutingMaskBehavior:
    """Routing masks (amr_used, stage3_used) must be integer flags, 0 or 1."""

    def test_amr_used_is_integer_flag(self, minimal_system):
        system, S2, edges_S2, nodes_total = minimal_system
        pipeline = CascadePipeline("botsim", cfg=system.cfg, embedder=system.embedder)
        result = pipeline.predict(system, S2, edges_S2, nodes_total=nodes_total)

        amr_used = result["amr_used"].to_numpy()
        assert set(np.unique(amr_used)).issubset({0, 1}), (
            "amr_used must be an integer flag column with values in {0, 1}"
        )

    def test_stage3_used_is_integer_flag(self, minimal_system):
        system, S2, edges_S2, nodes_total = minimal_system
        pipeline = CascadePipeline("botsim", cfg=system.cfg, embedder=system.embedder)
        result = pipeline.predict(system, S2, edges_S2, nodes_total=nodes_total)

        s3_used = result["stage3_used"].to_numpy()
        assert set(np.unique(s3_used)).issubset({0, 1}), (
            "stage3_used must be an integer flag column with values in {0, 1}"
        )

    def test_gate_amr_returns_boolean_array(self):
        rng = np.random.RandomState(0)
        n = 20
        th = StageThresholds()
        p2a = rng.uniform(0.0, 1.0, size=n)
        n2 = rng.uniform(0.0, 5.0, size=n)
        z1 = rng.uniform(-3.0, 3.0, size=n)
        z2a = rng.uniform(-3.0, 3.0, size=n)

        mask = gate_amr(p2a, n2, z1, z2a, th)
        assert mask.dtype == np.bool_ or mask.dtype == bool, (
            "gate_amr must return a boolean array"
        )
        assert mask.shape == (n,), f"gate_amr mask shape mismatch: {mask.shape}"

    def test_gate_stage3_returns_boolean_array(self):
        rng = np.random.RandomState(1)
        n = 20
        th = StageThresholds()
        p12 = rng.uniform(0.0, 1.0, size=n)
        n1 = rng.uniform(0.0, 5.0, size=n)
        n2 = rng.uniform(0.0, 5.0, size=n)

        mask = gate_stage3(p12, n1, n2, th)
        assert mask.dtype == np.bool_ or mask.dtype == bool, (
            "gate_stage3 must return a boolean array"
        )
        assert mask.shape == (n,), f"gate_stage3 mask shape mismatch: {mask.shape}"

    def test_gate_amr_all_false_when_all_confident_low_novelty(self):
        """When all accounts are confidently bot/human and novelty is low, AMR should not activate."""
        n = 20
        th = StageThresholds()
        # Make all accounts confidently bot with low novelty and low disagreement
        p2a = np.full(n, 0.99)   # above s2a_bot=0.95, not uncertain
        n2 = np.zeros(n)          # low novelty
        z1 = np.full(n, 5.0)     # z1 = logit(0.99), bot-leaning
        z2a = np.full(n, 5.0)    # z2a same direction, no disagreement

        mask = gate_amr(p2a, n2, z1, z2a, th)
        assert not mask.any(), (
            "AMR gate must not activate when all accounts are confidently classified with low novelty"
        )

    def test_gate_amr_activates_on_uncertainty(self):
        """AMR gate must activate for uncertain predictions."""
        n = 10
        th = StageThresholds()
        # Uncertain predictions (between s2a_human=0.05 and s2a_bot=0.95)
        p2a = np.full(n, 0.5)
        n2 = np.zeros(n)
        z1 = np.zeros(n)
        z2a = np.zeros(n)

        mask = gate_amr(p2a, n2, z1, z2a, th)
        assert mask.all(), (
            "AMR gate must activate for all uncertain accounts (p2a=0.5)"
        )

    def test_gate_stage3_activates_on_uncertainty(self):
        """Stage 3 gate must activate for uncertain combined predictions."""
        n = 10
        th = StageThresholds()
        # Uncertain predictions
        p12 = np.full(n, 0.5)
        n1 = np.zeros(n)
        n2 = np.zeros(n)

        mask = gate_stage3(p12, n1, n2, th)
        assert mask.all(), (
            "Stage3 gate must activate for all uncertain combined predictions (p12=0.5)"
        )


class TestAMROnlyBehavior:
    """AMR must be the only Stage 2 refinement path (no LSTM); delta-logit only."""

    def test_trained_system_has_amr_refiner_not_lstm(self, minimal_system):
        system, _, _, _ = minimal_system
        # amr_refiner must exist and have the delta-logit interface
        assert system.amr_refiner is not None, (
            "TrainedSystem must have amr_refiner (AMR delta-logit path)"
        )
        assert hasattr(system.amr_refiner, "refine"), (
            "amr_refiner must expose a refine() method"
        )
        assert hasattr(system.amr_refiner, "delta"), (
            "amr_refiner must expose a delta() method for the logit adjustment"
        )

    def test_trained_system_has_no_lstm_attribute(self, minimal_system):
        system, _, _, _ = minimal_system
        assert not hasattr(system, "stage2b_lstm"), (
            "TrainedSystem must not have stage2b_lstm (LSTM path removed in v1.5)"
        )
        assert not hasattr(system, "lstm_refiner"), (
            "TrainedSystem must not have lstm_refiner (LSTM path removed in v1.5)"
        )

    def test_amr_refiner_delta_is_additive_to_base_logit(self, minimal_system):
        """AMR refinement must add a delta to the base logit, not replace it."""
        system, _, _, _ = minimal_system
        rng = np.random.RandomState(99)
        n, d = 5, 384
        h_amr = rng.randn(n, d).astype(np.float32)
        z_base = rng.randn(n).astype(np.float64)

        delta = system.amr_refiner.delta(h_amr)
        refined = system.amr_refiner.refine(z_base, h_amr)

        np.testing.assert_allclose(
            refined,
            z_base + delta,
            rtol=1e-5,
            err_msg="AMR refinement must be z_base + delta(h_amr)",
        )

    def test_cascade_pipeline_has_no_lstm_path(self):
        """CascadePipeline must not expose any LSTM-related attributes."""
        pipeline = CascadePipeline("botsim")
        assert not hasattr(pipeline, "lstm"), (
            "CascadePipeline must not have an lstm attribute"
        )
        assert not hasattr(pipeline, "stage2b_lstm"), (
            "CascadePipeline must not have a stage2b_lstm attribute"
        )
