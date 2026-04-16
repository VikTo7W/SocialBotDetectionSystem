---
phase: 6
slug: ablation-infrastructure-and-differentiator-features
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-15
---

# Phase 6 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest (tests/ directory, conftest.py, test_*.py files exist) |
| **Config file** | none detected |
| **Quick run command** | `pytest tests/test_features_stage2.py tests/test_ablation.py -x -q` |
| **Full suite command** | `pytest tests/ -x -q` |
| **Estimated runtime** | ~5 seconds (unit tests only) |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_features_stage2.py tests/test_ablation.py -x -q`
- **After every plan wave:** Run `pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 10 seconds

---

## Per-Task Verification Map

| Task ID | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|-------------|-----------|-------------------|-------------|--------|
| Wave 0 | 0 | FEAT-04 stubs | unit stubs | `pytest tests/test_features_stage2.py -x -q` | ❌ W0 | ⬜ pending |
| FEAT-04a | 1 | `cross_msg_sim_mean=0.0`, `near_dup_frac=0.0` for 0/1-message accounts | unit | `pytest tests/test_features_stage2.py::test_feat04_default_zero -x` | ❌ W0 | ⬜ pending |
| FEAT-04b | 1 | `cross_msg_sim_mean` matches `np.mean(off_diag)` for known messages | unit | `pytest tests/test_features_stage2.py::test_feat04_sim_mean -x` | ❌ W0 | ⬜ pending |
| FEAT-04c | 1 | `near_dup_frac` correctly counts pairs with cosine > 0.9 | unit | `pytest tests/test_features_stage2.py::test_feat04_near_dup -x` | ❌ W0 | ⬜ pending |
| FEAT-04d | 1 | Feature vector shape is (N, 397) after FEAT-04 | unit | `pytest tests/test_features_stage2.py -x -q` | ❌ W0 (needs 395→397 update) | ⬜ pending |
| RETRAIN | 2 | `trained_system_v12.joblib` exists after `main.py` run | manual | Run `main.py`; verify `trained_system_v12.joblib` on disk | manual-only | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_features_stage2.py` — extend with FEAT-04 stubs (3 new tests: `test_feat04_default_zero`, `test_feat04_sim_mean`, `test_feat04_near_dup`)
- [ ] Update shape assertion in existing test(s): `(1, 395)` → `(1, 397)`
- [ ] Add `NormalizedFakeEmbedder` to `conftest.py` (needed for FEAT-04 value tests; the `minimal_system` fixture itself needs no dimension changes — it calls `extract_stage2_features()` which auto-adapts)

*Note: conftest.py already exists; FakeEmbedder normalization note — FEAT-04 value tests need normalized embeddings (use `embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)` in tests or a NormalizedFakeEmbedder).*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Full cascade trains end-to-end, serializes to `trained_system_v12.joblib` | RETRAIN | Requires full BotSim-24 dataset, sentence-transformers, ~minutes of compute | Run `main.py`; verify `trained_system_v12.joblib` exists on disk after completion |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 10s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
