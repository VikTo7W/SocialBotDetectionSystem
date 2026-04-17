---
status: testing
phase: 08-behavioral-tweet-parser-and-stage-1-adapter
source:
  - 08-01-SUMMARY.md
  - 08-02-SUMMARY.md
started: 2026-04-17T00:00:00Z
updated: 2026-04-17T00:35:00Z
---

## Current Test

number: 1
name: Revised Transfer Adapter
expected: |
  The Phase 8 transfer adapter should be reworked under the revised scope so that
  Twitter-authored behavior, topical breadth, and systematically missing TwiBot
  fields are handled in a way that improves zero-shot transfer rather than
  collapsing to near-all-human predictions.
awaiting: implementation

## Tests

### 1. Behavioral Transfer Result
expected: Running TwiBot-20 inference on test.json with the Phase 8 transfer adapter should produce a meaningful bot-detection result rather than collapsing to almost-all-human predictions.
result: issue
reported: "The results a really bad, the mapping needs to change i think so that tweets which are not RT or MT should map to the comment1of the botsim features and Mt should be comment2 as the RT are retweets that are not modified and probably just contain the message of a different account without any contribution from the account retweeting. Also the subreddit list should map to the domain field of the twibot acount json instead of the usernames. For the rest of the features which are set as 0 or nan suggest the imputing techniques as i think they also skew the predictions"
severity: major

### 2. Revised Stage 1 Mapping
expected: The Stage 1 adapter should use a documented Twitter-to-BotSim mapping justified by measured TwiBot behavior, including review of whether authored tweets should feed comment-like counts and whether subreddit breadth should map from domain.
result: reopened

### 3. Missingness Handling
expected: Systematically absent TwiBot fields that are not semantically zero should be handled with a dimensionality-preserving strategy that avoids misleading hard-zero defaults during zero-shot transfer.
result: reopened

## Summary

total: 3
passed: 0
issues: 1
pending: 0
reopened: 2
skipped: 0
blocked: 0

## Gaps

- truth: "Running TwiBot-20 inference on test.json with the Phase 8 transfer adapter should produce a meaningful bot-detection result rather than collapsing to almost-all-human predictions."
  status: failed
  reason: "User reported severe under-calling of bots and proposed revising the Stage 1 mapping plus introducing better treatment for fields that currently become 0 or NaN."
  severity: major
  test: 1
  root_cause: "Cross-domain collapse is driven by a combination of (1) Stage 1 semantic mismatch in the Twitter adapter, (2) Stage 2 feature collapse because TwiBot tweets load with ts=None so multiple temporal features become constant zeros, and (3) Reddit-trained meta and routing thresholds that keep Stage 3 almost unused on TwiBot even though Twitter graph data exists."
  artifacts:
    - path: "evaluate_twibot20.py"
      issue: "Current adapter semantics likely mismatch authored Twitter behavior and topical breadth."
    - path: "features_stage2.py"
      issue: "Timestamp-derived features collapse to zeros when TwiBot timestamps are missing."
    - path: "twibot20_io.py"
      issue: "Tweets are loaded with ts=None and domain is available but not yet used in the revised adapter."
    - path: "results_twibot20.json"
      issue: "Saved inference output shows only 1 predicted bot out of 1183 accounts."
    - path: "metrics_twibot20.json"
      issue: "Saved metrics show F1=0.0 and AUC=0.4674."
  missing:
    - "Re-specify the Stage 1 mapping under the revised Phase 8 scope."
    - "Implement missingness-aware handling for systematically absent TwiBot fields without changing feature dimensionality."
    - "Re-run TwiBot evaluation and compare against the collapsed baseline."
  debug_session: "local diagnosis from saved TwiBot outputs and code inspection on 2026-04-17"
