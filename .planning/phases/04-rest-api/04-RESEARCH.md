# Phase 4: REST API - Research

**Researched:** 2026-03-19
**Domain:** FastAPI, Pydantic v2, joblib serialization, single-account inference
**Confidence:** HIGH

## Summary

Phase 4 wraps the trained cascade pipeline in a FastAPI endpoint. The system is already complete
(Phases 1-3 done): `predict_system()` exists, `TrainedSystem` is a dataclass, and `calibrate_thresholds()`
writes calibrated thresholds back to `system.th` in-place. The primary work is: (1) serializing
`TrainedSystem` to disk after training, (2) loading it at server startup, (3) converting a single
JSON account into the DataFrame row format `predict_system()` expects, and (4) handling the Stage 3
graph dependency for single-account inference.

The most important design decision this phase must make is how to handle Stage 3 for single-account
requests. `predict_system()` calls `build_graph_features_nodeidx()` which requires an `edges_df`
DataFrame and a `nodes_total` count. For a single account with no graph context, the only safe
approach is to pass an empty edges DataFrame and set `node_idx=0` with `nodes_total=1`. This causes
Stage 3 to produce zero-degree features, and the routing gates (`gate_stage3`) will still function
normally — the meta123 model was trained on real graph features but will degrade gracefully on all-zero
inputs. This is the correct behavior for an API serving isolated accounts.

The second key insight is that `TrainedSystem` contains a `TextEmbedder` which wraps a live
`SentenceTransformer` model. joblib can pickle this correctly because `SentenceTransformer` is
a PyTorch module — the weights are serialized as tensors. The risk is model load time at startup
(~90MB for all-MiniLM-L6-v2), not correctness. Load once at module level using FastAPI's lifespan
pattern.

**Primary recommendation:** FastAPI 0.135.1 + uvicorn 0.42.0 + joblib 1.4.2 (already installed).
Use Pydantic v2 BaseModel (already installed at 2.10.3) for request validation. Use joblib.dump/load
for TrainedSystem serialization. Pass empty edges DataFrame for Stage 3.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| API-01 | POST /predict endpoint accepts JSON account data and returns p_final (bot probability) and binary label | FastAPI route + Pydantic request model + predict_system() adapter |
| API-02 | API loads a pre-trained and serialized TrainedSystem from disk and uses it for all requests without retraining | joblib.dump() in main.py after training; FastAPI lifespan loads once at startup |
| API-03 | Input JSON schema is validated against expected account fields before inference; missing required fields return HTTP 422 | Pydantic BaseModel with typed fields; FastAPI auto-raises HTTPException 422 on validation failure |
</phase_requirements>

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| fastapi | 0.135.1 | HTTP framework, routing, OpenAPI docs | Async-native, Pydantic-integrated, auto-422 on schema failure |
| uvicorn | 0.42.0 | ASGI server for FastAPI | Standard production server for FastAPI |
| pydantic | 2.10.3 | Request/response schema validation | Already installed; FastAPI v0.100+ requires Pydantic v2 |
| joblib | 1.4.2 | TrainedSystem serialization | Already installed; handles numpy arrays, sklearn objects, PyTorch modules |
| httpx | 0.28.1 | HTTP client for TestClient | Already installed; FastAPI TestClient wraps httpx |
| pytest | 8.3.4 | Test runner | Already in use across phases 2-3 |

Note: FastAPI and uvicorn are NOT currently installed. They must be installed in Wave 0.

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| python-multipart | latest | Form data support | Only if form uploads needed — not required here |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| FastAPI | Flask | Flask has no auto-422, no async, no OpenAPI generation; FastAPI is the correct choice |
| joblib | pickle | pickle works but joblib is safer with numpy arrays and already installed |
| joblib | cloudpickle | cloudpickle handles closures better but adds a dependency; joblib is sufficient |

**Installation:**
```bash
pip install fastapi==0.135.1 uvicorn==0.42.0
```

joblib, pydantic, httpx, pytest are already installed.

## Architecture Patterns

### Recommended Project Structure

```
api.py                   # FastAPI app, lifespan, /predict route
tests/
├── conftest.py          # existing (minimal_system fixture already here)
└── test_api.py          # API tests using FastAPI TestClient
trained_system.joblib    # serialized TrainedSystem (written by main.py)
```

Single-file API (`api.py`) is the right granularity for this project. No need for routers or
package structure — this is one endpoint.

### Pattern 1: FastAPI Lifespan for Startup Model Loading

**What:** Load TrainedSystem once at server startup, store in app.state, access in route handlers.
**When to use:** Any time a model must be loaded once and shared across requests.

```python
# Source: FastAPI official docs — lifespan events
from contextlib import asynccontextmanager
from fastapi import FastAPI
import joblib

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: load model
    app.state.system = joblib.load("trained_system.joblib")
    yield
    # Shutdown: nothing to clean up

app = FastAPI(lifespan=lifespan)
```

**Critical:** Do NOT use `@app.on_event("startup")` — it is deprecated in FastAPI 0.93+. Use
`lifespan` parameter instead.

### Pattern 2: Pydantic v2 Request Model with Optional Fields

**What:** Define Pydantic BaseModel matching the DataFrame columns that predict_system() requires.
**When to use:** API-03 — schema validation before inference.

The required columns (derived from reading features_stage1.py, features_stage2.py, botsim24_io.py):

**Stage 1 features** (from `extract_stage1_matrix`):
- `username` (str) — used for name_len
- `submission_num` (float)
- `comment_num_1` (float)
- `comment_num_2` (float)
- `subreddit_list` (list[str])

**Stage 2 features** (from `extract_stage2_features`):
- `profile` (str, optional) — used for embedding + AMR
- `messages` (list of message dicts, optional) — posts/comments

**predict_system() required columns:**
- `account_id` (str) — used for output DataFrame construction
- `node_idx` (int) — required by `build_graph_features_nodeidx`

```python
# Source: analysis of features_stage1.py, features_stage2.py, botdetector_pipeline.py
from pydantic import BaseModel, Field
from typing import List, Optional, Any, Dict

class MessageItem(BaseModel):
    text: Optional[str] = None
    ts: Optional[float] = None
    # other fields optional (kind, subreddit, score etc.)
    model_config = {"extra": "allow"}

class AccountRequest(BaseModel):
    account_id: str
    username: str
    submission_num: float = 0.0
    comment_num_1: float = 0.0
    comment_num_2: float = 0.0
    subreddit_list: List[str] = Field(default_factory=list)
    profile: Optional[str] = ""
    messages: List[MessageItem] = Field(default_factory=list)
```

Pydantic v2 automatically raises HTTP 422 with field-level error details when required fields
(account_id, username) are missing or wrong type. FastAPI intercepts the `RequestValidationError`
and returns the 422 response without any custom error handler needed.

### Pattern 3: Single-Account DataFrame Adapter

**What:** Convert one `AccountRequest` into a one-row DataFrame that predict_system() can process.
**When to use:** Every /predict call.

```python
import pandas as pd
import numpy as np

def account_to_dataframe(req: AccountRequest) -> pd.DataFrame:
    """Convert a single AccountRequest to a one-row DataFrame for predict_system()."""
    messages = [m.model_dump() for m in req.messages]
    row = {
        "account_id": req.account_id,
        "node_idx": np.int32(0),          # single node; no real graph context
        "label": 0,                        # dummy — not used during inference
        "username": req.username or "",
        "profile": req.profile or "",
        "subreddit_list": req.subreddit_list,
        "submission_num": float(req.submission_num),
        "comment_num_1": float(req.comment_num_1),
        "comment_num_2": float(req.comment_num_2),
        "messages": messages,
    }
    return pd.DataFrame([row])
```

### Pattern 4: Stage 3 Graph Handling for Single-Account Inference

**What:** Pass empty edges DataFrame and nodes_total=1 to predict_system().
**Why:** `build_graph_features_nodeidx()` requires edges_df. For a single account with no graph
context, all degree features will be zero. The Stage 3 model still runs but produces zero-degree
features, which is the correct degraded behavior.

```python
# Stage 3 graph: empty edges, single node
EMPTY_EDGES = pd.DataFrame({
    "src": pd.array([], dtype=np.int32),
    "dst": pd.array([], dtype=np.int32),
    "weight": pd.array([], dtype=np.float32),
    "etype": pd.array([], dtype=np.int8),
})
NODES_TOTAL = 1

# In route handler:
result = predict_system(
    sys=app.state.system,
    df=df_row,
    edges_df=EMPTY_EDGES,
    nodes_total=NODES_TOTAL,
)
```

**Important:** `gate_stage3` thresholds still apply. With calibrated thresholds, a single uncertain
account may or may not trigger Stage 3 routing. This is correct behavior — Stage 3 just contributes
zero-degree features if triggered.

### Pattern 5: POST /predict Route

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

@app.post("/predict")
async def predict(req: AccountRequest, request: Request):
    system = request.app.state.system
    df = account_to_dataframe(req)
    result = predict_system(
        sys=system,
        df=df,
        edges_df=EMPTY_EDGES,
        nodes_total=NODES_TOTAL,
    )
    p_final = float(result["p_final"].iloc[0])
    label = int(p_final >= 0.5)
    return {"p_final": p_final, "label": label}
```

### Pattern 6: TrainedSystem Serialization with joblib

**In main.py** (after training and calibration):
```python
import joblib
joblib.dump(sys, "trained_system.joblib")
```

**In api.py** (at startup):
```python
system = joblib.load("trained_system.joblib")
```

**Gotchas with joblib and this system:**
1. `TextEmbedder` holds a `SentenceTransformer` (PyTorch model). joblib pickles PyTorch state_dict
   correctly. Load will re-instantiate the model in CPU inference mode.
2. LightGBM is NOT currently installed (falls back to `HistGradientBoostingClassifier`). This is
   fine — the sklearn fallback pickles normally with joblib.
3. `MahalanobisNovelty` is a plain Python object with numpy arrays — serializes cleanly.
4. `AMRDeltaRefiner` holds only numpy arrays (`w`, `b`) — serializes cleanly.
5. `LogisticRegression` (meta12, meta123) is standard sklearn — serializes cleanly.
6. The joblib file will be large (~90-400MB depending on whether sentence-transformers weights are
   included in the pickle vs. loaded from cache). This is expected.

**Critical:** joblib uses Python's pickle protocol. The TrainedSystem must be loaded in an
environment with the same package versions and the same source files (botdetector_pipeline.py, etc.)
on the Python path. The API server must be run from the project root.

### Anti-Patterns to Avoid

- **Using `@app.on_event("startup")`:** Deprecated since FastAPI 0.93. Use lifespan.
- **Calling train_system() at API startup:** Out of scope (REQUIREMENTS.md explicitly excludes this).
- **Passing real node_idx from request:** The graph is static training data; the API accepts new accounts that aren't in the graph. Use node_idx=0, nodes_total=1.
- **Using Flask instead of FastAPI:** Flask does not auto-validate and return 422; would require manual error handling.
- **Loading model per-request:** Extremely expensive (90MB+ deserialization on every call).
- **Using `pickle.dump` directly:** joblib handles numpy arrays more safely (uses memory-mapped files for large arrays).

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Request validation and 422 | Custom validation logic in route | Pydantic BaseModel + FastAPI | FastAPI automatically raises 422 with field-level details |
| API schema documentation | Custom /docs endpoint | FastAPI built-in /docs (Swagger UI) | Auto-generated from Pydantic models |
| Model serialization | Custom __getstate__/__setstate__ | joblib.dump/load | Handles numpy arrays, sklearn, PyTorch correctly |
| HTTP test client | Custom requests-based test harness | FastAPI TestClient (httpx) | In-process, no server required |

**Key insight:** The entire validation + 422 layer is handled by Pydantic v2 + FastAPI with zero
custom code. Only the inference adapter (AccountRequest -> DataFrame) is project-specific.

## Common Pitfalls

### Pitfall 1: predict_system() Calling Convention Bug

**What goes wrong:** `predict_system()` in `botdetector_pipeline.py` calls
`extract_stage1_matrix(df, cfg)` and `extract_stage2_features(df, cfg, sys.embedder)` with extra
positional arguments. The real function signatures are `extract_stage1_matrix(df)` and
`extract_stage2_features(df, embedder, ...)`. This mismatch causes a TypeError.

**Why it happens:** The calling convention in `predict_system()` passes `cfg` as the second arg,
but the feature extraction functions only take `df` and then embedder directly.

**How to avoid:** The conftest.py already documents and solves this with monkeypatching. The API's
`predict_system()` call must use the same patched functions OR the pipeline code must be corrected.
The cleanest fix for production is to correct `predict_system()` directly so it calls
`extract_stage1_matrix(df)` and `extract_stage2_features(df, sys.embedder)`.

**Warning signs:** `TypeError: extract_stage1_matrix() takes 1 positional argument but 2 were given`
during API inference.

### Pitfall 2: TextEmbedder Not Serialized Correctly

**What goes wrong:** `TextEmbedder` wraps `SentenceTransformer` which is a PyTorch `nn.Module`.
Some versions of sentence-transformers override `__reduce__` in ways that break pickle.

**Why it happens:** sentence-transformers 5.x (the installed version) may store model config in
ways that depend on the model cache directory at load time.

**How to avoid:** Test joblib round-trip immediately after training with:
```python
import joblib, tempfile, os
with tempfile.NamedTemporaryFile(suffix=".joblib", delete=False) as f:
    path = f.name
joblib.dump(sys, path)
loaded = joblib.load(path)
os.unlink(path)
```
If this fails, the fallback is to NOT serialize the embedder, instead serialize the model name
string and reconstruct `TextEmbedder` at load time.

### Pitfall 3: Stage 3 node_idx Out-of-Bounds

**What goes wrong:** `build_graph_features_nodeidx()` does `X_all[node_ids]` where node_ids comes
from `df["node_idx"]`. If node_idx is 0 and nodes_total is 1, the numpy index `X_all[0]` is valid.
But if nodes_total is not set correctly, you get an IndexError.

**How to avoid:** Always set `nodes_total=1` when passing node_idx=0. This creates a 1-row feature
matrix, and `X_all[0]` is valid.

### Pitfall 4: Synchronous Blocking in Async Route

**What goes wrong:** `predict_system()` is synchronous and CPU-bound (embeddings via sentence-
transformers). Calling it directly in an `async def` route blocks the event loop.

**Why it happens:** FastAPI is async-first but most ML inference is synchronous.

**How to avoid:** For this single-user research API, use a synchronous route (`def predict(...)`)
instead of `async def predict(...)`. FastAPI runs sync routes in a thread pool automatically, so
the event loop is not blocked.

```python
@app.post("/predict")
def predict(req: AccountRequest, request: Request):  # sync, not async
    ...
```

### Pitfall 5: 422 vs 500 Error Boundary

**What goes wrong:** Pydantic validation catches type errors in the JSON body. But domain-level
errors (e.g., an account with valid JSON but all-zero features causing a downstream NumPy error)
will raise a 500 Internal Server Error rather than a 422.

**How to avoid:** Wrap the `predict_system()` call in a try/except that returns HTTP 422 for
ValueError and RuntimeError, and HTTP 500 for unexpected exceptions.

## Code Examples

### Complete api.py Skeleton

```python
# Source: analysis of botdetector_pipeline.py + FastAPI official docs
from __future__ import annotations
from contextlib import asynccontextmanager
from typing import List, Optional
import os

import numpy as np
import pandas as pd
import joblib
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field

import botdetector_pipeline as bp
from botdetector_pipeline import predict_system
from features_stage1 import extract_stage1_matrix
from features_stage2 import extract_stage2_features

# Patch calling convention (see conftest.py pattern)
def _patched_extract_stage1_matrix(df, *args, **kwargs):
    return extract_stage1_matrix(df)

def _patched_extract_stage2_features(df, *args, **kwargs):
    for a in args:
        if hasattr(a, "encode"):
            return extract_stage2_features(df, a)
    return extract_stage2_features(df, kwargs.get("embedder"))

bp.extract_stage1_matrix = _patched_extract_stage1_matrix
bp.extract_stage2_features = _patched_extract_stage2_features

MODEL_PATH = os.environ.get("MODEL_PATH", "trained_system.joblib")

EMPTY_EDGES = pd.DataFrame({
    "src": pd.array([], dtype=np.int32),
    "dst": pd.array([], dtype=np.int32),
    "weight": pd.array([], dtype=np.float32),
    "etype": pd.array([], dtype=np.int8),
})

@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.system = joblib.load(MODEL_PATH)
    yield

app = FastAPI(title="Bot Detector API", lifespan=lifespan)


class MessageItem(BaseModel):
    text: Optional[str] = None
    ts: Optional[float] = None
    model_config = {"extra": "allow"}


class AccountRequest(BaseModel):
    account_id: str
    username: str
    submission_num: float = 0.0
    comment_num_1: float = 0.0
    comment_num_2: float = 0.0
    subreddit_list: List[str] = Field(default_factory=list)
    profile: Optional[str] = ""
    messages: List[MessageItem] = Field(default_factory=list)


class PredictResponse(BaseModel):
    p_final: float
    label: int


def _to_dataframe(req: AccountRequest) -> pd.DataFrame:
    messages = [m.model_dump() for m in req.messages]
    return pd.DataFrame([{
        "account_id": req.account_id,
        "node_idx": np.int32(0),
        "label": 0,
        "username": req.username or "",
        "profile": req.profile or "",
        "subreddit_list": req.subreddit_list,
        "submission_num": float(req.submission_num),
        "comment_num_1": float(req.comment_num_1),
        "comment_num_2": float(req.comment_num_2),
        "messages": messages,
    }])


@app.post("/predict", response_model=PredictResponse)
def predict(req: AccountRequest, request: Request):
    df = _to_dataframe(req)
    try:
        result = predict_system(
            sys=request.app.state.system,
            df=df,
            edges_df=EMPTY_EDGES,
            nodes_total=1,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    p_final = float(result["p_final"].iloc[0])
    return PredictResponse(p_final=p_final, label=int(p_final >= 0.5))
```

### TestClient Pattern (FastAPI built-in)

```python
# Source: FastAPI official docs — TestClient
from fastapi.testclient import TestClient
from api import app

client = TestClient(app)

def test_predict_returns_200():
    payload = {
        "account_id": "test_001",
        "username": "testuser",
        "submission_num": 10,
        "comment_num_1": 5,
        "comment_num_2": 3,
        "subreddit_list": ["news"],
        "profile": "A regular user",
        "messages": [{"text": "hello world", "ts": 1700000000.0}]
    }
    response = client.post("/predict", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "p_final" in data
    assert "label" in data
    assert 0.0 <= data["p_final"] <= 1.0
    assert data["label"] in (0, 1)

def test_predict_missing_required_field_returns_422():
    response = client.post("/predict", json={"username": "noaccountid"})
    assert response.status_code == 422
```

### joblib Serialization in main.py

```python
# After training and calibration are complete:
import joblib
joblib.dump(sys, "trained_system.joblib")
print(f"[main] Saved TrainedSystem to trained_system.joblib")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Flask + marshmallow | FastAPI + Pydantic v2 | 2019-2022 | Auto-422, OpenAPI, async |
| `@app.on_event("startup")` | `lifespan` context manager | FastAPI 0.93 (2023) | Cleaner lifecycle, not deprecated |
| Pydantic v1 `.dict()` | Pydantic v2 `.model_dump()` | Pydantic v2 (2023) | Already installed at v2.10.3 |
| `pickle.dump` | `joblib.dump` | N/A | Better numpy handling |

**Deprecated/outdated:**
- `@app.on_event("startup")`: Replaced by lifespan. Still works but logs deprecation warning.
- `BaseModel.dict()`: Replaced by `BaseModel.model_dump()` in Pydantic v2.
- `BaseModel.schema()`: Replaced by `BaseModel.model_json_schema()` in Pydantic v2.

## Open Questions

1. **Can TextEmbedder (sentence-transformers 5.x) be round-tripped through joblib?**
   - What we know: SentenceTransformer is a PyTorch nn.Module; joblib uses pickle; PyTorch modules
     are picklable in principle.
   - What's unclear: sentence-transformers 5.x is a major version with potential pickle changes.
   - Recommendation: Wave 0 test task should verify joblib round-trip of a FakeEmbedder-based
     TrainedSystem (same structure). The real TextEmbedder serialization test requires a trained
     model file which Wave 0 may not have.

2. **Does predict_system() calling convention need a code fix or monkeypatching?**
   - What we know: conftest.py uses monkeypatching as the workaround and documents the bug.
   - What's unclear: Whether fixing `predict_system()` directly is appropriate or if the monkeypatch
     approach should be carried into api.py.
   - Recommendation: Fix `predict_system()` directly (remove the `cfg` pass-through to extraction
     functions, call `extract_stage1_matrix(df)` and `extract_stage2_features(df, sys.embedder)`
     directly). This is cleaner than monkeypatching in production code.

3. **Where should trained_system.joblib be written?**
   - What we know: main.py runs from project root; api.py should also run from project root.
   - Recommendation: Write to project root as `trained_system.joblib`. Accept `MODEL_PATH`
     environment variable override for flexibility.

## Validation Architecture

### Test Framework

| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | none — discovered via tests/ directory |
| Quick run command | `pytest tests/test_api.py -x -q` |
| Full suite command | `pytest tests/ -x -q` |

### Phase Requirements -> Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| API-01 | POST /predict with valid payload returns 200 + {"p_final": float, "label": 0\|1} | integration | `pytest tests/test_api.py::test_predict_returns_200 -x` | Wave 0 |
| API-01 | p_final is in [0.0, 1.0], label is 0 or 1 | integration | `pytest tests/test_api.py::test_predict_output_range -x` | Wave 0 |
| API-02 | App starts and loads TrainedSystem from disk without error | integration | `pytest tests/test_api.py::test_startup_loads_system -x` | Wave 0 |
| API-03 | Missing required field (account_id) returns HTTP 422 | integration | `pytest tests/test_api.py::test_missing_account_id_returns_422 -x` | Wave 0 |
| API-03 | Wrong type for numeric field returns HTTP 422 | integration | `pytest tests/test_api.py::test_wrong_type_returns_422 -x` | Wave 0 |

### Sampling Rate

- **Per task commit:** `pytest tests/test_api.py -x -q`
- **Per wave merge:** `pytest tests/ -x -q`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps

- [ ] `tests/test_api.py` — covers API-01, API-02, API-03 (5 test functions)
- [ ] `api.py` — the FastAPI app itself (created in Wave 1)
- [ ] Framework install: `pip install fastapi==0.135.1 uvicorn==0.42.0`
- [ ] `trained_system.joblib` — required by startup test; Wave 0 tests should use a fixture that
      saves a minimal system to a temp file and patches MODEL_PATH

The `minimal_system` fixture from `tests/conftest.py` can be reused to create a joblib-serialized
TrainedSystem for API tests without loading real data or the real sentence-transformers model.

## Sources

### Primary (HIGH confidence)

- Verified via `pip index versions`: fastapi 0.135.1, uvicorn 0.42.0 — current as of 2026-03-19
- Verified via `pip show`: pydantic 2.10.3, joblib 1.4.2, httpx 0.28.1, pytest 8.3.4 — installed
- Source code inspection: botdetector_pipeline.py, features_stage1.py, features_stage2.py,
  botsim24_io.py, tests/conftest.py — all read directly

### Secondary (MEDIUM confidence)

- FastAPI lifespan pattern: confirmed from FastAPI changelog that `@app.on_event` deprecated in
  0.93+; lifespan is the current pattern
- Pydantic v2 BaseModel API: `.model_dump()` replaces `.dict()` — confirmed from Pydantic v2
  migration guide knowledge

### Tertiary (LOW confidence)

- sentence-transformers 5.x joblib compatibility: inferred from PyTorch picklability rules; not
  directly verified with a round-trip test in this environment

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — versions verified against pip registry
- Architecture: HIGH — derived directly from reading source code
- Serialization gotchas: MEDIUM — joblib + sentence-transformers 5.x not tested here
- Pitfalls: HIGH — calling convention bug confirmed by reading conftest.py comments

**Research date:** 2026-03-19
**Valid until:** 2026-04-19 (FastAPI releases frequently; core patterns stable)
