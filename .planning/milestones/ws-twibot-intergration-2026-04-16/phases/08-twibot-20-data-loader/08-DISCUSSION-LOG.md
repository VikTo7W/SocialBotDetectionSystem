# Phase 8: TwiBot-20 Data Loader - Discussion Log

> **Audit trail only.** Do not use as input to planning, research, or execution agents.
> Decisions are captured in CONTEXT.md — this log preserves the alternatives considered.

**Date:** 2026-04-16
**Phase:** 08-twibot-20-data-loader
**Areas discussed:** messages dict structure, created_at representation, Validation output

---

## messages dict structure

| Option | Description | Selected |
|--------|-------------|----------|
| Full compat dict | `{text: str, ts: None, kind: 'tweet'}` — matches botsim24_io schema; ts=None already handled in stage2 | ✓ |
| Minimal dict | `{text: str}` only — smaller footprint, diverges from botsim24_io pattern | |
| You decide | Leave internal dict structure to Claude's discretion | |

**User's choice:** Full compat dict
**Notes:** Maintains schema compatibility with `features_stage2.py` which already handles `ts=None`.

---

## created_at representation

| Option | Description | Selected |
|--------|-------------|----------|
| Raw string | Keep Twitter date string as-is — column unused in temporal features | ✓ |
| Parsed Unix timestamp | Parse to float — consistent with botsim24_io, enables future account-age features | |

**User's choice:** Raw string
**Notes:** Twitter's non-standard date format ('Mon Apr 23 09:47:10 +0000 2012') makes parsing non-trivial; column is not used in TwiBot-20 inference.

---

## Validation output

| Option | Description | Selected |
|--------|-------------|----------|
| print() statements | Simple, consistent with no-logging codebase | ✓ |
| logging module | Suppressable, redirectable — first use of logging in codebase | |
| Return as dict | Clean API, caller decides output — adds burden on caller | |

**User's choice:** print() statements
**Notes:** Codebase currently has no logging module usage; print() keeps it consistent.

---

## Claude's Discretion

- Internal ID→node_idx mapping implementation (dict lookup)
- Handling of missing/None profile values for numeric columns
- Whether validate() is standalone function or method

## Deferred Ideas

None.
