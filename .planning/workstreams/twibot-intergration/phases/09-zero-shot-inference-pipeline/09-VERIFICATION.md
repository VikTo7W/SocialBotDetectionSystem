---
phase: 09-zero-shot-inference-pipeline
verified: 2026-04-16T00:00:00Z
status: passed
score: 7/7 must-haves verified
overrides_applied: 0
re_verification: null
gaps: []
deferred: []
human_verification: []
---

# Phase 09: Zero-Shot Inference Pipeline Verification Report

**Phase Goal:** Deliver evaluate_twibot20.py — a script that runs trained_system_v12.joblib on TwiBot-20 test accounts zero-shot (no retraining), adapts TwiBot-20 columns to BotSim-24 pipeline schema, applies Stage 1 ratio clamping, and exposes run_inference(path, model_path) -> pd.DataFrame for Phase 10 to import.
**Verified:** 2026-04-16
**Status:** passed
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | tests/test_evaluate_twibot20.py exists with all 5 stubs that now pass | VERIFIED | File exists at tests/test_evaluate_twibot20.py; pytest collected 5 tests, all PASSED |
| 2 | run_inference() returns a DataFrame with exactly 11 columns: account_id, p1, n1, p2, n2, amr_used, p12, stage3_used, p3, n3, p_final (TW-04) | VERIFIED | test_run_inference_returns_correct_schema PASSED; function signature confirmed: run_inference(path: str, model_path: str = "trained_system_v12.joblib") -> pd.DataFrame |
| 3 | Stage 1 ratio columns 6-9 are clamped to [0.0, 50.0] inside predict_system() when called from run_inference() — high statuses_count does not produce values > 50.0 in those columns (TW-05) | VERIFIED | test_ratio_clamping_applied PASSED; _clamped_s1 closure applies np.clip(X[:, 6:10], 0.0, 50.0) at evaluate_twibot20.py line 84; monkey-patch at line 87; test confirms p_final is NaN-free and in [0,1] |
| 4 | bp.extract_stage1_matrix is restored to _orig_extract_stage1_matrix after run_inference() returns, even if predict_system() raises | VERIFIED | finally block at evaluate_twibot20.py line 92-93; isolation confirmed by runtime check: `bp.extract_stage1_matrix is orig` assertion passes |
| 5 | __main__ block calls run_inference() and saves results_twibot20.json using results.to_json(orient='records', indent=2) | VERIFIED | test_main_block_saves_json PASSED; __main__ block at lines 98-110 of evaluate_twibot20.py; to_json at line 104: results.to_json(out_path, orient="records", indent=2) |
| 6 | Print summary shows account count, bot count, and p_final mean with [twibot20] prefix | VERIFIED | evaluate_twibot20.py lines 105-110 print 5 summary lines with [twibot20] prefix including bot count and p_final mean |
| 7 | BotSim-24 direct path is NOT clamped — extract_stage1_matrix() called directly produces X1[:,6:10] > 50.0 (isolation) | VERIFIED | test_botsim_path_not_clamped PASSED; direct call to features_stage1.extract_stage1_matrix with statuses_count=100000, comment columns zero, confirms X1[:,6:10].max() > 50.0 |

**Score:** 7/7 truths verified

### Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `evaluate_twibot20.py` | run_inference() public function + column adapter + __main__ block | VERIFIED | 111 lines; substantive implementation; imports from twibot20_io, botdetector_pipeline, features_stage1 |
| `tests/test_evaluate_twibot20.py` | 5 unit tests covering TW-04 and TW-05 | VERIFIED | 238 lines; all 5 tests PASSED; exports test_run_inference_returns_correct_schema, test_run_inference_end_to_end, test_main_block_saves_json, test_ratio_clamping_applied, test_botsim_path_not_clamped |

### Key Link Verification

| From | To | Via | Status | Details |
|------|----|-----|--------|---------|
| evaluate_twibot20.py:_clamped_s1 | botdetector_pipeline.bp.extract_stage1_matrix | direct attribute assignment before predict_system() call | WIRED | Line 87: `bp.extract_stage1_matrix = _clamped_s1` confirmed present |
| evaluate_twibot20.py:run_inference | twibot20_io.load_accounts | function call at top of run_inference() | WIRED | Line 55: `accounts_df = load_accounts(path)` confirmed present |
| evaluate_twibot20.py:column adapter | test.json record["ID"] | json.load() re-read to extract account_id | WIRED | Line 70: `df["account_id"] = [r["ID"] for r in raw]` confirmed present |
| evaluate_twibot20.py:__main__ | results_twibot20.json | results.to_json(orient='records') | WIRED | Line 104: `results.to_json(out_path, orient="records", indent=2)` confirmed present |
| test_botsim_path_not_clamped | features_stage1.extract_stage1_matrix | direct import call | WIRED | test calls extract_stage1_matrix(df) directly (not via run_inference); confirmed PASSED |

### Data-Flow Trace (Level 4)

Level 4 data-flow tracing is not applicable to this phase. The phase delivers an inference adapter script, not a component that renders data from a live database. The primary data flows are:

- TwiBot-20 JSON file -> load_accounts() -> accounts_df -> column adapter -> predict_system() -> results DataFrame (returned to caller)
- These flows are exercised by the 5 unit tests using mocked I/O, confirming the adapter chain is connected end-to-end.

### Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| run_inference() importable | python -c "from evaluate_twibot20 import run_inference; print('import OK')" | "import OK" | PASS |
| All 5 unit tests pass | python -m pytest tests/test_evaluate_twibot20.py -v -q | 5 passed in 1.81s | PASS |
| Full test suite passes (no regressions) | python -m pytest tests/ -x -q | 72 passed, 0 failed | PASS |
| Monkey-patch isolation confirmed | python -c "assert bp.extract_stage1_matrix is orig; print('isolation confirmed')" | isolation confirmed | PASS |
| evaluate_twibot20.py syntax valid | python -c "import ast; ast.parse(open('evaluate_twibot20.py').read()); print('syntax OK')" | "syntax OK" | PASS |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|-------------|-------------|--------|----------|
| TW-04 | 09-01-PLAN.md, 09-02-PLAN.md | User can run zero-shot inference on TwiBot-20 test accounts via evaluate_twibot20.py using trained_system_v12.joblib unchanged — no retraining, full cascade runs as-is | SATISFIED | run_inference() implemented; loads model via joblib.load(); calls predict_system() without retraining; returns 11-column DataFrame; confirmed by test_run_inference_returns_correct_schema and test_run_inference_end_to_end |
| TW-05 | 09-01-PLAN.md, 09-02-PLAN.md | TwiBot-20 inference path clamps Stage 1 ratio features (columns 6-9 of extract_stage1_matrix output) to [0.0, 50.0], preventing cascade routing collapse from divide-by-zero on zero-filled Reddit-specific columns | SATISFIED | Monkey-patch pattern implemented in run_inference(); _clamped_s1 applies np.clip(X[:, 6:10], 0.0, 50.0); finally block restores original; confirmed by test_ratio_clamping_applied and test_botsim_path_not_clamped |

**Note:** TW-06 and TW-07 are mapped to Phase 10 in REQUIREMENTS.md — not in scope for Phase 9. TW-01, TW-02, TW-03 are mapped to Phase 8 and are prerequisites fulfilled before this phase.

### Anti-Patterns Found

No anti-patterns detected.

- No TODO/FIXME/placeholder comments in evaluate_twibot20.py (grep confirmed 0 matches)
- No empty implementations or stub returns
- No hardcoded empty data that flows to rendering
- The `# __main__ block implemented in Plan 02` comment was a planned placeholder that was properly replaced in Plan 02
- No console.log-only implementations (Python equivalent: no print-only handlers)
- Deprecation warning in tests/test_features_stage2.py for datetime.utcfromtimestamp() is pre-existing, unrelated to Phase 9, and is a warning not an error

### Human Verification Required

None. All must-haves are fully verifiable programmatically through the test suite and code inspection. The phase goal — a script that runs trained_system_v12.joblib on TwiBot-20 test accounts zero-shot — requires real data files (test.json, trained_system_v12.joblib) for end-to-end execution, but the inference logic, column adapter, clamping, and Phase 10 import contract are all verified by the 5 passing unit tests using mocked I/O and a minimal_system fixture.

### Gaps Summary

No gaps. All 7 observable truths are verified, both artifacts exist and are substantive, all 5 key links are wired, both requirements (TW-04, TW-05) are satisfied, and the full test suite (72 tests) passes with no regressions.

---

_Verified: 2026-04-16_
_Verifier: Claude (gsd-verifier)_
