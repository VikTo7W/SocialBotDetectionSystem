# Requirements: Calibration Fix Workstream

**Defined:** 2026-04-16
**Milestone:** v1.1.1 Threshold Calibration Search Fix
**Core Value:** Calibration should produce a meaningful threshold policy, not spend repeated trials rediscovering an identical plateau.

## Calibration Diagnosis

- [x] **CALFIX-01**: Developer can identify and explain why threshold calibration trials repeatedly return the same `F1=0.993333`
- [x] **CALFIX-02**: Calibration logs or artifacts make it clear whether objective flatness comes from metric quantization, routing invariance, or another implementation issue

## Calibration Strategy

- [x] **CALFIX-03**: `calibrate_thresholds()` uses a strategy that avoids wasting trials on a flat objective plateau
- [x] **CALFIX-04**: The chosen strategy preserves reproducibility and has deterministic behavior under a fixed seed
- [ ] **CALFIX-05**: The calibrated selection rule can distinguish between candidate threshold sets when they have materially different routing or probability behavior

## Validation

- [ ] **CALFIX-06**: Tests or reproducible checks demonstrate that trial count is no longer effectively redundant for this calibration path
- [ ] **CALFIX-07**: The milestone records whether the fix uses early stopping, a revised objective, or both, and why that choice was made

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full retraining-stack redesign | This milestone is limited to calibration behavior |
| TwiBot-20 transfer evaluation | Covered by the separate `twibot-intergration` workstream |
| AMR implementation changes | Unrelated to the threshold-search plateau |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| CALFIX-01 | Phase 8 | Complete |
| CALFIX-02 | Phase 8 | Complete |
| CALFIX-03 | Phase 8 | Complete |
| CALFIX-04 | Phase 8 | Complete |
| CALFIX-05 | Phase 9 | Planned |
| CALFIX-06 | Phase 9 | Planned |
| CALFIX-07 | Phase 9 | Planned |
