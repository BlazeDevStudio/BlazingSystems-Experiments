# PHX-MASTER UTC04 — live owner/CI and exact COE #26 source-intake reconciliation

**Audit time:** 2026-11-23T04:41:02Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Execution:** Strict NO CODEX. Connected GitHub and ordinary read-only tree/provenance checks; no Codex app, CLI, API, agent, workflow or delegation.  
**Scope:** `coordination/phoenix/`, architecture/interface contracts, owner routing, cross-repository provenance and integration matrix only.

## 1. Exact repository and branch state

| Ref | Exact SHA / state |
|---|---|
| Experiments default branch `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments development `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master branch `phoenix/master-coordination` | starting HEAD `e3e1f642d5a4129f81300ce927c0c78ce250b7c4` |
| Experiments PR #288 | OPEN / DRAFT / UNMERGED; base main `f4e8a891...` |
| COE default branch `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE PR #26 | OPEN / DRAFT / UNMERGED; `b382d233ff06c8791b1028bed3c617cc7b670d12` |

Both repositories report default branch `main`. Experiments main/development/Master and COE main branch metadata all report `protected=false`, required-check enforcement `off`, no required contexts; repository rulesets endpoint returns an empty list. This requires repository-administrator action and independent re-read after configuration.

PR #288 has 181 changed paths; the complete PR filename set contains zero paths outside `coordination/phoenix/`. Its exact branch tree contains 181 coordination files and is non-truncated. No PR-triggered Master workflow runs or combined statuses exist.

## 2. Instructions, ownership and control plane re-read

- Master directive: uploaded `00_MASTER_PROJECT_PHOENIX(1).txt`; strict NO CODEX, one role-owned task per activation, exact SHA/CI evidence, no cross-owner source edits.
- `README_FIRST(20261114-191910).md`: seven full-team roles, GitHub as shared mailbox, no claim that issue-signal workflows wake chat workers.
- `COMMUNICATION_PROTOCOL(20261114-191912).md`: BLAZE-COMMS/1 JSON envelope and role/hour deduplication.
- Experiments root `AGENTS.md` SHA `d8777e3b58efc41caa5aa3c969c932aee9103d5f`: restricted Google Drive mirror, private registry/manifest/ledger must be read before new artifacts, no public private Drive IDs, verify artifact readback/hash.
- Live [CONTROL PLANE #172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172): latest PHX-MASTER checkpoint UTC03; no PHX-MASTER UTC04 checkpoint existed before this run.
- Live [cleanup #266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266): OPEN, all seven role boxes unchecked (0/7). The latest Hardware cleanup note is a single test-fidelity increment, not global cleanup completion.
- Current [ownership manifest](OWNERSHIP_ROUTES.json), blob `e4db324315a1b3543fec17a148fbf960170fcb29`: 11 routes, `DRAFT_REVIEW_ONLY`; PHX-MASTER target is null and kind is `coordination-only`. The broad Rental route remains `manual-file-mapping-required`, `copy_permitted=false`.

## 3. Exact owner PR and CI reconciliation

| Owner | Current candidate | Exact-head evidence |
|---|---|---|
| CORE | #252 `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Build [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; scoped CI only. |
| RENTAL | #328 `0e0da62acd47c6a1ce287f8a30fc700d603fa070`; parent #289 `68928774d0d7cf65adb26bc6b54199a3159d066c` | #328 APK identity [44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) and API21/API23 smoke [44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS; build [44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAIL: handover freshness and ESP32 compile missing `mbedtls/sha256.h`. #289 Windows/native runs [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) and [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS. |
| PISONET | #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows synthetic [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; physical COM acceptance NOT TESTED. |
| HARDWARE | #345 docs HEAD `ee1a9fee188942ad0fc21b0f01dda5b343e7b4cc`; source/test SHA `e95b1109141f8c3377aff055946c3fdd78965c73` | Quarantine [45107994891](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45107994891) and Relay [45107994845](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45107994845) PASS; Full [45107994895](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45107994895) FAIL at inherited QA-owned `Missing poll signature check`. All 14/14 target/platform jobs pass; simulations, update bundle, signing and publication skip. |
| HARDWARE parallel lines | #343 `dfeff7d5f63e699de7bc296c7641f2493f1e0e13`; #344 `3bfa530c94a929191d7b3335c085dbd7f99e1e18`; #283 `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`; #254 `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`; #239 `d83b715b116185107737fef721c2eece8feebf39` | #343 focused Quarantine/Relay PASS, Full FAIL; #344 Quarantine PASS, Full FAIL; #283 Quarantine PASS, build FAIL; #254 header PASS, build FAIL; #239 synthetic journal and build PASS. Preserve ancestry: #345 → #343 → #342 (`e7815297b1a8780b7868bc9b28f45011ec419dce`); #344 → #341 (`4368435ad762d507a907e72a9c739c7bddbc3a81`). |
| QA | #290 `5c29d15994cee1279058f1eca12f2a3180704292`; #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96`; #267 `ff5367990c2d27b8ebbb822ee208251af0c890e2` | #290 Windows [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; #292 no runs; #267 parallel-lab workflow [41452247439](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/41452247439) PASS. #264 and #279 no current-head runs. |
| RELEASE | #291 `ed73974472b5162e7d283211b3bb7ab8e208380e` | ESP32 compatibility [45111939876](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45111939876) PASS; Windows [45111939904](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45111939904) and Full build [45111939890](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45111939890) FAIL at CORE-owned handover freshness. Target builds/Android pass; downstream simulations/publisher/signing skip. |
| COE candidate | #26 `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows queued / zero jobs. #35 case guard PASS but shared/sandbox FAIL; #45 overlay + case guard PASS; #49 INTERCON + case guard PASS but Hardware/Shared FAIL. |

The current #345 test fixture stores opaque fake `/pending.dat` bytes and verifies byte preservation plus a deletion mutation on both extracted board sources. It is host FakeLittleFS evidence, not serialized PendingRecord validation, real LittleFS durability, power-cut proof or physical acceptance. Do not synthesize `response_sig` or weaken QA's assertion to make Full green.

RELEASE #291's exact logs show the CORE handover gate detects `PROJECT_HANDOVER.md` older than two source/workflow files; the release-owned compatibility run passes, but Windows and Full stop before publishing. CORE must update its own shared handover; RELEASE owns its workflow and re-run.

## 4. COE #26 destination staging — exact blob, test, import and licence comparison

COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243` is still a three-entry scaffold. PR #26 candidate is a non-truncated 286-entry tree / 205-file PR diff. No destination write was made.

### 4.1 PisoWiFi runtime intake

- Current CORE #252 rootfs source prefix has 61 blobs; COE #26 target prefix has 62.
- Exact current-owner comparison: **45 identical, 16 different, 0 missing, 1 destination-only**. The destination-only path is `Pisowifi/openwrt/rootfs/usr/sbin/blaze-appliance-diag`.
- Different source/destination blobs are at: `etc/init.d/blazepwifi`, `etc/init.d/blazepwifi-remote-admin`, `etc/uci-defaults/99-blazepwifi`, `usr/lib/blazepwifi/auth.sh`, `capabilities.sh`, `common.sh`, `config.sh`, `controller.sh`, `member.sh`, `rental.sh`, `usr/sbin/blazepwifi-core`, `blazepwifi-remote-admin-run`, `blazepwifi-remote-guard`, `www/blazepwifi/cgi-bin/admin`, `api`, and `vendo`.
- COE `Pisowifi/SOURCE_INTAKE.json` blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f`, schema 8, pins historical source commit `6d4c9b487af4d768c4d7627654d119417fcc6e00`; the recorded rootfs tree SHA `f4a923aaacf1374e90c7bab5f335efe6c6ec55cf` and test tree SHA `7e3b16f2a981c1c8ecab3b1da0d34a82b4e44f17` both match the historical commit's actual subtree refs. All 61 historical source blobs and all 61 destination blobs match the intake rows.
- Intake inconsistency: row statuses count **46 byte-identical + 15 derived**, while summary claims **47 + 14**. COE owner must correct the summary in its own branch. Current CORE #252 source is not equivalent to the historical intake pin (45 identical / 16 different against destination).

### 4.2 QA test identity

Experiments main has 38 blobs under `experiment/openwrt/BlazePwifi/tests/`; COE #26 has 19 under `Pisowifi/tests/`. Only one is byte-identical; `config.sh`, `integration.sh`, and `security.sh` differ; 34 source files are absent and 15 destination files are extra/derived. The source and destination test identities therefore cannot be treated as a complete copy or an equivalent test suite.

### 4.3 Other routed components

| Route | Current source vs COE #26 | Exact result |
|---|---|---|
| RENTAL Android (#328) | 991 / 8 blobs | No exact path/blob matches; all 991 source files absent from target route and 8 destination-only. Source contains `BlazeRentalLauncher/LICENSE` and `assets/license.html`; target has no counterparts. |
| RENTAL standalone (#328) | 12 / 4 | 1 different, 11 missing, 3 destination-only. |
| PISONET (#255) | 68 / 47 | 27 identical, 11 different, 30 missing, 9 destination-only. |
| HARDWARE ESP32 (#345) | 16 / 1 | 15 missing, 1 different. |
| HARDWARE ESP8266 (#345) | 30 / 1 | 29 missing, 1 different. |
| RELEASE workflow (#291) | 1 / 1 | Different blobs; route explicitly says reimplementation-review. |

### 4.4 Licence scope

Source `experiment/openwrt/BlazePwifi/LICENSE` and destination `Pisowifi/LICENSE` both have blob `1ee55b94183417be977ca287cd7391f9a6f7e721`. Experiments root `NOTICE.md` exists (blob `f6d92cd21465312be5993631fe26977219be0fb9`); COE root NOTICE is absent. Hardware-local LICENSE/NOTICE files are absent at checked locations. Rental Android's two source license files are not present in the target route. Preserve existing third-party vendor LICENSE/NOTICE files.

**Migration decision:** keep #26 FROZEN. No copy, move, overwrite, cherry-pick, rebase, destination edit or staging proposal. First require owner-authored per-file provenance, current source SHA, license/import map, exact test identity, same-SHA CI, and independent QA approval.

## 5. Master cleanup and execution limits

- Cleanup #266 remains OPEN, **0/7**. Master checklist remains unchecked because the broader duplicate/dead-code and cross-owner path audit is not complete.
- Current Master index audit: 96 `PHX_MASTER_*.md` files and 94 unique links, no duplicates/dangling links; two existing historical reports were unindexed. This update restores both links and adds this UTC04 report; resulting index is rechecked after commit.
- The complete Master unit suite and `verify_coordination.py` were NOT RUN. A normal `git clone --filter=blob:none` of the exact Master branch failed because the execution container could not resolve `github.com`. GitHub tree/blob/PR/CI metadata inspection and the static index/route/migration comparisons did execute; these are not unit-test results.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not surfaced in the Library search; only older v3–v7 registry snapshots appeared. No Google Drive connector is exposed in this runtime. No older snapshot was substituted and no private Drive IDs/content were published.

## 6. Exact next actions and safety disposition

1. PHX-QA reviews #345 at exact docs HEAD `ee1a9fee...` and replaces/reconciles the stale poll-signature assertion against the actual CORE producer contract. Do not weaken default-deny or synthesize a signature.
2. PHX-CORE refreshes its own shared `PROJECT_HANDOVER.md` after current source/workflow changes; RELEASE then reruns its exact-head Windows/Full checks. PHX-MASTER does not edit CORE/RELEASE handover files.
3. COE owner corrects the 47/14 summary to the row-derived 46/15 and documents the historical source pin separately from current CORE #252.
4. Repository administrators configure protected branches/required reviews/checks and verify exact policy readback.
5. Registry custodian supplies authorized access to v11 and newer corrections; human test runner executes the full Master suite at the exact resulting PR #288 commit.

**PRODUCTION NO-GO** remains mandatory until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device 24-hour soak and owner-authorized release gates all have independently verified evidence.

No subsystem source, COE destination, secret, signer, real payment system, hardware device, release or customer state was modified. No merge, migration, flash, physical test or production approval occurred.
