# Phase 8: LSTM Stage 2b Foundation - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `08-CONTEXT.md` - this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 08-lstm-stage-2b-foundation
**Areas discussed:** LSTM role, Sequence input, Compatibility contract, Foundation evidence

---

## LSTM role

| Option | Description | Selected |
|--------|-------------|----------|
| Refiner replacement | LSTM becomes the Stage 2b refinement path | |
| Parallel variant | Keep AMR Stage 2b untouched and build LSTM as a side-by-side experimental path first | x |
| Feature supplier | LSTM mainly produces features that another lightweight refiner consumes | |

**User's choice:** Parallel variant
**Notes:** The current AMR refiner stays available as the comparison baseline while the LSTM path is developed.

---

## Sequence input

| Option | Description | Selected |
|--------|-------------|----------|
| Raw messages | Ordered per-account message text sequence | |
| Embedded messages | Sequence of per-message embeddings, then LSTM over those | x |
| Hybrid | Text plus a small amount of per-message metadata if available | |

**User's choice:** Embedded messages
**Notes:** Phase 8 should start from a sequence model over per-message embeddings rather than direct raw-text recurrence.

---

## Compatibility contract

| Option | Description | Selected |
|--------|-------------|----------|
| Match z2 contract | Same Stage 2b-style refined `z2` output | x |
| Match p2 contract | Output calibrated probability directly and adapt around it | |
| Prototype first | Allow a temporary custom contract in Phase 8, normalize later | |

**User's choice:** Match z2 contract
**Notes:** The LSTM path should preserve the current downstream Stage 2/meta-model expectations as closely as possible.

---

## Foundation evidence

| Option | Description | Selected |
|--------|-------------|----------|
| Deterministic fixture | Scoped train/infer proof with empty-history handling and seed stability | x |
| Mini real path | Also run on a small real BotSim slice in Phase 8 | |
| Broader benchmark | Include early baseline comparison already in Phase 8 | |

**User's choice:** Deterministic fixture
**Notes:** Phase 8 should prove the foundation contract first; broader evaluation belongs later.

---

## the agent's Discretion

- Sequence padding/truncation details
- Fixture implementation details
- Internal helper APIs, as long as they preserve the `z2` contract and seeded reproducibility

## Deferred Ideas

- Real-data baseline comparison in Phase 8
- Immediate replacement of the AMR path
- Broader architecture search
