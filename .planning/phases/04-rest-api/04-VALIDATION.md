---
phase: 4
slug: rest-api
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 4 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.3.4 |
| **Config file** | none — discovered via tests/ directory |
| **Quick run command** | `pytest tests/test_api.py -x -q` |
| **Full suite command** | `pytest tests/ -x -q` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_api.py -x -q`
- **After every plan wave:** Run `pytest tests/ -x -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 15 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 4-W0-01 | 04-01 | 0 | API-01/02/03 | integration stubs | `pytest tests/test_api.py -x -q` | ❌ W0 | ⬜ pending |
| 4-01-01 | 04-01 | 1 | API-01 | integration | `pytest tests/test_api.py::test_predict_returns_200 -x` | ✅ W0 | ⬜ pending |
| 4-01-02 | 04-01 | 1 | API-01 | integration | `pytest tests/test_api.py::test_predict_output_range -x` | ✅ W0 | ⬜ pending |
| 4-01-03 | 04-01 | 1 | API-02 | integration | `pytest tests/test_api.py::test_startup_loads_system -x` | ✅ W0 | ⬜ pending |
| 4-01-04 | 04-01 | 1 | API-03 | integration | `pytest tests/test_api.py::test_missing_account_id_returns_422 -x` | ✅ W0 | ⬜ pending |
| 4-01-05 | 04-01 | 1 | API-03 | integration | `pytest tests/test_api.py::test_wrong_type_returns_422 -x` | ✅ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `pip install fastapi==0.135.1 uvicorn==0.42.0` — framework install
- [ ] `tests/test_api.py` — 5 test stubs covering API-01, API-02, API-03; use `minimal_system` fixture from conftest.py serialized to a temp joblib file; patch MODEL_PATH via monkeypatch
- [ ] Verify `joblib`, `httpx`, `pydantic` are importable before writing implementation tasks

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Server starts from real `trained_system.joblib` and loads ~90MB model in <30s | API-02 | Requires real TrainedSystem + real SentenceTransformer model; too slow for unit tests | Run `uvicorn api:app`, send curl POST /predict with valid JSON, confirm 200 response |
| API correctly degrades Stage 3 for single-account (all-zero graph features) | API-01 | Requires end-to-end inference with real model | Run curl POST /predict, check p_final is a reasonable float (not NaN, not 0.5 exactly) |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 15s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
