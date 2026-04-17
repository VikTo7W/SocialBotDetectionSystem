# Requirements — v1.2 TwiBot-20 Cross-Domain Transfer

## Active Requirements

### FEAT — Behavioral Feature Adapter

- [ ] **FEAT-01**: Behavioral tweet parser classifies each account's tweets into RT-prefixed, MT-prefixed, and regular (original) buckets, and extracts distinct @usernames from RT/MT tweets
- [ ] **FEAT-02**: Stage 1 adapter maps `submission_num` ← original tweet count, `comment_num_1` ← RT count, `comment_num_2` ← MT count, `subreddit_list` ← list of distinct @usernames from RT/MT tweets
- [ ] **FEAT-03**: Ratio cap is reviewed and tuned for Twitter tweet-count distributions (current 1000.0 may need adjustment with the new behavioral counts)

### CAL — Online Threshold Calibration

- [ ] **CAL-01**: Sliding-window threshold recalibrator updates all routing thresholds every N accounts using a running buffer of per-account novelty scores (unsupervised — labels never used during inference)
- [ ] **CAL-02**: Window size N is configurable (default suggested: 100 accounts)
- [ ] **CAL-03**: Calibrator degrades gracefully when the buffer has fewer than N accounts (cold-start: use original trained thresholds until buffer fills)

### EVAL — Evaluation and Paper Output

- [ ] **EVAL-01**: Before/after comparison reports F1, AUC, precision/recall on TwiBot-20 with (a) current demographic proxy adapter and (b) behavioral RT/MT adapter
- [ ] **EVAL-02**: Paper-ready LaTeX cross-dataset results table comparing BotSim-24 in-domain performance vs TwiBot-20 zero-shot transfer performance

## Future Requirements

- Retrain Stage 1 on a TwiBot-20 training split for domain-adapted (non-zero-shot) comparison baseline
- Stage 2a text feature adapter for TwiBot-20 (tweets have no timestamps — D-08 gap)
- True AMR graph parsing replacing the text-embedding stub (AMR-01, deferred from v1.0)

## Out of Scope

| Feature | Reason |
|---------|--------|
| Supervised threshold calibration using TwiBot-20 labels | Labels are held-out for final evaluation only |
| Retraining any model component on TwiBot-20 | Zero-shot transfer only — retraining invalidates the cross-domain claim |
| Stage 2a / Stage 3 feature adapters | Scope limited to Stage 1 behavioral mapping this milestone |
| Profile/description features | Permanently excluded — root cause of v1.1 leakage |

## Traceability

| REQ-ID | Phase | Plan |
|--------|-------|------|
| FEAT-01 | Phase 8 | — |
| FEAT-02 | Phase 8 | — |
| FEAT-03 | Phase 8 | — |
| CAL-01 | Phase 9 | — |
| CAL-02 | Phase 9 | — |
| CAL-03 | Phase 9 | — |
| EVAL-01 | Phase 10 | — |
| EVAL-02 | Phase 10 | — |
