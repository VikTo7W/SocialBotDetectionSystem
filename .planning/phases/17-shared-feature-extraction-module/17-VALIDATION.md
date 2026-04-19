---
phase: 17
slug: shared-feature-extraction-module
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-18
---

# Phase 17 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none detected (no pytest.ini / pyproject.toml) |
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
| 17-01-01 | 01 | 0 | CORE-01, CORE-02, CORE-05 | — | N/A | unit | `pytest tests/test_features_stage1.py tests/test_data_io.py tests/test_lstm_removed.py -x -q` | ❌ W0 | ⬜ pending |
| 17-02-01 | 02 | 1 | CORE-02 | — | N/A | unit | `pytest tests/test_features_stage1.py -x -q` | ❌ W0 | ⬜ pending |
| 17-02-02 | 02 | 1 | CORE-01 | — | N/A | unit | `pytest tests/test_data_io.py -x -q` | ❌ W0 | ⬜ pending |
| 17-03-01 | 03 | 1 | CORE-02 | — | N/A | unit | `pytest tests/test_features_stage2.py tests/test_features_stage2_twitter.py -x -q` | ✅ (update) | ⬜ pending |
| 17-04-01 | 04 | 1 | CORE-02 | — | N/A | unit | `pytest tests/test_features_stage3_twitter.py -x -q` | ✅ (update) | ⬜ pending |
| 17-05-01 | 05 | 1 | CORE-05 | — | N/A | unit | `pytest tests/test_lstm_removed.py -x -q` | ❌ W0 | ⬜ pending |
| 17-06-01 | 06 | 2 | CORE-01, CORE-02, CORE-05 | — | N/A | integration | `pytest tests/ -q` | ✅ (update) | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_features_stage1.py` — stubs for CORE-01 (Stage1Extractor botsim + twibot shape checks)
- [ ] `tests/test_data_io.py` — stubs for CORE-01 (load_dataset dispatch, both datasets)
- [ ] `tests/test_lstm_removed.py` — stubs for CORE-05 (import check, TrainedSystem field check)
- [ ] `tests/conftest.py` — remove `minimal_lstm_stage2b_inputs` fixture and LSTM imports (BLOCKING: without this, all tests fail to import)
- [ ] `tests/test_features_stage2.py` — update import from `features_stage2` to `from features.stage2 import Stage2Extractor`
- [ ] `tests/test_features_stage2_twitter.py` — same pattern
- [ ] `tests/test_features_stage1_twitter.py` — update to use `Stage1Extractor('twibot')`
- [ ] `tests/test_features_stage3_twitter.py` — update to use `Stage3Extractor` or `build_graph_features_nodeidx` from `features.stage3`

---

## Manual-Only Verifications

*All phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
