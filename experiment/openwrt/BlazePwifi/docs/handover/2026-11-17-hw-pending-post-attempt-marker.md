# PHX-HARDWARE handover — one-shot coin POST attempt marker

- Date: 2026-11-17 UTC05
- Role: PHX-HARDWARE
- Task: #172 / #177 / #266 — durable rejected/ambiguous event disposition
- Repository: BlazeDevStudio/BlazingSystems-Experiments
- Branch: `phoenix/hardware-quarantine-append-failclosed-20261117`
- Existing DRAFT PR: [#315](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/315), stacked on DRAFT #314
- Parent exact SHA: `75dc5f0b888f16e2c85e4321f62df4685639ad33`
- Status: DRAFT / exact-head CI pending / NOT HARDWARE ACCEPTED / PRODUCTION NO-GO

## Proven gap

At the previous #315 head, `loadPending()` restored a valid pending record with `pendingReady=true` and reset `lastSend=0`, while `canAttemptCoinPost()` permitted dispatch whenever LittleFS was mounted, the journal was not ambiguous, and pending pulses existed. If a coin POST had reached the server but its reply was lost, or a controller rejection was followed by failed quarantine append, the RAM-only `journalRecoveryRequired` latch disappeared on reboot. The same pending event could be automatically POSTed again.

This is the cross-reboot gap in Master Architecture Contracts §6.2. It is a source-level risk, not evidence that a duplicate credit occurred in production.

## Hardware-owned implementation

Both ESP8266 and ESP32 sketches now:

1. Persist `/pending.attempt` with the exact pending pulse count, nonce and target before the first `post("coin")`.
2. Confirm a matching durable pending record exists, then flush, close and read the marker back through the bounded PendingRecord validator.
3. Make the POST gate one-shot for the current boot.
4. On boot, treat matching, malformed, mismatched or orphan attempt markers as a hard reconciliation stop; no automatic replay is allowed.
5. Treat timeout, empty, malformed or unknown replies as ambiguous and retain the marker.
6. Remove the pending record first and the attempt marker last, only after the existing successful receipt or successful quarantine-append path. A failed marker removal leaves an orphan marker that blocks the next boot.

No receipt schema, CGI endpoint, crypto construction, finance backend, migration, witness, release workflow, pin mapping or remote-config contract changed.

## Failure-injection lab

New hardware-owned lab: `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/pending_attempt_marker_lab.py`.

The existing focused workflow invokes `quarantine_readback_lab.py`; that orchestrator now also invokes the new lab. It compiles the exact production record/checksum/read/load/mark/clear/POST-gate functions for both boards and checks:
- unattempted pending is eligible once;
- a verified marker blocks same-boot and post-reboot replay;
- mismatched, corrupt, truncated and orphan markers deny;
- marker open, short-write and readback faults deny dispatch;
- RAM-only pending cannot dispatch;
- pending deletion precedes marker deletion;
- failed pending/marker deletion remains fail-closed;
- multiple pending candidates remain untouched.

**CI:** not yet observed at the new commit. The lab reports source-extracted host simulation only; it does not establish flash power-cut durability or financial correctness.

## Coordination required

- PHX-CORE: review whether every POST attempt becomes operator-reconciliation-only after reboot, including power loss after marker commit but before request transmission; define durable receipt/replay and operator reconciliation.
- PHX-QA: independently inspect and run the exact-head marker lab, quarantine failure lab, pending-journal recovery lab and both target builds.
- PHX-MASTER: review marker ordering and §6.2 conformance; no shared schema/API change is proposed.
- PHX-RELEASE: no workflow edit requested; the existing focused workflow is reused.

No physical flash, device reset, live coin, real money, production migration, merge, signing, release or deployment occurred.

## 2026-11-17 UTC06 — focused harness repair

The new `pendingPostAttempted` production state caused the prior hardware-owned quarantine orchestrator to fail compilation because its fake C++ stub did not declare the variable. Updated `quarantine_readback_lab.py` to declare/reset the state and model the successful-clear reset. Exact failure: focused run 44027835302, job 133852350930. Target builds at 44027835329 passed ESP8266/ESP32 and returned platform targets; Full validation failed separately in QA-owned `v060_esp_poll_intake_guard.py` because its extracted loop omits `acceptPollResponse()`, `markPendingPostAttempt()`, and the new state variable. This PHX-HARDWARE repair is pending exact-head CI. No QA files or runtime firmware were changed.

## 2026-11-17 UTC06 — follow-up source-extracted harness alignment

The first attempt-marker integration exposed three additional hardware-owned harness dependencies. Updated the pending recovery lab to declare `pendingPostAttempted` and extract `samePendingRecord()`; updated pending write/readback lab with the one-shot state; added a direct attempted-marker denial case to the coin POST gate lab. Focused exact-head run 44028990570, job 133856072612, **PASS**. Full run 44028990577 validation job 133856107226 **FAILED** in QA-owned `v060_esp_poll_intake_guard.py`, which still does not extract/declare `pendingPostAttempted`, `acceptPollResponse()`, and `markPendingPostAttempt()`. The marker lab's printed denominator/aggregate was also corrected from 19/16 and 32/32 to 19/19 per board and 38/38 total; a new focused run is pending. No QA-owned files or firmware runtime behavior were changed.

## 2026-11-17 UTC06 — exact-head marker summary guard

The focused orchestrator now captures the one-shot marker lab output and asserts exactly two `PENDING_ATTEMPT_MARKER_PASS 19/19` board summaries plus the aggregate `38/38 total` line. This prevents a future harness from silently reporting stale denominators. The exact PR #315 head at this test is `ca2275bd4998197c6450d8a00cae367b255335d0`.

- Focused [run 44029841923](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44029841923), job `133858849902`: **COMPLETED SUCCESS at exact HEAD ca2275bd4998197c6450d8a00cae367b255335d0**. The source-extracted matrix passed: quarantine 17/17 per board; poll response 11/11 and strict JSON 13/13 per board; debounce/poll-window 8/8 per board; register-config 7/7 per board; attempt marker 19/19 per board (38/38 total); mount 7/7 per board; pending recovery 16/16 per board; pending clear 11/11 per board; pending write/readback 22/22 per board; coin POST gate 10/10 per board. All fake-filesystem/host simulations only.
- Full [run 44029841759](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44029841759), validation job `133858850165`: **FAILED** at QA-owned Controller protocol parity. Its extracted-loop harness still lacks `pendingPostAttempted`, `acceptPollResponse()`, and `markPendingPostAttempt()` for both boards. Other target jobs were still in progress at the last observation; no Full success is claimed.

PHX-QA must repair its owned `tests/v060_esp_poll_intake_guard.py` and independently rerun Full validation at the current #315 head. No QA-owned source was changed. No runtime firmware change, physical flash, real coin, relay, power cut, electrical pulse, soak, production migration, signing, merge, release or deployment occurred.

## 2026-11-17 UTC06 — coin POST gate aggregate count correction

The coin POST gate lab has 10/10 cases per board after the explicit one-shot-marker denial case was added; its previous aggregate banner still said 18/18. Corrected the banner to `20/20` total. The focused orchestrator workflow reran the actual ESP8266/ESP32 source-extracted suite at exact #315 head `b06034215439ff3264d273d20e0f851fdafc2366`.

- Focused [run 44030370904](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44030370904), job `133860589530`: **COMPLETED SUCCESS at exact HEAD b06034215439ff3264d273d20e0f851fdafc2366**. Logs confirm quarantine 17/17 per board; poll 11/11 and strict JSON 13/13 per board; debounce/poll-window 8/8 per board; register-config 7/7 per board; pending marker 19/19 per board (38/38 total); mount 7/7 per board; pending recovery 16/16 and pending clear 11/11 per board; write/readback 22/22 per board; coin POST gate 10/10 per board (20/20 total). Fake LittleFS/source-extracted host checks only.
- Full [run 44029841759](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44029841759) **COMPLETED CANCELLED** after validation job `133858850165` FAILED in QA-owned Controller protocol parity. The extractor still omits `pendingPostAttempted`, `acceptPollResponse()`, and `markPendingPostAttempt()`; ESP8266 compiled successfully, several Orange Pi targets passed, and ESP32/Ruijie/x86/Android plus simulations/release jobs were cancelled. No Full success.

No runtime firmware changed in this activation. PHX-QA still owns the failing extractor. No physical coin/relay/power-cut/electrical/soak test, production migration, signer, merge, release or deployment occurred.
