# PHX-MASTER — migration manifest and poll-response audit

**Snapshot:** 2026-11-17T00:34:51Z (08:34:51 PHT)  
**Role:** PHX-MASTER  
**Scope:** coordination/phoenix/, architecture contracts, cross-repo provenance and integration status only  
**State:** DRAFT / PRODUCTION NO-GO

## 1. Exact refs and ownership

| Ref | Observed SHA / state |
|---|---|
| Experiments default main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Experiments blazepwifi-v0.5.3-development | aad3aade72c1156eecba1fed30907c6d0283b2c5; 293 commits behind main |
| Experiments blazepwifi-v0.6.0-audit-foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859; 22 commits ahead of source pin 6d4c9b487af4d768c4d7627654d119417fcc6e00 |
| Experiments Master PR #288 before this audit | 3d3634dfab35d9f427e159b7d392194edda37930 |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration draft #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |

The v0.6 audit-foundation branch and main are divergent (main is 22 commits ahead; the v0.6 branch is 1,876 commits behind main). Do not collapse v0.5.3 development, v0.6 audit-foundation and main into one assumed development baseline.

Root AGENTS.md is the same blob d8777e3b58efc41caa5aa3c969c932aee9103d5f on Experiments main and Master. OWNERSHIP_ROUTES.json blob e4db324315a1b3543fec17a148fbf960170fcb29 remains DRAFT_REVIEW_ONLY; its source_ref is main f4e8a891..., destination is COE PR #26 b382d233..., and PHX-MASTER is coordination-only. No route authorizes source relocation.

## 2. PisoWiFi rootfs manifest discrepancy

At the exact COE #26 candidate:

- Pisowifi/SOURCE_INTAKE.json blob: 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f.
- Pisowifi/MIGRATION_MAP.md blob: b54fc15d83bc2269de03db8aadd0e76259fd13d9.
- The rootfs table has 61 file rows. Comparing recorded source/destination Git blob IDs gives 46 byte-identical rows and 15 different-blob rows (13 intentionally edited and 2 locally derived).
- SOURCE_INTAKE.json instead claims 47 byte-identical and 14 locally derived. Both summary counters are off by one.
- The two locally derived rootfs entries are member.sh and rental.sh; both state real-router test NOT_RUN.
- Four legacy test records contain two byte-identical tests (portal.sh and security.sh) and two derived tests (config.sh and integration.sh). Fifteen additional derived test scripts are listed: 11 NOT_RUN and 4 PENDING_CI_RUN.
- COE #26 still has five queued candidate-head workflows. None is completed integration acceptance.

A read-only verifier and synthetic regression suite were added under coordination/phoenix/. The verifier compares summary counters to recorded Git blob identities, checks SHA-1 formatting, duplicate paths, incomplete rows and status/blob contradictions. It does not fetch Git objects and does not claim that manifest-recorded hashes equal live source/destination trees.

## 3. Source-pin drift and selected exact blob comparisons

The source-intake manifest pins Experiments commit 6d4c9b487af4d768c4d7627654d119417fcc6e00 and records destination branch feature/pisowifi-cleanup-stabilization at pre-manifest head cf59b41e5273bcc42acf59a7971481670e4b2611. The current ownership routing manifest instead pins source main f4e8a891... and destination integration PR #26 b382d233.... These are different source/destination snapshots and require reconciliation before migration approval.

| File | Pinned source | Current v0.6 branch | Current Experiments main | COE #26 destination |
|---|---|---|---|---|
| cgi-bin/vendo | db58041c0575ad0a1101d99cb85403e03c8dcb22 | db58041c0575ad0a1101d99cb85403e03c8dcb22 | 2e3a1430d08cc6606429a042df3b5848f53c7267 | 0a71c4e253ac6ec2c30d46f1f99faf874dbaab8e |
| common.sh | 4ccb10777b08f541d092f7c2c2d2aad4d2f6562e | 50fa2d02d40af7fd8b06e83974345f1016a317f9 | not separately fetched | ae00667da26c68c9e44a54a941887191029afc11 |

The migration map marks vendo and common.sh as intentionally edited. The source pin is 22 commits behind the current v0.6 branch; common.sh has changed since the pin. The current main vendo blob also differs from both the pinned v0.6 source and destination. These are provenance questions for PHX-CORE and the COE integration owner, not permission for Master to select or overwrite a runtime implementation.

The following license/notice blobs match between pinned source and COE #26: root PisoWiFi LICENSE 1ee55b94183417be977ca287cd7391f9a6f7e721; QR vendor LICENSE 150770c0fc2994865ccdbef6662735cc083e780d; TailAdmin LICENSE cb92d4176b21b0594e5a6caf94d79340505e3d33; TailAdmin NOTICE.md f0425bbbe34c1227311098173b1eae0c3e2a807b. This is a bounded file check, not a complete dependency/license audit.

## 4. HARDWARE poll-response validation and keyless admission gap

Current Experiments HARDWARE PR #315 head is 939e6ae09050e3e7244249acf9c7969301a05363. Its focused poll-response lab run 43982762795 succeeded, but full run 43982762668 failed in validation job 133703130190. The job log reports acceptPollResponse was not declared in this scope for both ESP8266 and ESP32; firmware compile jobs themselves succeeded. Earlier #316 head 888e6941e3a7a81641682c23d937f97d8117d2ea has the same failure pattern in run 43972511250, while focused lab run 43972511337 succeeded. #316 remains open/draft; hardware ownership notes say its poll work was consolidated into #315. Master did not close or merge either PR.

The #294 source-extraction harness at experiment/openwrt/BlazePwifi/tests/v060_esp_poll_intake_guard.py does not extract acceptPollResponse, although the modified firmware loop calls it. PHX-QA owns the extractor and canonical validation harness.

A separate source-level security mismatch remains in both current #315 firmware sketches:

- ESP8266 blob e0a9bf8871c77917971f76ff587d35b7c4c04d75.
- ESP32 blob 5fd8f0f6082b4d204098b73b5da36c862dd77d04.
- acceptPollResponse initializes signatureOk to true and verifies the response signature only when cfg.key is nonempty. With an empty key, an ok=true response with a nonempty target can pass the positive-response checks without signature verification.
- The focused lab blob 2892db4c6bbf6049586f8661efb94298c53245ee initializes its test Config with key="test-key"; it has eight cases but no empty/unprovisioned-key case. Its 8/8 result does not cover keyless admission.

This conflicts with existing Architecture Contracts §6.1, which says an empty/unprovisioned key cannot authorize coin intake. PHX-HARDWARE owns firmware behavior, PHX-CORE owns server/signature and replay semantics, and PHX-QA owns the extractor and independent empty-key/reboot regressions. No firmware or financial source was changed by Master.

## 5. Current role PR and CI observations

| Role / area | Current exact head | Observed CI |
|---|---|---|
| MASTER #288 | 3d3634dfab35d9f427e159b7d392194edda37930 | No PR-triggered workflow runs returned |
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Run 42698139210 success; scoped/older evidence |
| RENTAL #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | Runs 43653329235 and 43653329229 success |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Run 42462978704 success; no native COM acceptance |
| HARDWARE #315 | 939e6ae09050e3e7244249acf9c7969301a05363 | Focused 43982762795 success; full 43982762668 validation failure; ESP32/ESP8266 compile jobs success |
| HARDWARE #316 | 888e6941e3a7a81641682c23d937f97d8117d2ea | Focused 43972511337 success; full 43972511250 validation failure |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered workflow runs returned |
| QA #267 | ff5367990c2d27b8ebbb822ee208251af0c890e2 | Run 41452247439 success; older scoped evidence |
| RELEASE #291 | 2c4edff231d9b2819415086825530d80b8801307 | Run 43744993487 success; no signing authorization |

COE role drafts on the integration candidate:

- COE #31 RELEASE head f4f93dd7c5e18eab1a653f1f756eb1dbb0a234ab: run 43986022373 validation plus ESP32/ESP8266 compile success; run 43986022315 case-collision success. Synthetic packaging and compilation only; no real ImageBuilder artifact or hardware acceptance.
- COE #29 CORE head d0830332dee8a1844a85606150681b41d91fe796: runs 43653906675 and 43653906676 success.
- COE #30 PISONET head 4897348d94a0cf7884ecd53244bfcd59e7bf2fbc: run 43653415598 success.
- COE #28 PISONET head b21b04617d38a177260258de2d56b24382822117: run 43632393888 success.
- COE #32 QA head 29b6fe08b10688182d981a66745f482758bd6630: run 43653540607 success; this does not cover the Experiments #315 poll extractor gap.
- COE #27 HARDWARE/Shared head 009f70cc2c2775039a5fb072c9d4fdedee76cfc7: runs 43079646393 and 43079646264 success.
- COE #18 PisoWiFi head 331e14bc63e163148f09813da0fdbf4d13581a19: case-collision run 43061613277 only. COE #19 Rental head 04c97030096aa5e5a854952e0cc377ffe31d5d07: case-collision run 43061768902 only.
- COE integration #26 remains at b382d233ff06c8791b1028bed3c617cc7b670d12 with five queued workflows: 43096752609, 43096752632, 43096752800, 43096752563, 43096752557.

These are per-commit workflow observations, not combined integration acceptance.

## 6. Registry access and execution limits

The exact private Google Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not retrievable through the available connected tool surface. Exact-name Library search returned historical v5-v7 registry files and a checkpoint, not v11; no Google Drive connector was exposed. No older registry was substituted and no private contents or identifiers were published. The public AGENTS.md cloud artifact policy and storage handover were read; that policy explicitly requires BLOCKED when the Drive connector is unavailable.

Local Master verifier tests: 10/10 synthetic Python unit tests passed; both files compiled. The live GitHub manifest/table counts were independently parsed from the fetched exact candidate files, but the new CLI was not run against a local clone of those files. No full Master suite or exact-head Master CI was executed.

## 7. Exact next actions

1. PHX-QA: add acceptPollResponse to the canonical source extractor, add empty-key positive-response denial tests for both boards, and rerun the full exact-head validation.
2. PHX-HARDWARE: make missing/empty key fail closed, preserve nonce/target/freshness checks, and reconcile #315/#316 under one owner-controlled stack.
3. PHX-CORE: confirm the provisioned-key/signature contract and durable rejected-event/replay semantics with HARDWARE.
4. COE integration owner: reconcile the 47/14 summary against the 46/15 recorded blob counts; update the manifest to identify the exact candidate destination head and current source pin; review common.sh and vendo against current development and main refs; run pending derived tests and complete the license/dependency audit.
5. Registry custodian: restore authorized private Drive read access to v11 and newer corrections.
6. PHX-MASTER: rerun the read-only verifier against the corrected exact candidate and refresh the matrix after independent owner evidence.

No subsystem source branch was modified. No source move, merge, release, signing, secret provisioning, firmware flash, physical test, customer payment, or live financial migration occurred. PRODUCTION NO-GO remains.