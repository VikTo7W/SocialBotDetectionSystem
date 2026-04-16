# Phase 10 Verification

**Phase:** 10 - Evaluation and Baseline Comparison  
**Status:** planned  
**Last updated:** 2026-04-16

## Planned checks

1. `python -m pytest tests/test_evaluate.py -q`
   - goal: prove the Phase 10 comparison and reporting contract
2. `python main.py`
   - goal: run the real BotSim S3 AMR-vs-LSTM comparison path and emit its artifact(s)

## What execution must prove

1. The workstream can compare AMR and LSTM on the real BotSim S3 cascade path.
2. The comparison includes both overall metrics and routing behavior.
3. The codebase can emit a compact comparison artifact and reusable tables.
4. The final recommendation can honestly keep AMR as the baseline if LSTM is only different, not clearly better.

## Requirement targets

- `LSTM-07` targeted
  - the workstream can compare the LSTM Stage 2b variant against the AMR baseline on meaningful metrics or routing behavior
- `LSTM-08` targeted
  - workstream artifacts record whether LSTM is better, worse, or merely different, and on what evidence

## Exit criteria

Phase 10 is complete when the repo has real S3 AMR-vs-LSTM evidence, compact reusable comparison outputs, and an explicit evidence-backed recommendation.
