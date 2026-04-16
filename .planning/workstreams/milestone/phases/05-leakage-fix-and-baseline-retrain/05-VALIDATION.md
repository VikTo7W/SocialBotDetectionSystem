---
phase: 5
slug: leakage-fix-and-baseline-retrain
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-13
---

# Phase 5 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (tests/ directory, conftest.py, test_*.py files exist) |
| **Config file** | none detected |
| **Quick run command** | `pytest tests/test_features_stage2.py -x -q` |
| **Full suite command** | `pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds (unit tests only) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_features_stage2.py -x -q`
- **After every plan wave:** Run `pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| Wave 0 | 01 | 0 | LEAK-02, LEAK-03, LEAK-04, FEAT-01, FEAT-02, FEAT-03 | unit stubs | `pytest tests/test_features_stage2.py tests/test_botsim24_io.py -x -q` | ❌ W0 | ⬜ pending |
| LEAK-02 | 01 | 1 | No identity in embedding pool | unit | `pytest tests/test_features_stage2.py::test_no_identity_in_embeddings -x` | ❌ W0 | ⬜ pending |
| LEAK-03a | 01 | 1 | AMR zero vector for no-message accounts | unit | `pytest tests/test_features_stage2.py::test_amr_zero_for_no_messages -x` | ❌ W0 | ⬜ pending |
| LEAK-03b | 01 | 1 | AMR uses message text, not profile field | unit | `pytest tests/test_features_stage2.py::test_amr_uses_message_not_profile -x` | ❌ W0 | ⬜ pending |
| LEAK-04 | 01 | 1 | character_setting absent from build_account_table | unit | `pytest tests/test_botsim24_io.py::test_no_character_setting_in_table -x` | ❌ W0 | ⬜ pending |
| FEAT-01a | 01 | 1 | cv_intervals = 0.0 for 0/1 message accounts | unit | `pytest tests/test_features_stage2.py::test_feat01_default_zero -x` | ❌ W0 | ⬜ pending |
| FEAT-01b | 01 | 1 | cv_intervals = delta_std / max(delta_mean, 1e-6) | unit | `pytest tests/test_features_stage2.py::test_feat01_formula -x` | ❌ W0 | ⬜ pending |
| FEAT-02a | 01 | 1 | char_len_mean/std = 0.0 for no-message accounts | unit | `pytest tests/test_features_stage2.py::test_feat02_default_zero -x` | ❌ W0 | ⬜ pending |
| FEAT-02b | 01 | 1 | char_len stats correct for known messages | unit | `pytest tests/test_features_stage2.py::test_feat02_values -x` | ❌ W0 | ⬜ pending |
| FEAT-03a | 01 | 1 | hour_entropy = 0.0 for 0/1 timestamp | unit | `pytest tests/test_features_stage2.py::test_feat03_default_zero -x` | ❌ W0 | ⬜ pending |
| FEAT-03b | 01 | 1 | hour_entropy uses UTC hours from timestamps | unit | `pytest tests/test_features_stage2.py::test_feat03_entropy_value -x` | ❌ W0 | ⬜ pending |
| LEAK-01 | 01 | manual | Stage 2a AUC < 90% after retrain | manual | Run `main.py`, check Stage 2a AUC printed — requires BotSim-24 data | manual-only | ⬜ pending |
| LEAK-05 | 01 | manual | Full cascade trains and serializes to trained_system_v11.joblib | manual | Run `main.py` end-to-end — requires BotSim-24 data and sentence-transformers | manual-only | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_features_stage2.py` — unit stubs for LEAK-02, LEAK-03, FEAT-01, FEAT-02, FEAT-03
- [ ] `tests/test_botsim24_io.py` — unit stub for LEAK-04

*Note: conftest.py already exists; minimal_system fixture must be updated to reflect the new 395-feature vector shape after this phase.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Stage 2a AUC < 90% on S3 | LEAK-01 | Requires loading full BotSim-24 dataset and running inference | Run `main.py` after all code fixes; check printed S3 Stage 2a AUC is below 90% |
| Full cascade trains end-to-end, serializes to `trained_system_v11.joblib` | LEAK-05 | Requires full dataset, sentence-transformers, ~minutes of compute | Run `main.py`; verify `trained_system_v11.joblib` exists on disk after completion |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
