# Stack Research: v1.1 Feature Leakage Audit & Fix

**Milestone:** v1.1 — Feature Leakage Audit & Fix
**Research date:** 2026-04-12

## Summary

One new dependency is justified. Everything else needed is already in the stack.

## Additions

### shap >= 0.45

**Purpose:** Per-feature importance analysis for LightGBM models.
`TreeExplainer` has native LightGBM support with exact (not sampled) SHAP values — de-facto standard for tree model interpretability in ML papers.

```
pip install shap>=0.45
```

**Integration:** Access raw LightGBM booster inside `CalibratedClassifierCV` via:
`model.calibrated_classifiers_[0].estimator.booster_`

## Already in Stack (no additions needed)

| Tool | Use | Location |
|------|-----|----------|
| `sklearn.inspection.permutation_importance` | Permutation importance on calibrated wrappers when direct booster access is awkward | scikit-learn >= 0.22 |
| `pandas.DataFrame.to_latex()` | Paper-ready LaTeX `tabular` for ablation tables. Use `float_format="%.3f"` | already in stack |
| `matplotlib` | Required by `shap.summary_plot()` | transitively installed via sentence-transformers |

## What NOT to Add

- LIME, captum, eli5, alibi, feature-engine, yellowbrick — wrong tool or unjustified overhead
- mlflow, wandb — experiment tracking not needed for a single audit pass
- tabulate, pylatex — `pd.to_latex()` is already correct for paper submission

## Leakage Detection Approach

The leakage is **semantic identity leakage** — username and profile text in Stage 2a embeddings encode bot identity. This is a code-audit problem, not a library problem.

Detection method:
1. SHAP on Stage 2a model — if embedding dimensions corresponding to username/profile tokens dominate, feature is leaky
2. Permutation importance: shuffle username/profile embedding → measure AUC drop
3. Compare cross-val AUC on S1 with vs. without username/profile in embedding input — near-perfect AUC with those features present is definitive

## Key Files

- `features_stage2.py:50-52` — username and profile appended to embedding texts (suspect)
- `botdetector_pipeline.py:539` — AMR also uses `text_field="profile"` (compounds the issue)
