# Phase 9: Validation and Selection Evidence - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Validate that the new calibration behavior is meaningfully better on the real calibration path, not just different in synthetic tests, and leave behind a compact reproducible artifact that explains the final selection policy clearly. This phase is about evidence and validation; it should only reopen calibration-flow changes if the validation proves the Phase 8 fix is insufficient.

</domain>

<decisions>
## Implementation Decisions

### Evidence source
- **D-01:** Phase 9 should validate on the real S2 calibration path only. Synthetic fixtures may remain as support tests, but they do not count as primary evidence for this phase.
- **D-02:** The key question is whether the actual pipeline now differentiates meaningful candidate threshold sets under real calibration behavior, not whether a mocked scenario can be made to do so.

### What counts as meaningful differentiation
- **D-03:** Validation must require both score separation and behavioral separation.
- **D-04:** "Behavioral separation" means observable differences such as routing behavior, positive prediction patterns, threshold choice rationale, or other real calibration outputs that show candidate threshold sets are materially distinct.
- **D-05:** A smooth secondary metric alone is not enough if the selected candidate is behaviorally indistinguishable from alternatives on the real path.

### Validation deliverable
- **D-06:** Phase 9 must leave behind a compact reproducible report artifact, not only passing tests.
- **D-07:** The report should explain the selected trial, near-best alternatives, tie counts, early-stop behavior if applicable, and why the final selection policy is justified.

### Scope and escalation rule
- **D-08:** Phase 9 may broaden scope again if real validation evidence shows the Phase 8 fix is not sufficient.
- **D-09:** Broad scope is conditional on evidence. The default expectation is validation/reporting first, then targeted calibration-flow changes only if the validation reveals a real gap.

### the agent's Discretion
- The exact report format can be a markdown summary, JSON-plus-markdown pair, or similar compact artifact, as long as it is reproducible and easy to inspect.
- The exact set of comparison candidates can be chosen during planning and execution, provided the chosen sample is representative of the real calibration path.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Workstream definition
- `.planning/workstreams/calibration-fix/PROJECT.md` - Overall milestone framing and constraints
- `.planning/workstreams/calibration-fix/REQUIREMENTS.md` - Phase 9 requirements `CALFIX-05`, `CALFIX-06`, and `CALFIX-07`
- `.planning/workstreams/calibration-fix/ROADMAP.md` - Phase 9 goal and success criteria
- `.planning/workstreams/calibration-fix/STATE.md` - Current workstream status and continuity

### Prior phase outputs
- `.planning/workstreams/calibration-fix/phases/08-calibration-signal-recovery/08-CONTEXT.md` - Locked decisions from Phase 8
- `.planning/workstreams/calibration-fix/phases/08-calibration-signal-recovery/08-01-SUMMARY.md` - Diagnostic groundwork added in Phase 8 plan 01
- `.planning/workstreams/calibration-fix/phases/08-calibration-signal-recovery/08-02-SUMMARY.md` - Hybrid tie-break and plateau-stop changes from Phase 8 plan 02
- `.planning/workstreams/calibration-fix/phases/08-calibration-signal-recovery/08-VERIFICATION.md` - What Phase 8 verified and what it intentionally did not prove yet

### Code and validation surfaces
- `calibrate.py` - Current calibration diagnostics, tie-break, and plateau stopping logic
- `main.py` - Real calibration invocation path
- `evaluate.py` - Existing evaluation/reporting structure that may help anchor real validation evidence
- `tests/test_calibrate.py` - Current automated coverage, including synthetic tie and plateau scenarios

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `system.calibration_report_` in `calibrate.py` already captures requested/executed trials, selected trial, tie counts, early-stop status, and per-trial diagnostics. This is the natural base for the Phase 9 report artifact.
- `main.py` already runs the real calibration path on S2, so it is the right integration point if Phase 9 needs a reproducible end-to-end validation run or a report-emission hook.
- `evaluate.py` and the existing ablation/reporting style in the repo provide patterns for compact reproducible result artifacts.

### Established Patterns
- Current tests in `tests/test_calibrate.py` prove the behavior on controlled fixtures, but the workstream state explicitly records that stronger evidence is still needed on the real calibration path.
- The calibration code now exposes both score-based and behavior-adjacent diagnostics, which means Phase 9 can compare selected and near-best candidates without redesigning the calibration interface first.
- Broad phase scope is allowed, but only if the real evidence shows that the current calibration report or selection policy is still too weak to satisfy `CALFIX-05` through `CALFIX-07`.

### Integration Points
- `calibrate.py` may need a helper for summarizing the selected trial against near-best alternatives from a real run.
- `main.py` may need a small call-site/reporting update so the real calibration path can emit the compact validation artifact reproducibly.
- `tests/test_calibrate.py` can be extended for regression protection, but the key new evidence must come from real-pipeline execution rather than synthetic-only checks.

</code_context>

<specifics>
## Specific Ideas

- The most useful Phase 9 outcome is likely a compact artifact that answers: "What did the real calibration run choose, what were the strongest alternative trials, how were they behaviorally different, and why was the final winner justified?"
- If the real run still shows behaviorally indistinguishable near-best candidates, that should be treated as evidence that the current Phase 8 fix is incomplete rather than papered over with more synthetic tests.

</specifics>

<deferred>
## Deferred Ideas

None - discussion stayed within phase scope.

</deferred>

---

*Phase: 09-validation-and-selection-evidence*
*Context gathered: 2026-04-16*
