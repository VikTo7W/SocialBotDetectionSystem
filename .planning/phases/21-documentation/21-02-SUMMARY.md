---
phase: 21
plan: "02"
subsystem: feature-stage-mapping
tags: [documentation, readme, features]
key-files:
  modified:
    - README.md
metrics:
  tasks_completed: 4
  tasks_total: 4
---

# Plan 21-02 Summary

## Outcome

Added a dataset-by-stage feature reference to `README.md` so the maintained BotSim-24 and TwiBot-20 feature surfaces are documented from the shared extractor modules.

## Delivered

- BotSim-24 Stage 1/2a/2b/3 feature mapping
- TwiBot-20 Stage 1/2a/2b/3 feature mapping
- explicit AMR-only Stage 2b contract for v1.5
- transfer-adapter note clarifying that Reddit-on-TwiBot transfer uses a compatibility adapter only for baseline evaluation, not for TwiBot-native feature definition

## Self-Check: PASSED

- [x] Stage 1, Stage 2a, Stage 2b, and Stage 3 are all documented
- [x] BotSim and TwiBot differences are explained without implying fake parity
- [x] the removed LSTM Stage 2b path is not described as maintained
- [x] the mapping is grounded in the shared extractor surface
