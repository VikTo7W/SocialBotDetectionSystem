# Requirements: v1.4 Twitter-Native Supervised Baseline

**Created:** 2026-04-18
**Milestone:** v1.4 Twitter-Native Supervised Baseline
**Status:** SHIPPED WITH ACKNOWLEDGED VERIFICATION GAP

## Milestone Goal

Build a Twitter-native cascade trained on TwiBot-20 to show the cascade performs meaningfully when platform-matched, while removing the ineffective online novelty-recalibration path from the Reddit transfer system.

## Requirements

### Twitter-Native Features

- [x] **TWN-01**: Stage 1 uses only TwiBot-20-native account and activity features, with no Reddit field analog mappings, imputing, or zero-fill stand-ins
- [x] **TWN-02**: Stage 2 uses only TwiBot-20-native tweet text and timeline features, with no Reddit semantic carry-overs for unavailable fields
- [x] **TWN-03**: Stage 3 uses only TwiBot-20-native graph features derived from follower/following neighbor structure

### Training and Evaluation

- [x] **TRN-01**: A full cascade is trainable on TwiBot-20 train split with leakage-safe split discipline and separate stored artifact(s)
- [x] **TRN-02**: The trained TwiBot cascade is evaluated on TwiBot-20 test split with overall, per-stage, and routing metrics
- [x] **TRN-03**: The TwiBot-trained artifact is stored separately from the Reddit-trained `trained_system_v12.joblib` model

### Comparison and Cleanup

- [x] **CMP-01**: A paper-facing comparison artifact and table contrast Reddit-trained-on-TwiBot versus TwiBot-trained-on-TwiBot results
- [x] **CMP-02**: Online novelty recalibration is removed from the Reddit system path for v1.4 because it does not materially improve transfer performance
- [x] **CMP-03**: v1.4 docs clearly explain the separate model artifacts, reproduction flow, and remaining caveats

## Traceability

| Requirement | Phase | Status | Notes |
|-------------|-------|--------|-------|
| TWN-01 | Phase 14 | Complete | Native Stage 1 extractor delivered in `features_stage1_twitter.py` |
| TWN-02 | Phase 14 | Complete | Native Stage 2 extractor delivered in `features_stage2_twitter.py` |
| TWN-03 | Phase 14 | Complete | Native Stage 3 contract delivered in `features_stage3_twitter.py` |
| TRN-01 | Phase 15 | Complete | Full TwiBot cascade training entry point delivered in `train_twibot20.py` |
| TRN-02 | Phase 15 | Complete | TwiBot test evaluation outputs delivered in `evaluate_twibot20_native.py` |
| TRN-03 | Phase 15 | Complete | Separate persisted native model artifact contract documented in `VERSION.md` |
| CMP-01 | Phase 16 | Complete | Paper comparison outputs delivered in `ablation_tables.py` |
| CMP-02 | Phase 16 | Complete | Maintained Reddit path simplified in `evaluate_twibot20.py` |
| CMP-03 | Phase 16 | Complete | Release/update docs refreshed in `README.md` and `VERSION.md` |

## Notes

- This milestone introduces a new TwiBot-trained system. It does not relabel or retrain the Reddit-trained `trained_system_v12.joblib`.
- Multi-seed stability, alternate calibration schemes, and true AMR graph parsing remain deferred unless explicitly promoted into this milestone later.
- Product requirements are complete; the only acknowledged verification gap is targeted pytest execution in this Windows workspace because temp-dir permissions interrupt tmp-path setup/cleanup.
