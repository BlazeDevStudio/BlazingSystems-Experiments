# PHX-HARDWARE — debounce clamp callsite lexical guard

**Date:** 2026-11-22 UTC06  
**Role:** PHX-HARDWARE  
**Task:** #172 / #177 / #266 / #327  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**PR:** #327 (OPEN / DRAFT / UNMERGED)  
**Final handover parent HEAD:** `dfeaf51363ab2987aecff086139efda4f2065836`

## Defect

`poll_response_failclosed_lab.py` used raw `source.count("boundedCoinDebounceMs(")` to assert that both board sketches retained the 20 ms debounce clamp on every configuration path. Raw source counting includes comments and string literals, so a removed real callsite could be replaced by a comment/string decoy and still satisfy the minimum count.

This was a verification false-positive, not a demonstrated firmware runtime defect.

## Test-first reproduction

- RED/test-only commit: `a5505730c919453d3eacb31ada27ad802a04f265`.
- Quarantine push run [#44992204984](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44992204984), job `137115494073`: FAIL, explicit marker `POLL_RESPONSE_DEBOUNCE_CALLSITE_DECOY_SURVIVED: ESP8266:comment,string`.
- Quarantine PR run [#44992208358](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44992208358), job `137115504340`: same expected RED.
- Relay/output PR run [#44992208359](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44992208359), job `137115504251`: same expected RED in the child poll-response lab.

The mutation removes one real `runDebounceMs=boundedCoinDebounceMs(...)` callsite and inserts either a comment decoy or a C++ string-literal decoy. The old raw counter accepts both mutants.

## Correction

- Implementation commit: `814545cc0bbe29ff0a991efa0521eb8638b163a3`.
- Log-marker commit: `dfeaf51363ab2987aecff086139efda4f2065836`.
- Only changed source/test path: `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_response_failclosed_lab.py`.
- Imported the existing shared lexical masker `mask_non_code` from `firmware_lab_source.py` and count only code after comments and literals are masked.
- Retained both failure-injection mutants and added explicit `POLL_RESPONSE_DEBOUNCE_CALLSITE_DECOY_REJECTED 2/2` output per board.

No ESP sketch, runtime firmware behavior, shared API, financial logic, signer/witness, QA-owned source, or Release workflow changed.

## CI evidence

At exact implementation SHA `814545cc0bbe29ff0a991efa0521eb8638b163a3`:

- Quarantine push [#44992333172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44992333172), job `137115893741`: SUCCESS.
- Quarantine PR [#44992336456](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44992336456), job `137115903998`: SUCCESS.
- Relay/output PR [#44992336463](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44992336463), source job `137115903984`: SUCCESS; ESP32 boot-polarity job `137115904216`: SUCCESS.

Exact logs show both-board poll-response fail-closed tests 11/11, root JSON tests 13/13, coin POST root ACK checks 4/4, default-deny disposition 4/4, debounce floor 8/8, poll-window 13/13, blocking poll inhibit 1/1, pulse capture 17/17 per board, and existing mutation guards. The final marker commit `dfeaf51363ab2987aecff086139efda4f2065836` was revalidated on exact-head PR workflows: Quarantine [#44992468629](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44992468629), job `137116314307`, SUCCESS; Relay/output [#44992468613](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44992468613), source job `137116314422` and ESP32 boot-polarity job `137116314326`, both SUCCESS. Exact logs print `POLL_RESPONSE_DEBOUNCE_CALLSITE_DECOY_REJECTED 2/2` for ESP8266 and ESP32. The push Quarantine run [#44992464704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44992464704) was still in progress at the last read and is not needed for the exact-head PR evidence.

Full BlazePwifi validation remains blocked by the inherited QA-owned `Missing poll signature check` assertion. The previous Full attempt at `814545cc...` was cancelled after the next commit superseded it; no Full PASS is claimed.

## Evidence classification

- Test harness regression: **CI VERIFIED** at `814545cc...`.
- Firmware runtime: unchanged.
- Poll/pulse host labs: **SIMULATED / CI VERIFIED**, not physical acceptance.
- Coin acceptor, relay, electrical pulse/recovery, power-cut, and 30-device soak: **NOT TESTED**.
- HARDWARE ACCEPTED: **NO**.
- PRODUCTION READY: **NO-GO**.

## Next exact action

PHX-QA and PHX-CORE must reconcile the positive poll-signature assertion with an approved authenticated register/poll and event-bound receipt contract. PHX-MASTER must refresh the live Hardware stack pins and decide whether #254 may receive the Mbed TLS 4 PSA compatibility change from the canonical #327 line. PHX-HARDWARE must revalidate the exact #327/#339/#340 heads before the next owned task.
