# Roadmap: Social Bot Detection System

## Milestones

- ✅ **v1.0 MVP** — Phases 1-4 (shipped 2026-04-12)
- ✅ **v1.1 Feature Leakage Audit & Fix** — Phases 5-7 (shipped 2026-04-16)
- [ ] **v1.2 TwiBot-20 Cross-Domain Transfer** — Phases 8-10 (active)

## Phases

<details>
<summary>✅ v1.0 MVP (Phases 1-4) — SHIPPED 2026-04-12</summary>

- [x] Phase 1: Pipeline Integration (0 plans — pre-existing) — completed 2026-03-19
- [x] Phase 2: Threshold Calibration (2/2 plans) — completed 2026-03-19
- [x] Phase 3: Evaluation (1/1 plans) — completed 2026-03-19
- [x] Phase 4: REST API (2/2 plans) — completed 2026-03-19

See `.planning/milestones/v1.0-ROADMAP.md` for full phase details.

</details>

<details>
<summary>✅ v1.1 Feature Leakage Audit & Fix (Phases 5-7) — SHIPPED 2026-04-16</summary>

- [x] Phase 5: Leakage Fix and Baseline Retrain (2/2 plans) — completed 2026-04-14
- [x] Phase 6: Ablation Infrastructure and Differentiator Features (2/2 plans) — completed 2026-04-15
- [x] Phase 7: Ablation Execution and Paper Tables (2/2 plans) — completed 2026-04-15

See `.planning/milestones/v1.1-ROADMAP.md` for full phase details.

</details>

<details open>
<summary>v1.2 TwiBot-20 Cross-Domain Transfer (Phases 8-10) — ACTIVE</summary>

- [ ] **Phase 8: Behavioral Tweet Parser and Stage 1 Adapter** - One-line description
- [ ] **Phase 9: Sliding-Window Online Threshold Recalibration** - One-line description
- [ ] **Phase 10: Cross-Domain Evaluation and Paper Output** - One-line description

</details>

## Phase Details

### Phase 8: Behavioral Tweet Parser and Stage 1 Adapter
**Goal**: The system can accept a TwiBot-20 account's tweet list and produce valid Stage 1 feature vectors using behaviorally-grounded Twitter equivalents
**Depends on**: Phase 7 (existing trained cascade)
**Requirements**: FEAT-01, FEAT-02, FEAT-03
**Success Criteria** (what must be TRUE):
  1. Given a list of tweets for an account, the parser correctly classifies each tweet as RT-prefixed, MT-prefixed, or original, and extracts the set of distinct @usernames from RT/MT tweets
  2. The Stage 1 adapter produces a feature vector where submission_num equals the original tweet count, comment_num_1 equals the RT count, comment_num_2 equals the MT count, and subreddit_list equals the distinct @username list
  3. The adapter feeds into the existing trained Stage 1 LightGBM without any model retraining — zero-shot transfer is confirmed by running inference end-to-end on at least one TwiBot-20 account without errors
  4. The ratio cap is reviewed against TwiBot-20 tweet-count distributions; the cap value is either retained with documented justification or updated, and the decision is recorded
**Plans**: TBD
**UI hint**: no

### Phase 9: Sliding-Window Online Threshold Recalibration
**Goal**: The inference pipeline adjusts routing thresholds unsupervised as accounts are processed, using only novelty scores from a running buffer
**Depends on**: Phase 8
**Requirements**: CAL-01, CAL-02, CAL-03
**Success Criteria** (what must be TRUE):
  1. After N accounts are processed, the calibrator computes updated routing thresholds from the novelty score buffer and applies them to subsequent accounts — labels are never consulted during this process
  2. The window size N is configurable via a parameter (default 100), and changing N produces different update cadences without code changes
  3. When fewer than N accounts have been processed (cold start), the calibrator leaves the original trained thresholds unchanged rather than producing degenerate values
  4. The calibrator can be toggled off so that the original static thresholds are used, allowing before/after comparison in Phase 10
**Plans**: TBD
**UI hint**: no

### Phase 10: Cross-Domain Evaluation and Paper Output
**Goal**: Quantitative evidence of zero-shot transfer performance on TwiBot-20 is produced and formatted for the paper's robustness section
**Depends on**: Phase 8, Phase 9
**Requirements**: EVAL-01, EVAL-02
**Success Criteria** (what must be TRUE):
  1. Running the evaluation script on TwiBot-20 produces F1, AUC, precision, and recall under both conditions: (a) current demographic proxy adapter and (b) behavioral RT/MT adapter
  2. The before/after comparison is printed in a structured format that makes the performance delta immediately readable
  3. A LaTeX table is generated comparing BotSim-24 in-domain performance against TwiBot-20 zero-shot transfer performance, formatted to drop into the paper's robustness section without manual editing
**Plans**: TBD
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
| 8. Behavioral Tweet Parser and Stage 1 Adapter | v1.2 | 0/? | Not started | - |
| 9. Sliding-Window Online Threshold Recalibration | v1.2 | 0/? | Not started | - |
| 10. Cross-Domain Evaluation and Paper Output | v1.2 | 0/? | Not started | - |
