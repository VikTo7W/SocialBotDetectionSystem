# Requirements: Stage 2b LSTM Variant

**Workstream:** stage2b-lstm-version
**Defined:** 2026-04-16
**Core Value:** The cascade must still produce a single, well-calibrated bot probability per account while letting us test whether a sequence-model Stage 2b adds useful signal beyond the current AMR-inspired refinement path.

## v1.2.1 Requirements

### LSTM Stage 2b Model

- [x] **LSTM-01**: Developer can train an LSTM-based Stage 2b model on BotSim-24 message sequences using the existing split discipline without introducing leakage
- [x] **LSTM-02**: The LSTM Stage 2b path produces a drop-in refinement output compatible with the current Stage 2 / meta-model flow, or an explicitly documented equivalent contract
- [x] **LSTM-03**: Sequence preprocessing for the LSTM path handles empty or short message histories deterministically and reproducibly

### Cascade Integration

- [ ] **LSTM-04**: The cascade can run with the LSTM Stage 2b variant enabled without breaking the existing AMR-based baseline path
- [ ] **LSTM-05**: Configuration or code-path selection makes it clear which Stage 2b variant is active during training and inference
- [ ] **LSTM-06**: Tests or reproducible checks cover the new LSTM Stage 2b training/inference contract

### Evaluation and Comparison

- [ ] **LSTM-07**: Developer can compare the LSTM Stage 2b variant against the current AMR delta-refiner baseline on meaningful metrics or routing behavior
- [ ] **LSTM-08**: Workstream artifacts record whether the LSTM variant is better, worse, or merely different, and on what evidence

## Future Requirements

- **LSTM-F01**: Hyperparameter sweep for hidden size, sequence truncation, and pooling strategy
- **LSTM-F02**: Cross-dataset comparison of the LSTM Stage 2b path on TwiBot-20 once the TwiBot workstream is complete

## Out of Scope

| Feature | Reason |
|---------|--------|
| Full cascade redesign | This milestone is limited to a Stage 2b variant |
| Removal of the current AMR delta refiner | The current path must remain as the baseline |
| Frontend/API redesign for model selection | Internal research milestone only |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| LSTM-01 | Phase 8 | Complete |
| LSTM-02 | Phase 8 | Complete |
| LSTM-03 | Phase 8 | Complete |
| LSTM-04 | Phase 9 | Pending |
| LSTM-05 | Phase 9 | Pending |
| LSTM-06 | Phase 9 | Pending |
| LSTM-07 | Phase 10 | Pending |
| LSTM-08 | Phase 10 | Pending |

**Coverage:**
- v1.2.1 requirements: 8 total
- Mapped to phases: 8 (100%)
- Unmapped: 0

---
*Requirements defined: 2026-04-16*
