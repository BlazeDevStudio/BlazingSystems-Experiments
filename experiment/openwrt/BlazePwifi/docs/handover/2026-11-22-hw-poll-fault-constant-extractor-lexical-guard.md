# PHX-HARDWARE — poll-fault constant extractor lexical guard

**Date:** 2026-11-22 UTC07  
**Role:** PHX-HARDWARE  
**Task:** #172 / #177 / #266 / #327  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base #326:** `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test SHA:** `3179ef0317240856acac82377d4be4ec3ce4b83a`

## Defect

The Hardware-owned `poll_fault_dual_store_lab_fixtures.py:constants()` helper selected one-line `static const` declarations using raw `str.startswith()` and substring matching. It could import declarations that existed only inside a block comment or C++ raw-string body, and could mistake an identifier containing a requested constant name as the requested declaration.

That is a fixture-integrity defect: a decoy could alter the generated host harness even though it was not active C++ code.

## Test-first reproduction

- Test-only commit: [`0c9ad737`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/0c9ad73741b97adea7aff84c7ad1e8def4d9d8f4).
- Expected RED: [Quarantine push run #44999721675](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44999721675), job `137138368330`, FAILURE at `test_constants_extract_only_active_declarations`.
- The failing output contained nine selected lines: two block-comment decoys, two raw-string decoys, the alias `NOT_POLL_FAULT_EEPROM_OFFSET_ALIAS`, and the four real declarations. This confirms the old helper's false-positive.

## Correction

- Source/test commit: [`3179ef03`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/3179ef0317240856acac82377d4be4ec3ce4b83a).
- `constants()` now calls the existing `mask_non_code()` helper, preserves original declaration text, checks line-count preservation, and matches requested identifiers with word boundaries.
- The regression covers active declarations, block-comment decoys, raw-string decoys and a substring-alias decoy. No firmware `.ino`, runtime behavior, pin, GPIO, relay, controller contract, financial source, QA-owned assertion or Release workflow changed.

## Exact-source GREEN

[Quarantine push run #44999815392](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44999815392), job `137138659665`: **SUCCESS** on exact source/test SHA `3179ef0317240856acac82377d4be4ec3ce4b83a`.

Log marker: `POLL_FAULT_CONSTANT_EXTRACTION_NON_CODE_DECOYS_REJECTED 4/4`.

The same job also completed the existing ESP32/ESP8266 dual-store, EEPROM lifecycle, NVS commit/readback, LittleFS mount, poll-loop, pulse-capture, boot-polarity and mutation-rejection labs. Those are source-extracted host simulations; they do not emulate flash physics or physical coin/relay behavior.

## Full integration

[BlazePwifi build run #44999815361](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44999815361) completed **FAILURE**:
- Validation job `137138673360` failed at the inherited QA-owned `Missing poll signature check` in `tests/controllers.sh`.
- All 14/14 firmware/platform target jobs, including ESP8266 and ESP32, completed SUCCESS.
- Browser, x86, Ruijie, Orange Pi, ESP simulations, candidate gate, signing and publication were SKIPPED after validation failed.

Hardware did not change the QA assertion or invent a `response_sig`. The main controller register/poll producer still lacks the approved authenticated response contract. Keep controller configuration, coin admission, coin POST disposition and relay enable fail-closed until PHX-CORE publishes the contract and PHX-QA independently verifies it.

## Evidence classification

- Constant-extractor regression: **CI VERIFIED**.
- Dual-store / poll / pulse host labs: **SIMULATED + CI VERIFIED**.
- Exact Full integration: **FAILED / BLOCKED**.
- Physical EEPROM/flash durability: **NOT TESTED**.
- Physical coin pulse / relay / electrical recovery: **NOT TESTED**.
- 150 controlled power cuts: **NOT TESTED**.
- 30-device / 24-hour soak: **NOT TESTED**.
- HARDWARE ACCEPTED: **NO**.
- PRODUCTION READY: **NO-GO**.

## BLAZE-COMMS/1

```json
{
  "protocol": "BLAZE-COMMS/1",
  "message_id": "PHX-HARDWARE-20261122T07-POLL-FAULT-CONSTANT-LEXER",
  "from": "PHX-HARDWARE",
  "to": ["PHX-MASTER", "PHX-QA"],
  "type": "DONE",
  "priority": "P2",
  "task_id": "#172/#177/#266/#327",
  "branch": "phoenix/hardware-prepoll-edge-abort-20261119",
  "base_sha": "58c558fb6a237935214621adc3dee65a10fe1a51",
  "scope": [
    "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_fault_dual_store_lab.py",
    "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_fault_dual_store_lab_fixtures.py"
  ],
  "status": "VERIFIED",
  "evidence": [
    "RED commit 0c9ad73741b97adea7aff84c7ad1e8def4d9d8f4; Quarantine #44999721675 job 137138368330 failed at the expected decoy assertion",
    "GREEN source/test SHA 3179ef0317240856acac82377d4be4ec3ce4b83a; Quarantine #44999815392 job 137138659665 SUCCESS; marker POLL_FAULT_CONSTANT_EXTRACTION_NON_CODE_DECOYS_REJECTED 4/4",
    "Full #44999815361 validation job 137138673360 fails at inherited QA-owned Missing poll signature check; 14/14 target jobs PASS; downstream candidate/signing/publication SKIPPED"
  ],
  "blockers": [
    "Authenticated register/poll and event-bound receipt contract pending PHX-CORE",
    "Independent behavioral/golden-vector poll verification pending PHX-QA",
    "Physical EEPROM, pulse, relay, power-cut and 30-device soak acceptance NOT TESTED",
    "Private Google Drive registry v11 unavailable through the exposed connector surface"
  ],
  "next_action": "PHX-MASTER refresh the stale #327 branch pin; PHX-CORE/QA resolve the authenticated poll contract and independent assertions; PHX-HARDWARE retain default-deny and revalidate exact heads next activation.",
  "updated_utc": "2026-11-22T07:50:00Z"
}
```

No merge, rebase, force-push, flash, reset, signing, payment, migration, release tag or deployment was performed.
