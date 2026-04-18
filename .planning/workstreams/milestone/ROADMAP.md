# Roadmap: Social Bot Detection System

## Milestones

- [x] **v1.0 MVP** - Phases 1-4 (shipped 2026-04-12)
- [x] **v1.1 Feature Leakage Audit & Fix** - Phases 5-7 (shipped 2026-04-16)
- [x] **v1.2 TwiBot-20 Cross-Domain Transfer** - Phases 8-10 (shipped 2026-04-18)
- [ ] **v1.3 Twibot System Version** - Phases 11-13 (active)

## Phases

<details>
<summary>[x] v1.0 MVP (Phases 1-4) - SHIPPED 2026-04-12</summary>

- [x] Phase 1: Pipeline Integration (0 plans - pre-existing) - completed 2026-03-19
- [x] Phase 2: Threshold Calibration (2/2 plans) - completed 2026-03-19
- [x] Phase 3: Evaluation (1/1 plans) - completed 2026-03-19
- [x] Phase 4: REST API (2/2 plans) - completed 2026-03-19

See `.planning/milestones/v1.0-ROADMAP.md` for full phase details.

</details>

<details open>
<summary>v1.3 Twibot System Version (Phases 11-13) - ACTIVE</summary>

- [x] **Phase 11: Reproducible TwiBot Evaluation Flow** - Harden the TwiBot evaluation path so static and recalibrated runs can generate stable artifacts without the current temp/cache fragility (2/2 plans) - completed 2026-04-18
- [x] **Phase 12: Fresh Transfer Evidence and Paper Outputs** - Run fresh TwiBot comparisons, validate the observed transfer behavior, and regenerate the cross-dataset paper outputs from live artifacts (2/2 plans) - completed 2026-04-18
- [ ] **Phase 13: System Version Packaging and Release Docs** - Publish the chosen TwiBot system version with explicit artifacts, commands, caveats, and release-facing documentation

</details>

<details>
<summary>[x] v1.1 Feature Leakage Audit & Fix (Phases 5-7) - SHIPPED 2026-04-16</summary>

- [x] Phase 5: Leakage Fix and Baseline Retrain (2/2 plans) - completed 2026-04-14
- [x] Phase 6: Ablation Infrastructure and Differentiator Features (2/2 plans) - completed 2026-04-15
- [x] Phase 7: Ablation Execution and Paper Tables (2/2 plans) - completed 2026-04-15

See `.planning/milestones/v1.1-ROADMAP.md` for full phase details.

</details>

<details>
<summary>[x] v1.2 TwiBot-20 Cross-Domain Transfer (Phases 8-10) - SHIPPED 2026-04-18</summary>

- [x] **Phase 8: Behavioral Tweet Parser and Transfer Adapter Stabilization** - Replace demographic-proxy transfer assumptions with behaviorally-grounded Twitter equivalents and stabilize zero-shot transfer when TwiBot fields are systematically missing
- [x] **Phase 9: Sliding-Window Online Threshold Recalibration** - Adjust novelty routing thresholds online from buffered TwiBot novelty scores without retraining
- [x] **Phase 10: Cross-Domain Evaluation and Paper Output** - Compare static vs recalibrated TwiBot transfer and export paper-ready cross-dataset metrics

</details>

## Phase Details

### Phase 8: Behavioral Tweet Parser and Transfer Adapter Stabilization
**Goal**: The system can accept a TwiBot-20 account's tweet/domain data and produce transfer-stable features for zero-shot inference without retraining
**Depends on**: Phase 7 (existing trained cascade)
**Requirements**: FEAT-01, FEAT-02, FEAT-03, FEAT-04
**Success Criteria** (what must be TRUE):
  1. Given a list of tweets for an account, the parser correctly classifies each tweet as RT-prefixed, MT-prefixed, or original, and extracts the set of distinct @usernames from RT/MT tweets
  2. The Stage 1 transfer adapter uses a documented Twitter-to-BotSim mapping that is justified by measured TwiBot behavior rather than frozen Reddit analogies alone
  3. If TwiBot fields are systematically unavailable but not semantically zero, the transfer path handles them without collapsing entire feature blocks to misleading default values
  4. The adapter feeds into the existing trained cascade without any model retraining, and end-to-end inference on TwiBot-20 runs without errors
  5. The ratio cap is reviewed against TwiBot-20 tweet-count distributions; the cap value is either retained with documented justification or updated, and the decision is recorded
**Plans**: 2 plans
Plans:
- [x] 08-01-PLAN.md - Add parse_tweet_types() in twibot20_io.py with TDD coverage of RT/MT/original classification, case-insensitivity, @username extraction, and dedup (FEAT-01)
- [x] 08-02-PLAN.md - Rewrite the transfer adapter in evaluate_twibot20.py, add distribution/missingness logging, review/document `_RATIO_CAP`, and verify TwiBot transfer behavior (FEAT-02, FEAT-03, FEAT-04)
**UI hint**: no

### Phase 9: Sliding-Window Online Threshold Recalibration
**Goal**: The inference pipeline adjusts routing thresholds unsupervised as accounts are processed, using only novelty scores from a running buffer
**Depends on**: Phase 8
**Requirements**: CAL-01, CAL-02, CAL-03
**Success Criteria** (what must be TRUE):
  1. After N accounts are processed, the calibrator computes updated routing thresholds from the novelty score buffer and applies them to subsequent accounts - labels are never consulted during this process
  2. The window size N is configurable via a parameter (default 100), and changing N produces different update cadences without code changes
  3. When fewer than N accounts have been processed (cold start), the calibrator leaves the original trained thresholds unchanged rather than producing degenerate values
  4. The calibrator can be toggled off so that the original static thresholds are used, allowing before/after comparison in Phase 10
**Plans**: 1 plan
**UI hint**: no

### Phase 10: Cross-Domain Evaluation and Paper Output
**Goal**: Quantitative evidence of zero-shot transfer performance on TwiBot-20 is produced and formatted for the paper's robustness section
**Depends on**: Phase 8, Phase 9
**Requirements**: EVAL-01, EVAL-02
**Success Criteria** (what must be TRUE):
  1. Running the evaluation script on TwiBot-20 produces F1, AUC, precision, and recall under both conditions: (a) revised transfer adapter with static thresholds and (b) revised transfer adapter with online recalibration
  2. The before/after comparison is printed in a structured format that makes the performance delta immediately readable
  3. A LaTeX table is generated comparing BotSim-24 in-domain performance against TwiBot-20 zero-shot transfer performance, formatted to drop into the paper's robustness section without manual editing
**Plans**: 2 plans
Plans:
- [x] 10-01-PLAN.md - Add Phase 10 TwiBot before/after comparison for static vs online-recalibrated thresholds and persist comparison artifacts (EVAL-01)
- [x] 10-02-PLAN.md - Generate the final cross-dataset LaTeX table from BotSim-24 plus both TwiBot conditions (EVAL-02)
**UI hint**: no

### Phase 11: Reproducible TwiBot Evaluation Flow
**Goal**: The TwiBot evaluation path can be run reproducibly in the local environment and emits stable artifacts for both static and recalibrated evaluation modes
**Depends on**: Phase 10
**Requirements**: REPRO-01, REPRO-02, REPRO-03
**Success Criteria** (what must be TRUE):
  1. Running the TwiBot evaluation entry point produces static and recalibrated artifacts in a stable, documented output location
  2. The artifact-generation path does not depend on fragile default temp/cache directories for normal successful runs
  3. The artifact filenames and payload structures are explicit enough for downstream tooling and paper generation to consume reliably
**Plans**: 2 plans
Plans:
- [x] 11-01-PLAN.md - Fix two failing test stubs in tests/test_evaluate_twibot20.py so Phase 9 kwargs forwarding is absorbed by monkeypatched lambdas (REPRO-02, REPRO-03)
- [x] 11-02-PLAN.md - Add output_dir argument + os.path.join routing to evaluate_twibot20.py __main__, document canonical command and artifact payloads in the module docstring, and add TWIBOT_COMPARISON_PATH env-var override in ablation_tables.py (REPRO-01, REPRO-02, REPRO-03)
**UI hint**: no

### Phase 12: Fresh Transfer Evidence and Paper Outputs
**Goal**: Fresh TwiBot comparison evidence and cross-dataset outputs are generated from live runs and recorded as the current transfer result
**Depends on**: Phase 11
**Requirements**: EVID-01, EVID-02, EVID-03
**Success Criteria** (what must be TRUE):
  1. A fresh static-vs-recalibrated TwiBot run completes and saves comparison metrics from the current revised adapter
  2. The final LaTeX cross-dataset table is regenerated from live BotSim-24 and TwiBot artifacts
  3. The milestone records whether recalibration helped, hurt, or made no meaningful difference on TwiBot transfer
**Plans**: 2 plans
Plans:
- [x] 12-01-PLAN.md - Generate fresh TwiBot comparison artifacts in a milestone-owned output directory and emit a stable evidence summary from the live comparison output (EVID-01)
- [x] 12-02-PLAN.md - Regenerate Table 5 from the fresh comparison artifact and write the milestone-facing interpretation of whether recalibration materially helped transfer (EVID-02, EVID-03)
**UI hint**: no

### Phase 13: System Version Packaging and Release Docs
**Goal**: The TwiBot transfer system version is packaged as a reproducible, documented release artifact set for future evaluation and reporting
**Depends on**: Phase 12
**Requirements**: VERS-01, VERS-02, VERS-03
**Success Criteria** (what must be TRUE):
  1. The chosen TwiBot system version explicitly names the model artifact, comparison mode(s), and output files it ships with
  2. A developer can follow the docs to reproduce the TwiBot system-version artifacts end to end
  3. The release docs clearly state the remaining caveats, environment assumptions, and known limitations
**Plans**: 2 plans
Plans:
- [ ] 13-01-PLAN.md - Author VERSION.md at the project root naming the v1.3 model artifact, evaluation modes, output files, release-time transfer verdict, and environment overrides (VERS-01)
- [ ] 13-02-PLAN.md - Expand README.md with an end-to-end Reproduction Guide plus Known Caveats and Known Limitations sections, cross-referenced to VERSION.md (VERS-02, VERS-03)
**UI hint**: no

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. Pipeline Integration | v1.0 | 0/0 (pre-existing) | Complete | 2026-03-19 |
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
| 13. System Version Packaging and Release Docs | v1.3 | 0/2 | Not started | - |
