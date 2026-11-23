# PHX-HARDWARE — boot GPIO OFF before LittleFS mount

**Checkpoint:** 2026-11-21 UTC02  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Exact source/test SHA:** `2d10db5db8ad95f15abf335f25cbbbb2d02c7fae`  
**Firmware behavior commit:** `ebadec9aaed3113c632a0776a2ac71238ecd0d13`  
**Test-first RED commit:** `430910122111dc246686145c4dea4882a3fa125b`

## Finding

Both production `setup()` paths loaded local configuration and then mounted LittleFS through `initPendingStore()` before calling `configureRuntimePins()`. That left the relay/LED pins without an explicit firmware OFF preload during filesystem mount/recovery. The actual external relay state during reset is not proven by source inspection, but the source ordering unnecessarily prolonged the high-impedance interval after the stored pin/polarity configuration was already known.

This is a bounded boot-time coin-ingress safety mitigation, not proof that any physical relay was energized or that a coin pulse was lost.

## Firmware change

- **ESP8266:** `loadCfg()` completes first, so the EEPROM fault-backup configuration is available. After validated runtime pin/polarity selection, `configureRuntimePins()` now drives outputs OFF and attaches the coin ISR **before** `initPendingStore()` mounts LittleFS.
- **ESP32:** `loadConfig()` and `initPollFaultBackupStore()` complete first, making the NVS backup available. After validated runtime pin/polarity selection, `configureRuntimePins()` now drives outputs OFF and attaches the coin ISR **before** `initPendingStore()` mounts LittleFS.
- Portal startup and network connection remain after storage initialization.
- No register/poll/coin response contract, positive admission path, financial behavior, relay policy, or shared API was changed. Existing default-deny behavior remains.

If an ingress transition is detected before LittleFS is mounted, the LittleFS fault-marker write is unavailable by design; the already-initialized EEPROM/NVS secondary store is the persistence path. Once LittleFS mounts, boot latch loading observes that secondary marker and denies admission. If both persistent stores fail, the existing limitation remains: the current boot is denied, but durable post-reboot evidence cannot be guaranteed.

## Test-first evidence

### RED — test-only commit

Commit `430910122111dc246686145c4dea4882a3fa125b` added source-order guards before the firmware change.

- Relay/output PR run [#44853714503](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44853714503)
  - ESP32 boot-polarity job `136690820247`: expected FAIL — `relay/LED GPIO OFF configuration must precede LittleFS mount`.
  - Source/output job `136690820485`: expected FAIL — same assertion.
- This is the intended test-first RED; the assertion exposed the existing unsafe ordering on both board setup paths.

### GREEN — exact source/test SHA

Commit `2d10db5db8ad95f15abf335f25cbbbb2d02c7fae` includes the firmware reorder, source-order guards, mutation injection, and a dual-store fixture that models `fsReady=false` before LittleFS mount.

- Quarantine push [#44854117893](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44854117893), job `136692139117`: **SUCCESS**.
  - `GPIO_OFF_BEFORE_LITTLEFS_MOUNT_PASS board=ESP8266`.
  - `PRE_LITTLEFS_SECONDARY_BACKUP_REBOOT_DENY_PASS` on ESP8266 and ESP32.
  - `POLL_FAULT_DUAL_STORE_LAB=PASS` on both boards.
  - `SIMULATED_ONLY=1`; physical relay/power-cut markers remain false.
- Quarantine PR [#44854124210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44854124210), job `136692158151`: **SUCCESS**.
- Relay/output PR [#44854124205](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44854124205):
  - Source/output job `136692157830`: **SUCCESS**.
  - ESP32 boot-polarity job `136692158209`: **SUCCESS**, with `GPIO_OFF_BEFORE_LITTLEFS_MOUNT_PASS board=ESP32`.
- Full push [#44854117952](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44854117952):
  - Firmware/target + Android jobs: **14/14 SUCCESS**.
  - Validation job `136692223812`: **FAILURE**, inherited QA-owned `Missing poll signature check` in `experiment/openwrt/BlazePwifi/tests/controllers.sh`.
  - Downstream signed import, simulation, update bundle, candidate/signing/publication gates did not pass and remain closed.
- Full PR [#44854124169](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44854124169), validation job `136692241195`: same **FAILURE** at `Missing poll signature check`. At handover capture, the Android job was still running; no result is claimed for that PR matrix.

## Scope and safety boundary

Changed only Hardware-owned ESP8266/ESP32 sketches, their boot-polarity labs, the Hardware dual-store lab fixture, and this handover. No QA-owned controller assertion, CORE server/API, financial ledger, witness, Release workflow, COE destination, secret, customer data, or production deployment was changed.

No physical flashing, router reset, coin insertion, live money, production migration, signing, release tag, merge, or force-push was performed.

## Current blockers

1. Full validation remains blocked by the QA-owned positive poll-signature assertion. PHX-CORE must publish the approved authenticated register/poll/coin receipt contract; PHX-QA must align source-exact tests without weakening default-deny.
2. Master-owned `ROLE_ASSIGNMENTS.md` and `INTEGRATION_MATRIX.md` still pin an obsolete #327 head; #172's body also has stale #327 and Master heads. Current Master PR #288 head at audit was `fcb3f1d5ad6d9dbe0c9e8431910277fc97693b03`; current Hardware source/test SHA is above. Hardware did not edit Master-owned coordination files.
3. The requested private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available through the connected Library surface. An older `BLAZE_PROJECT_REGISTRY.json` snapshot was not substituted.
4. The Hardware README still says “current production release 0.3.0” while the root README labels BlazePwifi alpha; Master/Release should reconcile the public status wording.

## Evidence classification

- Boot-order and dual-store host tests: **SIMULATED / CI VERIFIED**.
- Firmware target builds: **CI VERIFIED** on the Full push matrix (14/14).
- Physical relay polarity, pulse conditioning, electrical recovery, 150 power cuts, and 30-device/24-hour soak: **NOT TESTED**.
- HARDWARE ACCEPTED: **NO**.
- PRODUCTION READY: **NO**.

## Next exact action

PHX-MASTER refreshes the #172 active-head table, `ROLE_ASSIGNMENTS.md`, and `INTEGRATION_MATRIX.md` to the current #327 head without retargeting the stack. PHX-CORE/PHX-QA resolve the authenticated response contract and Full validation blocker. PHX-HARDWARE re-reads all live heads on the next activation before selecting the next owned firmware task.
