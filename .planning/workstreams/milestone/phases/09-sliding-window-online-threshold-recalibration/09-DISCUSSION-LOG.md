# Phase 9: Sliding-Window Online Threshold Recalibration - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-17
**Phase:** 09-sliding-window-online-threshold-recalibration
**Areas discussed:** Integration point, Which thresholds update, Update formula, Toggle and state handling

---

## Integration Point

| Option | Description | Selected |
|--------|-------------|----------|
| Loop inside evaluate_twibot20.py | run_inference() processes in chunks of N, accumulates novelty scores, updates local threshold copy before each chunk. predict_system() untouched. | ✓ |
| New streaming wrapper around predict_system | Wraps predict_system per-account in a loop. More general but expensive per-account embedding calls. | |
| Claude's discretion | Claude picks simplest integration. | |

**User's choice:** Loop inside evaluate_twibot20.py (Recommended)
**Notes:** predict_system() stays batch-capable and is called per-chunk with the current threshold copy.

---

## Which Thresholds Update

| Option | Description | Selected |
|--------|-------------|----------|
| Novelty thresholds only | Update n1_max_for_exit, n2_trigger, novelty_force_stage3. Probability thresholds stay fixed. | ✓ |
| All 10 dimensions | Update all StageThresholds including probability thresholds — unclear mapping, high risk. | |
| Claude's discretion | Claude picks based on what novelty scores can support. | |

**User's choice:** Novelty thresholds only (Recommended)
**Notes:** Probability thresholds (s1_bot, s2a_bot, etc.) carry no novelty signal and remain at trained values.

---

## Update Formula

| Option | Description | Selected |
|--------|-------------|----------|
| Percentile-based | new_threshold = percentile(buffer, P), P configurable (default 75th). Robust to outliers. | ✓ |
| Mean + k×std | new_threshold = mean(buffer) + k×std(buffer), k configurable. Sensitive to outliers in small buffers. | |
| Claude's discretion | Claude picks formula. | |

**User's choice:** Percentile-based (Recommended)
**Notes:** Intuitive interpretation — "route accounts more novel than P% of what we've seen so far."

---

## Toggle and State Handling

| Option | Description | Selected |
|--------|-------------|----------|
| Parameter on run_inference + local copy | run_inference(... online_calibration=True, window_size=100). Local current_th copy, sys.th never mutated. Phase 10 calls with/without flag for before/after. | ✓ |
| Wrapper class SlidingWindowCalibrator | Class wraps TrainedSystem with own threshold state. More reusable but adds layer. | |
| Claude's discretion | Claude picks design minimizing coupling. | |

**User's choice:** Parameter on run_inference + local copy (Recommended)
**Notes:** sys.th immutable; clean before/after comparison flag for Phase 10.

---

## Claude's Discretion

- Buffer structure (deque vs flat list) — implementer's choice
- Whether to log threshold updates per window — fine, one line per update
- Percentile default (75th) — adjustable based on TwiBot-20 novelty distribution testing
- Whether novelty buffer uses n1, n2 jointly or separate per-dimension percentiles

## Deferred Ideas

None — discussion stayed within phase scope.
