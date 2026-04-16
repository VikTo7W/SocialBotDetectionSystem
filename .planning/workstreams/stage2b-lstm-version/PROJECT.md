# Workstream Project: Stage 2b LSTM Variant

## What This Is

A parallel workstream for adding an LSTM-based Stage 2b variant to the existing social bot cascade. The goal is not to replace the whole architecture, but to introduce a sequence-model alternative to the current AMR delta refiner so we can compare quality, routing behavior, and implementation fit inside the existing Stage 2 pipeline.

## Current Milestone: v1.2.1 Stage 2b LSTM Variant

**Goal:** Build an LSTM-powered Stage 2b path that can train and run inside the current cascade, then compare it against the existing AMR delta-refiner baseline.

**Target features:**
- LSTM-based Stage 2b model that consumes account message sequences
- Training and inference integration for the LSTM variant without breaking the current Stage 2a or cascade contracts
- Evaluation path that compares the LSTM Stage 2b variant against the current AMR delta refiner on the existing BotSim-24 pipeline

## Core Value

The cascade must still produce a single, well-calibrated bot probability per account while letting us test whether a sequence-model Stage 2b adds useful signal beyond the current AMR-inspired refinement path.

## Constraints

- Preserve the existing leakage protections and split discipline (`S1`/`S2`/`S3`)
- Keep the current cascade structure intelligible; this workstream is an internal variant, not an uncontrolled architecture fork
- Prefer additive integration so the current AMR delta refiner remains available as a baseline
- Maintain seeded, reproducible training/evaluation behavior

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Keep this milestone workstream-local | Avoid overwriting the main project's active TwiBot-20 milestone docs | Active |
| Scope to Stage 2b variant work only | This is an architectural experiment inside the existing cascade, not a full redesign | Active |
| Treat current AMR delta refiner as baseline, not dead code | We need an apples-to-apples comparison against the existing Stage 2b behavior | Active |

---
*Created: 2026-04-16*
