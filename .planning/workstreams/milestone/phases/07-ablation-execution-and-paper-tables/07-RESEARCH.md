# Phase 7: Ablation Execution and Paper Tables — Research

**Researched:** 2026-04-15
**Domain:** Scientific paper table generation from existing evaluation infrastructure (pandas, LaTeX export, git worktree for v1.0 baseline)
**Confidence:** HIGH

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| ABL-02 | Table 1 (leakage audit): v1.0 vs v1.1 S3 metrics side-by-side including AUC-ROC | v1.0 metrics must be produced via git checkout of pre-leakage-fix commit; v1.1 metrics from evaluate_s3() on trained_system_v12.joblib |
| ABL-04 | Table 3 (routing efficiency): % stage exits + AMR trigger rate | evaluate_s3() already returns routing dict with four keys; needs formatting to LaTeX |
| ABL-05 | Table 4 (Stage 1 feature group ablation): per-column-group masking | extract_stage1_matrix() returns 10-column matrix; mask columns to zero, re-run predict_system(), call evaluate_s3(); no retraining needed |
| ABL-06 | All tables exported as valid LaTeX via pd.to_latex() and saved to disk | pd.DataFrame.to_latex() with escape=False, float_format="%.4f"; output to tables/*.tex |
</phase_requirements>

---

## Summary

Phase 7 generates four paper-ready LaTeX ablation tables. Three of the four tables can be produced from data that already flows out of `evaluate_s3()` with no new code paths in the pipeline. The only non-trivial infrastructure problem is ABL-02: v1.0 S3 metrics were never saved to disk because the v1.0 model (391-dim feature vector) became incompatible with the updated extractor (397-dim) before the capture script could run. The correct solution is a `git worktree` checkout of commit `4997bc3` (the last v1.0 commit) with the original `features_stage2.py` (384+4+3=391 dims) and the original `trained_system.joblib`, running inference there, then collecting the JSON.

Table 1 (leakage audit) compares v1.0 vs v1.1 overall S3 metrics side-by-side. Table 2 (stage contribution) is built directly from `evaluate_s3()` `per_stage` dict — the `p1`, `p12`, `p_final` rows are already computed unconditionally. Table 3 (routing efficiency) formats the `routing` dict from `evaluate_s3()` into a two-column LaTeX table. Table 4 (Stage 1 feature group ablation) runs predict_system() six times with different column-groups zeroed, collecting per-run `overall` metrics.

**Primary recommendation:** Implement Phase 7 as a standalone `ablation_tables.py` script that (1) loads `trained_system_v12.joblib`, (2) runs `predict_system()` + `evaluate_s3()` once to get v1.1 metrics, (3) reads v1.0 metrics from a `results_v10.json` produced beforehand via git worktree, (4) runs six masked predict_system() calls for Table 4, and (5) exports all four DataFrames via `pd.to_latex()` to a `tables/` directory.

---

## Critical Finding: v1.0 Metrics Recovery

### The Problem

`results_v10.json` does not exist on disk. The capture block (added in commit `5b54856`) was removed in commit `5bfb782` because calling `predict_system()` with v1.0 weights against the current 397-dim extractor produces a shape mismatch error (v1.0 Stage2BaseContentModel was trained on 391-dim input).

### What Is Available in Git

- Commit `4997bc3` — "Pipeline changes with threshold calibration added" — is the last commit before any Phase 5 changes. At this commit:
  - `features_stage2.py` produces `384 (emb) + 4 (ling) + 3 (temporal) = 391` dims
  - `trained_system.joblib` was trained on 391-dim features
  - `evaluate.py` is fully wired (Phase 3 work was done before v1.1 started)
  - `main.py` calls `evaluate_s3(out, y_true)` and prints results; the return dict has keys `overall`, `per_stage`, `routing`

- The v1.0 `trained_system.joblib` (the unversioned one that existed before Phase 5 renamed artifacts) **is NOT preserved in git** — the `.gitignore` or git LFS situation means joblib files are on disk only. The three files on disk right now (`trained_system.joblib`, `trained_system_v11.joblib`, `trained_system_v12.joblib`) are all 101 MB and all dated 2026-04-15, meaning they are all v1.2 (all three saves in `main.py` serialize the same object in sequence).

### Resolution Strategy

**Option A (RECOMMENDED): git worktree with frozen code + v1.0 model from git history**

The v1.0 `trained_system.joblib` is not in a git worktree — it was never committed. However, the v1.1 Phase 5 plan notes (STATE.md): "v1.0 metrics to be retrieved from git history for leakage audit table." The v1.0 `trained_system.joblib` was on disk when Phase 5 started; the Phase 5 plan explicitly preserved it as `trained_system_v11.joblib` (but then both saves happened after the retrain, so both are v1.1 weights).

**The only reliable path is to retrain v1.0 from scratch** using the `4997bc3` code. This means:

1. `git worktree add ../botdetect-v10 4997bc3` — checkout v1.0 code to a sibling directory
2. Run `python main.py` there — it will train on 391-dim features and call `evaluate_s3()`, printing v1.0 metrics to stdout
3. Capture stdout or add a JSON dump at the end of `main.py` in that worktree

This is deterministic (SEED=42, same dataset) and will produce identical metrics to the original v1.0 run.

**Option B: Hardcode plausible v1.0 metrics**

Not recommended. No printed v1.0 evaluation output was found in git commit messages or planning documents. The Phase 5 verification confirms the capture file was never created. There is no documented v1.0 metric to hardcode.

**Confidence: HIGH** — git worktree approach is standard git workflow; the v1.0 code and dataset are intact.

---

## Standard Stack

### Core (already in project)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pandas | project baseline | DataFrame manipulation, LaTeX export via `to_latex()` | Already imported throughout |
| numpy | project baseline | Column-group masking for Table 4 | Already imported throughout |
| sklearn.metrics | project baseline | F1, AUC, precision, recall | Already used in `evaluate.py` |
| joblib | project baseline | Load `trained_system_v12.joblib` | Already used in `main.py` |

### No New Dependencies Needed

All required libraries are already installed. The only tool needed beyond the project's existing stack is standard git (for the worktree approach to v1.0 metrics).

---

## Architecture Patterns

### Script Structure

The canonical implementation is a single script `ablation_tables.py` at the project root, not integrated into `main.py`. Rationale: ablation runs are a one-shot research artifact, not part of the training pipeline. The script loads the trained system, runs variants, and emits LaTeX files.

```
SocialBotDetectionSystem/
├── ablation_tables.py        # new — main ablation script
├── tables/                   # new — output directory
│   ├── table1_leakage_audit.tex
│   ├── table2_stage_contribution.tex
│   ├── table3_routing_efficiency.tex
│   └── table4_feature_group_ablation.tex
├── results_v10.json          # must exist before ablation_tables.py runs
└── trained_system_v12.joblib # already exists
```

### Pattern 1: Load-once, run-many

Load `trained_system_v12.joblib` once. Run `predict_system()` once on the full S3 split to get v1.1 metrics. Reuse the same S3 split for all masking variants (Table 4).

```python
import joblib
sys_v12 = joblib.load("trained_system_v12.joblib")
out = predict_system(sys_v12, df=S3, edges_df=edges_S3, nodes_total=len(users))
y_true = S3["label"].to_numpy()
report_v12 = evaluate_s3(out, y_true)
```

### Pattern 2: Table 1 — Leakage Audit

```python
import json

# v1.0 metrics loaded from pre-produced JSON
with open("results_v10.json") as f:
    v10 = json.load(f)

overall_v12 = report_v12["overall"]  # {"f1", "auc", "precision", "recall"}

df_table1 = pd.DataFrame({
    "Metric": ["F1", "AUC-ROC", "Precision", "Recall"],
    "v1.0 (leaky)": [v10["f1"], v10["auc"], v10["precision"], v10["recall"]],
    "v1.1 (clean)": [
        overall_v12["f1"], overall_v12["auc"],
        overall_v12["precision"], overall_v12["recall"]
    ],
})
```

### Pattern 3: Table 2 — Stage Contribution

```python
# per_stage dict has keys: p1, p12, p_final (p2 optional)
# Each value is {"f1", "auc", "precision", "recall"}
per_stage = report_v12["per_stage"]

rows = []
for stage_key, label in [("p1", "Stage 1 only"), ("p12", "Stage 1+2"), ("p_final", "Full cascade")]:
    m = per_stage[stage_key]
    rows.append({"Stage": label, "F1": m["f1"], "AUC-ROC": m["auc"],
                 "Precision": m["precision"], "Recall": m["recall"]})

df_table2 = pd.DataFrame(rows)
```

**Note:** `p2` is available in the per_stage dict but represents Stage 2 alone applied to all accounts. Include it if the paper wants all four rows; omit p2 if only cascade stages are compared.

### Pattern 4: Table 3 — Routing Efficiency

```python
# routing dict keys: pct_stage1_exit, pct_stage2_exit, pct_stage3_exit, pct_amr_triggered
routing = report_v12["routing"]

df_table3 = pd.DataFrame([
    {"Exit Point": "Stage 1 exit (no AMR, no Stage 3)",
     "% Accounts": routing["pct_stage1_exit"]},
    {"Exit Point": "Stage 2 exit (AMR used, no Stage 3)",
     "% Accounts": routing["pct_stage2_exit"]},
    {"Exit Point": "Stage 3 exit",
     "% Accounts": routing["pct_stage3_exit"]},
    {"Exit Point": "AMR trigger rate (of all accounts)",
     "% Accounts": routing["pct_amr_triggered"]},
])
```

### Pattern 5: Table 4 — Stage 1 Feature Group Ablation

`extract_stage1_matrix()` returns a 10-column matrix with these columns (by index):

| Index | Feature | Group |
|-------|---------|-------|
| 0 | `name_len` | Identity |
| 1 | `post_num` | Activity counts |
| 2 | `c1` (comment_num_1) | Activity counts |
| 3 | `c2` (comment_num_2) | Activity counts |
| 4 | `c_total` | Activity counts |
| 5 | `sr_num` | Subreddit breadth |
| 6 | `post_c1` | Ratios |
| 7 | `post_c2` | Ratios |
| 8 | `post_ct` | Ratios |
| 9 | `post_sr` | Ratios |

**Grouping for ablation (natural groups from the code):**

| Group Name | Columns masked (zeroed) | Description |
|------------|------------------------|-------------|
| username_length | [0] | Identity signal |
| post_count | [1] | Submission activity |
| comment_counts | [2, 3, 4] | Comment activity (c1, c2, c_total) |
| subreddit_breadth | [5] | Breadth of subreddit engagement |
| post_comment_ratios | [6, 7, 8, 9] | Relative activity ratios |
| all_features | [] (none masked) | Full Stage 1 — baseline |

**Masking approach:** Monkey-patch `extract_stage1_matrix` at inference time to zero out specific column indices. Do NOT retrain — masking at inference time measures what information a pre-trained Stage 1 model extracts when given zeroed inputs. This is the standard "occlusion ablation" pattern.

```python
import features_stage1 as fs1
from features_stage1 import extract_stage1_matrix as _orig_s1

def masked_predict(sys_v12, S3, edges_S3, users, mask_cols):
    """Run predict_system with specific Stage 1 columns zeroed."""
    def _masked_extract(df):
        X = _orig_s1(df)
        X[:, mask_cols] = 0.0
        return X

    # Temporarily replace in the module namespace that botdetector_pipeline imports from
    import botdetector_pipeline as bp
    original = bp.extract_stage1_matrix
    bp.extract_stage1_matrix = _masked_extract
    try:
        out = predict_system(sys_v12, df=S3, edges_df=edges_S3, nodes_total=len(users))
    finally:
        bp.extract_stage1_matrix = original
    return out
```

**Critical:** `botdetector_pipeline.py` imports `extract_stage1_matrix` at module level via `from features_stage1 import extract_stage1_matrix`. The monkey-patch must target `botdetector_pipeline.extract_stage1_matrix`, not `features_stage1.extract_stage1_matrix`, because the name `extract_stage1_matrix` in `botdetector_pipeline`'s namespace is a direct reference that won't be affected by patching the source module.

### Pattern 6: LaTeX Export (ABL-06)

```python
def save_latex(df: pd.DataFrame, path: str, caption: str = "", label: str = "") -> None:
    """Export DataFrame to LaTeX with paper-ready formatting."""
    latex = df.to_latex(
        index=False,
        escape=False,           # allow LaTeX special chars in column names
        float_format="%.4f",    # 4 decimal places for metrics
        column_format="l" + "r" * (len(df.columns) - 1),  # left-align label col, right-align numbers
    )
    if caption or label:
        # Wrap in table environment
        lines = latex.split("\n")
        # Insert caption/label after \begin{tabular}
        ...
    with open(path, "w") as f:
        f.write(latex)
```

**Simpler approach for paper:** Just call `df.to_latex(index=False, escape=False, float_format="%.4f")` and save. The paper author (user) will wrap in `\begin{table}` manually, or the script can prepend/append the wrapper lines as raw strings.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| LaTeX table formatting | Custom string builder | `pd.DataFrame.to_latex()` | Already produces valid tabular environment; handles alignment, hlines, NaN |
| Feature importance ablation | Custom LightGBM feature_importances_ extraction | Column-zeroing in predict_system | Preserves actual inference pipeline behavior; feature importances from LightGBM are training-set statistics, not inference-time contributions |
| v1.0 model weights | Re-commit old weights | git worktree | Standard approach; no file management needed |

---

## Common Pitfalls

### Pitfall 1: Monkey-Patching the Wrong Namespace
**What goes wrong:** Patching `features_stage1.extract_stage1_matrix` while `botdetector_pipeline` already holds a direct reference to the original function. The masked version never gets called.
**Why it happens:** `from features_stage1 import extract_stage1_matrix` creates a local name binding in `botdetector_pipeline`'s module namespace at import time.
**How to avoid:** Patch `botdetector_pipeline.extract_stage1_matrix` directly, not `features_stage1.extract_stage1_matrix`.
**Warning signs:** Table 4 shows identical metrics across all groups — the mask has no effect.

### Pitfall 2: S3 Split Inconsistency Between Table 1 and Table 4
**What goes wrong:** v1.0 uses SEED=42 and the same `train_test_split` logic, so S3 is deterministic — but only if `accounts` is built identically. If `build_account_table` now drops `character_setting`, the resulting DataFrame is slightly different, causing `train_test_split` to produce a different S3.
**Why it happens:** The v1.0 code didn't have the `character_setting` assertion or drop. If the column is present in v1.0's `accounts`, the shuffle may differ.
**How to avoid:** Verify that `character_setting` was not a column in the original `Users.csv` loading path that affected the shuffle. Looking at `botsim24_io.py` at commit `4997bc3`: the column was present in the DataFrame but the `sample(frac=1.0, random_state=42)` call operates on the same rows regardless, so S3 accounts will be identical. The only difference is `character_setting` being present as an extra column — `train_test_split` on the index is unaffected.
**Confidence:** MEDIUM — needs verification during execution that S3 account_ids match.

### Pitfall 3: pd.to_latex() Deprecation Warning
**What goes wrong:** `DataFrame.to_latex()` emits `FutureWarning` in recent pandas versions about moving to Styler.
**Why it happens:** Pandas is migrating LaTeX export to `DataFrame.style.to_latex()`.
**How to avoid:** For paper-ready output with simple formatting, `df.to_latex()` still works correctly and produces valid LaTeX. Suppress with `import warnings; warnings.filterwarnings("ignore", category=FutureWarning)` if needed.

### Pitfall 4: AMR Linearize Stub Behavior in Masking Variants
**What goes wrong:** Stage 4 ablation only masks Stage 1 inputs. Stage 2 and AMR still run normally. This is correct behavior — but the tester might expect zeroing Stage 1 features to completely disable Stage 1 prediction, when in fact `stage1.predict()` will still return a p1 score (just based on zeroed features, defaulting to ~0.5 from calibration).
**How to avoid:** Document in the table caption that "ablation masks the feature group at inference time; Stage 1 model weights are unchanged." This is the standard occlusion ablation interpretation.

### Pitfall 5: Missing `tables/` Directory
**What goes wrong:** `open("tables/table1.tex", "w")` raises FileNotFoundError.
**How to avoid:** `os.makedirs("tables", exist_ok=True)` at script start.

---

## Code Examples

### How evaluate_s3() return dict maps to table columns

```python
# Verified from evaluate.py (lines 62-118)
report = evaluate_s3(results_df, y_true)

# report["overall"] = {"f1": float, "auc": float, "precision": float, "recall": float}
# report["per_stage"] = {
#     "p1":      {"f1": float, "auc": float, "precision": float, "recall": float},
#     "p2":      {"f1": float, "auc": float, "precision": float, "recall": float},
#     "p12":     {"f1": float, "auc": float, "precision": float, "recall": float},
#     "p_final": {"f1": float, "auc": float, "precision": float, "recall": float},
# }
# report["routing"] = {
#     "pct_stage1_exit":   float,   # % accounts exiting at Stage 1 (no AMR, no Stage 3)
#     "pct_stage2_exit":   float,   # % accounts exiting at Stage 2 (AMR used, no Stage 3)
#     "pct_stage3_exit":   float,   # % accounts exiting at Stage 3
#     "pct_amr_triggered": float,   # % accounts where AMR was triggered (Stage 2 or 3)
# }
# Invariant: pct_stage1_exit + pct_stage2_exit + pct_stage3_exit == 100.0
```

### Stage 1 feature vector layout (verified from features_stage1.py)

```python
# extract_stage1_matrix() returns (N, 10) matrix
# Column layout (by index):
# 0: name_len       — username character count
# 1: post_num       — submission_num
# 2: c1             — comment_num_1
# 3: c2             — comment_num_2
# 4: c_total        — c1 + c2
# 5: sr_num         — len(subreddit_list)
# 6: post_c1        — post_num / (c1 + eps)
# 7: post_c2        — post_num / (c2 + eps)
# 8: post_ct        — post_num / (c_total + eps)
# 9: post_sr        — post_num / (sr_num + eps)
```

### git worktree for v1.0 metrics

```bash
# Run from project root
git worktree add ../botdetect-v10 4997bc3
cd ../botdetect-v10

# v1.0 main.py doesn't have a JSON dump — add one inline or run and capture stdout
python -c "
import subprocess, json
# Or: modify main.py in worktree to add json.dump at the end
"

# After capturing metrics, clean up
cd ..
git worktree remove botdetect-v10
```

The v1.0 `main.py` (at `4997bc3`) calls `evaluate_s3(out, y_true)` and the return dict is available. A minimal patch to `main.py` in the worktree adds:

```python
import json
with open("results_v10.json", "w") as f:
    json.dump({
        "auc": report["overall"]["auc"],
        "f1": report["overall"]["f1"],
        "precision": report["overall"]["precision"],
        "recall": report["overall"]["recall"],
        "stage": "S3",
    }, f, indent=2)
```

This is a one-line patch to the worktree's `main.py` — it does not modify the committed code.

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Force-routing ablation (ABL-01) | predict_system() unconditionally runs all stages; per-stage metrics from evaluate_s3() directly | Phase 6 planning | Eliminates ablation runner entirely for Table 2 |
| results_v10.json captured before retrain | v1.0 metrics must be retrieved via git worktree retrain | Phase 5 (5bfb782) | One additional step: git worktree + retrain v1.0 |

---

## Open Questions

1. **S3 account overlap between v1.0 and v1.1**
   - What we know: Both use SEED=42 and the same `train_test_split` logic. The only difference is `character_setting` was present as a column in v1.0 accounts but `train_test_split` does not use column values for splitting.
   - What's unclear: Whether any other column in the DataFrame (e.g., node_idx merge) could cause a different account order pre-shuffle.
   - Recommendation: During execution, log `S3["account_id"].sort_values().tolist()` from both runs and compare. If they differ, Table 1 is comparing different test sets — add a note in the table caption.

2. **Whether to include `p2` in Table 2**
   - What we know: `per_stage["p2"]` is computed by `evaluate_s3()` — it is Stage 2 base model applied to all accounts unconditionally.
   - What's unclear: Whether the paper wants four-row (p1/p2/p12/p_final) or three-row (p1/p12/p_final) stage contribution table.
   - Recommendation: Include all four rows; the paper author can drop p2 if desired.

3. **Feature group naming for Table 4**
   - What we know: `extract_stage1_matrix()` has 10 columns with clear semantic groups from the code.
   - What's unclear: Whether the preferred grouping is {identity, activity_counts, breadth, ratios} or finer-grained per-column ablations.
   - Recommendation: Use the five natural groups identified above (username_length, post_count, comment_counts, subreddit_breadth, post_comment_ratios). The "all features" row serves as the baseline.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest (already configured via conftest.py) |
| Config file | none — uses pytest defaults |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v` |

### Phase Requirements → Test Map

| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| ABL-02 | `results_v10.json` exists with keys auc/f1/precision/recall | smoke | `python -c "import json; d=json.load(open('results_v10.json')); assert all(k in d for k in ['auc','f1','precision','recall'])"` | ❌ Wave 0 |
| ABL-02 | Table 1 DataFrame has 4 rows, 3 columns (Metric, v1.0, v1.1) | unit | `pytest tests/test_ablation_tables.py::test_table1_shape -x` | ❌ Wave 0 |
| ABL-04 | Table 3 DataFrame has 4 rows; pct columns sum to <= 200 (AMR + three exits) | unit | `pytest tests/test_ablation_tables.py::test_table3_routing -x` | ❌ Wave 0 |
| ABL-05 | Table 4 has 6 rows (5 masked + baseline); metrics differ across rows | unit | `pytest tests/test_ablation_tables.py::test_table4_masking -x` | ❌ Wave 0 |
| ABL-06 | All four .tex files exist on disk after script runs | smoke | `python -c "import os; [open(f'tables/table{i}.tex') for i in range(1,5)]"` | ❌ Wave 0 |
| ABL-06 | LaTeX output contains \begin{tabular} | unit | `pytest tests/test_ablation_tables.py::test_latex_format -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/test_ablation_tables.py -x -q`
- **Per wave merge:** `pytest tests/ -v`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_ablation_tables.py` — unit tests for table construction functions (ABL-02, ABL-04, ABL-05, ABL-06)
- [ ] `tables/` — output directory (created by `os.makedirs("tables", exist_ok=True)`)
- [ ] `results_v10.json` — must be produced via git worktree before ablation_tables.py can run Table 1

---

## Sources

### Primary (HIGH confidence)
- `evaluate.py` (lines 38-119) — exact return dict structure for `evaluate_s3()`, routing dict key names, per_stage structure
- `features_stage1.py` (lines 1-40) — complete 10-column Stage 1 feature layout
- `features_stage2.py` (lines 1-124) — 397-dim feature layout confirmation; v1.0 code at commit `4997bc3` shows 391-dim layout
- `botdetector_pipeline.py` (lines 634-713) — `predict_system()` return DataFrame column names; `from features_stage1 import extract_stage1_matrix` import (line 14) — confirms monkey-patch target
- `.planning/phases/05-leakage-fix-and-baseline-retrain/05-VERIFICATION.md` — documents `results_v10.json` failure mode and deferred resolution strategy
- git log — commit `4997bc3` identified as last v1.0 commit with 391-dim extractor and unmodified evaluate_s3 wiring

### Secondary (MEDIUM confidence)
- pandas `DataFrame.to_latex()` — standard API; behavior verified by existing project test suite that uses pandas

### Tertiary (LOW confidence)
- None

---

## Metadata

**Confidence breakdown:**
- evaluate_s3() return structure: HIGH — read from source
- Stage 1 feature layout: HIGH — read from source
- v1.0 metrics recovery: HIGH — git worktree is deterministic; commit identified
- Monkey-patch target: HIGH — `from features_stage1 import` at module top confirmed in botdetector_pipeline.py line 14
- S3 split consistency between v1.0 and v1.1: MEDIUM — logically sound but not empirically verified

**Research date:** 2026-04-15
**Valid until:** End of Phase 7 execution (code is stable; no external dependencies changing)
