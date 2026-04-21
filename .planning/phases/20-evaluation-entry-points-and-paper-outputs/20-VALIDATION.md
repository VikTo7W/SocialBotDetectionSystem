---
phase: 20
slug: evaluation-entry-points-and-paper-outputs
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-19
---

# Phase 20 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none detected |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd-verify-work`:** Full suite must be green
- **Max feedback latency:** ~30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Threat Ref | Secure Behavior | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|------------|-----------------|-----------|-------------------|-------------|--------|
| 20-01-01 | 01 | 0 | EVAL-01, EVAL-02, EVAL-03, PAPER-01 | — | N/A | unit | `pytest tests/test_eval_botsim_native.py tests/test_eval_reddit_twibot_transfer.py tests/test_eval_twibot_native.py -x -q` | ❌ W0 | ⬜ pending |
| 20-02-01 | 02 | 1 | EVAL-01 | — | N/A | unit | `pytest tests/test_eval_botsim_native.py -x -q` | ❌ W0 | ⬜ pending |
| 20-03-01 | 03 | 1 | EVAL-02 | — | N/A | unit | `pytest tests/test_eval_reddit_twibot_transfer.py -x -q` | ❌ W0 | ⬜ pending |
| 20-04-01 | 04 | 1 | EVAL-03 | — | N/A | unit | `pytest tests/test_eval_twibot_native.py -x -q` | ❌ W0 | ⬜ pending |
| 20-05-01 | 05 | 2 | PAPER-01, PAPER-02, PAPER-03 | — | N/A | unit | `pytest tests/test_paper_outputs.py -x -q` | ❌ W0 | ⬜ pending |
| 20-06-01 | 06 | 2 | PAPER-03 | — | N/A | integration | `python -c "from ablation_tables import generate_cross_dataset_table; print('OK')"` | ✅ fix | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_eval_botsim_native.py` — stubs for EVAL-01 (BotSim native evaluation contract)
- [ ] `tests/test_eval_reddit_twibot_transfer.py` — stubs for EVAL-02 (zero-shot transfer evaluation contract)
- [ ] `tests/test_eval_twibot_native.py` — stubs for EVAL-03 (TwiBot native evaluation contract)
- [ ] `tests/test_paper_outputs.py` — stubs for PAPER-01/02 (confusion matrix + routing stats output)
- [ ] Fix `ablation_tables.py` import breakage (`filter_edges_for_split` moved from `main` to `train_botsim`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Confusion matrix image is correctly labelled (human/bot axes, title) | PAPER-01 | Visual inspection | Open `paper_outputs/confusion_matrix_*.png` and verify axes labels |
| Table 5 LaTeX output renders correctly | PAPER-03 | LaTeX rendering | Compile and inspect the generated LaTeX table |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
