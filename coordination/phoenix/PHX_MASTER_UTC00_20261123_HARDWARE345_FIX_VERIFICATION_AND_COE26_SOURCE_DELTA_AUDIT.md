# PHX-MASTER UTC00 — Hardware #345 current-head verification and COE #26 exact-tree delta audit

**Checkpoint:** 2026-11-23T00:59Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Mode:** strict NO CODEX; coordination/phoenix only  
**Disposition:** Hardware #345 focused Quarantine/Relay PASS, Full FAIL at the inherited QA parity assertion; COE #26 remains FROZEN; PRODUCTION NO-GO.

## 1. Exact refs and ownership

| Ref | Exact value | Disposition |
|---|---|---|
| Experiments default | `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b` | unchanged base |
| Experiments development | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` | owner development branch |
| PHX-MASTER before final refresh | `ab9e16a6ef357efdadcb82f257b52004b4e49491` | existing Master branch |
| Master PR #288 | OPEN / DRAFT / UNMERGED | existing draft reused |
| Hardware PR #345 | `01916c89ae6718d3991c778b676d06718155d6a2` | OPEN / DRAFT / UNMERGED; child of #343 |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` | three-entry scaffold |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | OPEN / DRAFT / FROZEN; 286-entry candidate |

The ownership manifest remains `coordination/phoenix/OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29`: 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER target `null`. No route promotion, source ownership transfer, or destination write is authorized.

## 2. Hardware #345 — current implementation and test expansion

PR #345 remains OPEN / DRAFT / UNMERGED, based on exact #343 parent `dfeff7d5f63e699de7bc296c7641f2493f1e0e13`. Current PR/docs HEAD is `01916c89ae6718d3991c778b676d06718155d6a2`; latest source/test SHA is `6eb3e9ba82fdbdcfe4fb6dc8ab1c38c9ffdc3043`.

Six Hardware-owned paths changed in the current PR:
- ESP8266 sketch blob `203db2f8394a5466517845d964195f8d6f25752f`.
- ESP32 sketch blob `2a5bad5904a1f6afabdcac95e762482975ebd886`.
- Host-lab runner blob `b115820c841888ded9d9ee522f6da566e29cc338`.
- Fixture-export module blob `abcb47af17a305680a831d7fbffd66569aebfc78`.
- Scenario fixture blob `0ecee6d19dc5e205e86073b120ceccd03463d053`.
- Hardware handover blob `7889799ca5dd733def606352f174ae0bd6b648e6`.

Both sketches gate sampled coin ingress on `controllerEnabled && coinEnabled && relayEnabled`. An edge while any configured gate is OFF enters the sticky poll-fault path, deasserts outputs before persistence, clears insertion mode/target, preserves any existing pending identity, and creates no new pending credit. Temporary poll-time relay suspension remains distinct because `relayEnabled` stays true while `pollIntakeSuspended` temporarily deasserts the physical output.

### Host-lab coverage

- Six disabled-gate cases per board: controller OFF, coin OFF and relay OFF, each with and without an ISR sequence.
- Six pending-identity preservation cases per board: seed a two-pulse pending batch with target/nonce, then observe a disabled-gate edge with/without ISR sequence. Each case checks unchanged pending count/target/nonce, `pendingReady` set for reconciliation, no POST/save, sticky fault `pulses=3`, and relay/LED/insertion OFF.
- Two mutation controls reject removing the pendingReady preservation assignment and clearing pending target/nonce inside the fault helper.

Source commits: test-first RED `834738d2e82b6857779935b988c4046cbcb6c89f`; ESP8266 correction `911543b8c09044944803d3cee09ddc062b1c191a`; ESP32 correction `ccf2ed3b45d8b1b3b7d634ba4f1c32a054b23863`; initial test pin `587f82b80d546a5b6c027e33ede9caa7fef24ba7`; latest source/test pin `6eb3e9ba82fdbdcfe4fb6dc8ab1c38c9ffdc3043`.

### Exact-source CI

| Gate | Run / exact head | Result |
|---|---|---|
| Initial disabled-ingress Quarantine | [#45084968734](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45084968734), `587f82b8...` | PASS; six cases per board |
| Pending-identity Quarantine | [#45090899038](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45090899038), `6eb3e9ba...` | PASS; six cases per board; both mutations rejected |
| Pending-identity Relay/output | [#45090899225](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45090899225), `6eb3e9ba...` | PASS |
| Pending-identity Full | [#45090899167](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45090899167), `6eb3e9ba...` | FAIL at inherited QA-owned `Missing poll signature check`; all 14 target/platform jobs pass; downstream skipped |
| Current-head Relay/output | [#45091417060](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45091417060), `01916c89ae6718d3991c778b676d06718155d6a2` | PASS |
| Current-head Quarantine | [#45091417124](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45091417124), `01916c89ae6718d3991c778b676d06718155d6a2` | PASS; six pending-identity cases per board; both mutations rejected |
| Current-head Full | [#45091417147](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45091417147), `01916c89ae6718d3991c778b676d06718155d6a2` | FAIL at `Controller protocol parity` / inherited `Missing poll signature check` |

At current-head Full, validation job `137421604329` fails step 8 `Controller protocol parity`. All 14 target/platform jobs (13 firmware targets plus Android) completed SUCCESS. Downstream simulations, update bundle, candidate gate, signing and publication were skipped. Focused CI is not physical acceptance; HARDWARE ACCEPTED NO.

**Durability boundary:** `latchPollPulseFault()` attempts secondary NVS/EEPROM and LittleFS markers and reports partial/dual-store failures. The host tests prove pending identity preservation and no new POST/save, not physical reboot durability. If both stores fail, source explicitly says current-boot fail-closed but reboot durability is NOT established. Independent QA must verify both stores, partial/dual-store failure and reboot recovery before any durability claim.

**Ownership:** HARDWARE owns both sketches, host fixtures/runner and handover. QA owns the inherited parity assertion and independent negative/default-deny review. MASTER owns only the cross-role contract and integration record. Do not add a positive legacy poll signature to firmware.

## 3. Current owner CI snapshot

| Owner / candidate | Exact head | Current CI evidence |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) Build PASS; CORE source untouched by Master |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) APK identity PASS; [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) API21/API23 PASS; [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) build FAIL |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) Windows PASS |
| HARDWARE #283 | `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30` | [#45057637178](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45057637178) Quarantine PASS; [#45057637196](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45057637196) Full FAIL |
| HARDWARE #343 | `dfeff7d5f63e699de7bc296c7641f2493f1e0e13` | [#45062595339](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062595339) Quarantine PASS; [#45062595335](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062595335) Relay PASS; [#45062595995](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062595995) Full FAIL |
| HARDWARE #344 | `3bfa530c94a929191d7b3335c085dbd7f99e1e18` | [#45080942944](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45080942944) Quarantine PASS; [#45080942789](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45080942789) Full FAIL |
| HARDWARE #345 | `01916c89ae6718d3991c778b676d06718155d6a2` | current-head Quarantine + Relay PASS; Full FAIL at inherited QA parity |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) Windows PASS; native COM lab not demonstrated by this workflow |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No workflow runs returned |
| RELEASE #291 | `1e0e58aa3b518d85382106d684c0ab4b23fd334a` | [#45088729284](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45088729284) Windows FAIL; [#45088729330](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45088729330) Full FAIL; [#45088729327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45088729327) ESP32 compatibility PASS |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows QUEUED, zero jobs |
| COE RELEASE #35 | `16c0e140cbfd52d4cb572b7121189866763c77b2` | [#45082913966](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45082913966) case guard PASS; [#45082913844](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45082913844) shared validation FAIL closed; [#45082913881](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45082913881) sandbox FAIL |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) overlay/shell PASS; [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) case guard PASS |
| COE Stage 5.1 #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) stage PASS; [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) case guard PASS; [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) shared ESP32 build FAIL |

RENTAL #328 and COE #49 retain the missing `mbedtls/sha256.h` / toolchain compatibility issue. RELEASE #291 remains blocked by handover freshness. COE #35 remains blocked by site-scoped ULA /48 authority and unavailable Bubblewrap. CORE implementation remains with its separate owner; no CORE source work was started.

## 4. COE #26 exact migration gate — still frozen

COE main remains a three-entry scaffold; #26 is a separate 286-entry draft candidate. Current source and destination recursive trees are non-truncated.

| Item | Experiments #345 source | COE #26 destination | Result |
|---|---|---|---|
| ESP32 sketch | `2a5bad5904a1f6afabdcac95e762482975ebd886` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | DIFFERENT |
| ESP8266 sketch | `203db2f8394a5466517845d964195f8d6f25752f` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | DIFFERENT |
| Disabled-ingress / pending-identity host fixtures | source runner/fixture blobs above | no corresponding Hardware Python paths | ABSENT |

Source has 34 board-local Python helpers; COE #26 has zero corresponding Hardware Python helpers. The source hardening test and destination hardening test remain different identities.

**PisoWiFi intake:** schema 8 has 61 runtime rows; destination blobs match the intake map 61/61. Actual status counts are 46 byte-identical / 15 derived while the summary says 47 / 14. Against current Experiments main `f4e8a891...`, historical source pins classify 33 unchanged / 20 changed / 8 absent. PisoWiFi LICENSE matches at `1ee55b94183417be977ca287cd7391f9a6f7e721`; source root NOTICE exists, COE root NOTICE is absent, and Hardware-local LICENSE/NOTICE are absent.

**Decision:** #26 remains FROZEN. No staging, copy, move, overwrite, rebase, cherry-pick, route promotion or destination edit.

## 5. Governance and execution limits

- Cleanup #266 remains OPEN; the MASTER cleanup checkbox is still unchecked. The cross-owner inventory is partial.
- Experiments main/development branch metadata reports `protected=false`; rulesets return empty, while classic branch-protection detail is 403 through this integration. Effective policy needs administrator verification; Master branch protection is not independently verified.
- Canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not surfaced. Library search found older v3–v7 snapshots and a 2026-11-09 checkpoint summary referencing v11, not the canonical registry. No substitute was used and no private contents/IDs were published; no Google Drive connector is exposed.
- The active automation index exposed separate Hardware and Release continuations; CORE source work was not started and remains reserved to its separate owner.
- Master PR #288 has no PR-triggered workflow runs or combined statuses. Full Master unittest discovery and `verify_coordination.py` are NOT RUN. Local `git ls-remote` failed because this runtime could not resolve `github.com`; GitHub API reads succeeded.
- Static tree, blob, intake-count, route and index checks were executed in-memory; these are not the full Python Master suite.

## 6. Next exact actions

1. PHX-QA: replace/reconcile the inherited `Controller protocol parity` / `Missing poll signature check` assertion against the current deny-only producer; do not add a positive legacy signature to firmware.
2. PHX-QA + PHX-HARDWARE: independently review both board sources, disabled-gate and pending-identity cases, both fault stores, partial/dual-store failure and reboot durability boundaries.
3. PHX-RENTAL/CORE owners: resolve Mbed TLS/toolchain and handover freshness on their own branches.
4. PHX-RELEASE: refresh handover and rerun Windows/Full at exact current #291 head.
5. COE integration owner: reconcile the 61-row intake discrepancy, current source drift, missing helpers/tests, firmware/test identities and NOTICE/license scope before any staging review.
6. Repository administrators: verify effective branch protection and required checks.
7. Registry custodian: restore authorized v11/newer-correction access; Master test runner: execute the full Master suite in an authenticated checkout.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory. No merge, release, signing, secret provisioning, hardware flashing, real-payment operation, financial migration or physical hardware test was performed.
