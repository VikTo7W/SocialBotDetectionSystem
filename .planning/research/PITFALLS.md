# Pitfalls: TwiBot-20 Cross-Dataset Integration

**Project:** Social Bot Detection System — v1.2 TwiBot-20 Cross-Dataset Evaluation
**Research date:** 2026-04-16
**Confidence:** HIGH for code-verified pitfalls | MEDIUM for distribution-shift pitfalls

---

## Critical Pitfalls (will silently corrupt results if not addressed)

### P-TW-01 — Stage 1 Feature Column Mismatch
**What goes wrong:** `extract_stage1_matrix` accesses `submission_num`, `comment_num_1`, `comment_num_2`, `subreddit_list` — Reddit-specific columns with no Twitter equivalent. Silent zero-fill causes degenerate inputs.
**Consequences:** p1 values near 0.5; misleading Stage 1 contribution metrics.
**Prevention:** Map TwiBot-20 fields explicitly: `submission_num` → `statuses_count`, `comment_num_1/2` → 0, `subreddit_list` → []. Document every substitution.
**Detection:** After building DataFrame, assert all expected column names exist. Check median Stage 1 novelty — if median n1 > 5.0, inputs are degenerate.
**Phase:** Loader implementation

### P-TW-02 — Stage 3 Graph Features: edge.csv String IDs vs. Integer Node Indices
**What goes wrong:** `build_graph_features_nodeidx` uses `np.add.at(out_deg, src, 1.0)` with integer array indices. TwiBot-20 edge.csv uses string Twitter user IDs — passing strings crashes with TypeError; raw 64-bit IDs crash with index-out-of-bounds.
**Consequences:** Pipeline crash without remapping; garbage features with incorrect remapping.
**Prevention:** Build `user_id → node_idx` map from account list. Filter edges to evaluation-set accounts (both src AND dst). Remap: `"following"` → 0, `"followers"` → 1 (int8). Set `num_nodes_total = len(accounts_df)`.
**Detection:** Assert `edges_df["src"].max() < num_nodes_total` and `edges_df["etype"].dtype == np.int8` with unique values `{0, 1}` before calling `build_graph_features_nodeidx`.
**Phase:** Loader implementation

### P-TW-03 — Timestamp Format Mismatch Zeros All Temporal Features
**What goes wrong:** `botsim24_io._to_unix_seconds()` hardcodes `"%Y-%m-%d %H:%M:%S"`. Twitter `created_at` is RFC 2822: `"Mon Jan 01 00:00:00 +0000 2020"`. The `except Exception: return None` silently zeroes every timestamp → all 7 temporal features = 0 for all accounts.
**Prevention:** Write a Twitter-specific timestamp parser using `email.utils.parsedate_to_datetime`. Never reuse `_to_unix_seconds` for TwiBot-20.
**Detection:** After loading a sample, check `ts_available_fraction`. If < 0.1, the parser is failing.
**Phase:** Loader implementation

### P-TW-04 — Row-Order Label Assignment Applied to TwiBot-20
**What goes wrong:** `load_users_csv` contains `df.loc[df.index >= 1907, "label"] = 1` — BotSim-24-specific (first 1907 = humans, next 1000 = bots). TwiBot-20 stores labels by user ID in `label.csv`.
**Consequences:** All F1/AUC/precision/recall metrics computed against wrong ground truth.
**Prevention:** Write separate loader reading `label.csv` and merging on user ID. Never inherit `load_users_csv` for TwiBot-20.
**Detection:** After loading, print `label.value_counts()`. TwiBot-20 is ~74% human / 26% bot. If ratio matches BotSim-24's 65.6%/34.4%, wrong labels are being used.
**Phase:** Loader implementation

### P-TW-05 — Novelty Saturation Corrupts Cascade Routing Interpretation
**What goes wrong:** `MahalanobisNovelty` models were trained on BotSim-24 distributions. All novelty models will score TwiBot-20 accounts far above thresholds (3.0–3.5). Result: `gate_amr` and `gate_stage3` trigger for ~100% of accounts.
**Consequences:** No efficiency benefit on TwiBot-20; BotSim-24 routing statistics cannot be naively compared.
**Prevention:** Accept as expected behavior. Report `results["stage3_used"].mean()` separately. Note in paper that novelty saturation forces full-cascade evaluation on OOD inputs — valid finding demonstrating conservative fallback behavior.
**Detection:** After inference, check `results["stage3_used"].mean()`. If > 0.95, confirm as expected novelty saturation.
**Phase:** Inference pipeline and paper tables

### P-TW-09 — Unfiltered edge.csv Edges Include Non-Evaluation Nodes
**What goes wrong:** TwiBot-20 edge.csv contains edges for ALL users in the full graph. `build_graph_features_nodeidx` will crash with index-out-of-bounds for nodes outside the evaluation set.
**Prevention:** Filter edges: keep only edges where BOTH src AND dst are in the evaluation account ID set before remapping.
**Phase:** Loader implementation

---

## Moderate Pitfalls

### P-TW-06 — Stage 2a LightGBM Domain Shift
Twitter bots have different content patterns (retweets, promotional content, reply spam) vs. Reddit bots (generic news summaries). Expected Stage 2a AUC on TwiBot-20: 0.65–0.75 (vs. 0.97 on BotSim-24 S3).
**Prevention:** Report per-stage AUC (`p1_auc`, `p12_auc`, `p_final_auc`) separately. If p_final AUC substantially exceeds p12 AUC, Stage 3 structural features are providing cross-domain robustness — the paper's main claim.

### P-TW-08 — p_final Values Biased by BotSim-24 Class Prior
meta123 trained on 34.4% bot prior (BotSim-24 S2). TwiBot-20 has ~26% bots → p_final values will be systematically elevated.
**Prevention:** Use AUC-ROC as primary cross-dataset metric (threshold-independent). State in paper that BotSim-24 threshold is applied without recalibration.

### P-TW-10 — TwiBot-20 JSON Field Names Vary by Dataset Version
Different TwiBot-20 releases use `"full_text"` vs. `"text"` for tweet content.
**Prevention:** Inspect the actual `user.json` before writing loader. Use `.get()` fallback chains: `tweet.get("full_text") or tweet.get("text") or ""`.

### P-TW-13 — Per-Tweet Timestamps May Not Be Available in All TwiBot-20 Versions
Some distributions store only account-level `created_at`, not per-tweet.
**Prevention:** Verify tweet-level `created_at` exists by inspecting the first account. Zero and document explicitly if absent.

---

## Phase-Specific Warnings Summary

| Phase | Pitfall | Mitigation |
|-------|---------|------------|
| Loader | P-TW-01: Stage 1 column mismatch | Explicit field mapping; document substitutions |
| Loader | P-TW-02: Edge CSV string IDs | Remap to zero-indexed int; validate bounds |
| Loader | P-TW-03: Timestamp silent failure | Twitter-specific parser; assert ts_fraction > 0.8 |
| Loader | P-TW-04: Row-order labels | Read label.csv only; assert ~74/26 class balance |
| Loader | P-TW-09: Unfiltered edges | Filter to evaluation accounts before remapping |
| Loader | P-TW-10: Field name variance | Inspect actual file; .get() fallback chains |
| Inference | P-TW-05: Novelty saturation | Expect ~100% Stage 3 routing; document as expected |
| Inference | P-TW-06: Stage 2a domain shift | Report per-stage AUC; interpret Stage 3 as robustness |
| Evaluation | P-TW-08: Calibration prior shift | Primary metric = AUC-ROC; note threshold invalidity |
| Paper tables | P-TW-11: Unlabeled context | "Dataset" column; label in-distribution vs. zero-shot rows |

---

## Source Confidence

**HIGH (code-verified):**
- `extract_stage1_matrix` — confirmed hardcoded column names (`submission_num`, `comment_num_1`, `comment_num_2`, `subreddit_list`)
- `build_graph_features_nodeidx` — confirmed `np.add.at` integer index, `int8` etype, `num_nodes_total` pre-allocation
- `botsim24_io._to_unix_seconds` — confirmed hardcoded `DATETIME_FMT = "%Y-%m-%d %H:%M:%S"` + silent `except Exception: return None`
- `load_users_csv` — confirmed row-order label logic `df.loc[df.index >= 1907, "label"] = 1`
- BotSim-24 class balance: 1000 bots / 2907 accounts = 34.4%

**MEDIUM (established dataset documentation):**
- TwiBot-20 (Feng et al., 2021): edge.csv fields `source_id, relation, target_id`; label.csv by user ID; ~74%/26% class balance
- Twitter API `created_at`: RFC 2822-like format incompatible with BotSim-24's `DATETIME_FMT`
