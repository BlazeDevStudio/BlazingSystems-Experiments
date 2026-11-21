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
- Exact post-fix CI: the source/test SHA passed the focused quarantine/readback and relay/output workflows; exact run/job evidence follows.

## Exact post-fix CI evidence

Source/test SHA: `3292d2a1e207da4241189952eec0e97255a48475`.

- Quarantine/readback [run #44872148862](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44872148862), job `136748836404`: PASS. Exact log marker `SOURCE_QUARANTINE_PASS 36/36 scenarios (physical power cut NOT tested)`. The same job also passed the ESP8266 config-read recovery lab, both-board poll-drain pulse-capture lab (17/17 per board with fail-open mutations rejected), and ESP8266 boot-polarity lab.
- Relay/output [run #44872148854](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44872148854), jobs `136748836217` and `136748836417`: PASS. Exact logs retain 11/11 poll-response fail-closed cases, 13/13 strict root JSON cases, 4/4 coin POST root-status cases, 4/4 coin-disposition default-deny cases, and both-board poll-window / output-polarity mutation rejection.
- Source-SHA Full BlazePwifi build [run #44872148863](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44872148863), validation job `136748899166`: FAIL at the inherited QA-owned `Missing poll signature check`; target jobs were cancelled after validation failed.
- Current docs-only head `79eb2f801b55005ddd5d32ed30649b25f5af859a`: quarantine/readback [run #44872543642](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44872543642), job `136750059419`, PASS `SOURCE_QUARANTINE_PASS 36/36`.
- Current docs-only head Full build [run #44872543657](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44872543657), validation job `136750065184`: FAIL at the same QA-owned `Missing poll signature check`. All 15 target/platform jobs (ESP8266, ESP32, Android, Ruijie, Orange Pi and x86 matrix) completed SUCCESS; downstream simulations, update-bundle, candidate, signing and publication jobs were skipped. This is target-build CI evidence, **not** a Full validation pass.

- Docs-head quarantine/readback [run #44872202794](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44872202794), job `136749005366`: PASS on docs-only head `2bb29f783ecaf34a85657a2f4908b90bdafa1a47`, with the same `SOURCE_QUARANTINE_PASS 36/36` marker.
- Docs-head relay/output [run #44872202836](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44872202836), jobs `136749005528` and `136749005721`: PASS on the same docs-only head.
- Docs-head Full build [run #44872202781](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44872202781), validation job `136749067462`: FAIL at the same QA-owned controller protocol/signature assertion; target builds and downstream release jobs were cancelled or skipped.

The firmware fix is **focused CI VERIFIED** and the current docs-only head has **15/15 target/platform builds CI VERIFIED**. The Full controller validation gate still fails, so this is not Full integration CI VERIFIED. The Full integration gate remains failed, and no physical acceptance is inferred.

## Scope and safety

Changed paths:
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/quarantine_readback_lab.py` (test-first assertion)

No other role's files or shared APIs were modified. The #327 → #326 stack is preserved; no rebase, force-push, merge or retarget occurred.

**Evidence classification:** host fake-LittleFS / source-extracted regression only (SIMULATED; CI VERIFIED only after exact-head focused run passes). Physical flash durability, coin acceptor, relay, electrical recovery, 150 power cuts, and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.
