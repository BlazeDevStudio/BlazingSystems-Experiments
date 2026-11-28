# PHX-MASTER UTC01 — report-index deduplication and architecture pointer reconciliation

**Checkpoint:** 2026-11-23T01:07:03Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Mode:** strict NO CODEX; coordination/phoenix only  
**Disposition:** Master index repaired and statically revalidated; Hardware #345 focused CI PASS / Full FAIL; COE #26 remains FROZEN; PRODUCTION NO-GO.

## 1. Governing instructions and live refs

- Re-read the uploaded Master directive, latest README_FIRST (2026-11-14 19:19:26), latest COMMUNICATION_PROTOCOL / BLAZE-COMMS/1 (2026-11-14 19:19:25), root AGENTS.md, and current Master coordination documents.
- Control plane #172 remains OPEN; latest prior Master checkpoint is UTC00. Cleanup #266 remains OPEN with 0/7 checkboxes complete.
- Experiments main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Experiments development: blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Master branch at audit start: phoenix/master-coordination@d83ffead4c84921b5ac56ca6edba077e31282d63.
- PR #288: OPEN / DRAFT / UNMERGED; base main@f4e8a891...; 179 changed paths before this update, all under coordination/phoenix/.
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243; exact recursive tree has 3 entries (README.md and Pisonet placeholder).
- COE integration PR #26: b382d233ff06c8791b1028bed3c617cc7b670d12; OPEN / DRAFT / FROZEN; 286-entry tree; five workflows QUEUED and zero jobs.
- OWNERSHIP_ROUTES.json blob: e4db324315a1b3543fec17a148fbf960170fcb29; 11 routes; DRAFT_REVIEW_ONLY; PHX-MASTER destination null.
- Branch objects report protected=false for Experiments main, Experiments development and COE main. Effective branch protection must be verified by repository administrators.

No CORE, RENTAL, PISONET, HARDWARE, QA, RELEASE or COE source branch was modified.

## 2. Proven index inconsistency

The exact Master recursive tree at d83ffead was complete (truncated=false), with 2,521 total entries, 179 paths under coordination/phoenix/, and 94 PHX_MASTER_*.md report files.

The matching INDEX.md blob 64c36213909fd7855595b1361495e2b9a76bcb33 contained:
- 96 report-link occurrences;
- 94 unique report targets;
- two duplicate link occurrences;
- zero dangling targets;
- zero unindexed report files.

The duplicate targets were:
1. PHX_MASTER_UTC20_20261121_EXACT_HEAD_ROLE_CI_COE26_MANIFEST_BASELINE_CANDIDATE_AUDIT.md — linked at the then-current INDEX lines 482 and 492.
2. PHX_MASTER_UTC17_20261121_EXACT_HEAD_ROLE_CI_COE26_SOURCE_MAIN_PROVENANCE_AUDIT.md — linked at lines 446 and 702.

The two reports themselves were not duplicates. Both report files were present and retained. The error was repeated navigation entries, not duplicate source documents.

A second index defect was found: its ARCHITECTURE_CONTRACTS.md summary stopped at §6.69, while the exact current architecture blob 712f0669dc832cb1a82f77331b60ac91d81b1df5 contains the current Hardware #345 gates §6.76–§6.79.

## 3. Reversible correction

INDEX.md was changed only to:
- retain one link for each duplicate target, merging the useful post-commit note into the retained entry;
- update the architecture-contract summary through §6.79;
- update its timestamp;
- add this audit report and the post-update inventory result.

No historical report was deleted, renamed or rewritten. ARCHITECTURE_CONTRACTS.md and all subsystem source files were left unchanged.

## 4. Hardware #345 exact-head evidence

Hardware PR #345 remains OPEN / DRAFT / UNMERGED at 01916c89ae6718d3991c778b676d06718155d6a2, child of #343 at dfeff7d5f63e699de7bc296c7641f2493f1e0e13. Latest source/test SHA: 6eb3e9ba82fdbdcfe4fb6dc8ab1c38c9ffdc3043.

Both board sketches require controllerEnabled && coinEnabled && relayEnabled before a sampled edge can become pending/credit eligible. A disabled-gate edge enters the sticky fault path, deasserts outputs, preserves an existing pending identity, creates no new pending credit, and requires operator reconciliation.

- Quarantine #45091417124: SUCCESS; six pending-identity scenarios per board and both mutation controls rejected.
- Relay/output #45091417060: SUCCESS.
- Full #45091417147: FAILURE at validation step 8, inherited QA-owned Controller protocol parity / Missing poll signature check. All 14 target/platform jobs pass; downstream simulations, update bundle, candidate, signing and publication are skipped.
- Evidence is host-lab/CI only. Physical coin, relay, reboot durability, power-cut and hardware acceptance remain NOT TESTED.

QA owns the inherited assertion and independent verification of both fault stores/reboot behavior. Do not add a positive legacy poll signature to firmware.

## 5. Exact owner PR and CI snapshot

| Owner / PR | Exact head | Current evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; separate CORE owner retained |
| RENTAL #328 | 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | APK identity [44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) and API21/API23 [44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS; build [44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAIL |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM acceptance NOT TESTED |
| HARDWARE #283 | 4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30 | Quarantine [45057637178](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45057637178) PASS; Full [45057637196](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45057637196) FAIL |
| HARDWARE #327 | fadac4ed3bc837cf729753264b9427fa3fd312b9 | Quarantine [45029851960](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029851960) and Relay [45029852010](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029852010) PASS; Full [45029851959](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029851959) FAIL |
| HARDWARE #339 | b3e1558845ae2cd508e42d0d4722fdcd28293e32 | Quarantine [44986635350](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44986635350) PASS; Full [44986635417](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44986635417) FAIL |
| HARDWARE #340 | 20c5889fc4ceeb95ab0b05c7c11952704caff36b | Six preflight, quarantine, core-compile and full-build runs [44983396262–44983396365](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44983396262) all PASS; separate child of #283 |
| HARDWARE #341 | 4368435ad762d507a907e72a9c739c7bddbc3a81 | Quarantine [45060591705](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45060591705) PASS; Full [45060591630](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45060591630) FAIL |
| HARDWARE #342 | e7815297b1a8780b7868bc9b28f45011ec419dce | Quarantine [45043657779](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45043657779) PASS; Full [45043657792](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45043657792) FAIL |
| HARDWARE #343 | dfeff7d5f63e699de7bc296c7641f2493f1e0e13 | Quarantine [45062595339](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062595339) and Relay [45062595335](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062595335) PASS; Full [45062595995](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062595995) FAIL |
| HARDWARE #344 | 3bfa530c94a929191d7b3335c085dbd7f99e1e18 | Quarantine [45080942944](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45080942944) PASS; Full [45080942789](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45080942789) FAIL |
| HARDWARE #345 | 01916c89ae6718d3991c778b676d06718155d6a2 | Quarantine [45091417124](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45091417124) and Relay [45091417060](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45091417060) PASS; Full [45091417147](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45091417147) FAIL |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Windows [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; native COM lab not invoked |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No workflow runs; base is stale |
| RELEASE #291 | 1e0e58aa3b518d85382106d684c0ab4b23fd334a | Windows [45088729284](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45088729284) and Full [45088729330](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45088729330) FAIL; ESP32 compatibility [45088729327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45088729327) PASS |
| COE #35 | 16c0e140cbfd52d4cb572b7121189866763c77b2 | Case guard [45082913966](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45082913966) PASS; shared [45082913844](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45082913844) and sandbox [45082913881](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45082913881) FAIL |
| COE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Overlay/shell [44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case guard [44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS |
| COE #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage 5.1 [44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case guard [44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared contracts [44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL |

## 6. COE #26 exact migration provenance — still frozen

All recursive trees were complete (truncated=false): Experiments main 2,340 entries; Hardware #345 2,482; historical source pin 6d4c9b... 2,391; COE #26 286; COE main 3.

The schema-8 SOURCE_INTAKE.json has 61 runtime rows. Exact blob comparison confirms:
- all 61 source blobs match the recorded historical source pin;
- all 61 destination blobs match the recorded map;
- actual equality is 46 byte-identical / 15 derived, while summary says 47 / 14;
- current Experiments main vs the historical source pin is 33 unchanged / 20 changed / 8 absent.

Hardware import and identity gaps:
- 34 board-local Python helpers in the #345 source tree vs zero corresponding Hardware Python helpers in COE #26;
- ESP32 sketch source blob 2a5bad5904a1f6afabdcac95e762482975ebd886 vs destination 3cc7ec54b476943dc04a8d1af5e2df5fe054e422;
- ESP8266 sketch source blob 203db2f8394a5466517845d964195f8d6f25752f vs destination c8be98f72596681e36a3ad1f8939bf8046c96887;
- source hardening test experiment/openwrt/BlazePwifi/tests/v05_firmware_hardening_test.sh blob 41211b2c110ab409f6d9d1812ef12fda73b13211 vs destination Hardware/tests/test_firmware_hardening.sh blob f921c56cecc19cab1989507b9b4ade1f45dac54e.

Licensing:
- PisoWiFi LICENSE matches exactly: 1ee55b94183417be977ca287cd7391f9a6f7e721.
- Source root NOTICE.md exists (f6d92cd21465312be5993631fe26977219be0fb9); COE #26 root NOTICE.md is absent.
- Hardware-local LICENSE/NOTICE are absent from the destination.
- Of 15 derived tests, 11 are marked NOT_RUN and 4 PENDING_CI_RUN.

No staging, copy, move, overwrite, rebase, cherry-pick, route promotion or COE destination modification occurred. COE #26 remains FROZEN.

## 7. Governance and execution boundary

- Canonical private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections remain inaccessible in the available tool surface. Library search found older v3–v7 snapshots only; none was substituted and no private registry contents or identifiers were disclosed.
- PR #288 exact current-head workflow runs: zero. Combined status entries: zero.
- Full Master unittest discovery: NOT RUN.
- verify_coordination.py: NOT RUN.
- The static index/tree/blob assertions are inventory checks, not the repository Master test suite.
- Cleanup #266 remains OPEN, 0/7 complete.
- CORE remains owned by its separate Blaze Production Continuation automation; Master made no CORE source change.

## 8. Next actions

1. QA: replace the inherited positive poll-signature assertion with source-linked negative/default-deny tests and independently verify both fault stores, partial/dual-store failure and reboot durability limits.
2. HARDWARE: retain #345 as its own child of #343; do not combine it with the separate #338→#339→#341→#344 host-lab lineage.
3. COE integration owner: reconcile the 61-row classification, 20 changed / 8 absent current-source paths, 34 missing helper imports, firmware/test identities and NOTICE/license scope before requesting any staging review.
4. Repository administrators: verify effective branch protection and required checks.
5. Registry custodian: restore authorized access to v11 and newer corrections.
6. Human test runner: execute the full Master suite and verify_coordination.py from an authenticated checkout at the exact final Master SHA.

**Final safety:** PRODUCTION NO-GO. No merge, release, signing, secret provisioning, hardware flash, physical test, real payment operation or financial migration was performed.
