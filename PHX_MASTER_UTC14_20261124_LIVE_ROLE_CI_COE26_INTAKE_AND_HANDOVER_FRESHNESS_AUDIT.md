# PHX-MASTER UTC14 — live role CI, COE #26 intake reconciliation and handover freshness

**Updated:** 2026-11-24T14:05:18Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, migration provenance and integration matrix only  
**Status:** Coordination update committed; COE #26 remains frozen; production remains NO-GO.

## 1. Exact live references

| Item | Read-time state |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Issue-designated development | blazepwifi-v0.5.3-development @ aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Master branch at start | phoenix/master-coordination @ ba356baf4acb3921d2fd5c7373e4dd4decfaabd4 |
| Master PR #288 | OPEN / DRAFT / UNMERGED; base main @ f4e8a891; 197 changed paths, all under coordination/phoenix/ |
| Control plane #172 | OPEN; latest Master checkpoint is UTC12; issue body last updated 13:58:12Z |
| Cleanup #266 | OPEN; 0/7 tracks checked |
| Ownership manifest | OWNERSHIP_ROUTES.json @ e4db324315a1b3543fec17a148fbf960170fcb29; 11 routes; DRAFT_REVIEW_ONLY; PHX-MASTER target null |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | OPEN / DRAFT / FROZEN at b382d233ff06c8791b1028bed3c617cc7b670d12; five workflows QUEUED, zero jobs and zero commit statuses |

The root AGENTS.md blob is d8777e3b58efc41caa5aa3c969c932aee9103d5f. Its linked Cloud Artifact Policy and Cloud Storage Handover could not be retrieved through the available GitHub connector. The private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer Drive corrections were not available through the connected Library/tool surface; no Google Drive connector was exposed. Older registry snapshots were not substituted and no private registry data was copied into GitHub.

## 2. Current owner PR and exact-head CI matrix

| Owner / PR | Exact source or PR head | Exact-head evidence and interpretation |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build #42698139210 PASS, scoped. CORE source ownership untouched. |
| RENTAL #328 | 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | APK #44782114384 PASS; API #44782114393 PASS; build #44782114390 FAIL. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows #42462978704 PASS; synthetic CI only. |
| HARDWARE #345 | ca72497ed386c9ac4e50d3f811827bef51e296ad | Relay #45165015665 and Quarantine #45165015610 PASS; build #45165015859 FAIL. |
| HARDWARE #347 | 960184670379f01e20f0e7e8bc23b3e5eedacd3f | Quarantine #45299741995, Relay #45299742437 and build #45299741993 FAIL. Parent evidence is not transferred to child #349. |
| HARDWARE #348 | eb7afcb2ba0d1e84054c052c8b129cb51a91d062 | Focused header #45352513178 PASS; build #45352513177 FAIL at ESP32 mbedtls/sha256.h. |
| HARDWARE #349 | source/test 839c72ac68bb1f0a8fd9a2fc74a166cec15b624e; docs/PR 16a51a995f2c2ed52c35969f19a4adaf857c3910 | Final docs-head Relay #45407965381 PASS; Quarantine #45407965439 PASS; Full #45407965339 FAIL at QA-owned Missing poll signature check. All 14/14 firmware/platform targets plus Android pass; dependent update/simulation/candidate/signing/publication stages skip. |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Windows #43633486963 PASS. |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered workflow runs. |
| RELEASE #291 | source/test 57c0844a8b49e5bb98f84729276da7b42b0074d3; docs 350875888129132fca161e20d473276e4379b50e; current PR head 0b186e11676cd26d863b87d03e5d9b8a75e68a39 | Prior CI-0701 job 138472212729 passed 53/53 provenance tests at source/test head; final docs-head CI-0701 job 138473253594 also passed 53/53. The overall source workflow #45401855484 was CANCELLED, and the docs-head build #45402102533 / Windows #45402102471 failed at shared handover freshness. At current PR head, Windows #45408109183 and build #45408109177 still fail at CURRENT_STATE freshness; ESP32 compatibility #45408109178 PASS. Independent PR reviews: 0. |

COE owner candidates remain:
- #35 @ e7801818b00854f34a5a88955d979c601ec96404 — case-collision #45303825417 PASS; profile validation #45303825436 FAIL because all ten appliance profiles lack approved site-scoped ULA /48 authority; sandbox #45303825459 FAIL because Bubblewrap is absent (exit 125).
- #45 @ 9d76a134c1f6512aa40c20ec4d247306a71a8cce — overlay/shell #44295049727 and case-collision #44295049903 PASS.
- #49 @ aeb8ff11b2f5db9a5f86280ab62ab988245f3919 — Stage 5.1 #44646341873 and case-collision #44646341992 PASS; shared ESP32 compile #44646341922 FAIL at missing mbedtls/sha256.h.

Master PR #288 at the read-time head has zero Actions runs and zero combined statuses. COE #26 still has five queued workflows and no completed jobs or commit statuses.

## 3. COE #26 — exact pinned-source, current-main and destination audit

The candidate SOURCE_INTAKE.json is schema 8, blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f. Its pinned source commit is 6d4c9b487af4d768c4d7627654d119417fcc6e00; destination is COE PR #26 head b382d233ff06c8791b1028bed3c617cc7b670d12. All recursive trees were complete and non-truncated.

The pinned source tree has 2,391 entries; current Experiments main has 2,340; COE #26 has 286. The source rootfs tree SHA f4a923aaacf1374e90c7bab5f335efe6c6ec55cf and original tests tree SHA 7e3b16f2a981c1c8ecab3b1da0d34a82b4e44f17 exactly match the manifest's pinned tree identities.

### Runtime rows and summary discrepancy

- All 61 SOURCE_INTAKE runtime rows resolve to the exact pinned source blob, destination blob and Git mode.
- Actual classification: 46 byte-identical and 15 derived.
- Manifest summary claims 47 byte-identical and 14 derived. Its summary is off by one in both counters.
- The four original test rows all match their pinned source/destination blobs and modes: two byte-identical, two derived.
- All 15 JSON derived-test rows match their destination blobs and modes.
- MIGRATION_MAP.md blob b54fc15d83bc2269de03db8aadd0e76259fd13d9 has only 14 derived-test rows. It omits voucher_txn_journal.sh and contains stale blob IDs for run_focus.sh and member_txn_journal.sh. The JSON and destination tree agree; the map does not.

### Historical snapshot versus current source authority

The ownership routing manifest points to Experiments main @ f4e8a891, while SOURCE_INTAKE remains pinned to historical commit 6d4c9b48.

For the 61 pinned runtime paths:
- Current main still matches 33 pinned source blobs.
- 20 source blobs have drifted.
- Eight pinned source paths are absent from current main.
- Current main versus COE #26 destination: 25 exact blob+mode matches, 28 divergent paths and eight missing paths.

The historical pinned source is not the current source authority. Do not refresh or copy from either snapshot without owner review and an updated, exact provenance manifest.

### Current HARDWARE source versus COE destination

At HARDWARE #349 source/test SHA 839c72ac versus COE #26 head b382d233:
- Current source tests: 47; destination tests: 19.
- Exact same-path blob+mode: 1.
- Divergent same-path files: 3 (config.sh, integration.sh, security.sh).
- Source-only tests: 43; destination-only tests: 15.
- ESP32/ESP8266 board subtrees: 58 source files versus two destination sketches.
- Board-local Python labs/helpers: 46 source, zero destination.
- Both firmware sketch blobs differ between source and destination.

License/notice inventory: product LICENSE, QRCode LICENSE and TailAdmin LICENSE/NOTICE have exact destination counterparts. Source root NOTICE.md, Tabler LICENSE and the jsqr test-vendor LICENSE have no destination counterpart in this candidate. BlazeRentalLauncher LICENSE belongs to the separate RENTAL/android route, not the PisoWiFi destination route, and needs its own owner review. No license file was copied.

**Disposition:** COE #26 remains FROZEN. No staging, copying, moving, overwriting, rebasing, cherry-picking, destination edit or migration approval occurred.

## 4. Shared handover freshness and ownership boundaries

RELEASE #291 has 29 changed paths: 24 RELEASE-owned paths, three shared BlazePwifi handover paths and two PISONET-owned SoftTimer ReleaseSigning test paths. The two PISONET paths are PublisherMockCli.ps1 and negative-selftest.ps1; PISONET review remains required. The PR has zero independent reviews.

Exact shared handover blobs differ across current owner heads:

| Shared path | CORE #252 | PISONET #255 | RELEASE #291 |
|---|---|---|---|
| experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md | 72e8e487 | d3e66608 | 31e1fdbc |
| experiment/openwrt/BlazePwifi/docs/handover/CHANGE_LEDGER.md | df50981c | 02963d32 | e954dd70 |
| experiment/openwrt/BlazePwifi/docs/handover/CURRENT_STATE.md | 72c38aeb | 47e07b7c | 85dd3c1e |

At RELEASE #291 current PR head 0b186e116, CURRENT_STATE.md remains blob 85dd3c1e and its last checkpoint remains d85eb6a2766781b6cac1807cef461993d8216b84. The exact current-head Windows/build gates still reject newer release workflow/source changes. CORE owns canonical shared CURRENT_STATE reconciliation; RELEASE owns release workflows and exact-head reruns; PISONET owns the two SoftTimer tests; QA independently reviews.

HARDWARE #349 keeps deny-only behavior. CORE owns the authenticated register/poll producer contract and canonical bytes/vectors; QA owns independent assertion reconciliation. No signature was invented and no QA assertion was relaxed.

## 5. Governance, execution and limitations

- Experiments main, development and COE main report protected=false; both repositories' rulesets endpoints return empty arrays. Master branch effective protection remains UNKNOWN.
- The private v11 registry/newer corrections are NOT RECOVERED. No Google Drive connector is exposed; no older snapshot was substituted.
- Master Python unit tests and verify_coordination.py were NOT RUN; no authenticated local checkout is available through the connected GitHub tool surface.
- Executed audit validation: ten JavaScript assertions against complete recursive Git trees. All ten passed: exact 61 runtime rows, four original tests, 15 derived tests, historical/current-source drift counts, current #349 test identity counts and board helper counts were reproduced; the expected SOURCE_INTAKE/MIGRATION_MAP inconsistencies were detected.
- Master PR Actions and combined statuses: zero. GitHub owner Actions results above are not Master Python-suite results.
- No subsystem source, COE destination, ownership manifest, secret, signer, payment system, hardware or release artifact changed.

## 6. Next actions

1. PHX-CORE refreshes the canonical CURRENT_STATE.md and shared handover set at the exact current RELEASE source/workflow head; PHX-RELEASE then reruns Windows and full build without bypassing the freshness gate.
2. PHX-PISONET reviews the two PISONET-owned ReleaseSigning tests in #291; PHX-QA independently reviews the corrected exact-head release boundary.
3. PHX-CORE publishes the approved authenticated register/poll response contract and canonical vectors; PHX-QA reconciles the signature assertion; HARDWARE remains deny-only.
4. COE integration owner corrects SOURCE_INTAKE summary counters and MIGRATION_MAP omissions/stale hashes, then reconciles historical source against current main and completes test/license provenance before any staging review.
5. Registry custodian restores authorized v11 Drive access; repository administrators establish effective branch protection; an authorized human runner executes the Master Python suite and coordination verifier.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible financial migration tests, independent QA, native hardware acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain outstanding.
