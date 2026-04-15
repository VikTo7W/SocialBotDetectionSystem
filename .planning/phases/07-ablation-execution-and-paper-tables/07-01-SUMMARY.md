---
phase: 07-ablation-execution-and-paper-tables
plan: "01"
subsystem: testing
tags: [pytest, ablation, pandas, latex, tdd, wave-0]

requires:
  - phase: 06-ablation-infrastructure-and-differentiator-features
    provides: trained_system_v12.joblib with 397-dim feature extractor

provides:
  - Wave 0 TDD stubs for all ablation table functions (build_table1..4, save_latex)
  - Contract definition for ablation_tables.py implementation in Plan 02

affects:
  - 07-02 (implements ablation_tables.py against these stubs)

tech-stack:
  added: []
  patterns:
    - "Wave 0 TDD: import-level test stubs establish API contract before implementation"
    - "Module-level MOCK_* dicts mirror exact evaluate_s3() return structure for fast, hermetic tests"

key-files:
  created:
    - tests/test_ablation_tables.py
  modified: []

key-decisions:
  - "Table 2 uses 3 rows (p1/p12/p_final) not 4 — p2 excluded per plan spec (Stage 2 alone on all accounts is not a cascade stage)"
  - "First row of Table 4 is 'all_features' baseline; remaining 5 rows are masked groups"
  - "save_latex contract requires float_format='%.4f' — verified via '0.9000' string in output"

patterns-established:
  - "Pattern: MOCK_* dicts at module level — no pytest fixtures needed for pure data contracts"
  - "Pattern: ImportError at collection time is expected Wave 0 RED state — AST parse confirms syntactic correctness"

requirements-completed:
  - ABL-02
  - ABL-04
  - ABL-05
  - ABL-06

duration: 1min
completed: "2026-04-15"
---

# Phase 07 Plan 01: Ablation Table Test Stubs Summary

**6 pytest stubs establishing the DataFrame-shape and column-name contract for build_table1/2/3/4 and save_latex against synthetic evaluate_s3() mock data**

## Performance

- **Duration:** ~1 min
- **Started:** 2026-04-15T22:51:56Z
- **Completed:** 2026-04-15T22:53:17Z
- **Tasks:** 1
- **Files modified:** 1

## Accomplishments

- Created `tests/test_ablation_tables.py` with 6 test functions covering all ablation table public API
- Synthetic MOCK_* dicts exactly mirror the keys returned by `evaluate_s3()` (overall/per_stage/routing structure)
- AST parses cleanly; existing 39 tests still pass; ImportError on collection is expected RED state
- Table contracts fully specified: shapes, column names, row labels, value assertions, and LaTeX format validation

## Task Commits

1. **Task 1: Create test stubs for ablation table functions** - `d45017b` (test)

**Plan metadata:** (added in final commit below)

## Files Created/Modified

- `tests/test_ablation_tables.py` - 6 test stubs for build_table1, build_table2, build_table3, build_table4, save_latex with MOCK_* fixtures mirroring evaluate_s3() output structure

## Decisions Made

- Table 2 spec uses exactly 3 rows (p1/p12/p_final) — p2 is available in per_stage dict but plan specifies it is excluded from the stage-contribution table
- Table 4 first row must be "all_features" (baseline); 5 masked groups follow
- save_latex contract enforces float_format="%.4f" — test asserts "0.9000" appears in file content

## Deviations from Plan

None - plan executed exactly as written.

Note: The plan states "6 test items appear in the collection output" as verification. In practice, pytest shows ImportError at collection time when the module-level import fails, so test names are not listed individually — this is correct Wave 0 behavior. The plan's acceptance criteria (AST parse OK + 6 test functions present) are fully met.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- `tests/test_ablation_tables.py` provides the complete implementation contract for Plan 02
- Plan 02 creates `ablation_tables.py` with build_table1..4 and save_latex — these tests will turn GREEN
- `results_v10.json` still missing (deferred from Phase 5) — Plan 02 must handle v1.0 metrics recovery via git worktree before Table 1 can produce real values

---
*Phase: 07-ablation-execution-and-paper-tables*
*Completed: 2026-04-15*
