# Phase 8: LSTM Stage 2b Foundation - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Define the LSTM-based Stage 2b foundation so it can train reproducibly and expose a stable contract for later cascade integration. This phase is about the model/data contract, deterministic preprocessing, and proof that the LSTM path can behave like a controlled side-by-side variant of the current Stage 2b logic. It is not yet the phase for full-cascade rollout or final baseline judgment.

</domain>

<decisions>
## Implementation Decisions

### LSTM role
- **D-01:** The LSTM Stage 2b path should start as a **parallel variant**, not an immediate replacement for the AMR delta refiner.
- **D-02:** The AMR-based Stage 2b path remains the active baseline while the LSTM path is developed and validated beside it.

### Sequence input
- **D-03:** Phase 8 should use a sequence of **per-message embeddings** as the LSTM input, rather than feeding raw text directly into the recurrent model.
- **D-04:** Sequence ordering should follow the existing account message ordering conventions already used by the pipeline.

### Compatibility contract
- **D-05:** The LSTM path should aim to preserve the current Stage 2b compatibility contract by producing a refined `z2`-style output that fits the existing Stage 2 / meta-model flow.
- **D-06:** If an internal prototype needs intermediate helper structures, they should still collapse back to the `z2`-compatible contract by the end of the phase.

### Foundation evidence
- **D-07:** Phase 8 only needs a deterministic fixture proof, not a broad real-data benchmark yet.
- **D-08:** The required proof includes seeded reproducibility, deterministic handling of empty/short histories, and a scoped train/infer contract that downstream phases can build on.

### the agent's Discretion
- Exact tensor shapes, batching helpers, and sequence padding strategy can be chosen during planning as long as the seeded behavior and `z2` compatibility goal stay intact.
- The exact fixture composition can be synthetic or narrowly scoped from existing test assets, provided it proves the Phase 8 contract clearly.

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Workstream docs
- `.planning/workstreams/stage2b-lstm-version/PROJECT.md` - milestone framing and constraints
- `.planning/workstreams/stage2b-lstm-version/REQUIREMENTS.md` - Phase 8 requirements `LSTM-01`, `LSTM-02`, `LSTM-03`
- `.planning/workstreams/stage2b-lstm-version/ROADMAP.md` - Phase 8 goal and success criteria
- `.planning/workstreams/stage2b-lstm-version/STATE.md` - current workstream status

### Existing Stage 2b baseline
- `botdetector_pipeline.py` - current Stage 2a / Stage 2b flow, `AMRDeltaRefiner`, `extract_amr_embeddings_for_accounts`, `train_system()`, and `predict_system()`
- `tests/conftest.py` - current synthetic fixture and `TrainedSystem` assembly pattern used for calibration/testing
- `tests/test_features_stage2.py` - current Stage 2 feature and AMR-anchor invariants that should inform sequence preprocessing choices

### Project-level context
- `.planning/PROJECT.md` - existing cascade architecture, leakage constraints, and current baseline positioning
- `.planning/MILESTONES.md` - prior shipped milestone history

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `AMRDeltaRefiner` in `botdetector_pipeline.py` already defines the baseline Stage 2b role as a refinement on top of `z2a`; this is the closest contract for the LSTM variant to mirror.
- `extract_amr_embeddings_for_accounts()` already encodes per-account message-derived inputs in temporal order, which is a useful precedent for Stage 2b sequence construction.
- `tests/conftest.py` already builds a minimal synthetic `TrainedSystem` and is the natural place to anchor deterministic fixture proofs for Phase 8.

### Established Patterns
- The pipeline currently treats Stage 2b as an additive refinement step over Stage 2a logits rather than an independent full classifier.
- Empty-message accounts already have deterministic zero-vector behavior in the AMR path; the LSTM path should preserve an equally explicit rule.
- Seeded reproducibility is already treated as a hard constraint across training and calibration flows.

### Integration Points
- `train_system()` is the eventual integration point for training an alternate Stage 2b path.
- `predict_system()` is the eventual inference integration point where variant selection will need to hook in later.
- Phase 8 can likely prototype the LSTM foundation without fully editing both paths yet, as long as it proves a `z2`-compatible output contract.

</code_context>

<specifics>
## Specific Ideas

- The cleanest Phase 8 outcome is probably a separately trainable LSTM Stage 2b component that consumes ordered per-message embeddings and returns a refined logit compatible with the current Stage 2 pipeline.
- Because the user chose a parallel-variant approach, planning should avoid any design that forces deletion or semantic reinterpretation of the current AMR refiner in this phase.

</specifics>

<deferred>
## Deferred Ideas

- Full cascade switch-over to the LSTM path
- Broad real-data benchmark or final AMR-vs-LSTM judgment
- Hyperparameter search over the LSTM architecture

</deferred>

---

*Phase: 08-lstm-stage-2b-foundation*
*Context gathered: 2026-04-16*
