# Phase 10: Evaluation Metrics and Paper Table - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 10-evaluation-metrics-and-paper-table
**Areas discussed:** Script structure, BotSim-24 source for table, LaTeX table format

---

## Script Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Expand evaluate_twibot20.py | Adds evaluate_twibot20() function + expands __main__; single file handles inference and evaluation | ✓ |
| New evaluate_twibot20_metrics.py | Separate evaluation script, cleaner separation but adds a second file | |
| Add to ablation_tables.py | Inference + evaluation folded into ablation_tables.py main() | |

**User's choice:** Expand evaluate_twibot20.py
**Notes:** Phase 10 adds evaluate_twibot20() function below run_inference(). __main__ block expanded to call evaluate_s3() and save metrics_twibot20.json.

---

## Output of `python evaluate_twibot20.py`

| Option | Description | Selected |
|--------|-------------|----------|
| Inference + full eval report + JSON | Prints evaluate_s3() report, saves results_twibot20.json (Phase 9) and metrics_twibot20.json | ✓ |
| Inference + eval report only (no metrics JSON) | Prints report to stdout only, no separate metrics file | |

**User's choice:** Inference + full eval report + JSON
**Notes:** metrics_twibot20.json mirrors evaluate_s3() return structure for use by ablation_tables.py.

---

## BotSim-24 Source for Cross-Dataset Table

| Option | Description | Selected |
|--------|-------------|----------|
| Load from metrics_twibot20.json + ablation_tables live run | generate_cross_dataset_table() takes pre-computed dicts; ablation_tables.py:main() reads metrics_twibot20.json | ✓ |
| Both computed live inside ablation_tables.py | ablation_tables.py:main() calls run_inference() for TwiBot-20 at runtime | |
| Hardcoded BotSim-24 paper values | BotSim-24 metrics hardcoded in generate_cross_dataset_table() | |

**User's choice:** Load from metrics_twibot20.json + ablation_tables live run
**Notes:** Consistent with build_table1/2/3/4 pattern — function is a pure formatter, no inference inside.

---

## LaTeX Table Format — Rows

| Option | Description | Selected |
|--------|-------------|----------|
| F1, AUC-ROC, Precision, Recall + p_final only | 4 overall metric rows, p_final only — clean cross-dataset comparison | ✓ |
| F1, AUC-ROC, Precision, Recall + all 4 stages | 4 metrics × 4 stage columns — more complete but large | |
| F1 + AUC-ROC only (compact) | Two most-cited metrics only | |

**User's choice:** F1, AUC-ROC, Precision, Recall + p_final only

---

## LaTeX Table Format — Columns

| Option | Description | Selected |
|--------|-------------|----------|
| BotSim-24 (Reddit, in-dist.) \| TwiBot-20 (Twitter, zero-shot) | Full context labels, self-contained | ✓ |
| BotSim-24 \| TwiBot-20 | Short labels only | |
| In-Distribution (Reddit) \| Zero-Shot (Twitter) | Emphasizes evaluation paradigm | |

**User's choice:** BotSim-24 (Reddit, in-dist.) | TwiBot-20 (Twitter, zero-shot)
**Notes:** Table 5 is self-contained — reader sees platform and evaluation type without needing the caption.

---

## LaTeX Output Path

| Option | Description | Selected |
|--------|-------------|----------|
| tables/table5_cross_dataset.tex | Continues tables/table{N}.tex naming convention | ✓ |
| tables/cross_dataset_comparison.tex | Descriptive name, breaks numbered convention | |

**User's choice:** tables/table5_cross_dataset.tex

---

## Claude's Discretion

- Full `evaluate_s3()` dict vs `overall` only as return value of `evaluate_twibot20()`
- Print formatting for metrics_twibot20.json save confirmation
- Row label formatting in generate_cross_dataset_table() (e.g., "F1" vs "F1 Score")

## Deferred Ideas

None.
