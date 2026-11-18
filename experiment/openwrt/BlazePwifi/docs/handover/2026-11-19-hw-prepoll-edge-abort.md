# PHX-HARDWARE handover — persist drain-window ISR edges before synchronous poll

**Task:** P0 #177 / control plane #172  
**Candidate:** [PR #327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Parent:** PR #326 branch `phoenix/hardware-pending-write-fault-latch-20261119` at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Test-first RED:** `43187f01a068e012aa96ea8bf47b0a78884eb463`  
**Disposition:** focused regression correction under CI; SIMULATED only; physical acceptance NOT TESTED; PRODUCTION NO-GO.

## Defect found

Both board sketches snapshot `coinEdgeSequence` before `beginPollWindow()`. That helper turns outputs off and performs a 250 ms quiet drain. An ISR edge can be recorded after the final GPIO quiet sample but before the helper returns true. The current loop then calls synchronous `post("poll")` and does not compare the ISR sequence until after the HTTP wait. The edge is only volatile RAM during that wait; a power loss before the post returns could lose it before the durable deny marker is written.

This is a source-level race, not a claim that a physical acceptor accepted a coin while relay power was inhibited.

## Test-first reproduction

The hardware-owned `poll_loop_blocking_inhibit_lab.py` extracts the actual ESP8266/ESP32 `loop()`, `coinEdgeISR()`, `snapshotCoinEdgeSequence()`, `beginPollWindow()`, `latchPollPulseFault()`, and LittleFS marker writer. The test injects an ISR sequence increment after the final quiet sample and immediately before `beginPollWindow()` returns.

- RED commit: `43187f01a068e012aa96ea8bf47b0a78884eb463`.
- Quarantine workflow [#44362175071](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44362175071), job `135006232626`: expected failure at ESP8266 `edge-after-drain-before-snapshot: expected exit 0, got 22`; prior quarantine/readback suites and ESP8266/ESP32 pulse-capture 8/8 passed before the new assertion.
- Relay/output workflow [#44362175321](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44362175321), job `135006234538`: expected failure at the same new assertion after output polarity, boot gate, and 250 ms poll-drain labs passed.
- Full build [#44362175280](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44362175280): validation job `135006235791` failed at inherited QA-owned `Controller protocol parity`; target jobs were still running when the RED checkpoint was captured. This is not Full CI acceptance.

## Firmware correction

Both sketches now compare `snapshotCoinEdgeSequence()` with the pre-drain snapshot immediately after a successful `beginPollWindow()` and before any HTTP call. If a drain-window ISR edge exists, the loop:

1. Calls the existing `latchPollPulseFault(delta)` immediately, while poll inhibition is still asserted.
2. The production latch sets the sticky RAM deny state and drives logical relay/LED OFF before secondary-store and LittleFS persistence.
3. Releases the temporary poll-inhibit flag only after the latch returns; `journalRecoveryRequired` continues to hold outputs OFF.
4. Updates `lastPoll` and defers HTTP polling, avoiding a hot retry loop.

If `beginPollWindow()` detects an active pulse through GPIO and aborts normally, the existing loop path still samples that pulse and writes the pending journal. Edges observed during the later 3.5 s HTTP wait continue to use the existing post-wait fault latch. No positive poll, coin admission, credit, receipt, replay, finance API, migration, shared schema, signer, or QA-owned test file changed.

## Exact-head verification

**Source/test SHA:** `a4b22b68a4a745d9749687a972a608f1ff6b1d21`  
**Current source commits:** ESP8266 `5a6acb8031f727f07c85db6f67060c10c08a294f`; ESP32 `900e9ede0a9f14c36bb374845c3f041db2ee6a1b`.  
**Test-first RED:** `43187f01a068e012aa96ea8bf47b0a78884eb463`.

- Quarantine/readback [run #44363238933](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44363238933), job `135009999752`: **SUCCESS**. Both ESP8266 and ESP32 poll-loop race cases pass; `POLL_EDGE_SNAPSHOT_RACE_PASS` and `MUTATION_REJECTED missing-pre-poll-edge-abort` appear on both fixtures. Existing pulse capture is 8/8 per board; the full poll-loop mutation set is rejected; quarantine/readback and poll-response default-deny suites pass.
- Relay/output [run #44363239280](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44363239280), job `135010001678`: **SUCCESS**; ESP32 boot-polarity job `135010000647`: **SUCCESS**. Poll-window timeline, response fail-closed, output polarity and pre-persistence output-inhibit checks pass.
- Full BlazePwifi build [run #44363238868](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44363238868): validation job `135010181665` **FAILED** at inherited `Controller protocol parity` / `Missing poll signature check`. This is the known stale positive poll-signature assertion; no unauthenticated signature acceptance was added. ESP8266 target job `135010181475` passed; ESP32 target job `135010181401` and remaining target jobs were still running at the checkpoint. Full target matrix is not accepted.
- Earlier intermediate focused runs failed while existing ordering assertions and the new mutation anchor were being updated; those were harness-order/escaping issues. The final exact source/test SHA above has both focused workflows SUCCESS.

These are source-extracted host/fake-I/O simulations and CI only. They do not prove ISR timing on silicon, relay/acceptor propagation, flash atomicity, reboot durability if both stores fail, physical electrical pulse recovery, 150 power cuts or 30-device/24-hour soak. No flash, reset, live coin, customer money, migration, merge, release or deployment occurred.

## Review / next action

- PHX-MASTER: review #327 stack placement under #326 and the pre-poll abort semantics.
- PHX-QA: independently verify the same exact source SHA and mutation rejection; continue replacing the stale positive poll-signature fixture with negative deny-only tests.
- PHX-CORE: review the unresolved-ingress marker's reconciliation semantics; no ledger/API change is included.
- PHX-HARDWARE: preserve default-deny and await exact-head focused CI before further edits.
