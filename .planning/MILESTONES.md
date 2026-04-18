# Milestones

## v1.3 Twibot System Version (Shipped: 2026-04-18)

**Phases completed:** 3 phases (11-13), 6 plans

**Key accomplishments:**

- Fixed test stub kwargs incompatibility from Phase 9 forwarding; `evaluate_twibot20.py` hardened with `output_dir` routing and `os.makedirs` — artifact writes no longer depend on temp/cache defaults
- Generated fresh live TwiBot comparison: static F1=0.0/AUC=0.5964, recalibrated F1=0.0/AUC=0.5879, verdict `no_material_change` — confirms recalibration does not materially improve zero-shot transfer
- Table 5 regenerated from live Phase 12 artifacts; `TABLE5_OUTPUT_PATH` and `TABLE5_INTERPRETATION_PATH` env-var overrides added for paper workflow flexibility
- `VERSION.md` authored at project root — names `trained_system_v12.joblib`, both eval modes, all 6 output files, live verdict, and all 3 env-var overrides (VERS-01)
- `README.md` expanded from 1 line to full release docs: numbered reproduction guide, environment assumptions, required inputs, caveats, and known limitations (VERS-02, VERS-03)
- `build_transfer_evidence_summary()` and `build_transfer_result_interpretation()` added for machine-readable and human-readable evidence artifacts

**Known deferred items at close:** 3 (see STATE.md Deferred Items)

- Fresh real-data TwiBot evidence was generated (closes v1.2 gap); stale root-level pre-Phase-12 artifacts remain in repo root
- Full pytest green-suite verification still blocked by Windows temp-dir cleanup permissions (pytest-level only — production code unaffected)
- No dedicated v1.3 milestone audit was run before close

---

## v1.2 TwiBot-20 Cross-Domain Transfer (Shipped: 2026-04-18)

**Phases completed:** 3 phases, 5 plans

**Key accomplishments:**

- Replaced the TwiBot demographic-proxy adapter with behaviorally grounded Stage 1 mappings driven by tweet types and `domain`
- Added missingness-aware timestamp handling for TwiBot transfer without changing feature dimensionality or retraining
- Implemented sliding-window novelty-threshold recalibration for TwiBot inference with configurable window size and cold-start preservation
- Added a persisted static-vs-recalibrated TwiBot comparison artifact and readable before/after metric summary
- Updated cross-dataset LaTeX table generation so the paper path reflects BotSim-24, TwiBot static, and TwiBot recalibrated results

**Known gaps:**

- No `v1.2` milestone audit was run before close
- Fresh real-data TwiBot comparison evidence is still pending
- Final pytest/runtime verification remained partially blocked by local Windows temp/process permission issues

---

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
