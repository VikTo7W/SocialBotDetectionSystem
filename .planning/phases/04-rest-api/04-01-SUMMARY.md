---
phase: 04-rest-api
plan: "01"
subsystem: api
tags: [fastapi, uvicorn, joblib, serialization, test-stubs, integration-tests]
dependency_graph:
  requires:
    - "03-01: evaluate.py and main.py wired with evaluate_s3"
    - "02-01: conftest.py minimal_system fixture"
  provides:
    - "tests/test_api.py: 5 integration test stubs for api.py"
    - "main.py: joblib.dump serialization after calibration"
    - "FastAPI + uvicorn installed and importable"
  affects:
    - "04-02: api.py implementation must satisfy the test contracts defined here"
tech_stack:
  added:
    - fastapi==0.135.1
    - uvicorn==0.42.0
  patterns:
    - "importlib.reload for post-monkeypatch module import in fixtures"
    - "joblib.dump for TrainedSystem serialization"
    - "TestClient from fastapi.testclient for in-process API testing"
key_files:
  created:
    - tests/test_api.py
  modified:
    - main.py
decisions:
  - "importlib.reload used in client fixture to ensure MODEL_PATH env var is read before api module initializes"
  - "No module-level from-api imports in test file — all api imports inside client fixture only"
  - "joblib.dump placed after evaluate_s3 call so serialized system includes calibrated thresholds"
metrics:
  duration: "2 minutes"
  completed: "2026-03-19"
  tasks_completed: 2
  files_created: 1
  files_modified: 1
---

# Phase 4 Plan 01: FastAPI Install + Test Stubs Summary

FastAPI 0.135.1 + uvicorn 0.42.0 installed, main.py serializes TrainedSystem to trained_system.joblib after evaluation, and tests/test_api.py has 5 integration test stubs covering API-01/02/03.

## What Was Built

**Task 1: Install FastAPI + uvicorn and add joblib serialization to main.py**

- Installed `fastapi==0.135.1` and `uvicorn==0.42.0` via pip
- Added `import joblib` at the top of `main.py` (line 1, before other imports)
- Added two lines after `report = evaluate_s3(out, y_true)` in main.py:
  - `joblib.dump(sys, "trained_system.joblib")` — serializes the full TrainedSystem including calibrated thresholds
  - `print(f"[main] Saved TrainedSystem to trained_system.joblib")` — confirmation message

**Task 2: Create test stubs for API in tests/test_api.py**

Created `tests/test_api.py` with:
- `VALID_PAYLOAD` module-level dict with all required account fields
- `client` fixture: serializes `minimal_system` to `tmp_path/test_system.joblib`, patches `MODEL_PATH` env var, uses `importlib.reload(api_module)` to re-evaluate the module after env var is set, returns `TestClient(app)`
- 5 test functions:
  1. `test_predict_returns_200` — POST /predict returns 200 with `p_final` and `label` keys
  2. `test_predict_output_range` — p_final in [0.0, 1.0], label in {0, 1}, consistent with threshold 0.5
  3. `test_startup_loads_system` — `client.app.state.system` is not None and has `stage1`
  4. `test_missing_account_id_returns_422` — missing account_id returns 422
  5. `test_wrong_type_returns_422` — string value for submission_num returns 422

## Commits

| Hash | Message |
|------|---------|
| a50d77c | feat(04-01): install FastAPI + uvicorn, add joblib serialization to main.py |
| bd7914f | feat(04-01): create test stubs for API in tests/test_api.py |

## Deviations from Plan

None — plan executed exactly as written.

## Verification Results

All verification checks passed:
- `python -c "import fastapi, uvicorn, joblib, httpx; print('all imports OK')"` — passes
- `grep "joblib.dump" main.py` — line 121: `joblib.dump(sys, "trained_system.joblib")`
- `python -c "import ast; ast.parse(open('tests/test_api.py').read()); print('syntax OK')"` — passes
- `grep -c "def test_" tests/test_api.py` — returns 5

## Next Steps

Plan 04-02 must implement `api.py` with:
- `MODEL_PATH = os.environ.get("MODEL_PATH", "trained_system.joblib")`
- FastAPI lifespan loading `joblib.load(MODEL_PATH)` into `app.state.system`
- `AccountRequest` Pydantic model with all required fields from `VALID_PAYLOAD`
- POST `/predict` route returning `{"p_final": float, "label": int}`
- Calling convention patch for `predict_system()` (see conftest.py monkeypatch pattern)

## Self-Check: PASSED

Files exist:
- tests/test_api.py: FOUND
- main.py (with joblib.dump): FOUND

Commits exist:
- a50d77c: FOUND
- bd7914f: FOUND
