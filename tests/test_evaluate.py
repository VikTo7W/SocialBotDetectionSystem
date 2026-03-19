"""
Unit tests for evaluate.py — evaluate_s3() function.

Tests cover:
- Return structure (keys "overall", "per_stage", "routing")
- Overall metric values (f1, auc, precision, recall in [0, 1])
- Per-stage metric structure (p1, p2, p12, p_final each with f1/auc/precision/recall)
- Routing statistics structure and invariants
- Routing percentage sum == 100%
- Printed output headers
- Edge case: all-zeros amr_used and stage3_used
"""

import numpy as np
import pandas as pd
import pytest

from evaluate import evaluate_s3


# ---------------------------------------------------------------------------
# Helper: build a hand-crafted minimal results DataFrame
# ---------------------------------------------------------------------------

def _make_results_df(n=50, amr_used=None, stage3_used=None, seed=0):
    """
    Build a minimal results DataFrame matching predict_system() output columns.
    All probabilities are random but reproducible.
    """
    rng = np.random.RandomState(seed)
    if amr_used is None:
        amr_used = rng.randint(0, 2, size=n)
    if stage3_used is None:
        stage3_used = rng.randint(0, 2, size=n)

    return pd.DataFrame({
        "account_id": [f"acc_{i}" for i in range(n)],
        "p1":         rng.uniform(0.0, 1.0, size=n),
        "n1":         rng.uniform(0.0, 5.0, size=n),
        "p2":         rng.uniform(0.0, 1.0, size=n),
        "n2":         rng.uniform(0.0, 5.0, size=n),
        "amr_used":   amr_used.astype(int),
        "p12":        rng.uniform(0.0, 1.0, size=n),
        "stage3_used": stage3_used.astype(int),
        "p3":         rng.uniform(0.0, 1.0, size=n),
        "n3":         rng.uniform(0.0, 5.0, size=n),
        "p_final":    rng.uniform(0.0, 1.0, size=n),
    })


def _make_y_true(n=50, seed=0):
    """Balanced binary labels."""
    y = np.zeros(n, dtype=int)
    y[n // 2:] = 1
    return y


# ---------------------------------------------------------------------------
# Test 1: Return structure — top-level keys
# ---------------------------------------------------------------------------

class TestReturnStructure:
    def test_returns_dict_with_required_keys(self):
        results = _make_results_df()
        y_true = _make_y_true()
        report = evaluate_s3(results, y_true)
        assert isinstance(report, dict)
        assert "overall" in report
        assert "per_stage" in report
        assert "routing" in report


# ---------------------------------------------------------------------------
# Test 2: Overall metrics structure and value ranges
# ---------------------------------------------------------------------------

class TestOverallMetrics:
    def setup_method(self):
        self.results = _make_results_df()
        self.y_true = _make_y_true()
        self.report = evaluate_s3(self.results, self.y_true)

    def test_overall_has_required_keys(self):
        overall = self.report["overall"]
        assert "f1" in overall
        assert "auc" in overall
        assert "precision" in overall
        assert "recall" in overall

    def test_overall_values_are_floats_in_0_1(self):
        overall = self.report["overall"]
        for key in ("f1", "auc", "precision", "recall"):
            val = overall[key]
            assert isinstance(val, float), f"overall[{key!r}] should be float"
            assert 0.0 <= val <= 1.0, f"overall[{key!r}] = {val} not in [0, 1]"


# ---------------------------------------------------------------------------
# Test 3: Per-stage metrics structure
# ---------------------------------------------------------------------------

class TestPerStageMetrics:
    def setup_method(self):
        self.results = _make_results_df()
        self.y_true = _make_y_true()
        self.report = evaluate_s3(self.results, self.y_true)

    def test_per_stage_has_required_stage_keys(self):
        per_stage = self.report["per_stage"]
        for stage in ("p1", "p2", "p12", "p_final"):
            assert stage in per_stage, f"per_stage missing key {stage!r}"

    def test_each_stage_has_metric_keys(self):
        per_stage = self.report["per_stage"]
        for stage in ("p1", "p2", "p12", "p_final"):
            for metric in ("f1", "auc", "precision", "recall"):
                assert metric in per_stage[stage], \
                    f"per_stage[{stage!r}] missing key {metric!r}"

    def test_per_stage_values_in_0_1(self):
        per_stage = self.report["per_stage"]
        for stage in ("p1", "p2", "p12", "p_final"):
            for metric in ("f1", "auc", "precision", "recall"):
                val = per_stage[stage][metric]
                assert isinstance(val, float), \
                    f"per_stage[{stage!r}][{metric!r}] should be float"
                assert 0.0 <= val <= 1.0, \
                    f"per_stage[{stage!r}][{metric!r}] = {val} not in [0, 1]"


# ---------------------------------------------------------------------------
# Test 4: Routing statistics structure and value ranges
# ---------------------------------------------------------------------------

class TestRoutingStatistics:
    def setup_method(self):
        self.results = _make_results_df()
        self.y_true = _make_y_true()
        self.report = evaluate_s3(self.results, self.y_true)

    def test_routing_has_required_keys(self):
        routing = self.report["routing"]
        for key in ("pct_stage1_exit", "pct_stage2_exit", "pct_stage3_exit", "pct_amr_triggered"):
            assert key in routing, f"routing missing key {key!r}"

    def test_routing_values_are_floats_in_0_100(self):
        routing = self.report["routing"]
        for key in ("pct_stage1_exit", "pct_stage2_exit", "pct_stage3_exit", "pct_amr_triggered"):
            val = routing[key]
            assert isinstance(val, float), f"routing[{key!r}] should be float"
            assert 0.0 <= val <= 100.0, f"routing[{key!r}] = {val} not in [0, 100]"


# ---------------------------------------------------------------------------
# Test 5: Routing percentages sum to 100%
# ---------------------------------------------------------------------------

class TestRoutingPercentageInvariant:
    def test_exit_percentages_sum_to_100(self):
        results = _make_results_df()
        y_true = _make_y_true()
        report = evaluate_s3(results, y_true)
        routing = report["routing"]
        total = routing["pct_stage1_exit"] + routing["pct_stage2_exit"] + routing["pct_stage3_exit"]
        assert abs(total - 100.0) < 0.01, \
            f"Exit percentages sum to {total:.4f}, expected 100.0"

    def test_exit_percentages_sum_to_100_with_all_stage3(self):
        """When all accounts go through Stage 3, pct_stage3_exit == 100."""
        n = 40
        amr_used = np.ones(n, dtype=int)
        stage3_used = np.ones(n, dtype=int)
        results = _make_results_df(n=n, amr_used=amr_used, stage3_used=stage3_used)
        y_true = np.array([0] * (n // 2) + [1] * (n // 2))
        report = evaluate_s3(results, y_true)
        routing = report["routing"]
        assert abs(routing["pct_stage3_exit"] - 100.0) < 0.01
        total = routing["pct_stage1_exit"] + routing["pct_stage2_exit"] + routing["pct_stage3_exit"]
        assert abs(total - 100.0) < 0.01


# ---------------------------------------------------------------------------
# Test 6: Printed output contains expected headers
# ---------------------------------------------------------------------------

class TestPrintedOutput:
    def test_output_contains_overall_metrics_header(self, capsys):
        results = _make_results_df()
        y_true = _make_y_true()
        evaluate_s3(results, y_true)
        captured = capsys.readouterr()
        assert "Overall Metrics" in captured.out

    def test_output_contains_per_stage_metrics_header(self, capsys):
        results = _make_results_df()
        y_true = _make_y_true()
        evaluate_s3(results, y_true)
        captured = capsys.readouterr()
        assert "Per-Stage Metrics" in captured.out

    def test_output_contains_routing_statistics_header(self, capsys):
        results = _make_results_df()
        y_true = _make_y_true()
        evaluate_s3(results, y_true)
        captured = capsys.readouterr()
        assert "Routing Statistics" in captured.out


# ---------------------------------------------------------------------------
# Test 7: Edge case — all-zeros amr_used and stage3_used
# ---------------------------------------------------------------------------

class TestEdgeCaseNoAmrNoStage3:
    def test_no_amr_no_stage3_gives_100pct_stage1_exit(self):
        n = 50
        amr_used = np.zeros(n, dtype=int)
        stage3_used = np.zeros(n, dtype=int)
        results = _make_results_df(n=n, amr_used=amr_used, stage3_used=stage3_used)
        y_true = _make_y_true(n)
        report = evaluate_s3(results, y_true)
        routing = report["routing"]
        assert abs(routing["pct_stage1_exit"] - 100.0) < 0.01, \
            f"Expected 100% stage1 exit, got {routing['pct_stage1_exit']:.2f}%"
        assert abs(routing["pct_stage2_exit"] - 0.0) < 0.01, \
            f"Expected 0% stage2 exit, got {routing['pct_stage2_exit']:.2f}%"
        assert abs(routing["pct_stage3_exit"] - 0.0) < 0.01, \
            f"Expected 0% stage3 exit, got {routing['pct_stage3_exit']:.2f}%"
        assert abs(routing["pct_amr_triggered"] - 0.0) < 0.01, \
            f"Expected 0% AMR triggered, got {routing['pct_amr_triggered']:.2f}%"


# ---------------------------------------------------------------------------
# Integration test: using minimal_system fixture from conftest.py
# ---------------------------------------------------------------------------

class TestIntegrationWithMinimalSystem:
    def test_evaluate_s3_with_predict_system_output(self, minimal_system):
        """
        Use the minimal_system fixture to run predict_system and then evaluate_s3.
        Verifies full integration without real data or sentence-transformers.
        """
        from botdetector_pipeline import predict_system

        system, S2, edges_S2, nodes_total = minimal_system
        results = predict_system(system, S2, edges_S2, nodes_total)
        y_true = S2["label"].to_numpy()

        report = evaluate_s3(results, y_true)

        # Structure checks
        assert set(report.keys()) == {"overall", "per_stage", "routing"}
        assert set(report["overall"].keys()) == {"f1", "auc", "precision", "recall"}
        assert set(report["per_stage"].keys()) == {"p1", "p2", "p12", "p_final"}
        for stage in report["per_stage"].values():
            assert set(stage.keys()) == {"f1", "auc", "precision", "recall"}
        assert set(report["routing"].keys()) == {
            "pct_stage1_exit", "pct_stage2_exit", "pct_stage3_exit", "pct_amr_triggered"
        }

        # Invariant check
        routing = report["routing"]
        total = routing["pct_stage1_exit"] + routing["pct_stage2_exit"] + routing["pct_stage3_exit"]
        assert abs(total - 100.0) < 0.01, f"Exit percentages sum to {total:.4f}"
