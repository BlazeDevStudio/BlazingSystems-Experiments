# PHX-MASTER UTC20 — exact-head, migration-map and governance revalidation

**Audit timestamp:** 2026-11-28T20:34:16Z  
**Task ID:** PHX-MASTER-20261128T20Z-HW380-COE26-REVALIDATION  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, migration provenance and integration matrix only  
**Starting Master head:** a4630ce90f06d38684721c3d01f608eac84517c0  
**Scope:** coordination/phoenix only. No CORE, RENTAL, PISONET, HARDWARE, QA or RELEASE source branch was changed. No COE destination, hardware, payment, signer, secret or production state was changed.

## 1. Instructions and control plane re-read

- Read the uploaded 00_MASTER_PROJECT_PHOENIX(1).txt, latest README_FIRST(20261114-191912).md and COMMUNICATION_PROTOCOL(3).md.
- Read Experiments root AGENTS.md at main blob d8777e3b58efc41caa5aa3c969c932aee9103d5f.
- Read the linked Cloud Artifact Policy at BlazeDevStudio/BlazingSystems main blob 5e503925750c4e511314e4b7624579d82f60aae2 and Cloud Storage Recovery Handover blob a15f14cb3baf46424b820e1a921462794422f06b.
- CONTROL PLANE #172 remains OPEN. The latest PHX-MASTER checkpoint before this scheduled UTC hour is UTC19 comment #7244973542. A current-date/current-hour PHX-MASTER UTC20 checkpoint was not present before this run.
- Cleanup issue #266 remains OPEN; all seven cleanup tracks remain unchecked (0/7).
- P0 issue #177 remains OPEN. Its body pins 9df0a7e7, but the actual active v0.6 audit-foundation branch is 2fbd2475e9f54878c316fa7cea2f228386b0e859. The issue-body pin is stale.

## 2. Exact live repository refs

| Ref | Exact SHA |
|---|---|
| Experiments main | 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 |
| Experiments development (blazepwifi-v0.5.3-development) | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Active v0.6 audit foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Master phoenix/master-coordination before this commit | a4630ce90f06d38684721c3d01f608eac84517c0 |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |

Master PR #288 remains OPEN / DRAFT / UNMERGED. Its base is main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b; live compare is 722 ahead / 1 behind with merge base f4e8a891. The 278 existing changed paths are all under coordination/phoenix/. The PR's mergeable flag is not an approval or release gate.

OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29, schema v1, 11 routes, DRAFT_REVIEW_ONLY; PHX-MASTER source is coordination/phoenix/ and its target is null. The manifest was not modified.

Branch-protection detail reads returned 403 for Experiments main, Experiments development and COE main. Effective protection/required checks remain UNKNOWN; the Master branch protection endpoint could not be resolved by the connector.

## 3. HARDWARE #376–#380 exact-head refresh

PR #380 remains OPEN / DRAFT / UNMERGED, based on #377@95ace1236c2b3e4816515c372edd4853ceeed064. Its current docs/PR head is 5297760322c3752878087d38b784ee8c715db6f2; its source/test SHA remains 83fc27e474064f2ed429332b8a14fa8ffb66784c.

Exact compare from previously tested docs head a4ec03835fb8ad3483d0447d105436f0f38071e3 to current head 5297760322c3752878087d38b784ee8c715db6f2 is one commit and one added file only: experiment/openwrt/BlazePwifi/docs/handover/2026-11-28-hw-master-canonical-pin-380-utc19.md. No source or test file changed.

| Exact current-head workflow | Result |
|---|---|
| [Poll Intake Deny #46182701890](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46182701890) | PASS |
| [ESP32 Mbed TLS 3/4 #46182701872](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46182701872) | 3/3 PASS |
| [Full build #46182701931](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46182701931) | FAIL |
| Native Synthetic Journal | NOT RUN; current docs-only path does not match its workflow filter |

The Full run failed job 141095693934 at step 14, Controller protocol parity. The 14/14 firmware target/platform jobs passed before the parity failure; downstream update bundle, simulations, signing and publication stages were skipped. This is exact-head CI, not physical hardware acceptance.

| PR | Exact head | Exact-head CI disposition |
|---|---|---|
| #376 | 0f5968b232f411943c4be3a4d4911a0da4f83fff | Poll, Mbed 3/4 and Full PASS; signing/publication not evidence of acceptance |
| #377 | 95ace1236c2b3e4816515c372edd4853ceeed064 | Poll/Mbed PASS; Native PAY-0745 FAIL; Full Controller parity FAIL |
| #378 | 3f67ba41dc3e087f868d3c57f6604e69f7a0e17b | Poll/Mbed PASS; Full CANCELLED; stale parent; mergeable=false |
| #379 | 5ac75dbb53bc36abc161fb276b6e7e80534e9b28 | Poll/Mbed PASS; Full Controller parity FAIL |
| #380 | 5297760322c3752878087d38b784ee8c715db6f2 | Canonical combined DRAFT child of #377; current Poll/Mbed PASS; Full parity FAIL |

Master keeps #380 as the integration-order candidate only. Preserve #378/#379 OPEN and unmerged for history; #376 remains separate. HARDWARE owns firmware/handover edits; Master does not rewrite them.

## 4. P0 source order and controller boundary

Active v0.6 source was read at exact branch SHA 2fbd2475e9f54878c316fa7cea2f228386b0e859.

- ESP8266 sketch blob 12c4bb82b6fddafe813674a0b5f692c1d3634073: timeout line 263; synchronous post("poll") line 354; first digitalRead(runCoinPin) line 357.
- ESP32 sketch blob 29f1125d52ff474a0d028ad41f7af201be1f0f9d: timeout line 230; synchronous poll line 314; first digitalRead(runCoinPin) line 318.

Both sketches still poll before their first coin sample. This is source-order inspection, not a physical pulse test. No coin slot, relay, device or money state was operated.

CORE owns the canonical versioned authenticated controller/configuration and receipt/disposition producer contract. HARDWARE owns its consumer and deny/inhibit behavior. QA owns semantic fail-closed/controller-parity tests. The #380 Full failure remains QA-owned Controller protocol parity; do not add decoy config_revision or invented response_sig fields and do not infer positive admission.

## 5. Current role PRs and CI

| Role / PR | Exact head | Exact-head evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | [Build #42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS |
| RENTAL #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | [Build #43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) and [native auth #43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | [Build #45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL; API21 smoke #45622918364, native auth/recovery #45622918551 and APK identity #45622918340 PASS |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | [Windows Release #42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | [Windows synthetic #43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No exact-head workflow run returned |
| RELEASE #291 | bf339a76964a1abe2412fac45392fe06a8e66418 | No exact-head workflow run returned; mergeable=false |

Supporting COE owner PRs:

- RELEASE #35 at bc57ba8e: case-collision guard PASS; ImageBuilder sandbox and Hardware/Shared Contracts FAIL.
- CORE #45 at 9d76a134: PisoWiFi Overlay & Shell and case-collision checks PASS; durable ledger epoch/sequence authority and independent financial acceptance remain blocked.
- INTERCON #49 at aeb8ff11: case-collision and Stage 5.1 router bridge workflows PASS; Hardware/Shared Contracts FAIL.

CORE source remains owner-only. No parallel CORE work was started.

## 6. COE #26 exact-tree migration/provenance gate

COE main remains a6513ab4412b4c014eee2863e45cbe32d06cb243. PR #26 remains OPEN / DRAFT / FROZEN at b382d233ff06c8791b1028bed3c617cc7b670d12, branch integration/ecosystem-nonproprietary-candidate-20261111. Its SOURCE_INTAKE pins source commit 6d4c9b487af4d768c4d7627654d119417fcc6e00, but its destination branch field still says feature/pisowifi-cleanup-stabilization.

Recursive source and candidate Git trees were complete and non-truncated: 2,391 source entries and 286 candidate entries.

- Runtime: 61/61 source/destination Git blob and mode identities match. Actual row classifications are 46 byte-identical / 15 derived. SOURCE_INTAKE summary remains stale at 47/14.
- Tests: four original plus fifteen derived = 19 manifest entries. All 19 source/destination test blobs and modes match the exact trees. MIGRATION_MAP contains only 18 test rows (four original plus fourteen derived); tests/voucher_txn_journal.sh is missing from the map.
- Two map hashes are stale: run_focus.sh map value fa1f4f2c6393504499d50659d8bf980caf7ff85b versus current destination blob 2b7b861ec63cf811d18d0e63b11a65efd1bec0e9; member_txn_journal.sh map value 01dc9c65ae9d74eaafb403d47aebcd20edd14390 versus current destination blob d04df3c6f3ada60b9fda8c8c04230dd31e37019a.
- Four in-scope legal artifacts match source/destination blob and mode exactly: Pisowifi/LICENSE, vendor/qrcode/LICENSE, vendor/tailadmin/LICENSE and vendor/tailadmin/NOTICE.md.
- All five exact-head PR #26 workflows remain CANCELLED: Rental Standalone, Hardware & Shared Contracts, PisoWiFi Overlay & Shell, Case-collision guard and Pisonet Windows synthetic CI.

The OWNERSHIP_ROUTES source_ref remains historical f4e8a891 while SOURCE_INTAKE pins 6d4c9b48. These are different provenance fields and must not be silently normalized. The stale destination branch pin, stale count, missing test-map row and two hashes require owner correction and exact-head CI before any staging proposal. No copy, move, cherry-pick, overwrite, rebase, staging or destination write occurred.

## 7. Governance, registry and access blockers

- Cleanup #266 remains OPEN / 0-of-7. P0 #177 remains OPEN.
- Private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not recovered. Exact Library search returned historical registry generations only; no Google Drive connector/action is exposed in this runtime. Per the Cloud Artifact Policy, registry and sync ledger access is required before any mirror or artifact operation. No old registry was substituted, no private ID/content was copied, and no Drive write occurred.
- Branch-protection detail reads returned 403 for Experiments main/development and COE main; effective required checks remain UNKNOWN.
- No automation enumeration/write was used. CORE remained read-only and no competing CORE worker or branch was started.

## 8. Validation classification

**Read-only GitHub tree/API assertions:** source and candidate trees non-truncated; 61/61 runtime identities match; 19/19 test identities match; 4/4 in-scope legal identities match; the manifest count, migration-map row count and two hash discrepancies were independently identified.

**CI evidence:** exact-head workflow results were fetched from GitHub; Master did not trigger or rerun those workflows.

**Master repository tests:** verify_coordination.py, test_verify_coordination.py, architecture tests, migration-map tests and full Master suite were NOT RUN. No authenticated non-Codex local checkout is available. No Master Actions run was returned for starting head a4630ce90f06d38684721c3d01f608eac84517c0.

## 9. Next owner actions

1. HARDWARE refresh #380's handover/description to current head 52977603 and coordinate the Controller protocol parity failure with QA; no merge.
2. CORE publish the canonical versioned authenticated controller/configuration envelope.
3. QA resolve semantic Controller parity and PAY-0745 with source-exact negative tests.
4. COE integration owner correct SOURCE_INTAKE counts, add the voucher test-map row, repair two hashes and refresh the destination branch pin; then rerun all five candidate workflows.
5. Registry custodian provide authorized access to v11 and newer corrections through the private Drive mirror.
6. Repository administrator verify branch protection and provide a non-Codex validation checkout.

## 10. Release disposition

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.

No merge, release, signing, secret provisioning, flashing, physical test, real payment operation, financial migration or customer cutover occurred.
