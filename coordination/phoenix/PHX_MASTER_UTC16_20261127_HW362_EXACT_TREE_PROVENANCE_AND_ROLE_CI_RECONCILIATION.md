# PHX-MASTER UTC16 — exact-head reconciliation, PR #362 and COE #26 provenance

**Observed:** 2026-11-27T16:36:51Z  
**Role / task:** PHX-MASTER / PHX-MASTER-20261127T16Z  
**Scope:** coordination/phoenix/, architecture/interface evidence, cross-repository migration provenance and integration gates.  
**Execution:** connected GitHub reads/writes and exact recursive Git-tree/blob comparison; strictly NO CODEX.

## 1. Exact refs re-read

| Repository / ref | Exact SHA | State |
|---|---|---|
| Experiments default main | 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 | default branch |
| Active v0.6 audit foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 | active development source |
| Legacy v0.5.3 development | aad3aade72c1156eecba1fed30907c6d0283b2c5 | retained development line |
| PHX-MASTER | 081a79a58127db90f5c649926187b238ba959cab | pre-update head |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 | default branch |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | OPEN / DRAFT / FROZEN |

PR #288 remains OPEN / DRAFT / UNMERGED, branch phoenix/master-coordination, base main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b. The ownership manifest is unchanged: blob e4db324315a1b3543fec17a148fbf960170fcb29, 11 routes, DRAFT_REVIEW_ONLY, PHX-MASTER target null. Cleanup #266 remains OPEN / 0-of-7. P0 #177 remains OPEN.

## 2. Role ownership and exact-head CI

No source ownership changed. CORE, RENTAL, PISONET, HARDWARE, QA and RELEASE remain owner-reserved. PHX-MASTER changed coordination/phoenix/ only.

| Role / PR | Exact head | Existing exact-head evidence |
|---|---|---|
| MASTER #288 | 081a79a58127db90f5c649926187b238ba959cab | no PR-triggered workflow runs; no combined statuses |
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build #42698139210 PASS, scoped only |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | API #45622918364 PASS; auth/installer #45622918551 PASS; APK identity #45622918340 PASS; shared build #45622918468 FAIL |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows synthetic #42462978704 PASS; native COM acceptance NOT TESTED |
| HARDWARE #361 | 8a1999ccdcab02445ef93c153316e519d9476210 | Poll #46018576706 PASS; Mbed TLS #46018576254 PASS 3/3; Full #46018576372 FAIL |
| HARDWARE #362 | eeddfc37d24d20ebc14641dfe3ffa247bbbc1ebd | focused push #46029346165 PASS; focused PR #46029353181 PASS; Mbed TLS #46029353094 PASS 3/3; Full #46029353015 FAIL; Native #46029353001 FAIL |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Windows synthetic #43633486963 PASS; native COM lab not invoked |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | no exact-head PR workflow run |
| RELEASE #291 / #242 | bf339a76964a1abe2412fac45392fe06a8e66418 / 36c0d0bb3e58786359555b307bb784f720f023ce | no exact-head PR-triggered workflow runs |

### HARDWARE #362 exact result

PR #362 is OPEN / DRAFT / UNMERGED, stacked on #361 at 8a1999cc. Its firmware/test commit is a45b2491f312f1d66e70f8caef5b55f49dec60bb; harness assertion correction is 2768bf701945401aa6efed9c7c2573ed08b2b8cb; workflow sync is 7536b6568c186a35bcbde0cddff1c6774bfe6c6d; final docs/PR head is eeddfc37d24d20ebc14641dfe3ffa247bbbc1ebd.

- Focused PR #46029353181 and push #46029346165 pass. Both boards report 15 scenarios, six ambiguous-preservation cases and 18/18 injected unsafe mutations rejected.
- Mbed TLS 3/4 PR #46029353094 passes 3/3.
- Full #46029353015: ESP8266, ESP32, Android and all 13 firmware target jobs pass; validation job 140609142439 fails at tests/controllers.sh:21 on literal config_revision parity. Update bundle, simulations, signing handoff and publication jobs are skipped.
- Native #46029353001: PAY-0745 fails a literal assertion expecting if(any) return false; the source has an explicit fail-closed block. QA owns semantic reconciliation; Hardware did not weaken the guard.
- The first focused attempt #46028536467 exposed a test-only ordering assertion bug; the correction is recorded in PR #362 and the exact-head focused reruns pass.

These are CI/source-lab results only, not native device or physical acceptance.

## 3. P0 #177 re-read against active v0.6

Issue #177's embedded source pin 9df0a7e7cae31fc06d098d5a0ea7ae27f56a75ed is stale relative to active v0.6 HEAD 2fbd2475e9f54878c316fa7cea2f228386b0e859. The live sketches were fetched at that exact active branch HEAD:

| Board | Source blob | 3,500 ms timeout | synchronous poll | first coin sample |
|---|---|---:|---:|---:|
| ESP8266 | 12c4bb82b6fddafe813674a0b5f692c1d3634073 | line 263 | line 354 | line 357 |
| ESP32 | 29f1125d52ff474a0d028ad41f7af201be1f0f9d | line 230 | line 314 | line 318 |

Both sketches still call synchronous post("poll") before digitalRead(runCoinPin). HARDWARE owns firmware changes; CORE/HARDWARE must agree the authenticated poll/receipt/disposition contract; QA owns independent regression semantics. No firmware source was modified by Master.

## 4. COE #26 exact source/destination tree and route comparison

The candidate destination was read at exact PR #26 head b382d233ff06c8791b1028bed3c617cc7b670d12. Both recursive trees were non-truncated.

- SOURCE_INTAKE pinned source 6d4c9b487af4d768c4d7627654d119417fcc6e00: 2,391 entries / 1,845 blobs.
- COE #26 destination: 286 entries / 207 blobs.
- Current HARDWARE candidate #362 source tree eeddfc37d24d20ebc14641dfe3ffa247bbbc1ebd: 2,428 entries / 1,882 blobs.

The path-suffix mapping below is a provenance comparison only; it is not copy authorization.

| Route | Source blobs | Destination blobs | Exact | Divergent | Missing | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| CORE OpenWrt library | 20 | 20 | 14 | 6 | 0 | 0 |
| CORE Vendo CGI | 1 | 1 | 0 | 1 | 0 | 0 |
| RENTAL Android | 983 | 8 | 0 | 0 | 983 | 8 |
| RENTAL standalone server | 12 | 4 | 0 | 1 | 11 | 3 |
| PISONET SoftTimer | 44 | 47 | 16 | 9 | 19 | 22 |
| HARDWARE ESP32 | 3 | 1 | 0 | 1 | 2 | 0 |
| HARDWARE ESP8266 | 3 | 1 | 0 | 1 | 2 | 0 |
| QA PisoWiFi tests | 149 | 19 | 2 | 2 | 145 | 15 |
| RELEASE workflow reimplementation | 1 | 1 | 0 | 1 | 0 | 0 |

The test-path inventory includes README, fixture, vendor and other non-executable entries; it is not a count of executable test cases.

### Current #362 hardware candidate versus COE #26

At #362 head eeddfc37, the ESP8266 sketch blob is 7527dbff41b7f21bdc3d3ed9ee3db1c0d21eb07b and the ESP32 sketch blob is a673e323e1c160cbfe03949d13a9e01b47386596. COE #26 still contains ESP8266 c8be98f72596681e36a3ad1f8939bf8046c96887 and ESP32 3cc7ec54b476943dc04a8d1af5e2df5fe054e422. Neither matches.

The #362 pending-recovery lab (05e65ff1d78fcd347d039fd06b13cb34b02aa98c), C++ harness (e460fee5d4935ebeb8707a2941a35868d4f5dc4c) and imported firmware_source_extract.py dependency (22f86bd5e0b462c125b55110356641bf1d759767) are source-only. Their route-derived Hardware/esp8266/BlazePwifiVendo destination paths are absent from #26. The destination Hardware/tests tree contains only test_firmware_hardening.sh; it does not contain this candidate lab/harness/dependency.

### SOURCE_INTAKE and MIGRATION_MAP integrity

At exact #26 head:
- SOURCE_INTAKE.json blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f has 61 runtime rows. Actual row statuses are 46 byte_identical / 15 derived_cleanup_review_required_real_router_test, while summary claims 47 / 14.
- Intake derived_tests contains 15 entries; MIGRATION_MAP.md blob b54fc15d83bc2269de03db8aadd0e76259fd13d9 lists 14 test rows. tests/voucher_txn_journal.sh is absent from the map.
- Intake and destination both identify tests/run_focus.sh at 2b7b861ec63cf811d18d0e63b11a65efd1bec0e9; the map claims fa1f4f2c6393504499d50659d8bf980caf7ff85b.
- Intake and destination both identify tests/member_txn_journal.sh at d04df3c6f3ada60b9fda8c8c04230dd31e37019a; the map claims 01dc9c65ae9d74eaafb403d47aebcd20edd14390.
- tests/voucher_txn_journal.sh exists at destination blob 4277a56af800b930135745bb942d62b6d580cb99 and appears in intake, but has no migration-map row.
- Intake pins source commit 6d4c9b48 and destination branch feature/pisowifi-cleanup-stabilization. Live PR #26 instead targets integration/ecosystem-nonproprietary-candidate-20261111 at b382d233. The intake does not describe the live PR branch.

### License / NOTICE provenance

The pinned source tree contains nine LICENSE/NOTICE paths; COE #26 contains four. Four mapped counterparts are exact: PisoWiFi project LICENSE, rootfs qrcode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE. Five source artifacts lack exact destination counterparts at their routed paths: repository-root NOTICE.md, BlazeRentalLauncher/LICENSE, jsqr vendor LICENSE, UI qrcode LICENSE and UI Tabler LICENSE. This is provenance evidence, not legal approval.

All five COE #26 candidate workflows remain CANCELLED: #43096752563, #43096752800, #43096752557, #43096752609 and #43096752632. Exact destination combined statuses are empty. PR #26 remains OPEN / DRAFT / FROZEN. No staging, copy, move, overwrite, cherry-pick, rebase or destination write occurred.

## 5. Private registry and repository policy dependencies

Exact Library search did not surface canonical BLAZE_PROJECT_REGISTRY_v11_20261027.json or newer corrections. No Google Drive connector is exposed in this runtime; no older registry snapshot was substituted and no private Drive content or IDs were published.

AGENTS.md at main blob d8777e3b58efc41caa5aa3c969c932aee9103d5f requires the cloud artifact policy and verified storage handover from the legacy BlazingSystems/BlazingSystems repository. Both linked file fetches failed to return readable content and remain NOT READ / BLOCKED. Repository administration must restore the canonical documents or provide authorized current copies.

CORE source remains reserved per the explicit ownership boundary; no CORE/RENTAL/PISONET/HARDWARE/QA/RELEASE source branch was modified. The automation inventory surfaced a separate active Blaze Hourly Production Development task assigned to PHX-HARDWARE; no competing CORE implementation or automation change was started.

## 6. Test execution classification

- Exact GitHub refs, PR metadata, issue #172/#266/#177, role PRs, owner CI, recursive trees, file blobs and route manifest: READ.
- Exact source/destination route, test and license comparisons: performed in-memory against non-truncated GitHub tree/blob results.
- HARDWARE #362 focused, Mbed, Full and Native results: existing GitHub Actions inspected; no Master execution implied.
- Master Python suite and verify_coordination.py: NOT RUN; no authenticated local checkout is available.
- Master #288 exact-head workflow runs and combined statuses: NONE.
- Native COM, physical hardware, real power cuts, 30-device/24-hour soak and production financial migration: NOT TESTED.

## 7. Next exact owner actions

1. Registry custodian restores authorized access to canonical v11 and newer corrections; keep all private records private.
2. Repository admin restores the two AGENTS-linked cloud policy/handover documents and provides a non-Codex Master checkout or dedicated Master CI.
3. PHX-QA reconciles the #362 Controller config_revision and PAY-0745 assertions against the approved fail-closed semantics; do not add decoy fields or weaken guards.
4. PHX-CORE publishes the authenticated poll/receipt/disposition contract; PHX-HARDWARE owns firmware changes; PHX-QA owns independent source-linked regression verification.
5. COE integration owner reconciles the source pin, live destination branch, runtime counts, test map/hashes, firmware and all license/NOTICE counterparts before proposing any staging.
6. Role owners update cleanup #266 only when their own cleanup evidence is complete. Master inventory remains incomplete; no role checkbox is marked complete.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory. No merge, release, signer or secret provisioning, hardware flash, physical test, real payment operation, financial migration or customer cutover occurred.
