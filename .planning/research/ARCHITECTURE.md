# Architecture Research: Ablation Methodology for Cascade Bot Detection

**Domain:** ML cascade classifier — ablation study design
**Researched:** 2026-04-12
**Milestone:** v1.1 Feature Leakage Audit & Fix

---

## Key Findings

### 1. Two confirmed leakage sources (code-verified)

- `features_stage2.py:50-52` — injects `"USERNAME: " + username` and `"PROFILE: " + profile` into the sentence-transformer embedding pool alongside message content
- `botdetector_pipeline.py:539` — uses `text_field="profile"` for AMR embeddings — same leak vector, amplified

### 2. Meta-learners must be retrained after leakage fix

`meta12` and `meta123` were trained on outputs from the leaky Stage 2a. Using old meta-learners with clean Stage 2a outputs measures distribution mismatch, not feature contribution. Every ablation variant that changes Stage 2a must retrain meta12 and meta123 on clean S2 predictions.

### 3. Force-routing is the correct ablation pattern for cascades

To ablate "Stage N contribution," override the routing thresholds to force all accounts through that stage regardless of confidence. This ensures the full test set is evaluated — not just the ambiguous minority routed there in normal operation.

```python
# Force all accounts through Stage 2a (ablate Stage 1 contribution):
th.s1_bot = 0.0
th.s1_human = 1.0

# Force all accounts through Stage 3 (ablate Stage 1+2 contribution):
th.s12_bot = 0.0
th.s12_human = 1.0
```

### 4. AMR ablation does not require retraining Stage 2a

The AMR refiner is an additive delta-logit (Option C). Disabling it means setting `z2 = z2a` (no refinement) and `amr_used = zeros`, then only retraining meta12. Stage 2a weights are unchanged.

### 5. Threshold handling across ablation variants

- The leakage-fix baseline itself should recalibrate thresholds (Bayesian search on S2) — probability distributions change substantially after removing leaky features
- All subsequent ablation variants should fix thresholds from the clean baseline — prevents threshold-shopping across variants and isolates the feature contribution

---

## Ablation Study Structure

### Four tables for a complete paper ablation section

**Table 1 — Leakage Audit (before vs. after fix)**

| Variant | Stage 2a F1 | Stage 2a AUC | p_final F1 | p_final AUC |
|---------|-------------|--------------|------------|-------------|
| v1.0 (with profile+username) | ~0.97+ | ~0.99+ | ... | ... |
| v1.1 (content-only) | expected 0.70–0.85 | expected 0.75–0.90 | ... | ... |

**Table 2 — Stage Contribution (force-routed, full test set)**

Each row removes one stage by setting its routing thresholds to force pass-through:

| Variant | F1 | AUC | Prec | Recall |
|---------|-----|-----|------|--------|
| Stage 1 only (metadata) | ... | ... | ... | ... |
| Stage 1 + 2a (no AMR) | ... | ... | ... | ... |
| Stage 1 + 2a + AMR | ... | ... | ... | ... |
| Full cascade (all stages) | ... | ... | ... | ... |

**Table 3 — Routing Efficiency**

| % Stage 1 exit | % Stage 2 exit | % Stage 3 exit | AMR trigger rate | p_final F1 |
|----------------|----------------|----------------|-----------------|------------|

**Table 4 — Stage 1 Feature Group Ablation (within-stage)**

Column masking — zero out one feature group at a time, re-predict on S3:

| Features removed | Stage 1 F1 | Stage 1 AUC |
|-----------------|------------|-------------|
| All features (baseline) | ... | ... |
| -username_length | ... | ... |
| -submission_num | ... | ... |
| -comment counts | ... | ... |
| -subreddit count | ... | ... |
| -ratios only | ... | ... |

---

## Build Order for v1.1

Build order must respect cascade dependencies — meta-learners retrain downstream from stage changes:

```
Phase 5: Leakage Fix & Baseline Retrain
  → Strip username/profile from Stage 2a embedding inputs
  → Fix AMR text_field (profile → message text anchor)
  → Full retrain: all stages + meta12 + meta123 + threshold calibration
  → Confirm AUC drops to realistic range
  → This phase gates all subsequent ablation work

Phase 6: Ablation Infrastructure
  → AblationConfig dataclass for parameterized train/predict variants
  → Force-routing threshold helpers
  → Results collector (append to DataFrame, export to LaTeX via pd.to_latex())

Phase 7: Stage Contribution & Feature Group Ablation
  → Run ablation variants (Tables 2, 3, 4)
  → Generate paper-ready LaTeX tables
  → Document findings
```

---

## AMR Contribution Note for Paper

The AMR stub (profile embedding approximation, not true AMR graph parsing) means the paper's contribution claim should be stated as "learned semantic delta-logit refinement via profile-text embedding" — not full AMR semantics. After the leakage fix, this becomes "delta-logit refinement via representative message-text embedding." The architecture is sound; the text field choice was the bug.

---

## Integration Points

| Component | Change Required | Who Changes It |
|-----------|----------------|----------------|
| `features_stage2.py:extract_stage2_features` | Remove username/profile from texts list | Phase 5 |
| `botdetector_pipeline.py:extract_amr_embeddings_for_accounts` | Replace `text_field="profile"` with message text anchor | Phase 5 |
| `botdetector_pipeline.py:train_system` | No structural change; retrain after feature fix | Phase 5 |
| `main.py` | Re-run full training + calibration after fix | Phase 5 |
| New `ablation.py` | Ablation runner, AblationConfig, results export | Phase 6 |
| New `paper_tables.py` or inline in `evaluate.py` | LaTeX table generation | Phase 7 |
