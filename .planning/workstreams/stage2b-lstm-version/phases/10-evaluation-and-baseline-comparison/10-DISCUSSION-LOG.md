# Phase 10: Evaluation and Baseline Comparison - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md - this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 10-evaluation-and-baseline-comparison
**Areas discussed:** Comparison evidence, What counts as better, Final output artifact, Recommendation policy

---

## Comparison evidence

| Option | Description | Selected |
|--------|-------------|----------|
| Real S3 only | Compare AMR vs LSTM on the actual BotSim S3 path only | ✓ |
| Real + ablations | Real S3 comparison plus a small supporting breakdown like stage/routing tables | |
| Broader | Include TwiBot or extra slices already in Phase 10 | |

**User's choice:** Real S3 only
**Notes:** The headline judgment for Phase 10 should come from the actual BotSim S3 cascade path rather than from broader or earlier-expansion evaluation.

---

## What counts as better

| Option | Description | Selected |
|--------|-------------|----------|
| Metric + routing | Overall metrics plus routing/behavior differences | ✓ |
| Metrics only | Winner is whoever scores higher on evaluation metrics | |
| Routing only | Prefer the variant with better cascade behavior even if headline metrics tie | |

**User's choice:** Metric + routing
**Notes:** Phase 10 should surface both top-line quality and cascade behavior differences when judging AMR vs LSTM.

---

## Final output artifact

| Option | Description | Selected |
|--------|-------------|----------|
| Compact report + tables | Concise recommendation artifact plus reusable comparison tables | ✓ |
| Report only | Recommendation artifact without extra table work | |
| Full analysis | Deeper benchmark write-up even if it takes more work | |

**User's choice:** Compact report + tables
**Notes:** The result should be reusable in workstream artifacts and existing reporting/table surfaces without turning into a large benchmark monograph.

---

## Recommendation policy

| Option | Description | Selected |
|--------|-------------|----------|
| Honest neutral | AMR can stay the recommendation if LSTM is only different, not better | ✓ |
| Prefer novelty | Lean toward LSTM if it is competitive and behaviorally interesting | |
| Ship challenger | Make Phase 10 pick a new default unless LSTM clearly fails | |

**User's choice:** Honest neutral
**Notes:** Phase 10 should preserve the ability to recommend keeping the AMR baseline if the LSTM path does not clearly win.

---

## the agent's Discretion

- Exact metric bundle and comparison-table format
- Exact artifact names and whether reporting extends `ablation_tables.py` directly or reuses its patterns in a nearby file

## Deferred Ideas

- Cross-dataset Phase 10 comparison beyond BotSim S3
- Any forced replacement of the AMR default before the evidence supports it
