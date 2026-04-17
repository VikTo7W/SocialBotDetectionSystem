# Phase 9: Cascade Integration and Variant Selection - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Wire the LSTM Stage 2b prototype into the existing cascade so training and inference can explicitly select either the AMR baseline or the LSTM variant without changing the rest of the pipeline semantics. This phase is about controlled end-to-end integration and variant selection, not yet the final benchmark judgment between the two approaches.

</domain>

<decisions>
## Implementation Decisions

### Variant selection mode
- **D-01:** Phase 9 should use an **explicit config-controlled switch** for Stage 2b variant selection.
- **D-02:** Training and inference should both make the active Stage 2b choice visible and intentional rather than relying on implicit object presence or fallback behavior.

### Integration depth
- **D-03:** Phase 9 should wire the LSTM path through **both `train_system()` and `predict_system()`**.
- **D-04:** The result should be a real end-to-end cascade option, not a partially integrated experimental hook.

### Baseline preservation
- **D-05:** The integration should preserve a **shared pipeline** where everything outside the Stage 2b branch remains as identical as practical.
- **D-06:** AMR vs LSTM comparison value comes from keeping the rest of the cascade stable, not from rewriting adjacent parts of the architecture during this phase.

### Phase 9 proof
- **D-07:** Phase 9 only needs **integration tests**, not a broader early benchmark.
- **D-08:** The phase should prove that variant selection, training, and inference wiring behave correctly and reproducibly; Phase 10 remains responsible for evaluative comparison.

### the agent's Discretion
- Exact config surface, enum/string names, and helper boundaries can be chosen during planning as long as variant choice stays explicit and shared-pipeline semantics remain clear.
- Minor nearby cleanup is acceptable only if it directly supports a cleaner explicit variant switch without changing the comparison baseline.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Workstream docs
- `.planning/workstreams/stage2b-lstm-version/PROJECT.md` - milestone framing and constraints
- `.planning/workstreams/stage2b-lstm-version/REQUIREMENTS.md` - Phase 9 requirements `LSTM-04`, `LSTM-05`, `LSTM-06`
- `.planning/workstreams/stage2b-lstm-version/ROADMAP.md` - Phase 9 goal and success criteria
- `.planning/workstreams/stage2b-lstm-version/STATE.md` - current workstream status

### Prior phase outputs
- `.planning/workstreams/stage2b-lstm-version/phases/08-lstm-stage-2b-foundation/08-CONTEXT.md` - locked Phase 8 decisions
- `.planning/workstreams/stage2b-lstm-version/phases/08-lstm-stage-2b-foundation/08-01-SUMMARY.md` - sequence contract groundwork
- `.planning/workstreams/stage2b-lstm-version/phases/08-lstm-stage-2b-foundation/08-02-SUMMARY.md` - LSTM prototype and fixture proof
- `.planning/workstreams/stage2b-lstm-version/phases/08-lstm-stage-2b-foundation/08-VERIFICATION.md` - what Phase 8 proved and what remains

### Code and test surfaces
- `botdetector_pipeline.py` - current training/inference flow, `TrainedSystem`, AMR Stage 2b baseline, and new LSTM prototype helpers
- `tests/conftest.py` - synthetic system assembly and fixture patterns
- `tests/test_features_stage2.py` - sequence preprocessing invariants already established
- `tests/test_calibrate.py` - fixture-backed contract proof style already used in this repo

### Project-level context
- `.planning/PROJECT.md` - current cascade architecture and non-negotiable leakage/reproducibility constraints
- `.planning/MILESTONES.md` - prior shipped milestone history

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `Stage2LSTMRefiner` already exists as a trainable additive Stage 2b prototype with `delta()` / `refine()` methods.
- `extract_message_embedding_sequences_for_accounts()` already defines the deterministic sequence contract Phase 9 needs to reuse.
- `TrainedSystem` already holds the AMR baseline objects and now has an optional `stage2b_lstm` slot, which is the natural anchor for explicit variant selection.

### Established Patterns
- The current cascade is centered on `train_system()` and `predict_system()` as the end-to-end contract.
- Stage 2b is currently modeled as a refinement over Stage 2a logits rather than as an independent classifier stage.
- The workstream must preserve seeded reproducibility and leakage discipline while adding the variant selector.

### Integration Points
- `train_system()` must learn which Stage 2b variant to train and how to populate `TrainedSystem`.
- `predict_system()` must learn how to choose the configured Stage 2b variant at inference time.
- Tests in `tests/conftest.py` are likely the fastest way to prove shared-pipeline integration without needing a broader benchmark yet.

</code_context>

<specifics>
## Specific Ideas

- The cleanest Phase 9 outcome is likely a Stage 2b variant flag on the training/inference path, with AMR and LSTM both implementing the same high-level refinement role.
- Because the user chose integration tests only, planning should optimize for deterministic end-to-end path validation rather than early metric storytelling.

</specifics>

<deferred>
## Deferred Ideas

- Full AMR-vs-LSTM benchmark or recommendation
- Broader Stage 2 architecture refactor
- Hyperparameter search or deeper variant family exploration

</deferred>

---

*Phase: 09-cascade-integration-and-variant-selection*
*Context gathered: 2026-04-16*
