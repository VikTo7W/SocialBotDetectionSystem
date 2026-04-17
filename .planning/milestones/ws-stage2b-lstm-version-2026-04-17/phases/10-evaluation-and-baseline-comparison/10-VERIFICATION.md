# Phase 10 Verification

**Phase:** 10 - Evaluation and Baseline Comparison  
**Status:** complete  
**Last updated:** 2026-04-16

## Checks run

1. `python -m pytest tests/test_evaluate.py -q`
   - result: `17 passed`
2. `python main.py`
   - result: completed and wrote [10-real-run-variant-comparison.json](c:/Users/dzeni/PycharmProjects/SocialBotDetectionSystem/.planning/workstreams/stage2b-lstm-version/phases/10-evaluation-and-baseline-comparison/10-real-run-variant-comparison.json)
3. `python ablation_tables.py`
   - result: completed and exported:
     - `tables/table5_stage2b_variant_comparison.tex`
     - `tables/table6_stage2b_routing_comparison.tex`

## Real comparison outcome

- **Recommended variant:** `lstm`
- **Recommendation status:** `challenger_better`
- **Primary rationale:** LSTM beat AMR on final F1 by `0.0165`, exceeding the configured recommendation margin of `0.01`

### Overall metrics

| Variant | F1 | AUC | Precision | Recall |
|---------|----|-----|-----------|--------|
| `amr` | `0.9767` | `0.9992` | `0.9735` | `0.9800` |
| `lstm` | `0.9933` | `0.9997` | `1.0000` | `0.9867` |

### Routing behavior

| Variant | Stage 1 Exit % | Stage 2 Exit % | Stage 3 Exit % | Stage 2b Route % |
|---------|----------------|----------------|----------------|------------------|
| `amr` | `46.68` | `42.11` | `11.21` | `50.11` |
| `lstm` | `7.09` | `71.62` | `21.28` | `91.30` |

## Interpretation

1. Requirement `LSTM-07` is satisfied because the repo now performs a real BotSim S3 comparison between AMR and LSTM and records both metric and routing differences.
2. Requirement `LSTM-08` is satisfied because the milestone artifacts now state clearly that LSTM is better on this evaluation path, while also preserving the routing-cost tradeoff.
3. The result is not merely a routing shift: the LSTM variant improved the headline evaluation metrics as well.
4. The stronger LSTM result comes with heavier Stage 2b and Stage 3 usage, so future deployment decisions should consider runtime and cascade-cost implications.

## Exit criteria

Phase 10 is complete: the repo has real S3 AMR-vs-LSTM evidence, compact reusable comparison outputs, and an explicit evidence-backed recommendation.
