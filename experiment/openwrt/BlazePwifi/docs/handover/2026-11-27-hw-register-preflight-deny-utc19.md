# PHX-HARDWARE UTC19 — startup register fail-closed guard coverage

**Role:** PHX-HARDWARE  
**Task:** hardware #177 / cleanup-first #266 / existing stacked DRAFT PR #355  
**Branch:** `phoenix/hw-poll-preflight-lab-modules-20261127-utc18`  
**Parent/base:** `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05@fc842342596786e072630179acfbbc4feeb2ba02`  
**Source/test SHA:** `caeea7f30bc959c3264b785592b8e53f28d040b6`  
**Prior canonical docs-sync HEAD:** `375bbd4824f12e0c6ffe513432c988f95394ca45`  
**Current PR state:** OPEN / DRAFT / UNMERGED · **PRODUCTION:** NO-GO.

## Completed bounded task

Added source-extracted assertions to the Hardware-owned poll-preflight lab for the synchronous startup register exchange on both ESP8266 and ESP32. The contract requires exactly one register POST inside the Wi-Fi-connected `connectSta()` branch, explicit response discard, no startup `applyRemoteConfig()` consumer, unconditional deny before `connectSta()`, and unconditional deny after registration. Comment/string decoys are ignored.

Failure injection rejects **8/8** unsafe mutations per board, including missing/conditional startup deny, moving register outside the Wi-Fi-connected branch, missing/conditional post-register deny, consuming/applying the response, and duplicate register POST outside `connectSta()`. The two response-use variants are separately **2/2 rejected**.

No production `.ino`, GPIO logic, shared API, QA/CORE/Master source, finance, signer, witness, migration or COE destination changed.

## Exact evidence

- Focused source/test [#45882710658](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45882710658), job `140125732751`: **PASS** at `caeea7f30bc959c3264b785592b8e53f28d040b6`.
- Focused docs-head [#45883295366](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45883295366), job `140127681438`: **PASS**; both boards 8/8 mutations rejected, 2/2 response-use variants rejected, decoys ignored; poll 4/4 polarity and blocking-wait model PASS.
- Mbed TLS [#45882710626](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45882710626): source-contract `140126409598`, core 3.3.13 `140126410030`, core 4.0.0 `140126410147`: **PASS** at exact source/test SHA.
- Full pre-sync [#45882710608](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45882710608): 13 firmware targets + Android PASS; validation failed stale handover, superseded by the post-sync run.
- Full post-sync [#45883295442](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45883295442): CI-0701 and handover gate PASS; validation `140127752453` fails at QA-owned `tests/controllers.sh:21` because `config_revision` is absent. Both sketches contain `applyRemoteConfig` only as a deny-only stub (`(void)response; denyRemoteControl();`) and have no callsite. Thirteen firmware target jobs PASS; Android `140127752382` IN_PROGRESS at last check. Production import/update/simulation/candidate/signing/publication skipped.

## Release and ownership boundary

QA owns the deny-only-incompatible `config_revision` assertion; CORE owns authenticated register/poll and receipt/disposition; MASTER owns global assignments and branch pins. Master role files at `ed6bb786c08d360a611e0e6c5c0505fa90d9b477` still do not list #355. Cleanup #266 remains OPEN / 0-of-7; financial #31/#32, safety #34 and witness #43 remain open.

Host/source-extracted results are SIMULATED / CI VERIFIED only. Physical GPIO/relay, real coin acceptor, electrical pulse/recovery, LittleFS power-loss, 150 power cuts and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO. Private Drive registry v11 and hourly signal YAML were not available; no older registry substituted.

## Next exact action

Request QA/CORE/Master reconciliation, preserve deny-only behavior, and continue Hardware work only after the authenticated contract is approved. Keep PR #355 DRAFT and parent #354 unchanged.

**Updated UTC:** 2026-11-26T19:25:00Z

## UTC19 — startup output deny before LittleFS recovery

## CURRENT STATUS — 2026-11-27 UTC19 — startup output deny moved ahead of LittleFS recovery; exact-head CI pending

**Role:** PHX-HARDWARE · **Task:** hardware #177 / cleanup-first #266 / DRAFT PR #355 (stacked on #354)  
**Branch:** `phoenix/hw-poll-preflight-lab-modules-20261127-utc18` · **Parent/base #354:** `fc842342596786e072630179acfbbc4feeb2ba02`  
**Test-first RED:** `39aa77e56806df3c1febae0f0a097b0f661ca2c6` · **Firmware correction:** `6bb8eafe03e5a2548524b7c693a37a95638c140e`  
**PR:** OPEN / DRAFT / UNMERGED · **Production:** NO-GO.

### Proven startup-order defect and correction

Both current Vendo sketches mounted/recovered LittleFS before configuring the configured relay/LED pins and calling `denyRemoteControl()`. This left a potentially blocking filesystem mount and pending-journal recovery ahead of the software output-off latch.

The setup order is now:
1. Load persisted pin/polarity configuration.
2. Apply configured runtime pins with the existing OFF preload behavior.
3. Call `denyRemoteControl()` so controller, coin, relay and LED admission remain disabled.
4. Only then mount/recover LittleFS and inspect pending journal state.
5. Continue portal/network setup with the existing deny-only behavior.

ESP8266 moves `initPendingStore()` after the output latch. ESP32 moves `LittleFS.begin(false)` and `loadPending()` after it. No pin mapping, polarity, journal format, receipt semantics, positive coin admission or shared API changed.

**Scope limitation:** EEPROM/Preferences configuration loading still precedes pin initialization because the saved pins/polarity are needed to select the correct OFF level. This change does not prove the electrical state during that configuration read; board-level bias and physical boot behavior still require hardware evidence.

### Test-first evidence

- Expected RED at test-only SHA `39aa77e56806df3c1febae0f0a097b0f661ca2c6`: [focused run #45886210859](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45886210859), job `140137430702`. The new guard failed on **both ESP8266 and ESP32** because LittleFS startup preceded configured output pins and the deny latch. This is the expected pre-fix failure.
- Firmware correction at `6bb8eafe03e5a2548524b7c693a37a95638c140e`. Exact-head focused GREEN and Full results are pending; do not treat the RED as a passing test.
- Full build [#45886367363](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45886367363) was pending when this checkpoint was written.

### Ownership and release boundary

Only ESP8266/ESP32 sketches and Hardware-owned lab/handover paths changed. QA retains controller assertions, CORE retains authenticated register/poll and receipt/disposition contracts, MASTER retains role assignments and stack pins. #355 stays a DRAFT child of #354; no merge, rebase, retarget or force-push.

Host/source-order tests are **SIMULATED** until exact-head CI completes. Physical GPIO/relay, real coin acceptor, electrical pulse/recovery, LittleFS power-loss, 150 power cuts and 30-device/24-hour soak remain **NOT TESTED**. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.


**Exact scope:** `BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`, `BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`, and Hardware-owned startup-order guard. The test-only RED at `39aa77e` failed on both boards as expected; firmware correction `6bb8eafe` moves filesystem initialization after output configuration and deny. Exact-head GREEN remains pending at this checkpoint. EEPROM/Preferences config reads still precede GPIO setup; board-level bias and physical boot behavior are not established.

## UTC19 exact-head startup output latch CI update

Source/test SHA `6b4f7a873dd72663c00c4e08f23131d58e662584`. Focused [#45886748490](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45886748490) job `140139222908` PASS for ESP8266/ESP32 startup output-before-LittleFS and early-mount mutation rejection. Mbed matrix [#45886748407](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45886748407) PASS: source contract, ESP32 core 3.3.13 and 4.0.0 clean builds. Full [#45886748466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45886748466) target builds and CI-0701 passed, but validation job `140140135720` failed because CHANGE_LEDGER lacked the required `## 2026-` heading. This heading is now recorded; a fresh Full run is required. Native synthetic [#45886748463](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45886748463) still fails QA-owned active-`clearPending` assertion. Physical acceptance NOT TESTED; keep PR #355 DRAFT and coin admission deny-only.

## UTC19 final post-sync Full/QA revalidation

At docs head `d4a35e5e12b8abd85b6a45fa6902d09471c84e4d`, focused #45887618603 job `140142163199` PASS; exact-source Mbed #45886748407 source-contract and core 3.3.13/4.0.0 builds PASS. Full #45887618795 CI-0701 and mandatory handover freshness/history gate PASS, but QA-owned `controllers.sh:21` fails on missing `config_revision`; ESP8266 and all 13 OpenWrt target jobs PASS, ESP32/Android in progress at last check. Native #45887618600 fails QA-owned active-`clearPending` assertion. Keep deny-only and PR #355 DRAFT; physical acceptance NOT TESTED, PRODUCTION NO-GO.
