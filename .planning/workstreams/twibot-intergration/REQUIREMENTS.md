# Requirements: TwiBot-20 Cross-Dataset Evaluation

**Workstream:** twibot-intergration
**Defined:** 2026-04-16
**Core Value:** The cascade must produce a single, well-calibrated bot probability per account — routing efficiently through stages while catching sophisticated bots that simple models miss.

## v1.2 Requirements

### Data Loading

- [ ] **TW-01**: User can load TwiBot-20 accounts from `test.json` into a BotSim-24-compatible DataFrame — `profile` fields mapped to metadata columns (`screen_name`, `statuses_count`, `followers_count`, `friends_count`, `created_at`), `tweet` list of plain strings used as messages, `label` field parsed inline as ground truth (str "0"/"1" → int), `node_idx` column (int32, 0-indexed) assigned by row enumeration
- [ ] **TW-02**: Edge loader builds `edges_df` from each account's `neighbor.following` / `neighbor.follower` lists — string Twitter IDs remapped to zero-indexed node_idx integers (only IDs present in the evaluation set), `"following"` → etype 0, `"follower"` → etype 1, weight = `log1p(1.0)` for all edges, accounts with `neighbor: None` produce no edges; output schema `{src: int32, dst: int32, etype: int8, weight: float32}` — drop-in compatible with `build_graph_features_nodeidx(n_types=3)`
- [ ] **TW-03**: Loader validates data integrity — asserts `edges_df["src"].max() < len(accounts_df)`, `edges_df["dst"].max() < len(accounts_df)`, required column names present; logs no-neighbor count (~9%) and no-tweet count

### Zero-Shot Inference

- [ ] **TW-04**: User can run zero-shot inference on TwiBot-20 test accounts via `evaluate_twibot20.py` using `trained_system_v12.joblib` unchanged — no retraining, full cascade (Stage 1 → 2a → 2b → 3) runs as-is
- [ ] **TW-05**: TwiBot-20 inference path clamps Stage 1 ratio features (columns 6–9 of `extract_stage1_matrix` output) to [0.0, 50.0], preventing cascade routing collapse from divide-by-zero on zero-filled Reddit-specific columns (`comment_num_1`, `comment_num_2`, `subreddit_list`)

### Paper Evaluation

- [ ] **TW-06**: Evaluation produces F1, AUC-ROC, precision, recall on TwiBot-20 test set with per-stage breakdown (p1_auc, p12_auc, p_final_auc) and routing statistics (stage3_used rate, amr_used rate); notes that timestamp-dependent features (cv_intervals, rate, delta_mean, delta_std, hour_entropy) are zero for all TwiBot-20 accounts due to plain-text tweet format
- [ ] **TW-07**: `generate_cross_dataset_table()` added to `ablation_tables.py` produces a LaTeX table comparing BotSim-24 S3 (in-distribution, Reddit) vs. TwiBot-20 test (zero-shot, Twitter) metrics side-by-side with dataset context labels

## Future Requirements

### Retraining on TwiBot-20

- **TW-F01**: Train a fresh cascade on TwiBot-20 train/dev splits and report test metrics for direct comparison
- **TW-F02**: Joint training on combined BotSim-24 + TwiBot-20 training data

### Timestamp Recovery

- **TW-F03**: Use Twitter API or alternative TwiBot-20 release that includes per-tweet timestamps to recover temporal features

## Out of Scope

| Feature | Reason |
|---------|--------|
| TwiBot-20 retraining | Zero-shot only for this milestone; retraining deferred to future |
| train.json / dev.json evaluation | test.json only for clean evaluation; training split not used for zero-shot |
| Timestamp-dependent temporal features | Tweets in this dataset are plain strings; no per-tweet `created_at` available |
| True AMR graph parsing | AMR-01 is tracked separately on main workstream |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| TW-01 | TBD | Pending |
| TW-02 | TBD | Pending |
| TW-03 | TBD | Pending |
| TW-04 | TBD | Pending |
| TW-05 | TBD | Pending |
| TW-06 | TBD | Pending |
| TW-07 | TBD | Pending |

**Coverage:**
- v1.2 requirements: 7 total
- Mapped to phases: 0 (pending roadmap)
- Unmapped: 7 ⚠

---
*Requirements defined: 2026-04-16*
*Last updated: 2026-04-16 after initial definition*
