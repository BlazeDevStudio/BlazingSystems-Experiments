# PHX-HARDWARE — poll-inhibit independent polarity regression

**Date:** 2026-11-26 UTC14  
**Issue / PR:** [#177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177) / [#354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/354)  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05`  
**Base:** `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`  
**Source/test SHA:** `9bb46bb27e4be80f6506dbebf2846700efd4cb81`  
**State:** OPEN / DRAFT / UNMERGED · test harness validated · production NO-GO

## Defect in the test

`poll_preflight_inhibit_lab.py` previously assigned the same polarity to the relay and status LED. That left a cross-wiring regression undetected if the relay OFF branch accidentally used `runLedActiveHigh`, or the LED OFF branch used `runRelayActiveHigh`.

## Changes

- Test-only RED commit `0e27daaf9440dba2f0d7907e5332d0c876d3f000` added the two cross-polarity mutations while the old harness still used symmetric polarities.
- The test correctly failed because the relay-OFF/LED-polarity mutation survived.
- Commit `96d6cfc3b9914fcd2d346f3d1bbfc95b07892290` changed the harness to all four independent relay/LED combinations and checked both OFF outputs and pending evidence.
- Commit `9bb46bb27e4be80f6506dbebf2846700efd4cb81` made the C++ harness stdout and rejected-mutation outcomes visible in CI logs.

## Exact evidence

- RED PR: [#45833611464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45833611464), job `139956531105`, FAIL at expected mutation-detection assertion.
- RED push: [#45833601391](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45833601391), job `139956496937`, same expected failure.
- GREEN PR: [#45834845699](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45834845699), job `139960864159`, PASS.
- GREEN log explicitly prints `POLL_INTAKE_GPIO_POLARITY_PASS 4/4` for ESP8266 and ESP32; relay/LED cross-polarity mutations are rejected on both boards (exit 12); deny-state mutation is rejected (exit 11).
- Full [#45834845628](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45834845628), validation job `139960957851`, failed at mandatory handover freshness because this documentation refresh had not yet landed. It is not a source compile failure and not Full PASS.

## Evidence boundary

Only the Hardware-owned host lab changed. Both production sketches remain unchanged and deny-only. No poll response is trusted, no automatic coin POST is enabled, no pending evidence is cleared, and no positive relay admission is introduced. The host model is SIMULATED / CI VERIFIED only; physical GPIO voltage/contact behavior, coin acceptor, electrical recovery, LittleFS power-loss, 150 power cuts and 30-device/24-hour soak remain NOT TESTED.

## Process note

The test-only RED commit was made before a new `IN PROGRESS` record was staged in `CURRENT_STATE.md`. This ordering deviation is disclosed. Future source work must stage the IN PROGRESS record first.

## Next exact action

PHX-QA reconciles the deny-only native/controller-parity assertions without weakening the fail-closed boundary; PHX-CORE publishes the authenticated register/poll and event receipt/disposition contract; PHX-MASTER refreshes #354 branch pins. PHX-HARDWARE then revalidates and reruns Full. No merge, flash, reset, live-money operation, production migration, signing, release tag or deployment.

