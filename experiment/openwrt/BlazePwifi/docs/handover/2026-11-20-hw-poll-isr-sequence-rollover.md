# PHX-HARDWARE — ISR edge-sequence rollover regression

**Date:** 2026-11-20 UTC12  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test SHA:** `cd32710a7924b29edb9d540da3d5a91cabbbca36`

## Scope

One Hardware-owned host-lab change in:

`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py`

No ESP8266/ESP32 runtime sketch, shared API, finance schema, CORE code, QA-owned test, Release workflow, COE source, or physical hardware was changed.

## Regression

The ISR sequence is a 32-bit unsigned counter. This fixture initializes both `coinEdgeSequence` and `lastHandledCoinEdgeSequence` to `UINT32_MAX`, then injects one ISR edge during the 3.5-second synchronous HTTP poll. The ISR increments the counter from `UINT32_MAX` to zero.

Expected and asserted against the extracted production loop on both boards:

1. The poll begins only after the 250 ms intake-inhibit/quiet-drain window.
2. The injected ISR edge occurs while relay/LED outputs remain OFF and poll intake remains suspended.
3. Unsigned sequence subtraction detects exactly one edge across wraparound.
4. The controller persists `COIN_INGRESS_UNRESOLVED` with `pulses=1`.
5. No pending credit is fabricated; relay/LED remain OFF and insert mode stays disabled.

A negative mutation replaces modulo subtraction with a non-wrap-safe comparison that maps the wrapped delta to zero. Both board fixtures reject the mutation with expected exit 50.

## Exact CI evidence

Source/test SHA: `cd32710a7924b29edb9d540da3d5a91cabbbca36`.

- Quarantine/readback [run #44738644294](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44738644294), job `136296335889`: **SUCCESS**. Both ESP8266 and ESP32 emitted `POLL_BLOCKED_ISR_SEQUENCE_ROLLOVER_DENY_PASS` and rejected `non-wrap-safe-poll-edge-delta` with expected exit 50. Existing #177 timing regression and other poll/coin fault scenarios also passed.
- Relay/output polarity [run #44738644297](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44738644297), jobs `136296335751` and `136296336270`: **SUCCESS**.
- Full BlazePwifi [run #44738644445](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44738644445): validation job `136296338073` **FAILED** at the inherited QA-owned `Missing poll signature check`. This is not a Full validation PASS. Target jobs were still finishing when this handover was written; only terminal results should be reported later.

## Evidence classification

- **SIMULATED:** host C++ fake clock/GPIO/HTTP/LittleFS with exact production loop extraction.
- **CI VERIFIED:** both board rollover regressions and the unsafe non-wrap-safe mutation at the source/test SHA above.
- **NOT TESTED:** physical coin acceptor, relay electrical behavior, oscilloscope pulse conditioning, brown-out/power-loss, 150 controlled power cuts, 30-device 24-hour soak.
- **HARDWARE ACCEPTED:** NO.
- **PRODUCTION READY:** NO.

## Coordination / blockers

- #177 remains OPEN. This regression verifies unsigned ISR-sequence reconciliation in a host fixture; it does not close physical coin-ingress acceptance.
- PHX-QA owns the inherited positive poll-signature assertion. Replace it with source-exact default-deny tests without weakening firmware admission.
- PHX-CORE must publish the authenticated register/poll and event-bound receipt contract before positive coin disposition is enabled.
- PHX-MASTER must refresh the active #327 head and stack entry in the canonical assignment ledger. No Master-owned file was changed.

## Next exact action

PHX-QA: correct the legacy positive poll-signature assertion and rerun Full validation at an exact selected head. PHX-HARDWARE: preserve this rollover regression and continue only within the assigned ESP32/ESP8266 firmware/lab scope. No merge, flash, reset, production migration, signing, release tag, or deployment was performed.
