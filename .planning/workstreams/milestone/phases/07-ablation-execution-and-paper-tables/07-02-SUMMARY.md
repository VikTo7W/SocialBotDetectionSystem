---
phase: 07-ablation-execution-and-paper-tables
plan: "02"
subsystem: evaluation
tags: [ablation, latex, pandas, joblib, monkey-patch, feature-masking]

# Dependency graph
requires:
  - phase: 07-01
    provides: test_ablation_tables.py stub tests (6 tests, RED state)
  - phase: 06-02
    provides: trained_system_v12.joblib with 397-dim feature extractor
provides:
  - ablation_tables.py with build_table1/2/3/4, save_latex, masked_predict, main()
  - All 4 LaTeX table builders verified by unit tests (pending full run)
affects:
  - paper writing (consumes .tex files from tables/)
  - Phase 07 Task 2 continuation (user runs worktree retrain + full script)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Monkey-patch module-level name binding: import botdetector_pipeline as bp; bp.extract_stage1_matrix = ... — patches the bound name, not the source module"
    - "Feature masking via column-zero: copy X, set X[:, mask_cols] = 0.0 at inference time"
    - "S3 split reconstruction: identical SEED=42 train_test_split(test_size=0.15, stratify) from main.py"

key-files:
  created:
    - ablation_tables.py
  modified: []

key-decisions:
  - "Monkey-patch targets botdetector_pipeline.extract_stage1_matrix (not features_stage1) because from-import creates a local binding in bp module scope"
  - "Table 2 uses only p1/p12/p_final rows — p2 excluded as it is not a coherent cascade stage comparison"
  - "save_latex uses float_format='%.4f' so test assertion '0.9000' string matches formatted output"
  - "masked_predict copies X before zeroing columns to avoid mutating the original array"

patterns-established:
  - "Pattern 1: Monkey-patch module attribute (not source module) for inference-time feature ablation"
  - "Pattern 2: S3 split reconstructed from raw data using SEED=42 to guarantee same split as training"

requirements-completed: [ABL-02, ABL-04, ABL-05, ABL-06]

# Metrics
duration: 5min
completed: 2026-04-15
---

# Phase 7 Plan 02: Ablation Tables Implementation Summary

**ablation_tables.py implemented with 4 table builders, monkey-patch masking helper, and LaTeX export — all 6 unit tests pass; pending user worktree retrain and full script run**

## Performance

- **Duration:** ~5 min
- **Started:** 2026-04-15T22:55:00Z
- **Completed:** 2026-04-15T22:56:16Z
- **Tasks:** 1 of 2 (Task 2 blocked at checkpoint — requires user action)
- **Files modified:** 1

## Accomplishments

- ablation_tables.py created with all 7 required functions (build_table1-4, save_latex, masked_predict, main)
- All 6 unit tests pass against synthetic fixtures without any trained model on disk
- Monkey-patch pattern correctly targets `botdetector_pipeline.extract_stage1_matrix` (the bound name in bp's module scope) — patching `features_stage1` directly would be silently ignored
- main() reconstructs S3 split identically to main.py (SEED=42, stratified 15% split)

## Task Commits

1. **Task 1: Implement ablation_tables.py with all table functions** - `ece8647` (feat)

## Files Created/Modified

- `ablation_tables.py` — All 4 table builders, save_latex, masked_predict helper, main() entry point

## Decisions Made

- Monkey-patch targets `botdetector_pipeline.extract_stage1_matrix` not `features_stage1.extract_stage1_matrix` — `from features_stage1 import extract_stage1_matrix` on line 14 of botdetector_pipeline.py creates a local name binding; only patching `bp.extract_stage1_matrix` affects predict_system calls
- Table 2 excludes p2 row — Stage 2 alone on all accounts is not a meaningful cascade stage comparison (decision carried over from Phase 07-01 research)
- masked_predict copies X before zeroing to avoid mutating the array returned by `_orig_extract_stage1_matrix`

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

Task 2 is a blocking checkpoint requiring two manual steps:

**Step A — Produce results_v10.json via git worktree retrain:**

```bash
# Create worktree at the last v1.0 commit
git worktree add ../botdetect-v10 4997bc3

# Patch main.py in the worktree to dump metrics JSON after evaluate_s3
cd ../botdetect-v10
python -c "
code = open('main.py').read()
patch = '''
import json
with open('results_v10.json', 'w') as f:
    json.dump({
        'auc': report['overall']['auc'],
        'f1': report['overall']['f1'],
        'precision': report['overall']['precision'],
        'recall': report['overall']['recall'],
        'stage': 'S3',
    }, f, indent=2)
print('results_v10.json written')
'''
code = code.rstrip() + '\n' + patch
open('main.py', 'w').write(code)
print('main.py patched')
"

# Run v1.0 training + evaluation (takes several minutes)
python main.py

# Copy results back and clean up
cp results_v10.json ../SocialBotDetectionSystem/
cd ../SocialBotDetectionSystem
git worktree remove ../botdetect-v10
```

**Step B — Run ablation_tables.py to generate all 4 LaTeX tables:**

```bash
python ablation_tables.py
```

**Verification after Step B:**
1. `results_v10.json` exists with keys: auc, f1, precision, recall
2. `tables/table1_leakage_audit.tex` through `tables/table4_feature_group_ablation.tex` exist
3. Each .tex file contains `\begin{tabular}` and numeric values with 4 decimal places
4. Table 4 metrics vary across feature groups (confirms monkey-patch worked)
5. `pytest tests/ -x -q` — full suite green

## Next Phase Readiness

- ablation_tables.py is complete and unit-tested — ready for full execution once results_v10.json is on disk
- After Task 2 checkpoint: continuation agent will commit results_v10.json + all 4 .tex files
- Phase 07 will be complete once all 4 LaTeX tables are on disk with valid content

---
*Phase: 07-ablation-execution-and-paper-tables*
*Completed: 2026-04-15 (partial — Task 2 at checkpoint)*
