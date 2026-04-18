# Phase 14 Patterns

## Existing Patterns to Reuse

### Standalone feature extractor modules

- `features_stage1.py`
- `features_stage2.py`

Use these as shape and testing-pattern references only. Phase 14 should mirror their
module-level single-purpose style while keeping TwiBot-native logic in separate files.

### TwiBot-specific override pattern

- `evaluate_twibot20.py`

This file already shows the project’s accepted pattern for temporarily overriding
`botdetector_pipeline.extract_stage1_matrix` in a scoped `try/finally` block.
Phase 15 can build on that exact pattern for training/evaluation entry points.

### Loader and parser contract

- `twibot20_io.py`

This is the canonical source for TwiBot field semantics in this repo. All new native
feature code should consume its normalized account and edge outputs instead of reading raw
JSON directly.

### Focused feature tests

- `tests/test_features_stage2.py`
- `tests/test_twibot20_io.py`

Use the repo’s current style of small synthetic fixtures and direct assertions on feature
values/shapes instead of high-overhead integration tests.

## Recommended New File Mapping

- `features_stage1_twitter.py` → closest analog: `features_stage1.py`
- `features_stage2_twitter.py` → closest analog: `features_stage2.py`
- `features_stage3_twitter.py` → thin wrapper around `botdetector_pipeline.build_graph_features_nodeidx()`
- `tests/test_features_stage1_twitter.py` → closest analog: focused extractor tests in `tests/test_features_stage2.py`
- `tests/test_features_stage2_twitter.py` → closest analog: `tests/test_features_stage2.py`
- `tests/test_features_stage3_twitter.py` → closest analog: graph/loader assertions in `tests/test_twibot20_io.py`

## Planning Guidance

- Keep write scopes clean by stage so Phase 15 training can depend on stable extractor modules
- Do not mix training entry-point work into Phase 14
- Prefer explicit documented feature contracts over “smart” reuse that hides platform assumptions
