# PHX-MASTER UTC16 — exact-head owner CI, interface boundary, and COE #26 provenance

**Observed:** 2026-11-26T16:33:57Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Execution:** Strict NO CODEX.  
**Starting Master HEAD:** 6bdb731b5ca5af1dfa7cb95134f8ed8ff71d96aa on phoenix/master-coordination.

## 1. Exact refs and authority

The uploaded master prompt, latest README_FIRST, COMMUNICATION_PROTOCOL (BLAZE-COMMS/1), Experiments AGENTS.md, canonical cloud artifact policy and recovery handover, live #172/#266, Master PR #288, routing manifest and COE #26 were re-read.

| Ref | Exact HEAD |
|---|---|
| Experiments main | 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 |
| Legacy v0.5.3 development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Active v0.6 development | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Master coordination starting HEAD | 6bdb731b5ca5af1dfa7cb95134f8ed8ff71d96aa |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE #26 integration branch | b382d233ff06c8791b1028bed3c617cc7b670d12 |

PR #288 is OPEN / DRAFT / UNMERGED, 617 ahead / 1 behind main, merge base f4e8a891aed8af86d5fd315d28750a0ac3a7372b. Its 237 existing changed paths are all under coordination/phoenix/. It reports mergeable=true but remains draft and is not authorized for merge. Master Actions and combined statuses at starting HEAD: zero runs / zero statuses.

The latest prior Master checkpoint is #7196879951 (UTC15); latest UTC16 message is RELEASE #7197545127. No PHX-MASTER checkpoint for 2026-11-26 UTC16 was found. Cleanup #266 remains OPEN, 0/7; the Master cleanup-first inventory is incomplete.

## 2. Routing authority

OWNERSHIP_ROUTES.json blob e4db324315a1b3543fec17a148fbf960170fcb29 declares 11 routes, DRAFT_REVIEW_ONLY, source_ref f4e8a891aed8af86d5fd315d28750a0ac3a7372b, COE candidate PR #26 at b382d233ff06c8791b1028bed3c617cc7b670d12, and PHX-MASTER target null. The source_ref is a historical merge-base anchor, not current main or active v0.6. It remains unchanged because COE intake pins another historical source commit. The manifest is not a copy/move authorization.

## 3. Owner PR heads and CI

| Owner / PR | Exact head | Current evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Scoped build #42698139210 PASS; not financial acceptance. |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | API/auth/APK focused #45622918364/#45622918551/#45622918340 PASS; shared build #45622918468 FAIL. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows synthetic #42462978704 PASS; native COM NOT TESTED. |
| HARDWARE #340 | f70f6af78c64ef86ba0f631faeb02b6cb6eb2725 | Six workflows PASS; Full #45747758154 = 26 successful jobs / 4 production skips. |
| HARDWARE #353 | 5a5f31908acf88272fe890ca64f95255c35ed7aa | Relay #45852949294 FAIL; Quarantine #45852949605 FAIL; Full #45852949273 FAIL. PR body stale at docs/source-test refs cb1787ac / ed2f77d. |
| HARDWARE #354 | bbb209f55ddcd48f248eb8d700629db8754dc13a | Focused #45836227697 + Mbed TLS #45836227855 PASS; Full #45836227694 and Native #45836227876 FAIL. Candidate remains deny-only. |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Windows synthetic #43633486963 PASS; native COM NOT TESTED. |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No exact-head PR runs. |
| RELEASE #242 | 842abd8ab29042ccdd928c1332a94770dcb6c0c7 | Updated 16:30:59Z; no exact-head CI/status; mergeable=false. |
| RELEASE #291 | bf339a76964a1abe2412fac45392fe06a8e66418 | No exact-head CI/status; mergeable=false. |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Overlay/Shell #44295049727 + case guard #44295049903 PASS. |
| COE INTERCON #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage 5.1 #44646341873 + case guard #44646341992 PASS; shared #44646341922 FAIL. |
| COE RELEASE #35 | e1ad4fad1c234976ba76a34758d1ca993a897776 | Shared #45848921260: 255 PASS / 2 skipped, then 10/10 ULA profile failures. Sandbox #45848921270: 48/48 host PASS, Bubblewrap missing / exit 125. Case guard #45848921527 PASS. |
| COE #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows queued / zero jobs; no combined statuses. |

### HARDWARE #353 exact failures

Current head 5a5f319 is based on #352 at 2fa3b7db. Relay job 140023796440 (run #45852949294) and Quarantine job 140023797532 (run #45852949605) both reach remote_config_revision_lab and fail exact-source ESP8266 and ESP32 checks with exit 13 after stale/equal/zero revision denial checks pass. Full validation job 140023957627 (run #45852949273) fails controllers.sh because the ESP8266 sketch is missing the required poll-signature check. HARDWARE owns the correction and stale PR handover.

### HARDWARE #354 deny-only boundary

Full fails because QA's controllers.sh expects config_revision in both sketches; neither candidate contains it. Native fails because v060_vendo_sequence_contract.py requires active clearPending(true/false) callsites. Each candidate has only the clearPending function declaration, no callsites, and lacks response_sig/config_revision. Do not add unsigned config consumption or pending-clear callsites to satisfy incompatible assertions. QA owns assertions; CORE owns authenticated register/poll and receipt/disposition contract; HARDWARE owns firmware.

### RELEASE ancestry

PR #242 base pin 6d4c9b487af4d768c4d7627654d119417fcc6e00 is 22 commits behind current active v0.6 HEAD 2fbd2475e9f54878c316fa7cea2f228386b0e859. PR #291 base pin 734b89d9e7792247e8376335c3f3685500ab3f89 is 13 commits behind its current parent release branch at 842abd8. Both are mergeable=false with no exact-head CI. RELEASE owns reconciliation; Master did not edit release source.

## 4. Architecture/interface contract status

At active v0.6 HEAD 2fbd2475, CGI blob db58041c0575ad0a1101d99cb85403e03c8dcb22 emits poll fields ok, insert, target_nonce, expires and controller, but no response_sig. Member snapshot/auth/mutation endpoints include response_sig; those signatures do not authenticate poll.

Active v0.6 ESP32 blob 29f1125d52ff474a0d028ad41f7af201be1f0f9d and ESP8266 blob 12c4bb82b6fddafe813674a0b5f692c1d3634073 still read insert/target_nonce and call applyRemoteConfig. This is an unsigned poll trust boundary, not an approved contract.

HARDWARE #354 deny-only source blobs are ESP32 3edbe38da543ef118b287f3e04c1601692cfa99f and ESP8266 b45eb2d0bebfc0088e1c9f506c5e94c59cf054d9. They have no response_sig/config_revision and no active clearPending callsites. Keep deny-only until CORE defines versioned response envelope, controller binding, key provisioning, freshness/replay and receipt/disposition; HARDWARE implements after approval; QA independently verifies both boards.

## 5. COE #26 exact tree and migration provenance

Complete recursive trees, all truncated=false: HARDWARE #353 2,572 entries; HARDWARE #354 2,406; COE #26 286.

| Route | Candidate | Source files | Destination files | Exact blob+mode | Divergent | Source-only | Destination-only |
|---|---|---:|---:|---:|---:|---:|---:|
| ESP32 | #353 | 16 | 1 | 0 | 1 | 15 | 0 |
| ESP8266 | #353 | 67 | 1 | 0 | 1 | 66 | 0 |
| ESP32 | #354 | 4 | 1 | 0 | 1 | 3 | 0 |
| ESP8266 | #354 | 8 | 1 | 0 | 1 | 7 | 0 |
| Vendo tests | #353 | 47 | 19 | 1 | 3 | 43 | 15 |
| Vendo tests | #354 | 150 | 19 | 2 | 2 | 146 | 15 |

Firmware blobs:
- ESP32: #353 source 8154297e30e72d82692987ed5690983df4955aea; #354 source 3edbe38da543ef118b287f3e04c1601692cfa99f; COE destination 3cc7ec54b476943dc04a8d1af5e2df5fe054e422.
- ESP8266: #353 source 2613bfc36b0ddac9dd720592d4ff37e32a891744; #354 source b45eb2d0bebfc0088e1c9f506c5e94c59cf054d9; COE destination c8be98f72596681e36a3ad1f8939bf8046c96887.
Neither destination sketch matches either current source candidate.

Record conflicts:
- SOURCE_INTAKE.json blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f is schema 8, source commit 6d4c9b487af4d768c4d7627654d119417fcc6e00, destination branch feature/pisowifi-cleanup-stabilization (not current #26 branch integration/ecosystem-nonproprietary-candidate-20261111).
- It has 61 runtime rows: 46 byte_identical / 15 derived; summary says 47 / 14. Four test records: two derived and two byte-identical. hardware_tested=false, full_ci_tested=false, source_admission_complete=false.
- MIGRATION_MAP.md blob b54fc15d83bc2269de03db8aadd0e76259fd13d9 repeats the historical source and old destination branch.
- HARDWARE_FIRMWARE_AUDIT.md blob 86c06e7574761465b80482430296eb712d985367 says sketches have not been copied, but both exist in COE #26.
- PR #26 body says P0-1 formally resolved/removed, while intake still marks hardware/full CI/source admission incomplete.

Source root NOTICE.md, BlazeRentalLauncher LICENSE, Tabler LICENSE and COE root LICENSE have no destination counterparts. PisoWiFi MIT LICENSE, QRCode LICENSE and TailAdmin LICENSE/NOTICE match exact source blobs. The 11-route manifest remains DRAFT_REVIEW_ONLY with Master target null. No destination staging/copy/move/cherry-pick/overwrite occurred.

## 6. Governance and execution limits

- Cleanup #266 remains OPEN / 0-of-7.
- Private Drive registry v11 and newer corrections were NOT RECOVERED. Library inventory surfaces v3-v7 only; no v11 or newer correction. No Google Drive connector was exposed. No older snapshot or private data was substituted/published.
- Active automation inventory surfaced Phoenix Release Hourly Development (PHX-RELEASE) and Blaze Hourly Production Development (PHX-HARDWARE). The exact separate Blaze Production Continuation / CORE title was not surfaced. CORE remains untouched and owner-reserved.
- Exact Git tree/blob comparisons, source inspection and record recounts were executed in the connected runtime; these are static audits, not repository tests.
- Master Python suite and verify_coordination.py NOT RUN. Local git ls-remote failed because the container could not resolve github.com. Master Actions/statuses at starting HEAD: zero runs / zero statuses.

## 7. Next owner actions

1. HARDWARE refreshes #353 handover to exact head 5a5f319 and fixes both remote-config revision lab failures plus the ESP8266 poll-signature validation.
2. QA corrects #354 assertions for deny-only behavior and pending-evidence preservation; CORE publishes authenticated register/poll and receipt/disposition contract before positive admission.
3. COE integration owner reconciles #26 P0-1 claim, SOURCE_INTAKE counts/branch pins, MIGRATION_MAP source pin, firmware presence/blob differences, test identities and license gaps.
4. RELEASE refreshes #242/#291 ancestry against current base branches and obtains exact-head CI.
5. Registry custodian restores authorized v11/newer-correction access; administrators verify effective branch protection.
6. Master cleanup-first inventory remains open under #266; no mass moves/deletions.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory. No merge, release, signing, secret provisioning, firmware flashing, physical test, real-payment operation, customer cutover or financial migration occurred.
