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
