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
