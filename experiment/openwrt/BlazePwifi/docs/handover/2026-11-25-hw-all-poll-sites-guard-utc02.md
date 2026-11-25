# PHX-HARDWARE UTC02 — all synchronous poll sites remain inside the deny bracket

**Date:** 2026-11-25  
**Role:** PHX-HARDWARE  
**Task:** P0 #177 mitigation regression hardening, Hardware-owned PR #340  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#340 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/340)  
**Branch:** `phoenix/hardware-prepoll-intake-deny-20261122-utc01`  
**Source/test HEAD:** `11531195a522048b9a4285768b35f7313533fa12`

## Scope and ownership

This continuation changed only the Hardware-owned host/source-extracted regression lab:

`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_preflight_inhibit_lab.py`

No production `.ino`, shared CORE API, finance, relay policy, quarantine journal, witness, migration, COE source, QA-owned extractor, or Release file changed. Issue #177 is a PHX-L-VERIFY P0 tracker; this work stayed on the already assigned Hardware-owned PR #340 and did not take over L-VERIFY-owned files.

## Defect and correction

The existing parser found only the first `post("poll")` inside the bounded Wi-Fi poll block. A second synchronous poll request inserted after that block, before coin sampling, escaped the guard.

Test-first history:

- **RED test commit:** `a2cb61cd322e8dca287fd9d3c585ad2e400fdfef`.
- Poll Preflight RED [#45529228739](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45529228739), job `138920086934`: failed exactly because the unguarded second-poll mutation was not rejected.
- Quarantine RED [#45529228795](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45529228795), job `138920086973`: same regression failure; unrelated quarantine/readback and journal labs passed.
- **Intermediate parser attempt:** `c2887652b774f8d4a9677198f078867c5facb0e0`. It checked every call inside the bounded block but still missed the injected call outside that block. Poll Preflight #45529364508 and Quarantine #45529364569 correctly remained red. This intermediate failure was not reported as a fix.
- **Final correction:** `11531195a522048b9a4285768b35f7313533fa12`. The parser now compares all loop-level poll request occurrences with those inside the bounded block, rejects any poll outside that block, and checks a deny-before / deny-after pair for every request in the block. The existing ordering check also keeps coin sampling after the final poll.

The failure injection is source-extracted/static host simulation, not execution of the real timed loop on a device.

## Final exact-source evidence — SHA `11531195a522048b9a4285768b35f7313533fa12`

| Workflow | Exact run / job | Result |
|---|---|---|
| Poll Preflight | [#45529529785](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45529529785), `138921095340` | PASS |
| Quarantine Append Readback | [#45529529755](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45529529755), `138921095215` | PASS |
| ESP32 Mbed TLS SHA256 guard | [#45529529834](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45529529834), `138921095496` | PASS |
| ESP8266 Arduino core 3.1.2 compile | [#45529529815](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45529529815), `138921096148` | PASS |
| ESP8266 push compile | [#45529524020](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45529524020), `138921076394` | PASS |
| ESP32 Arduino core 3.3.13 compile | [#45529529835](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45529529835), `138921279161` | PASS |

The Poll Preflight log prints guard PASS, existing deny mutation rejection, and pre-poll-order mutation rejection for **both ESP8266 and ESP32**. It also explicitly records `PHYSICAL_COIN_RELAY_ACCEPTANCE=0` and `PHYSICAL_POWER_CUT_ACCEPTANCE=0`.

Pinned compile evidence:

- ESP8266 `esp8266:esp8266@3.1.2`, FQBN `esp8266:esp8266:nodemcuv2`; binary SHA-256 `e4af65d3070a061827f9c4c03470687bfe9aa4998c85f5f5a22764d6ec7d3e81`. RAM 31,368/80,192 (39%); IRAM+cache report 60,535/65,536 (92%); flash 313,872/1,048,576 (29%).
- ESP32 `esp32:esp32@3.3.13`, FQBN `esp32:esp32:esp32`; binary SHA-256 `0ad9b926d6f2b2140746fc25c91f1cc734fee73013128da566988d14c03c3808`. Program storage 1,028,940/1,310,720 (78%); global variables 49,456/327,680 (15%).

These are CI builds of the existing sketches; this task did not modify their runtime source or flash any device.

## Full build / simulation status at final check

[BlazePwifi build #45529524001](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45529524001) is still **IN PROGRESS** at the last check. Validation, all 14 firmware/platform targets, Android build, browser simulation, ESP8266/ESP32 simulations, Orange Pi simulations, Ruijie simulation, and update bundle were successful. Only `v04_android_emulator` remained in progress; the x86 simulation had completed successfully. Production APK import, prerelease, production signing handoff and publication were skipped. No overall Full-workflow success is claimed until the run is terminal.

## Live stack and blockers

- #340 remains OPEN / DRAFT / UNMERGED. No rebase, retarget, merge or force-push.
- Direct parent branch ref `cleanup/esp-firmware-hardening-and-quarantine-20261111` resolved to `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`; the PR API still reports base SHA `88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d`. This snapshot discrepancy is left for MASTER to reconcile.
- #239 Phase A deny remains open/draft; #254 ControllerAuthV1Lab remains open/draft; #283 parallel sketches remain open/draft. None was edited.
- #177 remains OPEN / P0; #266 cleanup-first remains OPEN / 0-of-7.
- Safety #34, financial #31/#32, and witness #43 remain OPEN. No financial, replay, signer, witness or migration authority was changed.
- CORE still owns the canonical authenticated register/poll and event-bound receipt contract; QA owns independent contract/assertion reconciliation. Keep coin admission and relay enable deny-default.
- Experiments main remains `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; COE main remains `a6513ab4412b4c014eee2863e45cbe32d06cb243`. COE #26 remains frozen; no COE source was touched.
- The private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not retrievable: no Google Drive file connector was exposed, and exact-title Library search/list did not return the file. No older registry was substituted.

## Status and next action

**CI VERIFIED:** focused source-extracted deny/guard labs and pinned ESP8266/ESP32 compile jobs at the exact source/test SHA.  
**SIMULATED:** poll mutation and deny-path tests only.  
**NOT TESTED:** local independent execution, physical coin pulse, relay contacts/electrical recovery, LittleFS power-loss durability, 150 power cuts, 30-device 24-hour soak.  
**HARDWARE ACCEPTED:** NO.  
**PRODUCTION READY:** NO-GO.

**Next exact action:** MASTER reconciles #340's parent/base snapshot and stack order; CORE publishes the approved authenticated poll/receipt contract; QA independently reviews the fail-closed vectors. PHX-HARDWARE revalidates live heads on the next activation before selecting another unblocked Hardware-owned task.

No Codex, live money, device reset/flash, customer data, production migration, signer provisioning, release tag, merge or deployment.
