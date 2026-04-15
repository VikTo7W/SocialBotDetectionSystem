---
phase: 06-ablation-infrastructure-and-differentiator-features
plan: 01
subsystem: testing, features
tags: [numpy, cosine-similarity, tdd, feature-engineering, sentence-transformers]

# Dependency graph
requires:
  - phase: 05-leakage-fix-and-feature-expansion
    provides: "features_stage2.py producing 395-dim output with FEAT-01/02/03 at indices 391-394"
provides:
  - "FEAT-04: cross_msg_sim_mean at index 395, near_dup_frac at index 396"
  - "features_stage2.py producing 397-dim feature vectors"
  - "NormalizedFakeEmbedder helper for cosine similarity value tests"
  - "Full test coverage for all FEAT-01 through FEAT-04 features"
affects:
  - "06-02-PLAN.md: retrain pipeline must handle 397-dim input; fixture update required"

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "TDD RED/GREEN: write failing tests first, implement to pass"
    - "NormalizedFakeEmbedder pattern: L2-normalize fake embeddings so emb @ emb.T yields valid cosine similarities"
    - "Off-diagonal mask via ~np.eye(n, dtype=bool) for pairwise similarity computation"

key-files:
  created: []
  modified:
    - "features_stage2.py"
    - "tests/test_features_stage2.py"
    - "tests/conftest.py"

key-decisions:
  - "NormalizedFakeEmbedder defined locally in test file (conftest.py is not directly importable as a module — pytest injects it)"
  - "FEAT-04 defaults to 0.0 for accounts with 0 or 1 messages (no pairwise comparison possible)"
  - "near_dup_frac threshold set at _NEAR_DUP_SIM_THRESHOLD = 0.9 module-level constant"

patterns-established:
  - "NormalizedFakeEmbedder: use L2-normalized fake embeddings when testing cosine similarity values"
  - "Off-diagonal mask: ~np.eye(n, dtype=bool) pattern for pairwise feature computation"

requirements-completed: [FEAT-04]

# Metrics
duration: 3min
completed: 2026-04-15
---

# Phase 6 Plan 01: FEAT-04 Cross-Message Cosine Similarity Summary

**Two cross-message similarity features (cross_msg_sim_mean, near_dup_frac) appended at indices 395-396, growing feature vector from 395 to 397 dims via TDD.**

## Performance

- **Duration:** 3 min
- **Started:** 2026-04-15T00:45:39Z
- **Completed:** 2026-04-15T00:48:00Z
- **Tasks:** 2 (TDD RED + GREEN)
- **Files modified:** 3

## Accomplishments

- Added `NormalizedFakeEmbedder` to `conftest.py` and locally in test file for cosine similarity value tests
- Updated `test_feat01_default_zero` shape assertion from `(1, 395)` to `(1, 397)` — RED phase
- Added 3 failing FEAT-04 tests: `test_feat04_default_zero`, `test_feat04_sim_mean`, `test_feat04_near_dup` — RED phase
- Implemented FEAT-04 in `features_stage2.py`: off-diagonal cosine similarity mean and near-duplicate fraction — GREEN phase
- Full test suite (39 tests) passes with no regressions

## Task Commits

Each task was committed atomically:

1. **Task 1: Wave 0 — Create FEAT-04 test stubs, update shape assertions, add NormalizedFakeEmbedder** - `7386e02` (test)
2. **Task 2: Implement FEAT-04 — cross-message cosine similarity features** - `ba09621` (feat)

_Note: TDD tasks have two commits (test RED then feat GREEN)_

## Files Created/Modified

- `features_stage2.py` — Added `_NEAR_DUP_SIM_THRESHOLD = 0.9` constant; FEAT-04 computation block using off-diagonal cosine similarity; updated concatenation to append `[cross_msg_sim_mean, near_dup_frac]`; vector is now 397-dim
- `tests/test_features_stage2.py` — Updated shape assertion `(1,395)→(1,397)`; added `NormalizedFakeEmbedder` class; added `test_feat04_default_zero`, `test_feat04_sim_mean`, `test_feat04_near_dup`
- `tests/conftest.py` — Added `NormalizedFakeEmbedder` class (also available for other test files via pytest injection)

## Decisions Made

- `NormalizedFakeEmbedder` defined locally in test file: `conftest.py` cannot be directly imported as a Python module (pytest auto-injects fixtures but `from conftest import X` fails at collection time). Defined the class both in `conftest.py` (for fixture injection) and locally in the test module (for direct use in test bodies).
- FEAT-04 defaults to `0.0` for 0 and 1-message accounts: no pairwise comparison is possible without at least 2 embeddings.
- Near-duplicate threshold `0.9` extracted as module-level constant `_NEAR_DUP_SIM_THRESHOLD` for maintainability.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Fixed conftest import error**
- **Found during:** Task 1 (RED phase collection)
- **Issue:** Plan specified `from conftest import NormalizedFakeEmbedder` but `conftest.py` is not a regular importable module — pytest injects it automatically, but direct imports fail with `ModuleNotFoundError`
- **Fix:** Defined `NormalizedFakeEmbedder` locally within `tests/test_features_stage2.py` (kept it in `conftest.py` too for future fixture use)
- **Files modified:** `tests/test_features_stage2.py`
- **Verification:** `pytest --co -q` collects all 12 tests without error
- **Committed in:** `7386e02` (Task 1 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking import error)
**Impact on plan:** Single minor fix to conftest import pattern. No scope creep, behavior matches plan spec exactly.

## Issues Encountered

- `conftest.py` module import pattern: pytest conftest files are auto-injected, not directly importable. Resolved by defining `NormalizedFakeEmbedder` locally in the test file.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `features_stage2.py` produces 397-dim vectors — 06-02-PLAN.md (retrain to v12) can proceed
- Fixture update required in 06-02: `conftest.py minimal_system` fixture trains Stage2BaseContentModel on 397-dim input; no code changes needed since `FakeEmbedder` will now automatically produce 397-dim output through the updated extractor
- All tests green — no blockers for retrain phase

---
*Phase: 06-ablation-infrastructure-and-differentiator-features*
*Completed: 2026-04-15*
