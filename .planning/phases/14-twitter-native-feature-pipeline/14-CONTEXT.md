# Phase 14: Twitter-Native Feature Pipeline - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning
**Source:** v1.4 milestone scaffold + existing v1.4 research pack

<domain>
## Phase Boundary

Phase 14 is the feature-foundation phase for the TwiBot-native supervised baseline.
It does not train models. It establishes the TwiBot-native Stage 1, Stage 2, and Stage 3
feature extraction paths that later training and evaluation scripts will rely on.

This phase must produce feature extractors and tests that are independently verifiable
without requiring a trained TwiBot model artifact.

</domain>

<decisions>
## Implementation Decisions

### Locked Decisions

- TwiBot-native features only: no Reddit-to-Twitter slot mappings, no imputing, no zero-fill stand-ins for absent Reddit analogs
- The Reddit-trained `trained_system_v12.joblib` path remains untouched in this phase
- Stage 1 must use real TwiBot account/activity signals available from `twibot20_io.load_accounts()`
- Stage 2 must use real TwiBot tweet text signals; timestamp-derived features are not part of the native TwiBot Stage 2 vector
- Stage 3 must use TwiBot-native follow-graph structure from `twibot20_io.build_edges()`
- Existing reusable pipeline pieces should be preferred over invasive edits to `botdetector_pipeline.py`
- Feature extraction must be testable independently of full training

### the agent's Discretion

- Exact module names for TwiBot-native feature extractors
- Exact native feature column ordering and dimensionality, as long as it is documented and consistent between train/eval paths
- Whether the Stage 3 native path is best expressed as a wrapper/helper module or a narrowly-scoped integration utility around the existing graph feature builder

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone and scope
- `.planning/PROJECT.md` - v1.4 milestone goal, constraints, and carry-over decisions
- `.planning/ROADMAP.md` - Phase 14 goal, dependencies, and success criteria
- `.planning/REQUIREMENTS.md` - TWN-01, TWN-02, TWN-03 requirements
- `.planning/STATE.md` - current milestone position and deferred items

### TwiBot-native research
- `.planning/research/ARCHITECTURE.md` - recommended TwiBot-native architecture, integration contract, and build order
- `.planning/research/FEATURES.md` - vetted Stage 1/2/3 TwiBot-native feature landscape
- `.planning/research/STACK.md` - dependency and integration guidance for TwiBot-native training

### Existing code patterns
- `twibot20_io.py` - TwiBot account loading, edge building, tweet parsing
- `features_stage1.py` - Reddit-native Stage 1 extractor shape/pattern reference only
- `features_stage2.py` - Reddit-native Stage 2 extractor shape/pattern reference only
- `botdetector_pipeline.py` - `train_system()`, `predict_system()`, `build_graph_features_nodeidx()`, and extractor import points
- `evaluate_twibot20.py` - established monkey-patch pattern for TwiBot-specific feature path overrides

</canonical_refs>

<specifics>
## Specific Ideas

- Create a standalone TwiBot-native Stage 1 extractor rather than branching inside `features_stage1.py`
- Create a standalone TwiBot-native Stage 2 extractor that omits timestamp-only features entirely
- Reuse the existing graph degree builder via a TwiBot-native wrapper that documents or enforces the native Stage 3 output contract
- Add focused unit tests for each stage extractor so Phase 15 can build training on top of verified feature interfaces

</specifics>

<deferred>
## Deferred Ideas

- Full TwiBot training/evaluation entry points (`train_twibot20.py`, `evaluate_twibot20_native.py`) - deferred to Phase 15
- Paper comparison outputs and Reddit recalibration cleanup - deferred to Phase 16
- Multi-seed stability, alternate calibration schemes, and true AMR graph parsing - deferred beyond this phase unless explicitly promoted

</deferred>

---

*Phase: 14-twitter-native-feature-pipeline*
*Context gathered: 2026-04-18 via local milestone research synthesis*
