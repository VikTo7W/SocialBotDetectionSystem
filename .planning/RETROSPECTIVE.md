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

## Milestone: v1.1 — Feature Leakage Audit & Fix

**Shipped:** 2026-04-16
**Phases:** 3 | **Plans:** 6

### What Was Built

- Leakage removal from Stage 2a: username/profile embeddings and profile AMR anchor eliminated; character_setting dropped from build_account_table
- 3 behavioral features: cv_intervals, char_len_mean/std, hour_entropy (FEAT-01/02/03); feature vector 391→395 dims
- 2 cross-message similarity features: cross_msg_sim_mean, near_dup_frac (FEAT-04); feature vector 395→397 dims
- Full cascade retrain: trained_system_v11.joblib (395-dim clean baseline), trained_system_v12.joblib (397-dim with FEAT-04)
- ablation_tables.py: 4 paper-table builders with monkey-patch masking helper and LaTeX export via pd.to_latex()
- 36 tests passing; ABL-01 and ABL-03 requirements correctly identified as obsolete and dropped

### What Worked

- **Code inspection over AUC threshold:** Leakage removal confirmed by static analysis, not by hitting a target AUC. Avoided chasing a metric that turned out to be legitimately high (0.97-0.98) on this dataset
- **Atomic leakage fix:** Both leakage paths fixed in a single commit + retrain prevented partial-fix artifacts from polluting the artifact history
- **v11/v12 artifact versioning:** Preserving v11 alongside v12 as a 395-dim baseline made the leakage audit table tractable without re-running old code
- **TDD for FEAT-04:** NormalizedFakeEmbedder test harness caught the correct index placement (395, 396) before implementation
- **Dropping ABL-01/ABL-03 early:** Recognized during planning that force-routing was already implicit in evaluate_s3() — saved a full plan of unnecessary work

### What Was Inefficient

- **AUC criterion over-specified in ROADMAP:** The success criterion "AUC below 90%" was wrong for BotSim-24 and had to be overridden mid-phase. Domain-specific expected ranges should be validated before writing success criteria
- **results_v10.json not capturable:** v1.0 model is incompatible with the 395-dim extractor — baseline metrics must come from git history instead. A version-pinned metrics capture step before any feature changes would have avoided this
- **Phase 7 end-to-end run deferred:** ablation_tables.py is tested against synthetic data only; the actual paper numbers still require a worktree retrain. A phased plan that separates "build + unit test" from "run on real data" is cleaner but leaves the milestone technically incomplete

### Patterns Established

- Monkey-patch target is the module where the name is imported, not where it's defined (from-import creates local binding)
- masked_predict copies input arrays before zeroing columns — never mutate arrays returned by the extractor
- Feature indices documented explicitly in SUMMARY.md (e.g., "appended at indices 395-396") for cross-plan traceability

### Key Lessons

1. Write success criteria in terms of code properties (no X in file Y), not performance thresholds, when the expected range is uncertain
2. Capture version-pinned baseline metrics immediately at the start of any milestone that modifies features — before any changes land
3. ABL-type requirements often duplicate what evaluation code already provides; verify against existing eval output before planning

### Cost Observations

- Model mix: sonnet for execution, opus for planning
- Sessions: ~4 sessions across 3 phases over 3 days
- Notable: Recognizing obsolete requirements early (ABL-01, ABL-03) saved approximately one full plan of implementation

---

## Cross-Milestone Trends

| Milestone | Phases | Plans | Issues Found Late | Key Win |
|-----------|--------|-------|-------------------|---------|
| v1.0 | 4 | 5 | 2 (calling convention + NaN) | TDD foundation with minimal_system fixture |
| v1.1 | 3 | 6 | 1 (results_v10.json not capturable) | Atomic leakage fix; obsolete requirements dropped early |

### Top Lessons (Verified Across Milestones)

1. Validate assumptions about existing code before writing code that depends on it (calling conventions, expected output shapes, AUC ranges)
2. TDD with minimal fixtures pays compounding returns — minimal_system and NormalizedFakeEmbedder both caught index/signature bugs before implementation
3. Metrics capture must happen before changes land — retroactive retrieval from git history is painful
