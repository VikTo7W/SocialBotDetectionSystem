# Plan 10-01 Summary

**Status:** Complete  
**Executed:** 2026-04-16

## What changed

- Added reusable AMR-vs-LSTM comparison helpers in [evaluate.py](c:/Users/dzeni/PycharmProjects/SocialBotDetectionSystem/evaluate.py) so Phase 10 can compare overall quality metrics and routing behavior in one compact artifact.
- Updated [main.py](c:/Users/dzeni/PycharmProjects/SocialBotDetectionSystem/main.py) to run the real BotSim S3 comparison for both Stage 2b variants under the shared cascade flow and write [10-real-run-variant-comparison.json](c:/Users/dzeni/PycharmProjects/SocialBotDetectionSystem/.planning/workstreams/stage2b-lstm-version/phases/10-evaluation-and-baseline-comparison/10-real-run-variant-comparison.json).
- Added deterministic coverage in [tests/test_evaluate.py](c:/Users/dzeni/PycharmProjects/SocialBotDetectionSystem/tests/test_evaluate.py) for the comparison artifact structure, routing evidence, and neutral-recommendation contract.
- Allowed `train_system()` in [botdetector_pipeline.py](c:/Users/dzeni/PycharmProjects/SocialBotDetectionSystem/botdetector_pipeline.py) to reuse an already-loaded embedder so the real comparison can run from local artifacts without online model initialization.

## Execution notes

- The real comparison kept the split and evaluation flow shared across variants and changed only the Stage 2b branch.
- The final artifact shows LSTM beating AMR on the primary metric: F1 improved from `0.9767` to `0.9933`.
- Routing behavior also changed materially: LSTM routed far fewer accounts out at Stage 1 and routed more accounts through Stage 2 and Stage 3.

## Verification

- `python -m pytest tests/test_evaluate.py -q`
  - result: `17 passed`
- `python main.py`
  - result: completed and wrote the real Phase 10 comparison artifact
