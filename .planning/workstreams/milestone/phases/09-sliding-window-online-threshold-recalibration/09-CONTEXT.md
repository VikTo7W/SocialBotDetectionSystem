# Phase 9: Sliding-Window Online Threshold Recalibration - Context

**Gathered:** 2026-04-17
**Status:** Ready for planning

<domain>
## Phase Boundary

Add unsupervised sliding-window threshold recalibration to the TwiBot-20 inference path. After processing every N accounts, the calibrator updates the novelty-based routing thresholds from the accumulated novelty score buffer — without consulting labels. The probability thresholds remain fixed. `sys.th` is never mutated; the update is local to the inference run. `predict_system()` and all existing pipeline files are untouched.

</domain>

<decisions>
## Implementation Decisions

### Integration Point
- **D-01:** The sliding-window calibrator lives inside `evaluate_twibot20.py`. `run_inference()` processes accounts in chunks of N, accumulates novelty scores per chunk, and updates a *local copy* of `sys.th` before each subsequent chunk. `predict_system()` stays batch-capable and is called per-chunk with the current threshold copy.
- **D-02:** The chunking loop replaces the existing single `predict_system()` call inside `run_inference()`. The external signature of `run_inference()` is unchanged except for the two new optional parameters.

### Which Thresholds Update
- **D-03:** Only the three novelty-based routing thresholds are updated from the buffer: `n1_max_for_exit`, `n2_trigger`, and `novelty_force_stage3`. The six probability thresholds (`s1_bot`, `s1_human`, `s2a_bot`, `s2a_human`, `s12_bot`, `s12_human`) and `disagreement_trigger` stay fixed at the trained values — novelty scores carry no signal for unsupervised probability threshold adjustment.

### Update Formula
- **D-04:** New threshold values are computed as a percentile of the accumulated novelty score buffer. The percentile P is configurable (suggested default: 75th). Formula: `new_threshold = np.percentile(buffer, P)`. Percentile-based is robust to outlier novelty spikes in small early windows and has an intuitive interpretation: "route accounts that are more novel than P% of what we have seen so far."
- **D-05:** The same buffer and percentile P is applied to all three novelty threshold dimensions. There is no per-dimension tuning in Phase 9 — that can be explored in future work.

### Toggle and State Handling
- **D-06:** `run_inference()` accepts two new optional parameters: `online_calibration: bool = True` and `window_size: int = 100`. When `online_calibration=False`, the function behaves exactly as before (single `predict_system()` call, `sys.th` used directly). This enables Phase 10 to produce a clean before/after comparison by calling `run_inference()` twice with different flag values.
- **D-07:** Inside `run_inference()`, a local `current_th` is initialized as a copy of `sys.th` at the start. Only `current_th` is ever modified; `sys.th` is immutable from the perspective of this function.
- **D-08:** Cold-start handling (CAL-03): until the buffer has accumulated novelty scores from at least N accounts, `current_th` retains the original trained thresholds unchanged. The first threshold update happens only after the first full window completes.

### Claude's Discretion
- The exact buffer structure (flat list vs. rolling deque) can be chosen by the implementer — a `collections.deque(maxlen=window_size)` or a flat list with periodic reset both satisfy CAL-01.
- Whether to print a summary of threshold updates per window is Claude's call (a single log line per update is fine for debugging).
- The percentile parameter default (75th) can be adjusted if testing reveals it is too aggressive or too conservative for TwiBot-20 novelty distributions.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Pipeline integration
- `botdetector_pipeline.py` lines 224–239 — `StageThresholds` dataclass: all 10 threshold dimensions; D-03 applies to `n1_max_for_exit`, `n2_trigger`, `novelty_force_stage3` only
- `botdetector_pipeline.py` lines 841–920 — `predict_system()` full implementation; understand the `sys.th` usage pattern before chunking it
- `evaluate_twibot20.py` lines 35–130 — `run_inference()` current implementation; Phase 9 modifies this function

### Requirements
- `.planning/REQUIREMENTS.md` — CAL-01, CAL-02, CAL-03 (sliding-window calibrator requirements)
- `.planning/workstreams/milestone/ROADMAP.md` — Phase 9 goal and four success criteria

### Prior phase context
- `.planning/workstreams/milestone/phases/08-behavioral-tweet-parser-and-stage-1-adapter/08-CONTEXT.md` — Phase 8 locked decisions (isolation rule, column adapter, clamping)
- `.planning/workstreams/milestone/STATE.md` — current project state and accumulated decisions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `StageThresholds` is a plain dataclass — `copy.copy(sys.th)` or `dataclasses.replace(sys.th, n1_max_for_exit=..., ...)` gives an independent local copy without affecting the original
- `predict_system(sys, df, edges_df, nodes_total)` accepts a full batch DataFrame — calling it per-chunk requires slicing `df` and `edges_df` by row index, then concatenating results
- `evaluate_twibot20.run_inference()` already loads `accounts_df`, `edges_df`, and calls `predict_system()` — the chunking loop wraps this call
- `n1`, `n2` are already present in the `predict_system()` output DataFrame — the buffer accumulation can read these columns after each chunk

### Established Patterns
- `sys.th` is accessed as `cfg, th = sys.cfg, sys.th` inside `predict_system()` — D-07 (local copy) must be implemented by passing a modified `sys` copy or by monkey-patching `sys.th` temporarily (dataclasses.replace on the TrainedSystem is cleaner)
- Novelty scores in output: `n1` (Stage 1 Mahalanobis), `n2` (Stage 2a Mahalanobis), `n3` (Stage 3 Mahalanobis, zero for unrouted accounts) — buffer should use `n1` and `n2` (always populated); `n3` is sparse

### Integration Points
- `run_inference()` returns a results DataFrame — chunked results must be `pd.concat()`-ed in the same column order as the current single-call return
- Phase 10 will call `run_inference(path, model_path, online_calibration=False)` for the baseline and `run_inference(path, model_path, online_calibration=True)` for the recalibrated run

</code_context>

<specifics>
## Specific Ideas

- The cleanest implementation: at the start of `run_inference()`, do `import dataclasses; current_th = dataclasses.replace(sys.th)`. After each chunk, call `np.percentile(novelty_buffer, P)` and use `dataclasses.replace(current_th, n1_max_for_exit=..., n2_trigger=..., novelty_force_stage3=...)` to produce the next `current_th`. Pass updated thresholds to `predict_system()` by temporarily swapping `sys.th = current_th` inside the loop, restoring it with a `finally` block — or better, create a lightweight local `TrainedSystem`-like object that holds `current_th`.
- For the novelty buffer, using `n1` and `n2` jointly (e.g., `max(n1, n2)` per account, or separate percentiles per dimension) is a detail for the planner to decide based on which produces the most stable thresholds on TwiBot-20.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 09-sliding-window-online-threshold-recalibration*
*Context gathered: 2026-04-17*
