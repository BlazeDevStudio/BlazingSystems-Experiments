# PHX-HARDWARE handover — poll-window timeline guard follows fixture extraction

**Date:** 2026-11-21 UTC09  
**Role:** PHX-HARDWARE  
**Task:** #266 cleanup-first / #177 firmware safety evidence / #327  
**PR:** [#327 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test fix commit:** [`3110a42886bb595e28ba7ddeac16a51c2b86bd1c`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/3110a42886bb595e28ba7ddeac16a51c2b86bd1c)

## Master-directed task

Master's exact-head audit at [PR #288 commit `783c97ce`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/783c97ce997b6bfd0706f4d11e1b97fff588140e) identified a test-harness regression introduced when the poll-response C++ fixture payloads were moved out of `poll_response_failclosed_lab.py` into `poll_response_failclosed_lab_fixtures.py`.

The runner imports `WINDOW_MAIN` from the fixture module, but `poll_window_timeline_guard_lab.py` still searched for the synchronous-poll scenario in the runner. This was a stale path assumption, not a production sketch defect.

## Test-first evidence

- Pre-fix exact-head Relay failure: [run #44886128521](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44886128521), job `136791689099`. Failure: `AssertionError: missing synchronous-poll scenario`.
- The same pre-fix head's Quarantine workflow passed: [run #44886128587](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44886128587), job `136791689346`.

## Correction

Only the Hardware-owned `poll_window_timeline_guard_lab.py` changed.

- Load `poll_response_failclosed_lab_fixtures.py` explicitly and inspect its `WINDOW_MAIN` payload.
- Keep the runner checks for the `WINDOW_MAIN` / `WINDOW_STUBS` imports and the final-idle-sample failure-injection wiring.
- Validate the exact 250 ms quiet boundary, 70 ms into-poll sample, full 3500 ms synchronous timeout, and monotonic event ordering in the extracted fixture.
- Add a guard self-test that shortens the timeout from 3500 ms to 3499 ms and must be rejected.

No ESP8266/ESP32 production sketch, relay/coin behavior, controller API, response-signature contract, finance, witness, QA-owned assertion, or Release workflow changed. Poll admission remains default-deny.

## Exact-source GREEN evidence — source/test SHA `3110a42886bb595e28ba7ddeac16a51c2b86bd1c`

- Relay/output: [run #44887543780](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44887543780), job `136796017635`: **SUCCESS**. Logs include:
  - `MUTATION_REJECTED shorten-blocking-poll-timeout`
  - `POLL_WINDOW_TIMELINE_GUARD_PASS; MUTATION_REJECTED=1/1`
  - ESP8266 and ESP32: `POLL_WINDOW_GUARD_PASS 13/13`
  - ESP8266 and ESP32: `BLOCKING_POLL_RELAY_INHIBIT_PASS 1/1`
  - Physical coin, relay and power-cut markers remain zero.
- Quarantine/readback: [run #44887543799](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44887543799), job `136796017486`: **SUCCESS**.
- Full integration: [run #44887543788](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44887543788), validation job `136796018094`: **FAILURE** at the inherited QA-owned `Missing poll signature check` in `tests/controllers.sh`. At handover time, 13 target/platform jobs had completed successfully and Android job `136796018119` was still in progress. Downstream simulations, update bundle, signing and publication jobs were skipped. Do not claim Full validation passed.

## Classification and limits

- **SIMULATED:** exact-source host C++ control-flow and fixture mutation checks.
- **CI VERIFIED:** the narrow Relay/output and Quarantine workflows above.
- **Full integration:** FAILED at the separate CORE/QA controller contract gate.
- **HARDWARE ACCEPTED:** NO. Physical coin acceptor, relay polarity/contact, electrical pulse recovery, 150 physical power cuts, and 30-device/24-hour soak remain NOT TESTED.
- **PRODUCTION READY:** NO.

The tests model source behavior and do not emulate real flash physics, electrical relay behavior, a protected independent witness, or real customer money.

## Next exact action

PHX-CORE must publish the authenticated register/poll and event-bound receipt contract with canonical bytes and golden vectors. PHX-QA must align the positive poll-signature assertion only after that contract is approved, retaining all negative/default-deny checks. PHX-HARDWARE will re-read live heads on the next activation and select the next unblocked Hardware-owned task.

No merge, rebase, retarget, force-push, physical flash, production migration, signing, release tag, deployment or cutover was performed.
