# PHX-HARDWARE handover — pending-journal lab reuses the shared lexical extractor

**Date:** 2026-11-20 UTC15  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test commit:** `53243577ca145e90efa40eeadb536f1737933f6f`

## Selected cleanup-first task

The Hardware-owned `pending_journal_recovery_lab.py` contained a local C++ function extractor that searched for the first brace and counted raw braces. It could truncate an extracted production function when a `}` appeared inside an ordinary string, C++ raw string, line comment, or block comment. The same repository already had a shared lexical-aware extractor in `firmware_lab_source.py`, used by other Hardware-owned labs.

This was a test-harness integrity issue: a truncated source function could make the journal recovery lab validate an incomplete body.

## Test-first reproduction

- RED test commit: [`acb908cc5f2e74cc4938eca1fada6998b0785247`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/acb908cc5f2e74cc4938eca1fada6998b0785247).
- Quarantine push [#44765324968](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44765324968), job `136388278128`: **EXPECTED FAILURE** at `PENDING_JOURNAL_EXTRACTOR_FAIL: ordinary string brace truncated target()`. The prior poll-fault suites completed before the new fixture failed.
- The fixture covers ordinary strings, C++ raw strings, line comments and block comments.

## Correction

- Removed the local raw-brace counter.
- Added the ESP8266 Hardware lab directory to `sys.path` and imported `extract_block` / `extract_function` from `firmware_lab_source.py`.
- Kept a small signature adapter: struct extraction delegates to `extract_block`; function extraction resolves the function name and delegates to `extract_function`.
- Retained the four-case fixture as a permanent regression.
- Preserved the existing `re` use for reading the actual `PENDING_MAGIC` constant.

Only this Hardware-owned host lab changed. No production `.ino`, shared protocol/API, financial ledger, persistence schema, QA-owned test, Release-owned workflow, or COE destination changed.

## Exact-head focused validation

At source/test SHA `53243577ca145e90efa40eeadb536f1737933f6f`:

- Quarantine/readback push [#44765440712](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44765440712), job `136388693179`: **SUCCESS**; literal checkout SHA verified.
- Log markers include `PENDING_JOURNAL_LEXICAL_EXTRACTOR_PASS 4/4`.
- Both board runs report `PENDING_JOURNAL_LAB_PASS 16/16` and `PENDING_CLEAR_LAB_PASS 17/17`.
- Existing pending-attempt-marker, pulse-capture, poll-loop-inhibit, EEPROM/config-read and boot-polarity labs in the same job also pass; pulse capture reports `16/16` on ESP8266 and ESP32.
- The workflow explicitly reports `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`.

Full BlazePwifi push [#44765440815](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44765440815), validation job `136388855976`: **FAILED** at the inherited QA-owned `Missing poll signature check` in `tests/controllers.sh`. At the last read, several independent target jobs were still in progress; this is not a Full validation pass and no target-matrix completion is claimed here.

## Evidence classification and limitations

- Lexical extraction fixture: **CI VERIFIED**.
- Journal recovery / pending-clear / poll and pulse host tests: **SIMULATED / CI VERIFIED**.
- Physical LittleFS/EEPROM durability, coin acceptor pulse conditioning, relay polarity, electrical recovery, 150 controlled power cuts and 30-device/24-hour soak: **NOT TESTED**.
- Protected anti-rollback signer/witness, v1-to-v2 migration, durable accounting/replay and independent QA/release signoff: **NOT ESTABLISHED**.
- **HARDWARE ACCEPTED:** NO. **PRODUCTION READY:** NO-GO.

## Coordination and next action

- **PHX-QA** owns the inherited positive poll-signature assertion. Replace it with source-exact negative/default-deny validation; do not invent a positive `response_sig` or weaken firmware admission.
- **PHX-CORE** owns the canonical authenticated register/poll and event-bound receipt contract.
- **PHX-MASTER** owns `coordination/phoenix/ROLE_ASSIGNMENTS.md`; its #327 active-head entry is stale and must be refreshed to the current PR head after this handover commit. Preserve the #326 → #327 ancestry.
- **PHX-HARDWARE** should continue with the next bounded ESP32/ESP8266-owned task after revalidating the live stack. No physical test, flash, migration, merge or release is authorized by this handover.
