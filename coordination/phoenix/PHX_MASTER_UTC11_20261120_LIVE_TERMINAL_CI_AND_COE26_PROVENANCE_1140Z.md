# PHX-MASTER UTC11 live terminal CI and COE provenance revalidation

**Audit time:** 2026-11-20T11:52:08.298Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, cross-repo provenance and integration matrix only  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Audit-start branch/head:** phoenix/master-coordination @ 3d75d241263576c3913a6388a26d9d761324a957  
**PR:** #288 OPEN / DRAFT, base main @ f4e8a891aed8af86d5fd315d28750a0ac3a7372b  
**Mode:** Strict NO CODEX. No Codex app, CLI, API, agent, workflow or delegation.

## 1. Source-of-truth refresh

- CONTROL PLANE #172: OPEN; body last updated 2026-11-20T11:35:07Z. Existing PHX-MASTER UTC11 checkpoint comment #7038320157 is the same-hour idempotency target; update it in place, do not create another role/hour comment.
- Cleanup issue #266: OPEN; current checklist still requires Master duplicate/dead-code inventory. Master checkbox remains intentionally unchecked.
- Experiments repository default branch: main @ f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- BlazePwifi legacy development: blazepwifi-v0.5.3-development @ aad3aade72c1156eecba1fed30907c6d0283b2c5.
- v0.6 audit foundation: blazepwifi-v0.6.0-audit-foundation @ 2fbd2475e9f54878c316fa7cea2f228386b0e859 (comparison-only; not promoted).
- COE default branch: main @ a6513ab4412b4c014eee2863e45cbe32d06cb243.
- COE integration PR #26: OPEN / DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12; five workflows QUEUED, zero jobs.
- Master routing manifest: OWNERSHIP_ROUTES.json blob e4db324315a1b3543fec17a148fbf960170fcb29, status DRAFT_REVIEW_ONLY; PHX-MASTER target remains null.
- Experiments main, development, v0.6 and Master branch APIs report protected=false; repository rulesets endpoint returned an empty list. Effective organization-level enforcement is not independently established.
- Experiments AGENTS.md was read. Its linked Cloud Artifact Policy and Cloud Storage Handover could not be fetched through the available GitHub/web connector paths. No Drive connector is exposed in this run.

## 2. Current role PRs and exact-head CI

| Role | Current PR / exact head | Current exact-head CI | Disposition |
|---|---|---|---|
| CORE | #252 c82705f2de865c89ab733b10efa84f26f56a5cc4 | #42698139210 SUCCESS | Scoped PASS only; separate Blaze Production Continuation retains CORE source ownership. |
| RENTAL | #240 a7d113fb8ae3f0c5e838e64d31cae7a154e37b56; #287 a4fffd01c8fb1818c32a53522e0590c1dc8a77cd; #289 68928774d0d7cf65adb26bc6b54199a3159d066c | #240 #40910311159/#40910311141 SUCCESS; #287 #43754089203 SUCCESS; #289 #43653329229/#43653329235 SUCCESS | Scoped PASS; no physical Device Owner acceptance. |
| PISONET | #255 d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | #42462978704 SUCCESS | Scoped Windows CI only; native COM bench unverified. |
| HARDWARE | #327 89442ce681df965b16c80f73055236a0d842fe0c, base #326 58c558fb6a237935214621adc3dee65a10fe1a51 | Quarantine #44722725391 PASS; relay/output #44722725315 PASS; Full #44722725399 FAIL | Full validation fails at QA-owned “Missing poll signature check” in controllers.sh. Firmware remains deny-only; QA must align the legacy fixture with the signed-response contract. |
| HARDWARE | #254 84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9 | Focused #44683629378 PASS; Full #44683629491 FAIL | Scoped helper PASS; Full remains failed. |
| QA | #290 5c29d15994cee1279058f1eca12f2a3180704292; #292 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #290 #43633486963 SUCCESS without NativeComInterfaceHandleLab; #292 no exact-head run | Native COM acceptance remains unverified; #292 is UNKNOWN, not PASS. |
| RELEASE | #291 0d4a3c9213a253d64f54de296af306386f915d82 | Compatibility #44728953554 SUCCESS on both ESP32 core legs; Windows #44728953500 FAIL; Full #44728953513 CANCELLED | Compatibility parser/section checks and two clean image comparisons now pass on the workflow-pinned source. Windows remains blocked by PISONET-owned negative-selftest.ps1; Full was cancelled with some simulations cancelled and production signing/publishing skipped. |

### RELEASE / PISONET ownership collision

PR #291's current changed-file list includes:
- experiment/windows/BlazePisonet-SoftTimer/tests/ReleaseSigning/PublisherMockCli.ps1
- experiment/windows/BlazePisonet-SoftTimer/tests/ReleaseSigning/negative-selftest.ps1

These are PISONET-owned paths. The current Windows run #44728953500, job 136263518218, fails in negative-selftest.ps1 because $buildWorkflow is read before it is set. PISONET owns and must approve the correction; RELEASE owns its workflow and release-specific tests. PHX-MASTER did not modify either subsystem path or reassign ownership.

The compatibility run #44728953554 completed both core legs successfully, including exact-source verification, pinned toolchain checks, ELF inspectors and two-build byte comparison. This supersedes the previous compatibility import failure for the tested pinned source; it does not establish a production artifact or authorize signing.

The Full run #44728953513 ended CANCELLED. Validation, Android, firmware targets and several simulations completed successfully, but Android emulator, x86 and two Orange Pi simulations were cancelled. Production APK import, prerelease/release publication and production sign handoff were skipped. Do not label this Full PASS.

## 3. Exact Hardware-to-COE #26 provenance

Recursive trees were complete and not truncated:
- Experiments HARDWARE #327 @ 89442ce681df965b16c80f73055236a0d842fe0c: 2,435 entries.
- COE #26 @ b382d233ff06c8791b1028bed3c617cc7b670d12: 286 entries.

| Item | Source #327 exact blob | Destination #26 exact blob | Result |
|---|---|---|---|
| ESP8266 sketch | 3ff575f5cd879c021407849578854b74a2d460bd | c8be98f72596681e36a3ad1f8939bf8046c96887 | Different |
| ESP32 sketch | 849a2c63d75bbbcda58e1a0a7fc55e7c047ea26e | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 | Different |
| Board-local Python labs/helpers | 25 | 0 | No exact test import identity |
| Hardware test entrypoints | 25 Python labs | one generic shell test f921c56cecc19cab1989507b9b4ade1f45dac54e | Not equivalent |
| Scoped Hardware workflows | 3 PHX workflows | one generic hardware-ci.yml fe79adbdb3745a22c5ef6d1f0c87c868b7785793 | Not workflow parity |
| MIT license | source BlazePwifi/LICENSE 1ee55b94183417be977ca287cd7391f9a6f7e721 | destination Pisowifi/LICENSE same blob | Sibling match only |
| Root NOTICE | source NOTICE.md f6d92cd21465312be5993631fe26977219be0fb9 | absent | Missing |
| Hardware license/notice scope | no separate Hardware license in source subtree | Hardware/LICENSE and Hardware/NOTICE.md absent | Unresolved |

The matching Pisowifi MIT blob does not independently establish the Hardware subtree's notice/license scope. COE #26 has five queued workflows and zero jobs. No copy, move, overwrite, cherry-pick, rebase, staging, route promotion or migration is proposed.

### Separate COE candidates — not integrated into #26

| PR | Exact head | Exact-head CI |
|---|---|---|
| #28 | b21b04617d38a177260258de2d56b24382822117 | #43632393888 PASS |
| #29 | d0830332dee8a1844a85606150681b41d91fe796 | #43653906676 / #43653906675 PASS |
| #30 | 4897348d94a0cf7884ecd53244bfcd59e7bf2fbc | #43653415598 PASS |
| #31 | 59ed44d0b911e176f1a95b9cf5585ef811ffd31b | sandbox #44222517263 FAIL; shared #44222517238 and case guard #44222517258 PASS |
| #32 | 29b6fe08b10688182d981a66745f482758bd6630 | #43653540607 PASS |
| #35 | 7b9706d898fb5f36c6ed96504aefd04dc59bdc1b | sandbox #44617781877 and shared #44617782050 FAIL; case guard #44617783021 PASS |
| #44 | 582fd5d5e83e36b36546ac28534740298ba94af4 | sandbox #44390136327 FAIL; shared #44390136309 and case guard #44390136296 PASS |
| #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | #44295049727 / #44295049903 PASS |
| #48 | 8286548e395366f2332830025fed00ceebdfb24a | Stage 5 #44643670696 and case guard #44643670679 PASS; shared Hardware #44643670685 FAIL |
| #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage 5.1 #44646341873 and case guard #44646341992 PASS; shared Hardware #44646341922 FAIL |

These are separate candidates with no route in OWNERSHIP_ROUTES.json. Their scoped green checks do not establish combined destination acceptance.

## 4. Storage, tests and governance limitations

- The canonical private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections could not be retrieved: no Google Drive connector is exposed, and exact Library title search did not return v11. Older Library snapshots were not substituted. No private registry content or identifiers were published.
- The full Master Python suite was NOT RUN. A local git ls-remote attempt failed because this container could not resolve github.com. No Master-specific PR-triggered Actions run was found.
- Source/tree and GitHub CI inspection above is not a local test execution. The subsystem run links are real exact-head GitHub Actions results.
- Repository branch API reports protected=false and rulesets=[]; effective organization-level enforcement remains unverified.
- No subsystem source, test, workflow or COE destination file was changed. No migration, merge, release, signing, secret provisioning, hardware flash, physical test or real-payment action occurred.

## 5. Required next human actions

1. PHX-QA: correct the poll-signature fixture against the current deny-only response contract; do not weaken firmware default-deny.
2. PHX-PISONET: fix and own the $buildWorkflow initialization in its Pisonet negative-selftest.ps1 and review the Pisonet-owned publisher mock file included in RELEASE #291.
3. PHX-RELEASE: rerun Windows after the PISONET-owned correction; preserve the two-core exact-source comparator and obtain terminal non-production Full evidence.
4. COE integration owner: keep #26 frozen; complete exact file/blob, license/NOTICE, test identity, workflow and destination CI review before proposing any move.
5. Registry custodian: restore authorized private v11 and newer-correction access through an approved Drive connector.
6. Repository administrator: independently establish effective protected branch/ruleset enforcement.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.
