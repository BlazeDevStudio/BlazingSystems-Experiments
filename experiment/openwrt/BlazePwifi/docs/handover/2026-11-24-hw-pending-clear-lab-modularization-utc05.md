# PHX-HARDWARE UTC05 — pending-clear/quarantine lab modularization

**Role:** PHX-HARDWARE  
**Task:** #177 / #266 / #349  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Parent/base:** #347 `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Source/test commit:** `1247a5c7b332677ae8dca83dc94cf586a015e7a0`  
**Pre-handover docs parent:** `1247a5c7b332677ae8dca83dc94cf586a015e7a0`  
**PR:** https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349

## Scope and change

A cleanup-first, behavior-preserving split of the pending-journal/quarantine host lab:

- Added `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/pending_clear_failure_lab_fixtures.py`.
- Reduced `pending_clear_failure_lab.py` from 22,494 to 12,052 characters (10,442 characters / 46.4% removed from the orchestration file).
- Moved the five C++ fixture constants unchanged: `CLEAR_PENDING_STUBS`, `CLEAR_PENDING_MAIN`, `BOOT_ORPHAN_ATTEMPT_MAIN`, `QUARANTINE_PENDING_STUBS`, and `QUARANTINE_PENDING_MAIN`.
- The runner imports those fixtures and retains its source-exact extraction, append-failure, clear-failure, attempt-marker and fail-open mutation cases.
- Read-back comparison verified all five original fixture strings are present byte-for-byte in the new module, all five names are imported, the runner and mutation anchors remain present.

This is a test-harness organization change only. No production `.ino`, controller API, schema, finance, signer, witness, GPIO or relay behavior changed. The host adapters remain SIMULATED and do not prove LittleFS power-loss durability.

## Exact commits

- Fixture module addition: `8b5a9bfe28a6852c3fb0d492332b4c4188d787f5`
- Orchestration import/refactor: `1247a5c7b332677ae8dca83dc94cf586a015e7a0`

## CI at source/test SHA `1247a5c7`

- Quarantine Byte Readback [run #45335896662](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45335896662), job `138247764396`: **IN_PROGRESS at checkpoint time**. No pass is claimed.
- Relay Output Polarity [run #45335896640](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45335896640): source/output job `138247764534` **PASS**; ESP32 boot job `138247764983` **PASS**.
- Full BlazePwifi [run #45335896670](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45335896670): validation job `138247765213` **FAIL** at the inherited `Missing poll signature check`. All 13/13 firmware target/platform jobs completed **PASS**. Android was still running at checkpoint time. Validation-dependent simulation/update/signing/publication jobs were skipped.

The Full failure is the existing producer/consumer contract mismatch, not caused by this fixture split. Current main CGI blob `2e3a1430d08cc6606429a042df3b5848f53c7267` emits no `response_sig` for register/ping or poll. PHX-CORE owns the authenticated producer contract and canonical golden vectors; PHX-QA owns assertion reconciliation. Hardware must not invent a signature or weaken default-deny.

## Revalidated parallel audit leads

- PR #283 remains a separate OPEN/DRAFT stack at `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`. Both sketches guard `clearPending()` behind successful `appendQuarantineRecord()`, but `quarantinePending()` is definition-only with no active callsite. The original unconditional-clear pattern is absent in this snapshot; the lifecycle is not end-to-end accepted.
- PR #283's `response_sig` mentions are explanatory comments only. Current main register/poll responses remain unsigned for controller authority. Keep the consumer deny-only.
- PR #239 remains OPEN/DRAFT at `d83b715b116185107737fef721c2eece8feebf39`; PR #254 remains OPEN/DRAFT at `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`. Do not rebase, merge or retarget these stacks.

## Evidence boundary and next action

- Test-harness refactor: committed; exact GitHub read-back verified.
- Relay lab: CI VERIFIED at source/test SHA.
- Quarantine lab: pending at checkpoint time; final exact-head result must be recorded after completion.
- Full integration: FAILED at the inherited poll-signature assertion.
- Physical coin/relay/electrical acceptance, LittleFS power cuts, 150 controlled cuts and 30-device/24-hour soak: NOT TESTED.
- HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.

**Next:** finish the exact-head Quarantine run, then rerun focused workflows on the final PR/docs HEAD; Master must refresh its stale #349 source/test/docs pins, while CORE/QA resolve the authenticated register/poll contract. No hardware flash, device reset, live money, migration, merge, release or deployment was performed.
