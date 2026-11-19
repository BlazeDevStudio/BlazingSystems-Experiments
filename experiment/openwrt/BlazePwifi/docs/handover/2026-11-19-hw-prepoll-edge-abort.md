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


## UTC03 addendum — Mbed TLS supported-major fail-closed guard (2026-11-19)

**Master assignment:** latest PHX-MASTER UTC02 checkpoint #6998343802 requested PHX-HARDWARE to resolve ESP32 Mbed TLS/toolchain compatibility on the hardware branch. The active #327 branch was revalidated at prior head `a3597125fef3964ab08f05b3300c8de3e47516ae`, base `58c558fb6a237935214621adc3dee65a10fe1a51`; PR #327 remains OPEN / DRAFT / UNMERGED.

**One scoped source correction:** commit [`11fae729`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/11fae729df415cc26b9e1675b1758cd8e4d22648), file `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`, blob `f54805b17cac45388dfacc5e65eff9b731234316`.

- Mbed TLS major 4 selects `<psa/crypto.h>` and the PSA SHA-256 path.
- Mbed TLS major 3 selects `<mbedtls/sha256.h>` and the legacy SHA-256 path.
- Any other major fails compilation with an explicit `#error`, rather than silently falling through to an unverified API.
- Existing provider-error checks remain: PSA init/hash status and exact 32-byte digest length; legacy starts/update/finish status.
- No request-body bytes, digest encoding, protocol/API, persistence schema, financial logic or coin-admission behavior changed.

**Exact current-source CI (SHA `11fae729df415cc26b9e1675b1758cd8e4d22648`):**

- Push Full [#44453227140](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44453227140): ESP32 job `135321984568` SUCCESS on `esp32:esp32@4.0.0` (sketch 1,095,025 bytes; globals 52,568 bytes); ESP8266 job `135321985132` SUCCESS; 13/13 firmware/platform targets SUCCESS; Android job `135321984823` SUCCESS. Validation job `135321984777` FAILED at the inherited QA-owned `Missing poll signature check`. 12 downstream release/simulation/signing/publishing jobs SKIPPED. Overall Full workflow FAILED.
- PR Full [#44453235564](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44453235564): ESP32 job `135322011864` SUCCESS on `esp32:esp32@4.0.0`; ESP8266 `135322011651` SUCCESS; Android `135322011311` SUCCESS; 13/13 firmware/platform targets SUCCESS. Validation job `135322011816` FAILED at the same inherited assertion; downstream gates SKIPPED. Overall Full workflow FAILED.
- Focused quarantine push [#44453227330](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44453227330), job `135321984757`: SUCCESS. Existing source-extracted persistence, configuration, digest-denial, pulse and poll-inhibit labs pass; logs explicitly mark `SIMULATED_ONLY=1` and physical power-cut acceptance zero.
- Focused quarantine PR [#44453235563](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44453235563), job `135322011247`: SUCCESS.
- Relay/output PR [#44453235544](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44453235544), job `135322010930`: SUCCESS.

**Mbed TLS 3.x evidence limitation:** earlier Experiments Full [#44439616677](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44439616677), ESP32 job `135276906877`, installed `esp32:esp32@3.3.13` and compiled successfully on the prior source head. The Mbed TLS 3 branch's SHA implementation was not changed by commit `11fae729`, but an exact-head 3.3.13 rebuild of `11fae729` has NOT YET RUN. The current Experiments build workflow installs an unpinned ESP32 core; PHX-RELEASE owns that workflow and is asked to provide a pinned 3.3.13 + 4.0.0 matrix or exact-head 3.3.13 run. No RELEASE-owned workflow was modified by Hardware.

**Cross-repository audit / request only:** COE #26/#35 destination blob `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` still has unconditional `<mbedtls/sha256.h>` and unchecked legacy SHA calls. Hardware did not edit or bulk-copy COE source. A scoped COE-INTEGRATION request was posted at [COE PR #26 comment #6999032274](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26#issuecomment-6999032274) to port the reviewed compatibility/error-propagation correction only after per-file provenance/ownership review; PHX-RELEASE is asked to pin and verify supported majors; PHX-QA is asked to independently test provider-error denial and unsupported-major compile rejection.

**Disposition:** current Experiments ESP32 firmware is CI VERIFIED on Mbed TLS 4 / ESP32 core 4.0.0 at exact source SHA `11fae729`; prior Mbed TLS 3 / core 3.3.13 build passed on an earlier source head, but exact-head 3.3.13 remains NOT TESTED. Full validation remains FAILED for the unrelated QA-owned poll-signature assertion. No positive poll authentication is implemented. No hardware flashing, physical relay/pulse acceptance, financial migration, signing, merge, release or deployment occurred. PRODUCTION NO-GO.


## UTC04 — ESP32 setup NVS configuration readback gate (2026-11-19)

**Task:** hardware-owned ESP32 setup-save integrity; no shared API, schema, finance, or destination migration.

- Firmware commit: [1475e100](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/1475e100af0812d0fa17c178f8444611fc924fa0)
- File: \`experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino\`
- New \`configFieldsMatchStored()\` requires every persisted SSID/password/server/key/device-ID, GPIO, coin polarity, debounce and pulse-group key to exist and read back exactly before \`persistLocalOutputPolarity()\` may publish \`polarityv=1\`.
- \`saveConfig()\` now forces insert mode/target off before writes. Any polarity-marker, field-readback or polarity-profile failure returns false and revokes \`outputPolarityKnown\` / \`pinConfigSafe\`; the setup route does not reboot or claim success.
- No NVS namespace/key/schema change, no wire/API change, no financial or coin-admission positive path.

**Exact-head CI initiated:** source SHA \`1475e100af0812d0fa17c178f8444611fc924fa0\`.
- Push quarantine/readback [#44460939893](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44460939893): IN_PROGRESS at handover update.
- PR quarantine/readback [#44460945811](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44460945811): IN_PROGRESS.
- Push relay/output [#44460945803](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44460945803): IN_PROGRESS.
- Push Full [#44460939672](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44460939672): IN_PROGRESS.
- PR Full [#44460945920](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44460945920): QUEUED.

**Independent review requested:** PHX-QA should inject failure/short-write/readback mismatch for each NVS config field and verify the polarity-valid marker remains invalid and no output can energize on the same boot or cold boot. The current existing labs do not yet establish that new ESP32 setup-save failure matrix. This handover does not claim that coverage.

**Disposition:** source change committed; CI pending; source-extracted/physical setup-write failure acceptance NOT TESTED until independent QA evidence. Physical relay, coin, power-cut and 30-device soak acceptance remain NOT TESTED. PRODUCTION NO-GO.


## UTC04 follow-up — ESP32 NVS config readback and exact-head CI

**Firmware source commits:** initial readback gate \`1475e100af0812d0fa17c178f8444611fc924fa0\`; source-shape compatibility correction \`8f08a9bbbe3ce9b816e18ec1e6870a1f9c820926\`. Current ESP32 sketch blob: \`c29483f0761ca6e2db0573bd12d6bfa502f12434\`.

The initial implementation correctly added per-field NVS presence/readback checks, but exact PR relay lab #44460945803 failed its existing source-contract assertion because \`saveConfig()\` no longer retained the canonical first-invalidation guard and direct \`return persistLocalOutputPolarity();\` form. This was a real test failure, not hidden. Commit \`8f08a9b\` restored the explicit guard/direct return while retaining the new all-field readback gate and revoking runtime output/pin safety before polarity persistence. No QA test was modified.

**Exact source SHA \`8f08a9bbbe3ce9b816e18ec1e6870a1f9c820926\`:**
- Quarantine/readback push [#44461480031](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44461480031), job \`135349045121\`: PASS.
- Quarantine/readback PR [#44461486014](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44461486014), job \`135349065899\`: PASS.
- Relay/output PR [#44461486038](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44461486038): PASS; source-output job \`135349066774\` PASS; ESP32 boot-polarity job \`135349066332\` PASS (\`ESP32_BOOT_POLARITY_GATE=PASS\`, \`UNKNOWN_AND_LEGACY_PROFILE_REMAINS_INPUT=PASS\`, \`LOCAL_POLARITY_MARKER_READBACK=PASS\`, \`ACTIVE_HIGH_AND_ACTIVE_LOW_OFF_PRELOAD=PASS\`).
- Full PR [#44461486025](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44461486025): overall FAILURE at validation job \`135349066851\`, exact message \`Missing poll signature check\` (QA-owned stale positive-presence fixture). All 13/13 firmware/platform target jobs and Android passed; ESP32 job \`135349067079\` compiled on \`esp32:esp32@4.0.0\` (sketch 1,096,577 bytes / 83%; globals 52,568 bytes / 16%; artifact \`14500660630\`, ZIP SHA-256 \`34adeaf0381ea37e0ac6a8611f411efd712d1751612333d0e6fba279acf86c8e\`). Downstream simulations, signing, candidate and publishing were skipped.
- Full push [#44461480050](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44461480050): at this handover, all 13/13 firmware/platform target jobs passed, including ESP32 and ESP8266; Android was still running, so the push run was not yet terminal.

**Coverage limitation:** existing \`esp32_boot_polarity_lab.py\` verifies boot polarity, unknown/legacy profile INPUT behavior, marker readback and active-high/low OFF preload. It does **not** inject failure into each new \`configFieldsMatchStored()\` NVS field or readback mismatch. PHX-QA must independently add/run that failure matrix and verify no \`polarityv=1\` commit plus current/cold-boot output denial. Exact-current-source ESP32 core 3.3.13 and unsupported Mbed TLS major compile rejection remain NOT TESTED; PHX-RELEASE/PHX-QA are requested to provide those exact-head checks.

**Disposition:** focused source-extracted labs and ESP32 core 4.0.0 build CI VERIFIED; Full workflow remains FAILED at the unrelated QA-owned poll-signature assertion; new per-field config-save failure matrix NOT TESTED; physical relay/coin/power-cut/soak/electrical acceptance NOT TESTED; PRODUCTION NO-GO.


## UTC04 terminal Full-run reconciliation

The two exact-source Full runs have now reached terminal state. The earlier note that the push run was still running is superseded by this reconciliation:

- Full push [#44461480050](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44461480050): **FAILURE** at validation job \`135349046384\`, exact message \`Missing poll signature check\`. All 13/13 firmware/platform target jobs passed and Android passed. ESP32 job \`135349046395\` compiled with \`esp32:esp32@4.0.0\`, artifact \`14500591631\`, ZIP SHA-256 \`d1273182e3be7d69f828e1e2ce9656a8e4914ae518006281e943ff6693348341\`.
- Full PR [#44461486025](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44461486025): **FAILURE** at validation job \`135349066851\`, same assertion. All 13/13 firmware/platform target jobs and Android passed. ESP32 job \`135349067079\` compiled with \`esp32:esp32@4.0.0\`, artifact \`14500660630\`, ZIP SHA-256 \`34adeaf0381ea37e0ac6a8611f411efd712d1751612333d0e6fba279acf86c8e\`.
- Focused quarantine push/PR and relay/output PR runs remain PASS at exact firmware source SHA \`8f08a9bbbe3ce9b816e18ec1e6870a1f9c820926\`.

No Full validation or downstream release gate is considered passed. The positive poll-signature assertion remains QA-owned and incompatible with current main register/poll responses. The new per-key ESP32 NVS failure matrix, exact-head Mbed TLS 3.3.13 build, and unsupported-major compile rejection remain NOT TESTED.

## UTC05 — valid non-erased ESP8266 configuration preservation under read failure (2026-11-19)

**Role:** PHX-HARDWARE. **PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327), OPEN / DRAFT / UNMERGED. The pre-handover PR head was \`2f1a209014e35768cab67a0d2c50c9c44bf54f77\`; base branch remains \`phoenix/hardware-pending-write-fault-latch-20261119\` at \`58c558fb6a237935214621adc3dee65a10fe1a51\`.

### One hardware-owned test change

Test commit [\`2f1a209\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/2f1a209014e35768cab67a0d2c50c9c44bf54f77) changes only \`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/config_load_read_failure_lab.py\`. No firmware, schema, protocol, finance, workflow or other-role files changed.

The new exact-source host scenario seeds a valid non-erased v3 configuration image plus a pre-existing poll-fault record, injects failure into both the \`EEPROM.begin()\` raw read and the subsequent full-image read, and asserts:
- \`loadCfg()\` leaves the in-RAM \`Config\` byte-for-byte zero/unmodified rather than applying defaults;
- outputs/insert mode remain denied and the recovery latch is set;
- no EEPROM commit/write occurs, \`saveCfg()\` remains blocked, and the complete fake-flash image plus fault marker remain byte-for-byte unchanged;
- a later cold boot with readable flash loads the original v3 SSID/configuration and still observes the existing poll-fault deny marker.

The test-first RED mutation removes the production \`refreshVerifiedEepromImage()\` guard. It is rejected with exit 58. The unmutated exact source prints \`VALID_V3_IMAGE_READ_FAILURE_PRESERVE_COLD_BOOT_PASS\`.

### Exact GitHub Actions evidence

- Focused quarantine/readback push [#44464397498](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44464397498), job \`135358569783\`: **SUCCESS**. Logs show the RED mutation rejection, the new GREEN scenario, and existing EEPROM read/recovery, malformed v1/v2, unknown-schema, local v1/v2-to-v3 migration, and failed-migration retry-denial cases. The lab explicitly reports \`LOCAL_CONFIG_MIGRATION_LAB_ONLY=1 FINANCIAL_MIGRATION_TESTED=0 PRODUCTION_MIGRATION_AUTHORIZED=0\`.
- Relay/output push [#44464397488](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44464397488): source-output job \`135358569594\` and ESP32 boot-polarity job \`135358569837\` **SUCCESS**.
- Full push [#44464397509](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44464397509): 13/13 firmware/platform target jobs **SUCCESS**; Android job \`135358570586\` **SUCCESS**. ESP32 job \`135358570392\` compiled (1,096,577 bytes / 83%; globals 52,568 bytes / 16%; artifact \`14501123685\`, ZIP SHA-256 \`34678d6251e5b7c353a73990ed20456ee2b21e5193765390c59003ddc02e5bb0\`). ESP8266 job \`135358570613\` compiled with core 3.1.2 (320,896 bytes / 30%; artifact \`14501163659\`, ZIP SHA-256 \`1f4ac7983f729df9d7420acd8d0b678bc0666eda1a50830eaf44685bb2bf63e2\`). The ESP32 core install in this workflow is floating/unpinned; this run is not evidence of the exact-head 3.3.13 matrix requested from PHX-RELEASE.
- Full validation job \`135358570696\`: **FAILURE**, exact inherited QA assertion \`Missing poll signature check\` in the ESP8266 sketch. Downstream update-bundle, simulations, signing and release publication were skipped. This is not a compile failure and was not bypassed.

### Issue #177 P0 cross-check — source candidate only

The new PHX-L-VERIFY finding describes a missed coin pulse while the legacy \`9df0a7e\` source leaves the acceptor relay energized during synchronous poll. The current #327 candidate already contains the hardware-owned \`pollIntakeSuspended\` / \`beginPollWindow()\` inhibit, quiet-after-inhibit drain, ISR edge reconciliation before and after HTTP, and sticky fault persistence. In the same exact focused run, both board source-extracted labs print \`POLL_BLOCKED_EDGE_FAULT_PASS 7/7\` and \`POLL_EDGE_SNAPSHOT_RACE_PASS\`; mutations removing the poll window, inhibit, quiet window, ISR delta or fault marker are rejected. This is **SIMULATED / CI VERIFIED only**. It does not prove the physical acceptor supply is actually de-energized, pulse conditioning under electrical noise, or recovery on a real board. Main remains unchanged; Master must select/integrate the candidate after independent review.

### Parallel PR audit

- #239 head \`d83b715b...\`; #254 head \`4054fbcc...\`; #283 head \`830c355376380f9b5533d5cda2558beed41a593a\`; parent #326/base \`58c558fb...\`; Master PR #288 coordination head \`8d98f7c61e01bbde9fbafb79e22b6fa01f09acd2\`.
- #283 latest audit comment [#7000278012](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283#issuecomment-7000278012): unconditional clear-after-failed-append is no longer present, but \`quarantinePending()\` remains definition-only (no active callsite); register/poll \`response_sig\` remains absent/unapproved and current main's register/poll replies do not emit it. Keep #283 deny-only / DRAFT; no edits by this run.

### Registry/provenance limitation

The Library root was paged through 1,422 items. It contains registry snapshots through \`BLAZE_PROJECT_REGISTRY_v7_20261027.json\`, but not the requested private \`BLAZE_PROJECT_REGISTRY_v11_20261027.json\`. No Google Drive connector is exposed in this run. Do not substitute v7 for v11 or use it as code-promotion authority.

### Disposition / next exact action

Local EEPROM configuration preservation is **SIMULATED / CI VERIFIED** at the test SHA; ESP32/ESP8266 and 13 firmware/platform targets compile in the current floating-core Full run. Full validation remains FAILED at the QA-owned poll-signature fixture. Exact-current-source ESP32 core 3.3.13, unsupported-major compile rejection, independent per-key ESP32 NVS failure injection, financial v1-to-v2 migration, durable accounting/replay, protected signer/witness, and all physical acceptance remain NOT TESTED or NOT ESTABLISHED.

**PHX-QA:** independently review the valid-v3 read-failure case and inject each NVS field/readback failure on its own branch; do not weaken default-deny to satisfy the stale poll-signature fixture. **PHX-RELEASE:** provide the exact-head pinned ESP32 core 3.3.13/4.0.0 build matrix. **PHX-CORE:** publish the canonical authenticated register/poll response contract. **PHX-MASTER:** decide how the #177 P0 candidate and #327 stack enter the integration matrix. No hardware flash, physical power-cut test, coin/finance operation, migration, signer provisioning, merge, release or deployment occurred. **PRODUCTION NO-GO.**



## UTC05 follow-up — Mbed TLS selector and digest failure-path coverage (2026-11-19)

**Master request:** PHX-MASTER UTC03/UTC04 requested explicit Mbed TLS 3.x branch coverage and unsupported-major compile rejection. This follow-up is limited to the ESP32 hardware-owned compatibility selector and hexDigest() implementation.

### One hardware-owned test/CI change

- Added experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/mbedtls_compat_guard_lab.py.
- The lab extracts the actual selector and hexDigest() function from the production sketch rather than copying the branch logic into the test.
- It compiles the Mbed TLS 3 legacy SHA branch and Mbed TLS 4 PSA branch against deliberately small API stubs.
- Failure injection verifies Mbed TLS 3 starts/update/finish errors return an empty digest; Mbed TLS 4 PSA init/hash errors and a non-32-byte digest length also return empty.
- Unsupported major versions 2 and 5 must fail compilation with the exact firmware #error diagnostic.
- Added the lab to the hardware-owned phx-hardware-quarantine-byte-readback.yml workflow.

**Important limitation:** this is a source-extracted selector/control-flow lab with stub APIs. It is not a real Mbed TLS 3.3.13 library build, not cryptographic known-answer verification, and not a substitute for PHX-RELEASE's pinned exact-head Arduino build.

### Exact source and CI evidence

**Source/test + workflow commit:** 0e5514adb0088649eca8bec9df6215faa50b556c.

- Quarantine/readback push [#44467340819](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44467340819), job 135368184074: **SUCCESS**.
- Quarantine/readback PR [#44467350247](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44467350247), job 135368212650: **SUCCESS**.
- Exact log markers: MBEDTLS_MAJOR_3_SELECTOR_AND_DIGEST_PASS, MBEDTLS_MAJOR_4_SELECTOR_AND_DIGEST_PASS, MBEDTLS_UNSUPPORTED_MAJOR_2_REJECTED, MBEDTLS_UNSUPPORTED_MAJOR_5_REJECTED, MBEDTLS_COMPATIBILITY_GUARD_LAB_PASS.
- The same quarantine logs also retain the existing request-digest failure-deny, NVS error-deny and valid-v3 EEPROM image-preservation scenarios.

**Full workflow remains blocked:**
- Push Full [#44467340845](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44467340845), validation job 135368185015: **FAILURE**, inherited Missing poll signature check in the ESP8266 sketch.
- PR Full [#44467350270](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44467350270), validation job 135368213733: same **FAILURE**.
- ESP8266 compile jobs completed SUCCESS. Other target jobs were still running at this checkpoint; release/simulation downstream jobs were skipped after validation failure. No Full validation pass is claimed.

No firmware source, cryptographic wire contract, shared schema, finance, QA-owned tests, COE destination or release-owned workflow changed in this task.

### Next exact actions

- **PHX-RELEASE:** provide a pinned exact-head ESP32 build using core 3.3.13 and 4.0.0 against the current sketch. The actual 3.3.13 build remains **NOT TESTED**.
- **PHX-QA:** independently review this compatibility lab and own the per-key ESP32 NVS write/readback failure matrix; reconcile the stale positive poll-signature assertion without weakening default-deny.
- **PHX-MASTER:** decide the #326/#327 integration sequence after QA review.

**Disposition:** Mbed TLS selector and digest error-control paths are **SIMULATED / CI VERIFIED**. Real Mbed TLS 3.3.13 exact-head build, physical electrical/power acceptance, financial migration, durable accounting/replay, protected witness, and independent QA/release acceptance remain **NOT TESTED / NOT ESTABLISHED**. PR #327 remains OPEN / DRAFT / UNMERGED; PRODUCTION NO-GO.


## UTC05 terminal Full-build reconciliation — exact docs head b45af38 (2026-11-19)

This supersedes the earlier note that target jobs were still running.

**Exact docs head tested:** b45af38e7d59bf409d6742d2007005b5925bf5eb. **Firmware/test source commit:** 0e5514adb0088649eca8bec9df6215faa50b556c.

### Terminal Full results

- Push Full [#44467794879](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44467794879): **FAILURE** at validation job 135369667217, exact message "Missing poll signature check" in the ESP8266 sketch. All 13 firmware/platform target jobs and Android completed SUCCESS. ESP32 job 135369667090 compiled with esp32:esp32@4.0.0; ESP8266 job 135369667137 compiled with esp8266:esp8266@3.1.2. All simulation, candidate, signing and publishing downstream jobs were skipped.
- PR Full [#44467800422](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44467800422): **FAILURE** at validation job 135369685670, same inherited assertion. All 13 firmware/platform target jobs and Android completed SUCCESS. ESP32 job 135369685621 compiled with esp32:esp32@4.0.0; ESP8266 job 135369685426 compiled with esp8266:esp8266@3.1.2. ESP32 artifact 14502508693; ESP8266 artifact 14502554063. All simulation, candidate, signing and publishing downstream jobs were skipped.

### Focused current-head results

- Quarantine/readback PR [#44467800414](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44467800414), job 135369684752: **SUCCESS**. Exact log markers include Mbed TLS 3 and 4 selector/digest pass, unsupported major 2 and 5 rejected, valid-v3 EEPROM image preservation, dual-store deny, request-digest deny and poll-edge race pass.
- Relay/output PR [#44467800464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44467800464), source-output job 135369685402 and ESP32 boot-polarity job 135369685711: **SUCCESS**.

The Full failure is a validation/test-contract failure, not an ESP32 or ESP8266 compilation failure. Do not satisfy it by adding an unauthenticated positive poll signature. PHX-CORE must define the canonical producer/consumer response envelope; PHX-QA owns the independent fixture/extractor correction.

**Still NOT TESTED:** real exact-head ESP32 core 3.3.13 build; actual Mbed TLS 3.3.13 library/API compatibility; physical coin/relay timing; 150 power cuts; 30-device 24-hour soak; electrical pulse/recovery; protected signer/witness; financial v1-to-v2 migration and durable accounting/replay.

**Disposition:** 13/13 firmware/platform targets + Android are CI VERIFIED on the current source; focused Mbed TLS selector lab is SIMULATED / CI VERIFIED; Full validation remains FAILED; HARDWARE ACCEPTED and PRODUCTION READY are NOT established. PR #327 stays OPEN / DRAFT / UNMERGED / PRODUCTION NO-GO.


## UTC05 terminal current-head reconciliation — f00e66d (supersedes in-progress note)

**Exact tested docs head:** f00e66d2869ca14c655baf2d921c31e458a49838. **Source/test commit:** 0e5514adb0088649eca8bec9df6215faa50b556c.

Both current-head Full workflows are now terminal **FAILURE** only at the inherited QA-owned poll-signature validation assertion:

- Push Full [#44468386658](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44468386658), validation job 135371588199: **FAILURE**, exact message "Missing poll signature check" in ESP8266. All 13 firmware/platform target jobs and Android completed SUCCESS. ESP32 core 4.0.0 job 135371587958; ESP8266 core 3.1.2 job 135371588177. Downstream simulations, candidate gate, signing and publishing skipped.
- PR Full [#44468394103](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44468394103), validation job 135371611487: same **FAILURE**. All 13 firmware/platform target jobs and Android completed SUCCESS. ESP32 core 4.0.0 job 135371611233; ESP8266 core 3.1.2 job 135371611473. Downstream simulations, candidate gate, signing and publishing skipped.

Current-head focused CI:
- Quarantine/readback PR [#44468394101](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44468394101), job 135371610358: **SUCCESS**, including Mbed TLS selector/digest tests, unsupported major 2/5 compile rejection, valid-v3 EEPROM preservation, poll-edge failure deny and request-digest failure deny.
- Relay/output PR [#44468394117](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44468394117), jobs 135371610544 and 135371610891: **SUCCESS**.

This is not a Full CI pass: validation failed and all downstream production/simulation/signing/publishing jobs were skipped. Exact-head ESP32 core 3.3.13 remains NOT TESTED; current ESP32 build uses core 4.0.0. The Mbed TLS 3 branch lab uses stub APIs only. Keep poll admission fail-closed and do not satisfy the legacy assertion by accepting unauthenticated signatures. PR #327 remains OPEN / DRAFT / UNMERGED / PRODUCTION NO-GO.

## UTC06 follow-up — C++ line-spliced comment extraction (2026-11-19)

**Task:** #177 / PR #327, PHX-HARDWARE-owned test-extractor reliability. This is a host-test parser correction only; no production sketch, poll contract, wire format, NVS/EEPROM schema, financial path or output behavior changed.

### Proven defect

The shared firmware_lab_source.py mask_non_code() stopped // comments at the first CR/LF. C++ translation phase 2 removes a backslash-newline pair before comment recognition, so a fake function definition on the continued line remained visible to extract_functions(). A source-extracted lab could therefore select comment text as if it were production code.

### Test-first evidence and correction

- Intermediate fixture commit c99768e3403a2350948d7f92321ecdb60392e947 had an incorrectly escaped fixture and is **not** used as RED evidence; it was superseded.
- Correct LF fixture commit 0a9ea0cebbff4bdffc5d8b2a84ba49c7916eeee8 produced expected RED: push [#44472972445](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44472972445), job 135386651744, failed exactly with AssertionError: backslash-newline // comment exposed a fake function.
- Fix commit a73af2552a2d7c0f89bbda485fe2c0db00bd04f6 now continues a // comment across LF or CRLF only when the line ending is immediately preceded by a backslash. It preserves source length and newline offsets.
- CRLF fixture commit 1a6da55e537375ec44e7637d5a83d26318b3f604 covers both LF and CRLF continuation and asserts CRLF positions remain unchanged.

### Exact-head CI

Exact source/test SHA: 1a6da55e537375ec44e7637d5a83d26318b3f604.

- Push quarantine/readback [#44473082805](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44473082805), job 135387009446: **SUCCESS**. Logs: POLL_FAULT_EXTRACTOR_SELFTEST=PASS, POLL_FAULT_DUAL_STORE_LAB=PASS board=ESP32, POLL_FAULT_DUAL_STORE_LAB=PASS board=ESP8266; existing poll/pulse failure mutations rejected. SIMULATED_ONLY=1, PHYSICAL_POWER_CUT_ACCEPTANCE=0.
- PR quarantine/readback [#44473090673](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44473090673), job 135387034342: **SUCCESS** on the same SHA.
- PR relay/output [#44473090588](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44473090588), jobs 135387034206 and 135387034447: **SUCCESS** on the same SHA.
- Full push [#44473082040](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44473082040): validation job 135387053332 **FAILED** at the inherited QA-owned Missing poll signature check. ESP8266 job 135387053241 passed; ESP32 job 135387053174 and the remaining target matrix were still running at the last observation.
- Full PR [#44473090543](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44473090543): validation job 135387085146 **FAILED** at the same assertion. ESP32 job 135387085564 and ESP8266 job 135387085736 passed; Android and some other target jobs were still running at the last observation. No Full workflow pass is claimed.

### Coordination / boundaries

- Latest PHX-RELEASE UTC06 assignment is #172 comment [#7001624265](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-7001624265): RELEASE owns the pinned exact-source ESP32 core 3.3.13/4.0.0 workflow on PR #291. PHX-HARDWARE did not edit .github/workflows/.
- PHX-QA retains ownership of the per-key ESP32 NVS failure matrix and positive poll-signature fixture reconciliation. Do not change the deny-only poll behavior to satisfy the stale assertion.
- The exact private Drive registry v11 remains unavailable through the exposed Library/connector surfaces; no older registry was substituted.

**Disposition:** shared source extractor LF/CRLF line-splice behavior is **CI VERIFIED** as test infrastructure. Firmware hardware acceptance remains **NOT TESTED**; Full validation remains failed; PR #327 remains OPEN / DRAFT / UNMERGED; production remains **NO-GO**.

## UTC06 terminal Full-build correction — exact source/test SHA 1a6da55

This supersedes the earlier in-progress target-matrix note above.

- Full push [#44473082040](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44473082040): **COMPLETED FAILURE** only at validation job 135387053332, exact message "Missing poll signature check" in the ESP8266 sketch. All 13 firmware/platform target jobs passed, including ESP32 job 135387053174 and ESP8266 job 135387053241; Android job 135387053462 passed. Simulation, update bundle, candidate, signing and publishing jobs were skipped.
- Full PR [#44473090543](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44473090543): **COMPLETED FAILURE** at validation job 135387085146 with the same exact assertion. All 13 firmware/platform target jobs passed, including ESP32 job 135387085564 and ESP8266 job 135387085736; Android job 135387085620 passed. All downstream simulation/candidate/signing/publishing jobs were skipped.
- These are Full workflow failures, not Full CI passes. The poll-signature assertion remains QA-owned and conflicts with current deny-only register/poll behavior. No unauthenticated positive signature was added.

The exact source/test SHA 1a6da55 is focused-CI verified for the line-spliced-comment fix; the latest documentation successor is 78c3d6f83c81401e7700b32f4478bd3b21c03dd3. Production remains NO-GO.

## UTC06 cross-role audit — PHX-RELEASE exact ESP32 core matrix

The latest Master coordination PR #288 is now at b44df280cd93a4a8893d5e486e9564d56a913489. Its UTC06 report and ROLE_ASSIGNMENTS keep Hardware ownership in esp32/esp8266 source and leave release workflows with PHX-RELEASE. No ownership transfer was made.

PHX-RELEASE's existing PR #291 advanced to b2b523dce7c994d4c8431ea3d7651990f4fb8493 and ran [#44473417412](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44473417412) against exact Hardware source commit 0e5514adb0088649eca8bec9df6215faa50b556c and ESP32 sketch blob c29483f0761ca6e2db0573bd12d6bfa502f12434.

Both matrix jobs verified the exact source/blob, pinned Arduino CLI 1.6.0, verified the Arduino CLI archive, installed and verified the requested ESP32 core, and ran the compile command:
- Core 4.0.0 job 135389001694: compiler reported 1,096,577 bytes program storage (83%) and 52,568 bytes globals (16%).
- Core 3.3.13 job 135389002084: compiler reported 1,042,632 bytes program storage (79%) and 49,952 bytes globals (15%).

Both jobs then failed in the same shell step after compilation. The final printf uses an extra escaped dollar before the GitHub matrix expression; GitHub renders it as "$4.0.0" or "$3.3.13", and Bash with set -u fails on the unset positional parameter ($4 / $3). The binary was found and sha256sum was invoked, but the printf failed before the binary hash was emitted; no artifact upload occurred. These are **compile-command-success observations inside failed workflow jobs**, not end-to-end compatibility-job PASS results.

PHX-HARDWARE posted a scoped audit request to [PR #291 comment #7001879641](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/291#issuecomment-7001879641), suggesting removal of the extra leading dollar or use of an environment variable. PHX-HARDWARE did not edit RELEASE-owned workflow/script files. RELEASE must correct and rerun both matrix jobs to produce a successful job and retained binary hashes.


## UTC07 follow-up — C++ phase-2 comment-token splices (2026-11-19)

**Task:** PR #327 / P0 #177, PHX-HARDWARE-owned host-lab source extractor reliability. This correction affects only test infrastructure; no ESP32/ESP8266 sketch, GPIO/output behavior, poll contract, wire format, NVS/EEPROM schema, financial path, QA-owned test, or Release-owned workflow changed.

### Proven defect and test-first reproduction

firmware_lab_source.py::mask_non_code() recognized // and /* only when the two delimiter characters were physically adjacent. C++ translation phase 2 removes backslash-newline pairs before phase-3 comment recognition, so a splice can form a comment opener or terminator. The old extractor could expose a fake function inside a line-spliced comment, or report a valid block comment as unterminated.

- Corrected fixture commit: 5224a1b98add4fdf86e3fd038002c60f5b6b7f48.
- Expected RED: push quarantine [#44476732076](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44476732076), job 135398979315, failed at AssertionError: line-spliced // opener exposed a fake function.
- Fix commit: c37338439eec23c54a2e4a5f9c9c538d08f182cf.
- The helper now recognizes comment delimiters across LF, CRLF, and CR line splices while preserving original source offsets and newline positions; block-comment openers and terminators use the same physical-offset-aware delimiter check.

### Exact-source CI

- Push quarantine [#44476885288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44476885288), job 135399482572: SUCCESS.
- PR quarantine [#44476892512](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44476892512), job 135399504538: SUCCESS. Logs include POLL_FAULT_EXTRACTOR_SELFTEST=PASS and POLL_FAULT_DUAL_STORE_LAB=PASS for ESP32 and ESP8266.
- PR relay/output [#44476892390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44476892390), jobs 135399504402 and 135399504589: SUCCESS.
- Full PR [#44476892346](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44476892346), validation job 135399615620: FAILURE at the inherited QA-owned Missing poll signature check in tests/controllers.sh. Other target jobs were still running at the last read; no Full pass is claimed. Full push [#44476885339](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44476885339) was still in progress at that read.

This establishes CI VERIFIED test-infrastructure correctness only. It does not establish physical flash, pulse, relay, EEPROM/NVS durability, financial migration, power-cut or hardware acceptance. Keep all coin/poll admission deny-only.



## UTC07 terminal Full-workflow reconciliation

The earlier in-progress Full note above is superseded by the terminal results for exact source/test SHA c37338439eec23c54a2e4a5f9c9c538d08f182cf:

- Full push [#44476885339](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44476885339): FAILURE at validation job 135399612997, exact assertion "Missing poll signature check" in the QA-owned controller fixture. All 13/13 firmware/platform target jobs and Android completed SUCCESS. Downstream simulation, update, candidate, signing and publishing jobs were skipped.
- Full PR [#44476892346](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44476892346): CANCELLED after validation job 135399615620 failed at the same assertion. Twelve of thirteen firmware/platform target jobs completed SUCCESS; x86_64 and downstream simulation/candidate/publishing jobs were cancelled. Android completed SUCCESS.
- These Full outcomes are separate from the passing focused hardware labs. The positive poll-signature assertion is QA-owned; do not change firmware to accept an unauthenticated poll response.



## UTC07 terminal verification on documentation head 705d20b

The documentation-only handover successor was also revalidated at exact PR head 705d20b67cd1eb2b6bd5a7969e4ab7df01237337. The firmware lab source/test remains c37338439eec23c54a2e4a5f9c9c538d08f182cf.

- Quarantine PR [#44477810677](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44477810677), job 135402489862: SUCCESS.
- Relay/output PR [#44477810173](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44477810173), jobs 135402489680 and 135402490014: SUCCESS.
- Full PR [#44477810675](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44477810675), validation job 135402490107: FAILURE at the QA-owned Missing poll signature check. All 13 firmware/platform target jobs and Android completed SUCCESS; downstream simulation, signing and publishing were skipped.
- Full push [#44477802363](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44477802363), validation job 135402506764: FAILURE at the same assertion. All 13 firmware/platform target jobs and Android completed SUCCESS; downstream simulation, signing and publishing were skipped.

This exact documentation-head verification supersedes the earlier partial/in-progress notes. It remains CI evidence for host-test infrastructure and firmware compilation only, not physical hardware acceptance.

## UTC07 NVS commit durability-model correction — 2026-11-19

**Disposition:** hardware-owned host-lab correction; focused CI VERIFIED; Full validation remains blocked; production NO-GO.

### Proven test-model defect

The ESP32 fake NVS backend previously copied nvs_set_blob() bytes directly into its durable vector and described nvs_commit() as a no-op. It modeled only the possible "bytes reached flash despite an error return" outcome. It could not represent a successful set followed by a commit failure before durable persistence.

ESP-IDF 5.5.6 documents that nvs_set_blob() changes are not guaranteed durable until nvs_commit() succeeds: https://docs.espressif.com/projects/esp-idf/en/v5.5.6/esp32/api-reference/storage/nvs_flash.html

### Test-first RED / GREEN

- RED commit a30df047a61c455a2d546a2a2531c6935f350594 added the missing commit-before-persistence failure scenario. Quarantine run #44482734420, job 135418637684, failed as intended at COMMIT_FAILURE_BEFORE_PERSISTENCE_WAS_MISTAKEN_FOR_DURABILITY board=ESP32 (exit 42). This proved the prior fake model incorrectly treated the failed commit as durable.
- GREEN commit da7202768383739a0a43419a2a303b5b64685b9f separates NVS pending data from durable data. nvs_set_blob() stages bytes; successful nvs_commit() moves them to the durable image; fail-before-persistence leaves only pending bytes, which are discarded on reboot; fail-after-persistence still models the ambiguous case where bytes reached flash but the API reports failure.
- Focused quarantine #44483015984, job 135419578031: SUCCESS. Exact logs show COMMIT_FAILURE_BEFORE_PERSISTENCE_REBOOT_LIMITATION=REPRODUCED and POLL_FAULT_DUAL_STORE_LAB=PASS for both ESP32 and ESP8266.
- Relay/output #44483016050: source-output job 135419578620 SUCCESS; ESP32 boot-polarity job 135419578876 SUCCESS.
- Full build #44483016111: validation job 135419703002 FAILED at the QA-owned Missing poll signature check in tests/controllers.sh. Firmware/platform targets and Android were still running at the last read; no Full workflow pass is claimed.

### Safety interpretation

The new lab explicitly reproduces the no-durable-marker outcome when LittleFS marker writing and NVS/EEPROM commit both fail. The current boot remains inhibited, but a reboot cannot recover a marker that neither persistence path durably stored. This is a known durability limitation, not a passing production guarantee. NVS and LittleFS/EEPROM remain regions on the same physical flash device, not an independent anti-rollback witness.

No firmware runtime, GPIO/relay behavior, shared API, CORE ledger, financial migration, QA-owned test, RELEASE workflow, COE destination, physical device or customer data changed. The lab is simulated host/fake-I/O evidence only.

**Next:** PHX-QA independently reviews both commit-failure outcomes; PHX-MASTER records the no-durable-marker limitation against #43; PHX-CORE/MASTER must retain the independent protected witness gate. No positive poll admission or persistence fallback is authorized by this test.



## UTC08 follow-up — field-specific ESP32 NVS configuration readback diagnostics

**Task:** hardware-owned, behavior-preserving cleanup on the existing #327 child branch. **PRODUCTION NO-GO.**

**Exact source commits:**
- Readback diagnostic refactor: `074ed6dc4726c047b9a8d81487b40ac5ca56cea0`
- Corrected diagnostic line terminator: `c59ebc91ed552f6e026fea0d465ca1227685a4a7`
- Current ESP32 sketch blob: `754a5738d30500fe12a573b89956fedeb0e279c3`
- ESP8266 sketch remains unchanged at blob `1b32cb90be11da79ba7ea1155f128aee9e495dd2`.

The ESP32 `configFieldsMatchStored` guard now accepts an optional first-failure output and reports the first mismatched/missing NVS key in the existing check order (SSID, password, server, API-key field, device ID, coin/LED/relay pins, polarity, debounce, pulse-group). The original no-argument wrapper remains. `saveConfig()` emits only the key name, never the stored value; on failure it still revokes `outputPolarityKnown` and `pinConfigSafe`, returns false, and does not reboot or publish a valid polarity marker. No NVS key/schema, config ordering, GPIO, poll, coin admission, finance, or wire contract changed.

### Exact-source Actions — source/test SHA `c59ebc91ed552f6e026fea0d465ca1227685a4a7`

- Quarantine/readback [#44486049670](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44486049670), job `135429665429`: **SUCCESS**. Both boards report `POLL_BLOCKED_EDGE_FAULT_PASS 7/7`, `POLL_EDGE_SNAPSHOT_RACE_PASS`, and the existing poll-loop mutation controls reject removal of the intake inhibit, quiet window, ISR edge reconciliation, fault marker and boot latch. ESP8266 config-read lab passes valid-v3 image preservation, malformed v1/v2 and unknown-schema setup-save denial, local v1/v2→v3 config migration marker preservation, and commit-failure retry denial. Poll-response lab passes 11/11 fail-closed cases, 13/13 strict-root JSON cases and 4/4 coin-POST status plus 4/4 disposition default-deny cases per board.
- Relay/output [#44486049762](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44486049762): **SUCCESS**; source-output job `135429667009` and ESP32 boot-polarity job `135429667650` both pass. ESP32 boot-polarity lab reports unknown/legacy profile INPUT, local polarity marker readback PASS, active-high/active-low OFF preload PASS and remote polarity authority DENIED.
- Full build [#44486049590](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44486049590): **COMPLETED FAILURE**. Validation job `135429794092` fails at the inherited QA-owned `Missing poll signature check` in `tests/controllers.sh`. All 13/13 firmware/platform target jobs and Android job `135429793469` completed SUCCESS. ESP32 job `135429794027` compiled with `esp32:esp32@4.0.0` (1,096,293 bytes program / 52,568 bytes globals; artifact `14510079216`, ZIP SHA-256 `860e4345bbcfef017b8e49e0955eb0037a194678357f205355a45f063f90024e`). ESP8266 job `135429794164` compiled with core 3.1.2 and uploaded artifact `14511225448` (ZIP SHA-256 `994f89fcc471b798493e8fa7449d4fe01c2c29dcc0c4f18326b8087fb5e99e5c`). Downstream simulation, update bundle, candidate, signing and publishing jobs were skipped.

### Coverage boundary and requests

The existing failure-injection labs above do **not** exercise every ESP32 `Preferences.put*` key failure against the new first-failure diagnostic. That per-key NVS write/readback failure matrix belongs to PHX-QA; it remains **NOT TESTED** here. This cleanup is compile- and focused-CI-verified, not independently QA-accepted. The current Full failure is not fixed by relaxing firmware: main register/poll has no approved positive response-signature contract, so keep default-deny.

- PHX-QA: add exact-source failure injection for each NVS config key; assert the reported key is correct, `polarityv` is never promoted after a mismatch, outputs remain inhibited, and no reboot/success response occurs. Replace the obsolete positive poll-signature presence assertion with source-exact negative/default-deny checks.
- PHX-RELEASE: rerun the pinned ESP32 3.3.13 compatibility leg against the new exact ESP32 sketch blob `754a5738...`; the 4.0.0 compile is covered by Full run #44486049590, but the prior dedicated 3.3.13 matrix used the pre-cleanup sketch blob.
- PHX-MASTER: review the updated #327 child stack and retain the separate same-chip dual-store durability limitation against witness issue #43.

No physical relay/acceptor, power-cut, electrical pulse/recovery, 150-cut trial, 30-device/24-hour soak, financial migration, signer or independent witness was exercised. `SIMULATED_ONLY=1`; `PHYSICAL_POWER_CUT_VERIFIED=0`; `PRODUCTION_MIGRATION_AUTHORIZED=0`.


## UTC08 follow-up — explicit-status ESP32 NVS string readback (2026-11-19)

**Task:** close a source-proven fail-open edge in the new ESP32 configFieldsMatchStored() diagnostic. **PRODUCTION NO-GO.**

### Defect and test-first reproduction

The previous readback implementation supplied the literal fallback "__PHX_NVS_READBACK_MISSING__" to Preferences.getString(). The Arduino Preferences String-returning overload returns that fallback when nvs_get_str() fails. Because configuration strings are user-controlled, any field may legally equal the fallback. If that field's readback failed while prefs.isKey() still reported the key present, the fallback could compare equal to the intended value and allow the readback guard to continue.

The exact-source failure-injection lab deliberately seeded all five string fields (ssid, pass, server, key, id) with the old fallback and injected read failures one key at a time.

- Test-first lab commit b15561ff4dfe8cd03a9215acd9027e57db0428de.
- Workflow wiring commit 3a076a4ad5e3b98227354757d19af1d322e9319f.
- Expected RED [#44491276794](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44491276794), job 135447222683: **FAIL as expected**, log SENTINEL_COLLISION_FAIL_OPEN key=ssid, exit 42. Existing preceding hardware labs passed before the new regression stopped the job.

### Firmware correction

- Source commit 48b31e9762aa68426ba1193b85b80a1f3731562e.
- ESP32 sketch blob 79bdae3da167289540b7197d32d6e854f1c444c4.
- Added nvsStringMatchesStored() and removed the fallback sentinel.
- The helper checks isKey, exact NUL-inclusive getStringLength, the buffer-overload getString(key, buffer, maxLen) return count, byte-for-byte contents, and allocation success. Any missing key, length/read error, mismatch or allocation failure returns false. The existing caller still reports only the failed key name, never the stored value, and retains output inhibition/no-reboot behavior.

**Upstream API verification:** both Arduino-ESP32 3.3.13 and 4.0.0 expose getStringLength() and the buffer-returning getString() overload. In both source versions, the length/read methods return zero on error and the stored string byte count including NUL on success:
- [Preferences.h 3.3.13](https://github.com/espressif/arduino-esp32/blob/3.3.13/libraries/Preferences/src/Preferences.h)
- [Preferences.cpp 3.3.13](https://github.com/espressif/arduino-esp32/blob/3.3.13/libraries/Preferences/src/Preferences.cpp)
- [Preferences.h 4.0.0](https://github.com/espressif/arduino-esp32/blob/4.0.0/libraries/Preferences/src/Preferences.h)
- [Preferences.cpp 4.0.0](https://github.com/espressif/arduino-esp32/blob/4.0.0/libraries/Preferences/src/Preferences.cpp)

No NVS key/schema, config serialization, GPIO, relay, coin, poll, register/poll wire contract or financial behavior changed.

### Exact-source Actions

- Quarantine/readback push [#44491449904](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44491449904), job 135447807843: **SUCCESS**. New lab log: NVS_STRING_READBACK_EXPLICIT_STATUS_PASS 5/5 read failures, 5/5 length failures, empty and mismatch controls. Existing source-extracted journal, poll, pulse, EEPROM and Mbed TLS labs also passed; logs explicitly retain SIMULATED_ONLY=1 and physical acceptance flags 0.
- Quarantine/readback PR [#44491461601](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44491461601), job 135447848735: **SUCCESS**.
- Relay/output PR [#44491461501](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44491461501), jobs 135447847957 and 135447848320: **SUCCESS**.
- Full push [#44491449848](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44491449848): **COMPLETED FAILURE** at validation job 135447953870, Missing poll signature check; ESP32, ESP8266, all 13 firmware/platform target jobs and Android completed successfully. Downstream simulation, update, signing and publication jobs were skipped.
- Full PR [#44491461660](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44491461660): validation job 135448008623 has the same failure. At the last observation, ESP32 target job 135448008646 was still in progress; this PR Full run is not counted as completed.

### Ownership and remaining checks

- PHX-QA: independently review the new sentinel-collision lab and still-outstanding per-key Preferences write/readback failure matrix; replace the obsolete positive poll-signature presence assertion with source-exact negative/default-deny tests. No QA-owned files were edited.
- PHX-RELEASE: run the pinned ESP32 core 3.3.13/4.0.0 matrix against the new exact sketch blob 79bdae3d...; do not reuse the earlier pre-fix source pin.
- PHX-MASTER: review the new hardware-owned fail-closed correction in the existing #327 child stack.
- Current PR #327 remains OPEN / DRAFT / UNMERGED; base is PR #326 head 58c558fb6a237935214621adc3dee65a10fe1a51.

No physical NVS, relay, acceptor, coin, power cut, migration, signer, customer money, release or deployment was exercised. This is source-extracted failure-injection and CI evidence only; hardware acceptance remains NOT TESTED.


## UTC09 — reuse the shared C/C++ source extractor in the ESP32 NVS lab (2026-11-19)

**Scope:** hardware-owned test-harness cleanup only; no firmware runtime or test-owner boundary change.  
**Candidate:** [PR #327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327), OPEN / DRAFT / UNMERGED.  
**Base:** PR #326 head `58c558fb6a237935214621adc3dee65a10fe1a51`.  
**Source/test head:** `b2a9e0c525caefd8ab18e9ef4c46266960d033cf`.

### Cleanup

`nvs_string_readback_lab.py` previously carried a local brace-counting extractor that did not mask C/C++ comments or literals. The same branch already contains the board-agnostic `firmware_lab_source.extract_function()`, which masks comments, escaped literals, raw strings and line splices while preserving original offsets/newlines.

The NVS lab now imports that shared helper, extracts `nvsStringMatchesStored` and `configFieldsMatchStored` by actual function definition, and no longer maintains a second parser. A small self-test places brace decoys in a string, line comment, block comment and character literal, with a following function as a boundary sentinel.

### Test and correction history

- Initial refactor commit `27e12e775a24251d94fb9ddbd1f48fdd4f2bd976` exposed an implementation error in the new probe: it encoded literal backslash-n sequences instead of newline escapes. Quarantine run [#44494664424](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44494664424), job `135458696960`, failed at `verify_shared_extractor()` with `unbalanced C/C++ block`. This was a harness-probe defect, not an expected source RED; no firmware source was changed by that commit.
- Corrected test commit: `b2a9e0c525caefd8ab18e9ef4c46266960d033cf`.
- Exact-head quarantine [#44494823962](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44494823962), job `135459210785`: **SUCCESS**. Logs include `SHARED_EXTRACTOR_COMMENT_LITERAL_BRACE_PASS` and `NVS_STRING_READBACK_EXPLICIT_STATUS_PASS` (5/5 read failures, 5/5 length failures, empty and mismatch controls). Existing EEPROM, poll-edge, pending-write, pulse-capture, digest-failure and Mbed TLS selector labs also passed.
- Exact-head relay/output [#44494824222](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44494824222): ESP32 boot-polarity job `135459212530` and source-output-polarity job `135459212984` **SUCCESS**.
- Full build [#44494824116](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44494824116) was PENDING at this handover update; no Full result is claimed.

### Boundaries

The NVS, poll, EEPROM and coin-ingress labs are source-extracted host/fake-I/O simulations. Logs retain `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`. No .ino runtime, NVS schema, wire contract, GPIO, relay, coin, finance, QA-owned test, Release workflow, COE destination, physical device, migration, signer, merge or release was changed.

**Next exact action:** read the terminal Full result for the new docs-head commit, then request PHX-QA independent review of the NVS per-key write/readback matrix and retain the existing poll-signature default-deny blocker.


## UTC09 terminal validation and cross-role source-pin recheck (2026-11-19)

### Full workflow terminal result for docs head `00640ac6ce38f64e4c675ed70a0984de8b0408e7`

[Full PR run #44495219491](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44495219491) completed **FAILURE**:

- Validation job `135461824134`: failed at the QA-owned `Missing poll signature check` in `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`.
- ESP32 job `135461824624`: **SUCCESS**, installed `esp32:esp32@4.0.0` and compiled the current candidate.
- ESP8266 job `135461824659`: **SUCCESS**, installed `esp8266:esp8266@3.1.2` and compiled the current candidate.
- All 13 firmware/platform target jobs and Android job `135461824562`: **SUCCESS**.
- Update bundle, simulations, signer handoff, candidate gate and publishing jobs: **SKIPPED** after validation failure.

This is a compile result, not Full workflow success, physical acceptance, signed release or production authorization.

### PHX-RELEASE #291 compatibility matrix — exact-source pin is stale

Read live [PR #291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/291), current head `3aacebcaa9d19f17b7b0d788cabb567d4ea5f196`, and its release-owned compatibility workflow. The matrix run [#44495882960](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44495882960) succeeded for both ESP32 cores:

- Core 3.3.13 job `135463310542`: **SUCCESS**.
- Core 4.0.0 job `135463310774`: **SUCCESS**.

However, the workflow pins **older** PHX-HARDWARE source `0e5514adb0088649eca8bec9df6215faa50b556c`, sketch blob `c29483f0761ca6e2db0573bd12d6bfa502f12434`. The current #327 source/test commit is `48b31e9762aa68426ba1193b85b80a1f3731562e`, ESP32 sketch blob `79bdae3da167289540b7197d32d6e854f1c444c4`. Therefore #291 proves the old source on 3.3.13/4.0.0, **not the current NVS/Mbed-TLS-corrected sketch**. Existing hardware audit comment [#7001879641](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/291#issuecomment-7001879641) is being updated with this exact-source gap. PHX-RELEASE must refresh the source SHA/blob and rerun both cores; PHX-HARDWARE did not edit release-owned files.

### COE #26 integration audit — empty-key signature bypass

Read COE candidate head `b382d233ff06c8791b1028bed3c617cc7b670d12` and exact hardware/server blobs. Both candidate hardware sketches default the stored key to empty and gate signature verification only under a nonempty-key condition while initializing `sigOk=true`. If the key is empty, the check is skipped and an `ok:true` register/poll response can pass the local gate; the poll path can set `insertMode` and `activeTarget`. The candidate server emits `response_sig`, but that does not protect a client that skips verification. Exact source evidence and deny-only request were added to existing COE PR #26 comment [#6999032274](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26#issuecomment-6999032274). No COE destination code was changed.

COE #26 ESP32/ESP8266 candidate blobs are `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` / `c8be98f72596681e36a3ad1f8939bf8046c96887`; paired candidate server blob is `0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e`. They are not byte-identical to Experiments #327. The five COE candidate workflows remain QUEUED with zero jobs. COE-INTEGRATION/CORE/QA own reconciliation and contract approval.

### Remaining hardware boundary

PR #327 remains OPEN / DRAFT / UNMERGED. Focused quarantine and relay/output tests pass at the source/test head and docs head. Full validation remains failed at the QA-owned poll assertion. NVS/coin/relay labs are simulated/fake-I/O; physical NVS, pulse, power-cut and electrical acceptance remain NOT TESTED. No finance, migration, signer, COE source, QA-owned test, Release workflow, merge or deployment was performed.


## UTC09 continuation — bounded coin-pulse overflow and target-drift fail-closed correction (2026-11-19)

**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Parent:** PR #326, base `58c558fb6a237935214621adc3dee65a10fe1a51`  
**PR:** [#327 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Source/test head before this handover:** `7ed129275d45c6523a8ec25aa2ae2176d396450b`

### Proven defect

Both ESP sketches previously accepted a pulse only when `pendingTarget==activeTarget && pendingPulses<20`. If the pending record already held 20 pulses, or if its target no longer matched the active target, the next physical rising edge was silently ignored. The pending-record readers/writers reject counts above 20, so the 21st edge could not be represented and must not be treated as an ordinary no-op.

### Firmware correction

Updated only the PHX-HARDWARE-owned board sketches:

- ESP32 source commit [`c260aea`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/c260aea666c49c975a493fa1d16d021e029737e7), blob `1e720d3b2fc76e348ff77e347e0d472d38559d04`.
- ESP8266 source commit [`860c496`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/860c496683331700248cd29be3dc0ab63ebdab9b), blob `75f62c359bbb69f4f580b7ee0c3875396b12cc7f`.

When an active edge cannot be appended because the batch is already at 20 or its target identity differs, `sampleCoinPulseEdge()` now calls the existing `latchPollPulseFault(pendingPulses+1)`, marks the pending event unresolved, and reapplies outputs OFF. It does not increment or rewrite the bounded pending record, mint a new nonce, post the partial batch, or clear the pending journal. The existing pending nonce/target are retained for operator reconciliation. The valid 20th pulse remains accepted; the unrepresentable 21st pulse fails closed.

No wire/API contract, EEPROM/NVS schema, financial accounting path, server CGI, shared CORE file, or release workflow was changed.

### Test-first and exact-source evidence

- Test-first RED commit [`28fa0f9`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/28fa0f94f34ae2f86b9f7268234f979959761c0f): old source failed at `pulse-overflow-21` on both boards, proving the previous silent-drop behavior.
- Final source/test head before this handover: `7ed129275d45c6523a8ec25aa2ae2176d396450b`.
- Focused quarantine push [#44500314957](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44500314957), job `135478049410`: **PASS**.
- Focused quarantine PR [#44500323767](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44500323767), job `135478074872`: **PASS**.
- Focused relay/output PR [#44500323856](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44500323856), jobs `135478074653` and `135478075066`: **PASS**.
- Coin pulse source-extracted lab: **10/10 per board**. Mutation injection rejected removal of the overflow guard, target-drift guard, overflow fault latch, edge latch, debounce strictness, persistence latch, and output inhibit.
- Poll-loop blocking/inhibit lab: PASS. ESP8266 config-read lab: PASS, including full-image read failure, malformed v1/v2 and unknown-schema setup-save denial, and local v1/v2-to-v3 marker preservation. These are source-extracted simulations, not physical acceptance.
- Full push [#44500314998](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44500314998), exact head `7ed129275d45c6523a8ec25aa2ae2176d396450b`: overall **FAIL** because validation job `135478194042` reports the inherited QA-owned `Missing poll signature check` in `tests/controllers.sh`. ESP32 core 4.0.0 job `135478194349` PASS; ESP8266 core 3.1.2 job `135478194799` PASS; all 13 firmware/platform targets and Android job `135478194471` PASS. Production import, simulations, signing, bundle and publishing jobs were skipped.
- The focused lab logs explicitly report `SIMULATED_ONLY=1`, `PHYSICAL_COIN_PULSE_ACCEPTANCE=0`, `PHYSICAL_RELAY_ACCEPTANCE=0`, and `PHYSICAL_POWER_CUT_ACCEPTANCE=0`.

### Live integration and ownership recheck

- Experiments main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; canonical organization `BlazeDevStudio`.
- Parent #326 head/base: `58c558fb6a237935214621adc3dee65a10fe1a51`.
- Parallel drafts remain open/unmerged: #239 `d83b715b...`, #254 `4054fbcc...`, #283 `830c3553...`; no parallel PR was edited.
- Master #288 remains draft at `1decd7715c4bac46673f673c49f27bfeca160a4e`.
- Release #291 API head is now `9b26671efe6138bb4dfe14c10db520902dff6cb8`; the latest UTC09 Release checkpoint still names `c99f508`, so that checkpoint is stale and needs Release/Master reconciliation. The earlier 3.3.13/4.0.0 compatibility run is on an older source head; exact-current-source ESP32 core 3.3.13 remains NOT TESTED.
- COE main remains `a6513ab4412b4c014eee2863e45cbe32d06cb243`; COE PR #26 remains draft at `b382d233ff06c8791b1028bed3c617cc7b670d12`. No firmware was copied or migrated into COE.
- Issues #172, #266, #177, #34, #31, #32 and #43 remain open. The cleanup-first, safety, finance and witness gates are not complete.
- The requested private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not found by exact-name authorized Library search, and no Google Drive connector was exposed. No older registry snapshot was substituted.

### Remaining blockers / next actions

1. **PHX-QA:** independently review the 20/21 boundary, target-drift behavior, pending identity preservation, and negative/default-deny poll fixture. Replace the stale positive poll-signature presence assertion only under QA ownership.
2. **PHX-CORE:** confirm the unresolved-edge count semantics and that the existing pending record plus fault marker is sufficient for the operator reconciliation contract; no shared API change is proposed.
3. **PHX-RELEASE:** provide a pinned exact-source ESP32 core 3.3.13 build in addition to the verified 4.0.0 build; refresh #291 handover after its current head `9b26671`.
4. **PHX-MASTER:** review #327 as a child of #326 and reconcile the latest role/PR heads. Keep both PRs draft and unmerged.

The poll-fault backup remains same-chip dual-store evidence, not an independent freshness witness. If both stores fail, reboot durability is not established even though the current boot denies outputs. No physical 150-power-cut test, 30-device 24-hour soak, electrical pulse/recovery acceptance, protected anti-rollback signer, durable financial migration, or independent QA/release signoff is evidenced.

**Disposition: CI VERIFIED for the focused source-extracted correction; Full validation remains FAIL; HARDWARE ACCEPTED not established; PRODUCTION NO-GO.**  
```json
{
  "protocol": "BLAZE-COMMS/1",
  "message_id": "PHX-HARDWARE-20261119T09-PULSE-BATCH-OVERFLOW-DENY",
  "from": "PHX-HARDWARE",
  "to": ["PHX-MASTER", "PHX-CORE", "PHX-QA", "PHX-RELEASE"],
  "type": "REQUEST_REVIEW",
  "priority": "P0",
  "task_id": "#172/#177/#266/#327",
  "branch": "phoenix/hardware-prepoll-edge-abort-20261119",
  "base_sha": "58c558fb6a237935214621adc3dee65a10fe1a51",
  "status": "IN_PROGRESS",
  "evidence": [
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44500314957",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44500323767",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44500323856",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44500314998"
  ],
  "blockers": [
    "QA-owned positive poll-signature fixture fails Full validation.",
    "Exact-current-source ESP32 core 3.3.13 build not tested.",
    "Independent witness, financial migration/replay and physical acceptance absent.",
    "Private registry v11 unavailable through exposed connector surface."
  ],
  "next_action": "QA independently verifies the bounded pulse deny path and poll fixture; CORE confirms event reconciliation semantics; RELEASE pins core 3.3.13; MASTER reviews the #326/#327 stack. Do not merge or enable coin admission.",
  "updated_utc": "2026-11-19T09:56:30Z"
}
```
