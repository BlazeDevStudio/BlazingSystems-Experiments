# PHX-HARDWARE handover — strict dual-store board fixture dispatch

**Date:** 2026-11-21 UTC06  
**Role:** PHX-HARDWARE  
**Task:** #266 cleanup-first / #177 firmware regression support  
**PR:** [#327 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test fix commit:** `ded516fc0234b380c1daefacad3d6e2268f2f10b`

## Defect

The Hardware dual-store lab fixture dispatcher used `if board == "ESP32": ... else: ...`. Any typo, unknown identifier, or case mismatch silently selected the ESP8266 EEPROM backend. A test invocation could therefore report a successful run against the wrong persistence model.

This was a host-lab dispatch defect, not a production firmware defect.

## Test-first reproduction

- Test-only commit: [`8981ee61302f4917738a10269921aa0469c546b6`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/8981ee61302f4917738a10269921aa0469c546b6)
- RED workflow: [Quarantine run #44877397024](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44877397024), job `136765016786`.
- Expected failure: `unknown board label silently selected the ESP8266 persistence backend`.

## Correction

- Added an explicit allow-list for exactly `ESP32` and `ESP8266` at the `harness()` boundary.
- Unknown labels raise `ValueError` and identify the rejected value.
- Added `test_unknown_board_identifier_fails_closed()` to the existing exact-source dual-store lab.
- No production `.ino`, GPIO, financial interface, controller response, signer, witness, QA-owned test, or Release workflow changed.

## Exact-source GREEN evidence

Fix SHA: `ded516fc0234b380c1daefacad3d6e2268f2f10b`.

- Quarantine: [run #44877478277](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44877478277), job `136765261311`, SUCCESS. Log includes `POLL_FAULT_UNKNOWN_BOARD_REJECTED`, `POLL_FAULT_DUAL_STORE_LAB=PASS board=ESP32`, and `POLL_FAULT_DUAL_STORE_LAB=PASS board=ESP8266`.
- Relay/output: [run #44877478259](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44877478259), jobs `136765261156` and `136765261418`, SUCCESS.
- Existing failure-injection checks remain active, including omitted ESP32 NVS commit and premature pre-commit durability mutations.

## Integration status and limits

- Full build: [run #44877478258](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44877478258). Validation job `136765324807` FAILED at the existing QA-owned `Missing poll signature check`. This task does not alter or bypass that contract.
  The run terminated CANCELLED after validation failed: 13/14 target/platform jobs completed SUCCESS; Android was CANCELLED; downstream simulation, update-bundle, signing and publication jobs were SKIPPED. Do not count the cancelled Android job as a build pass.
- The focused lab models NVS/EEPROM APIs. It does not emulate flash physics, electrical behavior, real power loss, or an independent physical witness.
- This result is **SIMULATED + CI VERIFIED** for the host lab only. Physical hardware acceptance remains **NOT TESTED**.
- No merge, physical flash, production migration, live-money operation, signing, release tag, deployment, or cutover was performed.

## Next action

PHX-MASTER should refresh canonical active-stack pins against current PR metadata. PHX-CORE must publish the authenticated register/poll and event-bound receipt contract before PHX-QA changes its positive poll-signature assertion. PHX-HARDWARE continues only with unblocked firmware-owned work; physical acceptance remains gated by owner-approved isolated noncustomer equipment and independent evidence.
