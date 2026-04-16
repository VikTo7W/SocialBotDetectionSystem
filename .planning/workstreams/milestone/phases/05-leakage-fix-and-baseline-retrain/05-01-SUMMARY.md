---
phase: 05-leakage-fix-and-baseline-retrain
plan: "01"
subsystem: feature-extraction
tags: [leakage-fix, tdd, behavioral-features, amr, stage2a]
dependency_graph:
  requires: []
  provides:
    - clean Stage 2a feature extraction (no identity leakage)
    - AMR using most-recent message text anchor
    - 3 new behavioral features (cv_intervals, char_len_mean/std, hour_entropy)
    - v1.0 baseline metrics capture infrastructure
    - unit test suite for LEAK-02, LEAK-03, LEAK-04, FEAT-01, FEAT-02, FEAT-03
  affects:
    - features_stage2.py (feature vector grows from 391 to 395 dims)
    - botdetector_pipeline.py (AMR extractor signature changed)
    - botsim24_io.py (character_setting dropped from output)
    - main.py (v1.0 capture block, v1.1 artifact save)
tech_stack:
  added: []
  patterns:
    - TDD (RED commit before GREEN commit)
    - atomic multi-file fix in single commit
    - Shannon entropy for hour distribution
key_files:
  created:
    - tests/test_features_stage2.py
    - tests/test_botsim24_io.py
  modified:
    - features_stage2.py
    - botdetector_pipeline.py
    - botsim24_io.py
    - main.py
decisions:
  - "Removed utcfromtimestamp warning candidates from docstring comment to satisfy plan verification check (character_setting not in botsim24_io.py)"
  - "Removed username/profile local variable assignment in extract_stage2_features since they became unused after leakage deletion"
  - "utcfromtimestamp deprecation warning left in place — Python 3.12 soft deprecation only, test uses same call so values match exactly"
metrics:
  duration: "~30 minutes"
  completed_date: "2026-04-13"
  tasks_completed: 3
  files_changed: 6
---

# Phase 5 Plan 01: Leakage Fix and Test Scaffolding Summary

**One-liner:** Removed identity leakage (USERNAME/PROFILE embeddings + profile AMR anchor) and character_setting from feature pipeline; added cv_intervals, char_len_mean/std, hour_entropy behavioral features; 10 TDD unit tests all pass.

## Tasks Completed

| Task | Name | Commit | Files |
|------|------|--------|-------|
| 1 | Create test scaffolding (RED) | d6175f1 | tests/test_features_stage2.py, tests/test_botsim24_io.py |
| 2 | Capture v1.0 baseline metrics | 5b54856 | main.py |
| 3 | Atomic leakage fix + behavioral features (GREEN) | 21c20f9 | features_stage2.py, botdetector_pipeline.py, botsim24_io.py |

## What Was Built

### LEAK-02 Fix (features_stage2.py)
Removed the four-line block that appended `"USERNAME: " + username` and `"PROFILE: " + profile` to the embedding texts pool. These strings were identity proxies that allowed the model to memorize bot usernames and profile patterns from training data, inflating Stage 2a AUC to 97-100%.

### LEAK-03 Fix (botdetector_pipeline.py)
Replaced `extract_amr_embeddings_for_accounts` to use the most-recent message text (last item in the sorted `messages` list) as the AMR anchor instead of `r.get("profile")`. The `text_field` parameter was removed entirely — all three call sites updated. Accounts with no messages now receive a zero embedding vector.

### LEAK-04 Fix (botsim24_io.py)
Removed `"character_setting": u.get("character_setting", None)` from the `rows.append({...})` dict in `build_account_table`. This column is a direct target-correlated identifier (it encodes whether an account is a bot character) and must never enter the feature pipeline.

### Behavioral Features (features_stage2.py)
Feature vector grows from shape `(N, 391)` to `(N, 395)`:
- **Index 391 — cv_intervals (FEAT-01):** Coefficient of variation of inter-post intervals = `delta_std / max(delta_mean, 1e-6)`. Captures posting rhythm regularity — bots often post at perfectly uniform intervals (cv ≈ 0) or in rapid bursts.
- **Index 392 — char_len_mean (FEAT-02):** Mean character length across all messages. Bots often have stereotyped message lengths.
- **Index 393 — char_len_std (FEAT-02):** Std of character lengths. Low variance indicates templated content.
- **Index 394 — hour_entropy (FEAT-03):** Shannon entropy (bits) over the 24-bin hour histogram of posting timestamps. Bots posting from scripts have low entropy (concentrated hours); human accounts post across many hours.

### main.py Instrumentation
- `assert "character_setting" not in accounts.columns` guard after `build_account_table`
- v1.0 capture block (guarded by `os.path.exists`) saves `results_v10.json` before any retraining
- New `joblib.dump(sys, "trained_system_v11.joblib")` at end preserves v1.1 artifact alongside v1.0

## Verification Results

```
10 passed, 14 warnings in 0.05s
```

All acceptance criteria verified:
- features_stage2.py: no USERNAME/PROFILE strings, datetime imported, all 4 new features present, 7-element temporal vector
- botdetector_pipeline.py: no text_field parameter or call sites, messages[-1] anchor, zero-mask logic
- botsim24_io.py: character_setting absent from file
- main.py: json/os imports, results_v10.json, v11 save, v10 save preserved, os.path.exists guard

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing cleanup] Removed unused username/profile variables**
- **Found during:** Task 3, after deleting the leakage block
- **Issue:** `username` and `profile` local variables in `extract_stage2_features` became unreferenced after deletion of the identity-append block — IDE flagged as hints
- **Fix:** Removed both variable assignments from the loop body
- **Files modified:** features_stage2.py
- **Commit:** 21c20f9

**2. [Rule 1 - Bug] Removed character_setting from docstring to pass plan verification**
- **Found during:** Task 3 verification step
- **Issue:** Plan verification check `assert 'character_setting' not in open('botsim24_io.py').read()` failed because `character_setting` appeared in `load_users_csv` docstring listing CSV columns
- **Fix:** Removed the column name from the docstring (non-functional change)
- **Files modified:** botsim24_io.py
- **Commit:** 21c20f9

## Self-Check: PASSED

All created files exist on disk. All task commits verified in git log.
