# Phase 8: Calibration Signal Recovery - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Diagnose why threshold calibration on S2 collapses into an effectively constant objective and implement a calibration strategy that restores useful search behavior. This phase is about recovering calibration signal and selection quality, not redesigning the full training stack or changing milestone scope outside calibration.

</domain>

<decisions>
## Implementation Decisions

### Calibration strategy
- **D-01:** Use a hybrid fix. The primary direction is to improve the calibration objective or selection rule so candidate threshold sets can be distinguished more meaningfully, with early stopping added as a guardrail when the search is demonstrably flat.
- **D-02:** Do not treat early stopping alone as the full solution unless the diagnosis proves the current objective is acceptable and the only issue is wasted repeated trials.

### Tie-breaking and selection quality
- **D-03:** When top-line F1 ties, prefer the candidate with a better secondary score rather than keeping the first Optuna winner by default.
- **D-04:** The preferred secondary signal is probability-sensitive, such as log loss, Brier score, AUC, or a similarly smooth discriminator, so plateau ties can be broken by confidence quality rather than trial order.

### Success criteria for the fix
- **D-05:** Phase 8 must explain the root cause of the repeated `F1=0.993333` plateau, not just patch around it.
- **D-06:** Phase 8 must show that the chosen calibration policy is more meaningful than the current one, meaning it either differentiates materially different threshold candidates or stops early for a clearly justified plateau condition.

### Scope and change budget
- **D-07:** Scope is broad enough to change any necessary part of the training/calibration flow if the diagnosis proves the problem is not isolated to `calibrate.py`.
- **D-08:** Broad scope does not authorize unrelated feature work; changes must stay tightly coupled to calibration signal recovery, selection quality, logging, and supporting validation.

### the agent's Discretion
- The exact secondary metric and plateau detection heuristic are left to implementation and research, as long as they satisfy reproducibility and the diagnosis-first strategy above.
- Instrumentation format is flexible: trial logs, summary tables, or helper outputs are all acceptable if they make plateau behavior auditable.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Workstream definition
- `.planning/workstreams/calibration-fix/PROJECT.md` - Milestone goal, constraints, and key questions for the calibration-fix workstream
- `.planning/workstreams/calibration-fix/REQUIREMENTS.md` - Phase requirements `CALFIX-01` through `CALFIX-07`
- `.planning/workstreams/calibration-fix/ROADMAP.md` - Phase 8 goal and success criteria
- `.planning/workstreams/calibration-fix/STATE.md` - Current workstream status and session continuity

### Calibration implementation
- `calibrate.py` - Current Optuna-based threshold calibration loop and objective definition
- `main.py` - Current calibration invocation and training-flow integration
- `botdetector_pipeline.py` - Threshold dataclass, gating logic, and `predict_system()` behavior that calibration is optimizing

### Validation and existing tests
- `tests/test_calibrate.py` - Current calibration contract tests and reproducibility expectations

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `calibrate.py:calibrate_thresholds()` already owns the Optuna study lifecycle, parameter bounds, and final threshold persistence, so it is the natural place for revised objective logic, tie-breaking, and plateau detection.
- `botdetector_pipeline.py:StageThresholds` is the single threshold contract used by both training and prediction, so any search/output changes should continue to target this dataclass rather than inventing a new threshold format.
- `botdetector_pipeline.py:predict_system()` already returns `p1`, `p2`, `p12`, `p_final`, plus routing flags `amr_used` and `stage3_used`, which provides enough structure to derive richer calibration diagnostics without redesigning model inference.
- `tests/test_calibrate.py` already covers bounds, metric switching, persistence, and seed reproducibility; Phase 8 can extend this suite with plateau-specific regression checks instead of starting from scratch.

### Established Patterns
- Calibration currently optimizes a single scalar metric on `result["p_final"]`, with hard classification at `0.5` for F1, precision, and recall. This strongly suggests piecewise-constant objective regions when probabilities move without crossing decision boundaries.
- The gating logic in `gate_amr()` and `gate_stage3()` uses threshold bands and novelty triggers, so many sampled threshold combinations can produce identical routing masks and identical `p_final` labels even when raw threshold values differ.
- Reproducibility is already handled through explicit `seed` values in the Optuna sampler and training flow, so any new strategy should preserve seed-driven determinism rather than introduce nondeterministic stopping or ranking behavior.

### Integration Points
- `main.py` is the current top-level caller and can surface improved calibration summaries or new configuration knobs if needed.
- `calibrate.py` can gather extra per-trial diagnostics from `predict_system()` outputs without changing model-training APIs.
- If richer tie-break metrics require helper logic, the most adjacent integration surface is still the calibration path and its tests, with pipeline changes only if the diagnosis proves current outputs are insufficient.

</code_context>

<specifics>
## Specific Ideas

- The likely failure mode is not Optuna itself but a flat or heavily quantized objective: hard-thresholded F1 on nearly fixed `p_final` outputs plus threshold-band routing can make many distinct parameter vectors indistinguishable.
- The preferred design direction is "diagnosis first, smoother ranking second, early stopping third": identify why the plateau occurs, rank tied candidates with a secondary probability-sensitive metric, and stop once the search is provably no longer discovering meaningfully different outcomes.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 08-calibration-signal-recovery*
*Context gathered: 2026-04-16*
