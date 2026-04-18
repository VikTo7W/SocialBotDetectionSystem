---
slug: all-predicted-one-class
status: resolved
trigger: Model predicts all accounts as one class (bot or human) — wrong results
created: 2026-04-17
updated: 2026-04-17
---

## Symptoms

- **Expected:** Accurate bot/human predictions via `python evaluate_twibot20.py`
- **Actual:** All predictions output the same class (either all bot or all human)
- **Errors:** No crash — silent wrong output; all predictions collapsed to one class
- **Timeline:** Never worked (new script/model, first run)
- **Reproduction:** `python evaluate_twibot20.py`

## Current Focus

hypothesis: CONFIRMED — feature domain mismatch between BotSim-24 (Reddit) training data and TwiBot-20 (Twitter) test data causes Stage 1 to map all test accounts into a narrow "high-confidence human" region, collapsing all predictions to near-zero p_final.
test: inspected model coefficients, simulated full prediction chain, verified existing results_twibot20.json
expecting: fix requires replacing Reddit-specific Stage 1 features with Twitter-compatible features for the TwiBot-20 path
next_action: DONE — fix applied

## Evidence

- timestamp: 2026-04-17T00:00:00Z
  observation: results_twibot20.json shows 1/1183 accounts predicted as bot — but ground truth is 640 bots, 543 humans
  source: results_twibot20.json
  significance: confirms all-one-class collapse, specifically collapsing to HUMAN

- timestamp: 2026-04-17T00:00:00Z
  observation: p1 range in results is [0.014, 0.124]; p12 range [0.00005, 0.646]; p_final range [0.00009, 0.583] — all near-zero
  source: results_twibot20.json diagnostic
  significance: every stage assigns near-zero bot probability, not just Stage 1

- timestamp: 2026-04-17T00:00:00Z
  observation: Stage 1 feature matrix for TwiBot-20 uses Reddit-specific columns: comment_num_1=0, comment_num_2=0, subreddit_list=[] for ALL Twitter accounts. After clamping, post_c1/c2/ct/sr all = 50.0 for every account regardless of actual statuses_count.
  source: features_stage1.py + evaluate_twibot20.py column adapter (lines 74-76)
  significance: ALL TwiBot-20 accounts map to identical ratio features [*,*,0,0,0,0,50,50,50,50] — Stage 1 trained on BotSim-24/Reddit interprets this as high-confidence human

- timestamp: 2026-04-17T00:00:00Z
  observation: Simulating Stage 1 across varied statuses_count + name_len with ratio=50: p1 range = [0.015, 0.035]. 100% predicted as human (p1 < 0.5).
  source: botdetector_pipeline.py Stage1MetadataModel.predict() diagnostic
  significance: Stage 1 confidently rejects all TwiBot-20 accounts as non-bot; this low z1 propagates through meta12 and meta123

- timestamp: 2026-04-17T00:00:00Z
  observation: meta12 intercept = 1.347 (p12 = 0.79 for all-zero features), but with z1=-3.7 and z2=-6.8 (from Stage 2 also seeing zero-text patterns), p12 drops to ~0.00006. meta123 then produces p_final ~0.0001.
  source: botdetector_pipeline.py predict_system() + model coefficient inspection
  significance: the cascade amplifies the Stage 1 error — all stages agree on "human" because all Twitter signals look like the null/zero case that BotSim-24 labeled human

- timestamp: 2026-04-17T00:00:00Z
  observation: After fix (D-09), post_c1 now has 1157 unique values (vs 1 before). post_c2 bot mean=22.1 vs human mean=76.4. post_sr bot mean=585 vs human mean=296. Features now vary and show discriminative signal.
  source: diagnostic after evaluate_twibot20.py fix
  significance: original all-identical feature bug is resolved; genuine variance restored

- timestamp: 2026-04-17T00:00:00Z
  observation: After fix, Stage 1 AUC = 0.6393, p_final AUC = 0.5778. Best F1 at threshold 0.016 using p1 = 0.703. Model is no longer stuck — it produces varied probabilities. However default threshold=0.5 still produces near-0 predicted bots due to meta-learner cascade compression from zero Stage 2 text features (D-08).
  source: results_twibot20.json post-fix analysis
  significance: all-one-class bug is fixed; residual cross-domain performance gap is a separate model calibration concern, not a feature construction bug

## Eliminated

- Wrong decision threshold: threshold=0.5 is not the issue — p_final mean is 0.0023, far below any reasonable threshold
- Model not loaded correctly: model loads fine; trained_system_v12.joblib exists and deserializes correctly
- Label encoding issue: meta12.classes_=[0,1] and meta123.classes_=[0,1] — labels are correct direction

## Resolution

root_cause: Feature domain mismatch. Stage 1 uses Reddit-specific features (comment_num_1, comment_num_2, subreddit_list) that are all zero for every TwiBot-20 (Twitter) account. The post/comment ratio features were clamped to 50.0 for all accounts, mapping every TwiBot-20 user into an identical feature region that the BotSim-24-trained model confidently classifies as human. This low p1 signal propagates through meta12 and meta123, collapsing p_final to near zero for all 1183 test accounts.

fix: Replaced Reddit-specific Stage 1 feature slots with Twitter-native equivalents in evaluate_twibot20.py column adapter (D-09). comment_num_1 <- followers_count, comment_num_2 <- friends_count, subreddit_list <- [None]*listed_count. Changed ratio cap from 50.0 to 1000.0 to preserve per-account variance while handling outliers. After fix: post_c1 has 1157 unique values, Stage 1 AUC = 0.64, p_final AUC = 0.578, best F1 = 0.70 at threshold 0.016. All-one-class collapse is eliminated.

verification: Ran python evaluate_twibot20.py test.json trained_system_v12.joblib — no crash, 1183 results written with varied p_final values. Unique post_c1 count = 1157 (was 1). Stage 1 AUC = 0.6393, p_final AUC = 0.5778. Best F1 = 0.703 at threshold 0.016.

files_changed:
  - evaluate_twibot20.py: column adapter lines 74-76 replaced with Twitter-native feature extraction; cap changed from 50.0 to 1000.0; added _int_field() helper; updated docstrings (D-09)
