# Phase 9: Cascade Integration and Variant Selection - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `09-CONTEXT.md` - this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 09-cascade-integration-and-variant-selection
**Areas discussed:** Variant selection mode, Integration depth, Baseline preservation, Phase 9 proof

---

## Variant selection mode

| Option | Description | Selected |
|--------|-------------|----------|
| Explicit config switch | Clear training/inference selector for `amr` vs `lstm` | x |
| Separate entrypoints | Different train/run functions for each variant | |
| LSTM-first fallback | Prefer LSTM when present, otherwise AMR | |

**User's choice:** Explicit config switch
**Notes:** Variant choice should be intentional and visible in both training and inference paths.

---

## Integration depth

| Option | Description | Selected |
|--------|-------------|----------|
| Both train and predict | Full end-to-end cascade option | x |
| Predict first | Inference path first, training integration later | |
| Train first | Training path first, inference wiring later | |

**User's choice:** Both train and predict
**Notes:** Phase 9 should produce a real end-to-end option rather than a partial integration.

---

## Baseline preservation

| Option | Description | Selected |
|--------|-------------|----------|
| Shared pipeline | Everything else identical except the Stage 2b branch | x |
| Light refactor | Allow small nearby cleanup/refactors if they help variant selection | |
| Broader reshape | Allow bigger Stage 2 internals changes if needed | |

**User's choice:** Shared pipeline
**Notes:** The comparison needs to stay apples-to-apples by keeping the rest of the cascade stable.

---

## Phase 9 proof

| Option | Description | Selected |
|--------|-------------|----------|
| Integration tests + smoke | Deterministic integration tests plus a small real-path smoke run | |
| Integration tests only | Keep it fully fixture/test based | x |
| Full early benchmark | Include broader AMR-vs-LSTM comparison already in Phase 9 | |

**User's choice:** Integration tests only
**Notes:** Phase 9 should prove correct wiring and selection semantics; broader evaluation belongs to Phase 10.

---

## the agent's Discretion

- Exact variant flag names and config placement
- Internal helper factoring needed to keep the shared pipeline readable

## Deferred Ideas

- Early full benchmark
- Broader Stage 2 refactor
- Separate train/run entrypoints per variant
