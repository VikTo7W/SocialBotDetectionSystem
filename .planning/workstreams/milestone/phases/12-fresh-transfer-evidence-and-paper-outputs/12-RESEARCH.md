# Phase 12: Fresh Transfer Evidence and Paper Outputs - Research

**Researched:** 2026-04-18
**Domain:** Live evidence generation for existing TwiBot evaluation code
**Confidence:** HIGH

---

## Summary

Phase 12 should not introduce new transfer logic. The current code already supports the exact evaluation modes this phase needs:

- static thresholds via `online_calibration=False`
- recalibrated thresholds via `online_calibration=True`
- fresh artifact output via the Phase 11 `output_dir` hardening
- downstream table consumption through `TWIBOT_COMPARISON_PATH`

The main gap is evidence freshness, not missing implementation. The repo still contains stale TwiBot outputs at the project root, and the current milestone state explicitly says fresh evidence is pending. So Phase 12 should be organized around running the current system, capturing the generated artifacts, and recording the observed deltas in a stable evidence summary.

## Verified Current Behavior

- `evaluate_twibot20.py` now supports:
  - `python evaluate_twibot20.py <test_json> <model_joblib> [output_dir]`
  - fresh writes to an explicit output directory
  - `metrics_twibot20_comparison.json` containing both static and recalibrated metrics
- `ablation_tables.py` now supports:
  - `TWIBOT_COMPARISON_PATH`
  - generating Table 5 from the fresh comparison artifact rather than only from cwd

## Planning Implications

### Plan 12-01 should be an execution-and-capture plan

It should:

- run the Phase 11-hardened TwiBot evaluation command against `test.json` and `trained_system_v12.joblib`
- direct outputs into a milestone-owned evidence directory
- confirm that all three TwiBot artifacts exist after the run
- extract the key metrics from the comparison artifact
- write a concise evidence JSON/markdown artifact that states:
  - static overall metrics
  - recalibrated overall metrics
  - delta metrics
  - a one-line interpretation of whether recalibration helped

### Plan 12-02 should be a consume-and-publish plan

It should:

- point `ablation_tables.py` at the fresh comparison artifact
- regenerate `tables/table5_cross_dataset.tex`
- verify that the regenerated table reflects the live static and recalibrated TwiBot metrics
- write a milestone-facing paper-output summary that links the fresh evidence and the regenerated table

## Recommended Artifact Strategy

Use a milestone-owned directory under the repo, rather than the root or a temp directory.

Recommended shape:

```text
phase12_outputs/
  results_twibot20.json
  metrics_twibot20.json
  metrics_twibot20_comparison.json
  transfer_evidence_summary.json
  transfer_evidence_summary.md
```

This keeps the evidence explicit and avoids ambiguity between stale root-level artifacts and current milestone outputs.

## Pitfalls

### Pitfall 1: Treating stale root artifacts as fresh evidence

The project root already contains TwiBot outputs from older runs. Phase 12 must not treat those as current evidence.

### Pitfall 2: Regenerating the table from the wrong artifact path

If `TWIBOT_COMPARISON_PATH` is not pointed at the fresh comparison artifact, `ablation_tables.py` may skip Table 5 or read stale data.

### Pitfall 3: Overloading Phase 12 with new modeling work

This phase is about evidence generation from the existing transfer system version. Model redesign, retraining, or feature remapping belongs to a future milestone.

## Recommendation

Use two plans:

1. `12-01` for fresh TwiBot artifact generation and evidence capture
2. `12-02` for paper-table regeneration and human-readable interpretation

That split cleanly maps to:

- `EVID-01` in Plan 12-01
- `EVID-02` and `EVID-03` in Plan 12-02
