# Phase 10: Evaluation and Baseline Comparison - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Compare the integrated LSTM Stage 2b variant against the AMR Stage 2b baseline on the real BotSim S3 cascade path, then record an honest recommendation based on the evidence. This phase is about evaluative judgment and milestone-close reporting, not more integration scaffolding or broader cross-dataset expansion.

</domain>

<decisions>
## Implementation Decisions

### Comparison evidence
- **D-01:** Phase 10 should use **real BotSim S3 comparison only** for the headline judgment.
- **D-02:** Both variants should be evaluated under the same split discipline and threshold policy so the comparison stays apples-to-apples.

### What counts as better
- **D-03:** Phase 10 should compare **overall metrics plus routing behavior**, not just a single top-line score.
- **D-04:** The evaluation should make behavioral differences visible, including cascade-routing consequences, even when headline metrics are close.

### Final output artifact
- **D-05:** Phase 10 should leave behind a **compact comparison report plus reusable table output**.
- **D-06:** The reporting should be concise enough for milestone documentation but structured enough to support `ablation_tables.py` or similar downstream reuse.

### Recommendation policy
- **D-07:** Phase 10 should allow an **honest neutral outcome**; AMR can remain the recommendation if the LSTM path is only different, not clearly better.
- **D-08:** The final result should explicitly support one of three honest conclusions: prefer AMR, prefer LSTM, or keep AMR as default while noting LSTM's distinct behavior.

### the agent's Discretion
- Exact metric bundle, table layout, and artifact filenames can be chosen during planning as long as the real S3 comparison stays primary and the recommendation remains evidence-driven.
- Small supporting evaluation helpers are acceptable if they sharpen the AMR-vs-LSTM comparison without broadening scope to new datasets or new model families.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Workstream docs
- `.planning/workstreams/stage2b-lstm-version/PROJECT.md` - milestone framing and comparison intent
- `.planning/workstreams/stage2b-lstm-version/REQUIREMENTS.md` - Phase 10 requirements `LSTM-07`, `LSTM-08`
- `.planning/workstreams/stage2b-lstm-version/ROADMAP.md` - Phase 10 goal and success criteria
- `.planning/workstreams/stage2b-lstm-version/STATE.md` - current workstream position and next-phase handoff

### Prior phase outputs
- `.planning/workstreams/stage2b-lstm-version/phases/08-lstm-stage-2b-foundation/08-CONTEXT.md` - original constraints for the LSTM Stage 2b path
- `.planning/workstreams/stage2b-lstm-version/phases/08-lstm-stage-2b-foundation/08-VERIFICATION.md` - what the standalone LSTM foundation proved
- `.planning/workstreams/stage2b-lstm-version/phases/09-cascade-integration-and-variant-selection/09-CONTEXT.md` - locked integration decisions for explicit variant selection
- `.planning/workstreams/stage2b-lstm-version/phases/09-cascade-integration-and-variant-selection/09-01-SUMMARY.md` - training-time selector and system-state integration
- `.planning/workstreams/stage2b-lstm-version/phases/09-cascade-integration-and-variant-selection/09-02-SUMMARY.md` - inference routing and integration-test proof
- `.planning/workstreams/stage2b-lstm-version/phases/09-cascade-integration-and-variant-selection/09-VERIFICATION.md` - what Phase 9 proved and what remains for comparison

### Code and reporting surfaces
- `botdetector_pipeline.py` - explicit `stage2b_variant` handling and shared cascade implementation
- `main.py` - current real BotSim split/training/calibration/evaluation entrypoint
- `evaluate.py` - current S3 metrics and routing report surface
- `ablation_tables.py` - existing table-generation patterns and reusable evaluation outputs
- `calibrate.py` - current threshold-report artifact style that can inform compact Phase 10 evidence output
- `tests/test_calibrate.py` - current Phase 9 integration assertions for variant selection
- `tests/test_evaluate.py` - current evaluation contract expectations

### Project-level context
- `.planning/PROJECT.md` - overall cascade architecture and evaluation framing
- `.planning/MILESTONES.md` - prior milestone history and reporting style

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `main.py` already reconstructs the real BotSim split, runs threshold calibration, evaluates on S3, and writes persisted model artifacts; this is the natural anchor for real-path Phase 10 comparison work.
- `evaluate_s3()` in `evaluate.py` already returns both top-line metrics and routing statistics, which aligns directly with the chosen "metric + routing" comparison rule.
- `ablation_tables.py` already has reusable table-building and LaTeX-export patterns that can support compact comparison output without inventing a separate reporting style.
- `botdetector_pipeline.py` now exposes explicit `stage2b_variant` selection, so Phase 10 can compare AMR and LSTM while keeping the rest of the cascade fixed.

### Established Patterns
- The repo already treats real S3 evaluation as the authoritative validation surface for cascade performance.
- Recent reporting work favors compact structured artifacts over ad hoc console-only output.
- Threshold calibration and Phase 9 evidence already established a "winner plus supporting alternatives/behavior" reporting pattern that Phase 10 can mirror at the variant-comparison level.

### Integration Points
- `train_system(..., stage2b_variant=...)` is the comparison control point for AMR vs LSTM system builds.
- `predict_system()` and `evaluate_s3()` are the comparison execution path for the real S3 judgment.
- `ablation_tables.py` is the obvious place to extend or reuse table output if Phase 10 needs side-by-side AMR-vs-LSTM summary tables.

</code_context>

<specifics>
## Specific Ideas

- The cleanest Phase 10 outcome is likely a paired AMR-vs-LSTM S3 comparison artifact that includes overall metrics, routing deltas, and a short plain-language recommendation.
- Because the user chose a neutral recommendation policy, planning should explicitly protect the ability to conclude "keep AMR" without treating that as a failed phase.

</specifics>

<deferred>
## Deferred Ideas

- TwiBot or other cross-dataset comparison
- Broader LSTM hyperparameter search beyond the current integrated variant
- Replacing the AMR baseline by policy before the real S3 evidence justifies it

</deferred>

---

*Phase: 10-evaluation-and-baseline-comparison*
*Context gathered: 2026-04-16*
