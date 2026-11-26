# PHX-MASTER UTC23 — exact Hardware, P0 pulse-loss and COE migration audit

Observed: 2026-11-26T23:39Z  
Role: PHX-MASTER — Master Auditor / Integration Coordinator  
Scope: coordination/phoenix/ only. No subsystem source, owner branch, COE destination, firmware, payment or release artifact changed. No Codex used.

## 1. Live refs read at activation

- Experiments default main: 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5.
- Experiments development blazepwifi-v0.5.3-development: aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Active v0.6 audit foundation: 2fbd2475e9f54878c316fa7cea2f228386b0e859.
- PHX-MASTER branch start: fb71a17bbe33c82da4c8286ee702289bf38ad916.
- COE default main: a6513ab4412b4c014eee2863e45cbe32d06cb243.
- Master PR #288: OPEN / DRAFT / UNMERGED, head fb71a17, base main at historical merge base f4e8a891; 242 paths under coordination/phoenix, 646 ahead / 1 behind at read time.
- COE integration PR #26: OPEN / DRAFT / UNMERGED, branch integration/ecosystem-nonproprietary-candidate-20261111, head b382d233ff06c8791b1028bed3c617cc7b670d12, 205 changed paths / 85 commits.
- Cleanup #266: OPEN, seven unchecked tracks (0/7). Control plane #172 remains the single coordination inbox.

GitHub branch metadata reports protected=false for Experiments main, development, active v0.6, and COE main. No protected signing witness is established by that metadata.

## 2. P0 coin-pulse sampling gap — issue #177

Issue #177 remains OPEN. At the exact active v0.6 source branch:

| Board | Source blob | Blocking poll | First subsequent coin sample |
|---|---|---:|---:|
| ESP8266 | 12c4bb82b6fddafe813674a0b5f692c1d3634073 | post("poll") line 354 | digitalRead(runCoinPin) line 357 |
| ESP32 | 29f1125d52ff474a0d028ad41f7af201be1f0f9d | post("poll") line 314 | digitalRead(runCoinPin) line 318 |

The issue records a source-extracted host C++ reproduction: a synchronous 3.5-second HTTP wait while the coin relay remains energized misses an active-low pulse on both boards; the simulated pending pulse/journal counts remain zero, while a no-poll control records one. This is a host simulation, not a real coin acceptor, relay, electrical, power-cut or device test.

**Master contract decision:** do not leave a coin acceptor energized while a blocking network operation prevents pulse sampling. HARDWARE owns a reversible intake-inhibit or nonblocking capture implementation; CORE owns authenticated poll/receipt/disposition authority; QA independently verifies the same exact source SHA. Any relay polarity, wiring, coin acceptor and power-loss claim requires native physical evidence. Do not rely on RAM-only ISR counts as durable credit. Do not enable positive admission from unsigned poll fields.

## 3. Current Hardware #355 — exact final head and CI

Live PR #355 docs HEAD: fa33bd1841494e0c271f99b18fbe244546ebd0b9.  
Hardware handover identifies firmware logic commit cadf8605 and source/test code head ba24c441.

Exact current-head evidence:

- Poll/intake-deny and config-persistence run #45907943770: PASS.
- Mbed TLS 3/4 matrix #45907943783: source-contract plus core 3.3.13 and 4.0.0, 3/3 PASS.
- Full run #45907943784: CI-0701 and handover freshness PASS; 14/14 target/platform builds PASS, including ESP32 and Android; validation FAILS at QA-owned tests/controllers.sh:21, which requires config_revision.
- Native synthetic run #45907943785: FAILS at QA-owned PAY-0745 assertion requiring active clearPending(true/false) callsites.

Exact source inspection: current #355 ESP32 blob fcf26a50cd3238941caf918a849c30ca66f4ce4b and ESP8266 blob 9f0f4829cf57a6a12f4d940b051f17035e0a1670 contain neither config_revision nor response_sig nor active clearPending(true/false) calls. The inherited controllers.sh blob 53a7af25fdee9a650e10e870c4204e0fb43239c requires sig (line 15) and config_revision (line 21); the sequence assertion blob 301d6d9287b7a059595e541ab570b9b4dd8fe226 requires both active pending-clear calls. The candidate remains deny-only. QA and CORE must reconcile those assertions with the approved authenticated contract; do not add unsigned fields or unsafe pending clears merely to turn CI green.

The PR body still carries an older UTC21 head pin; the latest Hardware UTC22 PR comment correctly records fa33bd / ba24c441 / cadf8605. Hardware owns refreshing its body and handover. No physical NVS/power-cut/electrical acceptance is implied.

Related Hardware stack:
- #354 at fc842342: poll #45864684458 PASS, Mbed #45864684325 PASS, Native #45864684295 FAIL, full build #45864684497 FAIL.
- #353 at f527b33c: Relay #45871096516 PASS, Quarantine #45871096480 PASS, Full #45871096425 FAIL.

## 4. Role PR and CI reconciliation

| Owner | Current PR head(s) | Exact-head evidence and boundary |
|---|---|---|
| CORE | #252 c82705f2 | Build #42698139210 PASS; not financial/native acceptance. CORE source remains owner-reserved and is separately continued by its own automation. |
| RENTAL | #328 10fc200b | API21/23 #45622918364, auth/installer #45622918551 and APK identity #45622918340 PASS; shared build #45622918468 FAIL. |
| PISONET | #255 d01fd164 | Windows synthetic #42462978704 PASS; native COM acceptance NOT TESTED. |
| HARDWARE | #355 fa33bd18; #354 fc842342; #353 f527b33 | Exact runs listed above. |
| QA | #290 5c29d159; #292 75a3f66d | #290 Windows synthetic #43633486963 PASS; #292 has no exact-head PR workflow run. |
| RELEASE | #242 36c0d0bb; #291 bf339a76 | No exact-head PR workflow runs or combined statuses returned for either current head. |
| COE RELEASE | #35 bc57ba8e | Case guard #45897198239 PASS; sandbox #45897198204 FAIL; shared Hardware/contracts #45897198326 FAIL. |
| COE CORE | #45 9d76a134 | Overlay #44295049727 and case guard #44295049903 PASS; contract vectors only, not production finance. |
| COE INTERCON | #49 aeb8ff11 | Stage 5.1 bridge #44646341873 and case guard #44646341992 PASS; shared Hardware/contracts #44646341922 FAIL. |

No owner branch was edited. The separate CORE continuation was not duplicated or taken over.

## 5. COE #26 — exact migration intake and destination audit

The current route manifest is blob e4db324315a1b3543fec17a148fbf960170fcb29: 11 routes, DRAFT_REVIEW_ONLY, PHX-MASTER target null. Its source_ref f4e8a891 is a historical reference, not the current Experiments main. The broad Rental parent route remains manual-file-mapping-only and copy_permitted=false.

COE #26 SOURCE_INTAKE.json blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f (schema 8) pins source commit 6d4c9b487af4d768c4d7627654d119417fcc6e00 and destination branch feature/pisowifi-cleanup-stabilization. The live PR #26 branch is integration/ecosystem-nonproprietary-candidate-20261111: the branch pins disagree.

| Exact comparison | Source | COE #26 destination | Result |
|---|---|---|---|
| Root tests | 150 files | 19 files | 4 common: 2 byte-identical, 2 divergent; 146 source-only, 15 destination-only |
| Board Python labs | 11 | 0 | NOT IMPORTED |
| Board firmware files | 17 | 2 sketches | Incomplete board-side import |
| ESP32 sketch blob | fcf26a50cd3238941caf918a849c30ca66f4ce4b | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 | DIFFERENT |
| ESP8266 sketch blob | 9f0f4829cf57a6a12f4d940b051f17035e0a1670 | c8be98f72596681e36a3ad1f8939bf8046c96887 | DIFFERENT |

The four common root tests are portal.sh and security.sh (identical), config.sh and integration.sh (divergent). The 15 destination-only test names and 146 source-only paths are recorded by the exact recursive-tree comparison; no test identity is inferred from filenames alone.

SOURCE_INTAKE has 61 runtime rows: actual 46 byte_identical and 15 derived_cleanup_review_required_real_router_test; its declared summary says 47 and 14. Its test inventory contains only four rows (two exact, two derived), which does not reconcile the 150-file source test tree to the 19-file destination test tree.

Licence/NOTICE readback:
- experiment/openwrt/BlazePwifi/LICENSE and Pisowifi/LICENSE are exact blob 1ee55b94183417be977ca287cd7391f9a6f7e721.
- QRCode LICENSE and TailAdmin LICENSE/NOTICE counterparts match exactly.
- Source root NOTICE.md blob f6d92cd21465312be5993631fe26977219be0fb9 is absent from COE #26.
- Source Tabler LICENSE, BlazeRentalLauncher LICENSE and test-vendor jsQR LICENSE have no corresponding destination files.
- No complete licence/NOTICE clearance is claimed.

At exact COE #26 head b382d233, five workflows are queued (case-collision, Pisonet Windows synthetic, Hardware/shared contracts, Rental standalone, PisoWiFi overlay); all five currently have zero jobs. The commit has zero check-runs. QUEUED is not PASS.

**Decision:** COE #26 remains FROZEN. No staging, copying, moving, cherry-picking, overwriting, rebasing or migration proposal is authorized. The COE integration owner must reconcile source/destination branch pins, exact blobs, all test identities, licenses/NOTICE, intake counts and completed exact-head CI before any file-level staging review.

## 6. Tool and external-evidence limits

- The private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not recovered. The exposed Library listing/search surfaced older v3-v7 registry snapshots only; none was substituted. No direct Google Drive connector is available in this execution surface. No private registry contents, IDs or Drive links are published.
- Git ls-remote failed because github.com DNS could not resolve. The Master Python suite and verify_coordination.py were NOT RUN. This is not a test pass.
- 19/19 read-only source/tree/manifest assertions passed, including exact test identities, route constraints, intake discrepancy, zero COE check-runs and seven unchecked cleanup items. These are structural audit assertions, not product tests or CI.
- Cleanup #266 remains OPEN / 0-of-7.

## 7. Next exact owner actions

1. HARDWARE and QA/CORE reconcile the P0 poll-before-sample pulse-loss path, deny-only controller assertions and pending-disposition semantics without weakening fail-closed behavior.
2. HARDWARE refreshes #355 body/handover to fa33bd / ba24c441 / cadf8605 and obtains exact-head reruns after owner changes.
3. COE integration owner resolves #26 branch pins, firmware blobs, 150-vs-19 test identity, 11 missing board labs, intake counts and licence/NOTICE gaps; then obtains executed exact-head CI.
4. Registry custodian supplies v11 and newer corrections through an authorized private Drive connector.
5. RELEASE refreshes #242/#291 and obtains exact-head CI; QA owns independent verification.
6. MASTER reruns the coordination suite when an authenticated checkout or repository CI execution path is available.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory. No real payment, production signing, merge, release, flash or physical test occurred.
