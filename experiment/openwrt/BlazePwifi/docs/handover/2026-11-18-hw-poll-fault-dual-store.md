# PHX-HARDWARE handover — poll-fault secondary-store fallback

**Disposition:** candidate implementation committed on a child of PR #322; exact-source host labs CI VERIFIED; ESP8266 and ESP32 target builds CI VERIFIED; all 14/14 target/platform matrix jobs CI VERIFIED; SIMULATED only; physical acceptance NOT TESTED; PRODUCTION NO-GO.

## Lineage and ownership

- Parent PR #322: phoenix/hardware-output-preload-child-20261118 at 50d93e0de3d682550b6f02fb43484e76ad9c7e08
- Child branch: phoenix/hardware-poll-fault-dual-store-20261118
- Scope: ESP32 and ESP8266 sketches, hardware-owned source-extracted lab, narrowly scoped hardware workflow and this handover
- No QA-owned tests, CORE server/ledger files, shared API, release/signing workflow, COE destination, migration or Master coordination files changed.

## Defect

PR #320 currently latches journalRecoveryRequired in RAM when a coin-line edge is detected during synchronous poll. It writes /pollpulse.fault to LittleFS and checks readback. If LittleFS cannot mount/open/write/read the marker, the current boot stays denied but the hold has no persistent fallback. A reboot with no pending record can therefore lose the only hold.

Master Architecture Contracts §6.2 explicitly says a RAM-only latch is not proof of cross-reboot non-replayability. Master UTC03 audit asks HARDWARE for a durable fallback and QA for reset/reboot vectors.

## Candidate implementation

- ESP32: write a versioned, fixed-size poll-fault record into NVS namespace phx_fault, key poll_fault, separate from the LittleFS partition. Verify putBytes length and exact readback.
- ESP8266: reserve bytes at offset 512 in the existing EEPROM-emulation sector, expand the EEPROM buffer to 544 bytes without moving the existing Config at offset 0, commit, close/reopen the emulation buffer, and verify flash-backed readback.
- A valid or malformed/non-erased secondary record is a permanent deny marker. No automatic clear or reset path is added.
- latchPollPulseFault() now attempts the secondary store and LittleFS. Either successful durable marker keeps boot denied; if both fail, current boot remains denied and logs explicitly that reboot durability is not established.
- If the secondary store cannot initialize/read, boot fails closed.
- The two stores are separate flash partitions/regions but remain on the same physical flash chip. This is not an independent physical witness and does not satisfy issue #43 or protected anti-rollback.

## Failure-injection lab

poll_fault_dual_store_lab.py extracts the production record and persistence functions from both sketches, compiles them with host storage API fixtures, and exercises:
- blank store;
- LittleFS marker failure with secondary-store success, followed by simulated reboot;
- corrupt/partial secondary marker;
- readback failure after write;
- secondary-store unavailable at boot;
- primary LittleFS success when secondary commit fails;
- both stores failing, explicitly reported as current-boot-only residual limitation.

The host fixture is SIMULATED. It does not measure flash wear, brown-out behavior, erase/program atomicity, or actual power-cut recovery.

## Review requests and blockers

- PHX-MASTER: approve/reject the NVS/EEPROM secondary-store layout and no-auto-clear invariant before integration.
- PHX-CORE: review the fault-hold semantics against event disposition, replay and future receipt handling; no financial authority is added.
- PHX-QA: independently add reboot-after-LittleFS-open/readback failure vectors to QA-owned tests and run them against this exact child head. This PR's local lab is not independent QA.
- PHX-RELEASE: review the new narrowly scoped hardware workflow path.

No flash, reset, relay actuation, real coin, live money, signer, migration, merge, release or deployment occurred.


## UTC04 exact-head evidence update

- Source/test SHA: 94c5ad327304bea8f42d5bc620ea9d804035f424
- PR #323 head at evidence read: 94c5ad327304bea8f42d5bc620ea9d804035f424
- Focused quarantine / journal / poll-fault workflow: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44240322241 SUCCESS on the exact source/test SHA. Logs show:
  - DUAL_STORE_FAILURE_LIMITATION=EXPECTED_CURRENT_BOOT_ONLY for ESP32 and ESP8266
  - POLL_FAULT_DUAL_STORE_LAB=PASS for both boards
  - existing source-extracted quarantine, pending-journal, mount, pending-clear, pending-write/readback, coin-post-gate, poll-window and pulse-capture labs passed
  - physical flash/power-cut flags explicitly remain zero
- Relay output polarity workflow: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44240322285 SUCCESS on the same exact source/test SHA.
- Full BlazePwifi build: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44240322231 completed FAILURE. Validation job 134586409067 FAILED at the existing QA-owned assertion Missing poll signature check. All 14/14 target/platform matrix jobs PASS, including ESP32 job 134586409380 and ESP8266 job 134586409487. Downstream signed-import, update-bundle, browser/ESP/x86/Ruijie/Orange Pi simulations, candidate gate and publish/sign handoff jobs were SKIPPED after validation failure. This is target-build CI evidence, not Full CI acceptance.
- Earlier exact-head lab/harness failures were retained in Actions history and corrected before the successful 94c5 run: the mount lab now isolates the new backup-reader seam and resets per-scenario state; the dual-store lab now extracts only persistent-format declarations and injects EEPROM readback failure after commit, matching the actual ESP8266 API.

## Live stack revalidation at UTC04

- PR #239 head d83b715b116185107737fef721c2eece8feebf39; scoped native journal gate #40815737375 and BlazePwifi build #40815737447 SUCCESS.
- PR #254 head 4054fbccd9b2a4ad0e5fe7cfca5a27aa629eed84; scoped build #44019837616 and controller-header lab #44019837617 SUCCESS.
- PR #283 head 830c355376380f9b5533d5cda2558beed41a593a; scoped quarantine append/readback #44219099309 and build #44219099256 SUCCESS.
- PR #322 remains at 50d93e0de3d682550b6f02fb43484e76ad9c7e08; #323 is a child of that exact head.
- Master PR #288 advanced to e95cda0ae3f08c4f1dbdfcdfa79808cc887cd7b3; Architecture Contracts §6.2 still requires a durable disposition/hold and independent QA of reboot/failure cases.
- Re-audit of #283 current source: both sketches now return before clearPending when quarantine append fails; this supersedes the earlier unconditional-clear finding. The no-retry latch after append failure remains a future-enable blocker, and the main producer still does not emit the response_sig expected by #283. Keep default-deny; no positive poll or config interoperability is claimed.

The secondary NVS/EEPROM records remain same-chip fallback regions, not an independent physical witness. Simultaneous failure of LittleFS and the secondary store is explicitly only current-boot fail-closed; reboot durability is not established in that case. QA/Master/CORE approval remains required before composition.


**Final UTC04 full-matrix update:** run 44240322231 is complete with all 14 target/platform jobs successful, including both ESP boards. The workflow remains FAILED solely at the inherited QA-owned Missing poll signature check; no signing, publishing, simulation or candidate gate ran. Do not count this as a full release pass.


## UTC05 exact-source correction — immediate output inhibit before flash writes

A second source audit found that `latchPollPulseFault()` set the RAM deny state but called `applyOutputs()` only **after** attempting NVS/EEPROM and LittleFS writes. Those flash operations may block while the relay remains at its previous physical state. The fix now deasserts relay/LED outputs immediately after setting `journalRecoveryRequired=true`, `insertMode=false`, and clearing `activeTarget`, before either persistence attempt.

### Test-first evidence

- Test-only RED commit: `c8e8e80a1eb4d6133043685e54795a7615cc9b3b`.
- Exact-source RED [run 44241798015](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44241798015), job `134591217970`: expected assertion failure `!persistenceBeforeOutputInhibit` against the unchanged latch ordering. The extracted ESP32 harness stopped at the first failing board, so this RED is not claimed as two-board execution.
- ESP32 source fix: `048f55df4dfd8a719afe9f7f12486ef0e9e8da16`.
- ESP8266 source fix / current source-test SHA: `6738171209a748c3c210ac13ebe69450eb6405f5`.
- Exact-head quarantine/journal/poll-fault [run 44241883128](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44241883128), job `134591494280`: SUCCESS. Both boards report `POLL_FAULT_DUAL_STORE_LAB=PASS`; both-store failure is explicitly reported as `EXPECTED_CURRENT_BOOT_ONLY`. Existing quarantine 36/36 per board, pending-attempt 28/28 per board, mount 8/8 per board, pending-journal 16/16 per board, pending-clear 17/17 per board, write/readback 22/22 per board, coin POST gate 10/10 per board, poll-window 11/11 per board and pulse-capture 8/8 per board passed.
- Exact-head relay/pulse/output lab [run 44241883164](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44241883164), job `134591494480`: SUCCESS. The `missing-immediate-output-inhibit` mutation is rejected on both ESP8266 and ESP32; pulse capture 8/8 per board and poll-window guards pass.
- Full build [run 44241883197](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44241883197): validation already FAILED at the QA-owned legacy `Missing poll signature check`; target matrix jobs were still running at this checkpoint. This is not Full CI acceptance.

All green results above are source-extracted host simulations / CI builds, not physical relay measurements. `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, `PHYSICAL_RELAY_ACCEPTANCE=0`, and `PHYSICAL_COIN_PULSE_ACCEPTANCE=0` remain explicit. The same-chip NVS/EEPROM fallback remains neither an independent witness nor an anti-rollback primitive. No flash, reset, coin, payment, migration, signing, merge, release or deployment occurred.


## UTC05 final Full-build readback at exact source/test SHA

The exact-source Full build [44241883197](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44241883197) completed **CANCELLED** after validation job `134591565845` failed at the QA-owned legacy `Missing poll signature check`. At this SHA, ESP8266 job `134591565856` completed SUCCESS; ESP32 job `134591565871` and the remaining target matrix were cancelled; downstream simulations, update bundle, candidate gate and signing/publishing jobs did not run. Do not carry forward the predecessor #323 14/14 matrix result as exact-head evidence.

Therefore, at source/test SHA `6738171209a748c3c210ac13ebe69450eb6405f5`:
- Focused source-extracted quarantine/dual-store suite: CI VERIFIED, both boards.
- Focused source-extracted relay/output/pulse suite: CI VERIFIED, both boards.
- ESP8266 target build: CI VERIFIED.
- ESP32 target build: NOT TESTED at this exact SHA (cancelled before execution).
- Full target matrix / Full workflow: NOT VERIFIED; cancelled after QA validation failure.
- Physical GPIO, relay, flash and power-cut acceptance: NOT TESTED.


## UTC05 — blocking-poll regression restored to focused CI; storage and physical acceptance plan

**Current source/test SHA:** `30fb7cd2de0af13c70aa8716da8d7cd9e43ce548`  
**PR #323:** OPEN / DRAFT / UNMERGED; parent #322 remains `50d93e0de3d682550b6f02fb43484e76ad9c7e08`.

### Test coverage defect and correction

The existing `poll_loop_blocking_inhibit_lab.py` exercised the actual synchronous poll loop and LittleFS marker path, but it was not invoked by the focused CI entrypoint and had become incompatible with the new secondary-store helper calls. Its old mutation anchors for marker-write removal and boot-latch removal no longer matched current firmware, so those mutations could silently become no-ops.

The hardware-owned `coin_pulse_capture_lab.py` entrypoint now invokes the companion poll-loop lab. No Release-owned workflow file was changed. The poll-loop lab explicitly stubs only the secondary NVS/EEPROM seam; `poll_fault_dual_store_lab.py` separately extracts and tests the real secondary-store helpers. The poll-loop lab now rejects missing mutation anchors rather than silently accepting stale mutations.

Test-first history:
- Runner-only RED commit `9559c37131163dfb17f7c2d18cbd52c6a7f417b5`: [run 44246521728](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44246521728), job `134606678746`, failed as expected because the stale lab lacked `pollFaultBackupPresentOrCorrupt` and `writePollFaultBackup` seams.
- First fixture repair `301e81db6425637764b8d35dfc65efedafc25194`: [run 44246626671](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44246626671), job `134607022281`, progressed through the board scenarios but exposed a `-Werror` unused-variable compile failure in the boot-latch mutation.
- Final test correction `30fb7cd2de0af13c70aa8716da8d7cd9e43ce548` changes that mutation to `backupHold && littleFsHold`, which keeps both source variables used and causes the expected runtime denial failure. It also documents the separate dual-store test boundary.

Exact-head GREEN:
- [Quarantine Byte Readback LAB 44246760443](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44246760443), job `134607466918`: SUCCESS. Both ESP32 and ESP8266 report `POLL_FAULT_DUAL_STORE_LAB=PASS` and `DUAL_STORE_FAILURE_LIMITATION=EXPECTED_CURRENT_BOOT_ONLY`. The invoked poll-loop lab reports 7/7 fault-marker scenarios and 7/7 existing guards per board, poll-edge snapshot-race PASS, and 10 failure mutations rejected per board, including marker-write and boot-latch removal. Coin-pulse capture remains 8/8 per board.
- [Relay Output Polarity LAB 44246760676](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44246760676), job `134607466771`: SUCCESS. The same blocking-poll, marker, race and mutation checks pass on both boards alongside output-polarity checks.
- Both runs explicitly retain `SIMULATED_ONLY=1`, `PHYSICAL_COIN_ACCEPTOR_VERIFIED=0`, `PHYSICAL_RELAY_POLARITY_VERIFIED=0`, and `PHYSICAL_POWER_CUT_VERIFIED=0`.

The runner integration closes a CI invocation gap; it does not establish flash physics, physical relay behavior, or cross-reboot durability when both persistent stores fail.

### Board storage layout and assumptions

**ESP32**
- Sticky fallback record: Preferences/NVS namespace `phx_fault`, key `poll_fault`, fixed 20-byte versioned record.
- The NVS partition is separate from the LittleFS partition but remains on the same physical flash chip and shares the board's flash failure/power domain.
- Write length and exact record readback are checked. Existing, malformed, or unreadable record state is treated as a deny hold; there is no automatic clear path.
- The record checksum is corruption detection only, not authentication, signing, anti-rollback, or independent witness evidence.

**ESP8266**
- EEPROM-emulation buffer is 544 bytes; the 20-byte sticky fallback record is reserved at offset 512.
- Compile-time assertions keep the existing `Config` structure at or below offset 512 and the record within the reserved buffer.
- The code commits, ends/reopens the EEPROM-emulation buffer, then checks the record readback.
- Any non-erased bytes in the reserved record are treated as a deny hold; partial/malformed bytes are never auto-cleared.
- EEPROM emulation and LittleFS remain regions on the same physical flash chip. They are not independent power-loss domains.

**Shared invariant**
- Set the RAM recovery deny, disable insertion, clear the active target, and apply outputs before any potentially blocking persistence call.
- If either durable marker succeeds, boot remains denied.
- If both writes fail, only the current boot is known fail-closed; reboot durability is explicitly NOT ESTABLISHED. Do not claim otherwise and do not auto-replay or re-enable coin admission.

Before physical work, record the exact board revision, flash part, partition table, NVS/LittleFS partition boundaries, EEPROM-emulation sector and firmware SHA for each test unit. Confirm non-overlap from read-only partition metadata; do not infer layout from board model alone.

### Physical acceptance plan — NOT EXECUTED

This is a proposed owner-authorized noncustomer lab plan, not a test result. It requires disposable boards, isolated storage, an external pulse generator/coin simulator (no real money), dummy relay loads, and independent measurement/power telemetry.

1. **Preflight and provenance:** identify board revision and flash part; capture partition map, firmware/source SHA, pin map, relay polarity, coin input polarity, storage offsets, and blank/nonblank marker state. Preserve read-only before/after media hashes and timestamps off-device.
2. **Electrical pulse/recovery:** use a calibrated isolated pulse generator and scope/logic analyzer to measure actual input levels, pulse widths, bounce, edge timing, relay/LED output transitions, and brownout recovery. Exercise active-high and active-low configurations only where the board and wiring are verified. Do not invent voltage or timing limits; derive acceptance bounds from the exact board/acceptor specifications and measured baseline.
3. **Persistence fault injection:** independently inject LittleFS open failure, short write, flush/close/readback failure, NVS/EEPROM initialization failure, commit failure, and readback corruption. Then inject simultaneous primary and secondary store failure. Verify immediate physical output deassertion before storage calls, sticky deny after any successful marker, and explicit operator recovery when both stores fail. Never treat a same-chip fallback as an independent witness.
4. **Power-cut matrix:** plan 150 abrupt power-loss trials for the two ESP board families: 2 board families × 5 checkpoint classes × 15 repetitions. Checkpoints: (a) immediately after ISR edge capture, (b) after RAM deny/output inhibit and before secondary write, (c) during NVS/EEPROM commit, (d) after secondary commit and before LittleFS marker completion, and (e) during LittleFS write/readback. Use an independent power controller and external timestamped logger; after every restoration inspect state before any retry. Any missing marker, unexpected output enable, false ACK, duplicate effect, lost prepaid state, or unexplained state divergence is a failure. This two-board allocation is not a substitute for any additional architectures required by issue #34.
5. **System soak:** separately run at least 30 real isolated test clients for 24 hours under mixed Wi-Fi/controller/rental load, collecting independent lost/duplicate ACK, event conservation, relay, pulse and recovery telemetry. This remains a system-level acceptance gate, not a firmware host-lab result.
6. **Independent review:** PHX-QA witnesses the fault matrix and verifies exact firmware SHA and raw evidence; PHX-CORE checks event identity, receipt/disposition, replay and balance conservation; PHX-MASTER reviews the independent witness/anti-rollback evidence; PHX-RELEASE confirms target builds and reproducible provenance. Any unresolved state fails closed.

**Stop conditions:** any relay/coin output remains active during a latched fault; any pulse is silently converted to credit or lost; a corrupt marker is cleared; a reboot restores accepting state after a persisted fault; an ACK or balance effect occurs without durable authenticated disposition; or external evidence is incomplete. Stop the trial, preserve media and logs, and require operator reconciliation.

No physical flash, reset, power cut, real coin, live money, customer device, production migration, signer provisioning, merge, release or deployment was performed in this activation.


## UTC06 — ESP32 NVS read/open errors remain fail-closed

**Audit finding and correction**

The previous ESP32 backup-presence check used Preferences::isKey("poll_fault"). In the Arduino-ESP32 Preferences implementation, isKey() delegates to getType(), whose PT_INVALID result does not distinguish a genuinely absent key from an unsuccessful NVS lookup. That could classify an NVS read error as a clean missing marker.

The current ESP32 sketch now uses the lower-level NVS API:
- Only ESP_ERR_NVS_NOT_FOUND is treated as an absent/clean key.
- ESP_OK, type mismatch, invalid-handle and every other NVS lookup error retain the deny latch.
- A secondary-store open failure also sets journalRecoveryRequired, clears the active target and disables insertion before LittleFS recovery.
- Existing NVS values are never overwritten; a non-NOT_FOUND lookup error during a new write returns failure and leaves the separate LittleFS fallback path available.

Current ESP32 source blob: bd74b11c1496b0943404ff387ee72bb45d4743e5. Previous Preferences-based blob: b0dfe6cf4dcea1c7fbad00d5b2c2cda08f26f8ba.

**Exact-source failure-injection coverage**

The hardware-owned dual-store lab now exercises an existing sticky marker under:
- NVS read error;
- NVS type mismatch;
- NVS namespace/open failure.

It also retains the prior LittleFS-only, secondary-store-only, readback, corrupt-marker and both-store-failure scenarios. The both-store-failure result remains explicitly EXPECTED_CURRENT_BOOT_ONLY; it is not counted as reboot durability.

- Test/source head: a3aa967087680887e925791f83a8fbc48a1e62b9
- Lab blob: 5b1b31885a2f756127f272adf4627a81db4769c3
- Focused quarantine/dual-store/poll-loop run [44256301463](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44256301463), job 134638692296: **SUCCESS**. Logs explicitly show ESP32_NVS_READ_ERROR_DENY_PASS, ESP32_NVS_TYPE_MISMATCH_DENY_PASS and ESP32_NVS_OPEN_FAILURE_DENY_PASS; ESP8266 and ESP32 dual-store labs both PASS. Existing quarantine 36/36 per board, mount 8/8 per board, pending-journal 16/16 per board, pending-clear 17/17 per board, poll-window 11/11, pulse-capture 8/8 and blocking-poll fault-marker 7/7 per board also pass.
- Relay/output/pulse run [44256302301](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44256302301), job 134638692980: **SUCCESS**; relay polarity 48/48 per board, output-enable sequence 4/4, poll-window 11/11, pulse capture 8/8 and blocking-poll 7/7 per board.
- Full BlazePwifi build [44256301436](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44256301436): validation job 134638691264 **FAILED** at the QA-owned Missing poll signature check in the ESP8266 sketch. Both board build jobs are SUCCESS (134638690917 ESP32; 134638691241 ESP8266), and all 14 firmware target jobs returned SUCCESS. Android job 134638691250 was still in progress at this checkpoint; downstream simulation/signing/publishing/candidate-gate jobs were skipped after validation failed. This is not a green Full build.

**Disposition**

Focused source-extracted labs and both ESP board builds are **CI VERIFIED**. Host NVS/EEPROM fixtures are SIMULATED, not flash-physics or power-cut evidence. Physical GPIO/relay polarity, real coin ingress, brown-out, 150 power cuts, 30-device/24-hour soak, protected independent witness, durable accounting/replay and v1→v2 migration remain **NOT TESTED / BLOCKED**. Same-chip NVS/EEPROM is not an independent witness. Keep PR #323 DRAFT / UNMERGED / PRODUCTION NO-GO.

**Next exact action:** PHX-QA must repair and independently rerun the legacy poll-signature parity assertion without restoring unauthenticated poll admission, then review the NVS read/open failure vectors at this exact source/test head. PHX-CORE reviews fault identity/disposition/replay; PHX-MASTER decides whether this same-chip fallback is acceptable as a candidate only. No flash, reset, merge, signing, migration, release or deployment.


## UTC07 — ambiguous secondary-store commit outcome regression

**Exact source/test commit:** `c13dfb8d9b7ae83c15aa97c94842c339db8b8584`  
**Base/parent:** PR #322 at `50d93e0de3d682550b6f02fb43484e76ad9c7e08`  
**PR #323 remains OPEN / DRAFT / UNMERGED / PRODUCTION NO-GO.**

The hardware-owned `poll_fault_dual_store_lab.py` now injects an ambiguous persistence API result on both board fixtures: the simulated NVS/EEPROM commit first copies the marker into the fixture's durable-media image, then reports failure. The LittleFS marker is also forced to fail. The test clears the injected API error, simulates a reboot, and requires `loadPollPulseFaultLatch()` to discover the persisted secondary marker and keep insertion denied.

- ESP32: `nvs_commit()` now has a dedicated fail-after-durable-write injection, distinct from fail-before-write.
- ESP8266: `FakeEEPROM.commit()` now has the matching fail-after-flash-copy injection, distinct from fail-before-write.
- Both board paths assert the current boot remains denied and the subsequent simulated reboot remains denied despite the failed commit return.
- This is a host fixture for ambiguous API completion, **not** a claim that the test emulates real flash programming, brown-out physics, or power-cut atomicity.
- No production `.ino`, shared API, CORE ledger, QA-owned tests, Release workflow, or COE destination file changed.

**Verification status at checkpoint:** the commit and PR head were read back successfully. No Actions run or combined commit status was returned for exact SHA `c13dfb8d9b7ae83c15aa97c94842c339db8b8584`; this new regression is **NOT RUN / NOT VERIFIED**. Prior source/test SHA `a3aa967087680887e925791f83a8fbc48a1e62b9` has focused run [44256301463](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44256301463) SUCCESS and relay run [44256302301](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44256302301) SUCCESS, but those runs do not verify this new scenario. Prior full run [44256301436](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44256301436) failed the QA-owned `Missing poll signature check`; target builds passed but downstream simulations/signing/publishing were skipped.

**Next exact action:** obtain a focused quarantine workflow run on exact SHA `c13dfb8d9b7ae83c15aa97c94842c339db8b8584`, inspect both board outputs for `AMBIGUOUS_COMMIT_REBOOT_DENY_PASS`, then request independent QA review. Keep same-chip NVS/EEPROM as candidate-only fallback; it is not an independent witness. Physical acceptance remains NOT TESTED.


## UTC07 exact-head Actions readback — ambiguous commit/reboot regression

**Exact source/test SHA:** `c13dfb8d9b7ae83c15aa97c94842c339db8b8584`  
**Final handover head before this update:** `b485058bf1bc1d08b136b3454b430bb8b8f4f6fe`  
**PR #323:** OPEN / DRAFT / UNMERGED; parent #322 remains `50d93e0de3d682550b6f02fb43484e76ad9c7e08`.

The delayed exact-head Actions results are now available:

- Focused quarantine / dual-store / poll-loop [run 44261049119](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44261049119), job `134654205777`: **SUCCESS**. Both board outputs contain `AMBIGUOUS_COMMIT_REBOOT_DENY_PASS` and `POLL_FAULT_DUAL_STORE_LAB=PASS`. The test models NVS/EEPROM bytes reaching the fixture's durable image while the commit API returns failure, forces LittleFS failure, clears the injected API error, then simulates reboot and verifies the sticky backup still denies intake. The same run also passed the invoked quarantine, pending journal/clear/readback, coin POST gate, poll-window, pulse-capture and blocking-poll suites. Logs explicitly retain `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`.
- Relay/output [run 44261049128](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44261049128), job `134654205785`: **SUCCESS**. Relay polarity 48/48 per board; output sequence 4/4; poll-window drain 11/11; pulse capture 8/8; blocking-poll fault marker 7/7 per board. Physical GPIO/relay behavior remains NOT TESTED.
- Full BlazePwifi build [run 44261049166](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44261049166): workflow **CANCELLED after validation failure**. Validation job `134654211662` failed at QA-owned `Missing poll signature check`. ESP8266 target job `134654211523` passed; ESP32 target job `134654211134` was cancelled. The target matrix was partial (only ESP8266 and two Orange Pi jobs completed successfully; other target jobs were cancelled); Android was cancelled. Downstream simulations, candidate gate, signing and publishing were skipped/cancelled. This is not Full CI or full target-matrix acceptance.

**Classification at exact source/test SHA c13dfb8d:** new ambiguous-commit reboot scenario CI VERIFIED in host fixtures for ESP32 and ESP8266; focused source-extracted suites CI VERIFIED; relay source lab CI VERIFIED; ESP8266 target build CI VERIFIED; ESP32 target build NOT TESTED at this SHA; full matrix NOT VERIFIED; physical acceptance NOT TESTED; production NO-go.

This test models an ambiguous API completion outcome. It does not prove flash erase/program atomicity, brown-out behavior, real power-cut recovery, or independent witness durability. The same-chip NVS/EEPROM fallback remains candidate-only. QA, CORE and Master review remain required; the stale positive poll-signature assertion must not be “fixed” by enabling unauthenticated admission.


## UTC07 Master decision reconciliation — poll and coin disposition remain hard-deny

Master's latest coordination commit [9fb0d615](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/9fb0d615c58731e488ea8f876e96d3e81425efb3) and audit [HARDWARE323_POLL_DENY_CONTRACT_AND_EXACT_HEAD_RECONCILIATION_20261118_UTC07.md](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/blob/9fb0d615c58731e488ea8f876e96d3e81425efb3/coordination/phoenix/HARDWARE323_POLL_DENY_CONTRACT_AND_EXACT_HEAD_RECONCILIATION_20261118_UTC07.md) were re-read after publication.

**Binding decision:** `acceptPollResponse()` and `coinPostDispositionVerified()` remain hard false on both boards. No unsigned poll or response may enable insertion, retain a target, clear pending evidence or authorize coin disposition. The current main CGI poll producer does not emit `response_sig`; the legacy QA fixture's positive `response_sig` / `|poll|` string-presence assertions are stale and must be replaced by negative behavior tests by PHX-QA. No synthetic signature string, positive admission or firmware relaxation is authorized.

This PR's UTC07 source/test change is limited to ambiguous NVS/EEPROM commit-result reboot coverage. It does not touch `acceptPollResponse()`, `coinPostDispositionVerified()`, the poll producer, QA-owned files, CORE schemas or Release workflows. The #323 child remains a draft-only candidate of #322; Master retains the review lineage #314 → #315 → #317 → #320 → #322, with #323 requiring explicit stack/QA review and no integration or migration authority.

No change to production status: focused host fixtures CI VERIFIED at source/test SHA `c13dfb8d...`; Full validation remains blocked by the stale QA fixture; physical flash, electrical pulse, 150 power cuts, 30-device/24-hour soak, independent witness and production readiness remain NOT TESTED / BLOCKED.


## UTC09 exact-source extraction hardening — source/test SHA 606ba4eeb90ffe7bb784a3c929ab5a9df45a0951

**Scope:** hardware-owned poll_fault_dual_store_lab.py only; no production .ino, QA-owned test path, shared API, CORE ledger, Release workflow, or COE destination changed.

### Cleanup and regression protection

The prior C/C++ source extractor counted every brace byte, including braces inside comments and string literals, and selected the first textual name( occurrence rather than requiring a function definition. That made the test harness unnecessarily fragile when firmware comments/literals or call order changed.

The lab now:
- scans nested C/C++ blocks while ignoring line/block comments, escaped string/character literals, and delimited raw strings;
- selects a function definition with a return-type/signature anchor, not a call, comment, or forward declaration;
- fails closed on missing or unterminated blocks;
- runs a small extractor self-test before either board harness, covering braces in comments, strings, characters, raw strings, nested initializers, a call before the definition, and an unterminated block.

### Exact-head CI evidence

- Initial implementation commit 86690c8acc3b87ea4386ad38a0c59c3460eb166a had a Python f-string syntax error in the signature pattern. The exact-head quarantine run [44273780927](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44273780927), job 134696640191, failed at that SyntaxError. This was an implementation error, not an expected regression RED.
- Corrected source/test commit: 606ba4eeb90ffe7bb784a3c929ab5a9df45a0951.
- Exact-head quarantine/readback [44273906126](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44273906126), job 134697064391: **SUCCESS**. POLL_FAULT_EXTRACTOR_SELFTEST=PASS; ESP32 and ESP8266 POLL_FAULT_DUAL_STORE_LAB=PASS; NVS read-error/type-mismatch/open-failure deny cases and ambiguous-commit/reboot deny cases pass. Existing quarantine 36/36 per board, pending marker 28/28 per board, mount 8/8 per board, pending journal 16/16, pending clear 17/17, pending write/readback 22/22, coin POST gate 10/10, poll-window 11/11, pulse capture 8/8 and blocking-poll fault 7/7 per board also pass.
- Exact-head relay/output [44273906309](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44273906309), job 134697065140: **SUCCESS**. Relay polarity 48/48 per board; output-enable sequence 4/4; poll drain 11/11 per board; pulse capture 8/8 per board; blocking-poll regression and mutation checks pass.
- Full build [44273906143](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44273906143): **FAILURE** at validation job 134697204281, existing QA-owned Missing poll signature check. All 14 firmware/platform jobs, including ESP8266, ESP32, Ruijie, Orange Pi and x86 targets, plus Android, completed **SUCCESS**. Production import/signing, update bundle, simulations, candidate gate and publishing were skipped after validation failure.

All new green evidence is source-extracted host simulation / CI only. PHYSICAL_COIN_ACCEPTOR_VERIFIED=0, PHYSICAL_RELAY_POLARITY_VERIFIED=0, and PHYSICAL_POWER_CUT_VERIFIED=0 remain. No physical flash, relay, coin, power cut, reset, live money, signer, migration, merge, release or deployment occurred.

### Coordination

- PHX-MASTER UTC08 decision remains binding: poll admission and coin POST disposition stay hard-deny; QA replaces the positive response_sig / |poll| assertion with negative deny-behavior tests; CORE owns the canonical response envelope and golden vectors.
- PHX-QA review is requested for the extractor cleanup and exact source/test SHA. This hardware-local lab is not independent QA evidence.
- PR #323 remains a draft candidate child of #322 at 50d93e0de3d682550b6f02fb43484e76ad9c7e08; no stack integration is authorized.
- The canonical private Google Drive registry v11 and newer corrections remain unavailable through the exposed Library/connector surface. No older registry was substituted.
- **Production remains NO-GO.**
