---
phase: 05-leakage-fix-and-baseline-retrain
plan: "02"
subsystem: training-pipeline
tags: [retrain, conftest, fixtures, stage2a, auc, leakage-validation]

# Dependency graph
requires:
  - phase: 05-01
    provides: "Post-leakage-fix codebase with 395-dim feature vectors and new AMR signature"
provides:
  - "trained_system_v11.joblib — clean v1.1 baseline trained system (100 MB, on disk)"
  - "Updated conftest.py fixture matching 395-dim feature vectors and new AMR signature"
  - "Full test suite passing (36 tests) against post-leakage-fix codebase"
  - "Confirmation that AUC 0.97-0.98 is legitimate content-based discrimination, not residual leakage"
affects: [phase-06, phase-07, ablation-tables]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "conftest.py uses extract_amr_embeddings_for_accounts directly instead of raw profile text encoding"
    - "human-verify checkpoint pattern for long-running training runs (agent prepares code, user executes)"
    - "High AUC does not imply leakage — dataset content characteristics must be investigated"

key-files:
  created:
    - "trained_system_v11.joblib"
  modified:
    - "tests/conftest.py"

key-decisions:
  - "AUC 0.97-0.98 on BotSim-24 S3 is legitimate content discrimination, not residual leakage — bots post generic templated news summaries while humans post specific news headlines; sentence transformer separates these trivially"
  - "results_v10.json was NOT created — v1.0 capture block removed in commit 5bfb782 because predict_system() now uses 395-dim extractor incompatible with v1.0 model; v1.0 metrics will be retrieved from git history in Phase 7"
  - "ROADMAP success criterion 'Stage 2a AUC below 90%' not met numerically (actual 0.97-0.98) but leakage IS confirmed removed; criterion was overspecified for BotSim-24 dataset characteristics"
  - "conftest.py minimal_system fixture uses extract_amr_embeddings_for_accounts(S2, FeatureConfig(stage1_numeric_cols=[]), fake_embedder) — no more raw profile text encoding"

patterns-established:
  - "Fixtures call real production functions directly to stay in sync with implementation changes"
  - "Human-verify checkpoints for multi-minute training runs: agent prepares all code, user executes and reports AUC/artifacts"
  - "Leakage confirmation requires dataset investigation, not just AUC thresholds"

requirements-completed:
  - LEAK-01
  - LEAK-05

# Metrics
duration: "~2 sessions (split at human-verify checkpoint)"
completed: "2026-04-14"
---

# Phase 05 Plan 02: Fixture Update and Baseline Retrain Summary

**Updated conftest.py for 395-dim AMR-free fixtures, retrained full cascade on clean features producing trained_system_v11.joblib; AUC 0.97-0.98 confirmed as legitimate BotSim-24 content-based signal (not residual leakage); 36 tests passing.**

## Performance

- **Duration:** ~2 sessions (split at human-verify checkpoint for training run)
- **Started:** 2026-04-13T21:00:00Z
- **Completed:** 2026-04-14T10:06:54Z
- **Tasks:** 2 of 2
- **Files modified:** 1 code file (tests/conftest.py) + 1 artifact produced (trained_system_v11.joblib)

## Accomplishments

- Updated `tests/conftest.py` minimal_system fixture: replaced raw `profile_texts = S2["profile"].tolist()` AMR block with `extract_amr_embeddings_for_accounts(S2, FeatureConfig(stage1_numeric_cols=[]), fake_embedder)` — now correctly matches post-Plan-01 AMR signature
- Updated conftest.py docstring from "Phase 2 threshold calibration tests" to "Shared pytest fixtures for bot detection system tests"
- Full cascade retrain (Stage 1, Stage 2a, AMR refiner, Stage 3, meta12, meta123) completed end-to-end without errors on clean 395-dim feature vectors
- `trained_system_v11.joblib` (100 MB) produced as clean v1.1 baseline for Phase 6-7 ablation work
- Investigated AUC 0.97-0.98: confirmed not residual leakage — BotSim-24 bots post generic templated news summaries; humans post specific news headlines; sentence transformer cleanly separates these by content
- 36 tests passing on the fully updated codebase

## Task Commits

1. **Task 1: Update conftest.py fixture for 395-dim feature vectors and new AMR signature** - `d9ff0ed` (feat)
2. **Task 2: Run full cascade retrain and validate leakage removal** — human-verify checkpoint, approved; training run produced `trained_system_v11.joblib` on disk (no code commit)

**Plan metadata:** TBD (docs commit after SUMMARY update)

## Files Created/Modified

- `tests/conftest.py` - Updated AMR block to use `extract_amr_embeddings_for_accounts`; updated docstring; 395-dim fixture now matches production code
- `trained_system_v11.joblib` - Clean v1.1 trained system artifact (100 MB); produced by `python main.py` retrain run on 2026-04-14

## Decisions Made

**1. AUC 0.97-0.98 is legitimate content-based discrimination, not residual leakage**

After retrain produced AUC 0.97-0.98 (vs expected 70-85% in ROADMAP), user investigated BotSim-24 data characteristics and confirmed:
- Bot accounts post generic templated news summaries
- Human accounts post specific news headlines
- Sentence transformer cleanly separates these by message content alone
- This is legitimate discriminative signal in the dataset, not a symptom of model overfitting or identity leakage

The ROADMAP's 70-85% AUC expectation was overly conservative for this dataset. The leakage fixes (removing USERNAME/PROFILE from embedding pool, switching AMR anchor to most-recent message text, dropping character_setting) are all correctly implemented.

**2. results_v10.json deferred to Phase 7**

The v1.0 metrics capture block was removed in fix commit `5bfb782` because `predict_system()` now uses the 395-dim feature extractor which is incompatible with the v1.0 model weights. Running v1.0 inference with 395-dim features would produce meaningless metrics. v1.0 baseline metrics will be retrieved from git history in Phase 7 by checking out a pre-fix commit.

## Deviations from Plan

### Known Deviations (Pre-documented)

**1. results_v10.json not created**
- **Expected by plan:** `results_v10.json` should exist with keys auc, f1, precision, recall, stage
- **Actual:** File does not exist on disk
- **Reason:** v1.0 metrics capture block removed in commit `5bfb782` (Plan 01 fix commit) — v1.0 model weights are incompatible with the 395-dim feature extractor. Generating metrics with wrong-dimensionality input would be meaningless
- **Resolution:** Phase 7 will retrieve v1.0 metrics from git history (check out pre-fix tag, run evaluation against frozen v1.0 model)
- **Impact:** Phase 7 leakage audit table deferred but not blocked — git history preserves all necessary data

**2. ROADMAP AUC success criterion not met numerically**
- **Criterion from plan:** "Stage 2a AUC on S3 is below 90% after retrain"
- **Actual:** AUC 0.97-0.98 on all partitions (p2, p12, p_final)
- **Finding:** Not residual leakage. User investigation confirmed BotSim-24 dataset has extreme content-based separability. Leakage fixes are correctly implemented and confirmed by code inspection
- **Resolution:** Criterion was overspecified for this specific dataset. The leakage removal is confirmed correct via code review, not just AUC threshold. Documentation updated to capture dataset characteristics

---

**Total deviations:** 2 known (both pre-documented in resume instructions, neither requires code changes)
**Impact on plan:** No code changes needed. Both deviations reflect infrastructure constraints (model incompatibility) and dataset characteristics (high separability), not implementation errors.

## Issues Encountered

None — Task 1 fixture update was straightforward; Task 2 retrain completed without errors.

## User Setup Required

None — retrain completed successfully. No further user action required.

## Next Phase Readiness

**Ready for Phase 6 (Ablation Study):**
- `trained_system_v11.joblib` exists as clean v1.1 baseline artifact (100 MB)
- Full test suite (36 tests) passing on post-leakage-fix codebase
- Feature pipeline confirmed: 395-dim, no identity leakage, behavioral features active
- AMR anchor correctly uses most-recent message text (not profile field)
- `character_setting` confirmed absent from `build_account_table` output

**Deferred to Phase 7:**
- v1.0 baseline metrics (results_v10.json) — will be retrieved from git history at pre-fix commit
- Formal leakage audit table comparing v1.0 vs v1.1 AUC values

## Self-Check

- [x] `trained_system_v11.joblib` exists (100 MB, 2026-04-14 10:05)
- [x] `trained_system.joblib` exists (100 MB, same size — v1.1 also written to original path)
- [x] `tests/conftest.py` updated — `d9ff0ed` in git log
- [x] 36 tests passing (`pytest tests/ -x -q`)
- [x] SUMMARY.md created at `.planning/phases/05-leakage-fix-and-baseline-retrain/05-02-SUMMARY.md`

## Self-Check: PASSED

All artifacts verified. Task commits in git log. 36 tests green.

---
*Phase: 05-leakage-fix-and-baseline-retrain*
*Completed: 2026-04-14*
