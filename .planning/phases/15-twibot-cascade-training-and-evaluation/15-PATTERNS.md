# Phase 15 Patterns

## Existing Patterns to Reuse

### Scoped extractor override

- `evaluate_twibot20.py`
- `api.py`

These files already show the repo's accepted pattern for temporarily overriding
module-level extractor references in `botdetector_pipeline` and restoring them in
a `try/finally` block. Phase 15 should reuse that discipline for TwiBot-native
training and native evaluation entry points.

### Training orchestration and split filtering

- `main.py`

Use `main.py` as the pattern source for:

- label-stratified split construction
- local `filter_edges_for_split()` logic
- saving trained joblib artifacts after evaluation-ready training

Mirror the shape of those helpers, but keep TwiBot-native code in standalone files.

### Metric and artifact writing

- `evaluate.py`
- `evaluate_twibot20.py`
- `calibrate.py`

Use these as patterns for:

- `evaluate_s3()` result shape
- compact JSON artifact helpers
- threshold-calibration evidence output

### Phase 14 native feature contracts

- `features_stage1_twitter.py`
- `features_stage2_twitter.py`
- `features_stage3_twitter.py`

Phase 15 should consume these files directly rather than re-deriving native features.

### Focused integration tests with fakes

- `tests/test_evaluate_twibot20.py`
- `tests/test_features_stage2.py`
- `tests/test_twibot20_io.py`

Use the repo's current style of:

- synthetic JSON fixtures
- fake embedders / stub systems
- direct assertions on artifact paths and metrics payloads

Avoid expensive full retrains in normal test coverage.

## Recommended New File Mapping

- `train_twibot20.py` -> closest analog: `main.py`
- `evaluate_twibot20_native.py` -> closest analog: `evaluate_twibot20.py`
- `tests/test_train_twibot20.py` -> closest analog: focused orchestration tests in `tests/test_evaluate_twibot20.py`
- `tests/test_evaluate_twibot20_native.py` -> closest analog: `tests/test_evaluate_twibot20.py`

## Planning Guidance

- Keep the TwiBot-native path standalone; do not branch inside the Reddit zero-shot files
- Prefer explicit artifact constants and helper functions so Phase 16 can consume the outputs directly
- Tests should lock down:
  - split usage (`train.json`, `dev.json`, `test.json`)
  - separate artifact naming
  - native extractor override and restoration
  - evaluation JSON schema
