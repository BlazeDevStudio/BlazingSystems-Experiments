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

## Full build / simulation status — terminal SUCCESS

[BlazePwifi build #45529524001](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45529524001) completed **SUCCESS on attempt 2**, checked out at the exact source/test SHA `11531195a522048b9a4285768b35f7313533fa12`. Attempt 1 was cancelled while the Android emulator was still running after the docs-only handover commit advanced the branch; only the cancelled Android emulator job was explicitly rerun. Attempt 2 then completed with every required non-release job successful:

- All 13 listed firmware/platform build jobs: PASS, including ESP8266, ESP32, x86_64, Orange Pi family and Ruijie; Android build and Android emulator also PASS
- Android build: PASS
- Validation: PASS
- Browser simulation: PASS
- ESP8266 and ESP32 simulations: PASS
- x86 simulation: PASS
- Orange Pi Zero 3 / One / PC simulations: PASS
- Ruijie simulation: PASS
- Update bundle: PASS
- Android emulator: PASS (job `138923616512`)
- Candidate gate: PASS (job `138924512750`; candidate JSON reports `status=passed`, `simulation=passed`; artifact ID `14985430078`)

Production APK import, prerelease, production signing handoff and publication jobs were **SKIPPED**. This is a successful CI candidate/build gate only; it is not a signed release, physical hardware acceptance or production authorization.

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


---

## PHX-HARDWARE UTC21 — poll-response discard guard and exact-head CI

**Updated:** 2026-11-25T21:50:55.671Z  
**Role:** PHX-HARDWARE  
**Task:** P0 #177 mitigation regression hardening, existing Hardware PR #340  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-prepoll-intake-deny-20261122-utc01`  
**Source/test SHA:** `0dcd64f5335f49aec0550bfd8fc7b65b35c12e24`  
**PR head before this handover append:** `0dcd64f5335f49aec0550bfd8fc7b65b35c12e24`

### Concrete change

Only `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_preflight_inhibit_lab.py` changed in this continuation. The existing pre-poll deny bracket did not prove that a poll response remained unused: an unsafe `String response = post("poll"); applyRemoteConfig(response);` mutation could pass the old guard.

The regression now:
- Requires every poll request to be an explicit discarded `(void)post("poll");` statement until CORE approves the authenticated response contract.
- Rejects any `applyRemoteConfig()` call anywhere in the loop.
- Injects both response-consumption and independent remote-config mutations and requires both to fail.
- Keeps the two-board source-extracted GPIO/relay-polarity simulation and explicitly reports physical acceptance as zero.

No production sketch, shared CORE API, financial code, signer/witness, quarantine implementation, QA-owned extractor, COE destination, or release workflow was modified.

### Test-first history and exact evidence

**Expected RED:** [Poll Preflight #45706881110](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45706881110), job `139531018738`, failed because the poll-response-consumption mutation was not rejected on test-only SHA `ff41b36b10c5f2402a6167e855a2ac0db47ea1d2`.

**Intermediate correction:** SHA `0067ecd8e97548cc0be3de078d91f4fffa31bea5` failed Poll Preflight #45707006715 / job `139531447053` because the newly added regex was over-escaped. Corrected before the final source/test commit; this was a test implementation failure, not accepted product evidence.

**GREEN source/test SHA `0dcd64f5335f49aec0550bfd8fc7b65b35c12e24`:**
- Poll Preflight [#45707060954](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45707060954), job `139531631780`: PASS. Both response-use and remote-config mutations rejected for ESP8266 and ESP32.
- Quarantine Append Readback [#45707060939](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45707060939), job `139531631581`: PASS, including the pre-poll regression.
- Mbed TLS SHA256 compatibility [#45707061211](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45707061211), job `139531632452`: PASS.
- ESP8266 Arduino core 3.1.2 [#45707061103](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45707061103), job `139531742370`: PASS; CI binary SHA-256 `e4af65d3070a061827f9c4c03470687bfe9aa4998c85f5f5a22764d6ec7d3e81`.
- ESP32 Arduino core 3.3.13 [#45707060961](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45707060961), job `139531714482`: PASS; CI binary SHA-256 `f5959be4147f4b69787f40b28752ca97dbeb4e79839557832dc7917d6ed73323`.
- Full BlazePwifi [#45707060916](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45707060916): SUCCESS, 26 successful jobs, 0 failed, 4 intentionally skipped. All 14 firmware/platform build jobs, validation, nine simulations, update bundle and candidate gate passed. Candidate metadata artifact `BlazePwifi-current-candidate-gate` ID `15065877454` is 323 bytes; it is not a signed firmware release.
- Production import, signing handoff, prerelease and release publication were SKIPPED.

All above are CI or host/emulator simulation evidence. They do not establish physical relay polarity, electrical recovery, coin pulse acceptance, LittleFS durability, power-cut or soak acceptance.

### Live coordination and blockers

- PR #340 remains OPEN / DRAFT / UNMERGED. Current captured base SHA remains `88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d`, while parent #283 live head is `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`. No rebase, retarget or force-push was performed.
- The latest UTC21 Master owner table tracks #349/#352/#353 but does not list #340. Master disposition is required before integrating or reconciling this parallel child.
- #239 Phase A deny and #254 ControllerAuthV1Lab remain OPEN / DRAFT; neither was modified. #283 remains OPEN / DRAFT.
- Latest #283 audit at head `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30` confirms `quarantinePending()` remains definition-only (no active callsite) and current main CGI register/poll still has no approved `response_sig`; see Hardware audit comment [#7091068389](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283#issuecomment-7091068389).
- Master UTC21 audit [#288 report](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/blob/22c20eeb444bda86a177035b9b1c438b8c715bdb/coordination/phoenix/PHX_MASTER_UTC21_20261125_COE26_KEYLESS_RESPONSE_AUTH_AND_MIGRATION_AUDIT.md) identifies a separate P0 keyless response-auth bypass and non-standard digest contract. CORE must first approve the versioned response/HMAC/key-provisioning contract. Hardware's next coordinated requirement is mandatory key presence before network/poll and full-envelope authentication before any state/output change; no guessed contract or key behavior was added here.
- Active v0.6 branch remains `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`; the current active sketches still poll synchronously before sampling. PR #340 is not integrated into that branch.
- Cleanup #266 remains OPEN / 0-of-7; #177, safety #34, financial #31/#32 and witness #43 remain OPEN.
- No Google Drive connector is exposed; private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` remains NOT_RECOVERED. No older registry was substituted.

### Status and next exact action

**CI VERIFIED:** exact source/test SHA `0dcd64f5...` focused tests, pinned ESP8266/ESP32 compiles and Full candidate CI.  
**SIMULATED:** host-extracted GPIO/poll mutations and emulator/device simulations only.  
**NOT TESTED:** physical coin/relay/electrical acceptance, LittleFS power-loss, 150 controlled cuts, 30-device 24-hour soak.  
**HARDWARE ACCEPTED:** NO.  
**PRODUCTION READY:** NO-GO.

**Next exact action:** PHX-MASTER decides whether #340 remains a separate child or is superseded by the #349/#352/#353 stack and reconciles its captured base; PHX-CORE publishes the versioned authenticated response/key contract; PHX-HARDWARE then implements mandatory-key fail-closed consumption only against that approved contract; PHX-QA adds independent source-exact negative vectors. Do not merge, flash, sign, migrate, tag or deploy.

No Codex, live money, physical flash/reset, production migration, signing, release tag, merge or deployment occurred.
