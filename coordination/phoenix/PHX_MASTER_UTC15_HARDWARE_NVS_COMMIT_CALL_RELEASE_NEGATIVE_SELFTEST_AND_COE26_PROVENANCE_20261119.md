# PHX-MASTER UTC15 — Hardware durability evidence, Release test ownership, and COE #26 provenance

**Date:** 2026-11-19 UTC15  
**Role:** PHX-MASTER — coordination/phoenix, architecture contracts, cross-repository migration provenance.  
**Execution rule:** no Codex app, CLI, API, agent or workflow was used.

## 1. Exact repository refs

| Ref | SHA / state |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Active audit foundation | blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Legacy v0.5.3 development | blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Master branch before this commit | phoenix/master-coordination@7f3ccbc3278c8f86b745bb4c8aecc3b8623da58b |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| Master PR #288 | OPEN/DRAFT, base main@f4e8a891..., pre-run head 7f3ccbc3278c8f86b745bb4c8aecc3b8623da58b |

Control-plane issue #172 and cleanup issue #266 remain OPEN. PR #288 had 104 changed paths before this run, all under coordination/phoenix/. The machine-readable ownership manifest remains blob e4db324315a1b3543fec17a148fbf960170fcb29, status DRAFT_REVIEW_ONLY, with PHX-MASTER destination null.

## 2. Hardware #327 — current exact head and durability evidence boundary

Current PR API head: c4954de95e319f7a2acf4bf4ee0bcae44b4b99b5. Current source/test head: 05ddd64f0d982c32d0297010596bfa9bd46bb472. Base #326: 58c558fb6a237935214621adc3dee65a10fe1a51.

Current exact-head CI:
- Quarantine [#44557974485](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44557974485): SUCCESS.
- Relay/output [#44557974378](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44557974378): SUCCESS.
- Full [#44557974541](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44557974541): FAILURE in validation at inherited QA-owned “Missing poll signature check”. All 13 firmware/platform jobs and Android completed PASS; downstream simulations, update bundle, signing and publishing were skipped.

The current PR contains the test-first EEPROM layout-guard dedup: RED [#44557366459](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44557366459), GREEN quarantine [#44557545656](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44557545656), and relay [#44557545748](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44557545748). The current API head is four commits ahead of the earlier Hardware UTC15 issue checkpoint #7013726241, which still names 92f8f3b; the owner should refresh that existing checkpoint in place.

The earlier NVS/EEPROM commit-call guard uses lab blob 2562cdb84135b3e9dab6e531567c6b1619eeeed3. It asserts exactly one backup commit per board and rejects an ESP32 source mutation that omits nvs_commit() (exit 61); a premature-durability mutation remains rejected (exit 60). Focused runs [#44555100182](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44555100182) and [#44555100184](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44555100184) passed for that checkpoint. This is a host-lab call-site guard only. Same-handle fake readback can observe pending bytes; NVS/EEPROM and LittleFS share physical flash; no independent anti-rollback witness or physical power-fail durability is established.

Current source code on both boards has acceptPollResponse() and coinPostDispositionVerified() returning false. Do not add fake signature strings or enable positive unauthenticated admission. PHX-QA owns the legacy positive fixture; PHX-HARDWARE owns firmware.

## 3. RELEASE #291 — exact head and PISONET-owned test defect

Current PR API/docs head: 97d500445d7a9bb6b3cf4b968b27e8dd9e046967. Exact source/test head from the RELEASE UTC15 checkpoint: 60325634e8359e22c7708403632244d3e876ef0b.

Current-head runs:
- BlazePwifi [#44555775939](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44555775939): SUCCESS.
- ESP32 compatibility [#44555775998](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44555775998): SUCCESS.
- Windows [#44555775954](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44555775954): FAILURE in RELEASE-SIGN negative controls; publisher skipped.

The failing PISONET-owned file is experiment/windows/BlazePisonet-SoftTimer/tests/ReleaseSigning/negative-selftest.ps1, blob 8b69174bf519154e43f7e12e4a9fa2c0e75d350f. It assigns $workflow at line 37 but reads $buildWorkflow at line 115 without assigning it. PISONET owns this path; Master and RELEASE did not modify it. PISONET must correct and test its own file, then RELEASE reruns #291. Keep #291 OPEN/DRAFT/UNMERGED and keep signing/publishing skipped.

## 4. COE #35/#44 site ULA state

COE #35 current docs head 0e3662b9aef4b2a2248e3a064b07d07e9097be1b, source/test 90ce4200b66ce0b55f40feaab42cc7b53fad1f2d. Its packager sets APPROVED_SITE_ULA_PREFIX=None and validates an explicit RFC 4193 /48. Exact-head shared run [#44543625272](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44543625272) passed 116 packager/tool tests (two skips), then correctly failed closed on all 10 appliance profiles because no approved site prefix exists. Case-collision [#44543625541](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44543625541) passed. Sandbox [#44543625389](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44543625389) passed 14/14 host preflight checks then failed because Bubblewrap is not installed (exit 125).

COE #44 head 582fd5d5e83e36b36546ac28534740298ba94af4 is diverged 15 ahead / 29 behind #35 and non-mergeable. It generates/persists a random Global ID per appliance installation, not one shared prefix for all appliances at a site. It is not the §6.45 site authority. CORE/COE owner must decide the durable site-prefix authority; RELEASE implements only that approved input; QA independently verifies same-site sharing, different-site separation and restore.

## 5. COE #26 exact source/destination provenance

Destination PR #26 remains OPEN/DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12. Five workflows are queued with zero jobs: case-collision, Windows SoftTimer, Hardware/shared, Rental and Pisowifi.

| Board | Experiments #327 source | COE #26 destination |
|---|---|---|
| ESP32 | 528187f68aaad7d76a690bbf1cbe338165ad3839, 64,308 bytes | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422, 18,505 bytes |
| ESP8266 | 5c473693a7ca1e865167217d00af90fc7645b44c, 68,018 bytes | c8be98f72596681e36a3ad1f8939bf8046c96887, 18,394 bytes |

Both sketch pairs differ. Source contains 22 board-local Python *_lab.py files, plus one shared helper and one RED fixture. COE Hardware contains one generic shell test, blob f921c56cecc19cab1989507b9b4ade1f45dac54e. It requires positive response_sig, |register| and |poll| source markers, conflicting with current source deny-only behavior.

Source BlazePwifi/LICENSE and destination Pisowifi/LICENSE match at blob 1ee55b94183417be977ca287cd7391f9a6f7e721. Source BlazePwifi/NOTICE.md is absent; destination Hardware/LICENSE and Hardware/NOTICE.md are absent. The Pisowifi license does not establish Hardware license/NOTICE scope. Destination hardware-ci.yml blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793 installs unversioned ESP8266/ESP32 cores. Pins and CI from COE #35 do not transfer to #26.

**Decision:** no copy, move, overwrite, staging, rebase, cherry-pick, merge or route promotion. Keep OWNERSHIP_ROUTES.json unchanged and PHX-MASTER target null.

## 6. Governance, execution and next owners

- Experiments and COE rulesets endpoints returned empty arrays; classic main branch-protection reads returned 403 for both repositories. Effective protection remains UNKNOWN; repository administrator must verify it.
- Experiments AGENTS.md blob d8777e3b58efc41caa5aa3c969c932aee9103d5f requires canonical private registry/manifest/ledger review before archive work. COE root AGENTS.md returns 404.
- Library search found only older registry v7 and earlier. Canonical private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not available through the current Library/connector surface; no older snapshot was substituted. No Google Drive connector was exposed. No private registry content was published.
- Direct shallow Git clone failed because the runtime could not resolve github.com. Master Python suite NOT RUN; no Master Actions run was returned.
- CORE #252, RENTAL #289, PISONET #255 and QA #290 have scoped CI passes only. QA #292 has no current-head run.

Next owner actions: QA replaces the positive poll fixture; PISONET fixes the uninitialized $buildWorkflow test variable; Hardware refreshes its stale role checkpoint; RELEASE reruns #291 after PISONET's correction; CORE/COE selects the site ULA authority; COE integration completes exact per-file provenance/licensing/test import and executable pinned CI; repository administrator verifies protections; registry custodian restores authorized v11 access.

**PRODUCTION NO-GO:** independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible financial migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.
