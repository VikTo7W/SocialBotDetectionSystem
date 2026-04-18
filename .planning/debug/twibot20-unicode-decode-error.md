---
slug: twibot20-unicode-decode-error
status: resolved
trigger: UnicodeDecodeError when running evaluate_twibot20.py
created: 2026-04-17
updated: 2026-04-17
---

## Symptoms

- **Expected:** Pipeline runs end-to-end via `python evaluate_twibot20.py`
- **Actual:** UnicodeDecodeError crash
- **Error:**
  ```
  File "c:\Users\dzeni\PycharmProjects\SocialBotDetectionSystem\evaluate_twibot20.py", line 132, in <module>
      results = run_inference(data_path, model_path)
    File "c:\Users\dzeni\PycharmProjects\SocialBotDetectionSystem\evaluate_twibot20.py", line 56, in run_inference
      accounts_df = load_accounts(path)
    File "c:\Users\dzeni\PycharmProjects\SocialBotDetectionSystem\twibot20_io.py", line 32, in load_accounts
      data = json.load(f)
    File "E:\Anaconda\Lib\json\__init__.py", line 293, in load
      return loads(fp.read(),
  UnicodeDecodeError: 'utf-8' codec can't decode byte 0xff in position 0: invalid start byte
  ```
- **Timeline:** Always (new script, never worked)
- **Reproduction:** `python evaluate_twibot20.py`

## Current Focus

hypothesis: RESOLVED
test: n/a
expecting: n/a
next_action: n/a

## Evidence

- timestamp: 2026-04-17
  observation: twibot20_io.py lines 31 and 75 both used `open(path, "r", encoding="utf-8")`
  conclusion: hardcoded UTF-8 cannot read a UTF-16 encoded file

- timestamp: 2026-04-17
  observation: evaluate_twibot20.py line 67 also used `open(path, "r", encoding="utf-8")`
  conclusion: same problem in a third call site

- timestamp: 2026-04-17
  observation: 0xff at position 0 is the UTF-16 LE BOM (\xff\xfe)
  conclusion: file is UTF-16 LE encoded; Python's `utf-16` codec auto-detects and strips the BOM

- timestamp: 2026-04-17
  observation: test fixtures in test_twibot20_io.py and test_evaluate_twibot20.py write JSON as UTF-8
  conclusion: fix must handle both encodings transparently; hardcoding utf-16 would break tests

## Eliminated

- chardet dependency: not needed; BOM sniffing is zero-dependency and deterministic

## Resolution

root_cause: All three `open()` calls in twibot20_io.py (lines 31, 75) and evaluate_twibot20.py (line 67) hardcoded `encoding="utf-8"`, but the real test.json file is UTF-16 LE encoded (0xff 0xfe BOM at byte 0).
fix: Added `_detect_encoding(path)` helper to twibot20_io.py that reads the first 2 bytes; returns "utf-16" on a UTF-16 BOM, "utf-8" otherwise. Replaced all three `encoding="utf-8"` arguments with `encoding=_detect_encoding(path)`. Exported the helper and imported it in evaluate_twibot20.py.
verification: All 13 existing tests in test_twibot20_io.py pass (UTF-8 fixture files still work). Smoke test confirmed _detect_encoding correctly identifies both UTF-16 LE and plain UTF-8 files.
files_changed: twibot20_io.py, evaluate_twibot20.py
