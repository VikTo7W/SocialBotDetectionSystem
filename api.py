from __future__ import annotations
from contextlib import asynccontextmanager
from typing import List, Optional
import os

import numpy as np
import pandas as pd
import joblib
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel, Field

from cascade_pipeline import CascadePipeline, infer_dataset

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
MODEL_PATH = os.environ.get("MODEL_PATH", "trained_system_botsim.joblib")

EMPTY_EDGES = pd.DataFrame({
    "src": pd.array([], dtype=np.int32),
    "dst": pd.array([], dtype=np.int32),
    "weight": pd.array([], dtype=np.float32),
    "etype": pd.array([], dtype=np.int8),
})

# ---------------------------------------------------------------------------
# Lifespan: load model once at startup, store in app.state
# ---------------------------------------------------------------------------
@asynccontextmanager
async def lifespan(app: FastAPI):
    app.state.system = joblib.load(MODEL_PATH)
    yield


app = FastAPI(title="Bot Detector API", lifespan=lifespan)

# Eager load at module level so TestClient fixtures (which do not enter the
# lifespan context) can still access app.state.system during tests.
# In production, the lifespan handler above re-loads the model on startup.
app.state.system = joblib.load(MODEL_PATH)

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Adapter: convert AccountRequest -> single-row DataFrame
# ---------------------------------------------------------------------------

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

# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------

@app.post("/predict", response_model=PredictResponse)
def predict(req: AccountRequest, request: Request):
    df = _to_dataframe(req)
    try:
        system = request.app.state.system
        dataset = infer_dataset(df, system.cfg)
        pipeline = CascadePipeline(dataset=dataset, cfg=system.cfg, embedder=system.embedder)
        result = pipeline.predict(
            system,
            df,
            EMPTY_EDGES,
            nodes_total=1,
        )
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=422, detail=str(exc))
    p_final = float(result["p_final"].iloc[0])
    return PredictResponse(p_final=p_final, label=int(p_final >= 0.5))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)