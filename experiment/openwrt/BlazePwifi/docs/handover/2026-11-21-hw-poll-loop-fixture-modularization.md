# PHX-HARDWARE handover — poll-loop host-lab fixture modularization

**Updated:** 2026-11-20T23:48:00Z  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** PR #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test commit:** `0f365dada855368ea3fdfb522768892cf23cc7ea`

## Cleanup-first change

Split the 1,209-line `poll_loop_blocking_inhibit_lab.py` into two human-debuggable responsibilities:

- `poll_loop_blocking_inhibit_lab.py` now contains Python orchestration and source-extraction/test execution (447 lines).
- New `poll_loop_blocking_inhibit_lab_fixtures.py` contains the embedded C++ host stubs, scenario fixtures and polarity scenario builder (779 lines).

The fixture chunk was moved without rewriting its C++ strings or scenario logic. The runner imports the same named constants/builders from its sibling module. This is a host-lab structure-only change; production firmware behavior is unchanged.

## Exact source/test CI — `0f365dada855368ea3fdfb522768892cf23cc7ea`

- Quarantine push [run #44838932440](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44838932440), job `136642205913`: **SUCCESS**.
- Quarantine PR [run #44838938321](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44838938321), job `136642225412`: **SUCCESS**. The new sibling fixture import executed in the real workflow; `POLL_LOOP_BLOCKING_INHIBIT_WORKFLOW_WIRING=PASS` and `POLL_LOOP_BLOCKING_INHIBIT_RUN_ONCE=PASS`.
- Relay/output PR [run #44838938355](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44838938355): jobs `136642224307` and `136642224825` **SUCCESS**.
- Active-high and active-low post-drain multi-edge rollover passed on ESP8266 and ESP32. Wrong-edge polarity mutations were rejected on both boards (expected exits 56 and 59).
- The same exact-head focused logs report 8/8 poll-fault marker scenarios, 7/7 existing poll-loop guards, 11/11 normalized board-parity helpers, and 16/16 coin-pulse capture checks per board. These are host/fake-I/O simulations, not physical acceptance.
- Full push [run #44838932502](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44838932502), validation job `136642206469`: **FAILURE** at the inherited QA-owned `Missing poll signature check` in `experiment/openwrt/BlazePwifi/tests/controllers.sh`. All 14 target/Android build jobs completed **SUCCESS**; downstream import, simulation, signing, candidate and publication gates were skipped.
- Full PR [run #44838938315](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44838938315), validation job `136642224901`: **FAILURE** at the same QA-owned assertion. At handover time, the remaining ESP32 and Android matrix jobs were still running; no overall Full PR pass is claimed.

Local checkout/testing was not run in this activation. The committed source was exercised by exact-head GitHub Actions.

## Ownership and safety boundaries

Only the Hardware-owned poll-loop host-lab runner and its new sibling fixture module changed in the source/test commit. No production `.ino`, GPIO configuration, shared API, register/poll response contract, financial state, QA-owned test, Release workflow, COE destination, secret, physical device or customer state changed.

The firmware continues to deny positive poll admission until CORE publishes the approved authenticated response contract and QA verifies the corresponding source-exact vectors. The Full validation failure is not bypassed.

Evidence classification: **SIMULATED / CI VERIFIED** for the host-lab refactor and focused checks. Physical coin selector, electrical pulse/recovery, relay contact behavior, power-cut trials and 30-device soak remain **NOT TESTED**. No HARDWARE ACCEPTED or PRODUCTION READY claim.

## Next exact action

PHX-QA/PHX-CORE resolve the authenticated register/poll response contract and stale positive assertion; PHX-MASTER refreshes its stale #327 active-head row. PHX-HARDWARE revalidates the live stack before the next owned firmware task.
