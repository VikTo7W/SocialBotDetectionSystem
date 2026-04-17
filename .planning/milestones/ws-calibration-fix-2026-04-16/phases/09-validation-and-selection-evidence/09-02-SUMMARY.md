# Plan 09-02 Summary

**Status:** Complete  
**Executed:** 2026-04-16

## Outcome

No further calibration-flow rewrite was needed after reviewing the real-run artifact from Plan 09-01.

## Evidence-based decision

- The real run did show a broad F1 plateau, but the plateau was not behaviorally flat.
- The selected trial beat nearby alternatives on smooth probability metrics while also routing substantially fewer accounts into AMR-heavy and Stage 3 paths.
- Because the artifact could explain the winner clearly, the Phase 8 hybrid fix was sufficient and Plan 09-02 stayed documentation-focused rather than reopening the algorithm.

## Final shipped policy

- **Primary objective:** maximize F1 on S2
- **Tie-break:** minimize log loss, then Brier score
- **Guardrail:** stop early when no lexicographic improvement appears for the plateau patience window
- **Final interpretation:** this milestone ships a **hybrid** fix, not early stopping alone

## Residual caveat

The real path still exhibits heavy F1 quantization. The meaningful differentiation now comes from probability quality and routing behavior rather than from distinct hard-label outcomes alone. That is acceptable for this milestone because the workstream goal was to avoid redundant trials and produce an evidence-backed selection rule, not to redesign the classifier stack.
