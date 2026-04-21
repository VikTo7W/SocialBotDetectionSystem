---
phase: 21
plan: "01"
subsystem: readme-architecture
tags: [documentation, readme, architecture]
key-files:
  modified:
    - README.md
metrics:
  tasks_completed: 4
  tasks_total: 4
---

# Plan 21-01 Summary

## Outcome

Reframed `README.md` around the maintained v1.5 modular codebase instead of the older v1.4 comparison-only story.

## Delivered

- new overview focused on the shared v1.5 cascade
- maintained architecture section covering:
  - `features/`
  - `cascade_pipeline.py`
  - `data_io.py`
  - `evaluate.py`
- technique-rationale sections for:
  - LightGBM
  - Mahalanobis novelty
  - AMR delta-logit refinement
  - logistic-regression stackers
  - Bayesian threshold calibration
- explicit note that `botdetector_pipeline.py` is now a compatibility-oriented layer rather than the main maintained pipeline surface

## Self-Check: PASSED

- [x] README opens with the v1.5 unified modular story
- [x] current maintained train/eval scripts are named
- [x] rationale for the main modeling choices is documented
- [x] removed duplicate evaluation scripts are not presented as maintained entry points
