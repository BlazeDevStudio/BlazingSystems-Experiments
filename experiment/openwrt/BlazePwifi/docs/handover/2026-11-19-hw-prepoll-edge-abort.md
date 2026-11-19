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


## UTC19 — source-backed ESP8266 EEPROM flash-read fail-closed correction

**Candidate:** [PR #327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327), still OPEN / DRAFT / UNMERGED; child of #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`.  
**Current source/test SHA:** `8eeb18edde426cbbff3f8a8042c163a9ce519ee1`.  
**Current firmware commit:** `36050116444926c33cc05f224da2d3ef0cfc788c`.  
**Current test/model commit:** `8eeb18edde426cbbff3f8a8042c163a9ce519ee1`.  
**Focused workflow trigger commit:** `a8d8588e652350836d7c7bec87762df7e3188c10`.

### Exact toolchain/source audit

The full-build logs identify the currently observed board packages:

- ESP8266 job `135044774217` on [run #44373043812](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373043812) installed `esp8266:esp8266@3.1.2`.
- ESP32 job `135044774992` on the same run installed `esp32:esp32@3.3.13`.
- The later exact-head build [#44383603449](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44383603449) again installed ESP8266 core 3.1.2 in job `135082278725` and ESP32 core 3.3.13 in job `135082278903`.

The current build workflow installs `esp8266:esp8266` and `esp32:esp32` without version suffixes. These are observed versions, **not a repository-enforced toolchain lock**. PHX-HARDWARE did not edit the shared build workflow; PHX-RELEASE is requested to pin the approved versions or coordinate a controlled version bump.

Source audit:

- [ESP8266 core 3.1.2 EEPROM.cpp](https://github.com/esp8266/Arduino/blob/3.1.2/libraries/EEPROM/EEPROM.cpp) maps the EEPROM sector from `EEPROM_start - 0x40200000`. Its `EEPROM.begin()` calls `ESP.flashRead()` but does not propagate the read result to the sketch. A valid `EEPROM.length()` therefore does not prove the flash read succeeded.
- [ESP8266 flash_hal.h](https://github.com/esp8266/Arduino/blob/3.1.2/cores/esp8266/flash_hal.h) exposes the EEPROM start mapping used by the core.
- [Arduino-ESP32 3.3.13 release](https://github.com/espressif/arduino-esp32/releases/tag/3.3.13) is based on ESP-IDF v5.5.6+.
- [ESP-IDF v5.5.6 nvs_api.cpp](https://github.com/espressif/esp-idf/blob/v5.5.6/components/nvs_flash/src/nvs_api.cpp) marks `nvs_commit()` as a no-op for now (while still resolving/validating the handle); [nvs_handle_simple.cpp](https://github.com/espressif/esp-idf/blob/v5.5.6/components/nvs_flash/src/nvs_handle_simple.cpp) sends `set_blob()` directly to `Storage::writeItem()`. The host model was corrected accordingly: `nvs_set_blob` writes the modeled durable image immediately, while an injected commit error is documented as a defensive API-error path, not a second flash-write boundary.

### Proven ESP8266 defect and source correction

The previous boot-critical presence check used `EEPROM.get()` after `EEPROM.begin()`. If the core's internal `ESP.flashRead()` failed, the sketch received no status and could inspect an erased-looking/uninitialized RAM buffer as if the reserved poll-fault area were clean.

The ESP8266 sketch now:

1. Includes the core's `flash_hal.h` for the same `EEPROM_start` mapping used by EEPROM.cpp.
2. Uses `readPollFaultBackupFlash()` to call status-bearing `ESP.flashRead()` at `EEPROM_start - 0x40200000 + POLL_FAULT_EEPROM_OFFSET`.
3. Treats a raw flash-read failure as present/corrupt (deny) in `pollFaultBackupPresentOrCorrupt()`.
4. Uses the same raw read for post-commit byte verification; a readback error sets the existing sticky `pollFaultBackupWriteFailed` latch and returns false.

The ESP32 firmware source was not changed in this slice. Its NVS read-error/type-mismatch/open-failure denial tests remain in the same two-board lab.

### Test-first and exact-head evidence

- **Expected RED:** test-only commit `a477c56f29cde89642ba6d35b278e0bfeefb2028`; [run #44383198882](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44383198882), job `135080701591`, failed with exit 33 on the ESP8266 raw-flash-read failure case. ESP32 NVS scenarios passed before the ESP8266 assertion stopped the executable. This is the intended reproduction of the old false-clean path.
- **Intermediate harness failure:** [run #44383464868](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44383464868), job `135081628544`, failed to compile because the newly extracted helper was emitted after its callers. This was a test-harness declaration-order defect, not a firmware compile result. The helper was moved before its callers in commit `8eeb18edde426cbbff3f8a8042c163a9ce519ee1`.
- **Final focused exact-head PASS:** [run #44383603474](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44383603474), job `135082100388`, SUCCESS at exact SHA `8eeb18edde426cbbff3f8a8042c163a9ce519ee1`. Logs include `ESP8266_RAW_FLASH_READ_ERROR_DENY_PASS`, `POLL_FAULT_DUAL_STORE_LAB=PASS` on ESP8266 and ESP32, 72/72 source quarantine scenarios, 56/56 pending-attempt cases, 16/16 mount/output cases, both-board pending journal/clear/write-readback and coin-post suites, 11/11 poll-window drain cases per board, and 8/8 pulse-capture cases per board. The job explicitly reports `SIMULATED_ONLY=1` and `PHYSICAL_POWER_CUT_ACCEPTANCE=0`.
- **Full build still not accepted:** [run #44383603449](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44383603449) has validation job `135082278352` FAILED at inherited `Controller protocol parity` / stale positive poll-signature expectation. ESP8266 compile job `135082278725` SUCCESS (core 3.1.2); ESP32 compile job `135082278903` SUCCESS (core 3.3.13). Other target jobs were still running at this handover update; do not claim a completed full matrix.

### Classification, residual gap, and requests

This correction is **CI VERIFIED / SIMULATED ONLY**. It does not prove actual ESP8266 flash-read fault behavior on silicon, power-cut atomicity, physical coin/relay behavior, or reboot durability if both LittleFS and EEPROM/NVS fail. The dual-store failure remains current-boot denial only; no independent witness exists. The positive poll-signature fixture, Android dependency reproducibility, private Drive v11 registry access, signer/witness, financial v1-to-v2 migration, durable accounting/replay, 150 power cuts, 30-device/24-hour soak and electrical pulse/recovery remain open gates.

- **PHX-RELEASE:** pin the ESP8266/ESP32 Arduino core versions in the shared build workflow (or approve a controlled bump); current logs show 3.1.2 and 3.3.13 but the workflow is unpinned.
- **PHX-QA:** independently review exact source/test SHA `8eeb18edde426cbbff3f8a8042c163a9ce519ee1`, including the raw flash-read failure and NVS source-model correction.
- **PHX-MASTER:** keep #327 candidate-only under #326; no stack merge requested.
- **PHX-HARDWARE:** next activation, revalidate current core/package pins and branch heads, then continue the bounded cold-boot persistence audit without claiming dual-store reboot durability.

No shared financial/API contract, signer, migration, QA-owned test, production image, or release artifact was changed. No flash, reset, live coin, customer money, merge, release or deployment occurred.


## UTC20 — distinguish unreadable EEPROM marker from an existing durable deny marker

**Task:** P0 #177 / #172 — PHX-HARDWARE-owned persistence-status correction. This is limited to the ESP8266 EEPROM-emulation fallback; no shared API, finance, CORE, QA-owned fixture, release workflow or COE destination was changed.

### Defect and test-first reproduction

pollFaultBackupPresentOrCorrupt() intentionally returns true when the direct raw flash read fails, because an unreadable marker must deny boot. The ESP8266 writePollFaultBackup() previously reused that boolean as an existence check and returned true immediately. Therefore a transient ESP.flashRead() failure before a new backup write could be misreported as an already-persisted secondary marker, without calling EEPROM.commit().

- Test-only RED commit: [c4af8772f486b94907708c3984f717af4d123c4c](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c4af8772f486b94907708c3984f717af4d123c4c).
- Exact-source focused run [#44393894786](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44393894786), job 135118520291: **EXPECTED FAILURE**, ESP8266 harness exit 35. The new scenario injected a raw flash-read failure before the writer and rejected the old false-success return. The same test-only SHA's PR run [#44393910940](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44393910940) also failed at the regression as expected.

### Source correction

- Firmware fix and combined source/test SHA: [dfa7f50b6e4e5cecf7e13d1a53a54f966bb5242c](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/dfa7f50b6e4e5cecf7e13d1a53a54f966bb5242c).
- writePollFaultBackup() now performs a status-bearing readPollFaultBackupFlash(existing) itself. Read failure sets pollFaultBackupWriteFailed and returns false. Only a successful read containing non-erased bytes is treated as an already-existing deny marker; erased bytes proceed to the new record write/commit/readback path.
- The boot-time pollFaultBackupPresentOrCorrupt() remains conservative: unavailable/corrupt state still denies. ESP32 firmware was not changed.

### Exact-head CI

- Push quarantine/readback [#44394240119](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44394240119), job 135119742396: **SUCCESS** at dfa7f50b...; log includes ESP8266_RAW_FLASH_READ_ERROR_WRITE_DENY_PASS, ESP8266_RAW_FLASH_READ_ERROR_DENY_PASS, and POLL_FAULT_DUAL_STORE_LAB=PASS for both ESP32 and ESP8266.
- PR quarantine/readback [#44394253673](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44394253673), job 135119789915: **SUCCESS** at the same SHA.
- PR relay/output [#44394253804](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44394253804): **SUCCESS**; ESP32 boot-polarity job 135119790666 and source-output job 135119791019 both passed.
- Full push [#44394238564](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44394238564), validation job 135119907527: **FAILED** at inherited QA-owned Missing poll signature check. Full PR [#44394253862](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44394253862), validation job 135119968436: **FAILED** at the same assertion. Do not add a synthetic positive signature or weaken default-deny. Both exact-head Full runs are terminal FAILURE only because validation failed at the inherited QA-owned Missing poll signature check. Push run #44394238564: all 13 firmware/platform target jobs and Android succeeded; PR run #44394253862: all 13 firmware/platform target jobs and Android succeeded. Downstream simulations, update bundle, candidate gate, signing and publishing were skipped. Target builds are CI VERIFIED; full validation is NOT accepted.

### Classification / remaining limit

The raw-read failure is now distinguished from a proven existing marker, and same-boot ambiguous-write retries remain blocked by the earlier RAM latch. This is still source-extracted host/fake-I/O simulation and CI only. It does not establish flash physics, cold-boot durability if both LittleFS and EEPROM/NVS fail, an independent anti-rollback witness, physical relay/acceptor behavior, 150 power cuts, 30-device/24-hour soak or electrical pulse/recovery. The two stores share the same flash chip on these boards; they are not an independent witness.

**Next exact action:** obtain PHX-QA independent review of the combined source/test SHA dfa7f50b...; request PHX-MASTER to refresh the #327 current-head/stack record; keep the stale positive poll-signature fixture with PHX-QA and preserve firmware deny-only behavior. No merge, flash, migration, signer provisioning, release or deployment.


## UTC22 — poll-drain abort inhibit continuity and exact-source mutation coverage

**Task:** P0 #177 / #172 — keep the poll intake inhibit asserted until the ISR sequence is reconciled for both successful and aborted quiet-drain outcomes. The firmware correction is already present in this stacked hardware branch; this activation repaired the hardware-owned source-extraction lab so it detects transient relay re-energization and its mutations still match the current production loop.

### Firmware behavior at the exact branch source

- Firmware correction: [ddb386847e152e8ca4992e9f6b3370bfa3f20462](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/ddb386847e152e8ca4992e9f6b3370bfa3f20462).
- `beginPollWindow()` now leaves `pollIntakeSuspended` asserted when the quiet drain returns false. It does not release the inhibit or call `applyOutputs()` from inside the helper.
- The caller snapshots `coinEdgeSequence` after either drain result. If an edge arrived, it latches the unresolved ingress fault and deasserts outputs before persistence, then releases the poll inhibit. Only the no-edge false-return path releases the inhibit after the sequence reconciliation.
- No response-signature contract, positive remote admission, coin POST, financial API or replay semantics were changed.

### Test-harness corrections in this activation

- [104b7caf70dcb27697103df204a1f3a1f5cfef58](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/104b7caf70dcb27697103df204a1f3a1f5cfef58) adds a harness-side observation that records any relay/LED re-energization after the injected drain-abort edge but before `journalRecoveryRequired` becomes sticky. The exact-source assertions cover active-low and active-high coin wiring.
- [427158c95d97b4ac1f87803df73d936b687b296a](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/427158c95d97b4ac1f87803df73d936b687b296a) updates the late-snapshot mutation anchor to include the production reconciliation comment.
- [ed667e88f6844284834ebd3a337dfce07a817e8c](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/ed667e88f6844284834ebd3a337dfce07a817e8c) updates the remove-`beginPollWindow` mutation to target the current `pollWindowReady=beginPollWindow()` call site rather than an obsolete `if(beginPollWindow())` form.

### Exact-head CI results

- Focused [run #44413615691](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44413615691), job [135187982356](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44413615691/job/135187982356), exact source/test SHA `ed667e88...`: **overall FAILURE**, but the poll-loop subtest completed on ESP8266 and ESP32. Both logs show `POLL_ABORT_DRAIN_INHIBIT_CONTINUITY_PASS`, active-low and active-high abort-edge persistence, and rejection of release-before-reconciliation, missing-pre-poll-edge and late-snapshot mutations. All remaining poll-window, pulse-capture, output-inhibit and boot-latch mutations in that lab also rejected as expected.
- The same focused job then failed in the separate `config_load_read_failure_lab.py` on ESP8266: `expected exit 0, got 31`. This is a **separate P0 source defect**, not a failure of the poll-drain correction. The lab's first scenario seeds a pre-existing poll-fault marker, injects failure of the `EEPROM.begin()` full-image read, and requires a subsequent status-bearing raw full-image read before config defaults/save can proceed. Current `loadCfg()` checks `EEPROM.length()` then uses `EEPROM.get()` without proving that the complete config image was read successfully; the test therefore exits 31 before reaching its recovery assertions. No fix for this separate issue is included in this UTC22 task.
- Relay/output run [#44413628747](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44413628747): ESP32 boot-polarity job succeeded; source-output job failed at the same config-read lab, after the poll-drain regression cases passed on both boards.
- Full build [#44413615638](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44413615638): validation job [135188137963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44413615638/job/135188137963) **FAILED** at inherited `Missing poll signature check`. ESP8266 and ESP32 compile jobs and all 13 firmware/platform target jobs were SUCCESS at last observation. Android was still IN PROGRESS; no completed Android pass or overall Full pass is claimed. Downstream simulations, update bundle, signing and publishing were skipped.

### Next bounded action and release limits

**Next PHX-HARDWARE action:** fix the separate ESP8266 `loadCfg()` full-image read-failure hazard with a status-bearing raw image read before decoding, defaults or `EEPROM.commit()`; preserve the existing poll-fault marker on transient and persistent read failure. Keep the existing failure lab's three scenarios: first read fails then full read recovers; two full-image reads fail and no commit occurs; persistent read failure remains deny-only and marker bytes survive. Coordinate any EEPROM layout/API assumptions with PHX-MASTER/PHX-CORE before changing shared semantics.

**PHX-QA / PHX-CORE:** the Full workflow's stale positive poll-signature assertion remains QA/contract-owned. Do not synthesize `response_sig` or weaken the default-deny consumer to make the old check pass.

Classification: poll-drain source behavior is **SIMULATED / CI subtest PASS**; the overall focused job is **FAIL** due to the separate config-read lab. Physical coin/relay, power-cut and electrical recovery acceptance remain **NOT TESTED**. PR #327 remains OPEN / DRAFT / UNMERGED. No flash, reset, migration, signer provisioning, merge, release or deployment occurred.


## UTC23 — full-image EEPROM read verification (2026-11-18T23Z)

**Disposition:** source correction committed; focused host/CI regression labs PASS; Full validation remains blocked by the inherited QA-owned poll-signature assertion. Hardware acceptance is NOT TESTED; production remains NO-GO.

### Defect and source correction

ESP8266 Arduino core 3.1.2 `EEPROMClass::begin()` invokes the flash read but does not expose its failure status to the sketch. An erased-looking or partially populated EEPROM RAM image therefore cannot be trusted as proof that the configuration region is blank.

Firmware source commit: `40cfc0799a6e65e4a724e8ccbe6baa0f5f51de54`

- Added `configImageReadVerified`, true only after a status-bearing read of the complete 544-byte EEPROM image and RAM-buffer reconciliation.
- Added `readFullEepromImage()`, using the EEPROM emulation sector mapping and `ESP.flashRead()` status.
- Added `restoreEepromRamImage()`, which copies the verified image into the EEPROM emulation buffer, preserving the reserved poll-fault record at offset 512.
- Added `refreshVerifiedEepromImage()`, which clears the verified flag and marks the backup unavailable on any full-image read/restore failure.
- `loadCfg()` now returns through the persistence-failure latch before reading configuration, applying defaults or committing when the complete image cannot be verified.
- `saveCfg()` and `writePollFaultBackup()` require a verified full image and revalidate after reopening the emulated EEPROM.
- `pollFaultBackupPresentOrCorrupt()` treats an unverified image as a deny condition.
- No EEPROM schema, offset or layout change; ESP32 source, shared financial semantics and QA-owned protocol validation were not modified.

Relevant source: [ESP8266 sketch, verified-image helpers](../esp8266/BlazePwifiVendo/BlazePwifiVendo.ino) (lines 391–423, 433–478, 618–647, 691–711).

### Test-first and CI evidence

The test-first RED was already present at the prior exact head: run [#44414150601](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44414150601), job `135189867065`, source/test SHA `ed667e88f6844284834ebd3a337dfce07a817e8c`; `config_load_read_failure_lab.py` exited 31.

The first correction attempt exposed stale host-lab adapters:
- [#44423553296](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423553296), job `135222434794`: generated C++ missing `configImageReadVerified`/helper declarations and a fake `EEPROM.end()` signature mismatch.
- [#44423560632](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423560632), job `135222459689`: stale `saveCfg` commit-failure instrumentation anchor.

Test-harness correction commit: `6b52d63f889a9567303f9f2de464c743c1991f0c`. It updates only hardware-owned source-extracted labs: `poll_fault_dual_store_lab.py` and `esp8266_boot_polarity_lab.py`.

Final exact-head focused evidence at source/test SHA `6b52d63f889a9567303f9f2de464c743c1991f0c`:
- PR quarantine [#44423903845](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423903845), job `135223655499`: PASS. Logs include:
  - `ESP8266_EEPROM_BEGIN_READ_FAIL_THEN_FULL_READ_RECOVER_MARKER_PRESERVED_PASS`
  - `ESP8266_EEPROM_RECOVERED_IMAGE_COLD_BOOT_DENY_PASS`
  - `ESP8266_EEPROM_FULL_READ_FAIL_MARKER_ONLY_RECOVERY_NO_COMMIT_PASS`
  - `ESP8266_EEPROM_FULL_READ_PERSISTENT_FAILURE_NO_COMMIT_PASS`
- Push quarantine [#44423897994](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423897994), job `135223632718`: PASS.
- Relay/output PR [#44423903842](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423903842), jobs `135223656681` and `135223657258`: PASS. Both boards passed 48/48 polarity scenarios; ESP8266 commit-failure trace, unknown-schema preservation, output-preload, poll-window and pulse-capture checks passed.

Full build:
- Push [#44423897080](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423897080): all 13 firmware/platform targets plus Android PASS (14 build jobs); validation job `135223766175` FAIL at `Missing poll signature check`; downstream simulation/update/signing jobs skipped.
- PR [#44423903891](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44423903891): all 13 firmware/platform targets plus Android PASS (14 build jobs); validation job `135223796039` FAIL at the same inherited assertion; downstream jobs skipped.

These are CI/host simulations, not flash-physics evidence. Logs explicitly retain `SIMULATED_ONLY=1` and `PHYSICAL_POWER_CUT_VERIFIED=0`.

### Coordination and provenance

- Full BLAZE-COMMS/1 checkpoint: [#172 comment 6995143780](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-6995143780).
- #177 pointer: [comment 6995144367](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177#issuecomment-6995144367).
- PR evidence: [#327 comment 6995144902](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327#issuecomment-6995144902).
- #327 remains OPEN/DRAFT/UNMERGED, stacked on #326 head `58c558fb6a237935214621adc3dee65a10fe1a51`.
- Revalidated stack: #239 `d83b715b116185107737fef721c2eece8feebf39`; #254 `4054fbccd9b2a4ad0e5fe7cfca5a27aa629eed84`; #283 `830c355376380f9b5533d5cda2558beed41a593a`; Master #288 `f16e17683cea47aee9bc48e96cf5b8b9ab16f780`.
- Experiments repository ownership is `BlazeDevStudio`; the former `BlazingSystems/BlazingSystems-Experiments` API endpoint returns Moved Permanently to repository ID `1389289885`.
- COE main remains `a6513ab4412b4c014eee2863e45cbe32d06cb243`; #26 and #44 remain OPEN/DRAFT. No COE or Labs/Projects source was modified.
- `README_FIRST(9).md`, `COMMUNICATION_PROTOCOL.md`, `README(10).md` and `phoenix-hourly-signal.yml` were read from Library. The signal remains signal-only.
- The exact owner upload `04_HARDWARE_FIRMWARE(1).txt` and private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` were not available in the searchable Library; no Google Drive connector was exposed. The full execution prompt in the active owner request was applied; registry provenance remains unverified.
- Repository rulesets query returned an empty list; branch-protection endpoint returned 403. Effective branch protection is therefore unverified.

### Remaining blockers and next action

1. PHX-QA must independently review the exact source/test SHA and reconcile the positive poll-signature assertion without enabling unauthenticated register/poll admission.
2. PHX-MASTER must refresh the #327 exact-head stack row.
3. PHX-HARDWARE will continue a non-destructive cold-boot audit with a valid non-erased configuration image under injected full-read failure, then verify that no defaults or writes occur.
4. Protected anti-rollback signer/witness, financial v1-to-v2 migration, durable accounting/replay, 150 real power cuts, 30-device/24-hour soak, electrical pulse/recovery and independent QA/release signoff remain outstanding.

No physical flashing, live coin/money operation, production migration, signer provisioning, merge, release or deployment occurred.


## UTC00 follow-up — exact ESP8266 EEPROM core buffer semantics (2026-11-19T00:50Z)

**Task:** P0 #177 / PR #327.  
**Role:** PHX-HARDWARE.  
**Docs/source-test starting HEAD:** `32cd2d2373623295ceba6fc10fd1f8a7d831af23`.  
**Test-only commit:** `32cd2d2373623295ceba6fc10fd1f8a7d831af23`.  
**Firmware runtime changes:** none in this follow-up.

### Official core audit and test-model correction

The official ESP8266 Arduino core 3.1.2 `EEPROM.cpp` was read directly:
[EEPROM.cpp at tag 3.1.2](https://github.com/esp8266/Arduino/blob/3.1.2/libraries/EEPROM/EEPROM.cpp).

The implementation:
- rounds the requested EEPROM size to four-byte alignment and caps it at one flash sector;
- allocates `new uint8_t[size]` only when no buffer exists or the size changes;
- reuses an existing same-size RAM buffer;
- calls `ESP.flashRead()` but only emits a debug message on failure; `begin()` returns no status and does not clear the buffer;
- resets `_dirty` after the attempted read.

The prior fake EEPROM model incorrectly reset its buffer to `0xFF` on every `begin()`, which did not model a same-size stale buffer after a failed read. It also described the failed-read buffer as necessarily erased-looking.

Test-only commit `32cd2d2373623295ceba6fc10fd1f8a7d831af23` corrects the model:
- deterministic `0xA5` poison represents indeterminate bytes in a newly allocated buffer;
- same-size `begin()` preserves the existing RAM allocation;
- size alignment, sector addressing and failed-read behavior follow the 3.1.2 implementation;
- a new source-extracted scenario seeds a pre-existing poll-fault marker, fills the same-size RAM buffer with stale poison, fails both the `begin()` flash read and the status-bearing full-image read, and asserts the stale bytes remain untrusted, no EEPROM write occurs, coin admission remains denied, the active target is cleared, and the marker survives a later cold boot.

### Exact-head CI

- Focused quarantine/readback [run #44431866549](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44431866549), job `135250957540`: **SUCCESS**. Logs include `ESP8266_EEPROM_SAME_SIZE_STALE_BUFFER_READ_FAILURE_DENY_PASS`, `EEPROM_CORE_3_1_2_BUFFER_SEMANTICS=MODELED`, all four prior full-image recovery cases, both-board poll-edge/pulse regressions, and explicit simulated-only / physical-power-cut-not-tested markers.
- Full BlazePwifi build [run #44431866576](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44431866576): **FAILURE** at validation job `135250958459`, `tests/controllers.sh` / `Missing poll signature check`. All 13 firmware/platform target jobs and Android completed **SUCCESS**. Downstream simulations, update bundle, signing, candidate gate and publishing were skipped.

This is source-extracted host/fake-I/O evidence only. It is **SIMULATED / CI VERIFIED**, not physical flash or hardware acceptance. No production configuration or financial migration was run.

### Next exact action

- **PHX-QA:** replace the inherited positive poll-signature presence assertion with negative/default-deny behavior tests and independently review the exact source/test SHA `32cd2d2373623295ceba6fc10fd1f8a7d831af23`.
- **PHX-MASTER:** refresh the #327 exact-head row and stack comparison.
- **PHX-HARDWARE:** next audit the local v1/v2 EEPROM configuration migration paths against a verified non-erased image, including malformed-record no-write behavior and reserved-marker preservation; do not alter the financial v1-to-v2 migration or shared ledger contract.

**Disposition:** PR #327 remains OPEN / DRAFT / UNMERGED. Physical acceptance remains NOT TESTED; production remains NO-GO.


## UTC01 — keep malformed/untrusted configuration non-writable after boot failure

**Task:** #177 / #172 — PHX-HARDWARE-owned ESP8266 local configuration safety correction.
**Source commit:** `5ad572f28fab4d5a018cdd4eb9ee395dd16ef69b`
**Branch head at source commit:** 5ad572f28fab4d5a018cdd4eb9ee395dd16ef69b
**Disposition:** source committed; focused CI VERIFIED; Full build validation FAILED at inherited QA-owned poll-signature assertion; physical acceptance NOT TESTED; PRODUCTION NO-GO.

### Defect and correction

`loadCfg()` intentionally refuses malformed v1/v2 records, invalid v3 records, and unknown non-erased schemas. However, `latchConfigPersistenceFailure()` previously left `configImageReadVerified` true after some parse/schema failures. `setupPortal()` starts the local WPA2 setup AP, whose `/save` handler can later call `saveCfg()`. Since `saveCfg()` uses the verified-image flag as its write gate, a subsequent local setup save could overwrite the exact malformed/unknown bytes that the boot path had just promised to preserve.

The failure latch now clears `configImageReadVerified` before setting the output/coin deny state. This preserves the existing EEPROM layout and marker bytes, prevents `saveCfg()` and `writePollFaultBackup()` from using that image after a configuration failure, and leaves the device deny-only until a separately reviewed recovery path exists. It does not add a remote override or change v1/v2 migration formats.

### Verification request / limits

- PHX-QA: independently add failure-injection vectors for malformed v1, malformed v2, unknown non-erased schema, and a later setup-save attempt; assert zero EEPROM commits and byte-for-byte preservation of the config region and existing poll-fault marker. Include commit-failure/reboot vectors where the fake model can distinguish definite failure from ambiguous persistence.
- Exact source SHA `5ad572f28fab4d5a018cdd4eb9ee395dd16ef69b`: quarantine/readback push [#44439012673](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44439012673), job `135274929637`, PASS; quarantine/readback PR [#44439018675](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44439018675), job `135274948740`, PASS; relay/output PR [#44439018914](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44439018914), jobs `135274949955` and `135274950911`, PASS. The existing EEPROM lab passes raw-read, same-size stale-buffer, and marker-preservation cases, but does not prove malformed-config followed by setup-save.
- Full docs-head build [#44439064420](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44439064420), validation job `135275207795`, completed FAILURE at inherited `Missing poll signature check`; all 13/13 firmware/platform targets and Android job `135275207254` completed SUCCESS; downstream simulation/update/signing/candidate/publishing jobs were skipped.
- PHX-QA request posted in #172/#177/#327 for malformed v1/v2/unknown-schema followed by setup-save failure injection, zero commits, and byte-for-byte config/marker preservation.
- No QA-owned tests directory, shared API, CORE ledger, EEPROM schema, marker offset, or financial migration was modified.


## UTC03 request-digest failure deny — 2026-11-19

**Task:** #172 / #177 / #327. **Scope:** ESP32/ESP8266 request signing only; no shared wire-contract, finance, receipt, migration, GPIO or admission behavior change.

### Test-first evidence

- Hardware-owned source-extracted lab: `esp8266/BlazePwifiVendo/request_digest_failure_lab.py`; compiles the real `signedBody()` and `post()` from both sketches while injecting empty, short and non-hex SHA-256 outputs at the `hexDigest()` boundary.
- Test-only head `87218da3c0f496eb7a260d303a292de1e3b4f279`: [focused RED run #44450313396](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44450313396), job `135312341724`; both ESP8266 and ESP32 failed at the expected guard assertion (exit 11), proving the old code built and dispatched a body with an empty signature.
- Source corrections: ESP32 `8b9d2153e5347df3d5f1fbea8c09b6d476f38079`; ESP8266 `071a711d6598c67124e84ffd995fd48aa7d9f054`.

### Firmware behavior

- Added `validSha256Hex()` requiring exactly 64 hexadecimal characters.
- `signedBody()` now returns empty on invalid digest and updates `lastSentNonce` only after digest validation.
- `post()` now returns before opening an HTTP client when the signed body is empty.
- Valid 64-character digest request bytes remain unchanged.

### Exact-head evidence

- Latest source/test head: `071a711d6598c67124e84ffd995fd48aa7d9f054`.
- Focused quarantine/readback [run #44450389343](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44450389343), job `135312580493`: SUCCESS. Both boards print `REQUEST_DIGEST_FAILURE_DENY_PASS`; empty/short/non-hex digests dispatch zero HTTP requests, while valid SHA-256 dispatches one. Existing poll-edge, EEPROM, marker, journal, quarantine and mutation suites also pass.
- Relay/output polarity [run #44450389393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44450389393), jobs `135312580868` and `135312581229`: SUCCESS.
- Full build [run #44450389363](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44450389363): validation job `135312677302` FAILED at inherited QA-owned `Missing poll signature check`. ESP8266 build job `135312677784` SUCCESS; ESP32 and remaining target jobs were still running at this handover update. Do not call this Full CI green.
- All evidence above is host/source-extracted simulation or CI, not physical flash/relay/coin acceptance.

### Coordination requests

- **PHX-QA:** independently verify both sketches at the exact source/test head; retain the empty/short/non-hex digest injections and assert zero HTTP begin/POST calls. Do not modify the shared response-signature fixture to manufacture a positive poll signature.
- **PHX-MASTER / PHX-CORE:** confirm the fail-closed request suppression is wire-compatible; no protocol fields or producer/consumer contract changed.
- **PHX-RELEASE:** read the completed ESP32 target result for the Mbed TLS 4 PSA compatibility path; this branch remains a draft candidate only.

**Disposition:** focused CI VERIFIED; SIMULATED only; physical acceptance NOT TESTED; production NO-go.


## Post-run exact-head reconciliation — 2026-11-19T03:26:05.612Z

The earlier sentence that ESP32 and remaining targets were still running is superseded by this final readback.

- The first test-only run [#44450228858](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44450228858) failed before reaching the assertion because the new lab's regex extractor was over-escaped. Corrected in test commit `87218da3c0f496eb7a260d303a292de1e3b4f279`.
- Corrected test-first RED [#44450313396](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44450313396), job `135312341724`: both boards failed at the intended empty-digest guard assertion (exit 11), reproducing the old behavior.
- Exact source/test GREEN remains [#44450389343](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44450389343), job `135312580493`: SUCCESS on ESP8266 and ESP32. Relay/output [#44450389393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44450389393): SUCCESS.
- Full run [#44450389363](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44450389363) completed with overall FAILURE at validation job `135314516017` (inherited `Missing poll signature check`). **All 13/13 firmware/platform build jobs succeeded** after the cancelled ESP32 job was rerun: ESP32 job `135314514743` compiled on `esp32:esp32@4.0.0` and uploaded artifact `14495587665`; ESP8266 job `135314567650` compiled successfully on `esp8266:esp8266@3.1.2`; the other 11 firmware/platform jobs also completed SUCCESS. Android job `135314575449` was CANCELLED and downstream release/simulation/publishing gates were skipped/cancelled. Do not call the overall Full workflow green.
- The ESP32 core 4.0.0 result is relevant to PHX-RELEASE's COE #35 toolchain-drift audit, but no COE files/workflows were changed by Hardware.

This is CI VERIFIED for the two board builds and source-extracted failure lab only. Physical relay, coin, flash, power-cut and soak acceptance remain NOT TESTED.


## BLAZE-COMMS/1 — PHX-HARDWARE UTC03 checkpoint

```json
{
  "protocol": "BLAZE-COMMS/1",
  "message_id": "PHX-HARDWARE-20261119T03-REQUEST-DIGEST-FAILCLOSED",
  "from": "PHX-HARDWARE",
  "to": [
    "PHX-MASTER",
    "PHX-QA",
    "PHX-CORE",
    "PHX-RELEASE"
  ],
  "type": "REQUEST_REVIEW",
  "priority": "P1",
  "task_id": "#172/#177/#327",
  "branch": "phoenix/hardware-prepoll-edge-abort-20261119",
  "base_sha": "58c558fb6a237935214621adc3dee65a10fe1a51",
  "scope": [
    "ESP32/ESP8266 validSha256Hex, signedBody and post fail-closed behavior",
    "hardware-owned request_digest_failure_lab.py and focused workflow",
    "narrow PHX-HARDWARE handover"
  ],
  "status": "BLOCKED",
  "evidence": [
    "source/test SHA 071a711d6598c67124e84ffd995fd48aa7d9f054",
    "docs/checkpoint head ec1068ee23282318952ef7387e1ecb43425210b8",
    "RED https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44450313396 job 135312341724",
    "focused GREEN https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44450389343 job 135312580493",
    "relay/output PASS https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44450389393",
    "Full validation failure and 13/13 target build results https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44450389363",
    "ESP32 core 4.0.0 compile job 135314514743 artifact 14495587665",
    "ESP8266 core 3.1.2 compile job 135314567650",
    "PR https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327"
  ],
  "blockers": [
    "Full validation fails at QA-owned Missing poll signature check; current main register/poll producer has no response_sig and no positive response-auth contract is approved",
    "Independent PHX-QA review of the new failure-injection lab is pending",
    "150 power cuts, 30-device 24-hour soak, electrical pulse/recovery and physical relay/coin acceptance are NOT TESTED",
    "Protected anti-rollback signer/witness, durable accounting/replay and financial v1-to-v2 migration are not evidenced",
    "Private Google Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json is not available through the current connector surface"
  ],
  "next_action": "PHX-QA independently review the exact source/test SHA 071a711d6598c67124e84ffd995fd48aa7d9f054 and validate that invalid digest outputs cause zero HTTP begin/POST calls; PHX-CORE must retain ownership of the poll response contract.",
  "updated_utc": "2026-11-19T03:26:48.799Z"
}
```


## UTC03 correction — local configuration failure/migration lab coverage

The earlier UTC01 handover sentence stating that malformed v1/v2 or unknown-schema followed by setup-AP save was not yet tested is **superseded at the source-extracted lab level** by the current exact source/test head `071a711d6598c67124e84ffd995fd48aa7d9f054`.

Focused quarantine/readback [run #44450389343](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44450389343), job `135312580493`, reports:

- `MALFORMED_V1_SETUP_SAVE_DENY_IMAGE_PRESERVED_PASS`
- `MALFORMED_V2_SETUP_SAVE_DENY_IMAGE_PRESERVED_PASS`
- `UNKNOWN_SCHEMA_SETUP_SAVE_DENY_IMAGE_PRESERVED_PASS`
- `VALID_V1_TO_V3_LOCAL_MIGRATION_MARKER_PRESERVED_PASS`
- `VALID_V2_TO_V3_LOCAL_MIGRATION_MARKER_PRESERVED_PASS`
- `V2_MIGRATION_COMMIT_FAILURE_SAME_BOOT_DENY_COLD_BOOT_RETRY_PASS`
- `ESP8266_EEPROM_SAME_SIZE_STALE_BUFFER_READ_FAILURE_DENY_PASS`

The lab explicitly prints `LOCAL_CONFIG_MIGRATION_LAB_ONLY=1 FINANCIAL_MIGRATION_TESTED=0 PRODUCTION_MIGRATION_AUTHORIZED=0`. This is **local device configuration** v1/v2-to-v3 source-extracted simulation, not the financial ledger v1-to-v2 migration, not physical EEPROM durability and not production migration acceptance. Independent PHX-QA review remains required.
