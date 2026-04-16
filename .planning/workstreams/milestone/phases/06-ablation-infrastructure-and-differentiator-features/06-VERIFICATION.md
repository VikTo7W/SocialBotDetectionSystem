---
phase: 06-ablation-infrastructure-and-differentiator-features
verified: 2026-04-15T00:00:00Z
status: passed
score: 6/6 must-haves verified
---

# Phase 6: Ablation Infrastructure and Differentiator Features — Verification Report

**Phase Goal:** Add cross-message cosine similarity features (FEAT-04) to Stage 2a, growing the feature vector from 395 to 397 dims, and update main.py to save trained_system_v12.joblib after retrain.
**Verified:** 2026-04-15
**Status:** PASSED
**Re-verification:** No — initial verification

---

## Goal Achievement

### Observable Truths

| #  | Truth                                                                       | Status     | Evidence                                                                                          |
|----|-----------------------------------------------------------------------------|------------|---------------------------------------------------------------------------------------------------|
| 1  | extract_stage2_features() produces (N, 397) shape                           | VERIFIED   | Concatenation: 384 (emb) + 4 (ling) + 7 (temporal) + 2 (FEAT-04) = 397; confirmed by dimension math and 39/39 tests passing |
| 2  | cross_msg_sim_mean at index 395                                              | VERIFIED   | features_stage2.py line 121: `np.array([cross_msg_sim_mean, near_dup_frac])` appended last; index 395 = 384+4+7+0 |
| 3  | near_dup_frac at index 396                                                  | VERIFIED   | Same concatenation; index 396 = 384+4+7+1; test_features_stage2.py lines 263-270 assert both indices explicitly |
| 4  | Both features default to 0.0 for accounts with 0 or 1 messages             | VERIFIED   | features_stage2.py lines 67-68 (1 message: else branch), lines 74-75 (0 messages: empty texts branch); test_feat04_zero_message_accounts asserts feat[0,395]==0.0 and feat[0,396]==0.0 for both cases |
| 5  | main.py saves trained_system_v12.joblib                                     | VERIFIED   | main.py lines 130-131: `joblib.dump(sys, "trained_system_v12.joblib")` present                   |
| 6  | main.py trained_system_v11.joblib save line still present (not overwritten) | VERIFIED   | main.py lines 128-129: `joblib.dump(sys, "trained_system_v11.joblib")` present; both v11 and v12 saves coexist |

**Score:** 6/6 truths verified

---

### Required Artifacts

| Artifact                  | Provides                                   | Status     | Details                                                                 |
|---------------------------|--------------------------------------------|------------|-------------------------------------------------------------------------|
| `features_stage2.py`      | extract_stage2_features() with FEAT-04     | VERIFIED   | 124 lines; cross_msg_sim_mean and near_dup_frac computed and appended at indices 395/396 |
| `main.py`                 | v12 joblib save alongside v11              | VERIFIED   | Lines 128-131 contain both dump calls                                   |
| `tests/test_features_stage2.py` | FEAT-04 unit tests                   | VERIFIED   | Tests cover: zero-message account, one-message account, cross_msg_sim_mean value correctness, near_dup_frac value correctness |

---

### Key Link Verification

| From                         | To                                  | Via                                      | Status   | Details                                                                                     |
|------------------------------|-------------------------------------|------------------------------------------|----------|---------------------------------------------------------------------------------------------|
| `features_stage2.py`         | `botdetector_pipeline.py`           | `from features_stage2 import extract_stage2_features` | WIRED | Used at lines 540, 567, 651 in botdetector_pipeline.py                        |
| `features_stage2.py`         | `api.py`                            | `from features_stage2 import extract_stage2_features` | WIRED | Imported at line 15, patched at line 40 for signature compatibility              |
| `cross_msg_sim_mean / near_dup_frac` | `feat` vector              | `np.concatenate([..., np.array([cross_msg_sim_mean, near_dup_frac])])` | WIRED | Line 121; appended as last 2 elements of every row vector                |
| `main.py` v12 save           | `trained_system_v12.joblib`         | `joblib.dump(sys, "trained_system_v12.joblib")` | WIRED | Line 130; immediately after v11 save                                             |

---

### Requirements Coverage

| Requirement | Description                                                                         | Status    | Evidence                                                                                                          |
|-------------|-------------------------------------------------------------------------------------|-----------|-------------------------------------------------------------------------------------------------------------------|
| FEAT-04     | Stage 2a includes cross-message cosine similarity and near-duplicate fraction       | SATISFIED | features_stage2.py implements both; indices 395/396 confirmed; 0-message and 1-message defaults to 0.0 confirmed; REQUIREMENTS.md line 50 checked [x]; status table line 108: "Complete" |
| ABL-01      | Ablation infrastructure (predict_system runs all stages; evaluate_s3 reports per-stage metrics) | OBSOLETE  | Marked obsolete during planning — both behaviors already existed before this phase; no new code required |

---

### Anti-Patterns Found

| File                  | Line | Pattern                         | Severity | Impact    |
|-----------------------|------|---------------------------------|----------|-----------|
| `features_stage2.py`  | 111  | `datetime.utcfromtimestamp()`   | INFO     | Deprecation warning in Python 3.12+; does not affect correctness or test results; pre-existing (FEAT-03, not FEAT-04) |

No blockers. No stubs. No unimplemented handlers.

---

### Human Verification Required

None. All observable truths for this phase are verifiable programmatically through static analysis and test results.

---

### Gaps Summary

No gaps. All 6 must-haves are satisfied:

- The feature vector grows from 395 to 397 dims via the two-element append in `features_stage2.py` line 121.
- Index positions 395 and 396 are exact by the fixed concatenation order (384 + 4 + 7 + 2).
- The 0-message and 1-message edge cases default to 0.0 via two separate guard branches.
- Both `trained_system_v11.joblib` and `trained_system_v12.joblib` dump calls are present and distinct in `main.py`.
- FEAT-04 is marked `[x]` Complete in REQUIREMENTS.md.
- All 39 tests pass with no failures.

---

_Verified: 2026-04-15_
_Verifier: Claude (gsd-verifier)_
