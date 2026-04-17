# Phase 9: Zero-Shot Inference Pipeline - Pattern Map

**Mapped:** 2026-04-16
**Files analyzed:** 1 new file (`evaluate_twibot20.py`) decomposed into 5 distinct components
**Analogs found:** 5 / 5

---

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match Quality |
|---|---|---|---|---|
| `evaluate_twibot20.py` — model loading block | utility | request-response | `main.py` lines 15–20 (`_load_pretrained_system_if_available`) | exact |
| `evaluate_twibot20.py` — predict_system invocation | service | request-response | `main.py` lines 152–154 (`predict_system` call on S3) | exact |
| `evaluate_twibot20.py` — monkey-patch block | utility | request-response | `tests/conftest.py` lines 156–173 (`minimal_system` fixture) | exact |
| `evaluate_twibot20.py` — column adapter | utility | transform | `botsim24_io.py` lines 100–184 (`build_account_table`) | role-match |
| `evaluate_twibot20.py` — JSON output + `__main__` | utility | file-I/O | `evaluate.py` lines 115–162 (report + print pattern) | role-match |

---

## Pattern Assignments

### Component 1: Model Loading

**Analog:** `main.py` lines 1–3 (imports) and lines 15–20 (`_load_pretrained_system_if_available`)

**Imports pattern** (`main.py` lines 1–3):
```python
from pathlib import Path
import joblib
from botdetector_pipeline import StageThresholds, train_system, predict_system
```

**Core model loading pattern** (`main.py` lines 15–20):
```python
def _load_pretrained_system_if_available(path: str = "trained_system.joblib"):
    artifact = Path(path)
    if not artifact.exists():
        return None
    print(f"[main] Loading pre-trained system from {artifact} for offline calibration/evaluation")
    return joblib.load(artifact)
```

**How to adapt for `evaluate_twibot20.py`:** Call `joblib.load(model_path)` directly inside `run_inference()` — no existence guard needed here since missing artifact should raise immediately (not silently return None as in training mode). Use `TrainedSystem` type annotation. The loaded object's `.th` attribute carries calibrated thresholds; pass `sys_loaded` directly to `predict_system()`.

**Key line** (`main.py` line 159):
```python
joblib.dump(sys, "trained_system_v12.joblib")
```
This confirms `joblib.load("trained_system_v12.joblib")` is the correct inverse.

---

### Component 2: `predict_system()` Invocation

**Analog:** `main.py` lines 150–154

**Core invocation pattern** (`main.py` lines 150–154):
```python
print("Running trained system on the test set")
# 5) Final evaluation on S3
out = predict_system(sys, df=S3, edges_df=edges_S3, nodes_total=len(users))
y_true = S3["label"].to_numpy()
report = evaluate_s3(out, y_true)
```

**`predict_system` signature** (`botdetector_pipeline.py` lines 634–639):
```python
def predict_system(
    sys: TrainedSystem,
    df: pd.DataFrame,
    edges_df: pd.DataFrame,
    nodes_total: Optional[int] = None,
) -> pd.DataFrame:
```

**Output schema** (`botdetector_pipeline.py` lines 701–712):
```python
return pd.DataFrame({
    "account_id": df["account_id"].astype(str).values,
    "p1": out1["p1"],
    "n1": out1["n1"],
    "p2": p2,
    "n2": out2["n2"],
    "amr_used": amr_mask.astype(int),
    "p12": p12,
    "stage3_used": stage3_mask.astype(int),
    "p3": p3,
    "n3": n3,
    "p_final": p_final,
})
```

**Critical requirement** (`botdetector_pipeline.py` line 702):
```python
"account_id": df["account_id"].astype(str).values,
```
`df["account_id"]` must be present — raises `KeyError` if missing. This is the column the adapter MUST populate from `record["ID"]`.

**`nodes_total` rule** (`botdetector_pipeline.py` lines 679, 375–376): `build_graph_features_nodeidx` allocates arrays of size `nodes_total`. Always pass `nodes_total=len(accounts_df)` — never hardcode. See PITFALL 3 in RESEARCH.md.

**`extract_stage1_matrix` call location** (`botdetector_pipeline.py` line 647):
```python
X1 = extract_stage1_matrix(df)
```
This is the name in `bp`'s namespace (imported at module level via `from features_stage1 import extract_stage1_matrix`). Patching `bp.extract_stage1_matrix` intercepts this call.

---

### Component 3: Monkey-Patch (Stage 1 Ratio Clamping)

**Analog:** `tests/conftest.py` lines 156–173 (`minimal_system` fixture)

**Established monkey-patch pattern** (`tests/conftest.py` lines 156–173):
```python
# Monkeypatch to handle predict_system's calling convention:
# predict_system calls: extract_stage1_matrix(df, cfg)
# Real signature:       extract_stage1_matrix(df)
def patched_extract_stage1_matrix(df, *args, **kwargs):
    return extract_stage1_matrix(df)

# predict_system calls: extract_stage2_features(df, cfg, sys.embedder)
# ...
def patched_extract_stage2_features(df, *args, **kwargs):
    for a in args:
        if hasattr(a, "encode"):
            return extract_stage2_features(df, a)
    return extract_stage2_features(df, fake_embedder)

monkeypatch.setattr(bp, "extract_stage1_matrix", patched_extract_stage1_matrix)
monkeypatch.setattr(bp, "extract_stage2_features", patched_extract_stage2_features)
```

**Imports required** (`tests/conftest.py` lines 20–21, 40–41):
```python
import botdetector_pipeline as bp
from features_stage1 import extract_stage1_matrix
from features_stage2 import extract_stage2_features
```

**How to adapt for `evaluate_twibot20.py`:** The conftest uses `monkeypatch.setattr` (pytest fixture). In `run_inference()` — which is not a test — use direct attribute assignment with a `try/finally` restore block:

```python
from features_stage1 import extract_stage1_matrix as _orig_extract_stage1_matrix
import botdetector_pipeline as bp

def _clamped_s1(df_inner, *args, **kwargs):
    X = _orig_extract_stage1_matrix(df_inner)
    X[:, 6:10] = np.clip(X[:, 6:10], 0.0, 50.0)  # TW-05: clamp post_c1/c2/ct/sr
    return X

bp.extract_stage1_matrix = _clamped_s1
try:
    results = predict_system(sys_loaded, df, edges_df, nodes_total=len(df))
finally:
    bp.extract_stage1_matrix = _orig_extract_stage1_matrix  # always restore
```

**Why `try/finally`:** The conftest relies on pytest teardown to restore state. `run_inference()` has no teardown mechanism, so `finally` is the correct substitute. It guarantees restoration even if `predict_system()` raises.

**Column indices confirmed** (`features_stage1.py` lines 19–37, per RESEARCH.md): Columns 6–9 of `extract_stage1_matrix()` output are `post_c1`, `post_c2`, `post_ct`, `post_sr` — the ratio features that blow up when Reddit columns are zero-filled. Slice is `X[:, 6:10]` (Python upper-exclusive).

---

### Component 4: Column Adapter (TwiBot-20 → Pipeline Schema)

**Analog:** `botsim24_io.py` lines 100–184 (`build_account_table`)

**Schema reference — what `predict_system()` requires** (`tests/conftest.py` lines 97–108):
```python
df = pd.DataFrame({
    "account_id": account_ids,    # str — MUST be present (line 702 of pipeline)
    "node_idx": node_idxs,        # int — required by build_graph_features_nodeidx
    "label": labels,              # int — not used by predict_system, but kept
    "username": usernames,        # str — used by extract_stage1_matrix
    "submission_num": submission_nums,   # float — Stage 1 ratio denominator
    "comment_num_1": comment_num_1s,     # float — Stage 1 ratio numerator
    "comment_num_2": comment_num_2s,     # float — Stage 1 ratio numerator
    "subreddit_list": subreddit_lists,   # list[str] — Stage 1 feature
    "profile": profiles,          # str — Stage 2 text feature
    "messages": messages_list,    # list[dict{text,ts,...}] — Stage 2 text feature
})
```

**BotSim-24 adapter pattern** (`botsim24_io.py` lines 169–183):
```python
rows.append({
    "account_id": uid,                              # str user ID
    "label": int(u["label"]),
    "username": (u.get("name") or ""),             # direct field mapping
    "profile": (u.get("description") or ""),
    "subreddit_list": sr_list,                      # list from parse_subreddits()
    "submission_num": float(u.get("submission_num", 0.0)),  # numeric cast
    "comment_num": float(u.get("comment_num", 0.0)),
    "comment_num_1": float(u.get("comment_num_1", 0.0)),
    "comment_num_2": float(u.get("comment_num_2", 0.0)),
    "messages": messages,                           # list[dict] with ts
})
```

**`twibot20_io.load_accounts()` output** (`twibot20_io.py` lines 41–50):
```python
rows.append({
    "node_idx": np.int32(idx),
    "screen_name": str(profile.get("screen_name", "") or "").strip(),
    "statuses_count": int(...),
    "followers_count": int(...),
    "friends_count": int(...),
    "created_at": str(...),
    "messages": messages,          # list[dict{text, ts=None, kind="tweet"}]
    "label": int(record["label"]),
})
```

**JSON re-read for `account_id`** (`twibot20_io.py` lines 79–81 — how `build_edges` does it):
```python
id_to_idx = {
    record["ID"]: int(accounts_df.iloc[i]["node_idx"])
    for i, record in enumerate(data)
}
```
Copy this iteration pattern. Both `load_accounts()` and the adapter iterate `enumerate(data)` — alignment is guaranteed by JSON array order.

**Complete adapter mapping** (decisions D-02, D-03, D-07):
```python
with open(path, "r", encoding="utf-8") as f:
    raw = json.load(f)
df = accounts_df.copy()
df["account_id"]     = [r["ID"] for r in raw]                    # D-07: Twitter user ID string
df["username"]       = df["screen_name"]                          # D-03: direct rename
df["submission_num"] = df["statuses_count"].astype(float)         # D-02: tweet count proxy
df["comment_num_1"]  = 0.0                                        # D-03: zero-fill
df["comment_num_2"]  = 0.0                                        # D-03: zero-fill
df["subreddit_list"] = [[] for _ in range(len(df))]              # D-03: empty list
```

---

### Component 5: JSON Output and `__main__` Block

**Analog:** `evaluate.py` lines 115–162 (return + print report pattern) and `main.py` lines 155–160 (save artifact pattern)

**Result serialization pattern — use pandas, not `json.dump`** (per RESEARCH.md Pitfall 5):
```python
# CORRECT: pandas handles numpy type coercion
results.to_json(out_path, orient="records", indent=2)

# WRONG: raises TypeError on numpy.float32 / numpy.int32
json.dump(results.to_dict(orient="records"), f)
```

**Print summary pattern** (`evaluate.py` lines 126–162 condensed, adapted):
```python
print(f"[twibot20] Saved {len(results)} results to {out_path}")
print(f"[twibot20] Stage 3 used: {results['stage3_used'].mean():.3f}")
print(f"[twibot20] AMR used:     {results['amr_used'].mean():.3f}")
print(f"[twibot20] p_final mean: {results['p_final'].mean():.4f}")
```
Copy the `[module_name]` prefix convention from `main.py` and `twibot20_io.py` print statements (e.g., `[main]`, `[twibot20]`).

**`__main__` argument pattern** (`main.py` line 28: `if __name__ == "__main__":`):
```python
if __name__ == "__main__":
    data_path  = sys.argv[1] if len(sys.argv) > 1 else "test.json"
    model_path = sys.argv[2] if len(sys.argv) > 2 else "trained_system_v12.joblib"

    results = run_inference(data_path, model_path)
    out_path = "results_twibot20.json"
    results.to_json(out_path, orient="records", indent=2)
    print(f"[twibot20] Saved {len(results)} results to {out_path}")
```

---

## Shared Patterns

### Module-Level Imports
**Source:** `twibot20_io.py` lines 1–9, `evaluate.py` lines 1–14, `main.py` lines 1–12

Copy this import header structure:
```python
"""<one-line module docstring>"""
from __future__ import annotations

import json
import sys

import joblib
import numpy as np
import pandas as pd

from twibot20_io import load_accounts, build_edges, validate
from features_stage1 import extract_stage1_matrix as _orig_extract_stage1_matrix
import botdetector_pipeline as bp
from botdetector_pipeline import predict_system, TrainedSystem
```

**Convention:** stdlib first, then third-party, then project-local. `from __future__ import annotations` is present in `twibot20_io.py` and `botsim24_io.py` — use it. Alias the original `extract_stage1_matrix` with `_orig_` prefix (leading underscore = module-private, per Python convention).

### Print Logging Convention
**Source:** `twibot20_io.py` lines 142–144, `main.py` lines 18–19

All print statements use `[module_name]` prefix:
```python
print(f"[twibot20] accounts: {n}, edges: {len(edges_df)}")
print(f"[main] Loading pre-trained system from {artifact}")
```
Use `[twibot20]` as the prefix in `evaluate_twibot20.py`.

### Docstring Style
**Source:** `twibot20_io.py` lines 14–27 (NumPy-style), `evaluate.py` lines 38–66 (Google-style)

Both styles are present. `evaluate.py` uses Google-style (Args/Returns sections). Copy `evaluate.py`'s Google-style for `run_inference()` since it is a public API function like `evaluate_s3()`.

---

## No Analog Found

All components have direct analogs in the codebase. No greenfield patterns are required.

---

## Metadata

**Analog search scope:** `main.py`, `botsim24_io.py`, `twibot20_io.py`, `evaluate.py`, `tests/conftest.py`, `botdetector_pipeline.py` lines 634–713
**Files read:** 6
**Pattern extraction date:** 2026-04-16
