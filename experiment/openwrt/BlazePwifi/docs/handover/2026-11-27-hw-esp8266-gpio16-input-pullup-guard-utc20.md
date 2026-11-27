# PHX-HARDWARE — ESP8266 GPIO16 coin-input capability guard

**Updated:** 2026-11-27T20:36:10Z  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-runtime-pin-config-guard-20261127-utc04`  
**Parent PR:** [#357 — Validate board GPIO roles before Vendo configuration persistence](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/357)  
**Base branch:** `phoenix/hw-poll-preflight-lab-modules-20261127-utc18` at `9f7a8ecb915cf199a82c0b4d37c56c40d722037b`  
**Source/test commit:** `750af995e28d7977dcac8ea4cc800f71c71d27d8`  
**Status:** SCOPED CI VERIFIED; FULL INTEGRATION BLOCKED.

## Finding

The ESP8266 runtime pin validator accepted GPIO16 as the coin-input role. The sketch configures that input with `pinMode(runCoinPin, INPUT_PULLUP)`, but the official ESP8266 Arduino Core reference lists GPIO16 as supporting `INPUT`, `OUTPUT`, and `INPUT_PULLDOWN_16`; GPIO0–15 support `INPUT_PULLUP`. GPIO16 therefore cannot satisfy the firmware's configured coin-input bias using the internal pull-up.

Reference: https://arduino-esp8266.readthedocs.io/en/latest/reference.html

## Change

- ESP8266 `validRuntimePins()` now rejects GPIO16 only when assigned to the coin-input role.
- GPIO16 remains allowed for relay and LED output roles because the core documents output support.
- Existing default tuple (coin 4 / LED 14 / relay 5) is unchanged.
- Invalid stored tuples continue through the existing safe-default path.
- ESP32 source and shared controller/finance contracts were not changed.

## Regression coverage

- Reject `validRuntimePins(16,5,14)`.
- Continue accepting GPIO16 as relay output: `validRuntimePins(4,16,14)`.
- Continue accepting GPIO16 as LED output: `validRuntimePins(4,5,16)`.
- Require the source to retain the `INPUT_PULLUP` setup that motivates the role restriction.
- Inject removal of the GPIO16 guard and require the host lab to reject the mutation.

The source-extracted host lab is SIMULATED evidence only. It does not measure input voltage, external resistor values, board revisions, relay contacts, or coin-slot pulses.

## Test status

- Source/test commit: `750af995e28d7977dcac8ea4cc800f71c71d27d8`.
- Focused GitHub Actions on final documentation head: PENDING.
- Firmware target builds: PENDING exact-head Actions.
- Physical GPIO / electrical acceptance: NOT TESTED.

## Blockers and next action

The deny-only v0.6 stack remains OPEN / DRAFT / UNMERGED. P0 poll/pulse mitigation, authenticated CORE register/poll/receipt/disposition, QA controller parity, physical wiring/polarity acceptance, 150 power cuts, 30-device/24-hour soak, signer/witness, durable accounting/replay, v1-to-v2 migration, and independent release signoff remain unaccepted.

**Next exact action:** run and inspect the exact-head `PHX-HARDWARE Active v0.6 Poll Intake Deny` workflow; then request Master to register PR #357's new source/test SHA in the role and integration matrices. Do not merge or enable coin/relay admission.


## Exact CI results

- Focused PR #46065708272: PASS, job 140730384339, source/test SHA 750af995e28d7977dcac8ea4cc800f71c71d27d8.
- Focused docs-head #46065796271: PASS, job 140730661656, docs SHA 022c3100a3b04acc02960ac00b7ac2933494da75.
- Mbed TLS #46065708312: PASS 3/3 (source contract 140730385175, core 3.3.13 job 140730384776, core 4.0.0 job 140730385291).
- Native #46065708271: FAIL at QA-owned PAY-0745 literal `clearPending(true/false)` assertion; the pending-sequence check itself passed. No unsafe clear call was added.
- Full build #46065702850: FAIL at handover freshness on source SHA 750af995 because the workflow checkout predated the docs sync; all 14 firmware target/platform jobs and Android passed, downstream bundles/simulations/sign/publish/candidate stages skipped.
- The source+handover checkpoint was co-committed after 5025a318 so a new Full run can see the synchronized record. Physical GPIO/electrical acceptance remains NOT TESTED.
