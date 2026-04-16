---
workstream: stage2b-lstm-version
milestone: v1.2.1
milestone_name: Stage 2b LSTM Variant
created: "2026-04-16"
phase_range: "8-10"
---

# Roadmap: v1.2.1 Stage 2b LSTM Variant

**Goal:** Build an LSTM-powered Stage 2b path that can train and run inside the current cascade, then compare it against the existing AMR delta-refiner baseline.

**Granularity:** standard
**Coverage:** 8/8 requirements mapped

## Phases

- [x] **Phase 8: LSTM Stage 2b Foundation** - Define the Stage 2b LSTM data/model contract and get deterministic training behavior working
- [x] **Phase 9: Cascade Integration and Variant Selection** - Integrate the LSTM Stage 2b path into the cascade without breaking the AMR baseline
- [ ] **Phase 10: Evaluation and Baseline Comparison** - Compare the LSTM variant against the AMR delta-refiner path and record the outcome

## Phase Details

### Phase 8: LSTM Stage 2b Foundation
**Goal**: An LSTM-based Stage 2b model can train reproducibly on the existing data split and expose a stable refinement contract
**Depends on**: Nothing
**Requirements**: LSTM-01, LSTM-02, LSTM-03
**Success Criteria** (what must be TRUE):
  1. Message-sequence preprocessing for the LSTM path is defined clearly and handles empty/short histories deterministically
  2. An LSTM Stage 2b model can be trained on BotSim-24 data under the existing seed and split conventions
  3. The LSTM path exposes outputs that can feed the current Stage 2 or meta-model flow, or the deviation is documented explicitly
**Plans**: 2 plans
Plans:
- [x] 08-01-PLAN.md - Sequence contract and deterministic preprocessing
- [x] 08-02-PLAN.md - Trainable LSTM prototype and fixture-backed contract proof

### Phase 9: Cascade Integration and Variant Selection
**Goal**: The cascade can run with either the AMR delta-refiner baseline or the LSTM Stage 2b variant in a controlled, testable way
**Depends on**: Phase 8
**Requirements**: LSTM-04, LSTM-05, LSTM-06
**Success Criteria** (what must be TRUE):
  1. Training and inference can select the LSTM Stage 2b path without breaking existing cascade behavior
  2. The AMR delta-refiner path remains available as a baseline
  3. Tests or reproducible checks cover the new variant-selection and integration contract
**Plans**: 2 plans
Plans:
- [x] 09-01-PLAN.md - Explicit Stage 2b selector through shared training state
- [x] 09-02-PLAN.md - Inference routing and deterministic integration proof

### Phase 10: Evaluation and Baseline Comparison
**Goal**: The LSTM Stage 2b variant is evaluated against the current AMR Stage 2b baseline and the result is documented honestly
**Depends on**: Phase 9
**Requirements**: LSTM-07, LSTM-08
**Success Criteria** (what must be TRUE):
  1. The workstream can compare the LSTM variant against the AMR baseline on meaningful evaluation outputs
  2. The result makes clear whether the LSTM path is better, worse, or just behaviorally different
  3. The milestone artifacts preserve the final recommendation and supporting evidence
**Plans**: 2 plans
Plans:
- [ ] 10-01-PLAN.md - Real S3 AMR-vs-LSTM comparison path and evidence artifact
- [ ] 10-02-PLAN.md - Compact comparison tables and final recommendation record

## Progress Table

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 8. LSTM Stage 2b Foundation | 2/2 | Complete | 2026-04-16 |
| 9. Cascade Integration and Variant Selection | 2/2 | Complete | 2026-04-16 |
| 10. Evaluation and Baseline Comparison | 0/2 | Planned | - |

---
*Roadmap created: 2026-04-16*
*Phase range: 8-10 (workstream-local milestone numbering)*
