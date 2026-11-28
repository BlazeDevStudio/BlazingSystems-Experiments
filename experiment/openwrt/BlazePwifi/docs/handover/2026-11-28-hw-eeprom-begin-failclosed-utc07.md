## PHX-HARDWARE UTC08 — EEPROM checked-store persistence contract (#374) — IN PROGRESS

**Task:** PHX-HW-EEPROM-STORE-TEST-CONTRACT-20261128T09Z  
**Role:** PHX-HARDWARE  
**PR:** [#374](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/374), OPEN / DRAFT / UNMERGED  
**Branch:** phoenix/hw-eeprom-begin-failclosed-20261128-utc07  
**Parent:** PR #373 at 3783654a3c9862598bbb714268c536fb8b34578b  
**Source/test commit:** 3934cf40f1a2999ba66df2fb4e9ff2f0a1081e51  
**Updated:** 2026-11-28T09:05:00Z (2026-11-28 17:05 Asia/Manila)

### Selected work and concrete changes

The previous #374 source change replaced ESP8266 core 3.1.2's void-returning EEPROM.begin() with a Hardware-owned CheckedEEPROMClass wrapper. The wrapper has a checked allocation and flash-read path, and configStoreReady gates configuration reads/writes, station networking, poll traffic and output admission.

That source change exposed a stale Hardware persistence test which still expected direct EEPROM.put() / EEPROM.commit() calls. This activation corrected the test contract to exercise the wrapper actually used by the sketch:

- config_persistence_write_result_lab_contract.py: assert checked beginConfigStore(), wrapper write, commit-result propagation and readiness invalidation on failed commit.
- config_persistence_write_result_lab_harness.py: model beginChecked(), configEeprom.put(), and commit(); inject begin failure, commit failure, successful commit and ready-state reuse.
- config_persistence_write_result_lab.py: replace obsolete EEPROM mutation anchors with four exact mutations for ignored begin result, skipped begin guard, ignored commit result and retained readiness after failed commit.

This source/test commit changes only those three Hardware-owned lab files. It does not modify production firmware, shared CORE APIs, QA-owned assertions, finance, receipt/disposition, signer, witness or COE.

### Exact-source evidence

- Poll Intake Deny push [run #46128730343](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46128730343), job 140929006378: PASS.
- Poll Intake Deny PR [run #46128734749](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46128734749), job 140929019615: PASS. Log confirms EEPROM begin-failure no-write, commit-failure propagation, successful commit/ready reuse, EEPROM config failure injection 17/17, and existing poll/register deny checks.
- The same job reports CHANGE_LEDGER_APPEND_ONLY_PASS base_bytes=1132798 appended_bytes=59093.
- Native Synthetic [run #46128734730](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46128734730), job 140929019769: FAIL at QA-owned tests/v060_vendo_sequence_contract.py:18; the test requires the literal if(any) return false; corruption guard in the ESP8266 sketch. Hardware did not edit that QA-owned test or add a decoy token.
- Mbed matrix [run #46128734862](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46128734862): source-contract job 140929020220 PASS; ESP32 core 3.3.13 and 4.0.0 target jobs were still running at this checkpoint.
- Pre-sync Full push [run #46128730422](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46128730422): CI-0701 passed; validation job 140929058201 failed the expected handover-freshness check because this source/test commit was newer than the previous canonical checkpoint 3fe9d835e89f3f53de7cedbba40985226186af70. ESP8266, ESP32 and the completed OpenWrt target jobs passed; Android and some target jobs were still running at the checkpoint. Full must be rerun after this documentation sync.
- Full PR run [#46128734722](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46128734722) was still running; its terminal result is not claimed here.

### Process note

The source/test commit was created before the required CURRENT_STATE.md IN PROGRESS entry. This is a sequencing deviation from HANDOVER_POLICY.md. It is recorded explicitly here rather than backdated or concealed; the canonical state and append-only ledger are now being synchronized. No production behavior was changed in this activation.

### Safety and readiness

Host-side failure injection is SIMULATED / CI VERIFIED only. The ESP8266 build at the prior #374 head passed, but this does not establish physical EEPROM/NVS behavior. Physical GPIO/relay behavior, EEPROM/NVS brown-out, LittleFS power loss, 150 power cuts, 30-device/24-hour soak and electrical pulse/recovery remain NOT TESTED. HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO.

**Rollback:** revert/close only child PR #374; preserve parent #373 and earlier stacks.  
**NEXT EXACT ACTION:** complete Mbed and Full exact-head reruns after this documentation checkpoint; ask PHX-QA to correct or explicitly supersede the stale corruption-state assertion on its own branch. Keep coin/relay admission denied.


---

## PHX-HARDWARE UTC08 terminal supersession — checked EEPROM persistence contract (#374)

**Task:** PHX-HW-EEPROM-STORE-TEST-CONTRACT-20261128T09Z  
**PR #374:** OPEN / DRAFT / UNMERGED  
**Branch:** phoenix/hw-eeprom-begin-failclosed-20261128-utc07  
**Source/test SHA:** 3934cf40f1a2999ba66df2fb4e9ff2f0a1081e51  
**Final docs/head checkpoint:** 26ee6b5a1f5b7de024ea04a602d8299812c5c384  
**Terminal CI read:** 2026-11-28T09:10Z

### Final exact-head evidence

- Focused Poll Intake Deny push [#46129051057](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46129051057), job 140929984400: **PASS**.
- Focused Poll Intake Deny PR [#46129056177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46129056177), job 140930000532: **PASS**. The append-only ledger guard reports base 1,132,798 bytes and appended 62,065 bytes. EEPROM wrapper harness logs begin failure/no write, commit failure propagation, commit success/readiness reuse; existing EEPROM failure injection is 17/17 and the EEPROM config write-result lab passes.
- Mbed [#46129056171](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46129056171): **3/3 PASS** — source-contract 140930000947; ESP32 Arduino core 3.3.13 job 140930000945; core 4.0.0 job 140930000750.
- Full [#46129056271](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46129056271): **TERMINAL FAILURE** at validation job 140930061660, QA-owned tests/controllers.sh line 21, literal config_revision presence check. HND-0700 and CI-0701 passed. All **14/14 target/platform builds passed**, including ESP8266, ESP32, Android and OpenWrt targets. Update bundle, simulations, signing and publication were skipped after validation failure.
- Native Synthetic [#46129056215](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46129056215), job 140930001011: **FAIL** at QA-owned tests/v060_vendo_sequence_contract.py line 18, which requires the literal text if(any) return false;. The current ESP8266 loadPending() contains semantic fail-closed handling: when a candidate exists but no valid candidate is chosen, it sets fsReady=false, sets pendingReady=true, preserves the files and returns false. Hardware did not add a decoy literal or edit QA-owned tests. QA should replace the token assertion with a semantic source-linked vector.
- Earlier source-head focused runs #46128730343 and #46128734749 also passed; the docs-head runs above supersede them for final evidence.

### Disposition

The scoped Hardware test-contract change is **CI VERIFIED**. The PR's Full integration remains **BLOCKED** by QA-owned controller parity; Native Synthetic remains **BLOCKED** by the literal pending-state assertion. These failures do not prove physical storage behavior or production acceptance.

The source/test commit changes only the three Hardware-owned persistence lab files. The preceding #374 CheckedEEPROMClass firmware change is compile-validated by the ESP8266 target in Full, but no physical EEPROM/NVS test was performed. No coin or relay admission is enabled.

The prior UTC08 process-sequencing deviation (source/test commit preceded the IN PROGRESS state entry) remains disclosed in the earlier section; it was not backdated or removed.

**HARDWARE ACCEPTED=NO. PRODUCTION READY=NO-GO.**  
**NEXT EXACT ACTION:** PHX-QA updates/supersedes the two assertions on its own branch using source-linked semantic deny-only vectors; PHX-MASTER refreshes #374 in ROLE_ASSIGNMENTS.md and INTEGRATION_MATRIX.md from bdd69c75 to 26ee6b5a. PHX-HARDWARE keeps coin/relay admission denied and does not rebase or merge this stack.
