---
phase: 16-comparative-paper-outputs-and-reddit-cleanup
verified: 2026-04-18T16:45:00Z
status: passed
score: 8/8
overrides_applied: 0
---

# Phase 16: Comparative Paper Outputs and Reddit Cleanup - Verification Report

**Phase Goal:** v1.4 records the platform-matched TwiBot baseline, compares it against the Reddit transfer baseline, and removes the unsupported recalibration path from the maintained Reddit evaluation flow.
**Verified:** 2026-04-18
**Status:** PASSED
**Re-verification:** No - initial verification

---

## Goal Achievement

### Observable Truths

| # | Truth | Status | Evidence |
|---|-------|--------|----------|
| 1 | Table 5 now compares Reddit transfer against the TwiBot-native baseline instead of static-vs-recalibrated Reddit variants | VERIFIED | `ablation_tables.py` now defines a Phase 16 comparison contract and `generate_cross_dataset_table()` emits columns for `TwiBot-20 (Reddit transfer)` and `TwiBot-20 (TwiBot-native)`. |
| 2 | The maintained comparison contract has an explicit stable schema | VERIFIED | `build_reddit_vs_native_comparison_artifact()` writes `comparison_type == "reddit_transfer_vs_twibot_native"` with `reddit_transfer` and `twibot_native` condition keys plus `delta_overall`. |
| 3 | The maintained Reddit-transfer evaluation contract writes only the post-cleanup baseline artifacts | VERIFIED | `evaluate_twibot20.py` defaults now route to `results_twibot20_reddit_transfer.json` and `metrics_twibot20_reddit_transfer.json`, and `list_expected_output_files()` returns only those two files. |
| 4 | Online novelty recalibration is no longer part of the maintained Reddit-transfer path | VERIFIED | `evaluate_twibot20.py` defaults `online_calibration=False` and the release-facing contract no longer writes or documents recalibration comparison outputs as the active path. |
| 5 | Historical Phase 12 evidence remains preserved without being the default v1.4 story | VERIFIED | `PHASE12_EVIDENCE_DIR`, `build_transfer_evidence_summary()`, and `compare_twibot20_conditions()` remain available for archived evidence, while the maintained Phase 16 defaults point to the new artifact names and directory. |
| 6 | Release docs now explain the separate Reddit-trained and TwiBot-trained artifacts and how to reproduce the comparison | VERIFIED | `README.md` documents the Reddit transfer command, the native TwiBot command, and the `ablation_tables.py` comparison step. `VERSION.md` names the active artifacts and comparison outputs. |
| 7 | The TwiBot-native evaluation path remains separate from the Reddit-transfer cleanup | VERIFIED | Phase 16 changed `evaluate_twibot20.py`, `ablation_tables.py`, `README.md`, and `VERSION.md`; the native evaluation entry point remains `evaluate_twibot20_native.py`. |
| 8 | The delivered Phase 16 code is syntactically valid and passes direct smoke validation | VERIFIED | `python -m py_compile evaluate_twibot20.py ablation_tables.py tests/test_evaluate_twibot20.py tests/test_ablation_tables.py` passed, and direct Python smoke checks confirmed the new artifact schema, delta calculation, and default filenames. |

**Score:** 8/8 truths verified

---

## Required Artifacts

| Artifact | Expected | Status | Details |
|----------|----------|--------|---------|
| `ablation_tables.py` | Phase 16 comparison contract, Table 5 rewrite, interpretation update | VERIFIED | Contains stable Reddit-transfer-vs-native comparison helpers and default Phase 16 comparison artifact wiring. |
| `tests/test_ablation_tables.py` | Focused tests for comparison schema and new Table 5 semantics | VERIFIED | Updated to assert new labels, comparison keys, and interpretation behavior. |
| `evaluate_twibot20.py` | Maintained Reddit-transfer baseline contract after recalibration retirement | VERIFIED | Default filenames and output contract now reflect the Phase 16 baseline-only path. |
| `tests/test_evaluate_twibot20.py` | Focused tests for the retired feature boundary and surviving baseline contract | VERIFIED | Updated to assert the active artifact names and archived-helper boundaries. |
| `README.md` | Reproduction guide for Reddit baseline, native TwiBot baseline, and comparison outputs | VERIFIED | Commands and env vars match the maintained v1.4 story. |
| `VERSION.md` | Concise release contract naming active and historical artifacts | VERIFIED | Documents the two separate model artifacts and the maintained comparison output set. |

---

## Behavioral Spot-Checks

| Behavior | Command | Result | Status |
|----------|---------|--------|--------|
| Phase 16 modules compile | `python -m py_compile evaluate_twibot20.py ablation_tables.py tests/test_evaluate_twibot20.py tests/test_ablation_tables.py` | Completed without syntax errors | PASS |
| Phase 16 comparison schema builds | direct Python smoke check for `build_reddit_vs_native_comparison_artifact()` | Returned `reddit_transfer_vs_twibot_native` with correct `delta_overall["f1"]` | PASS |
| Table 5 columns reflect new story | direct Python smoke check for `generate_cross_dataset_table()` | Emitted columns including `TwiBot-20 (Reddit transfer)` and `TwiBot-20 (TwiBot-native)` | PASS |
| Reddit-transfer default outputs are stable | direct Python smoke check for `list_expected_output_files()` | Returned only `results_twibot20_reddit_transfer.json` and `metrics_twibot20_reddit_transfer.json` | PASS |
| Targeted pytest | `python -m pytest tests/test_evaluate_twibot20.py tests/test_ablation_tables.py -q` | Blocked by Windows temp-dir permission failures during tmp-path setup/cleanup | ENVIRONMENT BLOCKED |

---

## Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
|-------------|------------|-------------|--------|----------|
| CMP-01 | 16-01-PLAN.md | Paper-facing comparison output contrasts Reddit-trained-on-TwiBot versus TwiBot-trained-on-TwiBot | SATISFIED | `ablation_tables.py` and `tests/test_ablation_tables.py` now use the Phase 16 comparison schema and new Table 5 labels. |
| CMP-02 | 16-02-PLAN.md | Online novelty recalibration is removed from the maintained Reddit system path | SATISFIED | `evaluate_twibot20.py` defaults now lock the maintained path to the Reddit transfer baseline artifacts, and release docs no longer present recalibration as an active feature. |
| CMP-03 | 16-03-PLAN.md | Docs explain separate artifacts, reproduction flow, and caveats | SATISFIED | `README.md` and `VERSION.md` document the Reddit baseline path, native TwiBot path, comparison outputs, and historical-vs-maintained distinction. |

---

## Gaps Summary

No product-code gaps remain for Phase 16. The only incomplete verification step is targeted pytest in this Windows workspace, where temp-directory setup and cleanup continue to fail with permission errors unrelated to the Phase 16 logic.

---

_Verified: 2026-04-18T16:45:00Z_
_Verifier: Codex_
