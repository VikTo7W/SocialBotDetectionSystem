# Phase 9: Validation and Selection Evidence - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in `09-CONTEXT.md` - this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 09-validation-and-selection-evidence
**Areas discussed:** Evidence source, Meaningful differentiation, Validation output, Scope

---

## Evidence source

| Option | Description | Selected |
|--------|-------------|----------|
| Real + synthetic | Validate on the real S2 path and keep one synthetic control | |
| Real only | Only trust evidence from the real pipeline | Yes |
| Synthetic first | Strengthen synthetic proof before real-run validation | |

**User's choice:** Real only
**Notes:** Synthetic fixtures can remain supportive, but they are not sufficient evidence for Phase 9.

---

## Meaningful differentiation

| Option | Description | Selected |
|--------|-------------|----------|
| Score + behavior | Require smooth-score differences and observable behavioral differences | Yes |
| Score only | Smooth metric separation is enough | |
| Behavior only | Routing/prediction differences matter more than score changes | |

**User's choice:** Score + behavior
**Notes:** Real validation must show that selected and alternative candidates are meaningfully different in more than one way.

---

## Validation output

| Option | Description | Selected |
|--------|-------------|----------|
| Compact report | Leave behind a reproducible summary/report artifact plus tests | Yes |
| Tests only | No report if the tests are good enough | |
| Verbose analysis | Produce a deeper, heavier-weight analysis artifact | |

**User's choice:** Compact report
**Notes:** The output should be compact but still explain the final selection policy clearly.

---

## Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Validation-focused | Mostly reporting/tests with tiny call-site updates | |
| Adjacent | Allow moderate nearby changes if validation reveals a gap | |
| Broad again | Change whatever is needed if the evidence says the current fix is insufficient | Yes |

**User's choice:** Broad again
**Notes:** Broad scope is allowed, but only when real validation exposes a genuine gap.

---

## the agent's Discretion

- Choose the exact report format and candidate-comparison slice during planning.
- Keep the phase anchored on real evidence first, not synthetic convenience.

## Deferred Ideas

None.
