# Phase 14 Research

## Summary

Existing v1.4 research is sufficient to plan this phase without additional external research.
The codebase already contains the reusable infrastructure needed for a TwiBot-native feature
pipeline; the missing work is phase-local implementation of TwiBot-native extractors and tests.

This forced re-research pass also resolved one important internal ambiguity in the earlier
milestone research:

- `.planning/research/ARCHITECTURE.md` recommends a standalone native Stage 2 extractor that
  omits timestamp-derived features entirely
- `.planning/research/STACK.md` suggests reusing `features_stage2.py` unchanged and training on
  the existing temporal sentinel path

After re-checking `features_stage2.py` against the v1.4 milestone constraints in
`.planning/PROJECT.md`, the correct Phase 14 direction is the standalone native Stage 2 path.
The sentinel path was introduced for Reddit-to-TwiBot transfer compatibility and is not the
clean native Twitter contract for a TwiBot-trained system.

## Reusable Building Blocks

- `twibot20_io.load_accounts()` already provides:
  - `screen_name`
  - `statuses_count`
  - `followers_count`
  - `friends_count`
  - `created_at`
  - `messages`
  - `domain_list`
- `twibot20_io.parse_tweet_types()` already provides RT/MT/original counts and RT/MT username extraction
- `twibot20_io.build_edges()` already provides TwiBot-native `{src, dst, etype, weight}` graph input
- `botdetector_pipeline.build_graph_features_nodeidx()` is already graph-format agnostic
- `evaluate_twibot20.py` already demonstrates a safe try/finally monkey-patch pattern for TwiBot-specific feature overrides

## Code-Verified Findings From This Refresh

- `botdetector_pipeline.py` still imports `extract_stage1_matrix` and `extract_stage2_features`
  at module scope, so future TwiBot-native training/evaluation entry points will either need a
  scoped monkey-patch or a later pipeline refactor
- `main.py` still uses the Reddit-native extractor imports directly; that reinforces the need to
  keep TwiBot-native feature code in separate modules rather than branching inside the Reddit files
- `features_stage2.py` still includes `_MISSING_TEMPORAL_SENTINEL = -1.0` and builds a temporal
  block even when timestamps are absent; that is acceptable for the v1.3 transfer path but does
  not match the cleaner native-TwiBot feature contract for v1.4
- `twibot20_io.py` already exposes every core native field Phase 14 needs, including `created_at`,
  `messages`, `domain_list`, and graph edges via `build_edges()`

## Phase 14 Planning Implications

### Stage 1

- Must be a standalone TwiBot-native extractor
- Should not import or mutate the Reddit extractor logic
- Best fit is a new module with direct feature computation from TwiBot account and tweet-type signals

### Stage 2

- Must be a standalone TwiBot-native extractor
- Should reuse the current embedding and lightweight linguistic/similarity pattern, but not the Reddit temporal sentinel path
- Because TwiBot timestamps are systematically absent, native TwiBot Stage 2 should define a shorter honest feature vector rather than smuggling in synthetic timestamp placeholders
- The forced-research decision for this phase is explicit: do **not** reuse `features_stage2.py`
  unchanged for the native TwiBot path

### Stage 3

- The core graph aggregation logic can be reused
- A TwiBot-native wrapper/helper is still useful so the native graph feature contract is explicit and testable
- The wrapper can document or enforce dropping the unused third edge-type block if that becomes the native training contract

## Resolved Planning Decisions

1. **Stage 1 file strategy**
   Use a separate `features_stage1_twitter.py` module. Do not branch inside `features_stage1.py`.

2. **Stage 2 file strategy**
   Use a separate `features_stage2_twitter.py` module. This phase explicitly rejects the
   “reuse `features_stage2.py` unchanged” option from the older stack notes.

3. **Stage 3 file strategy**
   Keep the generic graph aggregation in `botdetector_pipeline.py`, but expose a
   TwiBot-native wrapper/helper module so the contract is explicit for Phase 15.

## Risks to Plan Around

- Accidental coupling to Reddit extractor files would make future maintenance fragile
- Phase 15 training would become ambiguous if Phase 14 does not define stable native feature shapes and module names
- Tests must avoid full training dependencies and focus on shape/behavior contracts

## Recommended Phase 14 Split

1. TwiBot-native Stage 1 extractor + tests
2. TwiBot-native Stage 2 extractor + tests
3. TwiBot-native Stage 3 graph wrapper/contract + tests

## Verification Strategy

- Compile-level verification is insufficient; each plan should include focused unit tests
- Verification should prove:
  - feature matrices are produced from TwiBot-native fields only
  - empty/no-message edge cases do not crash
  - graph feature output matches the intended native contract
  - later training code can depend on these modules without redefining feature semantics

---

*Phase 14 research synthesized from `.planning/research/ARCHITECTURE.md`, `FEATURES.md`, `STACK.md`, and direct code inspection.*
