---
phase: 8
slug: behavioral-tweet-parser-and-stage-1-adapter
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-17
---

# Phase 8 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest.ini or pyproject.toml |
| **Quick run command** | `pytest tests/test_twibot20_io.py tests/test_evaluate_twibot20.py -x -q` |
| **Full suite command** | `pytest -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_twibot20_io.py tests/test_evaluate_twibot20.py -x -q`
- **After every plan wave:** Run `pytest -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 8-01-01 | 01 | 0 | FEAT-01 | — | N/A | unit | `pytest tests/test_twibot20_io.py::test_parse_tweet_types -x -q` | ❌ W0 | ⬜ pending |
| 8-01-02 | 01 | 1 | FEAT-01 | — | N/A | unit | `pytest tests/test_twibot20_io.py -x -q` | ✅ | ⬜ pending |
| 8-01-03 | 01 | 1 | FEAT-02/03 | — | N/A | unit | `pytest tests/test_evaluate_twibot20.py -x -q` | ✅ | ⬜ pending |
| 8-01-04 | 01 | 1 | FEAT-02 | — | N/A | integration | `pytest tests/test_evaluate_twibot20.py -x -q` | ✅ | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_twibot20_io.py` — stubs for `parse_tweet_types()` covering FEAT-01: RT/MT/original classification, @username extraction, zero-tweet account edge case
- [ ] `tests/test_evaluate_twibot20.py` — update stubs for FEAT-02 behavioral adapter: verify column mapping, ratio cap behavior

*Note: 4 tests in test_evaluate_twibot20.py are currently FAILING due to `KeyError: 'profile'` — these will be fixed as part of Wave 1 adapter rewrite.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Ratio cap value appropriateness for TwiBot-20 distributions | FEAT-03 | Requires real TwiBot-20 data — cannot mock distribution | Run `python evaluate_twibot20.py` with full dataset; inspect printed 95th/99th percentile of ratio columns; document decision |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
