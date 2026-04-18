# Phase 10: Cross-Domain Evaluation and Paper Output - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning

<domain>
## Phase Boundary

Produce the Phase 10 evaluation evidence for TwiBot-20 using the current live transfer path. In the current codebase, the meaningful before/after comparison is:

1. revised TwiBot adapter with static thresholds
2. revised TwiBot adapter with Phase 9 online recalibration enabled

This phase should not resurrect the old demographic-proxy adapter. Phase 8 already replaced it, and Phase 9 added the online-calibration toggle needed for a controlled before/after comparison.

Outputs should include:
- structured before/after TwiBot metrics
- persisted JSON artifacts for both TwiBot conditions
- a paper-ready LaTeX cross-dataset table that includes BotSim-24 in-domain performance and TwiBot-20 zero-shot performance

Out of scope:
- retraining any model
- changing `evaluate.py` metric definitions
- redesigning the TwiBot adapter again
- revisiting Phase 9 calibration logic itself

</domain>

<decisions>
## Implementation Decisions

### Interpretation of "Before/After"

- **D-01:** Because the old demographic-proxy adapter has been superseded by Phase 8, Phase 10 interprets "before/after" as `online_calibration=False` versus `online_calibration=True` on the current revised adapter.
- **D-02:** Phase 10 should preserve this comparison directly in code and artifacts rather than relying on older saved files with different semantics.

### Evaluation Output Shape

- **D-03:** `evaluate_twibot20.py` should expose a comparison-oriented entry point that can run both conditions and return a structured dict suitable for JSON persistence.
- **D-04:** The two TwiBot conditions should be named clearly, e.g. `static_thresholds` and `online_recalibrated`, so downstream reporting is self-explanatory.
- **D-05:** Existing `run_inference()` and `evaluate_twibot20()` functions should remain usable; Phase 10 adds orchestration on top of them rather than replacing them.

### Artifact Strategy

- **D-06:** Persist separate TwiBot metric artifacts for the two conditions or a single combined comparison artifact; either is acceptable as long as downstream table generation has a stable source of truth.
- **D-07:** The paper-table generator should consume persisted metrics, not rerun TwiBot inference internally.

### Table Format

- **D-08:** The LaTeX cross-dataset table should be generated from live BotSim-24 metrics plus TwiBot-20 zero-shot metrics.
- **D-09:** Since Phase 9 added an explicit before/after TwiBot condition, the most useful table shape is:
  - BotSim-24 (Reddit, in-dist.)
  - TwiBot-20 static thresholds
  - TwiBot-20 online recalibrated
- **D-10:** Table rows remain the headline overall metrics: F1, AUC-ROC, Precision, Recall.

### Claude's Discretion

- Whether the comparison helper lives in `evaluate_twibot20.py` as `compare_twibot20_conditions()` or similar
- Whether to persist two JSON files plus one comparison JSON, or just one comparison JSON
- Whether to print a compact before/after delta summary in addition to the existing `evaluate_s3()` report

</decisions>

<canonical_refs>
## Canonical References

### Live TwiBot inference path
- `evaluate_twibot20.py` - revised adapter plus Phase 9 online calibration toggle
- `twibot20_io.py` - TwiBot labels, messages, domains, and graph edges

### Metric engine and current reporting
- `evaluate.py` - `evaluate_s3()` return structure and print format
- `ablation_tables.py` - current cross-dataset table helper pattern and LaTeX export path

### Current milestone state
- `.planning/workstreams/milestone/ROADMAP.md` - Phase 10 goal/success criteria
- `.planning/REQUIREMENTS.md` - `EVAL-01`, `EVAL-02`
- `.planning/workstreams/milestone/STATE.md` - current resume point and blockers

### Useful prior analog
- `.planning/milestones/ws-twibot-intergration-2026-04-16/phases/10-evaluation-metrics-and-paper-table/`
  - prior TwiBot Phase 10 split and table-building approach
  - useful for structure, but not authoritative on current before/after semantics

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets

- `run_inference(path, model_path, online_calibration, window_size)` already supports the two TwiBot conditions Phase 10 needs
- `evaluate_twibot20(path, model_path, threshold)` already wraps `run_inference()` + `evaluate_s3()` for one condition
- `generate_cross_dataset_table()` already exists in `ablation_tables.py`, but it currently expects one TwiBot metric dict and may need expansion for the two-condition comparison
- `save_latex()` already handles table export

### Established Patterns

- evaluation helpers return plain dicts suitable for JSON serialization
- `ablation_tables.py` builds DataFrames first, then prints and exports LaTeX
- metric JSON artifacts are already used as inputs to later paper/report code

### Integration Points

- `evaluate_twibot20.py` should become the source of truth for TwiBot static vs recalibrated metrics
- `ablation_tables.py` should consume the new TwiBot comparison artifact(s)
- Phase 10 should not alter `evaluate.py`; only orchestrate and format around it

</code_context>

<specifics>
## Specific Ideas

- Plan split:
  - **10-01**: add a TwiBot comparison runner and JSON outputs for static vs recalibrated conditions
  - **10-02**: update `ablation_tables.py` to generate the final cross-dataset LaTeX table from BotSim-24 + both TwiBot conditions
- Current environment still has local Windows permission issues affecting full pytest/runtime verification; Phase 10 plans should expect honest partial verification if that remains unresolved

</specifics>

<deferred>
## Deferred Ideas

- any threshold search beyond the Phase 9 percentile rule
- any TwiBot retraining baseline
- any Twitter-native redesign of Stage 2 or Stage 3

</deferred>

---

*Phase: 10-cross-domain-evaluation-and-paper-output*
*Context gathered: 2026-04-18*
