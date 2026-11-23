# PHX-HARDWARE — ESP8266 EEPROM lifecycle failure injection

**Date:** 2026-11-22 UTC06  
**Role:** PHX-HARDWARE  
**Task:** #172 / #177 / #266 / #327  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**PR:** #327 — OPEN / DRAFT / UNMERGED  
**Base branch:** `phoenix/hardware-pending-write-fault-latch-20261119`  
**Base SHA:** `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test SHA:** `ab223494eacdd7d73eaab563031854bb677d04d5`

## Scope

Added failure-injection coverage for two ESP8266 EEPROM lifecycle outcomes in the Hardware-owned dual-store poll-fault lab:

1. `EEPROM.end()` reports failure after a successful `EEPROM.commit()`.
2. The post-commit `EEPROM.begin()` reopen/readback fails.

The tests assert that the current boot remains denied, the secondary-store writer is not retried in the same boot, and a fresh boot read discovers the persisted marker and remains denied.

**No production ESP8266/ESP32 sketch, financial code, shared API, QA-owned source, signer/witness, or Release workflow was changed.** The fake EEPROM models API outcomes only; it is not flash physics or physical durability evidence.

## Test-first evidence

- Test-only guard commit: `1d0ed7511f3e7091471724603bb589681c2a42bd`.
- Expected RED: [Quarantine run #44995054320](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44995054320), job `137124186290`: failed with `POLL_FAULT_EEPROM_LIFECYCLE_FAILURE_INJECTION_MISSING` for the two new required markers.
- First fixture attempt: `1bea0b89b72a997eef5a9720860ef00215c6171c`; [run #44995179598](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44995179598), job `137124559425`: failed to compile because the EEPROM-only scenarios were initially inserted into the shared ESP32/ESP8266 C++ harness. This was a test-fixture construction error, not a firmware failure.
- Corrected board-conditional fixture: source/test SHA `ab223494eacdd7d73eaab563031854bb677d04d5`.

## Exact-source GREEN

- PR Quarantine [run #44995304434](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44995304434), job `137124944702`: **SUCCESS** on exact source/test SHA `ab223494eacdd7d73eaab563031854bb677d04d5`.
- Push Quarantine [run #44995299815](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44995299815), job `137124931182`: **SUCCESS** on the same SHA.
- Exact logs include:
  - `ESP8266_EEPROM_END_FAILURE_REBOOT_DENY_PASS`
  - `ESP8266_EEPROM_REOPEN_FAILURE_REBOOT_DENY_PASS`
  - `POLL_FAULT_DUAL_STORE_LAB=PASS board=ESP8266`
  - `POLL_FAULT_DUAL_STORE_LAB=PASS board=ESP32`

Other Quarantine steps in the exact PR run passed, including pending-attempt marker, LittleFS mount fail-closed, poll-drain pulse capture, and ESP8266 boot-polarity verification. These remain source-extracted/host-simulated tests.

## Full integration status

[Full BlazePwifi PR run #44995304429](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44995304429), exact source/test SHA `ab223494eacdd7d73eaab563031854bb677d04d5`:

- Validation job `137125004111`: **FAIL** at the inherited `tests/controllers.sh` assertion:
  `Missing poll signature check` in the ESP8266 sketch.
- This is the existing QA/CORE authenticated register/poll contract mismatch. Hardware retains default-deny and did not alter the assertion or invent a `response_sig`.
- At handover time, 12 target jobs had passed; ESP32 and Android were still running. This is not a completed target matrix or Full integration pass.
- Signing, candidate, publication and production jobs remain gated/skipped.

## Evidence classification

- EEPROM lifecycle failure injection: **CI VERIFIED** (source-extracted fake EEPROM).
- Poll/coin and LittleFS host labs: **SIMULATED / CI VERIFIED**.
- Physical EEPROM/flash behavior: **NOT TESTED**.
- 150 controlled power cuts: **NOT TESTED**.
- 30-device / 24-hour soak: **NOT TESTED**.
- Electrical pulse/relay recovery: **NOT TESTED**.
- HARDWARE ACCEPTED: **NO**.
- PRODUCTION READY: **NO-GO**.

## Next exact action

PHX-MASTER must refresh the stale #327 Hardware pin in `ROLE_ASSIGNMENTS.md` and `INTEGRATION_MATRIX.md`. PHX-CORE must publish the authenticated register/poll and event-bound receipt contract; PHX-QA must reconcile the inherited positive poll-signature assertion against that approved contract. PHX-HARDWARE must keep coin admission and relay control fail-closed until those dependencies and physical acceptance are evidenced.
