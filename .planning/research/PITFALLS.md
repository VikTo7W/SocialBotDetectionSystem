# Pitfalls: Feature Leakage Audit & Ablation in Bot Detection Cascade

**Domain:** Social bot detection — BotSim-24, cascade classifier audit
**Researched:** 2026-04-12
**Milestone:** v1.1 Feature Leakage Audit & Fix

---

## Critical (Block Phase 1 if not addressed)

### P1 — Partial leakage fix leaves residual leak
**What:** Two separate code paths inject the leaked profile signal. Fixing only one leaves a hidden residual.
- Path 1: `features_stage2.py:50-53` — username and profile appended to embedding texts
- Path 2: `botdetector_pipeline.py:539` — `extract_amr_embeddings_for_accounts(..., text_field="profile")`

**Prevention:** Phase 1 must fix both in the same commit and re-run together.
**Detection:** After fix, run Stage 2a alone on S3 — if AUC is still >95%, a second source remains.
**Phase:** 5 (Leakage Fix)

### P2 — `character_setting` retained in DataFrame
**What:** `botsim24_io.py` keeps the `character_setting` column (bot-only field) in the accounts DataFrame with only a comment warning. Any accidental iteration over string columns or future feature addition could silently include it.
**Prevention:** Drop `character_setting` at load time in `build_account_table`, not just by comment.
**Detection:** Check that `character_setting` is not in `df.columns` for any DataFrame passed to feature extractors.
**Phase:** 5 (Leakage Fix)

### P3 — Meta-learners not retrained after feature change
**What:** `meta12` and `meta123` are stacking models trained on Stage 2a outputs. If Stage 2a features change but meta-learners are not retrained, the ablation measures distribution mismatch, not feature contribution.
**Prevention:** Every ablation variant that changes any stage must retrain all downstream meta-learners from scratch via `train_system()`. Zero-masking features without retraining is invalid.
**Detection:** If meta123 AUC is significantly lower than meta12 AUC after a variant run, the meta-learner was likely not retrained.
**Phase:** 5 (Leakage Fix), 6 (Ablation)

---

## High (Address before ablation phase)

### P4 — Ablation evaluated on S2 instead of S3
**What:** S2 is the threshold calibration set (Optuna TPE). Reporting ablation metrics on S2 double-dips — the thresholds were optimized on S2.
**Prevention:** All ablation tables in the paper must report S3 metrics only. S2 is for calibration, S3 is for reporting.
**Detection:** Verify that `evaluate_s3()` is called on `S3`, not `S2`, in every ablation run.
**Phase:** 6 (Ablation Infrastructure)

### P5 — Threshold not recalibrated for clean baseline
**What:** After removing leaky features, the probability distributions of all stages change substantially. Using v1.0 thresholds with clean Stage 2a outputs produces incorrect routing behavior.
**Prevention:** For the leakage-fix baseline (v1.1 clean), run full Optuna calibration on S2. For subsequent ablation variants, fix thresholds from the clean baseline to prevent threshold-shopping.
**Detection:** Check that routing statistics (% stage exits) are plausible — if 100% exit at Stage 1, thresholds were not recalibrated.
**Phase:** 5 (Leakage Fix)

### P6 — CalibratedClassifierCV fitted on training data
**What:** In Stage 1, 2a, and 3: `base.fit(X, y)` then `CalibratedClassifierCV(base, cv=3).fit(X, y)` on the same X, y. With `cv=3` and a pre-fitted estimator, sklearn re-trains in each fold — but in small datasets, this still causes optimistic calibration curves on training data.
**Prevention:** Use `cv="prefit"` with a dedicated held-out calibration subset, or accept that calibration on training data inflates S1/S2 calibration metrics (S3 evaluation is still clean).
**Detection:** Compare calibration reliability diagram on S1 vs S3 data — if S1 is perfectly calibrated but S3 shows overconfidence, this is the cause.
**Phase:** 5 (Leakage Fix) — flag as known concern; fix in same phase if feasible

---

## Medium (Address in ablation phase)

### P7 — Stage ablation uses confidence routing, not force-routing
**What:** If a stage is "ablated" by simply not routing accounts to it (normal confidence-based gating), only the ambiguous minority reaches downstream stages. This measures routing efficiency, not stage discriminative contribution.
**Prevention:** Use force-routing (set routing thresholds to 0.0/1.0) to evaluate the full test set at each stage. Report both routing-gated (efficiency) and force-routed (contribution) results.
**Phase:** 6 (Ablation Infrastructure)

### P8 — Ablation paper table missing flat baseline row
**What:** Without a "flat LightGBM on all features, no cascade" baseline, reviewers cannot assess whether the cascade architecture itself adds value over a single model.
**Prevention:** Include a flat LightGBM baseline trained on the union of all feature groups (no routing, no meta-learners) as the bottom row of the ablation table.
**Phase:** 7 (Paper Tables)

### P9 — Reporting F1 only, not AUC-ROC
**What:** F1 at threshold 0.5 hides calibration quality. For a bot detection system whose core value is a calibrated probability, AUC-ROC (threshold-independent) is the primary metric.
**Prevention:** All ablation tables must include AUC-ROC alongside F1. The routing statistics table should also include AUC-ROC for `p_final`.
**Phase:** 7 (Paper Tables)

---

## Low (Watch for)

### P10 — BotSim-24 dataset ordering bias
**What:** Labels are assigned by row order in `botsim24_io.py` (first 1907 = human, rest = bot). If the shuffle seed or split logic changes, splits could be stratified incorrectly.
**Prevention:** Always pass `stratify=accounts["label"]` and verify label counts at each split. Already implemented in `main.py` — keep this.
**Phase:** All phases

### P11 — AMR stub misrepresented in paper
**What:** The AMR "linearization" (`amr_linearize_stub`) returns the raw text unchanged. The paper should not claim true AMR graph-based semantic parsing.
**Prevention:** After fixing AMR to use message text instead of profile, state the contribution as "learned semantic delta-logit refinement via message-text embedding" — not AMR graph parsing.
**Phase:** 7 (Paper Tables / write-up)

### P12 — Cross-message similarity computed with test-set embeddings
**What:** If cross-message cosine similarity is added as a feature (Phase 6 differentiator), computing it using the sentence-transformer model that was also used for Stage 2a embedding does not introduce leakage — but the per-message embedding matrix must not be cached from training runs and reused at inference.
**Prevention:** Always re-encode messages at inference time; do not persist training embeddings and use them for test accounts.
**Phase:** 6 (if cross-message similarity is added)

### P13 — Reporting ablation without confidence intervals
**What:** Single-run ablation values look precise but may not be stable across seeds. Reviewers increasingly expect error bars.
**Prevention:** If time allows, run ablation variants with 3 seeds (SEED=42, 43, 44) and report mean ± std. Minimum: report with SEED=42 and note single-seed in paper.
**Phase:** 7 (Paper Tables)

### P14 — Stage 3 graph features from full graph, not split-filtered graph
**What:** `build_graph_features_nodeidx` computes degrees from `edges_df` which is already filtered per split in `main.py`. If a future ablation run reuses the wrong edges DataFrame, Stage 3 features will include cross-split edges.
**Prevention:** Always pass `edges_S3` to Stage 3 evaluation. Never reuse `edges_df` (full graph) for split-level feature extraction.
**Phase:** All phases
