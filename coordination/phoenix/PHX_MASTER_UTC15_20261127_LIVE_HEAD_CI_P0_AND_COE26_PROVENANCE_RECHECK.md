# PHX-MASTER UTC15 — live exact-head, P0 poll-order, role CI, and COE #26 provenance recheck

**Observed:** 2026-11-27T15:36:54Z  
**Role / task:** PHX-MASTER / PHX-MASTER-20261127T15Z  
**Scope:** coordination/phoenix/, architecture and interface evidence, cross-repository provenance, integration gates.  
**Execution:** connected GitHub read/write and recursive tree/blob inspection; ordinary local Git access attempted; strictly NO CODEX.

## 1. Exact live refs at audit start

| Repository / ref | Exact SHA | Notes |
|---|---|---|
| Experiments main | 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 | Current default branch |
| Active v0.6 audit foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 | Current development source reviewed for P0 |
| Legacy v0.5.3 development | aad3aade72c1156eecba1fed30907c6d0283b2c5 | Retained historical development line |
| PHX-MASTER | 4e740635beceb3504aa718ce0d0b4810b1b4eef4 | Pre-update branch head |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 | Structure-only three-entry scaffold |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | integration/ecosystem-nonproprietary-candidate-20261111 |

Experiments main metadata confirms default branch main. PR #288 is OPEN / DRAFT / UNMERGED, head phoenix/master-coordination, base main pinned at f4e8a891aed8af86d5fd315d28750a0ac3a7372b. Against the current main HEAD, Master was 665 commits ahead / 1 behind, merge base f4e8a891. Its 254 pre-update changed paths were all under coordination/phoenix/. No rebase, retarget, or merge was performed.

## 2. P0 #177 — stale issue pin, live source still polls before sampling

Issue #177 remains OPEN and its embedded source pin 9df0a7e7cae31fc06d098d5a0ea7ae27f56a75ed is stale relative to active v0.6 HEAD 2fbd2475e9f54878c316fa7cea2f228386b0e859.

The live source files were read at the active v0.6 HEAD:

| Board | Source blob | Blocking timeout | Synchronous poll | First coin sample |
|---|---|---:|---:|---:|
| ESP8266 | 12c4bb82b6fddafe813674a0b5f692c1d3634073 | line 263: setTimeout(3500) | line 354: post("poll") | line 357: digitalRead(runCoinPin) |
| ESP32 | 29f1125d52ff474a0d028ad41f7af201be1f0f9d | line 230: setTimeout(3500) | line 314: post("poll") | line 318: digitalRead(runCoinPin) |

This confirms the blocking poll still precedes the first coin-input sample on both boards. No firmware source was changed by Master. PHX-HARDWARE retains implementation ownership; CORE/HARDWARE/QA must agree the poll/receipt/disposition contract before any source change is accepted. Do not add a positive poll token or weaken default-deny behavior to satisfy a stale test.

## 3. Exact owner PR and CI reconciliation

All owner results below are existing GitHub Actions runs for the exact PR heads listed; they are not Master test executions or physical acceptance.

| Role / PR | Exact head | Exact-head evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build #42698139210 PASS (scoped only) |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | API #45622918364 PASS; auth/installer #45622918551 PASS; APK identity #45622918340 PASS; shared build #45622918468 FAIL |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows synthetic #42462978704 PASS |
| HARDWARE #361 | 8a1999ccdcab02445ef93c153316e519d9476210 | Poll #46018576706 PASS; Mbed TLS matrix #46018576254 PASS (3/3); Full build #46018576372 FAIL |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Windows synthetic #43633486963 PASS; native COM lab not invoked |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No exact-head PR-triggered workflow run |
| RELEASE #291 | bf339a76964a1abe2412fac45392fe06a8e66418 | No exact-head PR-triggered workflow run |
| RELEASE #242 | 36c0d0bb3e58786359555b307bb784f720f023ce | No exact-head PR-triggered workflow run |
| MASTER #288 | 4e740635beceb3504aa718ce0d0b4810b1b4eef4 | No exact-head workflow run or combined status |

HARDWARE #361 Full run #46018576372 failed in validate job 140572092833 at the Controller protocol parity step. The ESP8266 and ESP32 jobs, Android, and all listed optional/target firmware jobs succeeded; downstream update, simulation, signing, publishing, and release jobs were skipped. This is CI evidence only; it does not establish native or physical acceptance.

## 4. Cleanup-first gate

Issue #266 remains OPEN with 0-of-7 role tracks checked. MASTER's inventory/ownership track remains intentionally unchecked: the broader duplicate/dead-code inventory is incomplete. No mass move, rename, deletion, or ownership transfer was attempted.

## 5. COE #26 exact source/destination provenance

Recursive trees were fetched at exact refs and were not truncated:

| Tree | Entries |
|---|---:|
| Experiments pinned SOURCE_INTAKE source 6d4c9b487af4d768c4d7627654d119417fcc6e00 | 2,391 |
| Experiments current main 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 | 2,341 |
| Experiments active v0.6 2fbd2475e9f54878c316fa7cea2f228386b0e859 | 2,392 |
| COE PR #26 destination b382d233ff06c8791b1028bed3c617cc7b670d12 | 286 |
| COE main a6513ab4412b4c014eee2863e45cbe32d06cb243 | 3 |

### Source and destination pins disagree

SOURCE_INTAKE.json blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f pins Experiments source 6d4c9b48 and destination branch feature/pisowifi-cleanup-stabilization. Live PR #26 instead targets integration/ecosystem-nonproprietary-candidate-20261111 at b382d233. The intake does not describe the live PR destination branch. OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29, 11 routes, DRAFT_REVIEW_ONLY, and PHX-MASTER target null.

### Firmware blob identity

| Board | Pinned source blob | COE #26 destination blob | Exact match |
|---|---|---|---|
| ESP32 | 29f1125d52ff474a0d028ad41f7af201be1f0f9d | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 | NO |
| ESP8266 | 12c4bb82b6fddafe813674a0b5f692c1d3634073 | c8be98f72596681e36a3ad1f8939bf8046c96887 | NO |

The active v0.6 source sketches match the historical pinned source blobs, while both destination sketches differ. Current Experiments main has different board blobs again; no current source candidate is authorized by the intake.

### Runtime and test manifest integrity

- SOURCE_INTAKE runtime rows: 61. Actual row statuses: 46 byte-identical / 15 derived. Summary claims 47 / 14.
- SOURCE_INTAKE derived_tests: 15 entries. MIGRATION_MAP.md: 14 derived-test rows.
- tests/voucher_txn_journal.sh is present in the intake derived list and destination test tree but omitted from MIGRATION_MAP.
- tests/run_focus.sh intake blob 2b7b861ec63cf811d18d0e63b11a65efd1bec0e9 differs from map blob fa1f4f2c6393504499d50659d8bf980caf7ff85b.
- tests/member_txn_journal.sh intake blob d04df3c6f3ada60b9fda8c8c04230dd31e37019a differs from map blob 01dc9c65ae9d74eaafb403d47aebcd20edd14390.
- At the pinned source commit, 149 entries exist under the source tests/ path; destination Pisowifi/tests/ has 19 entries. Four relative paths are shared: two are byte-identical and two are divergent; 145 source entries are source-only and 15 destination entries are destination-only. Counts include README/fixture/vendor entries, so they are path inventory, not a claim that every entry is an executable test.

### License / notice provenance

Nine source LICENSE/NOTICE paths were found at the pinned source commit. Four mapped destination counterparts are exact. Five are absent at the mapped paths: repository-root NOTICE.md, Rental/android/BlazeRentalLauncher/LICENSE, Pisowifi/tests/vendor/jsqr-1.4.0/LICENSE, Pisowifi/ui/vendor/qrcode/LICENSE, and Pisowifi/ui/vendor/tabler/LICENSE. Pisowifi/LICENSE matches source project LICENSE at blob 1ee55b94183417be977ca287cd7391f9a6f7e721; rootfs qrcode and tailadmin license/notice blobs also match. This is provenance evidence, not legal approval.

All five COE #26 candidate workflows remain CANCELLED: #43096752563, #43096752800, #43096752557, #43096752609, #43096752632. The destination commit has no combined statuses. PR #26 remains OPEN / DRAFT / FROZEN. No staging, copy, move, overwrite, cherry-pick, rebase, or destination write was performed.

## 6. Private registry and repository policy dependencies

The exact Library title search for BLAZE_PROJECT_REGISTRY_v11_20261027.json did not return v11 or newer corrections; only older v3-v7 snapshots surfaced. No older snapshot was substituted. No Google Drive connector is exposed in this runtime, so the canonical private registry, artifact manifest, and sync ledger remain NOT_RECOVERED. No private Drive IDs or contents were written to public GitHub.

AGENTS.md at main blob d8777e3b58efc41caa5aa3c969c932aee9103d5f requires reading the cloud artifact policy and verified recovery handover from the legacy BlazingSystems/BlazingSystems repository. Those linked documents could not be fetched through the current GitHub connector surface; they remain NOT READ / BLOCKED. Repository admin must restore readable canonical documents or provide current copies.

## 7. Automation and ownership deconfliction

The current automation inventory surfaced an active Blaze Hourly Production Development task whose prompt explicitly assigns PHX-HARDWARE. It did not surface an automation with the exact title Blaze Production Continuation. Regardless, CORE #252 and all other subsystem source branches remained owner-reserved; Master made no CORE/RENTAL/PISONET/HARDWARE/QA/RELEASE source edits and changed no automation.

## 8. Test execution classification

- GitHub source, refs, recursive trees, file blobs, role PRs, and Actions results: inspected.
- Manifest/tree/count/blob comparisons: performed in-memory against connector-returned exact content.
- Master Python suite and verify_coordination.py: NOT RUN; ordinary local git ls-remote failed because this runtime could not resolve github.com.
- Master exact-head Actions: no runs and no combined statuses.
- Physical hardware, native COM acceptance, 150 real power cuts, and 30-device/24-hour soak: NOT TESTED.

## 9. Next exact actions

1. Registry custodian restores authorized access to canonical v11 and all newer corrections; keep private records private.
2. Repository admin restores the two AGENTS-linked cloud policy/handover documents and supplies a non-Codex checkout or dedicated Master CI path.
3. PHX-QA corrects the Controller protocol parity assertion against an approved semantic contract; do not add a decoy token.
4. CORE/HARDWARE/QA resolve poll intake and receipt/disposition semantics, then the firmware owner updates the two boards and QA adds source-linked regressions.
5. COE integration owner reconciles live source/destination branch pins, runtime counts, derived-test map/hashes, all license/NOTICE counterparts, and exact-head destination CI before proposing any staging.
6. Role owners update cleanup #266 only when their own cleanup evidence is complete; Master does not check other roles' boxes.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates remain mandatory. No merge, release, signer provisioning, secret provisioning, hardware flash, physical test, real payment operation, financial migration, or customer cutover occurred.
