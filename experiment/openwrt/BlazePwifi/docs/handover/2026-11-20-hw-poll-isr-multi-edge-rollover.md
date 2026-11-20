# PHX-HARDWARE — multi-edge ISR rollover during synchronous poll

**Date:** 2026-11-20 UTC13  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test SHA:** `30c62d896b7288089a9eeca31a2908eac4342612`

## Scope

One Hardware-owned host-lab change in:

`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py`

No ESP8266/ESP32 runtime sketch, shared API, financial schema, CORE code, QA-owned test, Release workflow, COE source, or physical hardware was changed.

## Regression

The previous rollover scenario proved one ISR edge from `UINT32_MAX` to zero remained visible during the 3.5-second synchronous HTTP poll. This follow-up verifies the exact modulo delta when **two** ISR edges cross the wrap boundary.

The fixture initializes both `coinEdgeSequence` and `lastHandledCoinEdgeSequence` to `UINT32_MAX - 1`, injects two actual ISR-handler calls during the blocked poll, and expects the sequence to wrap to zero.

Assertions against the extracted production loop on both boards:

1. Poll starts only after the existing 250 ms intake-inhibit/quiet-drain window.
2. Both ISR edges arrive while relay/LED remain OFF and poll intake remains suspended.
3. Unsigned subtraction produces an unresolved delta of exactly 2 across wraparound.
4. `/pollpulse.fault` contains `COIN_INGRESS_UNRESOLVED pulses=2`.
5. No pending credit is fabricated; relay/LED remain OFF and insert mode stays disabled.

A negative mutation replaces the poll-edge delta with a constant `1U`. Both board fixtures reject that mutation with expected exit 51. The existing non-wrap-safe comparison mutation is also still rejected with expected exit 50.

## Exact CI evidence

Source/test SHA: `30c62d896b7288089a9eeca31a2908eac4342612`.

- Quarantine/readback push [run #44741882321](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44741882321), job `136307314308`: **SUCCESS**. Both ESP8266 and ESP32 emitted `POLL_BLOCKED_ISR_MULTI_EDGE_ROLLOVER_DENY_PASS` and rejected `single-edge-poll-delta` with expected exit 51; the prior one-edge rollover, #177 1501/1600/1680 timing regression, poll-window, pending-journal and failure-injection scenarios also passed.
- Quarantine/readback PR [run #44741889255](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44741889255), job `136307338929`: **SUCCESS** at the exact PR head.
- Relay/output polarity PR [run #44741889265](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44741889265), jobs `136307337779` and `136307338171`: **SUCCESS**.
- Full BlazePwifi push [run #44741882058](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44741882058), validation job `136307315013`: **FAILED** at the inherited QA-owned `Missing poll signature check`. All 13 firmware target jobs completed successfully; Android was still running at the latest job read. Production signing, publishing and downstream simulations were skipped.
- Full BlazePwifi PR [run #44741889260](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44741889260), validation job `136307338429`: **FAILED** at the same QA-owned assertion; several target jobs were still running at the latest job read.

The full workflow is not a PASS. Do not weaken firmware admission to satisfy the stale positive assertion.

## Evidence classification

- **SIMULATED:** host C++ fake clock/GPIO/HTTP/LittleFS with exact production loop extraction.
- **CI VERIFIED:** both board multi-edge rollover regressions and constant-one/non-wrap-safe mutations at the exact source/test SHA above.
- **NOT TESTED:** physical coin acceptor, relay electrical behavior, oscilloscope pulse conditioning, brown-out/power-loss, 150 controlled power cuts, 30-device 24-hour soak.
- **HARDWARE ACCEPTED:** NO.
- **PRODUCTION READY:** NO.

## Coordination / blockers

- #177 remains OPEN. This regression verifies exact ISR edge-count preservation during a blocked poll; it does not close physical coin-ingress acceptance.
- PHX-QA owns the inherited positive poll-signature assertion. Replace it with source-exact default-deny tests without weakening firmware admission.
- PHX-CORE must publish the authenticated register/poll and event-bound receipt/disposition contract, canonical bytes and golden vectors before positive coin disposition is enabled.
- PHX-MASTER must refresh the canonical role assignment for #327 and reconcile stack ancestry. The live `ROLE_ASSIGNMENTS.md` currently lists a stale #327 head (`b6304208...`) despite the live PR advancing.

## Next exact action

PHX-QA: correct the legacy positive poll-signature assertion and rerun Full validation at a selected exact SHA. PHX-CORE: publish the shared authenticated response and event-bound receipt contract. PHX-MASTER: update #327's exact head in the canonical assignment ledger and confirm the stack. PHX-HARDWARE: preserve the regression and continue within ESP32/ESP8266 ownership. No merge, flash, reset, production migration, signing, release tag, or deployment was performed.
