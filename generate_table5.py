from __future__ import annotations

import json
import os
import sys

from ablation_tables import generate_cross_dataset_table, save_latex

DEFAULT_BOTSIM_METRICS_PATH = os.path.join("paper_outputs", "metrics_botsim.json")
DEFAULT_REDDIT_TRANSFER_METRICS_PATH = os.path.join("paper_outputs", "metrics_reddit_transfer.json")
DEFAULT_TWIBOT_NATIVE_METRICS_PATH = os.path.join("paper_outputs", "metrics_twibot_native.json")
DEFAULT_TABLE5_OUTPUT_PATH = os.path.join("tables", "table5_cross_dataset.tex")


def _load_metrics(path: str) -> dict:
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def generate_table5(
    botsim_metrics_path: str = DEFAULT_BOTSIM_METRICS_PATH,
    reddit_transfer_metrics_path: str = DEFAULT_REDDIT_TRANSFER_METRICS_PATH,
    twibot_native_metrics_path: str = DEFAULT_TWIBOT_NATIVE_METRICS_PATH,
    output_path: str = DEFAULT_TABLE5_OUTPUT_PATH,
) -> str:
    botsim_metrics = _load_metrics(botsim_metrics_path)
    reddit_transfer_metrics = _load_metrics(reddit_transfer_metrics_path)
    twibot_native_metrics = _load_metrics(twibot_native_metrics_path)

    df_t5 = generate_cross_dataset_table(
        botsim_metrics,
        reddit_transfer_metrics,
        twibot_native_metrics,
    )
    save_latex(df_t5, output_path)
    print(f"[table5] Saved LaTeX to {output_path}")
    return output_path


if __name__ == "__main__":
    botsim_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_BOTSIM_METRICS_PATH
    reddit_path = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_REDDIT_TRANSFER_METRICS_PATH
    twibot_path = sys.argv[3] if len(sys.argv) > 3 else DEFAULT_TWIBOT_NATIVE_METRICS_PATH
    out_path = sys.argv[4] if len(sys.argv) > 4 else DEFAULT_TABLE5_OUTPUT_PATH
    generate_table5(botsim_path, reddit_path, twibot_path, out_path)
