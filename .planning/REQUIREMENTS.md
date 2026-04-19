# Requirements: v1.6 Structural Consolidation and Code Surface Cleanup

**Created:** 2026-04-19
**Milestone:** v1.6 Structural Consolidation and Code Surface Cleanup
**Status:** Active

## Milestone Goal

Reduce maintained surfaces and overall file count by collapsing duplicate pipeline, feature, and dataset-I/O layers into single maintained modules, then add a short genuine comment pass across the simplified codebase.

## Requirements

### Structural Consolidation

- [ ] **CONS-01**: The project exposes one clearly maintained pipeline/orchestration surface; overlapping responsibilities between `botdetector_pipeline.py` and `cascade_pipeline.py` are removed or collapsed
- [ ] **CONS-02**: Maintained feature extraction lives in one consolidated file or module surface with one unifying class contract for all stages and both datasets
- [ ] **CONS-03**: Maintained dataset loading and dataset-specific preparation live in one consolidated file or module surface covering both BotSim-24 and TwiBot-20
- [ ] **CONS-04**: Active repo file count is reduced by removing redundant maintained-code files, wrappers, and compatibility layers once the simplified surfaces are in place

### Behavior Preservation

- [ ] **PRES-01**: Maintained training entry points (`train_botsim.py`, `train_twibot.py`) continue to work against the consolidated code surface without changing public artifact names
- [ ] **PRES-02**: Maintained evaluation entry points continue to work without changing paper-output filenames, metric schema, or Table 5 inputs
- [ ] **PRES-03**: Split discipline, routing logic, AMR-only Stage 2b behavior, and dataset-specific feature constraints are preserved through the cleanup

### Code Quality

- [ ] **QUAL-03**: Maintained classes and methods receive short lowercase descriptive comments where they genuinely improve readability, without padding the codebase with noisy boilerplate

## Future Requirements

- Full TwiBot-native fresh retraining rerun and artifact verification after the user-deferred debug cycle
- Full pytest green-suite once the Windows temp-dir cleanup issue is resolved
- Multi-seed ablation stability for paper confidence intervals
- True AMR graph parsing replacing the current embedding stub

## Out of Scope

| Feature | Reason |
|---------|--------|
| New model families or architecture redesign | This milestone is structural cleanup, not algorithm replacement |
| Frontend or dashboard UI | API and scripts only |
| Model retraining through the API | Offline training only |
| Changing maintained artifact names | External contract should stay stable |
| Changing maintained paper-output filenames or metric schema | Reproduction and docs should not need a second rewrite |
| Reintroducing the LSTM Stage 2b path | v1.5 retired it intentionally |
| Online novelty recalibration in the maintained Reddit path | v1.4 already retired it |

## Traceability

| REQ-ID | Phase | Status |
|--------|-------|--------|
| CONS-01 | Phase 22 | Pending |
| PRES-03 | Phase 22 | Pending |
| CONS-02 | Phase 23 | Pending |
| CONS-03 | Phase 24 | Pending |
| PRES-01 | Phase 24 | Pending |
| PRES-02 | Phase 24 | Pending |
| CONS-04 | Phase 25 | Pending |
| QUAL-03 | Phase 25 | Pending |
