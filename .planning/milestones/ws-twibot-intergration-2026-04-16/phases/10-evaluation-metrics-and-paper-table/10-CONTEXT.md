# Phase 10: Evaluation Metrics and Paper Table - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver full evaluation metrics for TwiBot-20 zero-shot inference and a paper-ready cross-dataset LaTeX table. Expands `evaluate_twibot20.py` with an `evaluate_twibot20()` function that calls `evaluate_s3()`, saves `metrics_twibot20.json`, and adds `generate_cross_dataset_table()` to `ablation_tables.py`.

**Out of scope:** Any changes to `evaluate_s3()`, `evaluate.py`, or any existing pipeline file. Phase 10 is additive only — two new functions, one new JSON file, one new LaTeX file.

</domain>

<decisions>
## Implementation Decisions

### Script Structure
- **D-01:** Phase 10 expands `evaluate_twibot20.py` (not a new file). Adds an `evaluate_twibot20()` function that calls `run_inference()` then `evaluate_s3()`, and expands `__main__` to call it and save `metrics_twibot20.json`.
- **D-02:** Running `python evaluate_twibot20.py` after Phase 10 produces three outputs:
  1. The `evaluate_s3()` paper-ready report printed to stdout (same style as `main.py`)
  2. `results_twibot20.json` — inference results (already done in Phase 9)
  3. `metrics_twibot20.json` — `evaluate_s3()` return dict saved as JSON for use by `ablation_tables.py`
- **D-03:** `evaluate_twibot20()` is an importable function (parallel to `run_inference()`). `ablation_tables.py` imports it if needed, but for Phase 10 `ablation_tables.py` reads `metrics_twibot20.json` directly.

### BotSim-24 Metrics Source for Cross-Dataset Table
- **D-04:** `generate_cross_dataset_table(botsim24_metrics: dict, twibot20_metrics: dict) -> pd.DataFrame` accepts pre-computed metric dicts as parameters. No inference inside the function — pure table formatter, consistent with `build_table1/2/3/4` pattern.
- **D-05:** `ablation_tables.py:main()` calls `generate_cross_dataset_table(report, twibot20_metrics)` where:
  - `report` = already-computed BotSim-24 `evaluate_s3()` result from the live main() run (no duplication)
  - `twibot20_metrics` = loaded from `metrics_twibot20.json` (written by `evaluate_twibot20.py`)
- **D-06:** Both metric dicts use the full `evaluate_s3()` return structure: `{"overall": {...}, "per_stage": {...}, "routing": {...}}`. `generate_cross_dataset_table()` reads `metrics["overall"]` for the table rows.

### LaTeX Table Format
- **D-07:** Table rows: F1, AUC-ROC, Precision, Recall (4 rows, `p_final` only). Per-stage breakdown (p1, p12) is NOT in this table — it would be a separate table if needed.
- **D-08:** Table columns: `BotSim-24 (Reddit, in-dist.)` and `TwiBot-20 (Twitter, zero-shot)` — full context labels, self-contained.
- **D-09:** LaTeX output saved to `tables/table5_cross_dataset.tex` — continues the existing `tables/table{N}.tex` naming convention.
- **D-10:** `save_latex()` in `ablation_tables.py` is reused for the output (already exists, no new function needed).

### Claude's Discretion
- Whether `evaluate_twibot20()` returns the full `evaluate_s3()` dict or just `overall` — Claude decides (return full dict for consistency with `evaluate_s3()` pattern)
- Print formatting details for `metrics_twibot20.json` save confirmation — Claude decides
- `generate_cross_dataset_table()` row label formatting (e.g., "F1" vs "F1 Score") — Claude decides, aim for consistency with existing tables

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Existing Evaluation Infrastructure
- `evaluate.py` — `evaluate_s3(results, y_true, threshold)` full signature and return dict structure; this is the core metric engine Phase 10 calls
- `ablation_tables.py` — `build_table1/2/3/4`, `save_latex()`, `main()` — patterns to follow for `generate_cross_dataset_table()`; `main()` shows how BotSim-24 metrics are computed and passed to table builders

### Phase 9 Output (Phase 10 input)
- `evaluate_twibot20.py` — `run_inference()` function Phase 10 calls; `__main__` block Phase 10 expands
- `.planning/workstreams/twibot-intergration/phases/09-zero-shot-inference-pipeline/09-02-SUMMARY.md` — what Phase 9 built

### Requirements
- `.planning/workstreams/twibot-intergration/REQUIREMENTS.md` — TW-06 and TW-07 (evaluation metrics and cross-dataset table)
- `.planning/workstreams/twibot-intergration/ROADMAP.md` — Phase 10 success criteria

### Data Layer
- `twibot20_io.py` — `load_accounts()["label"]` provides ground truth labels for `evaluate_s3()`

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `evaluate_s3(results, y_true, threshold)` — drop-in metric engine; Phase 10 calls this with TwiBot-20 results and `accounts_df["label"].to_numpy()`
- `save_latex(df, path)` in `ablation_tables.py` line 169 — reused for `table5_cross_dataset.tex`
- `build_table1(v10_metrics, v12_overall)` pattern — `generate_cross_dataset_table()` follows the same two-dict API
- `run_inference()` from `evaluate_twibot20.py` — Phase 10's `evaluate_twibot20()` calls this internally

### Established Patterns
- `ablation_tables.py:main()` computes BotSim-24 metrics as `report = evaluate_s3(out, y_true)` at line 289 — `generate_cross_dataset_table()` receives this as `botsim24_metrics`
- All table builders return `pd.DataFrame`; `main()` prints then calls `save_latex()` — same pattern for Table 5
- `metrics_twibot20.json` will mirror the `evaluate_s3()` return structure: `{"overall": {...}, "per_stage": {...}, "routing": {...}}`

### Integration Points
- `evaluate_twibot20.py` `__main__` block: expand to call `evaluate_twibot20()` and save `metrics_twibot20.json`
- `ablation_tables.py:main()`: add `json.load("metrics_twibot20.json")` + `generate_cross_dataset_table()` call + `save_latex()` for Table 5 after Table 4

</code_context>

<specifics>
## Specific Ideas

- `generate_cross_dataset_table()` signature: `generate_cross_dataset_table(botsim24_metrics: dict, twibot20_metrics: dict) -> pd.DataFrame` — takes full `evaluate_s3()` return dicts, reads `["overall"]` internally
- Table 5 columns: `"BotSim-24 (Reddit, in-dist.)"` and `"TwiBot-20 (Twitter, zero-shot)"` — these are the exact column header strings
- Table 5 rows: Metric (F1 / AUC-ROC / Precision / Recall), one row each, values from `metrics["overall"]`
- `evaluate_twibot20()` function adds to `evaluate_twibot20.py` below `run_inference()` and calls `run_inference()` internally — consistent with D-01

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 10-evaluation-metrics-and-paper-table*
*Context gathered: 2026-04-16*
