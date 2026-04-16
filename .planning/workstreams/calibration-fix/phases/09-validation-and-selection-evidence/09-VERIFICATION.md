# Phase 9 Verification Plan

**Phase:** 09 - Validation and Selection Evidence  
**Status:** Planned  
**Last updated:** 2026-04-16

## What execution must prove

1. The real S2 calibration path can produce inspectable evidence for why the selected threshold set won.
2. The evidence compares the selected trial against credible alternatives using both:
   - score-facing signals such as primary score and smooth secondary metrics
   - behavior-facing signals such as routing usage, positive prediction patterns, or equivalent real outputs
3. Trial count is no longer effectively redundant on the real path because calibration either:
   - differentiates meaningful candidates, or
   - stops early for a documented plateau reason
4. The milestone record clearly states whether the final shipped fix is:
   - early stopping
   - revised selection logic
   - a hybrid approach

## Required execution checks

1. `python -m pytest tests/test_calibrate.py -x -q`
2. `python main.py`
3. Inspect the emitted Phase 9 artifact and confirm it includes:
   - selected trial
   - selected thresholds
   - primary and secondary scores
   - tie count
   - near-best alternatives
   - behavior-facing comparison fields
   - early-stop status and stop reason, if present

## Pass conditions

- `CALFIX-05`: Passes only if the selected trial can be distinguished from alternatives by meaningful score and behavior evidence.
- `CALFIX-06`: Passes only if tests and the real-run artifact show trial count is not redundant in practice for this calibration path.
- `CALFIX-07`: Passes only if Phase 9 docs explicitly record the final calibration strategy and justify why it shipped.

## Failure conditions

- The real run emits no artifact or only synthetic-style evidence.
- The artifact cannot explain why the winner beat nearby alternatives.
- The real path still looks like first-trial-wins behavior disguised by better logging.
- Requirements are checked off without direct supporting evidence.
