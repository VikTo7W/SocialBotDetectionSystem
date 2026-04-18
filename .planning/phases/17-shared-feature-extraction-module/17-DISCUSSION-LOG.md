# Phase 17: Shared Feature Extraction Module - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-18
**Phase:** 17-shared-feature-extraction-module
**Areas discussed:** Module layout, Extractor interface, LSTM removal scope, Naming & file structure

---

## Module Layout

| Option | Description | Selected |
|--------|-------------|----------|
| features/ package | features/__init__.py, features/stage1.py, features/stage2.py, features/stage3.py | ✓ |
| Single features.py flat file | All extractors in one file at project root | |
| Keep flat per-stage files | features_stage1.py etc. at project root, merged | |

**User's choice:** features/ package

---

| Option | Description | Selected |
|--------|-------------|----------|
| Move to features/stage3.py | All extraction logic in features/, pipeline imports from there | ✓ |
| Leave in botdetector_pipeline.py | Stage 3 stays in pipeline file | |

**User's choice:** Move build_graph_features_nodeidx to features/stage3.py

---

## Extractor Interface

| Option | Description | Selected |
|--------|-------------|----------|
| Single class per stage, dataset arg | Stage1Extractor(dataset='botsim') — one class, branches internally | ✓ |
| Base class + subclasses | BotSimStage1Extractor and TwibotStage1Extractor | |
| Factory function | make_stage1_extractor(dataset='botsim') | |

**User's choice:** Single class per stage, dataset arg

---

| Option | Description | Selected |
|--------|-------------|----------|
| extract(df) → np.ndarray | Clean, consistent across all stages | ✓ |
| fit_transform(df) / transform(df) | sklearn-style | |
| You decide | Claude picks approach | |

**User's choice:** extract(df) returns np.ndarray

---

## LSTM Removal Scope

| Option | Description | Selected |
|--------|-------------|----------|
| Full removal | Delete _Stage2LSTMNet, Stage2LSTMRefiner, build_lstm_sequences, normalize_stage2b_variant, stage2b_variant/stage2b_lstm fields | ✓ |
| Classes only | Delete LSTM classes, keep variant infrastructure as dead stubs | |

**User's choice:** Full removal

---

## Naming & File Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Keep separate, move to io/ package | io/botsim24.py and io/twibot20.py | |
| Keep at root, unchanged | botsim24_io.py and twibot20_io.py unchanged | |
| Merge into one data_io.py | Single file with load_dataset() dispatch | ✓ |

**User's choice:** Merge into data_io.py

---

| Option | Description | Selected |
|--------|-------------|----------|
| load_dataset(dataset, ...) top-level function | load_dataset('botsim', ...) dispatches to right loader | ✓ |
| DataLoader class with dataset param | DataLoader(dataset='botsim').load() | |
| You decide | Claude picks what's cleanest | |

**User's choice:** load_dataset(dataset, ...) top-level function

---

## Claude's Discretion

- Internal branching style within extractor classes
- Whether features/__init__.py re-exports extractor classes
- Exact signature for Stage 3 extractor (edges_df shape, num_nodes_total default handling)

## Deferred Ideas

None.
