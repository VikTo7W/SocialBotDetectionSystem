# Milestones

## v1.1 Feature Leakage Audit & Fix (Shipped: 2026-04-16)

**Phases completed:** 3 phases, 6 plans, 8 tasks

**Key accomplishments:**

- Removed identity leakage (username/profile embeddings, profile AMR anchor, character_setting) from Stage 2a; confirmed AUC 0.97-0.98 is legitimate BotSim-24 content-based signal (not residual leakage)
- Added 3 behavioral features (cv_intervals, char_len_mean/std, hour_entropy); retrained full cascade to trained_system_v11.joblib (395-dim), 36 tests passing
- Added 2 cross-message similarity features (cross_msg_sim_mean, near_dup_frac) at indices 395-396; retrained to trained_system_v12.joblib (397-dim)
- ablation_tables.py implemented with 4 paper-table builders (leakage audit, stage contribution, routing efficiency, Stage 1 feature group ablation) and LaTeX export; 6 unit tests pass

---

## v1.0 MVP (Shipped: 2026-04-12)

**Phases completed:** 3 phases, 5 plans, 0 tasks

**Key accomplishments:**

- (none recorded)

---
