# Phase 16 Research

## Summary

Phase 16 should be planned as three execution plans, not two.

The repo already contains the two evidence streams this phase needs:

- Phase 12 zero-shot Reddit-trained-on-TwiBot artifacts and Table 5 paper path
- Phase 15 TwiBot-native trained artifact and native evaluation outputs

The missing work is to replace the old static-vs-recalibrated comparison story
with the v1.4 story, remove the now-disfavored online recalibration branch from
the maintained Reddit transfer path, and then update release-facing docs so the
artifact contract matches the code.

## Repo Reality That Drives Planning

### The old paper comparison is still centered on recalibration

The current paper-output surface is still v1.3-shaped:

- `evaluate_twibot20.py` writes:
  - `results_twibot20.json`
  - `metrics_twibot20.json`
  - `metrics_twibot20_comparison.json`
  - `transfer_evidence_summary.json`
- `ablation_tables.py` Table 5 reads `metrics_twibot20_comparison.json`
- `README.md` and `VERSION.md` still describe the shipped zero-shot comparison
  as static vs recalibrated

That is correct for v1.3, but it is stale for v1.4 Phase 16 because `CMP-01`
requires a paper-facing comparison between:

1. Reddit-trained cascade on TwiBot-20
2. TwiBot-trained cascade on TwiBot-20

### The Reddit recalibration cleanup surface is narrow

The online novelty recalibration implementation lives inside
`evaluate_twibot20.py`, mainly in:

- `run_inference(..., online_calibration=True, window_size=100)`
- `evaluate_twibot20(..., online_calibration=True, ...)`
- `compare_twibot20_conditions()`
- the `__main__` block that writes the comparison/evidence artifacts

This is the smallest safe cleanup boundary. `main.py` is not part of this
recalibration path. The code in `ablation_tables.py`, `README.md`, and
`VERSION.md` depends on the outputs and naming conventions from that script, so
cleanup should be planned as:

- code-path retirement in `evaluate_twibot20.py`
- companion test updates in `tests/test_evaluate_twibot20.py`
- downstream artifact/doc updates in separate plans

### Phase 15 already supplies the native side of the comparison

Phase 15 delivered:

- `train_twibot20.py`
- `evaluate_twibot20_native.py`
- default native artifact path: `trained_system_twibot20.joblib`
- native metrics artifact: `metrics_twibot20_native.json`
- native results artifact: `results_twibot20_native.json`

That means Phase 16 does not need another training/evaluation implementation.
It needs comparison plumbing, paper-output rewiring, and contract cleanup.

## Recommended Phase 16 Plan Split

### Plan 16-01: Comparison artifact + paper table refresh

This plan should satisfy `CMP-01`.

Scope:

- build or refresh the machine-readable comparison artifact that directly
  contrasts Reddit-trained zero-shot results against TwiBot-trained native
  results
- update the Table 5 generation path so it consumes that artifact by default
- keep the old Phase 12 static-vs-recalibrated evidence as historical output,
  not the active paper-facing default

Likely touched files:

- `ablation_tables.py`
- a new comparison helper/module or a small extension to an existing script
- focused tests around the new comparison schema and table text

### Plan 16-02: Retire online novelty recalibration from the Reddit path

This plan should satisfy `CMP-02`.

Scope:

- remove or retire the `online_calibration=True` execution path from the
  maintained Reddit zero-shot evaluation flow
- simplify the CLI/output contract so the maintained path reports the static
  Reddit transfer result only
- update tests so they no longer assert recalibrated-mode behavior as a current
  system feature

Likely touched files:

- `evaluate_twibot20.py`
- `tests/test_evaluate_twibot20.py`

This plan should be careful not to break historical Phase 12 artifacts already
present in `.planning/`. Those are evidence files, not active production
contracts.

### Plan 16-03: Release/docs contract update

This plan should satisfy `CMP-03` and should depend on 16-01 and 16-02.

Scope:

- update `README.md` reproduction guidance for the v1.4 comparison story
- update `VERSION.md` to describe separate Reddit-trained and TwiBot-trained
  artifacts, active evaluation entry points, and revised caveats
- ensure docs explain that recalibration is no longer part of the maintained
  Reddit path

Likely touched files:

- `README.md`
- `VERSION.md`

## Recommended Artifact Direction

The cleanest v1.4 artifact story is:

- keep Phase 12 historical artifacts as-is for provenance
- introduce a new comparison artifact for Phase 16 that compares:
  - Reddit-trained zero-shot TwiBot metrics
  - TwiBot-trained native TwiBot metrics
- point Table 5 and its interpretation output at the new artifact by default

That avoids rewriting the meaning of old files like
`metrics_twibot20_comparison.json`, whose current schema clearly encodes
`static` vs `recalibrated`.

## Risks To Plan Around

- `ablation_tables.py` currently assumes the comparison artifact has
  `conditions.static` and `conditions.recalibrated`; changing this contract will
  need targeted test coverage
- removing recalibration from `evaluate_twibot20.py` can leave docstrings,
  output filenames, and interpretation helpers internally inconsistent if not
  cleaned up together
- v1.4 docs must clearly separate:
  - historical v1.3 zero-shot evidence
  - current v1.4 maintained artifact and comparison story

## Verification Guidance

Phase 16 plans should include:

- `python -m py_compile` for changed entry points and tests
- targeted pytest for:
  - comparison-artifact schema / table generation
  - Reddit evaluation path behavior after recalibration retirement
  - docs-adjacent helper behavior where applicable
- optional smoke commands that exercise:
  - the Reddit transfer evaluation path
  - the TwiBot-native evaluation path
  - the paper table generation path

## Conclusion

Phase 16 is best planned as:

1. comparison artifact + paper output refresh
2. Reddit recalibration retirement
3. release/docs contract update

This split maps cleanly to `CMP-01`, `CMP-02`, and `CMP-03`, keeps the code
cleanup boundary small, and preserves historical v1.3 evidence without letting
it define the maintained v1.4 story.

---

*Phase 16 research synthesized from the live repo, Phase 12/15 outputs, and current release docs.*
