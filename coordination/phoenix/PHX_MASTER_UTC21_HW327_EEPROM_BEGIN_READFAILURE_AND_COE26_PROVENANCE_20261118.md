# PHX-MASTER UTC21 — ESP8266 EEPROM full-buffer read failure and COE #26 provenance

**Audit time:** 2026-11-18 21:10 UTC  
**Role:** PHX-MASTER — coordination, architecture contracts, provenance and integration matrix only  
**Disposition:** OPEN / DRAFT / REVIEW REQUIRED / PRODUCTION NO-GO

## Scope and exact references

- Experiments main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`
- Experiments development: `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`
- Master branch before this audit: `4c926ce7de5c6fdd2e59523b7bad55d004df9ea7`
- Hardware #327: OPEN / DRAFT, current PR/docs head `c51271938c15e13998d1c99f1d311ca777bb1cc2`, base #326 `58c558fb6a237935214621adc3dee65a10fe1a51`
- Current ESP8266 sketch blob: `4d73c5dc451c29f2ffd64a5cb2d230cc84a78ed5`
- Current ESP32 sketch blob: `ada9723c5f07879775284eb128a986ac865394f7`
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`
- COE integration #26: OPEN / DRAFT, `b382d233ff06c8791b1028bed3c617cc7b670d12`

No subsystem source branch was changed. No destination migration was proposed.

## 1. Hardware #327 — confirmed improvement and new P0 review gap

### 1.1 The new marker-only raw reader is source-consistent with ESP8266 core 3.1.2

The current ESP8266 sketch now uses `flash_hal.h` and a status-bearing `ESP.flashRead()` for the reserved poll-fault record. Its address calculation:

`EEPROM_start - 0x40200000 + POLL_FAULT_EEPROM_OFFSET`

matches the sector mapping used by ESP8266 Arduino core 3.1.2 EEPROM.cpp. The byte-buffer overload in Esp.cpp supports a byte pointer and handles pointer/size alignment. I found no offset error in this narrow mapping review.

Source references:

- [Current ESP8266 sketch at #327 head](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/blob/c51271938c15e13998d1c99f1d311ca777bb1cc2/experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino)
- [ESP8266 core 3.1.2 EEPROM.cpp — begin/read](https://github.com/esp8266/Arduino/blob/3.1.2/libraries/EEPROM/EEPROM.cpp#L46-L73)
- [ESP8266 core 3.1.2 EEPROM.cpp — sector erase and buffer write](https://github.com/esp8266/Arduino/blob/3.1.2/libraries/EEPROM/EEPROM.cpp#L126-L143)
- [ESP8266 core 3.1.2 Esp.h — byte-buffer flashRead overload](https://github.com/esp8266/Arduino/blob/3.1.2/cores/esp8266/Esp.h#L190-L203)
- [ESP8266 core 3.1.2 Esp.cpp — byte-buffer flashRead implementation](https://github.com/esp8266/Arduino/blob/3.1.2/cores/esp8266/Esp.cpp#L889-L933)

The source reserves bytes 512–543 of a 544-byte EEPROM image for the poll-fault record; a static assertion keeps Config within the first 512 bytes.

### 1.2 P0 source-level gap: the full EEPROM image read is still not status-checked

The marker-only reader does not make the initial full EEPROM image read reliable.

At the current #327 source head:

1. `loadCfg()` calls `EEPROM.begin(POLL_FAULT_EEPROM_BYTES)`.
2. It checks only `EEPROM.length()`, which confirms the requested buffer size, not that the flash read succeeded.
3. It then calls `EEPROM.get(0, current)`.
4. If `configRecordErased(current)` is true, it initializes defaults and calls `saveCfg()`.
5. `saveCfg()` writes the Config prefix and calls `EEPROM.commit()`.

ESP8266 core 3.1.2 declares `EEPROM.begin()` as void. It allocates the RAM buffer, calls `ESP.flashRead()`, logs a failed read, but does not return the failure to the caller. `EEPROM.commit()` erases the EEPROM sector and writes the entire configured buffer.

Therefore, if the initial 544-byte read fails and the RAM buffer appears erased, the Config loader can take the first-boot-default path. The subsequent full-buffer commit can overwrite bytes 512–543 before `initPendingStore()` calls `loadPollPulseFaultLatch()`. A pre-existing durable poll-fault marker could consequently be lost in this possible failure state.

This is a **source-level hazard and missing regression**, not a claim that a physical device has already lost a marker. The actual allocator contents and flash failure behavior require owner validation.

### 1.3 Why the current host lab does not close this path

The current `poll_fault_dual_store_lab.py` fake backend deliberately initializes its EEPROM RAM buffer to 0xFF and ignores the failed fake read result. That is a useful erased-looking failure model.

However, the lab extracts the dual-store helper path only; it does not execute `loadCfg()`, `configRecordErased()` or the default-config `saveCfg()` path. Its raw-read tests prove that marker-only read failure denies and avoids a marker write. They do not prove that a failed initial whole-image read cannot be mistaken for erased Config and then committed.

A separate Master-side deterministic model using the repository fake backend's all-0xFF failure state reproduced the possible marker overwrite: **1/1 model case**. This is not a repository CI test or a hardware result.

### 1.4 Required owner follow-up — task #177 / PR #327

PHX-HARDWARE should add a source-extracted regression with:

- A pre-existing valid poll-fault record at offset 512.
- An injected failure of the initial 544-byte EEPROM.begin read.
- A subsequent successful marker-only raw read (transient failure case).
- The Config-erased/default branch exercised through loadCfg().
- An assertion that no commit can erase, corrupt or replace the pre-existing marker or unverified Config bytes.
- A persistent-read-failure case that remains deny-only and does not commit a guessed image.
- A cold-boot check after the failure path.

The implementation must make a full-image read failure distinguishable from a genuinely erased Config region. No EEPROM commit should occur from an unverified RAM image. Hardware owns the source correction; Master will not edit the firmware.

PHX-QA should independently review the exact corrected source SHA and verify both marker preservation and default-deny behavior. PHX-RELEASE should pin the ESP8266 core version in the source build workflow or assert the resolved version. The current exact CI run resolved 3.1.2, but the workflow command remains unpinned.

## 2. Exact #327 CI — current candidate

- [Quarantine/readback run 44395507848](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44395507848): PASS. Logs include ESP8266 raw-flash-read deny/write-deny, dual-store lab PASS on both boards, and poll-edge snapshot-race PASS on both boards.
- [Relay/output run 44395508081](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44395508081): PASS. Host polarity/output ordering checks passed; physical GPIO/relay behavior was not tested.
- [Full build run 44395507878](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44395507878): FAIL at the inherited QA positive `Missing poll signature check` assertion. All 13 firmware/platform target jobs and Android completed successfully. Downstream simulation, update bundle, candidate gate, signing and publishing were skipped.

The current firmware remains deny-only. The QA fixture must be corrected to negative/default-deny assertions; firmware must not regain synthetic positive poll admission.

No physical board, coin acceptor, relay, flash power cut or payment test was performed.

## 3. COE #26 — exact destination tree and provenance refresh

Current source tree: #327 head `c51271938c15e13998d1c99f1d311ca777bb1cc2`.  
Current destination tree: COE #26 head `b382d233ff06c8791b1028bed3c617cc7b670d12`.

| Item | Experiments source tree | COE #26 destination |
|---|---:|---:|
| ESP32/ESP8266 Python board labs | 18 | 0 |
| Firmware sketches | 2 | 2 |
| Sketch blobs byte-identical | — | 0 of 2 |
| Hardware generic shell test | source-specific labs | 1 |
| Root NOTICE.md | present | absent |

Exact sketch blobs:

- ESP8266 source `4d73c5dc451c29f2ffd64a5cb2d230cc84a78ed5`; destination `c8be98f72596681e36a3ad1f8939bf8046c96887`.
- ESP32 source `ada9723c5f07879775284eb128a986ac865394f7`; destination `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.

The destination test `Hardware/tests/test_firmware_hardening.sh` blob `f921c56cecc19cab1989507b9b4ade1f45dac54e` still requires `response_sig` and `|poll|`. Destination workflow `.github/workflows/hardware-ci.yml` blob `fe79adbdb3745a22c5ef6d1f0c87c868b7785793` invokes that generic test. The source's 18 board-lab files are not present under destination Hardware. COE #26 currently has five workflows queued and zero jobs.

### NOTICE correction

Correction to the earlier UTC17/UTC18 wording: the current source tree **does contain** root `NOTICE.md`, blob `f6d92cd21465312be5993631fe26977219be0fb9`. It is absent from the COE #26 destination tree. The TailAdmin vendor NOTICE remains byte-identical in both trees. The source project MIT LICENSE blob `1ee55b94183417be977ca287cd7391f9a6f7e721` matches COE `Pisowifi/LICENSE`, but the intended scope of that sibling-directory license over `Hardware/` remains unresolved. This is a provenance/scope gap, not a legal conclusion.

**Decision:** no copy, move, overwrite, import proposal or route change. Require per-file source blob, license/notice scope, test identity, import completeness and exact-head CI mapping first.

## 4. Other role and release reconciliation

| Owner | Current PR / head | Exact-head CI result |
|---|---|---|
| CORE | Experiments #252 / `c82705f2...` | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS |
| RENTAL | #289 / `68928774...` | [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) PASS |
| PISONET | #255 / `d01fd164...` | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS |
| HARDWARE | #323 / `988904e8...`; #326 / `58c558fb...`; #327 / `c5127193...` | #327 focused PASS; Full FAIL as above |
| QA | #290 / `5c29d159...`; #292 / `75a3f66d...` | #290 [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS (native COM lab not invoked); #292 no exact-head run returned and its base is stale |
| RELEASE | Experiments #291 / `691ed55d...` | [44353380470](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44353380470) handover/build PASS; privileged publisher skipped |
| COE RELEASE | #35 / `1a5be48d...`; child #44 / `582fd5d5...` | #44 shared [44390136309](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136309) PASS; case [44390136296](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136296) PASS; mandatory sandbox [44390136327](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136327) FAILS closed because bubblewrap is missing after 14/14 host-preflight tests |
| COE CORE | #45 / `9d76a134...` | [44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) and [44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) PASS |

COE #44's site-scoped ULA authority remains pending; its random per-install prefix does not yet prove same-site multi-appliance prefix sharing. The separate CORE continuation retains CORE ownership; PHX-MASTER did not touch CORE source or start a competing CORE worker.

## 5. Governance, instructions and access

- Experiments main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Experiments development `2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- Master before this audit `4c926ce7de5c6fdd2e59523b7bad55d004df9ea7`.
- COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- COE #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- Branch objects report `protected=false` for Experiments main/development/Master and COE main; both repository rulesets endpoints returned empty lists. No settings were changed.
- Cleanup issue #266 remains OPEN; its checklist pins are historical and do not prove cleanup completion.
- Experiments AGENTS.md, README_FIRST, 00_MASTER_PROJECT_PHOENIX, BLAZE-COMMS/1, Cloud Artifact Policy and Cloud Storage Handover were read. The policy/handover require the owner-private registry and sync ledger before archive work.
- The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections are not available through the exposed connector/Library. No Google Drive connector is exposed. Older Library snapshots were not substituted. No private Drive identifiers or contents were published; no mirror/upload was attempted.
- Master PR #288 had no PR-triggered CI run on its prior head.

## 6. Verification performed by PHX-MASTER

- Exact source/destination tree assertions: **13/13 PASS**.
- Master-side deterministic all-0xFF failed-read model: **1/1 reproduces possible marker overwrite**. This is a bounded model, not repository CI or hardware evidence.
- GitHub CI: focused and Full results linked above; these are actual hosted runs.
- Full Master Python suite: NOT RUN.
- Master Actions: no run returned.
- Physical acceptance: NOT TESTED.

## 7. Next actions and release disposition

1. **PHX-HARDWARE / task #177:** add the fail-first whole-image EEPROM read regression and prevent commits from unverified RAM buffers.
2. **PHX-QA:** independently review the corrected exact SHA, verify marker preservation across reboot, and replace the stale positive poll-signature fixture with negative default-deny tests.
3. **PHX-RELEASE:** pin ESP8266 core 3.1.2 or assert the resolved version in the build workflow.
4. **COE integration owner:** retain #26 as draft; complete exact per-file source/license/NOTICE/test mapping before any import.
5. **Repository administrator:** configure and verify branch protections and required checks.
6. **Registry custodian:** restore authorized access to private v11 and newer corrections.

**PRODUCTION NO-GO** remains mandatory until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently evidenced.

No subsystem source branch was changed. No migration, merge, release, signing, secret provisioning, hardware flashing, physical testing or real-payment operation occurred. No Codex was used.
