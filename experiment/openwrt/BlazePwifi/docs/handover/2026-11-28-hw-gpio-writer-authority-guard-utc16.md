# PHX-HARDWARE UTC16 — centralized GPIO writer authority contract

**Task:** `PHX-HW-177-GPIO-WRITER-AUTHORITY-20261128T16Z`  
**Issue:** [P0 #177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Parent candidate:** [PR #378](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/378) at `3f67ba41dc3e087f868d3c57f6604e69f7a0e17b`  
**Branch:** `phoenix/hw-output-writer-authority-guard-20261129-utc16`  
**Updated:** 2026-11-28T16:36:58Z  
**Status:** IN PROGRESS; source/test CI not yet run.

## Scope and reason

The #378 regression rejects a direct relay GPIO ON mutation after the final post-poll deny. A source audit confirms that both current sketches centralize the physical `digitalWrite` in `writeLogical`, and all current `writeLogical` callsites are in `configureRuntimePins` or `applyOutputs`. This follow-up turns that observed property into a maintainable contract so a future helper cannot bypass the existing deny predicate.

## Planned contract

- Exactly one executable `digitalWrite` call exists, inside `writeLogical`.
- All `writeLogical` callsites are owned by `configureRuntimePins` or `applyOutputs`.
- `configureRuntimePins` may only write logical OFF.
- `applyOutputs` retains exactly the four board-polarity-aware calls, with ON values supplied only by its existing `accepting` predicate.
- Four independent mutations must be rejected on both ESP8266 and ESP32 source fixtures.

## Verification plan

Run the Poll Intake Deny workflow and ESP32 Mbed TLS 3.3.13/4.0.0 matrix on the exact source SHA. Record Full/Native separately; inherited QA failures are not transferred as passes. Do not modify QA-owned assertions or CORE protocol files.

## Safety and limits

This is a source-contract / host mutation test, not physical acceptance. Physical relay/acceptor polarity, pulse retention, EEPROM/NVS brown-out, LittleFS power-loss, 150 power cuts, 30-device/24-hour soak and electrical recovery remain NOT TESTED. HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO. No flash, reset, live money, migration, signing, release, merge or deployment.

**Rollback:** close/revert only this child PR; parent #378 and earlier stack remain unchanged.


## Source/test implementation — 2026-11-28T16:43:00Z

Source/test commit `b3db93481d676a519fd8870af3a66fc7f2d23d5a` changes only `poll_preflight_inhibit_lab_contract.py` and `poll_preflight_inhibit_lab_cases.py`. The new contract centralizes the sole `digitalWrite` in `writeLogical`, limits `writeLogical` callsites to startup OFF and the existing `applyOutputs` gate, and rejects four mutation classes per board (8/8 expected). CI pending; local checkout NOT RUN. No production sketch/API/QA/CORE file changed.
