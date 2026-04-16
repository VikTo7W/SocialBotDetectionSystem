# Phase 9: Zero-Shot Inference Pipeline - Context

**Gathered:** 2026-04-16
**Status:** Ready for planning

<domain>
## Phase Boundary

Deliver `evaluate_twibot20.py` — a new file that runs `trained_system_v12.joblib` on TwiBot-20 test accounts (zero-shot, no retraining). The script adapts TwiBot-20 DataFrame columns to the BotSim-24 pipeline schema, applies Stage 1 ratio clamping (TW-05), calls `predict_system()`, and surfaces results for Phase 10.

**Out of scope:** Any changes to existing pipeline files (`features_stage1.py`, `botdetector_pipeline.py`, `botsim24_io.py`, `evaluate.py`, etc.). The entire inference code change is isolated to `evaluate_twibot20.py`.

</domain>

<decisions>
## Implementation Decisions

### Script Structure
- **D-01:** `evaluate_twibot20.py` is structured as **module + `__main__`**: a `run_inference(path: str, model_path: str) -> pd.DataFrame` function that Phase 10 can import directly, plus a `if __name__ == "__main__":` block for manual execution. No subprocess needed between phases.

### Column Adapter (TwiBot-20 → pipeline schema)
- **D-02:** `statuses_count` maps to `submission_num`. This is the closest available analog (tweet count ≈ post-activity proxy). Stage 1 ratio clamping (D-04) handles the side-effects.
- **D-03:** Reddit-specific columns that have no TwiBot-20 equivalent are zero-filled:
  - `comment_num_1` = 0.0
  - `comment_num_2` = 0.0
  - `subreddit_list` = [] (empty list)
  - `username` = `screen_name` (direct mapping)
  - `account_id` = `ID` field (Twitter user ID string, e.g. `"12345"`)

### Stage 1 Ratio Clamping
- **D-04:** After calling `extract_stage1_matrix(df)`, clamp columns 6–9 (inclusive) of the resulting `X1` matrix to `[0.0, 50.0]`. This is done **inside `evaluate_twibot20.py`** — not in `features_stage1.py`. The clamp is a local `np.clip` call on the array, not a change to any shared module.
  - Column indices 6–9 are `post_c1`, `post_c2`, `post_ct`, `post_sr` (the ratio features prone to blowup when Reddit columns are zero).
  - Clamp upper bound: 50.0 (per TW-05).

### Results Output
- **D-05:** `run_inference()` returns the full results `pd.DataFrame` (same schema as `predict_system()` output: `account_id`, `p1`, `n1`, `p2`, `n2`, `amr_used`, `p12`, `stage3_used`, `p3`, `n3`, `p_final`).
- **D-06:** The `__main__` block also saves results to `results_twibot20.json` (records-oriented, for inspection and audit trail). Phase 10 imports `run_inference()` directly — it does not read the JSON.

### account_id
- **D-07:** Use `record["ID"]` (Twitter user ID string) as `account_id` in the results DataFrame. This is the canonical stable identifier. Matches what Phase 10 will use for ground-truth join.

### Temporal Features
- **D-08:** All TwiBot-20 messages have `ts: None` (no per-tweet timestamps). Temporal features (`cv_intervals`, `rate`, `delta_mean`, `delta_std`, `hour_entropy`) will naturally be zero for all accounts. No special handling needed — `extract_stage2_features` already guards `if m.get("ts") is not None`. Document this in the script's docstring.

### Claude's Discretion
- Threshold value passed to `predict_system()` — use `sys.th` (the calibrated threshold from the loaded model artifact). No override needed.
- Whether to print a brief summary after saving JSON — Claude decides (print is fine for human verification).

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Pipeline Integration
- `botdetector_pipeline.py` lines 634–710 — `predict_system()` signature, column requirements, output DataFrame schema
- `features_stage1.py` lines 1–38 — `extract_stage1_matrix()` full implementation; columns 6–9 are `post_c1`, `post_c2`, `post_ct`, `post_sr`
- `features_stage2.py` lines 27–90 — `extract_stage2_features()` — needs `messages` column; handles `ts=None` correctly already

### Phase 8 Data Layer
- `twibot20_io.py` — `load_accounts(path)`, `build_edges(accounts_df, path)`, `validate(accounts_df, edges_df)` — all available
- `.planning/workstreams/twibot-intergration/phases/08-twibot-20-data-loader/08-01-SUMMARY.md`
- `.planning/workstreams/twibot-intergration/phases/08-twibot-20-data-loader/08-02-SUMMARY.md`

### Requirements
- `.planning/workstreams/twibot-intergration/REQUIREMENTS.md` — TW-04 and TW-05 (zero-shot inference and ratio clamping)
- `.planning/workstreams/twibot-intergration/ROADMAP.md` — Phase 9 success criteria

### Existing Inference Pattern
- `main.py` lines 124–160 — shows how `joblib.load()`, `predict_system()`, and `evaluate_s3()` are composed in the BotSim-24 pipeline

</canonical_refs>

<code_context>
## Existing Code Insights

### Reusable Assets
- `botdetector_pipeline.predict_system(sys, df, edges_df, nodes_total)` — drop-in inference, just needs correct `df` schema
- `joblib.load(path)` — standard model loading pattern (see `main.py:_load_pretrained_system_if_available`)
- `twibot20_io.load_accounts`, `build_edges`, `validate` — all ready from Phase 8

### Established Patterns
- Model loading: `joblib.load("trained_system_v12.joblib")` returns a `TrainedSystem` dataclass with `.th` (calibrated thresholds)
- `predict_system` returns a DataFrame — same columns needed by `evaluate_s3()` in Phase 10
- `features_stage1.extract_stage1_matrix(df)` returns `np.ndarray` shape `(n, 10)` — columns 6–9 are the ratio features
- `features_stage2.extract_stage2_features(df, sys.embedder)` — already handles empty messages and `ts=None`

### Integration Points
- `evaluate_twibot20.run_inference()` → Phase 10 imports this to get the results DataFrame
- `results_twibot20.json` → saved by `__main__` for manual inspection
- `twibot20_io.validate()` should be called before inference (prints diagnostic fractions)

</code_context>

<specifics>
## Specific Ideas

- The adapter (mapping TwiBot-20 → pipeline schema) lives inline inside `evaluate_twibot20.py` — no new function in `twibot20_io.py`
- Stage 1 clamping: `X1[:, 6:10] = np.clip(X1[:, 6:10], 0.0, 50.0)` immediately after `extract_stage1_matrix` call
- Script should note in output/docstring that temporal features are zero for all accounts (plain-text tweets, no timestamps)

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 09-zero-shot-inference-pipeline*
*Context gathered: 2026-04-16*
