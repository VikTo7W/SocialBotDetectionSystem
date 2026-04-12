# Retrospective

## Milestone: v1.0 — MVP

**Shipped:** 2026-04-12
**Phases:** 4 | **Plans:** 5

### What Was Built

- Optuna TPE threshold calibration over 10 routing dimensions (S2 split, reproducible with SEED=42)
- Paper-ready S3 evaluation module: overall F1/AUC/precision/recall + per-stage metrics + routing statistics
- FastAPI REST API: POST /predict with Pydantic validation, lifespan model loading, joblib serialization
- Batch inference script (run_batch.py) for offline scoring of custom datasets with documentation
- 26-test suite covering calibration (6), evaluation (15), and API (5)

### What Worked

- **TDD approach:** Writing test stubs first (02-01, 04-01) before implementation made the implementations clean and requirements clear
- **Optuna over scikit-optimize:** Python 3.13 incompatibility caught early; Optuna was the right call
- **Modular files:** Each capability (calibrate.py, evaluate.py, api.py) is self-contained — no tangled dependencies
- **Calling convention patch in botdetector_pipeline.py:** Fixing the root bug directly rather than patching around it in api.py was cleaner

### What Was Inefficient

- **Calling convention bug discovered late:** `predict_system()` called `extract_stage1_matrix(df, cfg)` but the real signature is `(df)` — this broke calibration and had to be found and fixed during execution
- **NaN profile crash:** `features_stage2.py` did `(r.get("profile") or "").strip()` which fails on float NaN — should have been guarded in original code
- **Phase 1 had no plans:** Pipeline integration was treated as "pre-existing" but the pipeline had actual bugs. It would have been caught earlier with a real Phase 1 execution plan

### Patterns Established

- `minimal_system` fixture in `conftest.py` as the reusable test foundation — every subsequent phase built on it
- Eager module-level joblib.load pattern for TestClient compatibility (vs. async lifespan)
- Paper-ready report via plain `print()` — no tabulate/rich dependency added

### Key Lessons

- Always validate calling conventions of existing functions before writing code that depends on them
- NaN handling in text fields must be explicit: `str(x or "").strip()` not `(x or "").strip()`
- Pre-existing code needs a real integration test phase, not a "trust it works" assumption

### Cost Observations

- Model mix: primarily sonnet for execution, opus for planning
- Sessions: multiple sessions across pipeline fixes and phase execution
- Notable: background `main.py` run caught two bugs (NaN profile + calling convention) that weren't caught by tests written against mocks

## Cross-Milestone Trends

| Milestone | Phases | Plans | Issues Found Late | Key Win |
|-----------|--------|-------|-------------------|---------|
| v1.0 | 4 | 5 | 2 (calling convention + NaN) | TDD foundation with minimal_system fixture |
