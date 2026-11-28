# PHX-MASTER UTC18 — exact owner heads, release handover gate and COE #26 provenance

**Read time:** 2026-11-24T18:29:01.314Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Branch:** phoenix/master-coordination  
**Starting HEAD:** e793eb6a820a032537d54ee09c4526a51ad608c5  
**Base:** main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b  
**PR #288:** OPEN / DRAFT / UNMERGED  
**Execution:** strict NO CODEX

## 1. Exact repository and control-plane state

- Experiments main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Development branch blazepwifi-v0.5.3-development: aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Master starting HEAD: e793eb6a820a032537d54ee09c4526a51ad608c5; PR #288 has 200 changed paths, all under coordination/phoenix/.
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243.
- COE integration PR #26: b382d233ff06c8791b1028bed3c617cc7b670d12, OPEN / DRAFT / FROZEN, 205 changed paths.
- CONTROL PLANE issue #172: OPEN. Cleanup issue #266: OPEN, 0/7 tracks complete.
- OWNERSHIP_ROUTES.json: blob e4db324315a1b3543fec17a148fbf960170fcb29; 11 routes; DRAFT_REVIEW_ONLY; PHX-MASTER target null.

## 2. HARDWARE #349 — current handover and exact CI

**PR #349:** OPEN / DRAFT / UNMERGED. Base #347: 960184670379f01e20f0e7e8bc23b3e5eedacd3f.

- Source/test commit: 32c026538e737870ea8bb1e22143e438f9d61f7a.
- Final handover/docs/PR head: 66f6d101f21d8193466105da7677e3afe0ad92c3.
- Current handover blob: ed9246a975d1854f0554dd3b6fcc580a82aa30e6 at experiment/openwrt/BlazePwifi/docs/handover/2026-11-24-hw-json-fixture-runner-consolidation-utc18.md.
- Latest source/test commit is narrowly test-lab cleanup: poll_json_array_primitive_lab.py now calls shared cpp_fixture_runner.run_cpp_fixture; duplicate subprocess/tempfile compile logic was removed while C++17 flags and 30s/10s timeouts were preserved.
- Aggregate PR #349 still includes earlier firmware sketch edits; do not read the latest test-only commit as proof that the entire PR is test-only. Current ESP32 sketch blob a9a1c2fecb001d71f8f22b43952edbd160aacaf8 differs from COE #26 blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422. Current ESP8266 sketch blob 2f87a9de84ac53dbb0d2718b5c79a4662b63de8f differs from COE #26 blob c8be98f72596681e36a3ad1f8939bf8046c96887.
- PR description remains stale: it still pins source/test aa9ac766 and handover/docs d9adf204, despite current source/test 32c026 and final head 66f6d101.

Exact-head CI:
- Relay #45457011407 — SUCCESS.
- Quarantine #45457011596 — SUCCESS.
- BlazePwifi build #45457011223 — FAILURE at tests/controllers.sh: Missing poll signature check in the ESP8266 sketch. All 13 firmware targets plus Android passed (14/14); validation-dependent simulation, update, candidate, signing and publication stages skipped.
- The assertion is an unresolved CORE producer / QA contract mismatch. No response signature may be fabricated, no member endpoint signature may be reused for poll, and deny-default must not be weakened.
- Physical coin/relay acceptance, 150 power cuts and 30-device/24-hour soak remain NOT TESTED.

## 3. RELEASE #291 — newer workflow head and current handover failure

**PR #291:** OPEN / DRAFT / UNMERGED. Base #242: 734b89d9e7792247e8376335c3f3685500ab3f89.

- Source/test anchor in the current owner handover: a004c647e67f90269a9149f918887622bb8cc5e8.
- Current PR/workflow head: 32487a5720040b8fb8374a7ab6efd224aeac7207.
- Latest commit 32487a5 changes only .github/workflows/blazepwifi-v053-release.yml, correcting three escaped GitHub expressions for GH_TOKEN, SHA and SIGN_RUN.
- Current PROJECT_HANDOVER.md blob: ce00cabad64364c2255dc5a5a2fc29f4af0bcb17.
- Current CURRENT_STATE.md blob: 85dd3c1e9254d947c4e75daaeaf3351ef3e105e3.
- Current CHANGE_LEDGER.md blob: 7f0b0644e19bc575cf1c8b1ab7c2b96a7094a0c4.
- PR description still reflects older UTC17 documentation/source pins; it has not been reconciled to current head 32487a5.

Exact-head CI at 32487a5:
- Windows #45458949767 — FAILURE at the mandatory handover gate: source/workflow changes newer than PROJECT_HANDOVER.md; last checkpoint commit 0406ce0b0c6292a415b6318c7691c0de80b83519. Build-windows and publisher skipped.
- BlazePwifi build #45458949702 — CI-0701 docs-only sync proof PASS; validate FAILURE at the same PROJECT_HANDOVER.md freshness gate. Target jobs were still in progress at readback; no terminal matrix result is claimed. Downstream simulation/update/signing/publication stages skipped.
- ESP32 compatibility #45458949687 — PENDING at readback.
- Earlier Windows/build runs at head 76da627 also failed handover freshness; their result is superseded by the newer exact-head run above.
- The canonical handover must be updated by its owner after the workflow change. Do not bypass the freshness gate. PISONET retains its two test paths in the accumulated #291 diff; QA independently reviews.

## 4. COE #26 — exact source/destination provenance

Current source/test tree at #349 source/test SHA 32c026: 2,524 entries. Historical SOURCE_INTAKE source pin 6d4c9b487af4d768c4d7627654d119417fcc6e00: 2,391 entries. COE #26 destination tree b382d233: 286 entries.

### Runtime intake
SOURCE_INTAKE.json blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f (schema 8) contains 61 runtime rows. All 61 recorded source Git blobs and modes match the pinned historical source tree; all 61 recorded destination blobs and modes match the exact COE #26 tree.

The summary is wrong: it says 47 byte-identical / 14 derived. Recomputing the 61 rows gives 46 byte-identical / 15 derived. Compared with the current #349 source tree, only 33 of the historical source blobs remain unchanged; 20 have changed and 8 are missing. This is source drift, not a destination mismatch.

### Tests
- Source tests/ contains 47 files; destination Pisowifi/tests/ contains 19.
- Exact blob/mode matches: 1.
- Divergent same-path tests: config.sh, integration.sh and security.sh.
- Source-only: 43; destination-only: 15.
- JSON derived_tests contains 15 entries; MIGRATION_MAP.md records 14 derived/local test rows.
- run_focus.sh hash differs between JSON (2b7b861ec63cf811d18d0e63b11a65efd1bec0e9) and map (fa1f4f2c6393504499d50659d8bf980caf7ff85b).
- member_txn_journal.sh hash differs between JSON (d04df3c6f3ada60b9fda8c8c04230dd31e37019a) and map (01dc9c65ae9d74eaafb403d47aebcd20edd14390).
- voucher_txn_journal.sh exists in JSON at blob 4277a56af800b930135745bb942d62b6d580cb99 but has no MIGRATION_MAP row.

### Board source and licenses
- Source ESP32 subtree: 17 entries; destination Hardware/esp32: 2. Source-only entries include 15 labs/docs/helpers; the sketch blobs differ as recorded above.
- Source ESP8266 subtree: 49 entries; destination Hardware/esp8266: 2. Source-only entries include 47 labs/docs/helpers; the sketch blobs differ as recorded above.
- Exact license/notice matches: PisoWiFi product LICENSE, QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE.
- Missing destination counterparts: Experiments root NOTICE.md and Tabler LICENSE.
- BlazeRentalLauncher LICENSE is a separate RENTAL route, not a PisoWiFi copy.
- No jsqr path exists in either exact tree.

COE #26 has five workflows queued and zero completed jobs/statuses. Candidate remains FROZEN. No staging, copy, move, overwrite, rebase, cherry-pick or destination write occurred.

## 5. Other owner PRs and CI at exact heads

| Owner | PR / exact head | Current CI disposition |
|---|---|---|
| CORE | #252 c82705f2de865c89ab733b10efa84f26f56a5cc4 | Scoped BlazePwifi build #42698139210 PASS |
| RENTAL | #328 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | APK identity and API smoke PASS; BlazePwifi build #44782114390 FAIL |
| PISONET | #255 d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Synthetic Windows #42462978704 PASS |
| HARDWARE | #347 960184670379f01e20f0e7e8bc23b3e5eedacd3f | Quarantine, Relay and build runs FAIL |
| HARDWARE | #348 eb7afcb2ba0d1e84054c052c8b129cb51a91d062 | Focused controller header PASS; build #45352513177 FAIL |
| HARDWARE | #349 source 32c026 / docs head 66f6d101 | Relay/Quarantine PASS; full build validation FAIL |
| QA | #290 5c29d15994cee1279058f1eca12f2a3180704292 | Synthetic Windows #43633486963 PASS |
| QA | #292 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered runs |
| RELEASE | #291 source anchor a004c647 / current head 32487a5 | Windows freshness FAIL; build validate FAIL; target matrix incomplete; compatibility pending |
| COE RELEASE | #35 e7801818b00854f34a5a88955d979c601ec96404 | Case guard PASS; hardware/shared CI and sandbox FAIL |
| COE CORE | #45 9d76a134c1f6512aa40c20ec4d247306a71a8cce | PisoWiFi overlay/shell and case guard PASS |
| COE | #49 aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage 5.1 and case guard PASS; shared hardware CI FAIL |

The separate Blaze Production Continuation remains the CORE owner. PHX-MASTER did not modify CORE, RENTAL, PISONET, HARDWARE, QA or RELEASE source branches.

## 6. Access, tests and limitations

- Private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not available. A complete Library listing (8 pages) surfaced only the base registry and versions v3-v7; no v11 or newer correction. No Google Drive connector is exposed. No older snapshot was substituted; no private registry content is published.
- Root AGENTS.md, README_FIRST, COMMUNICATION_PROTOCOL and 00_MASTER_PROJECT_PHOENIX(1).txt were read. The AGENTS-linked Cloud Artifact Policy and Cloud Storage Handover could not be retrieved through the connected GitHub surface.
- GitHub recursive trees, exact blob/mode comparisons, owner PR heads, Actions statuses and failed-job logs were inspected.
- A local git clone attempt failed because github.com DNS could not resolve. Master Python unittest suite and verify_coordination.py are NOT RUN; Master PR Actions have zero runs/statuses. No Master test pass is claimed.
- Main, development and COE main branch metadata report protected=false. Master branch protection is not confirmed by this read.

## 7. Next exact owner actions

1. PHX-CORE publishes the approved versioned register/poll response contract and golden vectors, and refreshes the canonical shared handover at an exact source/workflow SHA.
2. PHX-QA independently reconciles Missing poll signature check without weakening deny-default.
3. PHX-HARDWARE updates PR #349 description to source/test 32c026 and final handover/docs head 66f6d101; do not claim full validation until exact-head CI is terminal and the contract is approved.
4. PHX-RELEASE refreshes PROJECT_HANDOVER.md after workflow head 32487a5 and reruns Windows/Build; PISONET and QA retain their existing review ownership.
5. COE integration owner corrects SOURCE_INTAKE 46/15 counters, the two stale test hashes and the missing voucher test row; then repeats exact-tree/license/CI review.
6. Registry custodian provides authorized Drive v11/newer-correction access; repository administrators establish effective branch protection; an authorized human runner executes Master Python tests and verify_coordination.py.

**Final disposition:** PR #288 remains OPEN / DRAFT / UNMERGED. COE #26 remains FROZEN. PRODUCTION NO-GO. No merge, release, signer provisioning, secret write, hardware flash, physical test, real-payment operation, customer cutover or financial migration occurred.
