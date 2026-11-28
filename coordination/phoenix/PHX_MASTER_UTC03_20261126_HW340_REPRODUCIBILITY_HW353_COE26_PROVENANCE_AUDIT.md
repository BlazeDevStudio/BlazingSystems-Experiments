# PHX-MASTER UTC03 — live exact-head role/CI, #340 core-4 reproducibility, #353 Full gate and COE #26 provenance

**Updated:** 2026-11-26T03:57:22Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Scope:** Master-owned coordination, architecture contract, migration provenance and integration matrices only.  
**Execution:** Strict NO CODEX. No subsystem source or COE destination write.

## 1. Live refs and governance

| Ref | Exact SHA |
|---|---|
| Experiments main | 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 |
| Experiments development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Master branch before UTC03 | c8deb97ba9418f264995c782eabc2901a933b26f |
| Active v0.6 audit foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| CoinOperatedEcosystem main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE #26 candidate | b382d233ff06c8791b1028bed3c617cc7b670d12 |

The 11-route ownership manifest blob e4db324315a1b3543fec17a148fbf960170fcb29 remains DRAFT_REVIEW_ONLY. PHX-MASTER owns coordination/phoenix/ with target null. The manifest source_ref f4e8a891 is a historical baseline, not a current source-main pin and not migration authority.

Cleanup issue #266 remains OPEN with 0/7 role checkboxes complete. The private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not recovered. Authorized Library search surfaced older v3-v7 snapshots only; no Google Drive connector was exposed. No older registry was substituted and no private registry content was copied to GitHub.

PR #288 was OPEN / DRAFT / UNMERGED at pre-run head c8deb97, 228 changed paths, all under coordination/phoenix/, 591 ahead / 1 behind main, merge base f4e8a891. Master branch protection enforcement remains unverified.

## 2. HARDWARE #340 — real core-4 compile, Full PASS, reproducibility gap

Current PR #340 head f70f6af78c64ef86ba0f631faeb02b6cb6eb2725; source/test SHA d1380acf80c0b631c5814d746dca36b2fad7a986. Current #283 parent is 4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30. Exact compare: 52 ahead / 0 behind. The final docs head is two commits beyond the source/test SHA; those commits only change PROJECT_HANDOVER.md and the UTC03 handover note.

The ESP32 sketch blob is fc883d20ef76ec5521a5872a175ec73a16cf8cbe at both source/test SHAs d3168ccb4959fe1eab718912fd04510ef7603253 and d1380acf80c0b631c5814d746dca36b2fad7a986.

### Exact CI

- ESP32 Arduino core 4.0.0 actual sketch compile [#45747192648](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747192648), job 139665996232: PASS. Log verifies expected/actual source SHA, Arduino CLI 1.6.0, ESP32 core 4.0.0 and actual sketch compile. Program storage 82%. Binary SHA-256: ea6bfb5fbf31f4fca3ed7942e92cede58b75c1d087cd74ac15414d9d568f0a2e.
- Prior core-4 compile [#45742944327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45742944327), job 139652109745: PASS at source/test SHA d3168ccb. Same sketch blob, same reported CLI 1.6.0 and core 4.0.0, but binary SHA-256 f9489e1df0d075cbfce549120c37af2778c53cb055f165c14a1d790623293c31.
- Focused provider guard #45747199083, poll preflight #45747199112, quarantine #45747199138, ESP8266 core 3.1.2 #45747199174 and ESP32 core 3.3.13 #45747199118 all PASS.
- Final docs-head Full [#45747758154](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747758154) PASS: 26 successful jobs / 4 intentional skips. Skips: production signed APK import, prerelease publication, release publication and production-sign handoff.
- Source/test Full #45747199081 was cancelled. Do not call that run a pass.

### Reproducibility finding

The two core-4 builds use the same source sketch blob and report the same Arduino CLI/core versions, yet their binary hashes differ. Both dedicated core-4 workflow runs returned zero retained artifacts, so byte-level comparison is impossible. The workflow blob 0598839f92831698a60bc8715df14db1c56b6fac uses arduino/setup-arduino-cli@v2, updates the live package index, installs core 4.0.0, and does not retain the core-4 binary. The logged CLI version is 1.6.0, but the complete package index, compiler/linker and transitive toolchain versions are not pinned in the workflow evidence.

This is an observed reproducibility gap; the cause is not established. It is not evidence of compromise and does not negate the successful compile. It blocks any claim that the core-4 binary is reproducible or release-ready. The separate final docs-head Full PASS does not replace the missing dedicated core-4 artifacts.

PHX-RELEASE owns full toolchain pinning, artifact retention and two-build reproducibility investigation. PHX-HARDWARE owns source identity and build intent. PHX-QA independently reviews the evidence. Master changed only the architecture contract and coordination/test documentation.

## 3. HARDWARE #353 — latest source/test and exact Full failure

Current PR #353 head 832692020a428ff4fe03a197a1bfce65b3f9316c; source/test SHA ed2f77d5924172881f27222cc26649f8f85abe6c; parent #352 head 2fa3b7db1161ddb531ed94bcf60617947fa1a7bd. Exact compare: 27 ahead / 0 behind. The final docs head is one commit after source/test and changes only PROJECT_HANDOVER.md plus the UTC03 handover note.

The source/test update adds a source-extracted contract for configureRuntimePins(): detach before pin reassignment, INPUT_PULLUP before ISR attachment, configured active edge, and quarantine after attachment on ESP8266 and ESP32. Four failure-injection mutations per board are rejected. The PR changed-file list contains lab/test/workflow/handover files but no production .ino source change.

- Quarantine [#45751177827](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45751177827) PASS.
- Relay [#45751177670](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45751177670) PASS.
- Full [#45751177730](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45751177730) FAILS in validation job 139679141206, step Controller protocol parity. Job log says Missing poll signature check in the ESP8266 sketch. All 14 target/platform jobs and Android passed; downstream simulation, update, signing, publication and candidate jobs were skipped.

The latest owner PR comment 7182089936 reports the current head; the PR description itself still contains an older head/source pin and should be refreshed by HARDWARE. Master did not rebase, retarget or alter the child branch.

## 4. Other exact-head owner CI

| Owner / PR | Current head | Exact evidence / blocker |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Scoped build #42698139210 PASS. CORE remains separately owned; no competing source work. |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | API smoke #45622918364, auth/installer #45622918551, APK identity #45622918340 PASS; shared build #45622918468 FAIL. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Synthetic Windows #42462978704 PASS; native COM not invoked. |
| HARDWARE #348 | 93afd4830b2728d5976e21951610943e1ec96c85 | Full #45731176586 FAIL at missing mbedtls/sha256.h under ESP32 core 4.0.0. |
| HARDWARE #349 | 1a2ecf5fa8c8c20a0095ac898c1bff254280ad27 | Full #45724609215 FAIL at Missing poll signature check. |
| HARDWARE #352 | 2fa3b7db1161ddb531ed94bcf60617947fa1a7bd | Full #45745420916 FAIL at Missing poll signature check. |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Synthetic Windows #43633486963 PASS; native COM not invoked. |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered runs. |
| RELEASE #242 | a7e27fe50e13326a7258bbaed1388594141ddda3 | No exact-head Actions run; source/test 9351dd053d4e2ed2349a25f3c5b6d37a308edf93 has static assertions only; PowerShell test not run. |
| RELEASE #291 | 9b928c9eaa72cb26fdcf3f0e50a0ec024f4e3c30 | Child based on former #242 head 734b89d9. Current #242 → #291 compare: 852 ahead / 9 behind. #291 Windows/Full fail CORE handover freshness; ESP32 compatibility pass. |
| COE RELEASE #35 | b6ec4ba78dda03a19d3d55d9be26b0a808eb4e26 | Shared #45742049762 fails site-ULA admission; sandbox #45742051077 fails Bubblewrap availability; case #45742049684 PASS. |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Overlay/Shell #44295049727 and case guard #44295049903 PASS; focused only. |
| COE INTERCON #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage 5.1/case PASS; shared ESP32 compile #44646341922 FAIL at missing mbedtls/sha256.h. |

## 5. Active v0.6 response-auth P0

Exact active v0.6 branch head remains 2fbd2475e9f54878c316fa7cea2f228386b0e859.

- ESP32 sketch blob 29f1125d52ff474a0d028ad41f7af201be1f0f9d.
- ESP8266 sketch blob 12c4bb82b6fddafe813674a0b5f692c1d3634073.
- CGI vendo blob db58041c0575ad0a1101d99cb85403e03c8dcb22.

Both board poll loops read unsigned insert/target_nonce and invoke applyRemoteConfig. The CGI poll response includes no response_sig. Request signing does not authenticate the response; member endpoint signatures are not a poll contract. No runtime attack or payment operation was run.

Required order remains CORE-approved authenticated envelope, canonical serialization, controller/target binding, mandatory nonempty key provisioning, freshness and replay rules; then HARDWARE consumer implementation; then independent QA vectors on both boards. Do not invent the contract or relax Missing poll signature check.

## 6. COE #26 migration/provenance hold

COE #26 remains OPEN / DRAFT / FROZEN at b382d233ff06c8791b1028bed3c617cc7b670d12 against COE main a6513ab4412b4c014eee2863e45cbe32d06cb243. Five workflows are queued with zero jobs.

Current #353 source board blobs:
- ESP32 1412cf57b70c6ee3061da9831b8d9abf6d58d94e.
- ESP8266 b99f1f21d8ad1e6df0e403b2b34507f97bd90c16.

COE #26 destination board blobs:
- ESP32 3cc7ec54b476943dc04a8d1af5e2df5fe054e422.
- ESP8266 c8be98f72596681e36a3ad1f8939bf8046c96887.

Both source/destination board blobs differ. The COE destination retains sigOk=true and conditional verification only when the controller key is nonempty; a keyless path bypasses response verification.

Source product LICENSE and destination Pisowifi/LICENSE match exact blob 1ee55b94183417be977ca287cd7391f9a6f7e721. Source root NOTICE.md blob f6d92cd21465312be5993631fe26977219be0fb9 has no destination root NOTICE.md (404).

The last complete #349 tree/test baseline was 2,553 source / 286 destination entries, 64/0 board-local Python helpers, and 47/19 mapped tests (4 common paths, 1 exact, 3 divergent, 43 source-only, 15 destination-only). This is historical baseline only: current #353 has advanced and adds ISR/runtime-pin labs; a full recursive remap at 8326920 is not claimed. The #26 changed-file list has one Hardware test script but no Hardware-specific SOURCE_INTAKE or MIGRATION_MAP. No staging, copy, move, overwrite, cherry-pick or destination write is authorized.

## 7. Master execution, tests and next actions

Master-owned changes in this activation: ROLE_ASSIGNMENTS.md, INTEGRATION_MATRIX.md, AUDIT_SUMMARY.md, ARCHITECTURE_CONTRACTS.md, INDEX.md, test_architecture_contracts.py and this report. No subsystem source, COE destination, payment, secret, signing or hardware state changed.

Master Python unittest suite and verify_coordination.py were NOT RUN: no authenticated local checkout was available and git ls-remote failed DNS resolution. Static content assertions were run against the new architecture contract and test insertion. Owner CI was inspected at exact SHAs; Master did not execute owner CI. Master Actions runs/statuses: zero.

Next actions:
1. PHX-CORE publishes the approved authenticated register/poll response contract and mandatory key/freshness/replay rules.
2. PHX-RELEASE pins the complete core-4 toolchain/package set, retains the actual core-4 firmware binary and manifest, and reproduces two clean identical builds or classifies the output NONDETERMINISTIC.
3. PHX-HARDWARE updates #353 description/handover at current head and resolves Missing poll signature check only against the CORE-approved contract; no Master rebase/retarget.
4. PHX-QA independently reviews the #353 mutation vectors and later validates both boards against the approved response contract.
5. COE integration owner supplies current #353 per-file import/test/license provenance; keep #26 frozen until exact-head CI and mapping are complete.
6. RELEASE/INFRA resolves site-scoped ULA authority and Bubblewrap runner; RELEASE reconciles #291 after #242 parent movement.
7. Registry custodian restores authorized private v11 and newer-correction access; repository administrators verify branch protection and required checks.

**Final disposition:** PR #288 remains OPEN / DRAFT / UNMERGED. No merge, release, signing, secret provisioning, flashing, physical test, real-payment operation or financial migration. Independent protected signing/anti-rollback witness, crash-atomic financial state, reversible migration tests, QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain unverified. **PRODUCTION NO-GO.**
