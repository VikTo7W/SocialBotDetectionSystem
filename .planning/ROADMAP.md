# Roadmap: Social Bot Detection System

## Milestones

- [x] **v1.0 MVP** - Phases 1-4 (shipped 2026-04-12)
- [x] **v1.1 Feature Leakage Audit & Fix** - Phases 5-7 (shipped 2026-04-16)
- [x] **v1.2 TwiBot-20 Cross-Domain Transfer** - Phases 8-10 (shipped 2026-04-18)
- [x] **v1.3 Twibot System Version** - Phases 11-13 (shipped 2026-04-18)
- [x] **v1.4 Twitter-Native Supervised Baseline** - Phases 14-16 (shipped 2026-04-18)
- [x] **v1.5 Unified Modular Codebase** - Phases 17-21 (shipped 2026-04-19)
- [ ] **v1.6 Structural Consolidation and Code Surface Cleanup** - Phases 22-25 (active)

## Phases

<details>
<summary>[x] v1.0 MVP (Phases 1-4) - SHIPPED 2026-04-12</summary>

- [x] Phase 1: Pipeline Integration (0/0 plans) - completed 2026-03-19
- [x] Phase 2: Threshold Calibration (2/2 plans) - completed 2026-03-19
- [x] Phase 3: Evaluation (1/1 plans) - completed 2026-03-19
- [x] Phase 4: REST API (2/2 plans) - completed 2026-03-19

</details>

<details>
<summary>[x] v1.1 Feature Leakage Audit & Fix (Phases 5-7) - SHIPPED 2026-04-16</summary>

- [x] Phase 5: Leakage Fix and Baseline Retrain (2/2 plans) - completed 2026-04-14
- [x] Phase 6: Ablation Infrastructure and Differentiator Features (2/2 plans) - completed 2026-04-15
- [x] Phase 7: Ablation Execution and Paper Tables (2/2 plans) - completed 2026-04-15

</details>

<details>
<summary>[x] v1.2 TwiBot-20 Cross-Domain Transfer (Phases 8-10) - SHIPPED 2026-04-18</summary>

- [x] Phase 8: Behavioral Tweet Parser and Transfer Adapter Stabilization (2/2 plans) - completed 2026-04-17
- [x] Phase 9: Sliding-Window Online Threshold Recalibration (1/1 plans) - completed 2026-04-18
- [x] Phase 10: Cross-Domain Evaluation and Paper Output (2/2 plans) - completed 2026-04-18

</details>

<details>
<summary>[x] v1.3 Twibot System Version (Phases 11-13) - SHIPPED 2026-04-18</summary>

- [x] Phase 11: Reproducible TwiBot Evaluation Flow (2/2 plans) - completed 2026-04-18
- [x] Phase 12: Fresh Transfer Evidence and Paper Outputs (2/2 plans) - completed 2026-04-18
- [x] Phase 13: System Version Packaging and Release Docs (2/2 plans) - completed 2026-04-18

</details>

<details>
<summary>[x] v1.4 Twitter-Native Supervised Baseline (Phases 14-16) - SHIPPED 2026-04-18</summary>

- [x] Phase 14: Twitter-Native Feature Pipeline (3/3 plans) - completed 2026-04-18
- [x] Phase 15: TwiBot Cascade Training and Evaluation (2/2 plans) - completed 2026-04-18
- [x] Phase 16: Comparative Paper Outputs and Reddit Cleanup (3/3 plans) - completed 2026-04-18

</details>

<details>
<summary>[x] v1.5 Unified Modular Codebase (Phases 17-21) - SHIPPED 2026-04-19</summary>

- [x] Phase 17: Shared Feature Extraction Module (6/6 plans) - completed 2026-04-19
- [x] Phase 18: Unified Cascade Pipeline and Calibration (4/4 plans) - completed 2026-04-19
- [x] Phase 19: Training Entry Points and Fresh Model Retraining (4/4 plans) - completed 2026-04-19
- [x] Phase 20: Evaluation Entry Points and Paper Outputs (5/5 plans) - completed 2026-04-19
- [x] Phase 21: Documentation (3/3 plans) - completed 2026-04-19

</details>

<details open>
<summary>[ ] v1.6 Structural Consolidation and Code Surface Cleanup (Phases 22-25) - ACTIVE</summary>

- [ ] Phase 22: Pipeline Surface Consolidation (0/3 plans) - ready to execute
- [ ] Phase 23: Unified Feature Surface (0/0 plans) - pending
- [ ] Phase 24: Unified Dataset I/O and Caller Migration (0/0 plans) - pending
- [ ] Phase 25: Final File Cleanup and Comment Pass (0/0 plans) - pending

</details>

## Phase Details

### Phase 22: Pipeline Surface Consolidation
**Goal**: Collapse overlapping maintained responsibilities between `botdetector_pipeline.py` and `cascade_pipeline.py` so one pipeline/orchestration surface is clearly the source of truth
**Depends on**: Phase 21
**Requirements**: CONS-01, PRES-03
**Success Criteria** (what must be TRUE):
  1. One maintained pipeline/orchestration layer clearly owns fit/predict routing and stage coordination
  2. Overlapping helper functions, wrappers, or duplicated orchestration logic are removed or collapsed
  3. Split discipline, routing logic, and AMR-only Stage 2b behavior remain unchanged after the consolidation
  4. Maintained callers still work without needing to know about multiple pipeline surfaces
**Plans**: 3 plans
Plans:
- [x] 22-01-PLAN.md - Create the red-test safety net for the maintained pipeline surface and compatibility-forwarding contract (CONS-01, PRES-03)
- [x] 22-02-PLAN.md - Consolidate orchestration ownership into `cascade_pipeline.py` and demote `botdetector_pipeline.py` to compatibility or stage-support duties (CONS-01, PRES-03)
- [x] 22-03-PLAN.md - Align maintained callers and docs to the clarified pipeline owner and run parity-focused verification (CONS-01, PRES-03)
**Completed**: not completed
**UI hint**: no

### Phase 23: Unified Feature Surface
**Goal**: Consolidate maintained feature extraction into one simplified file or module surface with one unifying class contract for all stages and both datasets
**Depends on**: Phase 22
**Requirements**: CONS-02
**Success Criteria** (what must be TRUE):
  1. Maintained feature extraction lives behind one simplified file or module surface rather than multiple stage files and leftover shims
  2. A unifying class or class family cleanly exposes Stage 1, Stage 2, and Stage 3 extraction for both datasets
  3. Maintained callers and tests import the new surface directly instead of through redundant compatibility layers
  4. Dataset-specific feature constraints remain intact even after the surface is consolidated
**Plans**: 0 plans
**Completed**: not completed
**UI hint**: no

### Phase 24: Unified Dataset I/O and Caller Migration
**Goal**: Merge BotSim-24 and TwiBot-20 dataset I/O into one maintained surface and migrate maintained callers onto the consolidated internals without changing external artifact or output contracts
**Depends on**: Phase 23
**Requirements**: CONS-03, PRES-01, PRES-02
**Success Criteria** (what must be TRUE):
  1. One maintained dataset I/O surface covers BotSim-24 and TwiBot-20 loading, split access, and caller-facing preparation
  2. Maintained training and evaluation entry points use the unified dataset I/O and consolidated internals
  3. Public artifact names, metric schema, and paper-output filenames stay unchanged
  4. API and batch callers remain aligned with the simplified code surface
**Plans**: 0 plans
**Completed**: not completed
**UI hint**: no

### Phase 25: Final File Cleanup and Comment Pass
**Goal**: Remove obsolete redundant files after the consolidation settles and add short lowercase descriptive comments to maintained classes and methods where they genuinely help readability
**Depends on**: Phase 24
**Requirements**: CONS-04, QUAL-03
**Success Criteria** (what must be TRUE):
  1. Redundant maintained-code files and stale compatibility layers are removed once no maintained caller depends on them
  2. The active repo surface is visibly smaller and easier to navigate than the v1.5 layout
  3. Maintained classes and methods have concise lowercase comments only where they help the next reader understand intent
  4. Documentation and tests point only to the simplified maintained surface
**Plans**: 0 plans
**Completed**: not completed
**UI hint**: no

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Pipeline Integration | v1.0 | 0/0 | Complete | 2026-03-19 |
| 2. Threshold Calibration | v1.0 | 2/2 | Complete | 2026-03-19 |
| 3. Evaluation | v1.0 | 1/1 | Complete | 2026-03-19 |
| 4. REST API | v1.0 | 2/2 | Complete | 2026-03-19 |
| 5. Leakage Fix and Baseline Retrain | v1.1 | 2/2 | Complete | 2026-04-14 |
| 6. Ablation Infrastructure and Differentiator Features | v1.1 | 2/2 | Complete | 2026-04-15 |
| 7. Ablation Execution and Paper Tables | v1.1 | 2/2 | Complete | 2026-04-15 |
| 8. Behavioral Tweet Parser and Transfer Adapter Stabilization | v1.2 | 2/2 | Complete | 2026-04-17 |
| 9. Sliding-Window Online Threshold Recalibration | v1.2 | 1/1 | Complete | 2026-04-18 |
| 10. Cross-Domain Evaluation and Paper Output | v1.2 | 2/2 | Complete | 2026-04-18 |
| 11. Reproducible TwiBot Evaluation Flow | v1.3 | 2/2 | Complete | 2026-04-18 |
| 12. Fresh Transfer Evidence and Paper Outputs | v1.3 | 2/2 | Complete | 2026-04-18 |
| 13. System Version Packaging and Release Docs | v1.3 | 2/2 | Complete | 2026-04-18 |
| 14. Twitter-Native Feature Pipeline | v1.4 | 3/3 | Complete | 2026-04-18 |
| 15. TwiBot Cascade Training and Evaluation | v1.4 | 2/2 | Complete | 2026-04-18 |
| 16. Comparative Paper Outputs and Reddit Cleanup | v1.4 | 3/3 | Complete | 2026-04-18 |
| 17. Shared Feature Extraction Module | v1.5 | 6/6 | Complete | 2026-04-19 |
| 18. Unified Cascade Pipeline and Calibration | v1.5 | 4/4 | Complete | 2026-04-19 |
| 19. Training Entry Points and Fresh Model Retraining | v1.5 | 4/4 | Complete | 2026-04-19 |
| 20. Evaluation Entry Points and Paper Outputs | v1.5 | 5/5 | Complete | 2026-04-19 |
| 21. Documentation | v1.5 | 3/3 | Complete | 2026-04-19 |
| 22. Pipeline Surface Consolidation | v1.6 | 3/3 | Complete   | 2026-04-19 |
| 23. Unified Feature Surface | v1.6 | 0/0 | Not started | |
| 24. Unified Dataset I/O and Caller Migration | v1.6 | 0/0 | Not started | |
| 25. Final File Cleanup and Comment Pass | v1.6 | 0/0 | Not started | |
