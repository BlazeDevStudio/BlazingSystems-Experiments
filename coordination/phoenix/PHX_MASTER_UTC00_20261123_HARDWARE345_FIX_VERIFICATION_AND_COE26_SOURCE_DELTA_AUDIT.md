# PHX-MASTER UTC00 — Hardware #345 fix verification and COE #26 exact-tree delta audit

**Checkpoint:** 2026-11-23T00:39:22Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Mode:** strict NO CODEX; coordination/phoenix only  
**Disposition:** Master docs updated; Hardware #345 focused gates pass at exact head but Full remains blocked; COE #26 remains FROZEN; PRODUCTION NO-GO.

## 1. Exact refs and ownership

| Ref | Exact value | Disposition |
|---|---|---|
| Experiments default branch | `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b` | unchanged base |
| Experiments development | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` | owner development branch |
| PHX-MASTER | `d1cb7dfe8cac0c491c424a1ea24769be220b98e2` | prior HEAD; new commit follows on same branch |
| Master PR #288 | OPEN / DRAFT / UNMERGED | existing draft reused |
| Hardware PR #345 | `01916c89ae6718d3991c778b676d06718155d6a2` | OPEN / DRAFT / UNMERGED; child of #343 |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` | structure-only tree, 3 entries |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | OPEN / DRAFT / FROZEN; 286-entry candidate tree |

The ownership manifest remains `coordination/phoenix/OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29`: 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER target `null`. No route promotion, source ownership transfer, or destination write is authorized.

## 2. Hardware #345 — corrected implementation verified at current PR head

PR #345 is a four-file child of Hardware #343 (parent `dfeff7d5f63e699de7bc296c7641f2493f1e0e13`). It now contains two sketch corrections, one host fixture update, and one Hardware-owned handover.

- ESP8266 sketch blob: `203db2f8394a5466517845d964195f8d6f25752f`.
- ESP32 sketch blob: `2a5bad5904a1f6afabdcac95e762482975ebd886`.
- Disabled-ingress fixture blob: `103357a14381fbc26240a3910373332f75c2ec83`.
- Handover blob: `690db41c7366cf48e4e6312a5e2948c302971f68`.
- Test-first RED: `834738d2e82b6857779935b988c4046cbcb6c89f`.
- ESP8266 correction: `911543b8c09044944803d3cee09ddc062b1c191a`.
- ESP32 correction: `ccf2ed3b45d8b1b3b7d634ba4f1c32a054b23863`.
- Final source/test pin recorded by Hardware: `587f82b80d546a5b6c027e33ede9caa7fef24ba7`.

Both sketches now use `controllerEnabled && coinEnabled && relayEnabled` as the configured coin-ingress eligibility gate. A sampled active edge while any configured gate is OFF enters the existing sticky poll-fault path, deasserts outputs before persistence, clears insertion mode/target, preserves any pre-existing pending identity, and creates no new pending credit. Temporary poll-time output suspension remains distinct: `relayEnabled` stays true while `pollIntakeSuspended` temporarily deasserts the output.

The shared host fixture exercises controller OFF, coin OFF, and relay OFF with and without an ISR sequence (six cases per extracted board source). It asserts sticky `/pollpulse.fault`, no new pending pulse/save, relay/LED OFF, insertion mode OFF, and cleared target. The workflow explicitly compiles exact ESP32 and ESP8266 quarantine sources with fault-injected fake LittleFS.

**Durability limit:** `latchPollPulseFault()` attempts both secondary NVS/EEPROM and LittleFS markers and logs partial/dual-store failure. The six new disabled-gate assertions check the LittleFS marker and no-save/no-credit state; they do not independently assert both stores for each new case. If both stores fail, the source explicitly says current-boot fail-closed but reboot durability is NOT established. Independent QA must verify both stores and partial/dual failure behavior before any durability claim.

## 3. Exact-head CI at Hardware #345 `01916c89ae6718d3991c778b676d06718155d6a2`

| Gate | Run | Result |
|---|---|---|
| Quarantine Byte Readback LAB | [#45085291729](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45085291729) | PASS; exact head `01916c89ae6718d3991c778b676d06718155d6a2`; job `quarantine-source` |
| Relay Output Polarity LAB | [#45085291635](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45085291635) | PASS; ESP32 boot-polarity and source-output-polarity jobs |
| Full BlazePwifi build | [#45085291816](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45085291816) | FAIL at `Controller protocol parity` / inherited QA-owned `Missing poll signature check` |

The Quarantine job compiles both exact board sketches and verifies pulse capture after poll-drain abort on both. The Full run's ESP32/ESP8266 and configured firmware target jobs plus Android pass, but the validation gate fails; simulations, update bundle, candidate gate, signing and publication are skipped. This is focused CI / simulated evidence only, not physical acceptance.

**Owner routing:** HARDWARE owns both sketch implementations and its fixture/handover. QA owns the inherited protocol-parity assertion and independent negative/default-deny verification. MASTER owns only the cross-role contract and integration record. Do not add a positive legacy poll signature to firmware to make the old assertion green.

## 4. Current owner CI snapshot

| Owner / candidate | Exact head | Current CI evidence |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) Build PASS; CORE source remains with its separate owner |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) APK identity PASS; [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) API21/API23 smoke PASS; [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) build FAIL |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) Windows PASS |
| HARDWARE #283 | `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30` | [#45057637178](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45057637178) Quarantine PASS; [#45057637196](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45057637196) Full FAIL |
| HARDWARE #343 | `dfeff7d5f63e699de7bc296c7641f2493f1e0e13` | [#45062595339](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062595339) Quarantine PASS; [#45062595335](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062595335) Relay PASS; [#45062595995](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062595995) Full FAIL |
| HARDWARE #344 | `3bfa530c94a929191d7b3335c085dbd7f99e1e18` | [#45080942944](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45080942944) Quarantine PASS; [#45080942789](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45080942789) Full FAIL |
| HARDWARE #345 | `01916c89ae6718d3991c778b676d06718155d6a2` | Quarantine + Relay PASS; Full FAIL as above |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) Windows PASS; native COM lab not demonstrated by this workflow |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No workflow runs returned |
| RELEASE #291 | `1e0e58aa3b518d85382106d684c0ab4b23fd334a` | [#45088729284](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45088729284) Windows FAIL; [#45088729330](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45088729330) Full FAIL; [#45088729327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45088729327) ESP32 compatibility PASS |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows QUEUED, zero jobs |
| COE RELEASE #35 | `16c0e140cbfd52d4cb572b7121189866763c77b2` | [#45082913966](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45082913966) case guard PASS; [#45082913844](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45082913844) shared validation FAIL closed; [#45082913881](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45082913881) sandbox FAIL |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) overlay/shell PASS; [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) case guard PASS |
| COE Stage 5.1 #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) stage PASS; [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) case guard PASS; [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) shared ESP32 build FAIL |

RENTAL #328 and COE #49 retain the missing `mbedtls/sha256.h` / toolchain compatibility issue. RELEASE #291 remains blocked by handover freshness. COE #35 remains blocked by site-scoped ULA /48 authority and unavailable Bubblewrap. CORE implementation was not touched.

## 5. COE #26 exact migration gate — still frozen

The COE main branch remains a three-entry scaffold tree; #26 is a separate 286-entry draft candidate. Both source and destination recursive trees were non-truncated.

**Hardware source/destination delta at exact heads:**

| Item | Experiments #345 source blob | COE #26 destination blob | Result |
|---|---|---|---|
| ESP32 sketch | `2a5bad5904a1f6afabdcac95e762482975ebd886` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | DIFFERENT |
| ESP8266 sketch | `203db2f8394a5466517845d964195f8d6f25752f` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | DIFFERENT |
| New disabled-ingress fixture | `103357a14381fbc26240a3910373332f75c2ec83` | no corresponding Hardware path | ABSENT |

The current source tree has 34 board-local Python helpers under ESP32/ESP8266; COE #26 has zero corresponding Hardware Python helpers. The source hardening test and destination hardening test remain different identities. The new #345 firmware correction is not present in the frozen destination.

**PisoWiFi intake revalidation:**

- `Pisowifi/SOURCE_INTAKE.json` schema 8 contains 61 runtime rows.
- All 61 destination blobs match the destination SHAs recorded in the manifest.
- Manifest status counts are 46 `byte_identical` and 15 derived, while the summary claims 47 and 14: one-row discrepancy remains.
- Against current Experiments main `f4e8a891...`, the 61 historical source pins classify as 33 unchanged, 20 changed, and 8 absent.
- Source `experiment/openwrt/BlazePwifi/LICENSE` and destination `Pisowifi/LICENSE` match at `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- Source root `NOTICE.md` exists; COE #26 root NOTICE is absent. Hardware-local LICENSE/NOTICE are absent at destination.

**Decision:** #26 stays FROZEN. No staging, copying, moving, overwriting, rebasing, cherry-picking, route promotion, or destination editing. The historical source pin, 61-row classification discrepancy, 20 changed/8 absent current-source paths, missing helpers, divergent firmware/test identities, and license/NOTICE scope all require owner reconciliation before a staging proposal.

## 6. Governance and execution limits

- Issue #266 remains OPEN; the MASTER cleanup checkbox is still unchecked. The cross-owner inventory is partial, not completion of the broader cleanup track.
- Experiments main/development branch metadata reports `protected=false`; rulesets return an empty list, while classic branch-protection detail is 403 through this integration. Effective required-check enforcement needs administrator verification. The Master branch's effective protection is not independently verified.
- The canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not surfaced. Library search found older v3–v7 snapshots and a 2026-11-09 checkpoint summary that references v11, not the canonical registry. No substitute was used and no private contents/IDs were published. No Google Drive connector is exposed in this run.
- The active automation index exposed separate Hardware and Release continuations; no CORE source work was started. CORE remains reserved to its separately assigned owner.
- Master PR #288 has no PR-triggered workflow runs or combined statuses. Full Master unittest discovery and `verify_coordination.py` are NOT RUN. A local `git ls-remote` attempt failed because this runtime could not resolve `github.com`; GitHub API tree/blob/PR/CI reads did succeed.
- Static tree, blob, intake-count, route, and index checks were executed in-memory; these are not a substitute for the full Python Master suite.

## 7. Next exact actions

1. PHX-QA: reconcile the stale `Controller protocol parity` / `Missing poll signature check` assertion against the current deny-only producer; keep negative/default-deny tests and do not add positive legacy signatures.
2. PHX-QA + PHX-HARDWARE: independently verify both board paths, existing pending-identity preservation, both fault stores, partial/dual-store failure, no new pending credit, and no POST eligibility at the exact #345 head.
3. PHX-RENTAL/CORE owners: resolve Mbed TLS/toolchain and handover freshness on their own branches.
4. PHX-RELEASE: refresh its current handover and re-run Windows/Full at the exact current #291 head.
5. COE integration owner: reconcile the 61-row intake discrepancy, current source drift, missing helper/test imports, firmware/test identities and NOTICE/license scope before any staging review.
6. Repository administrators: verify effective branch protection and required checks.
7. Registry custodian: restore authorized access to v11 and newer corrections; Master test runner: execute the full Master suite in an authenticated checkout.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates remain mandatory. No merge, release, signing, secret provisioning, hardware flashing, real-payment operation, financial migration, or physical hardware test was performed.
