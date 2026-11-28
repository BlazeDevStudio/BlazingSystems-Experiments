# PHX-MASTER UTC07 — 2026-11-28T07:35Z — exact role CI, COE #26 provenance and access audit

**Role:** PHX-MASTER · **Task:** PHX-MASTER-20261128T07Z-HW373-COE26-ROLE-CI-IMPORT-AUDIT  
**Audit-start branch:** phoenix/master-coordination @ c52dcab4b4803ee5946b5d9b5f8d3008ae4a73b6  
**Scope:** coordination/phoenix only. Strict NO CODEX. No subsystem source, COE destination, ownership route, secret, payment, firmware, hardware or customer state was changed.

## Control plane and live refs

- CONTROL PLANE #172 remains OPEN. The latest prior PHX-MASTER checkpoint is UTC05; no UTC07 Master message existed at audit start.
- Cleanup-first #266 remains OPEN, 0-of-7 role gates accepted.
- Experiments default branch: main @ 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5.
- Experiments development branch: blazepwifi-v0.5.3-development @ aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Active v0.6 audit branch: blazepwifi-v0.6.0-audit-foundation @ 2fbd2475e9f54878c316fa7cea2f228386b0e859.
- Master PR #288 remains OPEN / DRAFT / UNMERGED on phoenix/master-coordination, audit-start head c52dcab4b4803ee5946b5d9b5f8d3008ae4a73b6, base main. It has 268 changed paths, all under coordination/phoenix/. Live compare is 696 commits ahead / 1 behind, merge base f4e8a891aed8af86d5fd315d28750a0ac3a7372b. No rebase, retarget or merge.
- COE main is a6513ab4412b4c014eee2863e45cbe32d06cb243. COE PR #26 remains OPEN / DRAFT / FROZEN on integration/ecosystem-nonproprietary-candidate-20261111 @ b382d233ff06c8791b1028bed3c617cc7b670d12.
- OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29, 11 routes, DRAFT_REVIEW_ONLY. PHX-MASTER source is coordination/phoenix/ and target is null. No route promotion or ownership transfer.
- Repository AGENTS.md, README, cloud artifact policy and storage recovery handover were re-read. Branch-protection endpoint returned 403; the rulesets endpoint returned an empty list, so effective enforcement remains UNKNOWN.

## Live role PRs and exact-head CI

| Owner / PR | Exact head | Exact-head CI / disposition |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build #42698139210 PASS. Read-only; CORE ownership remains separate. |
| RENTAL #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | Build #43653329229 PASS; native auth instrumentation #43653329235 PASS. |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | API21/23 smoke #45622918364 PASS; native auth #45622918551 PASS; APK identity #45622918340 PASS. Build #45622918468 FAIL: validation job 139235967531 reports stale handover freshness; ESP32 job 139235967636 fails because mbedtls/sha256.h is unavailable. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows synthetic run #42462978704 PASS. Native COM/device acceptance NOT TESTED. |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Windows synthetic run #43633486963 PASS; not native acceptance. |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No exact-head workflow run. |
| RELEASE #291 | bf339a76964a1abe2412fac45392fe06a8e66418 | No exact-head workflow run. |
| HARDWARE #373 | 3783654a3c9862598bbb714268c536fb8b34578b | Focused #46118310162 PASS; Mbed TLS #46118310195 PASS 3/3; Full #46118310135 terminal FAIL at QA-owned tests/controllers.sh. All 14/14 target/platform builds, including Android, PASS; downstream simulation, update, signing and publication stages SKIPPED. |

Hardware #373 is a host-side EEPROM fixture-template improvement, not a production firmware fix or physical acceptance. Its Full validation job 140897017614 invokes tests/controllers.sh; the current main test blob 53a7af25fdee9a650e10e870c4204e0fb43239c6 still contains the literal config_revision assertion. QA owns replacing that obsolete presence check with source-linked deny-only contract assertions; do not add a decoy field. CORE owns the authenticated controller register/poll/receipt interface.

## P0 source contract

Issue #177 remains OPEN. Its body still cites stale source 9df0a7e7; the live active v0.6 branch is 2fbd2475e9f54878c316fa7cea2f228386b0e859.

- ESP8266 source blob 12c4bb82b6fddafe813674a0b5f692c1d3634073: HTTP timeout 3,500 ms; synchronous post("poll") precedes the first digitalRead(runCoinPin) (line 354 before line 357).
- ESP32 source blob 29f1125d52ff474a0d028ad41f7af201be1f0f9d: HTTP timeout 3,500 ms; synchronous post("poll") precedes the first digitalRead(runCoinPin) (line 314 before line 318).

The poll-before-first-sample hazard is still present in active v0.6. The deny-only Hardware drafts are not merged into that branch and do not resolve P0. Financial issues #31 and #32, physical acceptance #34, and independent witness #43 remain OPEN. No physical pulse, power-cut, native-device or soak test was performed.

## COE #26 exact source/destination provenance

Exact recursive Git trees were read at the pinned source, current source main and live destination candidate; all returned non-truncated trees.

| Tree | Exact ref | Entries |
|---|---|---:|
| Historical source pin | Experiments @ 6d4c9b487af4d768c4d7627654d119417fcc6e00 | 2,391 |
| Current Experiments main | 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 | 2,341 |
| COE PR #26 candidate | b382d233ff06c8791b1028bed3c617cc7b670d12 | 286 |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 | 3 entries / 2 blobs |

- All 61 SOURCE_INTAKE runtime rows match the pinned source blob, candidate destination blob and Git mode. Actual split is 46 byte-identical / 15 derived; SOURCE_INTAKE summary still says 47 / 14.
- Current Experiments main relative to the historical source pin: 33 same / 20 divergent / 8 missing runtime rows. Do not silently replace the historical source pin with current main.
- Source tests subtree has 149 blobs; candidate Pisowifi/tests has 19. Four original test identities match the destination 4/4; all 15 SOURCE_INTAKE derived-test identities match destination blobs and modes 15/15. This is not a complete source-test import inventory.
- MIGRATION_MAP has 14 derived-test rows for 15 derived tests. It omits tests/voucher_txn_journal.sh and records stale hashes for run_focus.sh (map fa1f4f2c6393504499d50659d8bf980caf7ff85b; actual 2b7b861ec63cf811d18d0e63b11a65efd1bec0e9) and member_txn_journal.sh (map 01dc9c65ae9d74eaafb403d47aebcd20edd14390; actual d04df3c6f3ada60b9fda8c8c04230dd31e37019a).
- Within the BlazePwifi project root, 11 LICENSE/NOTICE artifacts were found; four exact destination counterparts exist and seven are missing: Android Launcher LICENSE, MODULE_LICENSE_APACHE2 and assets/license.html; R281 rental QR license; tests/vendor/jsqr-1.4.0/LICENSE; UI vendor qrcode/LICENSE; UI vendor tabler/LICENSE.
- SOURCE_INTAKE still names destination branch feature/pisowifi-cleanup-stabilization, while live PR #26 is on integration/ecosystem-nonproprietary-candidate-20261111. OWNERSHIP_ROUTES source_ref is f4e8a891 while SOURCE_INTAKE pins source commit 6d4c9b48. Preserve both historical pins until the COE owner reconciles them.
- All five candidate workflows are CANCELLED: #43096752563, #43096752800, #43096752557, #43096752609 and #43096752632; combined commit statuses are empty.

No staging, copy, move, overwrite, cherry-pick, route promotion or destination write was performed. PR #26 remains FROZEN. No migration is proposed until the COE owner resolves the branch pins, test-map count/hashes, complete test inventory and missing license artifacts.

## Execution classification and blockers

- EXECUTED: read-only GitHub recursive-tree inspection; exact source/destination blob and mode comparisons; runtime/test/license manifest reconciliation; role PR head and workflow/job inspection; current controller-test source inspection.
- NOT RUN: Master Python suite, verify_coordination.py, local shell/native test suites, and any new Master Actions run. A non-Codex git ls-remote attempt failed because this runtime could not resolve github.com; no local checkout is available.
- Private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections are NOT_RECOVERED. No Google Drive connector/action is exposed in this runtime. No older Library registry was substituted and no private registry contents or IDs are published.
- COE #26 remains FROZEN; cleanup #266 remains 0/7; P0 #177/#31/#32/#34/#43 remain OPEN. Production remains NO-GO.

## Next owner actions

1. QA: replace the config_revision literal presence assertion with source-linked deny-only controller checks and rerun Full on the exact successor SHA.
2. COE integration owner: reconcile SOURCE_INTAKE/MIGRATION_MAP, license/NOTICE coverage and branch pins; complete per-file test inventory before any staging.
3. Registry custodian: restore the canonical private Drive v11 registry and newer corrections through an authorized Drive connector. Repository administrator: verify effective branch protection. Provide a network-authorized non-Codex checkout for Master tests.

**PRODUCTION NO-GO.** No merge, release, signer provisioning, secret handling, hardware flash, physical test, real payment operation, financial migration or customer data change.
