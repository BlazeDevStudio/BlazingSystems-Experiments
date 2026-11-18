# PHX-HARDWARE handover — poll-fault secondary-store fallback

**Disposition:** candidate implementation committed on a child of PR #322; exact-source host lab and board builds pending; SIMULATED only; physical acceptance NOT TESTED; PRODUCTION NO-GO.

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
