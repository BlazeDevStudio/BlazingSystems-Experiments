# PHX-MASTER UTC01 — exact-head role CI, Hardware stack and COE #26 provenance

**Recorded:** 2026-11-28T01:34:27Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Task:** PHX-MASTER-20261128T01Z-HW367-COE26-EXACT-PROVENANCE  
**Scope:** coordination/phoenix/ only. Strict NO CODEX.

## Executive disposition

Master coordination work is actionable and committed on the existing master branch. PR #288 remains OPEN / DRAFT / UNMERGED. COE #26 remains FROZEN. Cleanup issue #266 remains OPEN with 0/7 gates checked. P0 #177 remains OPEN. Production remains NO-GO.

No subsystem source branch, COE destination file, ownership route, shared interface, secret, signer, payment system, hardware device or release state was changed.

## 1. Exact live refs

| Ref | Exact SHA |
|---|---|
| Experiments main (default) | 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 |
| Experiments v0.5.3 development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Experiments v0.6 audit foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Master starting HEAD | bc780bcec4a6d9c25d005d35b80c437dc77d4bc4 |
| COE main (default) | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE PR #26 candidate | b382d233ff06c8791b1028bed3c617cc7b670d12 |

PR #288 is OPEN / DRAFT / UNMERGED and points to the Master branch. At the starting HEAD it had 264 changed paths, all under coordination/phoenix/. Current Experiments main compares 689 commits ahead / 1 behind, merge base f4e8a891aed8af86d5fd315d28750a0ac3a7372b. No rebase or retarget was performed. COE main is a structure-only tree of 3 entries / 2 blobs; the active work remains in draft PRs.

## 2. Exact-head role PRs and CI

| Role / PR | Current head | Exact evidence | Disposition |
|---|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build #42698139210 PASS | Scoped only; CORE untouched |
| RENTAL #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | Build #43653329229 PASS; native auth #43653329235 PASS | Parent draft remains unmerged |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | API/auth/APK checks #45622918364, #45622918551, #45622918340 PASS; Build #45622918468 FAIL | Handover freshness and ESP32 Mbed TLS include remain blocking; log reports missing mbedtls/sha256.h |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows synthetic #42462978704 PASS | Native COM acceptance NOT TESTED |
| HARDWARE #365 | e65b0b895af9c3fc5e5632f704cb67b347e69725 | Poll-intake #46056656161 PASS; Mbed #46056656203 PASS; Full #46056656151 FAIL | Test-only poll-boundary matrix; no physical acceptance |
| HARDWARE #366 | 07fef4e8e1055c06cf5e5c3a0d3829c52be31cc9 | Poll-intake #46059524018 PASS; Mbed #46059523991 PASS; Full #46059524022 FAIL | Child of #365; Full still fails inherited controller parity |
| HARDWARE #367 | 4e558a06ff558dffef8a966a6e412029e7340119 | Focused #46089846162 PASS; Mbed #46089846114 PASS; Full #46089846111 FAIL | 15 jobs PASS, 1 validation job FAIL, 13 downstream jobs SKIPPED |
| HARDWARE #354 | fc842342596786e072630179acfbbc4feeb2ba02 | Focused #45864684458 and Mbed #45864684325 PASS; Full #45864684497 and Native #45864684295 FAIL | Draft candidate only |
| HARDWARE #357 | 963c37135797e0d570ef910596c098bb9d902779 | Focused #46067421658 and Mbed #46067421664 PASS; Full #46067421812 and Native #46067421738 FAIL | Draft candidate only |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Windows synthetic #43633486963 PASS | Not hardware acceptance |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No exact-head workflow run | Expected RED remains unverified |
| RELEASE #291 / #242 | bf339a76964a1abe2412fac45392fe06a8e66418 / 36c0d0bb3e58786359555b307bb784f720f023ce | No exact-head workflow runs or statuses | Both remain draft; #242 mergeable=false |
| MASTER #288 | bc780bcec4a6d9c25d005d35b80c437dc77d4bc4 | No exact-head Actions run or combined status | Master suite NOT RUN |

### Hardware #365 → #366 → #367 stack

Current stack heads are #365 e65b0b89, #366 07fef4e8 and #367 4e558a06. The #367 diff has 10 Hardware-owned paths and no production .ino changes. Its latest source/test commit is 985a54c289b8e3c796c2bcc977f652b178b293c0; the docs/handover head is 4e558a06. The PR description still cites older source/test/docs pins 183650be / 3f1f7424 and must be refreshed by HARDWARE.

The exact #367 Full run fails at QA-owned tests/controllers.sh:21. The current main test script blob 53a7af25 requires config_revision in both sketches; the deny-only #367 candidate sketches omit it. Both ESP target builds and Android pass in the same run. This is a QA contract mismatch, not authority for Hardware to add an unauthenticated placeholder or weaken deny-default. QA must replace the stale presence assertion with source-linked deny-only vectors, then rerun Full on the exact current head.

## 3. P0 #177 — current active-v0.6 source recheck

Active branch blazepwifi-v0.6.0-audit-foundation is still 2fbd2475.

- ESP8266 sketch blob 12c4bb82: synchronous post("poll") precedes digitalRead(runCoinPin); 3,500 ms timeout remains.
- ESP32 sketch blob 29f1125d: same poll-before-first-sample ordering and 3,500 ms timeout.
- Current CGI producer blob db58041c has response_sig fields for member responses, but the register|ping and poll controller response blocks do not emit a controller response_sig. Member response signatures do not authenticate controller poll/disposition.
- The deny-only Hardware stack is a separate draft candidate; it does not resolve the active-v0.6 P0.

CORE owns the authenticated controller interface contract; HARDWARE owns firmware; QA owns independent regression evidence. No source changes were made.

## 4. COE #26 — exact source, destination and import completeness

Current COE PR #26 candidate branch is integration/ecosystem-nonproprietary-candidate-20261111 at b382d233. SOURCE_INTAKE.json and MIGRATION_MAP.md still name feature/pisowifi-cleanup-stabilization and pin historical source commit 6d4c9b48.

All recursive Git trees were fetched without truncation:

| Tree | Entries | Blobs |
|---|---:|---:|
| Historical SOURCE_INTAKE source 6d4c9b48 | 2,391 | 1,845 |
| Current Hardware #367 source 4e558a06 | 2,440 | 1,894 |
| COE #26 destination b382d233 | 286 | 207 |

### Route-level blob/mode comparison

| Route | Source blobs | Destination blobs | Exact | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| Pinned ESP32 | 3 | 1 | 0 | 1 | 2 | 0 |
| Pinned ESP8266 | 3 | 1 | 0 | 1 | 2 | 0 |
| Pinned QA tests | 149 | 19 | 2 | 2 | 145 | 15 |
| Current #367 ESP32 | 4 | 1 | 0 | 1 | 3 | 0 |
| Current #367 ESP8266 | 18 | 1 | 0 | 1 | 17 | 0 |
| Current #367 QA tests | 151 | 19 | 2 | 2 | 147 | 15 |

Current Hardware #367 sketch blobs are ESP8266 7527dbff and ESP32 a673e323. COE destination sketch blobs are ESP8266 c8be98f7 and ESP32 3cc7ec54. Historical pinned source blobs are ESP8266 12c4bb82 and ESP32 29f1125d. All three versions differ per board. The current #367 sketches do not contain response_sig, |poll| or config_revision; the COE destination sketches contain all three. COE Hardware test blob f921c56 requires response_sig and |poll|. This is an exact protocol/provenance mismatch, not a safe byte-copy candidate.

### SOURCE_INTAKE and test identity

A direct Git-tree comparison verified all 61 runtime rows against actual source/destination blob IDs and Git modes. Actual status counts are 46 byte-identical / 15 derived, while the manifest summary says 47 / 14.

The four original test rows match their declared source/destination identities and modes: portal/security are byte-identical; config/integration are intentionally edited.

All 15 derived-test destination blobs and modes match SOURCE_INTAKE. However:
- 11 derived tests are NOT_RUN.
- 4 derived tests are PENDING_CI_RUN.
- MIGRATION_MAP has 14 derived-test rows, not 15.
- Missing mapping: Pisowifi/tests/voucher_txn_journal.sh (destination blob 4277a56a, mode 100755).
- Stale map blob for run_focus.sh: declared fa1f4f2c, actual 2b7b861e.
- Stale map blob for member_txn_journal.sh: declared 01dc9c65, actual d04df3c6.
- The source pin does not contain voucher_txn_journal.sh; it is a destination-only derived test and needs explicit provenance.

### License and NOTICE audit

Ten named source license/notice artifacts were compared at exact mapped paths. Four destination counterparts are exact: PisoWiFi LICENSE, rootfs QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE. Six counterparts are absent: root NOTICE.md, Android Launcher LICENSE, Android Launcher assets/license.html, jsqr vendor LICENSE, UI QRCode LICENSE and UI Tabler LICENSE.

SOURCE_INTAKE explicitly keeps release_authorized=false, hardware_tested=false and full_ci_tested=false. No destination staging, copy, move, overwrite, cherry-pick, rebase or retarget was performed.

## 5. COE supporting candidate CI

- COE #26 at b382d233: all five candidate workflows CANCELLED (#43096752563, #43096752800, #43096752557, #43096752609, #43096752632).
- COE #35 at bc57ba8e: case-collision #45897198239 PASS; ImageBuilder #45897198204 FAIL; Hardware/Shared #45897198326 FAIL.
- COE #45 at 9d76a134: OpenWrt overlay #44295049727 PASS; case-collision #44295049903 PASS.
- COE #49 at aeb8ff11: case-collision #44646341992 PASS; Stage 5.1 bridge #44646341873 PASS; Hardware/Shared #44646341922 FAIL.

CI evidence is not native hardware acceptance and does not authorize integration.

## 6. Registry, automation and execution access

Current Experiments AGENTS.md blob d8777e3b, cloud artifact policy blob 5e503925 and storage handover blob a15f14cb were re-read. The policy requires the canonical private registry and sync ledger before new Drive mirror artifacts.

Canonical private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not recovered. Library title/content search did not surface them; no Google Drive connector/action is exposed. Older v3-v7 snapshots were not substituted and no private IDs or registry contents were published.

Visible automation inventory shows Phoenix Master Hourly Development enabled and Blaze Hourly Production Development assigned to PHX-HARDWARE. The exact Blaze Production Continuation CORE task was not surfaced in this inventory; CORE remains reserved to its separate owner and was not touched. No competing CORE worker or automation was created.

Master exact-head Actions and combined statuses are absent. Master repository Python tests and verify_coordination.py were NOT RUN because no local checkout/test runner is exposed. The in-memory Git-tree/manifest audit above was executed; it is source inspection, not a repository test or CI run.

## 7. Exact next actions

1. PHX-QA: replace the literal config_revision presence assertion in tests/controllers.sh with source-linked deny-only controller vectors; rerun Full on exact #367 head 4e558a06.
2. PHX-HARDWARE: refresh PR #367 body and canonical handover pins to source/test 985a54c and docs/head 4e558a06; keep coin/relay denied.
3. COE integration owner: correct the 46/15 summary, 14/15 derived-test map, two stale blob IDs, destination branch pin, six license/NOTICE gaps and firmware source baseline; do not stage until reviewed.
4. PHX-CORE / HARDWARE / QA: publish and independently verify authenticated controller register/poll/receipt/disposition contract; resolve P0 #177.
5. Registry custodian / repository administrator: restore authorized private v11 and newer corrections, plus a non-Codex Master checkout/test path.

## 8. Safety disposition

PRODUCTION NO-GO. Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain unverified.

No merge, release, signing, secret provisioning, hardware flashing, physical testing, real payment operation or financial migration occurred.
