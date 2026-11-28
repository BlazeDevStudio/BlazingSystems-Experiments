# PHX-MASTER UTC02 — exact-head Hardware #368, COE #26 provenance and role CI audit

**Task:** PHX-MASTER-20261128T02Z-HW368-COE26-SOURCE-PIN-ROLE-CI  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Execution:** Strictly NO CODEX. Master-only coordination and architecture scope.

## 1. Exact live refs and PR #288

| Ref | Exact SHA |
|---|---|
| Experiments main | 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 |
| v0.5.3 development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| v0.6 audit foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Master branch before this commit | 181d08e2a06d3d50ca298033fef76dacbd404a07 |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE #26 candidate | b382d233ff06c8791b1028bed3c617cc7b670d12 |

PR #288 is OPEN / DRAFT / UNMERGED, base main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b, 690 commits ahead / 1 behind, merge base f4e8a891. It has 265 changed paths and all 265 are under coordination/phoenix/. No rebase, retarget or merge.

Root AGENTS.md, README.md, the uploaded 00_MASTER_PROJECT_PHOENIX(1).txt, README_FIRST, COMMUNICATION_PROTOCOL(1).md, current coordination index, role assignments, integration matrix, architecture contracts, audit summary, repository routing and OWNERSHIP_ROUTES.json were re-read.

## 2. Current role PR heads and exact-head CI

| Role / PR | Current head | Exact CI / disposition |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build #42698139210 PASS (scoped); CORE left untouched |
| RENTAL #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | Build #43653329229 PASS; native auth #43653329235 PASS |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | API/auth/APK #45622918364/#45622918551/#45622918340 PASS; build #45622918468 FAIL at handover freshness and ESP32 mbedtls/sha256.h include |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows synthetic #42462978704 PASS; native COM NOT TESTED |
| HARDWARE #365 | e65b0b895af9c3fc5e5632f704cb67b347e69725 | Focused #46056656161 PASS; Mbed #46056656203 PASS; Full #46056656151 FAIL |
| HARDWARE #366 | 07fef4e8e1055c06cf5e5c3a0d3829c52be31cc9 | Focused #46059524018 PASS; Mbed #46059523991 PASS; Full #46059524022 FAIL |
| HARDWARE #367 | 85142129ed9336710539ea573ebf8f7a41cb2dd8 | Focused #46095032998 PASS; Mbed #46095033011 PASS; Full #46095032997 FAIL |
| HARDWARE #368 | 9885c81d934922fe35777d5c8f7245766b622255 | Focused #46095152313 PASS; Mbed #46095152451 PASS 3/3; Full #46095152346 FAIL |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Windows synthetic #43633486963 PASS; not hardware acceptance |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No exact-head workflow |
| RELEASE #291 | bf339a76964a1abe2412fac45392fe06a8e66418 | No exact-head workflow/status |
| RELEASE #242 | 36c0d0bb3e58786359555b307bb784f720f023ce | No exact-head workflow/status |

HARDWARE #368 is a child of #367. Its current Full run fails at validate job 140824749092, QA-owned tests/controllers.sh:21, the literal config_revision presence assertion. All 14 target/platform jobs that ran, including ESP8266, ESP32 and Android, passed; validation-dependent simulation, update, signing and publishing stages were skipped. The child changes only workflow/handover/lab-contract files; no production .ino file changed.

The #368 source-contract matrix rejects 14/14 alias mutations per board, including C-style and reinterpret_cast reference aliases; positive logical-AND and comment/string decoys pass. This is bounded regex/source-contract evidence, not complete C++ AST/dataflow analysis or electrical acceptance. QA should replace the stale literal-presence assertion with source-linked default-deny tests; do not add an unauthenticated decoy field or weaken deny-only behavior.

## 3. COE #26 exact-tree provenance

The exact recursive trees were non-truncated:

| Snapshot | Entries | Blobs |
|---|---:|---:|
| Historical SOURCE_INTAKE source 6d4c9b48 | 2,391 | 1,845 |
| Current Hardware #368 9885c81d | 2,442 | 1,896 |
| COE #26 destination b382d233 | 286 | 207 |
| COE main a6513ab4 | 3 | 2 |

The 11-route OWNERSHIP_ROUTES manifest remains DRAFT_REVIEW_ONLY and PHX-MASTER has no destination. Current #368 source-to-destination route comparison:

| Route | Source files | Exact | Divergent | Missing | Destination-only |
|---|---:|---:|---:|---:|---:|
| CORE library | 20 | 14 | 6 | 0 | 0 |
| CORE CGI | 1 | 0 | 1 | 0 | 0 |
| RENTAL Android | 983 | 0 | 0 | 983 | 8 |
| RENTAL server | 12 | 0 | 1 | 11 | 3 |
| PISONET SoftTimer | 44 | 16 | 9 | 19 | 22 |
| HARDWARE ESP32 | 4 | 0 | 1 | 3 | 0 |
| HARDWARE ESP8266 | 18 | 0 | 1 | 17 | 0 |
| QA tests | 151 | 2 | 2 | 147 | 15 |

The 30-file standalone-rental route is manual-file-mapping-required with copy_permitted=false. RELEASE workflow is reimplementation-review, not a direct copy.

### SOURCE_INTAKE / MIGRATION_MAP

SOURCE_INTAKE schema 8 has 61 runtime rows. All 61 declared source and destination Git blob SHAs and modes match the exact pinned-source and destination trees. However, actual row statuses are 46 byte-identical / 15 derived while the summary says 47 / 14.

Its 15 derived tests include 11 NOT_RUN and 4 PENDING_CI_RUN. MIGRATION_MAP has 14 derived-test rows and omits voucher_txn_journal.sh. Two recorded blob IDs are stale:
- run_focus.sh: map fa1f4f2c vs SOURCE_INTAKE 2b7b861e.
- member_txn_journal.sh: map 01dc9c65 vs SOURCE_INTAKE d04df3c6.

Both firmware files differ from the destination:
- ESP32 current #368 a673e323; COE destination 3cc7ec54; historical pinned source 29f1125d.
- ESP8266 current #368 7527dbff; COE destination c8be98f7; historical pinned source 12c4bb82.

Ten named source LICENSE/NOTICE artifacts were found; four exact destination counterparts exist. Six missing counterparts are root NOTICE.md, Launcher LICENSE and assets/license.html, jsqr vendor LICENSE, UI qrcode LICENSE and UI tabler LICENSE.

The route manifest source_ref f4e8a891 differs from SOURCE_INTAKE/MIGRATION_MAP source commit 6d4c9b48. SOURCE_INTAKE/MIGRATION_MAP destination branch feature/pisowifi-cleanup-stabilization differs from live PR #26 branch integration/ecosystem-nonproprietary-candidate-20261111, although the candidate SHA b382d233 matches. Preserve both records until the COE owner clarifies source-baseline semantics and updates its destination pin.

PR #26 is OPEN/DRAFT, 205 changed files / 85 commits. Its five workflows are all CANCELLED. No staging, copy, move, overwrite, cherry-pick or migration occurred. The PR body's strategic licensing resolution text does not supersede the current DRAFT_REVIEW_ONLY route manifest, incomplete import map, missing notices or cancelled CI.

## 4. P0 and architecture contract revalidation

Current v0.6 development branch 2fbd2475 still has the blocking poll-before-sample sequence:
- ESP8266: timeout 3,500 ms at line 263; post("poll") line 354; digitalRead(runCoinPin) line 357.
- ESP32: timeout 3,500 ms at line 230; post("poll") line 314; digitalRead(runCoinPin) line 318.

P0 #177 still OPEN. Its cited source commit 9df0a7e7 is stale, but both firmware blob SHAs match the current development branch. Current CGI blob db58041c signs member responses but controller register/ping lines 114–116 and poll lines 119–137 return no controller response_sig. Member response signatures are not controller-response authentication.

Financial crash-atomicity #31 and rental receipt/lease consistency #32 remain OPEN. Physical acceptance #34 and independent freshness witness #43 remain OPEN. Cleanup #266 is OPEN with 0/7 gates checked.

## 5. Registry, automation and execution limitations

The canonical private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not recovered. Library search surfaced older v3-v7 snapshots and a separate November 9 checkpoint only. No Google Drive connector/action is exposed. No old snapshot was substituted and no private registry content or IDs were published.

Visible automation inventory shows Phoenix Master Hourly Development and Blaze Hourly Production Development (PHX-HARDWARE). The exact-title Blaze Production Continuation CORE automation was not surfaced; Master honors the stated CORE ownership, leaves CORE untouched and starts no competing CORE worker.

Executed: exact non-truncated Git tree comparisons; 61/61 SOURCE_INTAKE runtime blob/mode checks; route-level exact/divergent/missing/extra counts; derived-test map and license/NOTICE inventory; exact role CI status and failing job identification.

NOT RUN: Master Python suite, verify_coordination.py, local build/test suite, Master exact-head GitHub Actions. No local non-Codex checkout/test runner was available. No physical tests or hardware operations occurred.

## 6. Owner actions / next step

1. QA: replace tests/controllers.sh:21 literal config_revision assertion with source-linked default-deny controller vectors and rerun Full on #368/#367.
2. HARDWARE: retain the deny-only contract; refresh only its own handover/PR evidence if the source/test head changes.
3. COE integration owner: reconcile source_ref semantics and actual destination branch pin; correct 46/15 summary, derived-test map/blob IDs, six license gaps and route-level incomplete imports. Keep candidate frozen until exact source, license, tests and CI are independently reviewed.
4. CORE + HARDWARE + QA: resolve P0 poll-before-sample and controller response authentication on owner branches.
5. Registry custodian/repository admin: restore authorized v11/newer corrections and provide a non-Codex Master test environment.

**PRODUCTION NO-GO.** Protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain unverified. No merge, release, signing, secret provisioning, flashing, real payment operation or financial migration occurred.
