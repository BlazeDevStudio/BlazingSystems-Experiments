# PHX-HARDWARE — inactive-preprocessor constant extraction guard

**Date:** 2026-11-22 UTC08  
**Role:** PHX-HARDWARE  
**Task:** #172 / #177 / #266 / #327  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base #326:** `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test SHA:** `22c99de65a461fec2e4b10b1272c5f5afd37b3ea`  
**Documentation-only follow-up before this handover:** `444f0e973a3e9240463ed2b8d95ffbfe0a94d3b7`

## Defect

The Hardware-owned `poll_fault_dual_store_lab_fixtures.py:constants()` extractor already masked comments and C++ string/character literals and used identifier boundaries. It still selected `static const` lines inside preprocessor branches that are provably inactive, such as `#if 0`, nested under other conditionals, or the `#else` side of `#if 1`.

That is a host-fixture integrity defect: a disabled declaration could be selected as if it were a live source constant. No production firmware runtime defect is claimed.

## Test-first reproduction

- Test-only commit: [`429541636e154028723d257c9677d1941c54d8c7`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/429541636e154028723d257c9677d1941c54d8c7).
- Expected RED: [Quarantine run #45004439976](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45004439976), job `137152771297`, FAILURE at `test_constants_extract_only_active_declarations`.
- The failing result selected disabled declarations for MAGIC, VERSION, OFFSET and EEPROM_BYTES in addition to the four active declarations. The test includes a nested `#if 1` inside `#if 0`, a literal `#elif 0`, an active `#else` branch, and a decoy in the `#else` side of `#if 1`.

## Correction

- Final source/test implementation: [`22c99de65a461fec2e4b10b1272c5f5afd37b3ea`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/22c99de65a461fec2e4b10b1272c5f5afd37b3ea).
- `constants()` now applies the existing lexical `mask_non_code()` and then a bounded preprocessor mask.
- The mask excludes branches known inactive from literal `#if/#elif 0` and `#if/#elif 1` conditions, including nested conditionals; it preserves source length, line count and original declaration text.
- Unknown macro expressions are deliberately kept conservatively visible. This is not a full C/C++ preprocessor and does not evaluate build-specific macro definitions or line-spliced directives.
- No production `.ino` sketch, GPIO, relay, controller API, financial code, signer/witness, QA-owned assertion or Release workflow was changed.
- Intermediate implementation commits were corrected before the final GREEN run; the final accepted source/test SHA is the one above.

## Exact-source GREEN

[Quarantine run #45004957249](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45004957249), job `137154355443`: **SUCCESS**, exact head `22c99de65a461fec2e4b10b1272c5f5afd37b3ea`.

Log markers:
- `POLL_FAULT_CONSTANT_EXTRACTION_NON_CODE_DECOYS_REJECTED 4/4`
- `POLL_FAULT_CONSTANT_EXTRACTION_PREPROCESSOR_INACTIVE_REJECTED 4/4`

The same focused job ran the existing dual-store, EEPROM lifecycle/config-read recovery, NVS, LittleFS mount, poll-drain, ISR edge reconciliation, pulse-capture and boot-polarity host labs. All were source-extracted/fake-backend tests; the logs retain `SIMULATED_ONLY=1` and physical acceptance flags at zero.

[Relay Output Polarity run #45004957285](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45004957285): **SUCCESS**, exact head `22c99de65a461fec2e4b10b1272c5f5afd37b3ea`; jobs `137154355798` (ESP32 boot polarity) and `137154356029` (source/output polarity) succeeded.

## Full integration

BlazePwifi build run [#45004957339](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45004957339) was **PENDING** at the last readback. No terminal Full result is claimed for this activation.

The previously observed Full blocker remains the inherited QA-owned `Missing poll signature check` in `tests/controllers.sh`. The main register/poll producer still lacks the approved authenticated response contract. Hardware did not invent `response_sig`, add a positive admission path, or weaken default-deny.

## Evidence classification

- Inactive-preprocessor extractor regression: **CI VERIFIED**.
- Dual-store, EEPROM, poll/ISR and pulse host labs: **SIMULATED + CI VERIFIED**.
- Full integration for this exact head: **PENDING at last readback; no acceptance claim**.
- Physical EEPROM/flash durability: **NOT TESTED**.
- Physical coin pulse, relay and electrical recovery: **NOT TESTED**.
- 150 controlled power cuts: **NOT TESTED**.
- 30-device / 24-hour soak: **NOT TESTED**.
- HARDWARE ACCEPTED: **NO**.
- PRODUCTION READY: **NO-GO**.

## BLAZE-COMMS/1

```json
{
  "protocol": "BLAZE-COMMS/1",
  "message_id": "PHX-HARDWARE-20261122T08-PREPROCESSOR-INACTIVE-CONSTANT-EXTRACTION",
  "from": "PHX-HARDWARE",
  "to": ["PHX-MASTER", "PHX-QA", "PHX-CORE"],
  "type": "DONE",
  "priority": "P2",
  "task_id": "#172/#177/#266/#327",
  "branch": "phoenix/hardware-prepoll-edge-abort-20261119",
  "base_sha": "58c558fb6a237935214621adc3dee65a10fe1a51",
  "scope": [
    "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_fault_dual_store_lab.py",
    "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_fault_dual_store_lab_fixtures.py",
    "experiment/openwrt/BlazePwifi/docs/handover/2026-11-22-hw-preprocessor-inactive-constant-extraction.md"
  ],
  "status": "VERIFIED",
  "evidence": [
    "RED #45004439976 job 137152771297 failed at the expected inactive-branch decoy assertion on test-only commit 429541636e154028723d257c9677d1941c54d8c7",
    "GREEN Quarantine #45004957249 job 137154355443 SUCCESS on source/test SHA 22c99de65a461fec2e4b10b1272c5f5afd37b3ea with both 4/4 extractor markers",
    "Relay #45004957285 jobs 137154355798 and 137154356029 SUCCESS on the same source/test SHA",
    "Full build #45004957339 pending at last readback; no Full acceptance claimed"
  ],
  "blockers": [
    "CORE authenticated register/poll and event-bound receipt contract pending",
    "QA independent poll golden vectors and inherited Full poll-signature fixture resolution pending",
    "Physical EEPROM, coin pulse, relay, electrical, 150 power-cut and 30-device soak acceptance NOT TESTED",
    "Private Google Drive v11 registry not available through the exposed connector surface"
  ],
  "next_action": "PHX-MASTER refresh exact #327 pins; PHX-CORE/QA resolve the authenticated poll contract; PHX-HARDWARE revalidate exact heads and continue with the next unblocked owned defect.",
  "updated_utc": "2026-11-22T08:56:00Z"
}
```

No merge, rebase, force-push, flash, reset, signing, payment, migration, release tag or deployment was performed.
