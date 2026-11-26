# PHX-MASTER UTC18 — exact-head owner CI, COE #26 provenance and registry-access audit

Observed: 2026-11-26T18:37:27Z. Role: PHX-MASTER — Master Auditor / Integration Coordinator. Execution: STRICT NO CODEX.

## 1. Scope and source refs

This activation re-read CONTROL PLANE #172, cleanup-first #266, the uploaded Master prompt, README_FIRST, BLAZE-COMMS/1, Experiments AGENTS.md, the current Master PR and ownership manifest, the relevant owner PRs/CI, COE main/#26, and the accessible Library inventory. All changes in this report are coordination-only.

| Ref | Exact HEAD / state |
|---|---|
| Experiments main (default) | 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 |
| Active v0.6 comparison/development base | blazepwifi-v0.6.0-audit-foundation @ 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Legacy v0.5.3 development | blazepwifi-v0.5.3-development @ aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Master coordination | phoenix/master-coordination @ 0730fff529d62ae2b6c436e14cfd520025291f6c |
| COE main (default) | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration #26 | integration/ecosystem-nonproprietary-candidate-20261111 @ b382d233ff06c8791b1028bed3c617cc7b670d12 |

An unqualified branch named development does not resolve; the two named v0.5.3 and v0.6 lines above are kept distinct. Do not substitute one for the other.

## 2. Master PR and ownership

PR #288 is OPEN / DRAFT / UNMERGED at 0730fff529d62ae2b6c436e14cfd520025291f6c. The live comparison against main is 637 commits ahead / 1 behind, merge base f4e8a891aed8af86d5fd315d28750a0ac3a7372b, and 239 changed paths. The current changed-path list contains zero paths outside coordination/phoenix/. No rebase, merge or force-push was performed.

OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29: 11 routes, DRAFT_REVIEW_ONLY, PHX-MASTER target null. It still pins source_ref f4e8a891 (the PR merge base, not current Experiments main 6be5d19b) and COE candidate #26 at b382d233. The broad Rental route is manual-file-mapping-only and not copy-permitted. No route was approved or moved.

COE #26 remains OPEN / DRAFT / FROZEN, based on COE main a6513ab4, with 205 changed paths and 85 commits. Its five PR workflows remain queued with zero jobs and zero completed statuses: case-collision, Pisonet synthetic, Hardware/shared contracts, Rental standalone, and PisoWiFi Overlay/Shell.

## 3. Exact owner PR heads and CI

| Owner / PR | Current exact PR head | Exact-head CI / disposition |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build #42698139210 PASS (scoped only); no production financial acceptance implied. |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | APK identity #45622918340, API smoke #45622918364 and auth/recovery instrumentation #45622918551 PASS; build #45622918468 FAIL, including ESP32 missing mbedtls/sha256.h. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows #42462978704 PASS; synthetic only, native COM hardware not accepted. |
| HARDWARE #340 | f70f6af78c64ef86ba0f631faeb02b6cb6eb2725 | Six focused/build workflows PASS (#45747758154, #45747758162, #45747758223, #45747758240, #45747758167, #45747758309); separate candidate, not merged acceptance. |
| HARDWARE #353 | docs/PR f527b33c9e391a9a66490388d96f06d6c8761dfa; source/test 44de55a0e132cb15fdb60ecf85446e9490fa277e | Relay #45871096516 and Quarantine #45871096480 PASS; Full #45871096425 FAILS at Missing poll signature check in the ESP8266 sketch. All target jobs completing in this run are not a physical acceptance claim. |
| HARDWARE #354 | docs/PR fc842342596786e072630179acfbbc4feeb2ba02; source/test 145aac9607682071e2db05944a6f9db5aa06e524 | Poll-deny #45864684458 and ESP32 Mbed TLS #45864684325 PASS; Full #45864684497 fails QA controllers.sh because it requires config_revision in both sketches; Native #45864684295 fails the QA assertion for clearPending(true/false). Current sketches contain neither config_revision nor those clearPending callsites. Do not add unsafe behavior merely to satisfy stale assertions. |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Windows synthetic #43633486963 PASS. |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered runs returned at this exact head. |
| RELEASE #291 | bf339a76964a1abe2412fac45392fe06a8e66418 | No PR-triggered runs returned at this exact head; mergeable=false and based on older draft/softtimer-future-release-signing-pipeline-20261029 @ 734b89d9. No retarget/rebase attempted. |
| COE RELEASE #35 | fdd7a7d36674b69243c4523dea55021046e35c45 | Shared #45876024450: 256 host tests pass / 2 skips, then 10/10 appliance profiles fail closed for missing approved site-scoped RFC 4193 ULA /48. Sandbox #45876024481: 48/48 host preflight pass, Bubblewrap unavailable (exit 125). Case guard #45876024459 PASS. |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Overlay/Shell #44295049727 and case guard #44295049903 PASS (scoped). |
| COE INTERCON #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage 5.1 #44646341873 and case guard #44646341992 PASS; Shared Hardware/Contracts #44646341922 FAIL. |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows queued / zero jobs / zero completed statuses. FROZEN. |

## 4. COE #26 exact migration-provenance recheck

Current destination files were fetched at b382d233; source files were fetched at the current #353 and #354 PR heads. The current destination contains both Vendo firmware sketches, but neither matches either current source candidate.

| Firmware path | #353 source blob | #354 source blob | COE #26 destination blob |
|---|---|---|---|
| ESP32 BlazePwifiVendo32.ino | 8154297e30e72d82692987ed5690983df4955aea | 3edbe38da543ef118b287f3e04c1601692cfa99f | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 |
| ESP8266 BlazePwifiVendo.ino | 2613bfc36b0ddac9dd720592d4ff37e32a891744 | b45eb2d0bebfc0088e1c9f506c5e94c59cf054d9 | c8be98f72596681e36a3ad1f8939bf8046c96887 |

Selected test-identity comparison (not a full recursive test inventory):

| Test | #353 source blob | #354 source blob | COE #26 destination blob |
|---|---|---|---|
| security.sh | 8e2e5cf929546c37498f48a925c27e4b49f161db | bd40ccbd7c0c339bce6128c7b19f1467316d6fc4 | bd40ccbd7c0c339bce6128c7b19f1467316d6fc4 |
| integration.sh | 1fb2ff1c1bd215da3e3297b600fcd0c67b27716f | f6e98112da059f0c853fbfc90ebc70192f78c692 | 557b4d3d5d8478811ad057eb59a2d9ecf5c3a6a5 |
| config.sh | a42a7d5ef27169f5aa72e7bf8d19b8637fbd3d80 | a42a7d5ef27169f5aa72e7bf8d19b8637fbd3d80 | d585b772538030bac20400197a981639eb3dd4b2 |

Only the #354 security.sh selected identity is byte-identical to the destination. The #354 mbedtls_sha256_compat_lab.py and poll_preflight_inhibit_lab.py have no same-path counterparts in the COE Hardware tree. The connector does not expose recursive Git tree enumeration, so this activation does not claim a complete current source/destination file-count or full test-import count.

### Intake and migration-map conflicts

COE Pisowifi/SOURCE_INTAKE.json is blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f, schema 8. It pins historical source commit 6d4c9b487af4d768c4d7627654d119417fcc6e00 and destination branch feature/pisowifi-cleanup-stabilization. Its summary declares 47 byte-identical / 14 derived files, but its 61 runtime rows actually count 46 byte-identical / 15 derived.

Pisowifi/MIGRATION_MAP.md is blob b54fc15d83bc2269de03db8aadd0e76259fd13d9 and repeats the historical source commit and old destination branch, not the current PR #26 integration branch. docs/audits/HARDWARE_FIRMWARE_AUDIT.md is blob 86c06e7574761465b80482430296eb712d985367 and says the two Vendo sketches have not been copied; the current destination tree contains both sketches. The COE #26 PR body says P0-1 was formally resolved/removed. These three records and the live blobs do not agree; owner reconciliation is required before any staging proposal.

### License/notice comparison

| Artifact | Source blob | COE #26 blob | Result |
|---|---|---|---|
| PisoWiFi project LICENSE | 1ee55b94183417be977ca287cd7391f9a6f7e721 | 1ee55b94183417be977ca287cd7391f9a6f7e721 | Exact |
| QRCode LICENSE | 150770c0fc2994865ccdbef6662735cc083e780d | 150770c0fc2994865ccdbef6662735cc083e780d | Exact |
| TailAdmin LICENSE | cb92d4176b21b0594e5a6caf94d79340505e3d33 | cb92d4176b21b0594e5a6caf94d79340505e3d33 | Exact |
| TailAdmin NOTICE.md | f0425bbbe34c1227311098173b1eae0c3e2a807b | f0425bbbe34c1227311098173b1eae0c3e2a807b | Exact |

The source PisoWiFi project root has no NOTICE.md, and the destination Pisowifi root has no NOTICE.md; therefore a source-to-destination root NOTICE omission is not established. COE repository-root LICENSE/NOTICE paths are absent, but they are not counterparts to a source root file in the PisoWiFi project. Do not repeat older claims that a source root NOTICE was omitted.

## 5. Governance, access and execution limits

- CONTROL PLANE #172 remains OPEN; its body is a historical index and its current comments carry the latest checkpoints. No archival/no-comment directive is present in the current body.
- Cleanup #266 remains OPEN; 0/7 MASTER cleanup checklist items are checked. No mass move, deletion or source cleanup was attempted.
- The private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not recovered. Exact-title Library search surfaced older v3-v7 snapshots only; no Google Drive connector/action is exposed. No older snapshot was substituted and no private registry content or identifiers were published.
- The visible automation inventory has active Phoenix Master, PHX-HARDWARE (Blaze Hourly Production Development) and PHX-RELEASE tasks. The exact separate CORE automation title Blaze Production Continuation was not surfaced among the 17 visible automations. CORE source was left untouched and owner-reserved.
- Master Actions at starting HEAD 0730fff returned zero PR-triggered runs/statuses. Master Python unittest suite and verify_coordination.py were NOT RUN because the local container cannot resolve github.com (git ls-remote failed with Could not resolve host).
- 23/23 inline static audit consistency assertions passed. These are data-consistency assertions only, not repository tests or CI.

## 6. Changes and next actions

This activation updates only coordination/phoenix/: ROLE_ASSIGNMENTS.md, INTEGRATION_MATRIX.md, AUDIT_SUMMARY.md and INDEX.md, and adds this report. No subsystem source, COE destination, ownership route, secret, financial record or hardware state was changed.

1. COE integration owner: reconcile SOURCE_INTAKE, MIGRATION_MAP, HARDWARE_FIRMWARE_AUDIT and the actual #26 firmware blobs; publish exact per-file provenance and license/test evidence before any staging proposal.
2. QA: revise the #354 controllers.sh and sequence-contract assertions to test the approved deny-only contract without requiring unauthenticated config_revision or unsafe pending-clear callsites; then request exact-head reruns.
3. HARDWARE: keep #353 deny-default and resolve the missing poll-signature contract only after CORE publishes the authenticated producer contract; refresh #353 handover at its exact head.
4. Registry custodian: restore authorized access to private Drive v11 and newer corrections; repository administrator: verify effective branch protection and required checks.

## 7. Production disposition

PRODUCTION NO-GO. Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device 24-hour soak and explicit owner-authorized release gates remain unverified. No merge, release, flash, secret provisioning, real-payment operation, physical test or financial migration occurred.