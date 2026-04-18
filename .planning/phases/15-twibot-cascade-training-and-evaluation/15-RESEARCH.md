# Phase 15 Research

## Summary

Existing repo code and milestone research are sufficient to plan Phase 15 without
external research. The main planning work is to connect the newly completed
Twitter-native feature modules to the already reusable cascade training and
evaluation infrastructure.

This forced re-research pass resolved three important stale assumptions in the
older v1.4 research pack:

1. Earlier milestone research described TwiBot split names as
   `train.json` / `val.json` / `test.json`, but this checkout and its
   `README.md` use `train.json` / `dev.json` / `test.json`.
2. Older stack notes still suggested reusing the Reddit-native
   `features_stage2.py` sentinel path for native training, but Phase 14
   deliberately delivered a standalone `features_stage2_twitter.py` contract.
3. Older architecture notes bundled Reddit recalibration cleanup into the same
   implementation stream. For the current roadmap, that remains Phase 16 work;
   Phase 15 should stay focused on native training/evaluation only.

Phase 15 should therefore treat `dev.json` as the calibration/development split,
consume the Phase 14 native extractors directly, and leave
`evaluate_twibot20.py` untouched for now.

## Reusable Building Blocks Confirmed by Code Inspection

- `botdetector_pipeline.train_system()` already encapsulates:
  - Stage 1 / Stage 2a / Stage 2b / Stage 3 fitting
  - OOF meta12 prediction generation on S2
  - meta12 and meta123 training
- `botdetector_pipeline.predict_system()` already produces the exact evaluation DataFrame shape consumed by `evaluate.evaluate_s3()`
- `calibrate.calibrate_thresholds()` already performs Optuna-based threshold tuning against a held-out set
- `evaluate.evaluate_s3()` already computes the overall, per-stage, and routing metrics required by TRN-02
- `twibot20_io.load_accounts()` and `twibot20_io.build_edges()` already load TwiBot-native accounts and edges for every split file
- Phase 14 delivered verified native extractor modules:
  - `features_stage1_twitter.py`
  - `features_stage2_twitter.py`
  - `features_stage3_twitter.py`

## Code-Verified Findings That Affect Planning

### Extractor injection remains the key integration tension

`botdetector_pipeline.py` still imports `extract_stage1_matrix` and
`extract_stage2_features` at module scope from the Reddit-native modules.
That means native TwiBot training/evaluation must either:

1. temporarily override those module-level names in a scoped way, or
2. refactor pipeline signatures to accept extractor callables

The repo already accepts scoped monkey-patching as a local integration pattern:

- `evaluate_twibot20.py` overrides `bp.extract_stage1_matrix` in a `try/finally`
- `api.py` patches both Stage 1 and Stage 2 module-level extractor references

For Phase 15 planning, the least invasive path is a scoped native extractor override
inside the new TwiBot-specific entry points.

This refresh also reconfirms that Phase 15 does **not** need a broader
`botdetector_pipeline.py` refactor first. A scoped override is enough to build
and verify the native path without destabilizing the Reddit-trained system.

### Split filtering pattern already exists locally

`main.py` contains a compact `filter_edges_for_split()` helper that restricts edges
to accounts present in the active split. This should be reused as the pattern for
TwiBot S1/S2/dev/test graph handling, but copied into the new TwiBot entry point
instead of importing from `main.py`.

### Native Stage 3 does not need a new learning algorithm

`features_stage3_twitter.py` is a documented wrapper over the existing graph builder.
No Phase 15 plan should invent a new Stage 3 training path; the current structural
model and graph feature builder are already platform-agnostic.

### The older v1.4 architecture doc is partially stale for this phase

`.planning/research/ARCHITECTURE.md` still contains useful reusable-pipeline
insight, but several specific recommendations are now outdated relative to the
live repo and roadmap:

- it refers to `val.json` rather than `dev.json`
- it assumes Stage 15 may still need to settle native Stage 2 feature semantics,
  which Phase 14 already locked down
- it sketches Reddit recalibration removal alongside native training, which the
  current roadmap assigns to Phase 16

The Phase 15 plan set in this directory is the corrected authoritative version.

### Separate artifact naming must be enforced in code and tests

The repo root already contains:

- `trained_system.joblib`
- `trained_system_v11.joblib`
- `trained_system_v12.joblib`
- `trained_system_stage2b_amr.joblib`
- `trained_system_stage2b_lstm.joblib`

Phase 15 must choose a distinct TwiBot-native artifact name and test that it does
not overwrite the Reddit-trained artifacts.

## Recommended Phase 15 Shape

### Plan 15-01: native training entry point

Create a dedicated TwiBot training script that:

- loads `train.json`, `dev.json`, and `test.json`
- splits `train.json` into S1/S2 with label stratification and fixed seed
- filters edges per split
- injects the Phase 14 native extractors in a scoped manner
- calls `train_system()`
- calibrates thresholds on `dev.json`
- saves a separate TwiBot-native artifact

This plan should cover TRN-01 and TRN-03.

### Plan 15-02: native evaluation entry point and artifacts

Create a dedicated native evaluation script that:

- loads the TwiBot-native joblib artifact
- runs `predict_system()` with native extractors on `test.json`
- computes `evaluate_s3()` metrics
- writes stable JSON outputs for Phase 16 comparison work
- locks the behavior down with focused tests

This plan should cover TRN-02 and reinforce TRN-03.

No additional execution plans are needed from this refresh. The existing 2-plan
split still cleanly matches the current requirement boundary.

## Risks to Plan Around

- Heavyweight end-to-end retraining may be expensive in unit tests, so tests should focus on wiring, split contracts, patch restoration, and artifact routing with stubs/fakes where possible
- `dev.json` may be missing in some developer environments even though it exists in this checkout; entry points should fail clearly rather than silently falling back to test data
- Native evaluation must not accidentally route through the older zero-shot transfer adapter in `evaluate_twibot20.py`
- If extractor overrides are not restored in `finally`, later imports in the same process could see the wrong extractor functions

## Verification Guidance

Phase 15 plans should include:

- `py_compile` for the new entry points and tests
- focused pytest around split handling, artifact separation, and native evaluation wiring
- at least one optional real-data smoke command gated on local availability of `train.json`, `dev.json`, and `test.json`

## Conclusion

Phase 15 does not require new ML components. It requires a careful integration layer
that binds the Phase 14 native features to the existing cascade training, calibration,
and evaluation stack while keeping artifact boundaries and split discipline explicit.

The forced refresh did not change the Phase 15 plan count or wave structure. It
did tighten the planning record so execution follows the current repo reality
(`dev.json`, native feature modules, Phase 16 cleanup boundary) instead of the
older exploratory v1.4 notes.

---

*Phase 15 research refreshed from local code inspection, README reality checks, and Phase 14 outputs.*
