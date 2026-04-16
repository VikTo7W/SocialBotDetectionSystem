# Roadmap: Calibration Fix Workstream

## Milestone

- [ ] **v1.1.1 Threshold Calibration Search Fix** - Phases 8-9

## Phases

### Phase 8: Calibration Signal Recovery

**Goal:** Diagnose why Optuna sees an effectively constant objective and implement a calibration strategy that restores useful search behavior.

**Requirements:** CALFIX-01, CALFIX-02, CALFIX-03, CALFIX-04

**Success criteria:**
1. We can point to the concrete reason trials collapse to the same score.
2. `calibrate_thresholds()` no longer blindly spends all configured trials on an undifferentiated plateau.
3. The updated search policy remains reproducible with the existing seed conventions.

### Phase 9: Validation and Selection Evidence

**Goal:** Prove the new calibration behavior is meaningful, not just different, and record the selection policy clearly.

**Requirements:** CALFIX-05, CALFIX-06, CALFIX-07

**Success criteria:**
1. Validation shows the calibration path can now differentiate meaningful candidates or stop early for a documented reason.
2. Tests or scripted checks cover the regression that made trial count redundant.
3. The workstream artifacts record whether the final fix is early stopping, objective redesign, or a hybrid approach.

## Progress

| Phase | Goal | Requirements | Status |
|-------|------|--------------|--------|
| 8 | Calibration Signal Recovery | CALFIX-01, CALFIX-02, CALFIX-03, CALFIX-04 | Ready |
| 9 | Validation and Selection Evidence | CALFIX-05, CALFIX-06, CALFIX-07 | Pending |
