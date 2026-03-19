---
phase: 2
slug: threshold-calibration
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-19
---

# Phase 2 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest |
| **Config file** | none — Wave 0 installs |
| **Quick run command** | `pytest tests/test_calibrate.py -x -q` |
| **Full suite command** | `pytest tests/ -q` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/test_calibrate.py -x -q`
- **After every plan wave:** Run `pytest tests/ -q`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 2-W0-01 | 01 | 0 | CALIB-01/02/03 | unit stubs | `pytest tests/test_calibrate.py -x -q` | ❌ W0 | ⬜ pending |
| 2-01-01 | 01 | 1 | CALIB-01 | unit | `pytest tests/test_calibrate.py::test_calibrate_runs -xq` | ✅ W0 | ⬜ pending |
| 2-01-02 | 01 | 1 | CALIB-01 | unit | `pytest tests/test_calibrate.py::test_threshold_bounds -xq` | ✅ W0 | ⬜ pending |
| 2-01-03 | 01 | 1 | CALIB-02 | unit | `pytest tests/test_calibrate.py::test_metric_switching -xq` | ✅ W0 | ⬜ pending |
| 2-01-04 | 01 | 1 | CALIB-02 | unit | `pytest tests/test_calibrate.py::test_invalid_metric -xq` | ✅ W0 | ⬜ pending |
| 2-01-05 | 01 | 1 | CALIB-03 | unit | `pytest tests/test_calibrate.py::test_th_persisted -xq` | ✅ W0 | ⬜ pending |
| 2-01-06 | 01 | 1 | CALIB-01/03 | unit | `pytest tests/test_calibrate.py::test_reproducibility -xq` | ✅ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_calibrate.py` — stubs for CALIB-01, CALIB-02, CALIB-03 (6 test functions, each raises NotImplementedError until implementation lands)
- [ ] `tests/conftest.py` — 50-account synthetic fixture (random numeric features, random labels) usable without real BotSim-24 data
- [ ] `pip install optuna==4.8.0` verified before writing tasks (confirm: `python -c "import optuna; print(optuna.__version__)"`)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Calibration on real S2 improves F1 vs default thresholds | CALIB-01 | Requires full trained system + real dataset; not feasible in fast unit tests | Run `main.py` with and without calibration, compare F1 on S3 |
| n_trials=200 converges (best value stable across last 50 trials) | CALIB-01 | Stochastic convergence; no deterministic assertion | Plot optuna study history; check variance of best_value across trials 150-200 |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
