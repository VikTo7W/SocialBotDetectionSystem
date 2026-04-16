---
phase: 09
slug: zero-shot-inference-pipeline
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-16
---

# Phase 09 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3.4 |
| **Config file** | none — uses default discovery |
| **Quick run command** | `python -m pytest tests/test_evaluate_twibot20.py -x -q` |
| **Full suite command** | `python -m pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds (unit tests only; ~20s full suite) |

---

## Sampling Rate

- **After every task commit:** Run `python -m pytest tests/test_evaluate_twibot20.py -x -q`
- **After every plan wave:** Run `python -m pytest tests/ -x -q`
- **Before `/gsd-verify-work`:** Full suite must be green (currently 61 tests pass baseline)
- **Max feedback latency:** ~5 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 09-01-01 | 01 | 1 | TW-04 | T-09-01 | No untrusted input paths | unit | `python -m pytest tests/test_evaluate_twibot20.py -x -q` | ❌ W0 | ⬜ pending |
| 09-01-02 | 01 | 1 | TW-05 | T-09-02 | Clamping isolated to TwiBot-20 path | unit | `python -m pytest tests/test_evaluate_twibot20.py::test_ratio_clamping_applied -x -q` | ❌ W0 | ⬜ pending |
| 09-02-01 | 02 | 2 | TW-04 | T-09-01 | JSON output written to local file only | unit | `python -m pytest tests/test_evaluate_twibot20.py::test_main_block_saves_json -x -q` | ❌ W0 | ⬜ pending |
| 09-02-02 | 02 | 2 | TW-05 | T-09-02 | BotSim-24 path unaffected | unit | `python -m pytest tests/test_evaluate_twibot20.py::test_botsim_path_not_clamped -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_evaluate_twibot20.py` — 5 unit tests covering TW-04 and TW-05:
  - `test_run_inference_returns_correct_schema` — 11-column DataFrame
  - `test_run_inference_end_to_end` — no errors on synthetic data
  - `test_main_block_saves_json` — results_twibot20.json written as records-oriented JSON
  - `test_ratio_clamping_applied` — columns 6-9 bounded at 50.0 (high statuses_count input)
  - `test_botsim_path_not_clamped` — direct `extract_stage1_matrix()` call is NOT clamped

*Existing `conftest.py` `minimal_system` fixture is reusable — no new fixtures required.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Integration against real test.json | TW-04 | test.json not in repo | `python evaluate_twibot20.py` — verify 1183 accounts, no NaN/Inf in p_final, results_twibot20.json written |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
