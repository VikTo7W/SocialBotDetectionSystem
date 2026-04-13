---
phase: 05-leakage-fix-and-baseline-retrain
plan: 02
subsystem: testing
tags: [conftest, fixtures, feature-vectors, amr, retrain, leakage-fix]

# Dependency graph
requires:
  - phase: 05-01
    provides: "Post-leakage-fix codebase with 395-dim feature vectors and new AMR signature"
provides:
  - "Updated conftest.py fixture matching 395-dim feature vectors and new AMR signature"
  - "Full test suite passing (36 tests) against post-Plan-01 code"
  - "trained_system_v11.joblib — clean v1.1 baseline trained system (awaiting user run)"
  - "results_v10.json — v1.0 S3 metrics for leakage audit table (awaiting user run)"
affects: [phase-06, phase-07, ablation-tables]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "conftest.py uses extract_amr_embeddings_for_accounts directly instead of raw profile text encoding"
    - "AMR refiner in fixtures trained on most-recent message text embeddings matching production code"

key-files:
  created: []
  modified:
    - "tests/conftest.py"

key-decisions:
  - "conftest.py minimal_system fixture uses extract_amr_embeddings_for_accounts(S2, FeatureConfig(...), embedder) — no more raw profile text encoding"

patterns-established:
  - "Fixtures call real production functions directly to stay in sync with implementation changes"

requirements-completed:
  - LEAK-01
  - LEAK-05

# Metrics
duration: 5min
completed: 2026-04-13
---

# Phase 05 Plan 02: Fixture Update and Baseline Retrain Summary

**conftest.py minimal_system fixture updated to use extract_amr_embeddings_for_accounts (message-based AMR) and 395-dim feature vectors; awaiting user confirmation of full cascade retrain**

## Performance

- **Duration:** ~5 min (Task 1 automated; Task 2 is human-verify checkpoint)
- **Started:** 2026-04-13T21:00:00Z
- **Completed:** 2026-04-13 (Task 1); Task 2 awaiting user verification
- **Tasks:** 1 automated + 1 human-verify checkpoint
- **Files modified:** 1

## Accomplishments
- Updated conftest.py docstring from "Phase 2 threshold calibration tests" to "bot detection system tests"
- Replaced raw `profile_texts` AMR block with `extract_amr_embeddings_for_accounts` call (matches production code)
- All 36 tests pass with the updated fixture and 395-dim feature vectors

## Task Commits

1. **Task 1: Update conftest.py fixture for 395-dim feature vectors and new AMR signature** - `d9ff0ed` (feat)
2. **Task 2: Run full cascade retrain and validate leakage removal** — human-verify checkpoint (user runs `python main.py`)

**Plan metadata:** (to be added after Task 2 confirmation)

## Files Created/Modified
- `tests/conftest.py` - Updated AMR block to use `extract_amr_embeddings_for_accounts`; updated docstring

## Decisions Made
None — followed plan as specified.

## Deviations from Plan
None — plan executed exactly as written.

## Issues Encountered
None.

## User Setup Required

**Task 2 requires the user to run `python main.py`** to execute the full cascade retrain.

Expected outputs to verify:
- Console: `[main] v1.0 metrics saved to results_v10.json` (first run only)
- Console: `[main] Saved v1.1 TrainedSystem to trained_system_v11.joblib`
- No assertion errors for `character_setting`
- Stage 2a AUC in evaluation output is below 90% (expected 70-85% range)
- `results_v10.json` exists with keys: `auc`, `f1`, `precision`, `recall`, `stage`
- `trained_system_v11.joblib` exists on disk

After confirming all the above, run the automated verification:
```bash
cd C:/Users/dzeni/PycharmProjects/SocialBotDetectionSystem && python -c "
import os, json
assert os.path.exists('results_v10.json'), 'results_v10.json not found'
d = json.load(open('results_v10.json'))
assert all(k in d for k in ['auc','f1','precision','recall','stage']), f'missing keys: {d.keys()}'
print('results_v10.json OK:', d)
if os.path.exists('trained_system_v11.joblib'):
    print('trained_system_v11.joblib exists')
else:
    print('WARNING: trained_system_v11.joblib not yet created (run main.py)')
"
```

## Next Phase Readiness
- Once `python main.py` completes successfully and Stage 2a AUC is confirmed below 90%, Phase 5 leakage fix is complete
- `trained_system_v11.joblib` will be the foundation for ablation work in Phases 6-7
- `results_v10.json` will supply v1.0 baseline metrics for the leakage audit comparison table

---
*Phase: 05-leakage-fix-and-baseline-retrain*
*Completed: 2026-04-13*
