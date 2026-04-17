# Phase 8: Calibration Signal Recovery - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `08-CONTEXT.md` - this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 08-calibration-signal-recovery
**Areas discussed:** Calibration mode, Tie-break policy, Success evidence, Scope strictness

---

## Calibration mode

| Option | Description | Selected |
|--------|-------------|----------|
| Hybrid | Improve objective or selection quality, then add early stopping as plateau guardrail | Yes |
| Early stopping first | Keep current objective and just stop redundant trials | |
| New technique | Replace the current search/evaluation approach more aggressively | |

**User's choice:** Hybrid
**Notes:** The fix should not stop at trial-count reduction alone; meaningful candidate ranking matters.

---

## Tie-break policy

| Option | Description | Selected |
|--------|-------------|----------|
| Secondary score | Use a smoother secondary metric when headline F1 ties | Yes |
| Routing behavior | Prefer fewer unnecessary escalations when F1 ties | |
| Simplest rule | Keep earliest plateau hit / first winner behavior | |

**User's choice:** Secondary score
**Notes:** Probability-sensitive tie-breaking is preferred over "first trial wins."

---

## Success evidence

| Option | Description | Selected |
|--------|-------------|----------|
| Stop redundancy only | Success means repeated wasted trials are eliminated | |
| Explain root cause + improve meaning | Diagnose the plateau and prove the chosen thresholds are more meaningful | Yes |
| Improve downstream evaluation too | Require improved held-out evaluation quality in this phase | |

**User's choice:** Explain root cause + improve meaning
**Notes:** Phase 8 must establish why the plateau exists, not just work around it.

---

## Scope strictness

| Option | Description | Selected |
|--------|-------------|----------|
| Local | Restrict changes to `calibrate.py`, logs, and tests | |
| Adjacent | Allow small nearby support changes in pipeline/eval code | |
| Broad | Change whatever is necessary inside training/calibration flow | Yes |

**User's choice:** Broad
**Notes:** Scope can extend beyond `calibrate.py` if the diagnosis demands it, but remains limited to calibration-signal recovery.

---

## the agent's Discretion

- Choose the exact secondary metric and plateau heuristic during planning and implementation.
- Decide how to expose diagnostics as long as the result is auditable and reproducible.

## Deferred Ideas

None.
