# PHX-HARDWARE — exact original poll timing regression for #177

**Date:** 2026-11-20 UTC11  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test SHA:** `099cf320a4c03b5de5e6da91dd1881f36dc7db86`

## Scope

One Hardware-owned host-lab change in:

`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py`

No ESP8266/ESP32 runtime sketch, controller response contract, finance schema, CORE code, QA-owned tests, Release workflow, COE source, or physical hardware was changed.

## Regression

The new source-extracted timing fixture reproduces the historical #177 timeline:

- Poll becomes due at fake time 1501 ms.
- The active-low coin pulse begins at 1600 ms and ends at 1680 ms.
- The production `loop()` and poll-window helpers are extracted from each actual board sketch.
- The pulse transition triggers the attached coin ISR while the pre-poll intake inhibit and quiet-drain window are active.

Expected and asserted on both ESP8266 and ESP32:

1. The synchronous HTTP poll is not entered (`pollCalls == 0`).
2. The ISR edge is observed and unresolved ingress is durably marked in the host LittleFS fixture as `COIN_INGRESS_UNRESOLVED` with `pulses=1`.
3. No pending credit is fabricated.
4. Relay and LED outputs remain OFF.
5. Temporary poll-drain state is cleared only after the persistent deny latch is set.

The negative mutation replaces the production `beginPollWindow()` call with `true`. Under that unsafe loop, the fixture expects exit 47 because the poll proceeds and the timed pulse is missed. Both board mutations were rejected with the expected exit code.

## Exact CI evidence

All evidence below is tied to source/test SHA `099cf320a4c03b5de5e6da91dd1881f36dc7db86`.

- Quarantine/readback PR [run #44731571301](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44731571301), job `136272371500`: **SUCCESS**. Both boards emitted `PHX_177_ORIGINAL_1501_1600_1680_TIMING_PASS` and `MUTATION_REJECTED issue-177-missing-prepoll-inhibit expected_exit=47`. Existing poll-window drain tests remained 11/11 per board.
- Quarantine/readback push [run #44731564071](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44731564071), job `136272346189`: **SUCCESS**.
- Relay/output polarity PR [run #44731571292](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44731571292): source-output job `136272371711` **SUCCESS**; ESP32 boot-polarity job `136272371786` **SUCCESS**.
- Full BlazePwifi PR [run #44731571244](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44731571244): validation job `136272494420` **FAILED** at QA-owned Controller protocol parity, with the exact error `Missing poll signature check` in the ESP8266 sketch. Other target jobs were still finishing at this handover's capture; no Full PASS is claimed.

Earlier test-fixture commits `9e832466...`, `2b8cf632...`, and `18f02ebb...` had harness-construction failures (missing reset helper, escaped fixture newlines, then a local-name collision). Those failures were corrected; only the final exact SHA above is the focused CI-verified result.

## Evidence classification

- **SIMULATED:** deterministic fake-clock / fake-GPIO / fake-LittleFS source-extracted scenario.
- **CI VERIFIED:** both board sketches, exact timing regression and negative mutation at the SHA above.
- **NOT TESTED:** physical coin acceptor pulse, electrical relay polarity, oscilloscope pulse conditioning, brown-out/power-loss behavior, 150 controlled power cuts, 30-device 24-hour soak.
- **HARDWARE ACCEPTED:** NO.
- **PRODUCTION READY:** NO.

## Coordination / blockers

- #177 remains OPEN. This regression verifies the host-side deny path; it does not close the physical coin-ingress acceptance requirement.
- PHX-QA owns the inherited positive poll-signature parity assertion. It must be replaced by source-linked default-deny tests without weakening firmware admission.
- PHX-CORE must publish the authenticated register/poll and event-bound receipt contract before positive coin disposition is considered.
- PHX-MASTER must reconcile this exact #327 head in its active assignment/stack snapshot. No Master-owned file was changed.
- Google Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available through the exposed connector surface; no older registry was substituted.

## Next exact action

PHX-QA: update the stale controller poll-signature assertion and independently rerun the Full validation. PHX-HARDWARE: retain this test-only regression and wait for authorized noncustomer physical acceptance before any hardware-ready claim. No merge, flash, reset, production migration, signing, release tag, or deployment was performed.
