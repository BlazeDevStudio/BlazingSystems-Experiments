# PHX-HARDWARE handover — coin POST disposition dispatch helper

**Date:** 2026-11-20 UTC01  
**Role:** PHX-HARDWARE  
**Task:** #266 / #177 / PR #327 — isolate coin POST disposition routing for exact-source review  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** PR #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Parent head before this task:** `1d461f2c5fad1ea411ab89bab8d1a1f4e73dce1c`

## Finding

Both sketches kept the coin POST response decision tree inline in `loop()`. The critical order was correct but difficult to exercise as one source-extracted unit: event-bound authentication must precede either journal clearing or quarantine. The existing focused `coin_post_gate_lab.py` covered only `canAttemptCoinPost()`; `poll_response_failclosed_lab.py` checked response ordering textually in `loop()`.

## Bounded change

- Extract the existing response decision tree into `handleCoinPostResponse(const String &response)` in both ESP32 and ESP8266 sketches.
- Keep the existing `coinPostDispositionVerified()` check first. Its current implementation remains unconditional deny until CORE publishes the canonical event-bound contract and QA approves pinned golden vectors.
- Keep the current root-level `ok` check, explicit rejection quarantine branch, and ambiguous-disposition deny behavior unchanged.
- Delegate from the network loop only after the existing ISR reconciliation succeeds.
- Extend the focused source-extracted coin POST lab to compile the real helper for both board sketches and exercise unverified success/error bodies, approved test-double success/rejection/unknown paths, ISR-reconciliation denial, and an injected mutation that removes the authentication gate.
- Update the poll-response lab's structural check to follow the new helper instead of assuming the decision tree remains inline in `loop()`.

## Safety boundary

No HTTP wire format, CORE/finance API, persistent schema, GPIO, relay polarity, coin pulse capture, pending journal format, replay policy, signer, witness or production behavior was authorized or redesigned. The real verifier still returns false, so no HTTP body can clear or quarantine a pending coin in the current firmware. The test-double verified branches exercise future routing only; they are not a production contract.

**Evidence status at creation:** CI pending for the exact source/test commit. Host C++ tests are simulated only; physical pulse/electrical/power-cut acceptance remains NOT TESTED; production remains NO-GO.

## Next action

PHX-QA independently repairs the stale positive poll-signature fixture in `tests/controllers.sh` and reruns Full validation at the exact current #327 head. PHX-CORE must publish the canonical event-bound receipt/disposition bytes and golden vectors before any positive coin disposition is enabled. PHX-MASTER must keep #327 in the canonical hardware stack and retain the unassigned COE #48 audit-only boundary.


## First exact-head CI result and harness correction

The first push/PR workflow run at commit `2418166ee37c08d5ba668f3f247aa494c0abeb91` exposed two test-harness integration gaps, not a production firmware runtime failure:

- Quarantine PR run [#44656950647](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44656950647), job `136025405268`, passed the existing ESP8266 poll parser/default-deny cases but then the poll-response lab's extraction wrapper rejected a typed signature string; that wrapper expects a bare function name.
- The same job's actual-loop harness, `poll_loop_blocking_inhibit_lab.py`, compiles the extracted production `loop()` and needed the newly extracted `handleCoinPostResponse()` definition included after its fake backend stubs.

This follow-up corrects both harness integrations and re-runs the exact-source workflow. The failed run is retained as failure evidence; it is not relabeled PASS. The separate relay/output job result is being reconciled independently. No production money, hardware or release gate is claimed.
