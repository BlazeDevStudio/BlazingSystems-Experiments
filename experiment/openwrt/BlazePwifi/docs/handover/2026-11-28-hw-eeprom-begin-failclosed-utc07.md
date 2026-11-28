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
