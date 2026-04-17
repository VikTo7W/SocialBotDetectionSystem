# Phase 9: Zero-Shot Inference Pipeline - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 09-zero-shot-inference-pipeline
**Areas discussed:** Script structure, Column mapping, Results output, account_id source

---

## Script Structure

| Option | Description | Selected |
|--------|-------------|----------|
| Module + `__main__` | `run_inference(path, model_path)` importable by Phase 10; `__main__` for manual runs | ✓ |
| Script only | Standalone `__main__` only; Phase 10 would need subprocess | |
| Module only | Importable function, no direct run capability | |

**User's choice:** Module + `__main__`
**Notes:** Phase 10 imports `run_inference()` directly — no subprocess dependency between phases.

---

## Column Mapping

| Option | Description | Selected |
|--------|-------------|----------|
| Map statuses_count → submission_num | Closest analog (tweet count ≈ post-activity proxy) | ✓ |
| Zero it too | Treat all Reddit activity columns as absent (purist zero-shot) | |

**User's choice:** Yes, map statuses_count to submission_num
**Notes:** comment_num_1, comment_num_2, subreddit_list still zero-filled. Ratio clamping handles Stage 1 blowup.

---

## Results Output

| Option | Description | Selected |
|--------|-------------|----------|
| Return DataFrame + save JSON | run_inference() returns DataFrame; __main__ saves results_twibot20.json | ✓ |
| Return DataFrame only | Clean but no audit trail | |
| Save to CSV + print | Phase 10 reads CSV; adds file I/O dependency | |

**User's choice:** Return DataFrame + save JSON
**Notes:** Phase 10 uses the imported function; JSON is for human inspection only.

---

## account_id Source

| Option | Description | Selected |
|--------|-------------|----------|
| Twitter ID (record['ID']) | Canonical stable identifier (e.g. '12345') | ✓ |
| screen_name | Human-readable handle; not guaranteed unique | |

**User's choice:** Twitter ID (record['ID'])
**Notes:** Matches Phase 10's ground-truth join key.

---

## Claude's Discretion

- Threshold: use `sys.th` from loaded model (no override)
- Print summary after saving JSON: Claude decides

## Deferred Ideas

None.
