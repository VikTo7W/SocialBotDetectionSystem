from __future__ import annotations

import json
import os

import pandas as pd
import pytest

from ablation_tables import generate_cross_dataset_table, save_latex
from generate_table5 import (
    DEFAULT_BOTSIM_METRICS_PATH,
    DEFAULT_REDDIT_TRANSFER_METRICS_PATH,
    DEFAULT_TWIBOT_NATIVE_METRICS_PATH,
    DEFAULT_TABLE5_OUTPUT_PATH,
    generate_table5,
)


def _minimal_metrics():
    return {
        "overall": {"f1": 0.8, "auc": 0.85, "precision": 0.75, "recall": 0.85},
        "per_stage": {
            "p1": {"f1": 0.7, "auc": 0.75, "precision": 0.65, "recall": 0.75},
            "p2": {"f1": 0.7, "auc": 0.75, "precision": 0.65, "recall": 0.75},
            "p12": {"f1": 0.75, "auc": 0.80, "precision": 0.70, "recall": 0.80},
            "p_final": {"f1": 0.8, "auc": 0.85, "precision": 0.75, "recall": 0.85},
        },
        "routing": {
            "pct_stage1_exit": 60.0,
            "pct_stage2_exit": 20.0,
            "pct_stage3_exit": 20.0,
            "pct_amr_triggered": 25.0,
        },
    }


def test_generate_cross_dataset_table_column_headers():
    df = generate_cross_dataset_table(_minimal_metrics(), _minimal_metrics(), _minimal_metrics())
    assert list(df.columns) == [
        "Metric",
        "BotSim-24 (Reddit, in-dist.)",
        "TwiBot-20 (Reddit transfer)",
        "TwiBot-20 (TwiBot-native)",
    ]
    assert len(df) == 4


def test_generate_table5_writes_tex_file(tmp_path):
    metrics = _minimal_metrics()
    botsim_path = tmp_path / "metrics_botsim.json"
    reddit_path = tmp_path / "metrics_reddit_transfer.json"
    twibot_path = tmp_path / "metrics_twibot_native.json"
    output_path = tmp_path / "table5_cross_dataset.tex"

    for path in (botsim_path, reddit_path, twibot_path):
        path.write_text(json.dumps(metrics), encoding="utf-8")

    generate_table5(
        str(botsim_path),
        str(reddit_path),
        str(twibot_path),
        str(output_path),
    )

    assert output_path.exists()
    assert "BotSim-24" in output_path.read_text(encoding="utf-8")


def test_generate_table5_returns_output_path(tmp_path):
    metrics = _minimal_metrics()
    botsim_path = tmp_path / "metrics_botsim.json"
    reddit_path = tmp_path / "metrics_reddit_transfer.json"
    twibot_path = tmp_path / "metrics_twibot_native.json"
    output_path = tmp_path / "table5_cross_dataset.tex"

    for path in (botsim_path, reddit_path, twibot_path):
        path.write_text(json.dumps(metrics), encoding="utf-8")

    returned = generate_table5(
        str(botsim_path),
        str(reddit_path),
        str(twibot_path),
        str(output_path),
    )

    assert returned == str(output_path)


def test_generate_table5_defaults_point_to_paper_outputs():
    assert os.path.normpath(DEFAULT_BOTSIM_METRICS_PATH).endswith(os.path.join("paper_outputs", "metrics_botsim.json"))
    assert os.path.normpath(DEFAULT_REDDIT_TRANSFER_METRICS_PATH).endswith(os.path.join("paper_outputs", "metrics_reddit_transfer.json"))
    assert os.path.normpath(DEFAULT_TWIBOT_NATIVE_METRICS_PATH).endswith(os.path.join("paper_outputs", "metrics_twibot_native.json"))
    assert os.path.normpath(DEFAULT_TABLE5_OUTPUT_PATH).endswith(os.path.join("tables", "table5_cross_dataset.tex"))


def test_generate_table5_raises_on_missing_metrics_file(tmp_path):
    output_path = tmp_path / "table5_cross_dataset.tex"
    with pytest.raises((FileNotFoundError, OSError)):
        generate_table5(
            str(tmp_path / "missing_botsim.json"),
            str(tmp_path / "missing_transfer.json"),
            str(tmp_path / "missing_twibot.json"),
            str(output_path),
        )
