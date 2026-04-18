# Phase 15: TwiBot Cascade Training and Evaluation - Context

**Gathered:** 2026-04-18
**Status:** Ready for planning
**Source:** v1.4 milestone scaffold + Phase 14 completion + live repo inspection

<domain>
## Phase Boundary

Phase 15 turns the Phase 14 Twitter-native feature modules into a trainable and
evaluable TwiBot-native cascade. This phase is responsible for:

- training a separate `TrainedSystem` on TwiBot data
- calibrating thresholds without touching the Reddit-trained artifact
- evaluating the TwiBot-trained system on the TwiBot test split
- persisting native metrics and model artifacts with stable names

This phase does not build paper-comparison tables or remove the old Reddit
recalibration path. Those remain Phase 16 work.

</domain>

<decisions>
## Implementation Decisions

### Locked Decisions

- The TwiBot-trained system must be stored separately from `trained_system_v12.joblib`
- Phase 15 must use the Phase 14 native extractor modules rather than the older Reddit-transfer adapter path
- The repo-local TwiBot split names are `train.json`, `dev.json`, and `test.json`; planning must not assume `val.json`
- Split discipline remains leakage-safe:
  - stage models train on an S1 subset of `train.json`
  - meta-learners train with OOF discipline on an S2 subset of `train.json`
  - threshold calibration uses `dev.json`
  - final evaluation uses `test.json`
- Existing reusable pipeline pieces in `botdetector_pipeline.py`, `calibrate.py`, and `evaluate.py` should be preferred over invasive rewrites
- The Reddit-trained zero-shot flow in `evaluate_twibot20.py` remains untouched during this phase

### the agent's Discretion

- Exact file/module layout for the TwiBot-native training/evaluation entry points
- Whether extractor injection is best handled by a scoped monkey-patch or a narrowly-scoped pipeline signature extension, as long as the Reddit path remains stable
- Exact artifact directory and JSON payload names for the native training/evaluation outputs, as long as they are explicit and reproducible
- Whether focused tests are pure unit tests, lightweight integration tests, or a mix, so long as they do not require a full expensive retrain to validate the contract

</decisions>

<canonical_refs>
## Canonical References

**Downstream agents MUST read these before planning or implementing.**

### Milestone and scope
- `.planning/PROJECT.md` - v1.4 milestone goal, constraints, and artifact-separation rules
- `.planning/ROADMAP.md` - Phase 15 goal, dependencies, and success criteria
- `.planning/REQUIREMENTS.md` - TRN-01, TRN-02, TRN-03 requirements
- `.planning/STATE.md` - current milestone state and deferred concerns

### Upstream phase outputs
- `.planning/phases/14-twitter-native-feature-pipeline/14-01-SUMMARY.md` - native Stage 1 contract
- `.planning/phases/14-twitter-native-feature-pipeline/14-02-SUMMARY.md` - native Stage 2 contract
- `.planning/phases/14-twitter-native-feature-pipeline/14-03-SUMMARY.md` - native Stage 3 contract
- `features_stage1_twitter.py` - native Stage 1 implementation
- `features_stage2_twitter.py` - native Stage 2 implementation
- `features_stage3_twitter.py` - native Stage 3 implementation

### Reusable training/evaluation machinery
- `botdetector_pipeline.py` - `train_system()`, `predict_system()`, `TrainedSystem`, routing, OOF stacking
- `calibrate.py` - threshold calibration flow and evidence artifact pattern
- `evaluate.py` - metric computation and artifact-writing patterns
- `twibot20_io.py` - TwiBot account loader and edge builder
- `main.py` - local split/filter/training orchestration pattern to mirror selectively
- `evaluate_twibot20.py` - accepted try/finally extractor override pattern and stable JSON artifact writing style

### Data and environment reality
- `README.md` - repo-visible TwiBot file names and reproduction assumptions (`train.json`, `dev.json`, `test.json`)
- `train.json` - training split expected at repo root
- `dev.json` - development/calibration split expected at repo root
- `test.json` - held-out evaluation split expected at repo root

</canonical_refs>

<specifics>
## Specific Ideas

- Add a dedicated `train_twibot20.py` entry point rather than overloading `main.py`
- Add a dedicated `evaluate_twibot20_native.py` entry point rather than branching inside the zero-shot script
- Reuse `train_system()`, `predict_system()`, `calibrate_thresholds()`, and `evaluate_s3()` with native extractors injected in a scoped manner
- Keep native artifact naming explicit, e.g. a TwiBot-trained joblib plus a native metrics JSON
- Add tests around split handling, artifact separation, and native evaluation plumbing so Phase 16 can depend on stable outputs

</specifics>

<deferred>
## Deferred Ideas

- Paper comparison tables and interpretation text - deferred to Phase 16
- Removal of the online novelty recalibration path from the Reddit zero-shot script - deferred to Phase 16
- Multi-seed stability, alternate calibration schemes, and true AMR graph parsing - still deferred beyond this phase unless explicitly promoted

</deferred>

---

*Phase: 15-twibot-cascade-training-and-evaluation*
*Context gathered: 2026-04-18 via local repo synthesis*
