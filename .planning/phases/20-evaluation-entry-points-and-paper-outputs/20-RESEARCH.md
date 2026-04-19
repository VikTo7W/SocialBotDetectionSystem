# Phase 20: Evaluation Entry Points and Paper Outputs - Research

**Researched:** 2026-04-19
**Domain:** evaluation entry-point cleanup and paper-ready output generation (confusion matrices, routing tables, Table 5)
**Confidence:** HIGH

## Summary

Phase 19 produces the two fresh training artifacts (`trained_system_botsim.joblib` and `trained_system_twibot.joblib`). Phase 20 then builds three clean evaluation entry points that each load those artifacts, run inference through `CascadePipeline.predict()`, and produce the full paper output set. The paper output set has never included confusion matrix images — those are a new requirement added in v1.5 (PAPER-01). The routing statistics and per-stage metric tables (PAPER-02) already exist as a text-print path in `evaluate.py`; Phase 20 must write them as persistent files, not only print them. Table 5 (PAPER-03) already has a builder in `ablation_tables.generate_cross_dataset_table()` but its current main() block is wired to stale v1.2/v1.4 artifact paths and must be rewired to consume the EVAL-02 and EVAL-03 outputs.

Three legacy evaluation scripts exist and must be understood as templates and demoted:
- `evaluate.py` — shared evaluation helper, kept as-is; `evaluate_s3()` is the stable evaluation API
- `evaluate_twibot20.py` — the legacy Reddit-transfer script, wired to `trained_system_v12.joblib` and monkey-patches Stage 1 via `bp.extract_stage1_matrix`; must be superseded by `eval_reddit_twibot_transfer.py`
- `evaluate_twibot20_native.py` — the legacy TwiBot-native script, already updated in Phase 18 to use `CascadePipeline.predict()`; should be superseded by `eval_twibot_native.py`

The biggest design risk for Phase 20 is the BotSim evaluation path. The existing `evaluate_twibot20.py` and `evaluate_twibot20_native.py` both consume TwiBot-20 data; there is no maintained `eval_botsim_native.py` or equivalent that loads BotSim-24 test data. The BotSim test split is currently reconstructed from a deterministic `train_test_split` inside `train_botsim.train_botsim()`. The evaluation entry point must replicate that same split logic — or the training script must export the test split — so that the evaluation script sees the same held-out set the model was validated on.

**Primary recommendation:** Build the three evaluation entry points in the same structural pattern: load artifact, reconstruct or load the correct test split, run `CascadePipeline.predict()`, call `evaluate_s3()`, then write confusion matrix image, metrics JSON, and routing/stage table files. Generate Table 5 as a final wave step that reads the persisted outputs from EVAL-02 and EVAL-03.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| EVAL-01 | `eval_botsim_native.py` evaluates Reddit-trained model on BotSim-24 test split with per-stage breakdown and routing statistics | BotSim test split reconstructed via `split_train_accounts()` from `train_botsim.py` with SEED=42; `CascadePipeline("botsim").predict()` is the inference path |
| EVAL-02 | `eval_reddit_twibot_transfer.py` evaluates Reddit-trained model on TwiBot-20 zero-shot | Supersedes `evaluate_twibot20.py`; the transfer adapter monkey-patch on `bp.extract_stage1_matrix` must migrate into `CascadePipeline` or be re-applied cleanly; model path changes from `trained_system_v12.joblib` to `trained_system_botsim.joblib` |
| EVAL-03 | `eval_twibot_native.py` evaluates TwiBot-trained model on TwiBot-20 test data | Supersedes `evaluate_twibot20_native.py`; already uses `CascadePipeline.predict()`; model path changes from `DEFAULT_TWIBOT_MODEL_PATH` (which already resolves to `trained_system_twibot.joblib`) |
| PAPER-01 | All three evaluation entry points write confusion matrix image files | `sklearn.metrics.ConfusionMatrixDisplay` + `matplotlib` (both installed); standard pattern is `ConfusionMatrixDisplay.from_predictions()` then `savefig()` |
| PAPER-02 | All three entry points produce routing statistics and per-stage metric tables in existing paper format | `evaluate_s3()` already returns the structured dict; need to persist it as a JSON file and optionally write a formatted text or LaTeX table — currently only printed, not saved |
| PAPER-03 | Table 5 generated from EVAL-02 and EVAL-03 outputs without manual steps | `ablation_tables.generate_cross_dataset_table()` already builds the three-column table; must add a BotSim metrics input; needs to read persisted JSON files from EVAL-01, EVAL-02, EVAL-03 and call `save_latex()` |
</phase_requirements>

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Model inference (all three eval paths) | `CascadePipeline.predict()` | — | Shared orchestration established in Phase 18; all eval entry points must route through it |
| BotSim test split reconstruction | `train_botsim.split_train_accounts()` | `train_botsim.load_botsim_accounts()` + `load_botsim_edges()` | Split is deterministic (SEED=42); helpers already exported from `train_botsim.py` |
| TwiBot test data loading | `twibot20_io.load_accounts` + `twibot20_io.build_edges` | `train_twibot.load_accounts_with_ids` | TwiBot uses explicit `test.json` split; no reconstruction needed |
| Reddit-to-TwiBot transfer adapter | `eval_reddit_twibot_transfer.py` | — | Column mapping logic currently lives in `evaluate_twibot20.run_inference()`; must be extracted into the new entry point cleanly without monkey-patching |
| Confusion matrix generation | Each eval entry point | `sklearn.metrics.ConfusionMatrixDisplay` | Image file written per evaluation run |
| Metrics persistence | Each eval entry point | `evaluate.evaluate_s3()` | Existing text-print format extended with JSON write |
| Table 5 generation | `ablation_tables.generate_cross_dataset_table()` | New `generate_table5.py` or `eval_paper_outputs.py` driver | Must read persisted EVAL-01/02/03 JSON files and call `save_latex()` |
| LaTeX table export | `ablation_tables.save_latex()` | — | Already implemented; reusable as-is |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| scikit-learn | 1.6.1 (verified) | `ConfusionMatrixDisplay`, `confusion_matrix` | Already in project; `ConfusionMatrixDisplay.from_predictions()` is the one-call API |
| matplotlib | 3.10.0 (verified) | Save confusion matrix as PNG | Already in project; `fig.savefig(path, dpi=150, bbox_inches="tight")` is standard |
| joblib | (project dep) | Load `.joblib` artifacts | Already used in all training and eval scripts |
| pandas | (project dep) | DataFrame handling throughout | Already used throughout |

[VERIFIED: pip show matplotlib scikit-learn on this machine]

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| seaborn | 0.13.2 (verified) | Optional: styled heatmaps | Skip — `ConfusionMatrixDisplay` is sufficient and already project-aligned |
| json | stdlib | Write metrics JSON files | Used in existing eval scripts; continue pattern |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| `ConfusionMatrixDisplay.from_predictions()` | Manual `plt.imshow(confusion_matrix(...))` | `from_predictions()` handles labels, colorbar, axis labels automatically; never hand-roll |

**Installation:** No new dependencies required. matplotlib and scikit-learn are already installed.

## Architecture Patterns

### System Architecture Diagram

```
Data files                  Artifact              Eval entry point                Paper outputs
-----------                 --------              ----------------                -------------
Users.csv                 trained_system_         eval_botsim_native.py   -->   confusion_matrix_botsim.png
user_post_comment.json    botsim.joblib    ----->   CascadePipeline             metrics_botsim.json
edge_index/type/weight.pt                         evaluate_s3()                  routing_botsim.json
                                                        |
test.json (TwiBot)        trained_system_         eval_reddit_twibot_transfer.py --> confusion_matrix_reddit_transfer.png
                          botsim.joblib    ----->   (transfer adapter)              metrics_reddit_transfer.json
                                                    CascadePipeline                routing_reddit_transfer.json
                                                    evaluate_s3()
                                                        |
test.json (TwiBot)        trained_system_         eval_twibot_native.py   -->   confusion_matrix_twibot_native.png
                          twibot.joblib    ----->   CascadePipeline             metrics_twibot_native.json
                                                    evaluate_s3()                  routing_twibot_native.json
                                                        |
                                              [EVAL-01 + EVAL-02 + EVAL-03 outputs]
                                                        |
                                              generate_table5.py / driver  -->  table5_cross_dataset.tex
                                              ablation_tables.generate_cross_dataset_table()
```

### Recommended Project Structure
```
eval_botsim_native.py          # new maintained BotSim evaluation entry point
eval_reddit_twibot_transfer.py # new maintained Reddit-transfer evaluation entry point
eval_twibot_native.py          # new maintained TwiBot-native evaluation entry point
evaluate.py                    # unchanged shared evaluation helper
ablation_tables.py             # updated: Table 5 driver reads new output paths
tables/                        # existing LaTeX output directory
  table5_cross_dataset.tex     # regenerated from new EVAL outputs
paper_outputs/                 # new: image and JSON outputs from the three eval scripts
  confusion_matrix_botsim.png
  metrics_botsim.json
  routing_botsim.json
  confusion_matrix_reddit_transfer.png
  metrics_reddit_transfer.json
  routing_reddit_transfer.json
  confusion_matrix_twibot_native.png
  metrics_twibot_native.json
  routing_twibot_native.json
```

### Pattern 1: BotSim Evaluation (EVAL-01)

The BotSim test split is not a separate file — it is the S3 split from the training run. The planner must decide between two approaches:

**Option A (recommended):** Re-run the same split logic from `train_botsim.py` at evaluation time using the same SEED=42. Since `split_train_accounts()` is exported from `train_botsim`, the eval script can call it directly. This is deterministic and requires no file change to the training script.

**Option B:** Have `train_botsim.py` write the S3 split indices to a sidecar file. This adds coupling but is more explicit. Not recommended unless reproducibility concerns require it.

```python
# Source: train_botsim.py (pattern to replicate in eval_botsim_native.py)
from train_botsim import (
    load_botsim_accounts,
    load_botsim_edges,
    split_train_accounts,
    filter_edges_for_split,
    DEFAULT_BOTSIM_MODEL_PATH,
)

users, accounts = load_botsim_accounts()
edges_df = load_botsim_edges()
_S1, _S2, S3 = split_train_accounts(accounts, seed=SEED)
edges_S3 = filter_edges_for_split(edges_df, S3["node_idx"].to_numpy())

system = joblib.load(model_path)
pipeline = CascadePipeline("botsim", cfg=system.cfg, embedder=system.embedder)
results = pipeline.predict(system, df=S3, edges_df=edges_S3, nodes_total=len(users))
metrics = evaluate_s3(results, S3["label"].to_numpy(), verbose=True)
```

### Pattern 2: Reddit-Transfer Evaluation (EVAL-02)

The legacy `evaluate_twibot20.run_inference()` applies a transfer adapter that:
1. Maps TwiBot tweet type counts to BotSim `submission_num`, `comment_num_1`, `comment_num_2` columns
2. Maps `domain_list` to `subreddit_list`
3. Monkey-patches `bp.extract_stage1_matrix` to clamp ratio columns (indices 6-9) to `_RATIO_CAP = 1000.0`

This monkey-patch is the ugliest part of the legacy code. Phase 20 must carry this forward but should express it differently — either via a wrapper DataFrame column rewrite before passing to `CascadePipeline.predict()`, or by preserving the monkey-patch but documenting it clearly. The key constraint is that `CascadePipeline` calls `self.stage1_extractor.extract(df)` internally, and the stage1 extractor reads specific column names from the DataFrame. The cleanest approach is to rewrite the columns in the DataFrame itself rather than patching the extractor function.

The model for EVAL-02 changes from `trained_system_v12.joblib` to `trained_system_botsim.joblib`.

```python
# Source: evaluate_twibot20.py (transfer adapter pattern — extracted from run_inference)
# rewrite TwiBot columns to match BotSim schema before calling pipeline.predict()
from twibot20_io import parse_tweet_types, build_edges, load_accounts

accounts_df = load_accounts(test_json_path)
tweet_stats = [parse_tweet_types(msgs) for msgs in accounts_df["messages"]]
accounts_df = accounts_df.copy()
accounts_df["submission_num"] = [float(s["original_count"] + s["mt_count"] + s["rt_count"]) for s in tweet_stats]
accounts_df["comment_num_1"] = [float(s["original_count"]) for s in tweet_stats]
accounts_df["comment_num_2"] = [float(s["mt_count"]) for s in tweet_stats]
accounts_df["subreddit_list"] = accounts_df["domain_list"].tolist()
# ratio clamping: apply after extraction, or pass through a wrapper
```

### Pattern 3: Confusion Matrix Image (PAPER-01)

```python
# Source: sklearn docs — ConfusionMatrixDisplay.from_predictions
from sklearn.metrics import ConfusionMatrixDisplay
import matplotlib
matplotlib.use("Agg")  # non-interactive backend for headless runs
import matplotlib.pyplot as plt

y_true = S3["label"].to_numpy()
y_pred = (results["p_final"].to_numpy() >= threshold).astype(int)
disp = ConfusionMatrixDisplay.from_predictions(
    y_true, y_pred,
    display_labels=["human", "bot"],
    colorbar=False,
)
disp.ax_.set_title(f"{eval_name} confusion matrix")
disp.figure_.savefig(output_path, dpi=150, bbox_inches="tight")
plt.close(disp.figure_)
```

[VERIFIED: `from sklearn.metrics import ConfusionMatrixDisplay` — confirmed importable in this environment]

### Pattern 4: Metrics and Routing File Persistence (PAPER-02)

`evaluate_s3()` already returns a dict with `{"overall": {...}, "per_stage": {...}, "routing": {...}}`. The evaluation scripts currently only call this for stdout printing (or write a combined metrics JSON). Phase 20 must write:

1. A combined `metrics_{name}.json` — the full `evaluate_s3()` return dict (already done in `evaluate_twibot20_native.py`)
2. A confusion matrix image file (new — PAPER-01)
3. The routing and per-stage data are inside the metrics JSON; no separate file is strictly required unless the planner chooses to split them

The existing format in `metrics_twibot20_native.json` is the reference standard:
```json
{
  "overall": {"f1": ..., "auc": ..., "precision": ..., "recall": ...},
  "per_stage": {"p1": {...}, "p2": {...}, "p12": {...}, "p_final": {...}},
  "routing": {"pct_stage1_exit": ..., "pct_stage2_exit": ..., "pct_stage3_exit": ..., "pct_amr_triggered": ...}
}
```

### Pattern 5: Table 5 Generation (PAPER-03)

`ablation_tables.generate_cross_dataset_table()` currently takes three metrics dicts and produces a DataFrame with columns: `["Metric", "BotSim-24 (Reddit, in-dist.)", "TwiBot-20 (Reddit transfer)", "TwiBot-20 (TwiBot-native)"]`. The function signature is:

```python
# Source: ablation_tables.py lines 192-229
generate_cross_dataset_table(
    botsim24_metrics: dict,        # full evaluate_s3() return dict
    reddit_transfer_metrics: dict,  # full evaluate_s3() return dict
    twibot20_native_metrics: dict,  # full evaluate_s3() return dict
) -> pd.DataFrame
```

The driver logic must:
1. Load the three persisted metrics JSON files from EVAL-01, EVAL-02, EVAL-03 outputs
2. Call `generate_cross_dataset_table()`
3. Call `save_latex(df, "tables/table5_cross_dataset.tex")` — already implemented in `ablation_tables.py`

This can be a standalone script (`generate_table5.py`) or added as a final step in the largest eval entry point. A standalone script is cleaner for pipeline reasons.

### Anti-Patterns to Avoid

- **Monkey-patching the module-level `bp.extract_stage1_matrix` in new maintained code:** The legacy `evaluate_twibot20.py` does this; the new `eval_reddit_twibot_transfer.py` should use DataFrame column rewriting instead, which avoids global state mutation
- **Relying on `evaluate_twibot20_native.DEFAULT_NATIVE_MODEL_PATH`:** This resolves to `DEFAULT_TWIBOT_MODEL_PATH` from `train_twibot`; the new `eval_twibot_native.py` should import the constant directly from `train_twibot`
- **Reconstructing the BotSim split with a different seed or split fraction:** Must use SEED=42 and the exact same fractions as `train_botsim.split_train_accounts()` — any deviation produces a contaminated test set
- **Writing confusion matrices inside `evaluate_s3()`:** That function is a shared helper and should remain output-format-agnostic; image writing belongs in the entry point scripts
- **Using `plt.show()` in entry point scripts:** Entry points may run headless; always use `matplotlib.use("Agg")` and `fig.savefig()` + `plt.close()`

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Confusion matrix rendering | Custom matplotlib grid | `sklearn.metrics.ConfusionMatrixDisplay.from_predictions()` | Handles labels, colorbar, axis formatting; one-call API |
| Metrics computation | Custom F1/AUC/precision/recall | `evaluate.evaluate_s3()` | Already tested and stable; shared across all eval paths |
| LaTeX table export | Custom string formatting | `ablation_tables.save_latex()` | Already implemented; used for Tables 1-4 |
| Transfer adapter column mapping | New mapping class | Re-use the column-rewrite logic from `evaluate_twibot20.run_inference()` | Logic is already tested in the existing script; extract and clean it, don't rewrite from scratch |

**Key insight:** All the building blocks for paper outputs exist in `evaluate.py` and `ablation_tables.py`. Phase 20 is primarily wiring and cleanup, not new algorithmic work.

## Common Pitfalls

### Pitfall 1: BotSim Test Split Contamination

**What goes wrong:** The eval script loads all BotSim-24 accounts and evaluates on the full dataset instead of only the S3 (test) split.

**Why it happens:** The BotSim test split is implicit (derived from a deterministic `train_test_split` call) rather than an explicit file. It is easy to skip the split reconstruction and evaluate on all data.

**How to avoid:** The eval script must call `split_train_accounts(accounts, seed=SEED)` and use only the returned S3 slice. The SEED and split fractions must match `train_botsim.py` exactly.

**Warning signs:** Evaluation set size is 2907 (full dataset) instead of ~436 (15% test split); F1 is suspiciously high.

### Pitfall 2: Transfer Adapter Breaks When Model Changes

**What goes wrong:** `eval_reddit_twibot_transfer.py` loads `trained_system_botsim.joblib` but the `FeatureConfig` stored in the system artifact still expects the BotSim feature column order. If the DataFrame column rewrite for the transfer adapter is incomplete, Stage 1 extraction silently reads zero or NaN for key columns.

**Why it happens:** The legacy monkey-patch path in `evaluate_twibot20.py` intercepts the extraction function after features are read from the DataFrame. A DataFrame-rewrite approach must ensure every column that `Stage1Extractor.extract()` reads from `df` is populated correctly before `pipeline.predict()` is called.

**How to avoid:** Inspect `features/stage1.py` to enumerate exactly which column names `Stage1Extractor("botsim").extract(df)` reads from the DataFrame, then verify the transfer adapter populates all of them.

**Warning signs:** Stage 1 F1 is 0.0 or AUC is 0.5 (random-chance level); `pct_stage1_exit` is 0% or 100%.

### Pitfall 3: matplotlib Non-Interactive Backend

**What goes wrong:** Confusion matrix image generation fails or opens a GUI window when run non-interactively.

**Why it happens:** The default matplotlib backend is not always `Agg` on Windows.

**How to avoid:** Call `matplotlib.use("Agg")` before any pyplot imports in the entry point scripts, or set `MPLBACKEND=Agg` in the environment.

**Warning signs:** `UserWarning: Matplotlib is currently using TkAgg` or `cannot connect to X server`.

### Pitfall 4: Table 5 Driver Reads Stale Phase 15/16 Artifacts

**What goes wrong:** The Table 5 generator reads `metrics_twibot20_native.json` from the Phase 15 artifact directory and `metrics_twibot20_reddit_transfer.json` from the Phase 16 directory, bypassing the new EVAL outputs.

**Why it happens:** `ablation_tables.py` has hardcoded `DEFAULT_NATIVE_METRICS_PATH` and `DEFAULT_REDDIT_TRANSFER_METRICS_PATH` pointing to those old paths.

**How to avoid:** The Phase 20 Table 5 driver must pass explicit paths pointing to the new EVAL-01, EVAL-02, EVAL-03 outputs — not the old defaults in `ablation_tables.py`.

**Warning signs:** `table5_cross_dataset.tex` shows old column headers (`TwiBot-20 (Twitter, static)` instead of `TwiBot-20 (Reddit transfer)`).

### Pitfall 5: `test_ablation_tables.py` Import Error Already Present

**What goes wrong:** The existing `tests/test_ablation_tables.py` fails to import because `ablation_tables.py` does `from main import filter_edges_for_split`, but Phase 19 demoted `main.py` and the function moved to `train_botsim.py`.

**Why it happens:** The import in `ablation_tables.py` line 38 references `main.filter_edges_for_split`, which no longer exists.

**How to avoid:** Phase 20 must fix the import in `ablation_tables.py` (`from train_botsim import filter_edges_for_split`) and update the corresponding test. This is a pre-existing breakage that blocks `pytest tests/` unless the file is excluded.

**Warning signs:** `ImportError: cannot import name 'filter_edges_for_split' from 'main'` — already confirmed.

## Code Examples

### Confusion Matrix (complete pattern)
```python
# Source: sklearn.metrics documentation — ConfusionMatrixDisplay
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from sklearn.metrics import ConfusionMatrixDisplay

y_true = ground_truth_labels  # numpy int array
y_pred = (results["p_final"].to_numpy() >= threshold).astype(int)

disp = ConfusionMatrixDisplay.from_predictions(
    y_true,
    y_pred,
    display_labels=["human", "bot"],
    colorbar=False,
    cmap="Blues",
)
disp.ax_.set_title(eval_label)
disp.figure_.tight_layout()
disp.figure_.savefig(confusion_matrix_path, dpi=150, bbox_inches="tight")
plt.close(disp.figure_)
```

### evaluate_s3 output persistence
```python
# Source: evaluate_twibot20_native.py (existing pattern to replicate for all three eval scripts)
import json

metrics = evaluate_s3(results, y_true, threshold=threshold, verbose=True)

with open(metrics_path, "w", encoding="utf-8") as f:
    json.dump(metrics, f, indent=2)
```

### Table 5 generation driver
```python
# Source: ablation_tables.py generate_cross_dataset_table + save_latex
import json
from ablation_tables import generate_cross_dataset_table, save_latex

def _load(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)

botsim_metrics = _load(botsim_metrics_path)
reddit_transfer_metrics = _load(reddit_transfer_metrics_path)
twibot_native_metrics = _load(twibot_native_metrics_path)

df_t5 = generate_cross_dataset_table(botsim_metrics, reddit_transfer_metrics, twibot_native_metrics)
save_latex(df_t5, "tables/table5_cross_dataset.tex")
```

## Existing Test Infrastructure

### Tests that already cover the Phase 20 surface
- `tests/test_evaluate.py` — 22 tests covering `evaluate_s3()` structure, routing invariants, printed output headers; all passing
- `tests/test_evaluate_twibot20_native.py` — 4 tests covering `evaluate_twibot20_native` entry-point contract; all passing
- `tests/test_evaluate_twibot20.py` — 1 test currently failing (`test_run_inference_returns_correct_schema`; likely wired to legacy artifact name); needs investigation
- `tests/test_ablation_tables.py` — currently broken by `ImportError: cannot import name 'filter_edges_for_split' from 'main'`; must be fixed in Phase 20

### Wave 0 gaps

New test files needed:
- `tests/test_eval_botsim_native.py` — contract tests for `eval_botsim_native.py`: correct model path default, S3 split isolation, metrics JSON schema, confusion matrix file written
- `tests/test_eval_reddit_twibot_transfer.py` — contract tests for `eval_reddit_twibot_transfer.py`: correct model path (`trained_system_botsim.joblib`), transfer adapter column mapping, metrics JSON schema
- `tests/test_eval_twibot_native.py` — contract tests for `eval_twibot_native.py`: correct model path (`trained_system_twibot.joblib`), metrics JSON schema, confusion matrix file written (Note: `evaluate_twibot20_native.py` is the precursor; the new script should be a renamed/updated version)
- `tests/test_paper_outputs.py` — tests for Table 5 generation: reads three metrics JSONs, produces correct column headers, `save_latex()` writes the file

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | none (pytest autodiscovery) |
| Quick run command | `python -m pytest tests/test_eval_botsim_native.py tests/test_eval_reddit_twibot_transfer.py tests/test_eval_twibot_native.py tests/test_paper_outputs.py -x -q` |
| Full suite command | `python -m pytest tests/ --ignore=tests/test_ablation_tables.py -q` (after ablation_tables import fix, run without ignore) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| EVAL-01 | `eval_botsim_native.py` uses S3 split and `trained_system_botsim.joblib` | unit (monkeypatched) | `pytest tests/test_eval_botsim_native.py -x -q` | ❌ Wave 0 |
| EVAL-02 | `eval_reddit_twibot_transfer.py` uses `trained_system_botsim.joblib` and transfer adapter | unit (monkeypatched) | `pytest tests/test_eval_reddit_twibot_transfer.py -x -q` | ❌ Wave 0 |
| EVAL-03 | `eval_twibot_native.py` uses `trained_system_twibot.joblib` and `CascadePipeline("twibot")` | unit (monkeypatched) | `pytest tests/test_eval_twibot_native.py -x -q` | ❌ Wave 0 |
| PAPER-01 | Each eval script writes a confusion matrix PNG file | unit (monkeypatched output_dir) | `pytest tests/test_eval_botsim_native.py -k confusion -x -q` | ❌ Wave 0 |
| PAPER-02 | Each eval script writes metrics JSON with `overall`/`per_stage`/`routing` keys | unit | included in Wave 0 tests | ❌ Wave 0 |
| PAPER-03 | Table 5 reads EVAL-01/02/03 outputs and writes `table5_cross_dataset.tex` | unit | `pytest tests/test_paper_outputs.py -x -q` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_evaluate.py tests/test_evaluate_twibot20_native.py -x -q` (existing passing tests, fast)
- **Per wave merge:** Full new eval entry-point test suite
- **Phase gate:** Full suite green before `/gsd-verify-work`

### Wave 0 Gaps
- [ ] `tests/test_eval_botsim_native.py` — covers EVAL-01, PAPER-01, PAPER-02
- [ ] `tests/test_eval_reddit_twibot_transfer.py` — covers EVAL-02, PAPER-01, PAPER-02
- [ ] `tests/test_eval_twibot_native.py` — covers EVAL-03, PAPER-01, PAPER-02
- [ ] `tests/test_paper_outputs.py` — covers PAPER-03 (Table 5 generation)
- [ ] Fix `tests/test_ablation_tables.py` import error (`from main import` -> `from train_botsim import`)

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| `evaluate_twibot20.py` (monkey-patches `bp.extract_stage1_matrix`) | `eval_reddit_twibot_transfer.py` (DataFrame column rewrite) | Phase 20 | Removes global state mutation; cleaner and testable |
| `evaluate_twibot20_native.py` (uses `DEFAULT_TWIBOT_MODEL_PATH` from `train_twibot`) | `eval_twibot_native.py` | Phase 20 | Rename + same logic; model path already correct |
| Table 5 in `ablation_tables.main()` (reads Phase 15/16 artifact paths) | Standalone Table 5 driver reading EVAL output paths | Phase 20 | Removes manual prerequisite steps; `PAPER-03` requirement |
| No confusion matrix image output | `ConfusionMatrixDisplay.from_predictions()` → PNG per eval | Phase 20 (new) | `PAPER-01` requirement — first time confusion matrices are written as files |

**Deprecated/outdated:**
- `evaluate_twibot20.py`: superseded by `eval_reddit_twibot_transfer.py`; keep as compatibility shim or demote clearly
- `evaluate_twibot20_native.py`: superseded by `eval_twibot_native.py`; keep as compatibility shim or demote clearly
- `ablation_tables.DEFAULT_NATIVE_METRICS_PATH` / `DEFAULT_REDDIT_TRANSFER_METRICS_PATH`: these paths point to old phase directories; the Table 5 driver in Phase 20 should pass explicit paths from EVAL outputs

## Open Questions

1. **Where should paper outputs be written?**
   - What we know: there is no dedicated `paper_outputs/` directory yet; `tables/` exists for LaTeX; the Phase 15 artifact dir holds the old `metrics_twibot20_native.json`
   - What's unclear: should each eval script write to a shared `paper_outputs/` directory, or to a phase-specific artifact directory under `.planning/phases/20-*/artifacts/`, or to the repo root alongside `tables/`?
   - Recommendation: write to a new `paper_outputs/` directory at the repo root (alongside `tables/`); this is visible, not buried in `.planning/`, and matches the expected paper reproduction workflow described in the future README (Phase 21)

2. **Should `eval_twibot_native.py` replace `evaluate_twibot20_native.py` or coexist?**
   - What we know: `evaluate_twibot20_native.py` is already updated to use `CascadePipeline.predict()` and imports from `train_twibot`
   - What's unclear: whether the legacy script should be deleted or kept as a compatibility shim
   - Recommendation: create `eval_twibot_native.py` as the new maintained name; demote `evaluate_twibot20_native.py` to a one-line compatibility shim (like `main.py` pattern from Phase 19)

3. **How does the transfer adapter handle the ratio clamping in the new DataFrame-rewrite approach?**
   - What we know: the legacy path clamps Stage 1 feature columns 6-9 to `_RATIO_CAP = 1000.0` via monkey-patch after extraction
   - What's unclear: `Stage1Extractor("botsim").extract(df)` internally calls `extract_stage1_matrix()` which computes ratios from the DataFrame columns; if we rewrite the DataFrame columns to BotSim analogs, we need to verify whether the ratio computation still needs clamping
   - Recommendation: inspect `features/stage1.py` Stage1Extractor for botsim to understand column extraction, then decide if clamping can be applied before or after extraction

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| matplotlib | PAPER-01 (confusion matrix images) | ✓ | 3.10.0 | — |
| scikit-learn ConfusionMatrixDisplay | PAPER-01 | ✓ | 1.6.1 | — |
| trained_system_botsim.joblib | EVAL-01, EVAL-02 | produced by Phase 19 | — | Phase 20 blocked until Phase 19 runs |
| trained_system_twibot.joblib | EVAL-03 | produced by Phase 19 | — | Phase 20 blocked until Phase 19 runs |
| BotSim-24 data files (Users.csv, user_post_comment.json, edge_*.pt) | EVAL-01 | local only | — | Smoke tests can be monkeypatched; full eval requires data |
| TwiBot-20 test.json | EVAL-02, EVAL-03 | local only | — | Smoke tests can be monkeypatched; full eval requires data |

**Missing dependencies with no fallback:**
- `trained_system_botsim.joblib` and `trained_system_twibot.joblib`: unit tests can be monkeypatched but the final paper-output run requires Phase 19 artifacts
- BotSim-24 and TwiBot-20 data: required for full evaluation runs; the final verification wave must document whether data was available

**Missing dependencies with fallback:**
- All test-suite coverage can proceed via monkeypatching even without real data files

## Security Domain

This phase processes local data files and writes local output files. No network access, authentication, or user-facing inputs are involved. ASVS categories V5 (input validation) applies minimally — the entry points accept file paths as CLI arguments and should validate that referenced files exist before attempting to load them.

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | BotSim test split can be reconstructed deterministically by calling `split_train_accounts(accounts, seed=42)` in `eval_botsim_native.py` | Pattern 1 | If `train_botsim.py` Phase 19 changes the split logic or seed, the eval script would see a different test set than the model was validated on; needs cross-check once Phase 19 is final |
| A2 | `Stage1Extractor("botsim").extract(df)` reads named DataFrame columns (not positional) so the transfer adapter can rewrite columns before calling `pipeline.predict()` | Pattern 2 / Pitfall 2 | If the botsim Stage1Extractor reads from a positional matrix rather than named columns, column rewriting won't work; must be verified against `features/stage1.py` |
| A3 | Paper outputs directory should be `paper_outputs/` at the repo root | Open Questions | If the planner chooses a different output path, artifact paths in tests and Table 5 driver must change |

**If this table is empty:** All claims in this research were verified or cited — no user confirmation needed.

## Sources

### Primary (HIGH confidence)
- Codebase: `evaluate.py` — `evaluate_s3()` function interface, output dict schema, `_print_report()` format
- Codebase: `evaluate_twibot20_native.py` — existing TwiBot-native eval pattern; confirmed uses `CascadePipeline.predict()`
- Codebase: `evaluate_twibot20.py` — transfer adapter logic (monkey-patch + column mapping + ratio clamping)
- Codebase: `train_botsim.py` — `split_train_accounts()`, `load_botsim_accounts()`, `load_botsim_edges()`, `filter_edges_for_split()` — all exported helpers needed by EVAL-01
- Codebase: `ablation_tables.py` — `generate_cross_dataset_table()`, `save_latex()`, existing Table 5 builder
- Codebase: `cascade_pipeline.py` — `CascadePipeline.predict()` interface
- Runtime check: `python -m pip show matplotlib scikit-learn` — confirmed matplotlib 3.10.0, scikit-learn 1.6.1
- Runtime check: `python -m pytest tests/test_evaluate.py tests/test_evaluate_twibot20_native.py -x -q` — confirmed 22 tests passing

### Secondary (MEDIUM confidence)
- Phase 18 VERIFICATION.md — confirms `CascadePipeline` is the shared prediction surface for both datasets; confirms `evaluate_twibot20_native.py` was already updated to use it

### Tertiary (LOW confidence — none)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — no new libraries; all tools confirmed installed
- Architecture: HIGH — entry-point patterns directly derived from existing code
- Pitfalls: HIGH — import error in `test_ablation_tables.py` confirmed live; split contamination risk verified from training code structure
- Test gaps: HIGH — confirmed against actual test directory listing

**Research date:** 2026-04-19
**Valid until:** End of Phase 20 execution (30 days); `cascade_pipeline.py` and `evaluate.py` interfaces are stable
