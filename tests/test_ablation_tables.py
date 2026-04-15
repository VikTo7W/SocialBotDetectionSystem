"""
Unit tests for ablation_tables.py — Wave 0 stubs.

Tests use synthetic dicts that mirror the exact structure of evaluate_s3() output
and results_v10.json. They run without trained_system_v12.joblib or real data.

All tests will fail with ImportError until Plan 02 creates ablation_tables.py.
That is the expected RED state.
"""

import pandas as pd
from ablation_tables import build_table1, build_table2, build_table3, build_table4, save_latex

# ---------------------------------------------------------------------------
# Module-level synthetic fixtures (plain dicts, no pytest fixtures needed)
# ---------------------------------------------------------------------------

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
    "p1":      {"f1": 0.70, "auc": 0.80, "precision": 0.72, "recall": 0.68},
    "p2":      {"f1": 0.75, "auc": 0.83, "precision": 0.76, "recall": 0.74},
    "p12":     {"f1": 0.85, "auc": 0.90, "precision": 0.86, "recall": 0.84},
    "p_final": {"f1": 0.92, "auc": 0.97, "precision": 0.91, "recall": 0.93},
}

MOCK_ROUTING = {
    "pct_stage1_exit": 40.0,
    "pct_stage2_exit": 35.0,
    "pct_stage3_exit": 25.0,
    "pct_amr_triggered": 60.0,
}

MOCK_GROUP_METRICS = {
    "all_features":        {"f1": 0.92, "auc": 0.97, "precision": 0.91, "recall": 0.93},
    "username_length":     {"f1": 0.90, "auc": 0.95, "precision": 0.89, "recall": 0.91},
    "post_count":          {"f1": 0.88, "auc": 0.94, "precision": 0.87, "recall": 0.89},
    "comment_counts":      {"f1": 0.85, "auc": 0.92, "precision": 0.84, "recall": 0.86},
    "subreddit_breadth":   {"f1": 0.89, "auc": 0.95, "precision": 0.88, "recall": 0.90},
    "post_comment_ratios": {"f1": 0.86, "auc": 0.93, "precision": 0.85, "recall": 0.87},
}

# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_table1_shape():
    """Table 1: Leakage audit — v1.0 vs v1.1 overall S3 metrics side-by-side."""
    df = build_table1(MOCK_V10, MOCK_V12_OVERALL)

    assert isinstance(df, pd.DataFrame), "build_table1 must return a pd.DataFrame"
    assert df.shape == (4, 3), f"Expected shape (4, 3), got {df.shape}"
    assert list(df.columns) == ["Metric", "v1.0 (leaky)", "v1.1 (clean)"], (
        f"Unexpected columns: {list(df.columns)}"
    )
    assert list(df["Metric"]) == ["F1", "AUC-ROC", "Precision", "Recall"], (
        f"Unexpected Metric column values: {list(df['Metric'])}"
    )
    assert df.loc[df["Metric"] == "F1", "v1.0 (leaky)"].iloc[0] == 0.9000, (
        "v1.0 F1 value should be 0.9000"
    )
    assert df.loc[df["Metric"] == "AUC-ROC", "v1.1 (clean)"].iloc[0] == 0.9700, (
        "v1.1 AUC-ROC value should be 0.9700"
    )


def test_table2_stage_contribution():
    """Table 2: Stage contribution — p1, p12, p_final rows only (NOT p2)."""
    df = build_table2(MOCK_PER_STAGE)

    assert isinstance(df, pd.DataFrame), "build_table2 must return a pd.DataFrame"
    assert df.shape == (3, 5), f"Expected shape (3, 5), got {df.shape}"
    assert list(df.columns) == ["Stage", "F1", "AUC-ROC", "Precision", "Recall"], (
        f"Unexpected columns: {list(df.columns)}"
    )
    assert list(df["Stage"]) == ["Stage 1 only", "Stage 1+2", "Full cascade"], (
        f"Unexpected Stage column values: {list(df['Stage'])}"
    )
    full_cascade_f1 = df.loc[df["Stage"] == "Full cascade", "F1"].iloc[0]
    assert full_cascade_f1 == 0.92, f"Full cascade F1 should be 0.92, got {full_cascade_f1}"


def test_table3_routing():
    """Table 3: Routing efficiency — stage exit percentages and AMR trigger rate."""
    df = build_table3(MOCK_ROUTING)

    assert isinstance(df, pd.DataFrame), "build_table3 must return a pd.DataFrame"
    assert df.shape == (4, 2), f"Expected shape (4, 2), got {df.shape}"
    assert list(df.columns) == ["Exit Point", "% Accounts"], (
        f"Unexpected columns: {list(df.columns)}"
    )
    # The three stage exit percentages must sum to 100.0 (exhaustive partition)
    stage_exit_sum = df["% Accounts"].iloc[:3].sum()
    assert abs(stage_exit_sum - 100.0) < 1e-9, (
        f"First three '% Accounts' values must sum to 100.0, got {stage_exit_sum}"
    )


def test_table4_masking():
    """Table 4: Stage 1 feature group ablation — baseline + 5 masked groups."""
    df = build_table4(MOCK_GROUP_METRICS)

    assert isinstance(df, pd.DataFrame), "build_table4 must return a pd.DataFrame"
    assert df.shape == (6, 5), f"Expected shape (6, 5), got {df.shape}"
    assert list(df.columns) == ["Group", "F1", "AUC-ROC", "Precision", "Recall"], (
        f"Unexpected columns: {list(df.columns)}"
    )
    assert df["Group"].iloc[0] == "all_features", (
        f"First row Group should be 'all_features' (baseline), got {df['Group'].iloc[0]!r}"
    )
    assert len(df) == 6, f"Expected 6 rows (1 baseline + 5 masked groups), got {len(df)}"
    assert df["F1"].nunique() > 1, (
        "Not all F1 values should be identical — metrics must differ across groups"
    )


def test_latex_format(tmp_path):
    """LaTeX export: save_latex writes valid tabular environment to file."""
    out_path = str(tmp_path / "test.tex")
    df = build_table1(MOCK_V10, MOCK_V12_OVERALL)
    save_latex(df, out_path)

    import os
    assert os.path.exists(out_path), f"LaTeX file not found at {out_path}"

    content = open(out_path).read()
    assert r"\begin{tabular}" in content, (
        r"LaTeX output must contain \begin{tabular}"
    )
    assert r"\end{tabular}" in content, (
        r"LaTeX output must contain \end{tabular}"
    )
    assert "0.9000" in content, (
        "float_format='%.4f' must format 0.9 as '0.9000' in output"
    )


def test_latex_all_tables(tmp_path):
    """LaTeX export: all four tables produce valid .tex files."""
    tables = [
        build_table1(MOCK_V10, MOCK_V12_OVERALL),
        build_table2(MOCK_PER_STAGE),
        build_table3(MOCK_ROUTING),
        build_table4(MOCK_GROUP_METRICS),
    ]

    for i, df in enumerate(tables, start=1):
        path = str(tmp_path / f"table{i}.tex")
        save_latex(df, path)

        import os
        assert os.path.exists(path), f"LaTeX file table{i}.tex not found at {path}"
        content = open(path).read()
        assert r"\begin{tabular}" in content, (
            rf"table{i}.tex must contain \begin{{tabular}}"
        )
