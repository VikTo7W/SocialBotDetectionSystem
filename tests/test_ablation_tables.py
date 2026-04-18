"""
Unit tests for ablation_tables.py.

These tests use synthetic metrics dicts and filesystem fixtures so they run
without trained model artifacts or real datasets.
"""

import json
import os

import pandas as pd
import pytest

from ablation_tables import (
    DEFAULT_COMPARISON_PATH,
    DEFAULT_NATIVE_METRICS_PATH,
    DEFAULT_REDDIT_TRANSFER_METRICS_PATH,
    build_reddit_vs_native_comparison_artifact,
    build_transfer_result_interpretation,
    build_table1,
    build_table2,
    build_table3,
    build_table4,
    generate_cross_dataset_table,
    load_twibot20_comparison,
    save_latex,
    write_transfer_result_interpretation,
)


MOCK_V10 = {
    "auc": 0.9500,
    "f1": 0.9000,
    "precision": 0.8800,
    "recall": 0.9200,
    "stage": "S3",
}

MOCK_V12_OVERALL = {
    "f1": 0.9200,
    "auc": 0.9700,
    "precision": 0.9100,
    "recall": 0.9300,
}

MOCK_PER_STAGE = {
    "p1": {"f1": 0.70, "auc": 0.80, "precision": 0.72, "recall": 0.68},
    "p2": {"f1": 0.75, "auc": 0.83, "precision": 0.76, "recall": 0.74},
    "p12": {"f1": 0.85, "auc": 0.90, "precision": 0.86, "recall": 0.84},
    "p_final": {"f1": 0.92, "auc": 0.97, "precision": 0.91, "recall": 0.93},
}

MOCK_ROUTING = {
    "pct_stage1_exit": 40.0,
    "pct_stage2_exit": 35.0,
    "pct_stage3_exit": 25.0,
    "pct_amr_triggered": 60.0,
}

MOCK_GROUP_METRICS = {
    "all_features": {"f1": 0.92, "auc": 0.97, "precision": 0.91, "recall": 0.93},
    "username_length": {"f1": 0.90, "auc": 0.95, "precision": 0.89, "recall": 0.91},
    "post_count": {"f1": 0.88, "auc": 0.94, "precision": 0.87, "recall": 0.89},
    "comment_counts": {"f1": 0.85, "auc": 0.92, "precision": 0.84, "recall": 0.86},
    "subreddit_breadth": {"f1": 0.89, "auc": 0.95, "precision": 0.88, "recall": 0.90},
    "post_comment_ratios": {"f1": 0.86, "auc": 0.93, "precision": 0.85, "recall": 0.87},
}

MOCK_BOTSIM24_FULL = {
    "overall": {"f1": 0.9200, "auc": 0.9700, "precision": 0.9100, "recall": 0.9300},
    "per_stage": MOCK_PER_STAGE,
    "routing": MOCK_ROUTING,
}

MOCK_REDDIT_TRANSFER_FULL = {
    "overall": {"f1": 0.7500, "auc": 0.8200, "precision": 0.7100, "recall": 0.7900},
    "per_stage": {
        "p1": {"f1": 0.60, "auc": 0.70, "precision": 0.62, "recall": 0.58},
        "p2": {"f1": 0.65, "auc": 0.73, "precision": 0.66, "recall": 0.64},
        "p12": {"f1": 0.72, "auc": 0.80, "precision": 0.73, "recall": 0.71},
        "p_final": {"f1": 0.75, "auc": 0.82, "precision": 0.71, "recall": 0.79},
    },
    "routing": {
        "pct_stage1_exit": 50.0,
        "pct_stage2_exit": 30.0,
        "pct_stage3_exit": 20.0,
        "pct_amr_triggered": 50.0,
    },
}

MOCK_TWIBOT20_NATIVE_FULL = {
    "overall": {"f1": 0.7900, "auc": 0.8500, "precision": 0.7500, "recall": 0.8300},
    "per_stage": {
        "p1": {"f1": 0.64, "auc": 0.74, "precision": 0.66, "recall": 0.62},
        "p2": {"f1": 0.68, "auc": 0.77, "precision": 0.70, "recall": 0.66},
        "p12": {"f1": 0.75, "auc": 0.83, "precision": 0.76, "recall": 0.74},
        "p_final": {"f1": 0.79, "auc": 0.85, "precision": 0.75, "recall": 0.83},
    },
    "routing": {
        "pct_stage1_exit": 48.0,
        "pct_stage2_exit": 32.0,
        "pct_stage3_exit": 20.0,
        "pct_amr_triggered": 52.0,
    },
}


def test_table1_shape():
    df = build_table1(MOCK_V10, MOCK_V12_OVERALL)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (4, 3)
    assert list(df.columns) == ["Metric", "v1.0 (leaky)", "v1.1 (clean)"]
    assert list(df["Metric"]) == ["F1", "AUC-ROC", "Precision", "Recall"]


def test_table2_stage_contribution():
    df = build_table2(MOCK_PER_STAGE)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (3, 5)
    assert list(df["Stage"]) == ["Stage 1 only", "Stage 1+2", "Full cascade"]


def test_table3_routing():
    df = build_table3(MOCK_ROUTING)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (4, 2)
    assert abs(df["% Accounts"].iloc[:3].sum() - 100.0) < 1e-9


def test_table4_masking():
    df = build_table4(MOCK_GROUP_METRICS)
    assert isinstance(df, pd.DataFrame)
    assert df.shape == (6, 5)
    assert df["Group"].iloc[0] == "all_features"


def test_latex_format(tmp_path):
    out_path = str(tmp_path / "test.tex")
    save_latex(build_table1(MOCK_V10, MOCK_V12_OVERALL), out_path)
    content = open(out_path, encoding="utf-8").read()
    assert r"\begin{tabular}" in content
    assert r"\end{tabular}" in content
    assert "0.9000" in content


def test_table5_cross_dataset():
    df = generate_cross_dataset_table(
        MOCK_BOTSIM24_FULL,
        MOCK_REDDIT_TRANSFER_FULL,
        MOCK_TWIBOT20_NATIVE_FULL,
    )

    assert isinstance(df, pd.DataFrame)
    assert df.shape == (4, 4)
    assert list(df.columns) == [
        "Metric",
        "BotSim-24 (Reddit, in-dist.)",
        "TwiBot-20 (Reddit transfer)",
        "TwiBot-20 (TwiBot-native)",
    ]
    assert df.loc[df["Metric"] == "F1", "TwiBot-20 (Reddit transfer)"].iloc[0] == 0.7500
    assert df.loc[df["Metric"] == "F1", "TwiBot-20 (TwiBot-native)"].iloc[0] == 0.7900


def test_table5_uses_overall_key():
    botsim = {"overall": {"f1": 0.91, "auc": 0.96, "precision": 0.90, "recall": 0.92}, "per_stage": {}, "routing": {}}
    reddit_transfer = {"overall": {"f1": 0.74, "auc": 0.81, "precision": 0.70, "recall": 0.78}, "per_stage": {}, "routing": {}}
    native = {"overall": {"f1": 0.79, "auc": 0.85, "precision": 0.75, "recall": 0.83}, "per_stage": {}, "routing": {}}
    df = generate_cross_dataset_table(botsim, reddit_transfer, native)
    assert df.loc[df["Metric"] == "F1", "BotSim-24 (Reddit, in-dist.)"].iloc[0] == 0.91
    assert df.loc[df["Metric"] == "F1", "TwiBot-20 (Reddit transfer)"].iloc[0] == 0.74
    assert df.loc[df["Metric"] == "F1", "TwiBot-20 (TwiBot-native)"].iloc[0] == 0.79


def test_table5_latex(tmp_path):
    df = generate_cross_dataset_table(
        MOCK_BOTSIM24_FULL,
        MOCK_REDDIT_TRANSFER_FULL,
        MOCK_TWIBOT20_NATIVE_FULL,
    )
    out_path = str(tmp_path / "table5.tex")
    save_latex(df, out_path)
    content = open(out_path, encoding="utf-8").read()
    assert "BotSim-24" in content
    assert "TwiBot-20 (Reddit transfer)" in content
    assert "TwiBot-20 (TwiBot-native)" in content
    assert "0.7900" in content


def test_load_twibot20_comparison_reads_conditions(tmp_path):
    path = tmp_path / "metrics_twibot20_reddit_vs_native.json"
    payload = {
        "comparison_type": "reddit_transfer_vs_twibot_native",
        "conditions": {
            "reddit_transfer": MOCK_REDDIT_TRANSFER_FULL,
            "twibot_native": MOCK_TWIBOT20_NATIVE_FULL,
        },
        "delta_overall": {"f1": 0.04, "auc": 0.03, "precision": 0.04, "recall": 0.04},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    loaded = load_twibot20_comparison(str(path))
    assert loaded["comparison_type"] == "reddit_transfer_vs_twibot_native"
    assert set(loaded["conditions"].keys()) == {"reddit_transfer", "twibot_native"}


def test_build_reddit_vs_native_comparison_artifact_schema():
    comparison = build_reddit_vs_native_comparison_artifact(
        reddit_transfer_metrics=MOCK_REDDIT_TRANSFER_FULL,
        twibot20_native_metrics=MOCK_TWIBOT20_NATIVE_FULL,
        reddit_metrics_path=DEFAULT_REDDIT_TRANSFER_METRICS_PATH,
        native_metrics_path=DEFAULT_NATIVE_METRICS_PATH,
    )
    assert comparison["comparison_type"] == "reddit_transfer_vs_twibot_native"
    assert comparison["sources"]["reddit_transfer_metrics_path"] == DEFAULT_REDDIT_TRANSFER_METRICS_PATH
    assert comparison["sources"]["twibot_native_metrics_path"] == DEFAULT_NATIVE_METRICS_PATH
    assert comparison["delta_overall"]["f1"] == pytest.approx(0.04)


def test_build_transfer_result_interpretation_uses_live_deltas():
    comparison = {
        "comparison_type": "reddit_transfer_vs_twibot_native",
        "conditions": {
            "reddit_transfer": MOCK_REDDIT_TRANSFER_FULL,
            "twibot_native": MOCK_TWIBOT20_NATIVE_FULL,
        },
        "delta_overall": {"f1": 0.04, "auc": 0.03, "precision": 0.04, "recall": 0.04},
    }
    text = build_transfer_result_interpretation(comparison)
    assert "Comparison result: improved." in text
    assert "Reddit transfer 0.7500 -> TwiBot-native 0.7900" in text
    assert "Source artifact: reddit_transfer_vs_twibot_native." in text


def test_write_transfer_result_interpretation_persists_text():
    comparison = {
        "comparison_type": "reddit_transfer_vs_twibot_native",
        "conditions": {
            "reddit_transfer": MOCK_REDDIT_TRANSFER_FULL,
            "twibot_native": {
                **MOCK_TWIBOT20_NATIVE_FULL,
                "overall": {"f1": 0.7560, "auc": 0.8230, "precision": 0.7140, "recall": 0.7960},
            },
        },
        "delta_overall": {"f1": 0.006, "auc": 0.003, "precision": 0.004, "recall": 0.006},
    }
    path = os.path.join(os.getcwd(), "phase16_transfer_interpretation_test.txt")
    try:
        write_transfer_result_interpretation(comparison, str(path))
        content = open(path, encoding="utf-8").read()
        assert "Comparison result: no_material_change." in content
        assert "Reddit transfer 0.7500 -> TwiBot-native 0.7560" in content
        assert DEFAULT_COMPARISON_PATH.endswith("metrics_twibot20_reddit_vs_native.json")
    finally:
        if os.path.exists(path):
            os.remove(path)
