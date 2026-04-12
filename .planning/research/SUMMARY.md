# Project Research Summary

**Project:** Social Bot Detection System — v1.1 Feature Leakage Audit & Fix
**Domain:** ML cascade classifier audit, social bot detection (BotSim-24)
**Researched:** 2026-04-12
**Confidence:** HIGH

## Executive Summary

This milestone addresses a confirmed semantic identity leakage in Stage 2a of the cascade bot detector. The root cause is well-understood and code-verified: `features_stage2.py` appends `"USERNAME: <username>"` and `"PROFILE: <profile_description>"` strings to the sentence-transformer embedding pool alongside message content, and `botdetector_pipeline.py` further amplifies this leak by passing `text_field="profile"` to the AMR delta-logit refiner. In BotSim-24, bot profile descriptions are AI-generated and follow templates while human profiles are organic, making them trivially separable. The near-perfect Stage 2a AUC (97–100%) is an artifact of this separation, not a signal of genuine bot behavior.

The recommended fix is a two-path surgical removal: strip username and profile from the embedding texts list in `extract_stage2_features`, and replace `text_field="profile"` in the AMR extractor with a representative message-text anchor. After fixing both paths simultaneously, the full system must be retrained from scratch — including all meta-learners (`meta12`, `meta123`) and threshold recalibration — because the downstream stacking models were trained on outputs from the leaky Stage 2a. Once the clean baseline is established, an ablation study with force-routing can rigorously quantify each stage's discriminative contribution for paper submission.

The key risk is incomplete repair: two independent code paths inject the same leaked signal, and fixing only one leaves a hidden residual. The secondary risk is evaluating ablation variants without retraining meta-learners, which measures distribution mismatch rather than feature contribution. Both risks have deterministic detection criteria (Stage 2a AUC remaining above 95% signals residual leakage; meta123 AUC dramatically below meta12 signals missing meta-learner retrain).

## Key Findings

### Recommended Stack

The existing stack requires only one addition. `shap >= 0.45` is the only new dependency needed for this milestone — `TreeExplainer` provides native LightGBM support with exact (not sampled) SHAP values, giving per-feature importance analysis to confirm the leakage audit findings. All other required tools (`sklearn.inspection.permutation_importance`, `pandas.DataFrame.to_latex()`, `matplotlib`) are already present transitively.

**Core technologies:**
- `shap >= 0.45`: Feature importance for LightGBM — access via `model.calibrated_classifiers_[0].estimator.booster_`
- `sklearn.inspection.permutation_importance`: Fallback importance when direct booster access is awkward — already in stack
- `pandas.DataFrame.to_latex()`: Paper-ready ablation tables — already in stack

See `STACK.md` for full details and explicit exclusion rationale (LIME, captum, mlflow, wandb all excluded as unjustified overhead for a single audit pass).

### Expected Features

The leakage fix requires surgical removal of two anti-features and replacement with clean behavioral signals. All replacement features derive solely from message content and timestamps — no identity strings, no dataset-construction artifacts.

**Must have (table stakes — immediate, Phase 5):**
- Message-text-only embeddings (content only) — strip username/profile from encoding pool; embed message texts only
- Coefficient of variation of inter-post deltas — one arithmetic step over existing `ts` array; directly measures machine-regularity
- Message character length distribution stats (mean, std) — no new data source; captures bot uniformity
- Posting hour-of-day entropy — requires `ts` → hour conversion; humans cluster in waking hours, bots are uniform

**Should have (differentiators — Phase 6):**
- Cross-message cosine similarity (mean pairwise) — directly measures copy-paste/template reuse across posts
- Near-duplicate fraction (sim > 0.9) — interpretable threshold version of the above; computed in same embedding pass
- Aggregate type/token ratio — more stable than per-message uniq_ratio for short messages

**Defer (not for this milestone):**
- Any features requiring external data sources not already in BotSim-24
- Profile-text features of any kind — the root cause of current leakage

**Expected outcome:** Stage 2a AUC drops from 97–100% to 70–85% range. This is a correct result — not a regression.

### Architecture Approach

The cascade architecture is sound. The bug is purely in text-field selection, not in the architecture itself. The correct build order respects cascade dependencies: meta-learners sit downstream of Stage 2a, so any Stage 2a feature change must propagate a full retrain of `meta12` and `meta123`. Force-routing (setting routing thresholds to 0.0/1.0) is the correct ablation pattern for cascades — it ensures the full test set is evaluated at each stage rather than only the ambiguous minority that normally reaches downstream stages.

**Major components:**
1. `features_stage2.py:extract_stage2_features` — remove username/profile from texts list (Phase 5)
2. `botdetector_pipeline.py:extract_amr_embeddings_for_accounts` — replace `text_field="profile"` with message text anchor (Phase 5)
3. New `ablation.py` — AblationConfig dataclass, force-routing threshold helpers, results collector (Phase 6)
4. Paper tables module — LaTeX table generation via `pd.to_latex()` for four ablation tables (Phase 7)

The ablation study requires four paper tables: (1) leakage audit before/after, (2) stage contribution via force-routing, (3) routing efficiency statistics, (4) Stage 1 feature group ablation via column masking.

### Critical Pitfalls

1. **Partial leakage fix leaves residual leak (P1)** — Two independent code paths inject the leaked signal. Fix both `features_stage2.py:50-53` and `botdetector_pipeline.py:539` in the same commit. Detection: Stage 2a AUC > 95% after fix means a second source remains.

2. **Meta-learners not retrained after feature change (P3)** — `meta12` and `meta123` are stacking models trained on leaky Stage 2a outputs. Every ablation variant that changes any stage must retrain all downstream meta-learners from scratch. Detection: meta123 AUC dramatically below meta12 AUC after a variant run.

3. **`character_setting` column retained in DataFrame (P2)** — `botsim24_io.py` keeps this bot-only field with only a comment warning. Drop it at load time in `build_account_table`. Detection: assert `character_setting not in df.columns` before feature extraction.

4. **Threshold not recalibrated for clean baseline (P5)** — After removing leaky features, probability distributions change substantially. Run full Optuna calibration on S2 for the clean baseline. Fix those thresholds for all subsequent ablation variants to prevent threshold-shopping.

5. **Ablation evaluated on S2 instead of S3 (P4)** — S2 is the Optuna calibration set; reporting metrics on S2 double-dips. All paper ablation tables must report S3 metrics only.

## Implications for Roadmap

Based on research, the build order is strictly determined by cascade dependencies. Each phase gates the next.

### Phase 5: Leakage Fix and Baseline Retrain

**Rationale:** This is the prerequisite for all subsequent work. No ablation result is meaningful until the leakage is removed and a clean baseline AUC is confirmed. Both leakage paths must be fixed atomically to avoid residual leakage (P1).

**Delivers:** A clean v1.1 system with realistic Stage 2a AUC (70–85%), recalibrated thresholds, and all meta-learners retrained on clean predictions.

**Addresses:**
- All table-stakes features from FEATURES.md (strip username/profile, add CV of inter-post deltas, message length stats, hour-of-day entropy)
- AMR text field fix (profile → representative message text)

**Avoids:** P1 (partial fix), P2 (character_setting), P3 (meta-learner not retrained), P5 (threshold not recalibrated), P6 (CalibratedClassifierCV calibration concern)

### Phase 6: Ablation Infrastructure and Differentiator Features

**Rationale:** Once the clean baseline exists, ablation infrastructure can be built against it. The force-routing pattern (P7) must be implemented before running stage contribution tables. Cross-message similarity features (differentiators from FEATURES.md) are added here because they share a per-message embedding pass that can be done efficiently once.

**Delivers:** `ablation.py` with AblationConfig, force-routing helpers, and results collector. Cross-message cosine similarity and near-duplicate fraction as additional Stage 2a features.

**Uses:** `shap >= 0.45` for feature importance confirmation; `sklearn.inspection.permutation_importance` as fallback.

**Implements:** Ablation runner architecture from ARCHITECTURE.md; differentiator features from FEATURES.md.

**Avoids:** P4 (S2 vs S3 evaluation), P7 (confidence routing instead of force-routing), P12 (cross-message similarity cache invalidation)

### Phase 7: Ablation Execution and Paper Tables

**Rationale:** Run all ablation variants after infrastructure is in place and generate the four paper tables. The flat LightGBM baseline (P8) and AUC-ROC reporting (P9) must be included. Multi-seed runs (P13) are optional but strongly recommended.

**Delivers:** Four paper-ready LaTeX ablation tables covering leakage audit, stage contribution, routing efficiency, and Stage 1 feature group ablation.

**Avoids:** P8 (missing flat baseline), P9 (F1-only reporting), P11 (AMR stub misrepresentation), P13 (no confidence intervals)

### Phase Ordering Rationale

- Phase 5 must come first: meta-learners cannot be meaningfully evaluated until Stage 2a features are clean. All downstream evaluation is corrupted otherwise.
- Phase 6 must follow Phase 5: the clean baseline AUC is the acceptance criterion for Phase 5 and the starting point for ablation design.
- Phase 7 must follow Phase 6: force-routing infrastructure and differentiator features must be in place before running the full ablation suite.
- Within Phase 5, both leakage paths must be fixed atomically (same commit, same retrain run) to prevent partial-fix confusion.

### Research Flags

Phases with well-documented patterns (skip additional research):
- **Phase 5:** Leakage removal is a code-audit task with exact line numbers identified. Retrain procedure follows existing `train_system()` and `calibrate()` call sequence. No new patterns needed.
- **Phase 6:** Force-routing pattern is explicitly documented in ARCHITECTURE.md with code examples. AblationConfig is straightforward dataclass design.
- **Phase 7:** `pd.to_latex()` usage is standard. Four table structures fully specified in ARCHITECTURE.md.

No phases require additional research-phase investigation.

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Single justified addition (shap). All other tools already present. Exclusion list is explicit. |
| Features | HIGH | Leakage root cause code-verified at exact line numbers. Replacement features are derived from existing data fields with no new sources required. |
| Architecture | HIGH | Build order is determined by cascade dependency graph — not ambiguous. Force-routing pattern is established ML practice for cascade ablation. |
| Pitfalls | HIGH | All critical pitfalls are code-verified (exact file:line references). Detection criteria are deterministic. |

**Overall confidence:** HIGH

### Gaps to Address

- **CalibratedClassifierCV calibration bias (P6):** Using `cv=3` on the same data used for training inflates calibration curves on training data. This is a known concern but the fix (`cv="prefit"` with a held-out calibration subset) requires restructuring the training pipeline. Recommendation: flag as known limitation in Phase 5; assess whether the fix is feasible within scope or deferred to v1.2.

- **Multi-seed ablation stability (P13):** Single-seed ablation results may not be stable. The research flags this as optional but increasingly expected by reviewers. Decision point in Phase 7: run 3 seeds (SEED=42, 43, 44) if compute time allows, or note single-seed caveat explicitly in paper.

- **AMR stub framing for paper (P11):** After the profile → message-text fix, the AMR contribution claim must be restated. This is a writing task, not a code task, but the exact framing ("learned semantic delta-logit refinement via message-text embedding") needs to be agreed before paper submission.

## Sources

### Primary (HIGH confidence)
- `features_stage2.py:50-52` — Direct code inspection confirming username/profile injection into embedding pool
- `botdetector_pipeline.py:539` — Direct code inspection confirming `text_field="profile"` in AMR extractor
- `botsim24_io.py` — Direct code inspection confirming `character_setting` column retained in DataFrame

### Secondary (MEDIUM confidence)
- scikit-learn documentation — `CalibratedClassifierCV` behavior with pre-fitted estimators and `cv` parameter
- shap library documentation — `TreeExplainer` native LightGBM support, `booster_` access pattern
- BotSim-24 dataset documentation — label assignment process (first 1907 = human, rest = bot) confirming profile leakage mechanism

### Tertiary (LOW confidence)
- General ML literature — 70–85% AUC range as "realistic" for content-only Stage 2 classifiers; actual result will be determined empirically after fix

---
*Research completed: 2026-04-12*
*Ready for roadmap: yes*
