---
phase: 04-rest-api
plan: "02"
subsystem: api
tags: [fastapi, pydantic, joblib, lifespan, calling-convention-patch, single-account-inference]
dependency_graph:
  requires:
    - "04-01: tests/test_api.py test stubs, minimal_system fixture, FastAPI/uvicorn installed"
    - "02-01: TrainedSystem dataclass with stage1/stage2a/amr_refiner/meta12/stage3/meta123"
    - "features_stage1.extract_stage1_matrix: real sig (df)"
    - "features_stage2.extract_stage2_features: real sig (df, embedder)"
  provides:
    - "api.py: FastAPI app with lifespan, /predict endpoint, Pydantic validation"
    - "POST /predict: accepts AccountRequest JSON, returns p_final float + label 0|1"
  affects:
    - "Production deployment: uvicorn api:app from project root"
tech_stack:
  added: []
  patterns:
    - "Module-level eager joblib.load for test compatibility (TestClient without lifespan context)"
    - "Async lifespan context manager for production server startup"
    - "Module-level monkeypatch of botdetector_pipeline.extract_stage1_matrix and extract_stage2_features"
    - "EMPTY_EDGES DataFrame for single-account Stage 3 graph inference"
    - "Sync route (def predict) to avoid blocking event loop with CPU-bound inference"
key_files:
  created:
    - api.py
  modified: []
decisions:
  - "Eager module-level joblib.load in addition to lifespan load — ensures TestClient fixtures work without entering lifespan context (Starlette 0.52.1 behavior)"
  - "Calling convention patch at module level (bp.extract_stage1_matrix, bp.extract_stage2_features) rather than fixing predict_system — follows conftest.py pattern, avoids touching pipeline code"
  - "nodes_total=1 and node_idx=0 for single-account Stage 3 inference — zero-degree features degrade gracefully through meta123"
metrics:
  duration: "3 minutes"
  completed: "2026-03-19"
  tasks_completed: 1
  files_created: 1
  files_modified: 0
---

# Phase 4 Plan 02: FastAPI /predict Endpoint Implementation Summary

FastAPI api.py with lifespan model loading, Pydantic AccountRequest/PredictResponse models, module-level calling convention patch, and sync /predict route — all 5 integration tests pass.

## What Was Built

**Task 1: Implement api.py with lifespan, Pydantic models, and /predict endpoint**

Created `api.py` in project root with:

- **Calling convention patch** (module-level): `bp.extract_stage1_matrix` and `bp.extract_stage2_features` are replaced with wrapper functions that strip the extra `cfg` positional argument that `predict_system()` incorrectly passes. Follows the same pattern as `tests/conftest.py`.

- **MODEL_PATH**: `os.environ.get("MODEL_PATH", "trained_system.joblib")` — evaluated at module import time so `importlib.reload` in test fixtures picks up the patched env var.

- **EMPTY_EDGES**: Empty DataFrame with `src/dst/weight/etype` columns typed correctly for `build_graph_features_nodeidx()`. Used for single-account inference where no graph context exists.

- **Lifespan**: `@asynccontextmanager async def lifespan(app)` loads `joblib.load(MODEL_PATH)` into `app.state.system` at server startup. Used in production via `uvicorn api:app`.

- **Eager load**: `app.state.system = joblib.load(MODEL_PATH)` at module level (after `app` is created). Required because `TestClient(app)` used without `with` in test fixtures does not trigger the lifespan context — `app.state.system` would otherwise be unset during tests.

- **Pydantic models**: `MessageItem(BaseModel)` with `extra="allow"`, `AccountRequest(BaseModel)` with required `account_id`/`username` and optional numeric/list/text fields, `PredictResponse(BaseModel)` with `p_final: float` and `label: int`.

- **`_to_dataframe()`**: Converts `AccountRequest` to single-row DataFrame. Sets `node_idx=np.int32(0)` and `label=0` as required by `predict_system()`.

- **`/predict` route** (sync, not async): Calls `predict_system()` with `EMPTY_EDGES` and `nodes_total=1`. Catches `ValueError`/`RuntimeError` and re-raises as HTTP 422. Returns `PredictResponse`.

## Commits

| Hash | Message |
|------|---------|
| 85496cd | feat(04-02): implement api.py with lifespan, Pydantic models, and /predict endpoint |

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Eager module-level model load for TestClient compatibility**

- **Found during:** Task 1 verification — all 5 tests failed with `AttributeError: 'State' object has no attribute 'system'`
- **Issue:** Starlette 0.52.1 `TestClient` only runs the lifespan context manager when entered via `with TestClient(app)`. The test fixture uses `return TestClient(app)` (no `with`), so the lifespan never fires and `app.state.system` is never set.
- **Fix:** Added `app.state.system = joblib.load(MODEL_PATH)` at module level immediately after `app` is created. The lifespan is still present (satisfying the `grep "async def lifespan"` acceptance criterion and production use). When `importlib.reload` runs in the test fixture after setting `MODEL_PATH` env var, this module-level load fires with the correct path.
- **Files modified:** api.py
- **Commit:** 85496cd

## Verification Results

All checks passed:
- `pytest tests/test_api.py -x -q` — 5 passed
- `pytest tests/ -x -q` — 26 passed (full suite green, no regressions)
- `grep "class AccountRequest" api.py` — FOUND
- `grep "class PredictResponse" api.py` — FOUND
- `grep "async def lifespan" api.py` — FOUND
- `grep "def predict" api.py` — FOUND (sync, not async)
- `grep "EMPTY_EDGES" api.py` — FOUND
- `grep "MODEL_PATH" api.py` — FOUND
- `grep "bp.extract_stage1_matrix" api.py` — FOUND
- No `on_event` in api.py
- No `train_system` in api.py

## Self-Check: PASSED

Files exist:
- api.py: FOUND

Commits exist:
- 85496cd: FOUND
