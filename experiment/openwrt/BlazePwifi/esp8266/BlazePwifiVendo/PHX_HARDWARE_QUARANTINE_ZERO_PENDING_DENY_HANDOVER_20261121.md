# PHX-HARDWARE handover — deny quarantine disposition with missing pending event

**Date:** 2026-11-21 (UTC05)  
**Role:** PHX-HARDWARE  
**Task:** #177 / #266 / #327 — quarantine-state consistency and fail-closed admission  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**PR:** #327 OPEN / DRAFT / UNMERGED  
**Parent PR #326:** `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Test-only RED commit:** `8b7311b28a4e35ddac1bd9208df40eb6f9721bb2`  
**Firmware fix commit:** `3292d2a1e207da4241189952eec0e97255a48475`

## Selected defect

The source-extracted quarantine lab already injected scenario 2 with a zero-pulse RAM state while a valid one-shot attempt marker still represented a four-pulse event. However, the assertion treated this inconsistent state as a benign no-op.

Both sketches' `quarantinePending()` returned immediately when `pendingPulses==0`, before checking the durable attempt marker or setting `journalRecoveryRequired`. A caller handling a verified rejection does not use the return value to release admission. Therefore this impossible/inconsistent disposition state needed an explicit fail-closed latch rather than a silent return.

This is not a normal valid quarantine path: a valid pending event must have a nonzero pulse count and matching durable attempt marker.

## Test-first RED

The test was tightened first in `esp32/BlazePwifiVendo32/quarantine_readback_lab.py`: scenario 2 now requires `journalRecoveryRequired==true` and continues to require that no pending clear occurs.

- Test-only commit: `8b7311b28a4e35ddac1bd9208df40eb6f9721bb2`
- Quarantine run [#44872068887](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44872068887), job `136748590678`: expected FAIL at `SOURCE_QUARANTINE_FAIL scenario=2`.
- The same exact-head PR attempt [#44872072437](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44872072437) also reproduced scenario 2 failure.

## Fix

Both ESP8266 and ESP32 `quarantinePending()` now treat a missing pending event as an inconsistent financial disposition:

- set `journalRecoveryRequired=true`;
- log an operator-reconciliation diagnostic;
- return false without calling `appendQuarantineRecord()` or `clearPending()`.

The fix is deliberately local to the two Hardware-owned sketches. It does not alter the receipt contract, server API, persistence format, controller signature scheme, credit/ledger authority, or QA-owned assertions.

- Firmware fix commit: `3292d2a1e207da4241189952eec0e97255a48475`
- Exact post-fix CI: pending at handover creation; final result is recorded in the PHX-HARDWARE UTC05 BLAZE-COMMS checkpoint.

## Scope and safety

Changed paths:
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/quarantine_readback_lab.py` (test-first assertion)

No other role's files or shared APIs were modified. The #327 → #326 stack is preserved; no rebase, force-push, merge or retarget occurred.

**Evidence classification:** host fake-LittleFS / source-extracted regression only (SIMULATED; CI VERIFIED only after exact-head focused run passes). Physical flash durability, coin acceptor, relay, electrical recovery, 150 power cuts, and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.
