# Phase 5: Leakage Fix and Baseline Retrain - Context

**Gathered:** 2026-04-13
**Status:** Ready for planning

<domain>
## Phase Boundary

Remove two identity leakage paths from Stage 2a feature extraction, drop the `character_setting` column at load time in `build_account_table`, add three table-stakes behavioral features (CoV of inter-post intervals, message character length stats, posting hour entropy), then retrain and recalibrate the full cascade. The output is a clean v1.1 baseline (`trained_system_v11.joblib`) with a realistic Stage 2a AUC (70–85%) that all ablation work in Phases 6–7 builds on.

Ablation infrastructure, cross-message similarity features, and paper table generation are out of scope for this phase.

</domain>

<decisions>
## Implementation Decisions

### Leakage fix approach
- Fix both leakage paths + drop `character_setting` + add FEAT-01/02/03 in a single commit, then do one retrain run
- Do not verify each fix in isolation — atomic fix per the research note in STATE.md (residual leakage risk if fixed separately)

### AMR anchor text (replacing text_field="profile")
- Use the **most recent message** in the account's post/comment history as the anchor text (last item in the messages list, consistent with the `messages[-max_msgs:]` slicing in `extract_stage2_features`)
- Truncate to `max_chars` characters (same limit as `extract_stage2_features`, currently 500)
- For accounts with **no messages**: return a zero embedding vector (consistent with how `extract_stage2_features` handles empty accounts)
- `text_field="profile"` call site in `botdetector_pipeline.py` line 539 must be removed entirely — no fallback to any identity field

### New behavioral features (FEAT-01, FEAT-02, FEAT-03)
- **Placement:** Append after the existing temporal features `[rate, delta_mean, delta_std]` — do not replace them
- Final temporal block: `[rate, delta_mean, delta_std, cv_intervals, char_len_mean, char_len_std, hour_entropy]`
- **FEAT-01 (CoV of inter-post intervals):** `cv = delta_std / max(delta_mean, 1e-6)` — default to `0.0` for accounts with 0 or 1 messages (undefined intervals)
- **FEAT-02 (character length stats):** mean and std of message character lengths across all messages — default both to `0.0` for accounts with no messages
- **FEAT-03 (posting hour entropy):** `entropy = -sum(p * log2(p))` over the 24-hour distribution — default to `0.0` for accounts with 0 or 1 messages (entropy trivially 0 for one message)
- Entropy uses timestamps already collected in `ts` list; extract hour via `datetime.utcfromtimestamp(ts_val).hour`

### character_setting column handling
- Drop `character_setting` at load time inside `build_account_table` in `botsim24_io.py` — not retained in the returned DataFrame at all
- Add an assertion after `build_account_table` returns to verify `"character_setting" not in df.columns`

### Post-retrain validation
- Minimum validation: Stage 2a AUC < 90% (from S3 evaluation) + assertion that `character_setting` is absent from the DataFrame produced by `build_account_table`
- Full cascade (meta12, meta123, recalibrated thresholds) must train end-to-end and serialize to `trained_system_v11.joblib` without error

### Artifact preservation and versioning
- The **existing `trained_system.joblib` (v1.0 artifact) must not be overwritten** — leave it in place
- The v1.1 retrain saves to `trained_system_v11.joblib` (new file)
- Before any code changes: run evaluation on the existing `trained_system.joblib` and save results to `results_v10.json` — this captures exact v1.0 S3 metrics (F1, AUC, precision, recall) for Phase 7's leakage audit table
- `results_v10.json` format: `{"auc": float, "f1": float, "precision": float, "recall": float, "stage": "S3"}`

### Claude's Discretion
- Exact implementation of `datetime.utcfromtimestamp` import and hour extraction
- Whether to add `results_v10.json` to `.gitignore` or commit it
- Internal structure of the evaluation script/function used to capture v1.0 metrics

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Leakage locations (primary change targets)
- `features_stage2.py` — Lines 29–35: the `texts.append("USERNAME: " + username)` and `texts.append("PROFILE: " + profile)` calls that constitute Leakage Path 1. These must be removed entirely.
- `botdetector_pipeline.py` — Line 539: `extract_amr_embeddings_for_accounts(S1, cfg, embedder, text_field="profile")` — Leakage Path 2. `text_field="profile"` must be removed; anchor must become the most recent message text.
- `botdetector_pipeline.py` — Line 567: second `extract_amr_embeddings_for_accounts` call (for S2 during meta-training) — same `text_field="profile"` fix required.
- `botsim24_io.py` — Line 183: `"character_setting": u.get("character_setting", None)` — must be dropped from `build_account_table` return value.

### Feature extraction (modification target)
- `features_stage2.py` — `extract_stage2_features()` function: add FEAT-01, FEAT-02, FEAT-03 to the temporal feature block
- `botdetector_pipeline.py` — `extract_amr_embeddings_for_accounts()` lines 131–149: update function signature and body to use most-recent-message anchor instead of `text_field` parameter

### Data loading
- `botsim24_io.py` — `build_account_table()` function: drop `character_setting` column

### Cascade retrain and serialization
- `botdetector_pipeline.py` — `train_system()` lines 505–614: the full training orchestration that must run cleanly after all fixes
- `main.py` — orchestration entry point; v1.0 metrics capture and `trained_system_v11.joblib` save happen here

### Requirements
- `.planning/REQUIREMENTS.md` — LEAK-01 through LEAK-05, FEAT-01 through FEAT-03 definitions

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `extract_stage2_features()` temporal block (`features_stage2.py`): already collects `ts` list and computes `rate`, `delta_mean`, `delta_std` — FEAT-01 and FEAT-03 extend this same `ts` list
- `simple_linguistic_features()` (`features_stage2.py`): already iterates messages to extract per-message features — FEAT-02 (char length stats) can reuse the same message iteration loop
- `MahalanobisNovelty`, `StageThresholds`, `TrainedSystem` — no changes needed to these core abstractions

### Established Patterns
- Zero-vector fallback: `emb_pool = np.zeros(probe_dim, dtype=np.float32)` for accounts with no messages — use same pattern for new feature fallbacks (default 0.0)
- `eps=1e-6` denominator guard already used in `features_stage1.py` — use same pattern for CoV denominator: `cv = delta_std / max(delta_mean, 1e-6)`
- Feature vector built by `np.concatenate([emb_pool, ling_pool, temporal], axis=0)` — extend `temporal` array in-place, keep the concatenation structure

### Integration Points
- `extract_amr_embeddings_for_accounts()` is called in two places in `botdetector_pipeline.py` (lines 539 and 567) — both calls need the `text_field` parameter removed and anchor logic updated
- `build_account_table()` is called in `main.py` — the assertion `assert "character_setting" not in df.columns` should be added in `main.py` after the call, not inside `botsim24_io.py`
- `trained_system.joblib` is loaded in `api.py` at module level — the API is unaffected by this phase (we are not touching `trained_system.joblib`)

</code_context>

<specifics>
## Specific Ideas

- v1.0 metrics JSON file: `results_v10.json` with keys `{"auc", "f1", "precision", "recall", "stage"}` — save before any code changes
- v1.1 artifact: `trained_system_v11.joblib` — saved at end of `main.py` run after full retrain
- Posting hour entropy computation: `from datetime import datetime, timezone` then `datetime.utcfromtimestamp(ts_val).hour` to extract the hour bucket

</specifics>

<deferred>
## Deferred Ideas

- None — discussion stayed within phase scope

</deferred>

---

*Phase: 05-leakage-fix-and-baseline-retrain*
*Context gathered: 2026-04-13*
