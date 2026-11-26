# PHX-HARDWARE UTC21 — ESP configuration persistence write-result guard

**Task:** PR #355 — setup configuration save must not claim success when storage reports failure  
**Control plane:** [Issue #172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-poll-preflight-lab-modules-20261127-utc18`  
**Parent PR:** [#354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/354) at `fc842342596786e072630179acfbbc4feeb2ba02`  
**Current PR:** [#355](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/355), OPEN / DRAFT / UNMERGED  
**Firmware correction commit:** `26a28c763168e2881d5b8e36d859a0a72d704524`  
**Exact focused source/test SHA:** `835017d95c129fb52b8fdca82032f1fb9a83ac33`  
**Documentation/source-comment sync parent:** `7ddcd897a3e69708294813a65e9eb6152b5e506b` · **Focused test SHA:** `835017d95c129fb52b8fdca82032f1fb9a83ac33`

## Proven defect

The ESP8266 EEPROM API declares `bool EEPROMClass::commit()` (ESP8266 Arduino core 3.1.2: [EEPROM.h](https://github.com/esp8266/Arduino/blob/3.1.2/libraries/EEPROM/EEPROM.h)). The prior `saveCfg()` ignored that result, and the setup POST handler always sent HTTP 200 and rebooted.

The ESP32 Preferences API declares `size_t` return values for `putString`, `putInt`, `putBool` and `putUInt` in both supported framework headers ([3.3.13](https://github.com/espressif/arduino-esp32/blob/3.3.13/libraries/Preferences/src/Preferences.h), [4.0.0](https://github.com/espressif/arduino-esp32/blob/4.0.0/libraries/Preferences/src/Preferences.h)). The previous `saveConfig()` ignored all 13 write results, then reported success and rebooted even if NVS rejected a write.

This could falsely tell a technician that changed Wi-Fi/device configuration was persisted. It did not alter paid balances or coin-event state.

## Firmware correction

- ESP8266 `saveCfg()` now returns `EEPROM.commit()`; the legacy-migration and defaults paths log a persistence failure rather than claiming a successful write.
- ESP8266 setup POST now checks `saveCfg()`. On failure it calls `denyRemoteControl()`, returns HTTP 500, and does not reboot or send the success response.
- ESP32 `saveConfig()` now checks every one of the 13 Preferences writes and returns false if any reports zero bytes written.
- ESP32 setup POST applies the same deny / HTTP 500 / no-reboot failure path.
- No EEPROM layout, Preferences key schema, pin mapping, network protocol, coin admission, pending journal, financial state, or shared CORE API changed.

**Explicit limitation:** ESP32 Preferences writes are still separate key writes, not an atomic multi-key transaction. If one write fails after earlier keys succeeded, partial configuration may already be stored. The handler now refuses success and reboot, and the candidate remains deny-only; this change does not claim rollback or transactional configuration durability.

## Test-first and exact CI evidence

- Expected test-first RED: [run #45896260968](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45896260968), job `140170795839`. The new lab correctly failed because the existing ESP8266 `saveCfg()` did not return the EEPROM commit result.
- Intermediate test-authoring failures were preserved and corrected: [#45896421871](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45896421871) selected the portal GET's HTTP 200 instead of the save-success response; [#45896529929](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45896529929) caught a malformed regex literal. These were test defects, not firmware failures.
- Exact focused GREEN: [run #45896670130](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45896670130), job `140172158275`, exact head `835017d95c129fb52b8fdca82032f1fb9a83ac33`: PASS.
  - `ESP8266_EEPROM_COMMIT_FAILURE_PROPAGATED_PASS`
  - `ESP32_PREFERENCES_WRITE_FAILURE_PROPAGATED_PASS writes=13/13`
  - Four injected regressions rejected: ignored EEPROM result, ignored ESP8266 failure gate, ignored Preferences write result, and ignored ESP32 failure gate.
  - Existing poll, deny-only remote-config, request-auth, output-polarity and bounded EEPROM labs also passed in the same job.
- Native synthetic [#45896670074](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45896670074), job `140172158388`: FAIL at QA-owned `PAY-0745 durable Vendo pending sequence and corruption contract`. Hardware did not add a pending disposition callsite.
- Full build [#45896670128](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45896670128): CI-0701 passed; validation job `140172339002` stopped at the mandatory handover freshness gate because this documentation had not yet been synchronized to the source change. Target jobs were still running at the last check; they are not counted as completed evidence here.
- ESP32 Mbed TLS matrix [#45896670138](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45896670138) was pending at the last check.

## Current coordination and release status

- Experiments `main`: `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`.
- Active v0.6 audit-foundation: `2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- Master coordination: `0e8a59a0463d522ddff95371a60cf271d4c752bc`; Master has recorded PR #355 in role assignments and integration matrix.
- PR #239, #254 and #283 remain OPEN / DRAFT / UNMERGED. Current audited heads: #239 `d83b715b`, #254 `84c442a4`, #283 `4dd0b01b`.
- Issue #177's synchronous poll / pulse-loss P0 is not fixed by this configuration-save change. Cleanup-first #266 remains OPEN / 0-of-7. Financial #31/#32, safety/hardware acceptance #34, and witness #43 remain OPEN.
- CoinOperatedEcosystem main remains `a6513ab4`; PR #26 remains frozen at `b382d233`.
- Private Google Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` remains unavailable through the exposed connector and was not found in Library search. No older registry was substituted.

## Acceptance classification

- Source-extracted host storage-failure harness: **SIMULATED / CI VERIFIED**.
- Focused GitHub Actions at exact source/test SHA: **CI VERIFIED**.
- Full target builds: **IN PROGRESS / NOT COUNTED** at this checkpoint.
- Physical GPIO, EEPROM/NVS brownout behavior, relay and coin-pulse recovery: **NOT TESTED**.
- 150 power cuts, 30-device/24-hour soak, electrical acceptance: **NOT TESTED**.
- Protected anti-rollback signer/witness, durable accounting/replay, v1→v2 migration, independent QA/release signoff: **NOT ACCEPTED**.
- **HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO.**

No secrets, live money, physical flash, device reset, production migration, deployment, merge, force-push or release tagging occurred.
