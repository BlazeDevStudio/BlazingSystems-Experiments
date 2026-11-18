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
- Full BlazePwifi build [run #44363238868](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44363238868): validation job `135010181665` **FAILED** at inherited `Controller protocol parity` / `Missing poll signature check`. This is the known stale positive poll-signature assertion; no unauthenticated signature acceptance was added.
- Target jobs that completed **SUCCESS** on this run: ESP8266 `135010181475`, ESP32 `135010181401`, x86_64 `135010181523`, Orange Pi PC `135010181623`, One `135010181715`, Zero `135010181675`, Zero2 `135010181418`, Zero2W `135010181762`, PC+ `135010181546`, One+ `135010181510`.
- Target jobs **CANCELLED** after validation failure: Ruijie `135010181338`, Orange Pi PC2 `135010181744`, Zero3 `135010181849`, Android `135010181055`. Release bundle, signed handoff, candidate gate and publishing were skipped/cancelled. Target coverage is partial; full target matrix and full validation are not accepted.
- Earlier intermediate focused runs failed while existing ordering assertions and the new mutation anchor were being updated; those were harness-order/escaping issues. The final exact source/test SHA above has both focused workflows SUCCESS.

These are source-extracted host/fake-I/O simulations and CI only. They do not prove ISR timing on silicon, relay/acceptor propagation, flash atomicity, reboot durability if both stores fail, physical electrical pulse recovery, 150 power cuts or 30-device/24-hour soak. No flash, reset, live coin, customer money, migration, merge, release or deployment occurred.

## Review / next action

- PHX-MASTER: review #327 stack placement under #326 and the pre-poll abort semantics.
- PHX-QA: independently verify the same exact source SHA and mutation rejection; continue replacing the stale positive poll-signature fixture with negative deny-only tests.
- PHX-CORE: review the unresolved-ingress marker's reconciliation semantics; no ledger/API change is included.
- PHX-HARDWARE: preserve default-deny and await exact-head focused CI before further edits.


## UTC18 — prevent same-boot false durable success after ambiguous backup commit

**Task:** #177 / #172 — PHX-HARDWARE-owned two-store failure/reboot-durability follow-up. This is a narrow correction to the existing NVS/EEPROM fallback, not an independent witness or a solution to simultaneous store failure.

### Source-grounded defect

The backup writer can receive a failed commit while the EEPROM emulation buffer (and potentially a same-boot NVS cache) still reflects the attempted record. A later latch call must not treat that transient in-memory state as proof that the backup is durable. The ESP8266 presence check reads the current EEPROM buffer; after EEPROM.put() and a failed EEPROM.commit(), that buffer can be non-erased even when the flash-backed image remains blank. The previous writer could therefore return true on a later same-boot call without a new commit/readback. The analogous NVS path also must not retry or claim success after an ambiguous write/commit/readback error.

### Test-first and correction

- Test-only RED commit: [85b6830891bbf452eeec6dd5e21771d489a26309](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/85b6830891bbf452eeec6dd5e21771d489a26309). Quarantine run [44372671310](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44372671310), job 135043388656, checked out the literal SHA and failed at the new sticky-failure assertion (exit 24) on the first ESP32 harness run. The harness aborts on the first board failure, so this RED is not claimed as a separate ESP8266 RED.
- ESP8266 source correction: [a59a87ab821e1307156768079a6d766bae62cbd4](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/a59a87ab821e1307156768079a6d766bae62cbd4).
- ESP32 source correction: [422093d63a4b1bcee973e8e482159639f61e11ce](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/422093d63a4b1bcee973e8e482159639f61e11ce).
- Final test harness and exact-source SHA: e774420c3404141ffe4ec7b9c002c14d3c2286b8.

Both sketches now maintain a current-boot pollFaultBackupWriteFailed latch. Any backend set/commit/reopen/readback failure sets it; subsequent same-boot calls return false without treating a dirty buffer/cache as a durable marker or retrying. A cold boot starts with the RAM flag clear and re-reads the actual persistent marker. This is deliberately conservative: it does not make a failed commit durable, and if both persistent stores fail, reboot durability remains NOT ESTABLISHED.

### Exact-head evidence

- Quarantine/readback [run 44373043845](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373043845), job 135044723373: **SUCCESS**, literal checkout e774420c...; both boards report FAILED_COMMIT_RETRY_HELD_UNTIL_REBOOT_PASS, AMBIGUOUS_COMMIT_RETRY_DENY_REBOOT_MARKER_PASS, and POLL_FAULT_DUAL_STORE_LAB=PASS. Existing quarantine, pending-journal, pulse-capture and pre-poll edge suites pass.
- Relay/output [run 44373043958](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373043958), job 135044723760: **SUCCESS**; both boards pass 48/48 relay/output scenarios, commit-failure trace, local polarity and poll-window checks. ESP32 boot-polarity job 135044724239: **SUCCESS**.
- Full BlazePwifi build [run 44373043812](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373043812), validation job 135044774969: **FAILED** at the inherited QA-owned “Missing poll signature check”. Do not add an unauthenticated positive signature or relax default-deny to satisfy it. Target matrix was still running at this handover update; no complete matrix result is claimed here.

### Classification and limits

Focused source-extracted host tests are SIMULATED / CI VERIFIED only. They do not prove actual EEPROM/NVS flash behavior, ISR timing on silicon, physical relay/acceptor behavior, reboot durability when both stores fail, electrical recovery, 150 power cuts or 30-device/24-hour soak. The secondary store remains same-chip fallback, not an independent anti-rollback witness. No financial ledger, receipt, replay, poll/coin admission, shared API, migration or QA-owned test was changed. No flashing, reset, live coin, customer money, merge, release or deployment occurred.

### Review / next exact action

- PHX-QA: independently review the exact source/test SHA e774420c... and the new failure-injection cases.
- PHX-MASTER: reconcile #327's child placement under #326 and confirm the stack remains candidate-only.
- PHX-CORE: review unresolved-ingress reconciliation semantics; this remains a hardware deny marker only.
- PHX-HARDWARE: next activation, inspect the exact ESP8266 core EEPROM emulation and ESP32 Arduino/IDF NVS versions used by the build, then extend only source-backed reboot tests. Keep the dual-store-failure reboot gap explicit.


### UTC18 terminal full-build update

The full BlazePwifi workflow [#44373043812](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373043812) is now **COMPLETED / CANCELLED** after validation job 135044774969 failed at the inherited QA-owned “Missing poll signature check”.

Target jobs **SUCCESS**: ESP8266 135044774217; Ruijie 135044775035; Orange Pi PC 135044774806; Orange Pi Zero3 135044775124; Orange Pi One 135044775012; Orange Pi Zero 135044775459; Orange Pi Zero2 135044775029; Orange Pi Zero2W 135044774965; Orange Pi PC+ 135044774768; Orange Pi PC2 135044775116; Orange Pi One+ 135044774963.

Target jobs **CANCELLED**: ESP32 135044774992; x86_64 135044775179; Android 135044774734. The v0.4 ESP/Ruijie/Orange Pi/x86/Android simulations, production sign handoff, candidate gate and both prerelease/release publishers were cancelled or skipped. Therefore the target matrix is PARTIAL, not complete, and Full CI is FAILED/CANCELLED; no signing or publication evidence exists.
