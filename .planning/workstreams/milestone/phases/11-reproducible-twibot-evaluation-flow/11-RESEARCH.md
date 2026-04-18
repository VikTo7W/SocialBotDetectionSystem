# Phase 11: Reproducible TwiBot Evaluation Flow - Research

**Researched:** 2026-04-18
**Domain:** Python evaluation hardening — artifact path management, test suite repair, Windows path hygiene
**Confidence:** HIGH

---

## Summary

Phase 11's job is entirely about hardening what already exists. The TwiBot evaluation logic
(run_inference, evaluate_twibot20, compare_twibot20_conditions) is fully implemented in
evaluate_twibot20.py, and the paper-output path (generate_cross_dataset_table, save_latex)
is fully implemented in ablation_tables.py. The gap is not missing functionality — it is
three specific engineering gaps that block reliable execution:

**Gap 1 — Missing artifact.** `metrics_twibot20_comparison.json` does not exist on disk.
The `__main__` block in evaluate_twibot20.py writes it to the process working directory with
a hardcoded bare filename. ablation_tables.py requires it at the same hardcoded bare filename.
Without it, Table 5 is silently skipped. Phase 12 needs it to regenerate live evidence.
[VERIFIED: file check; grep of source]

**Gap 2 — Two broken tests.** `test_evaluate_twibot20_returns_metrics` and
`test_evaluate_twibot20_calls_evaluate_s3` are failing because their monkeypatched stubs
use a 2-argument lambda `lambda p, m: results_df` that does not accept `online_calibration`
or `window_size`. evaluate_twibot20.py's `evaluate_twibot20()` now forwards these kwargs to
`run_inference()`, which the stubs reject. This is a test-code mismatch, not a production
code bug. [VERIFIED: pytest run shows 2 failed, 21 passed]

**Gap 3 — Hardcoded bare filenames everywhere.** All three output files
(`results_twibot20.json`, `metrics_twibot20.json`, `metrics_twibot20_comparison.json`) are
written to whatever the cwd happens to be. There is no documented "output directory", no
`--output-dir` parameter, and no env-var override. This is the "fragile default" REPRO-02
identifies.

The phase has no new dependencies, no new libraries, and no architectural changes. It is
purely: (1) fix the two broken tests, (2) introduce an explicit output-directory parameter
to the entry points, (3) write the missing comparison artifact, and (4) document the stable
command.

**Primary recommendation:** Introduce an `output_dir` parameter (default `"."`) to the
`__main__` block and to `compare_twibot20_conditions`. Write all three artifacts to that
directory. Update tests to use `tmp_path` for outputs rather than cwd. Fix the two lambda
stubs.

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| REPRO-01 | Developer can run a documented TwiBot evaluation command that produces both static-threshold and recalibrated outputs in a reproducible local artifact directory | Introduce `output_dir` parameter; document the command in a docstring or comment block |
| REPRO-02 | TwiBot evaluation no longer depends on fragile default temp/cache paths for its normal artifact-generation workflow | Replace hardcoded bare filenames with `os.path.join(output_dir, filename)`; default to `"."` for backward compat |
| REPRO-03 | Generated artifacts include results, metrics, and comparison outputs with stable filenames and documented meaning | The three filenames are already stable; documenting their payload structure is the remaining gap |
</phase_requirements>

---

## Architectural Responsibility Map

| Capability | Primary Tier | Secondary Tier | Rationale |
|------------|-------------|----------------|-----------|
| Artifact path resolution | Entry point (`__main__`) | `compare_twibot20_conditions` | The entry point controls the run; path decisions should not be buried in helper functions |
| Static-threshold inference | `run_inference(online_calibration=False)` | — | Already implemented and tested |
| Recalibrated inference | `run_inference(online_calibration=True)` | — | Already implemented and tested |
| Comparison struct | `compare_twibot20_conditions()` | — | Already implemented; needs path parameter |
| JSON serialization | `_save_json()` helper | — | Already exists in evaluate_twibot20.py |
| Table 5 generation | `ablation_tables.py` | — | Consumes persisted comparison artifact; needs to know where to look |
| Test isolation | pytest `tmp_path` fixture | — | All artifact writes in tests should use `tmp_path`, not cwd |

---

## Standard Stack

### Core (already in project — no new installs)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Python stdlib `os.path` | 3.x | Path joining, makedirs, existence checks | Zero-dependency path management |
| Python stdlib `json` | 3.x | JSON serialization of comparison artifacts | Already used throughout codebase |
| pytest | 8.3.4 | Test framework | Already installed [VERIFIED: pytest --version] |
| pytest `tmp_path` fixture | built-in | Per-test isolated temp directories | Preferred pytest pattern; avoids cwd writes in tests |

No new dependencies are needed. This phase does not install any packages.

**Version verification:** All libraries are stdlib or already installed.
[VERIFIED: `python -c "import pytest; print(pytest.__version__)"` -> 8.3.4]

---

## Architecture Patterns

### System Architecture Diagram

```
Developer runs:
  python evaluate_twibot20.py test.json trained_system_v12.joblib [output_dir]
                              |
                              v
                    __main__ block
                    resolves output_dir (default ".")
                              |
               +--------------+---------------+
               |                              |
        run_inference(static=False)   run_inference(recalibrated=True)
               |                              |
               v                              v
     results_twibot20.json       compare_twibot20_conditions()
     metrics_twibot20.json                    |
                                              v
                               metrics_twibot20_comparison.json
                                              |
                                              v
                               ablation_tables.py (Table 5)
                                              |
                                              v
                               tables/table5_cross_dataset.tex
```

### Recommended Output Structure
```
[output_dir]/                       # default ".", configurable
├── results_twibot20.json           # inference results DataFrame (N rows x 11 cols)
├── metrics_twibot20.json           # evaluate_s3() output for recalibrated run
└── metrics_twibot20_comparison.json # compare_twibot20_conditions() output
tables/
└── table5_cross_dataset.tex        # generated by ablation_tables.py (separate concern)
```

### Pattern 1: output_dir parameter with os.path.join
**What:** Replace hardcoded bare filenames with `os.path.join(output_dir, filename)`.
**When to use:** Wherever evaluate_twibot20.py writes an artifact.
**Example:**
```python
# Source: Python stdlib os.path — standard pattern
def __main__():
    output_dir = sys.argv[3] if len(sys.argv) > 3 else "."
    os.makedirs(output_dir, exist_ok=True)

    out_path = os.path.join(output_dir, "results_twibot20.json")
    metrics_path = os.path.join(output_dir, "metrics_twibot20.json")
    comparison_path = os.path.join(output_dir, "metrics_twibot20_comparison.json")
```

### Pattern 2: Fixing the monkeypatch stubs in tests
**What:** Two tests patch `run_inference` with a 2-arg lambda that does not accept kwargs.
The fix is to use `**kwargs` in the lambda or replace it with a proper function.
**When to use:** test_evaluate_twibot20_returns_metrics and test_evaluate_twibot20_calls_evaluate_s3.
**Example:**
```python
# Source: VERIFIED by reading test failure — evaluate_twibot20.py:196 forwards kwargs
# BROKEN (current):
monkeypatch.setattr("evaluate_twibot20.run_inference", lambda p, m: results_df)

# FIXED:
monkeypatch.setattr(
    "evaluate_twibot20.run_inference",
    lambda p, m, **kw: results_df
)
```

### Pattern 3: ablation_tables.py path override
**What:** `ablation_tables.py` hardcodes `metrics_twibot20_comparison.json` at the root.
For downstream tooling to find the artifact wherever the user chose to put it, the path
should be overridable via parameter or env var.
**When to use:** `main()` in ablation_tables.py.
**Example:**
```python
# Source: VERIFIED by reading ablation_tables.py lines 415-430
# Current (fragile):
metrics_twibot20_path = "metrics_twibot20_comparison.json"

# Hardened:
metrics_twibot20_path = os.environ.get(
    "TWIBOT_COMPARISON_PATH", "metrics_twibot20_comparison.json"
)
```
An env-var approach preserves backward compatibility (default still works from root) while
allowing Phase 12 runs from a different working directory.

### Anti-Patterns to Avoid
- **Writing to cwd without guarantee:** `open("results_twibot20.json", "w")` silently writes
  to whatever the shell cwd is. If the developer runs from a different directory, artifacts
  scatter. Use `os.path.join(output_dir, filename)` with a documented default.
- **Temp directory for normal output:** The Windows temp friction mentioned in STATE.md is
  from pytest cleanup of `TemporaryDirectory` objects, not from the production code itself.
  The production code does not use temp dirs. Do not introduce temp dirs for normal artifact
  paths. The test suite uses pytest's `tmp_path`, which pytest manages itself.
- **Patching with position-only lambdas:** `lambda p, m: ...` breaks as soon as the call
  site adds keyword arguments. Always use `**kwargs` in test stubs unless the exact
  signature is intentionally under test.

---

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Recursive directory creation | Manual mkdir chain | `os.makedirs(path, exist_ok=True)` | Already used in save_latex; consistent with existing codebase |
| Path joining on Windows | String concatenation with "/" | `os.path.join()` | Handles Windows backslash correctly; zero cost |
| Atomic JSON write | tempfile + rename | Direct `open(path, "w")` | Atomic write unnecessary for offline evaluation artifacts; adds Windows temp friction for no benefit |

**Key insight:** This is a path-hygiene phase, not an infrastructure phase. The goal is minimal
targeted changes to three specific gaps, not a rewrite of artifact management.

---

## Runtime State Inventory

> This phase does not rename or migrate any persisted state. The section is included to
> explicitly confirm there are no runtime state concerns.

| Category | Items Found | Action Required |
|----------|-------------|-----------------|
| Stored data | None — evaluation artifacts (json files) are outputs, not persisted state that needs migration | None |
| Live service config | None — no external services or registrations | None |
| OS-registered state | None — no scheduled tasks or services | None |
| Secrets/env vars | None — evaluation uses local files only | None |
| Build artifacts | None — no compiled artifacts affected | None |

---

## Common Pitfalls

### Pitfall 1: Writing comparison artifact but not aligning ablation_tables.py path
**What goes wrong:** Phase 11 introduces `output_dir` for evaluate_twibot20.py, writes
`metrics_twibot20_comparison.json` to that directory, but ablation_tables.py still looks for
it at a hardcoded `"metrics_twibot20_comparison.json"` (cwd). Table 5 continues to be skipped.
**Why it happens:** The two scripts have independent hardcoded paths; changing one without
the other leaves the consumer disconnected.
**How to avoid:** Either (a) ablation_tables.py accepts a `--twibot-comparison-path` argument
or env var, or (b) both scripts default to the same documented location (project root), and
the Phase 11 docs say to run evaluate_twibot20.py from the project root.
**Warning signs:** `[SKIP] Table 5` still appears after running evaluate_twibot20.py.

### Pitfall 2: Fixing evaluate_twibot20.py tests but breaking the __main__ block test
**What goes wrong:** test_main_block_saves_json explicitly simulates `__main__` behavior by
calling run_inference then writing to `tmp_path`. If the `__main__` block's signature or
path logic changes, this test may silently test the wrong thing.
**Why it happens:** The test does not actually invoke `__main__`; it manually replicates
what `__main__` does. A divergence between the test simulation and the real `__main__` is
undetected.
**How to avoid:** After updating `__main__`, verify the test still exercises the same code
path. If output_dir is added as a sys.argv parameter, the test should pass it explicitly.
**Warning signs:** test_main_block_saves_json passes but the real `__main__` writes to cwd.

### Pitfall 3: Two broken tests are test-code bugs, not production-code bugs
**What goes wrong:** Misreading the failure as "evaluate_twibot20 is broken" and patching the
production code when the tests are what need fixing.
**Why it happens:** The error message says `TypeError: ... got an unexpected keyword argument
'online_calibration'` at `evaluate_twibot20.py:196`, pointing at production code. But the
root cause is the test's lambda stub, not evaluate_twibot20.py.
**How to avoid:** The two failing tests (`test_evaluate_twibot20_returns_metrics`,
`test_evaluate_twibot20_calls_evaluate_s3`) both use `lambda p, m: results_df` as stubs.
The production code correctly forwards `online_calibration` and `window_size`. Fix the
lambda stubs, not the production code.
**Warning signs:** Attempting to "fix" the production evaluate_twibot20() signature to not
pass kwargs would break the 21 passing tests that exercise the online calibration path.

### Pitfall 4: Windows path separators in test assertions
**What goes wrong:** Test writes artifact to `tmp_path / "results_twibot20.json"` and
asserts with `os.path.exists()`, which works. But if any assertion uses string comparison
of path values from the comparison artifact (e.g., `comparison["path"]`), Windows
backslashes vs. forward slashes cause mismatches.
**Why it happens:** `compare_twibot20_conditions()` stores `"path": path` in its return dict.
On Windows, paths contain backslashes; forward-slash assertions in tests fail.
**How to avoid:** Use `os.path.normpath()` when comparing path strings in tests, or avoid
asserting on the `"path"` field content.

### Pitfall 5: `metrics_twibot20.json` and `results_twibot20.json` already exist from old runs
**What goes wrong:** Existing `metrics_twibot20.json` and `results_twibot20.json` at project
root were written by a previous run (before Phase 8/9 adapter fixes). They represent stale
data. If Phase 11 only introduces path parameters but does not note that a fresh run is
needed (Phase 12), downstream tooling may continue consuming stale artifacts.
**Why it happens:** Files exist; nothing forces a re-run.
**How to avoid:** Phase 11 scope is path hardening only. State explicitly in the plan that
the existing root-level json files are stale artifacts from pre-Phase-8 runs, and that fresh
artifacts are Phase 12's job. Do not delete existing files in Phase 11.

---

## Code Examples

### Current artifact writing (fragile — all hardcoded to cwd)
```python
# Source: VERIFIED by reading evaluate_twibot20.py __main__ block (lines 270-298)
out_path = "results_twibot20.json"                    # fragile: depends on cwd
metrics_path = "metrics_twibot20.json"                 # fragile: depends on cwd
comparison_path = "metrics_twibot20_comparison.json"   # fragile: depends on cwd
```

### Hardened artifact writing (Phase 11 target)
```python
# Source: VERIFIED by reading evaluate_twibot20.py + os.path stdlib
output_dir = sys.argv[3] if len(sys.argv) > 3 else "."
os.makedirs(output_dir, exist_ok=True)
out_path = os.path.join(output_dir, "results_twibot20.json")
metrics_path = os.path.join(output_dir, "metrics_twibot20.json")
comparison_path = os.path.join(output_dir, "metrics_twibot20_comparison.json")
```

### Fixed test stub (the two failing tests)
```python
# Source: VERIFIED by reading tests/test_evaluate_twibot20.py lines 267, 310
# and pytest failure output showing TypeError on online_calibration kwarg

# Before (broken — rejects kwargs forwarded by evaluate_twibot20()):
monkeypatch.setattr("evaluate_twibot20.run_inference", lambda p, m: results_df)

# After (fixed — accepts forwarded kwargs silently):
monkeypatch.setattr(
    "evaluate_twibot20.run_inference",
    lambda p, m, **kw: results_df,
)
```

### Documented entry point (for REPRO-01)
```bash
# Canonical command for both static and recalibrated artifacts
# (to be documented in evaluate_twibot20.py module docstring)
python evaluate_twibot20.py test.json trained_system_v12.joblib [output_dir]

# Produces in output_dir/:
#   results_twibot20.json         - inference results (N rows, 11 columns)
#   metrics_twibot20.json         - recalibrated-run evaluate_s3() output
#   metrics_twibot20_comparison.json - static vs recalibrated comparison dict
```

### Payload structure documentation (for REPRO-03)
```
results_twibot20.json
  Array of N objects: {account_id, p1, n1, p2, n2, amr_used, p12, stage3_used, p3, n3, p_final}

metrics_twibot20.json
  {overall: {f1, auc, precision, recall},
   per_stage: {p1: {...}, p2: {...}, p12: {...}, p_final: {...}},
   routing: {pct_stage1_exit, pct_stage2_exit, pct_stage3_exit, pct_amr_triggered}}

metrics_twibot20_comparison.json
  {path, model_path, threshold, window_size,
   conditions: {static: <metrics dict>, recalibrated: <metrics dict>},
   delta_overall: {f1, auc, precision, recall}}
```

---

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Single-condition TwiBot eval | Static vs recalibrated comparison via compare_twibot20_conditions() | Phase 10 | comparison artifact is now the canonical output |
| Demographic-proxy Stage 1 mapping | Behavioral tweet-type adapter (RT/MT/original) | Phase 8 | existing json files are stale |
| No online calibration | Sliding-window novelty percentile recalibration toggle | Phase 9 | online_calibration kwarg added to run_inference |

**Deprecated/outdated:**
- `results_twibot20.json` and `metrics_twibot20.json` at project root: written by a
  pre-Phase-8 run; do not consume for paper evidence until Phase 12 regenerates them.
- `metrics_twibot20_comparison.json`: does not yet exist; is the primary missing artifact
  Phase 11 must unblock.

---

## Environment Availability

| Dependency | Required By | Available | Version | Fallback |
|------------|------------|-----------|---------|----------|
| Python | Everything | Yes | 3.13 (inferred from .pyc filenames) | — |
| pytest | Test suite | Yes | 8.3.4 | — |
| test.json | run_inference() | Yes | present at project root | — |
| trained_system_v12.joblib | run_inference() | Yes | present at project root | — |
| metrics_twibot20_comparison.json | ablation_tables.py Table 5 | No | — | Phase 11 writes it |

**Missing dependencies with no fallback:**
- None that would block Phase 11 execution.

**Missing dependencies with fallback:**
- `metrics_twibot20_comparison.json`: absent, but Phase 11 writes it as part of its work.
  ablation_tables.py already has a graceful skip for its absence.

---

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.3.4 |
| Config file | none (uses defaults) |
| Quick run command | `python -m pytest tests/test_evaluate_twibot20.py -x --tb=short -q` |
| Full suite command | `python -m pytest tests/ --tb=no -q` |

### Current Test State (pre-Phase-11)
**Verified:** 2 failing tests in test_evaluate_twibot20.py; 109 total passing; 111 total.
```
FAILED tests/test_evaluate_twibot20.py::test_evaluate_twibot20_returns_metrics
FAILED tests/test_evaluate_twibot20.py::test_evaluate_twibot20_calls_evaluate_s3
```
[VERIFIED: `python -m pytest tests/ --tb=no -q` output]

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| REPRO-01 | Entry point produces static+recalibrated artifacts in documented location | smoke | `python -m pytest tests/test_evaluate_twibot20.py -k "main" -x -q` | Partial (test_main_block_saves_json exists; needs output_dir update) |
| REPRO-02 | No fragile cwd-relative artifact writes | unit | `python -m pytest tests/test_evaluate_twibot20.py -x -q` (all pass) | Yes — after fixing 2 failing stubs |
| REPRO-03 | Artifact filenames and payload structures documented | manual | inspect module docstring + artifact schema comment | No — docstring update needed |

### Sampling Rate
- **Per task commit:** `python -m pytest tests/test_evaluate_twibot20.py -x --tb=short -q`
- **Per wave merge:** `python -m pytest tests/ --tb=no -q`
- **Phase gate:** all tests in tests/ pass (currently 2 failing; both must be green)

### Wave 0 Gaps
- The two failing tests are pre-existing failures that Phase 11 must fix as part of its scope. No new test files are needed.
- No Wave 0 infrastructure gaps (pytest is installed, conftest.py is in place).

---

## Security Domain

Phase 11 involves only local file path management and test fixture repair. There are no authentication, session, access control, cryptography, or input validation surfaces introduced. Security domain is not applicable to this phase.

---

## Assumptions Log

| # | Claim | Section | Risk if Wrong |
|---|-------|---------|---------------|
| A1 | The two failing tests are test-code bugs (lambda stub too narrow), not production bugs | Common Pitfalls, Code Examples | If wrong: production code is actually broken in a way that must be fixed before tests can pass |
| A2 | Windows temp friction in STATE.md refers to pytest cleanup of TemporaryDirectory, not to production code | Summary | If wrong: production code itself uses a fragile temp path that needs fixing |
| A3 | The three json artifact filenames (results_twibot20.json, metrics_twibot20.json, metrics_twibot20_comparison.json) are the stable canonical names Phase 12 and Phase 13 should consume | Code Examples | If wrong: filenames need renaming, which would also affect ablation_tables.py path |

**A1 rationale:** The test failure is `TypeError: ... got an unexpected keyword argument 'online_calibration'` inside a monkeypatched stub. The lambda `lambda p, m: results_df` is the stub — it does not accept kwargs. The production `evaluate_twibot20()` function signature correctly includes `online_calibration` and `window_size` and forwards them. The 21 passing tests all use the four-patch pattern with separate `patch` context managers (not bare lambdas for `run_inference`), confirming the production code itself works. [VERIFIED: pytest run + reading failing test at line 267]

**A2 rationale:** grep of evaluate_twibot20.py, ablation_tables.py, twibot20_io.py found no `tempfile` or `gettempdir` usage in production code. The temp paths in Windows `AppData/Local/Temp` appear only in the pytest `tmp_path` fixture path shown in test failure output. [VERIFIED: grep -n tempfile on all three files returned zero results]

---

## Open Questions

1. **Should `ablation_tables.py` consume `output_dir` via env var or CLI argument?**
   - What we know: It hardcodes `"metrics_twibot20_comparison.json"` at line 415.
   - What's unclear: Whether Phase 11 changes ablation_tables.py at all, or whether the
     documented convention is "always run evaluate_twibot20.py from the project root, which
     is the default".
   - Recommendation: The simplest fix for REPRO-01 is to document that the canonical
     command is run from the project root (both scripts default to `"."`). Only add env-var
     override if Phase 12 or Phase 13 needs to run from a different directory.

2. **Should `__main__` write `metrics_twibot20.json` from the recalibrated run specifically,
   or should it write one file per condition?**
   - What we know: The current `__main__` calls `run_inference()` (which defaults to
     `online_calibration=True`), then saves `metrics_twibot20.json`. It also calls
     `compare_twibot20_conditions()` which saves `metrics_twibot20_comparison.json` for both
     conditions. There is no separate `metrics_twibot20_static.json`.
   - What's unclear: Whether REPRO-03 requires per-condition metric files or whether the
     comparison JSON is sufficient for downstream tooling.
   - Recommendation: The comparison JSON already contains both conditions' full metrics.
     A per-condition split is not needed unless ablation_tables.py or paper scripts require
     it. Keep current structure.

---

## Sources

### Primary (HIGH confidence)
- `evaluate_twibot20.py` (full read) — confirmed all artifact paths, entry point, run_inference signature
- `ablation_tables.py` (full read) — confirmed metrics_twibot20_comparison.json dependency
- `tests/test_evaluate_twibot20.py` (full read) — confirmed 2 failing tests, root cause
- `pytest -m pytest tests/ --tb=no -q` (live run) — confirmed 2 failed, 109 passed, 111 total
- `python -c "import os; print(os.path.exists(...))"` — confirmed missing comparison artifact
- `.planning/REQUIREMENTS.md` — REPRO-01/02/03 text
- `.planning/workstreams/milestone/STATE.md` — Windows temp friction note
- `grep -n "tempfile\|gettempdir"` on production files — confirmed zero temp usage in production code

### Secondary (MEDIUM confidence)
- `.planning/workstreams/milestone/phases/10-cross-domain-evaluation-and-paper-output/10-CONTEXT.md`
  — D-06/D-07 artifact strategy decisions from Phase 10
- `.planning/workstreams/milestone/phases/10-cross-domain-evaluation-and-paper-output/10-02-SUMMARY.md`
  — confirmed what Phase 10 built and what remains

---

## Metadata

**Confidence breakdown:**
- Gap identification: HIGH — verified by running pytest and file checks
- Root cause of failing tests: HIGH — read failure trace and test source
- Missing artifact cause: HIGH — read __main__ block and confirmed file absence
- Proposed fix approach: HIGH — stdlib os.path patterns, no new libraries
- Scope boundaries (what NOT to do): HIGH — Phase 12 owns fresh data runs

**Research date:** 2026-04-18
**Valid until:** Stable — only changes if evaluate_twibot20.py or test suite is modified
