# PHX-HARDWARE — ESP32 NVS boot readback fail-closed

**Date:** 2026-11-19 UTC22  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**PR:** [#327 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Parent:** #326 at base SHA `58c558fb6a237935214621adc3dee65a10fe1a51`

## Scope and source finding

The current Full build run [#44622826708](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44622826708) resolved ESP8266 Arduino core **3.1.2** (job `135908880352`) and ESP32 Arduino core **4.0.0** (job `135908881052`). The build workflow installs `esp8266:esp8266` and `esp32:esp32` without explicit version pins; these are observed resolved versions for that run, not a reproducible pin.

Upstream source checked:
- [ESP8266 Arduino 3.1.2 EEPROM.cpp](https://github.com/esp8266/Arduino/blob/3.1.2/libraries/EEPROM/EEPROM.cpp): `EEPROM.begin()` reuses a same-size buffer and its initial `flashRead` result is not used as an admission signal.
- [ESP32 Arduino 4.0.0 Preferences.cpp](https://github.com/espressif/arduino-esp32/blob/4.0.0/libraries/Preferences/src/Preferences.cpp): `Preferences::getString(key, default)` returns the caller's default when `nvs_get_str` fails; `getStringLength()` and the caller-buffer `getString()` return zero on read/length errors.

The ESP32 `loadConfig()` path read persisted strings through the fallback-returning overload, then accepted a valid local polarity marker through `loadLocalOutputPolarity()`. It did not verify that the just-loaded config still matched stored NVS values through the existing status-bearing `configFieldsMatchStored()` helper. A persistent read error could therefore leave `outputPolarityKnown=true` even though a field had been replaced by a fallback.

## Test-first evidence

- **RED:** [#44631396775](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44631396775), job `135938652043`, test-only commit `3ffdcc4f31ecb4317239f4bdf7bae2519b9f0791`. The new simulated-reboot test failed as intended with `NVS_BOOT_STRING_READ_ERROR_TRUSTED_POLARITY key=ssid` (exit 50).
- **GREEN after firmware fix:** [#44631548311](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44631548311), job `135939185853`, firmware fix commit `3c102f2fd5c518ea46f65be1ae217adb7a7415da`. The normal reboot and 5/5 string-read plus 5/5 length-read failure cases passed.
- **Exact source/test head including guard-removal mutation:** [#44631781169](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44631781169), job `135940008974`, source/test SHA `291f5206599f033d7e21cd3b031e7dd771afe748`: SUCCESS. Log confirms `ESP32_NVS_REBOOT_READ_FAILURE_FAIL_CLOSED_PASS 5/5 string reads and 5/5 length reads` and `MUTATION_REJECTED ESP32 missing boot readback guard mutation exit=50`.
- **Relay/output:** [#44631781075](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44631781075), jobs `135940008584` and `135940008960`: SUCCESS.

## Firmware change

In `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`:
- Added a forward declaration for `configFieldsMatchStored(const char **)`.
- After loading persisted fields, if a valid local polarity marker was found, `loadConfig()` now requires exact stored-field readback before trusting that polarity.
- On mismatch/read/length/allocation failure it clears config/run polarity, `outputPolarityKnown`, `pinConfigSafe`, `insertMode`, and `activeTarget`; runtime pin setup therefore remains INPUT-only.

In `nvs_string_readback_lab.py`:
- Added a simulated Preferences-handle reboot retaining only stored maps.
- Added a normal valid reboot control.
- Injected failures for each of five string fields through both fallback string read and explicit length/read paths.
- Added a deliberate guard-removal mutation and asserted that the regression rejects it for the expected boot-read failure.

No NVS namespace/key/schema, shared API, poll contract, financial logic, positive coin-admission path, GPIO polarity convention, or Release-owned workflow was changed.

## Remaining blockers and exact next actions

1. **PHX-QA:** independently review source/test SHA `291f5206599f033d7e21cd3b031e7dd771afe748`; replace the inherited positive poll-signature assertion only through an approved source-linked deny-contract test. Current Full validation still fails at `Missing poll signature check` in QA-owned `tests/controllers.sh`.
2. **PHX-RELEASE:** pin ESP8266 core 3.1.2 and ESP32 core 4.0.0, or add explicit resolved-version attestation. The build workflow is Release-owned and was not edited here.
3. **PHX-MASTER:** refresh `ROLE_ASSIGNMENTS.md`, #172 and the integration matrix with the live #327 head and this hardware-owned NVS finding. Current role-assignment snapshot still lists #239/#254/#283 but not #327.
4. **PHX-HARDWARE:** revalidate all heads on the next activation and take only the next unblocked hardware-owned task.

## Latest Full build disposition

Current docs-head Full build [#44631781091](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44631781091):
- Validation job `135940160543`: **FAILED** at QA-owned `Missing poll signature check` in `tests/controllers.sh`.
- ESP8266 target job `135940160792`: **SUCCESS**.
- ESP32 target job `135940160855` and all remaining target/platform jobs: **CANCELLED** after validation failed.
- Therefore no current Full target-matrix pass is established. The earlier run that resolved core versions is toolchain provenance only; it predates this NVS boot-readback fix.

## Evidence limits

This is a source-extracted host simulation with a fake Preferences backend, plus CI verification. It is **SIMULATED / CI VERIFIED**, not a real ESP32 NVS power-cut/reboot acceptance. Physical NVS durability, electrical relay behavior, 150 power cuts, 30-device 24-hour soak, and hardware acceptance remain **NOT TESTED**. No device was flashed or reset; no live coins or financial state were used. Production remains **NO-GO**.

Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not available in the connected Library/Drive tools during this activation; no substitute registry or private provenance data was copied into GitHub.


## UTC23 — Explicit ESP32 Preferences namespace-open failure

**Date:** 2026-11-19 UTC23  
**Role:** PHX-HARDWARE  
**PR:** [#327 OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Source/test SHA:** `9ef753a38226fcdf56b0903680a5110348027110`  
**Test-first RED SHA:** `b9c343447c00d32307d2436878f189bd353dadbf`

### Source finding

The pinned ESP32 Arduino core 4.0.0 [Preferences.cpp](https://github.com/espressif/arduino-esp32/blob/4.0.0/libraries/Preferences/src/Preferences.cpp) returns `false` from `Preferences::begin()` when NVS namespace open fails and leaves the handle not started. In that state, typed/string reads return defaults and writes return zero.

Before this change, `loadConfig()` ignored the return value and continued issuing reads, then attempted to write a generated `appass` through the inactive handle. The device's polarity gate already kept relay/LED pins inhibited, but the boot path did not explicitly stop after the failed namespace open.

### Test-first evidence

- RED commit: [`b9c34344`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/b9c343447c00d32307d2436878f189bd353dadbf).
- Push run [#44640050032](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44640050032), job `135968479328`: expected **FAIL** at `NVS_NAMESPACE_OPEN_FAILURE_NOT_HANDLED read_calls=13 write_calls=1`. This proves the old path performed 13 post-failure reads and one write attempt.

### Firmware correction

In `BlazePwifiVendo32.ino`, `loadConfig()` now checks `prefs.begin("blazevendo",false)`. On failure it:
- resets the configuration to safe defaults;
- clears output-polarity trust and pin-config safety;
- clears insert mode and active target;
- generates an ephemeral setup-AP password without attempting persistence;
- logs a critical namespace-open failure and returns before any further Preferences access.

No NVS namespace/key/schema, GPIO mapping, relay behavior on successful boot, poll/coin protocol, financial logic, shared API or Release-owned workflow changed.

### Regression and exact-head evidence

The fake Preferences backend now models `begin()` failure and the inactive-handle behavior. The lab asserts zero subsequent NVS reads/writes, safe output state and an ephemeral setup-AP password. It also removes the new guard deliberately.

- Exact source/test push [#44640230847](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44640230847), job `135969107058`: **SUCCESS**. Log includes `NVS_NAMESPACE_OPEN_FAILURE_EXPLICIT_FAIL_CLOSED_PASS` and `MUTATION_REJECTED ESP32 missing namespace-open guard mutation exit=52`.
- Relay/output PR run [#44640237308](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44640237308), jobs `135969131425` and `135969131902`: **SUCCESS**.
- Full build push [#44640230839](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44640230839), validation job `135969235458`: **FAILED** at the inherited QA-owned `Missing poll signature check` in ESP8266 controller validation. No positive poll authentication was invented and no firmware admission gate was weakened. Other target jobs were still running at the last status read; this is not a full target-matrix pass.

### Coordination and boundaries

- PHX-MASTER PR #288 is now at `52cb1a68f256c3f50969e5b23ccc1f57a3bf2782`. Its UTC23 report and integration matrix reconcile #327 at the current head. The canonical `ROLE_ASSIGNMENTS.md` Hardware active-PR list still names #239/#254/#283, so its task list needs a further narrow refresh.
- COE #48 remains **UNASSIGNED / AUDIT-ONLY** with no `OWNERSHIP_ROUTES.json` entry. No COE #48 source was changed.
- PHX-QA owns the stale positive poll-signature fixture. PHX-RELEASE owns Arduino core version pinning/attestation. No QA, CORE, MASTER, COE or Release-owned paths were modified.

### Evidence limits

This is source-extracted host simulation plus GitHub Actions. It is **SIMULATED / CI VERIFIED**, not physical NVS, relay, coin-slot or power-cut acceptance. No device was flashed/reset; no live coins, customer data, finance state, production migration, signer or release operation was used. 150 power cuts, 30-device/24-hour soak and electrical pulse/recovery remain **NOT TESTED**. Production remains **NO-GO**.
