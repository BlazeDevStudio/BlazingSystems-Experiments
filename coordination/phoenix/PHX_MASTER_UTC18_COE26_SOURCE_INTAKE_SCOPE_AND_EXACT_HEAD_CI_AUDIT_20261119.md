# PHX-MASTER UTC18 — COE #26 source-intake scope, exact-head role CI and migration provenance audit

**Checkpoint:** 2026-11-19T18:33:00Z  
**Role:** PHX-MASTER — architecture/interface contracts, coordination/phoenix/, cross-repo provenance and integration matrix  
**Task:** #172 / #266 / #288 / COE #26  
**Disposition:** MASTER DOCUMENTATION COMMITTED / COE MIGRATION BLOCKED / PRODUCTION NO-GO  
**Execution boundary:** No Codex app, CLI, API, agent, workflow or Codex-delegated implementation used.

## 1. Live control-plane and branch state

- Experiments main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b
- Legacy development: blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5
- Audit foundation: blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859 (comparison-only)
- Master branch before this run: phoenix/master-coordination@3b910343ea25ac93ecb417c3ea29cb2d09c84f00
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243
- COE integration #26: integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12
- Master PR #288: OPEN / DRAFT, base main@f4e8a891..., 106 pre-run changed paths; all 106 were under coordination/phoenix/.
- Cleanup #266 remains OPEN; its broader Master duplicate/dead-code inventory remains incomplete.
- OWNERSHIP_ROUTES.json blob e4db324315a1b3543fec17a148fbf960170fcb29 is unchanged, DRAFT_REVIEW_ONLY, PHX-MASTER destination null.

Issue #172 and #266, root AGENTS.md, root README.md, current Master routing manifest, Master architecture/matrix/role/audit documents, role PRs and exact-head CI were re-read. The uploaded 00_MASTER_PROJECT_PHOENIX(1).txt was read from Library. README_FIRST and COMMUNICATION_PROTOCOL were not found in the repository tree or Library search; BLAZE-COMMS/1 was followed from the uploaded Master directive and issue #172. The private Drive v11 registry and newer corrections were not surfaced; older v3-v7 Library snapshots were not substituted. No Google Drive connector was exposed.

## 2. New architecture decision — intake manifests are scope-bound

COE #26 contains Pisowifi/SOURCE_INTAKE.json blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f, schema v8. It declares:
- Source commit 6d4c9b487af4d768c4d7627654d119417fcc6e00
- Source project root experiment/openwrt/BlazePwifi
- Original rootfs tree f4a923aaacf1374e90c7bab5f335efe6c6ec55cf
- Original tests tree 7e3b16f2a981c1c8ecab3b1da0d34a82b4e44f17
- Destination root Pisowifi/
- 61/61 rootfs files recovered; 47 byte-identical; 14 locally derived; zero unrecovered rootfs files; two unchanged original tests.

This manifest is specific to its declared Pisowifi/rootfs intake. It does not declare Hardware/ as a source or destination root and cannot be used as evidence that ESP32/ESP8266 firmware, Hardware tests, or Hardware licensing were imported completely.

## 3. Exact firmware blob comparison

| Board | Experiments main source | Historical intake-commit source | COE #26 destination | Result |
|---|---|---|---|---|
| ESP32 | 117c6e937e8f12f3890ace2ae23b3a23ff1c3df0 / 15,049 bytes | 29f1125d52ff474a0d028ad41f7af201be1f0f9d | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 / 18,505 bytes | Neither source pair is byte-identical to destination |
| ESP8266 | bfb94920eb0a189ca01d52e5443954fa133f5423 / 14,583 bytes | 12c4bb82b6fddafe813674a0b5f692c1d3634073 | c8be98f72596681e36a3ad1f8939bf8046c96887 / 18,394 bytes | Neither source pair is byte-identical to destination |

The current routing manifest source ref is Experiments main. The COE intake manifest is pinned to an older source commit. Neither route proves exact firmware copy identity. Treat the COE Hardware sketches as derived candidates and require Hardware owner provenance and independent QA review.

## 4. Test identity and license scope

- Current Experiments main experiment/openwrt/BlazePwifi/tests/: 38 entries.
- COE #26 Pisowifi/tests/: 19 entries.
- Four shared basenames: config.sh, integration.sh, portal.sh, security.sh.
- Only portal.sh is byte-identical: 71b3c9622f51a80dc09a446389ba6faa001b7897.
- COE #26 Hardware/tests/ contains one generic test_firmware_hardening.sh blob f921c56cecc19cab1989507b9b4ade1f45dac54e.

This comparison does not claim the 38 PisoWifi shell tests are firmware-specific; it proves that the declared Pisowifi tests route is not a byte-identical import of the current-main test tree. Hardware test provenance is separately incomplete.

License/notice comparison:
- Source BlazePwifi/LICENSE and COE Pisowifi/LICENSE match at 1ee55b94183417be977ca287cd7391f9a6f7e721.
- Experiments root NOTICE.md exists at f6d92cd21465312be5993631fe26977219be0fb9.
- COE root NOTICE.md, Hardware/LICENSE and Hardware/NOTICE.md are absent in the inspected #26 candidate.

The Pisowifi MIT license match does not establish Hardware licensing/notice scope. Obtain owner/licensing review before any Hardware migration proposal.

## 5. Exact role PR and CI reconciliation

| Role / PR | Exact head | Exact-head evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | 42698139210 SUCCESS, scoped. Separate CORE continuation retains implementation. |
| RENTAL #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | 43653329235 and 43653329229 SUCCESS, scoped. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | 42462978704 SUCCESS, scoped. |
| HARDWARE #317 | fce915c1167fc43c6936f3594ae9efce376b711f | Focused 44209812693 / 44209812920 PASS; Full 44209812745 FAIL. |
| HARDWARE #318 | de428b7a3e15854804f09935a36a6afeb67d8cbe | No PR-triggered run returned. |
| HARDWARE #321 | 4c54d6299388617e9ff3d41d5501358ea545c54a | Focused 44294008493/44294008398 PASS; Full 44294008523 FAIL. |
| HARDWARE #322 | 50d93e0de3d682550b6f02fb43484e76ad9c7e08 | Focused 44232877611/44232877649 PASS; Full 44232877624 FAIL. |
| HARDWARE #323 | 988904e8bcd058b62a9fac4aa6319a9b7c5b2470 | Focused 44347847077/44347847191 PASS; Full 44347846832 FAIL. |
| HARDWARE #324 | 8e7f02201cb9295f15672dc21f8a75fc4e5cd0ba | Focused 44290338468/44290338178 PASS; Full 44290338340 FAIL. |
| HARDWARE #326 / #327 | #326 58c558fb6a237935214621adc3dee65a10fe1a51; #327 fa9381c72787ca728e77180023c3143f4225147a | #327 focused 44581897191 / 44581897200 PASS; Full 44581897225 FAIL. |
| QA #290 / #292 | #290 5c29d15994cee1279058f1eca12f2a3180704292; #292 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #290 43633486963 PASS but does not execute NativeComInterfaceHandleLab; #292 has no exact-head run and is based on stale Master b1ca02e.... |
| RELEASE #291 | a17f270ef5560e4fada4e9ef7ca4ea5ed03fbf28 | BlazePwifi 44581603752 PASS; ESP32 compatibility 44581603620 PASS; Windows 44581603605 FAIL. Handover passed; PISONET-owned negative-selftest.ps1 reads $buildWorkflow before assignment; publisher skipped. |

Hardware branches are parallel lineages, not one canonical stack: #318 and #321 are based on #317; #323 and #324 are sibling children of #322; #326 is based on #323; #327 is based on #326. The available Full failures are at the QA-owned legacy positive Missing poll signature check. Preserve firmware default-deny; QA owns fixture correction. No branch composition is authorized by Master.

## 6. COE integration CI and ULA blockers

COE #26 exact head b382d233ff06c8791b1028bed3c617cc7b670d12 has five queued workflows: case-collision 43096752609, PISONET 43096752632, Hardware/shared 43096752800, Rental 43096752563, Pisowifi 43096752557. All five job-list queries returned zero jobs. No destination test executed.

COE #35 head d41f3231e0eae6cf0c62d19f430818e30372162e:
- Shared 44586100929 ran the packager suite, then all ten appliance profiles failed closed because an approved site-scoped RFC 4193 /48 is absent; ESP32/ESP8266 compile jobs skipped.
- Mandatory sandbox 44586100962 failed because Bubblewrap is unavailable after host preflight; no unsandboxed fallback.
- Case-collision 44586101050 passed.

COE #44 head 582fd5d5e83e36b36546ac28534740298ba94af4 has shared/case passes but sandbox 44390136327 fails closed. Per-appliance random identity does not prove a shared site-wide prefix.

## 7. Executed audit checks and limits

- Eight connector-backed source-metadata assertions PASS: both firmware blob pairs differ; source/destination test counts and common basenames; only portal.sh exact; Pisowifi license blobs match; source root NOTICE exists.
- Five COE #26 workflow job-list checks returned zero jobs.
- These are metadata and CI-state checks, not the Master Python suite.
- Master Python suite: NOT RUN.
- Master Actions: no run returned.
- No physical hardware, real power-cut, financial migration, signing, flashing, payment, or 30-device soak test was run.
- No source copy/move, migration staging, merge, or owner branch modification occurred.

## 8. Required next owner actions

1. COE integration owner: add a Hardware-specific source-intake manifest with exact source commit/tree, per-file source/destination blob+mode, derivation notes, test identity map, license/NOTICE scope, and pinned toolchain.
2. PHX-HARDWARE: nominate one canonical branch stack and reconcile parallel #317/#318/#321/#322/#323/#324/#326/#327 ancestry with QA.
3. PHX-QA: replace the obsolete positive poll marker with negative/default-deny tests and execute on the selected exact source SHA.
4. PHX-PISONET: correct its own uninitialized $buildWorkflow test variable; PHX-RELEASE reruns #291 afterward.
5. PHX-CORE and COE integration: decide durable site ULA authority; RELEASE consumes only the approved site-wide input.
6. PHX-INFRA: provide an authorized Bubblewrap-capable runner.
7. Registry custodian: restore authorized private v11 and newer-correction access; no older snapshot substitution.
8. Repository administrator: verify effective branch protections and required checks.

**Final disposition:** migration BLOCKED; all owner scopes preserved; PRODUCTION NO-GO.
