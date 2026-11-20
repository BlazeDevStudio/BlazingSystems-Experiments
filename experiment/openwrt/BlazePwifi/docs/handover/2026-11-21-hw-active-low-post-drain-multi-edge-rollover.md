# PHX-HARDWARE handover — active-low post-drain multi-edge rollover

**Date:** 2026-11-21  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** PR #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test commit:** `af8e0e1e70e17ce70be77ec46b2ffbe738a16df2`

## Scope

One Hardware-owned host-lab file changed:

`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py`

No production `.ino`, GPIO mapping, register/poll contract, finance path, QA-owned fixture, Release workflow, or COE destination file changed.

## Regression added

The existing post-drain two-edge rollover scenario used active-high wiring only. This adds the active-low counterpart, using the source-extracted production `loop()`, `beginPollWindow()`, `configureRuntimePins()`, and the actual attached FALLING ISR on both board extractions.

- Start `coinEdgeSequence` and `lastHandledCoinEdgeSequence` at `0xFFFFFFFE`.
- Inject two ISR edges after the final quiet sample and before the post-drain snapshot.
- Require unsigned wrap to `0` and an unresolved fault marker with `pulses=2`.
- Require zero HTTP poll dispatch, relay/LED OFF, insert disabled, active target cleared, no pending credit, and no released poll intake.
- Require the configured interrupt edge to be FALLING for active-low mode.

Failure injection changes the active-low ISR attachment from FALLING to RISING. The scenario rejects that wrong-edge mutation with expected exit `59`.

## Exact-head CI evidence

At source/test SHA `af8e0e1e70e17ce70be77ec46b2ffbe738a16df2`:

- [Quarantine Byte Readback PR run #44828218835](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44828218835), job `136606156296`: **SUCCESS**. ESP8266 and ESP32 logs both show `POLL_POST_DRAIN_ACTIVE_LOW_MULTI_EDGE_ROLLOVER_PASS` and `MUTATION_REJECTED active-low-post-drain-edge-polarity expected_exit=59`.
- [Relay Output Polarity PR run #44828218934](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44828218934), jobs `136606156034` and `136606156575`: **SUCCESS**.
- [BlazePwifi Full PR run #44828218906](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44828218906), validation job `136606156951`: **FAILURE**, exact inherited assertion `Missing poll signature check`. At handover time, several firmware target jobs were still running; do not claim the full target matrix complete from this observation. The failed validation prevented downstream simulation, signing, candidate and publication gates from running.

## Disposition

**SIMULATED / FOCUSED CI VERIFIED only.** The lab uses source-extracted firmware control flow and host I/O stubs. It does not prove real coin acceptor behavior, electrical pulse integrity, relay contacts, LittleFS/NVS durability under power loss, or hardware acceptance.

Production remains **NO-GO**. Do not add a positive poll signature check or enable admission to satisfy the inherited QA assertion. The current main CGI producer does not emit a register/poll `response_sig`; PHX-CORE must define the authenticated response contract and PHX-QA must replace the stale positive assertion with source-exact negative/default-deny tests before any positive consumer is implemented.

## Coordination / next actions

1. PHX-QA: own the stale positive poll-signature validation fixture and rerun exact-head Full after correcting it to default-deny until the approved contract exists.
2. PHX-CORE: define versioned authenticated register/poll response bytes, canonical serialization, event-bound receipt/disposition and golden vectors.
3. PHX-MASTER: refresh the canonical role assignment and integration matrix to current #327/#326/#323 heads; keep #322 → #323 → #326 → #327 ancestry unchanged unless the owner explicitly authorizes a different stack.
4. PHX-HARDWARE: retain deny-only behavior; wait for the shared contract before any positive response consumer work.

No merge, rebase, force-push, flash, device reset, migration, signing, release or deployment was performed.
