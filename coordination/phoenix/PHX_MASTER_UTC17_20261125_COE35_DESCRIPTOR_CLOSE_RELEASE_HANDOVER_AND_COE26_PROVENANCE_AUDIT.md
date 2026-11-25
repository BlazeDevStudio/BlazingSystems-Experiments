# PHX-MASTER UTC17 — 2026-11-25T17:38Z

**Disposition:** coordination update only; PR #288 remains OPEN / DRAFT / UNMERGED; COE #26 remains FROZEN; **PRODUCTION NO-GO**. Strict NO CODEX.

## 1. Exact repository and control-plane identity

- Experiments default branch main: 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5.
- Active v0.6 development branch blazepwifi-v0.6.0-audit-foundation: 2fbd2475e9f54878c316fa7cea2f228386b0e859.
- Legacy v0.5.3 development branch: aad3aade72c1156eecba1fed30907c6d0283b2c5.
- PHX-MASTER starting branch HEAD: f3e743cc82001be925f28c3bbf1cdc37f682f73a.
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243.
- COE integration PR #26: b382d233ff06c8791b1028bed3c617cc7b670d12, OPEN / DRAFT / UNMERGED.
- Master PR #288: OPEN / DRAFT / UNMERGED, base main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b. Starting compare: 571 ahead / 1 behind, merge base f4e8a891. Its 217 existing changed paths are all under coordination/phoenix/. No synchronization with main was attempted.
- Master exact-head Actions query returned zero runs.
- Current ownership manifest blob e4db324315a1b3543fec17a148fbf960170fcb29: 11 routes, DRAFT_REVIEW_ONLY, PHX-MASTER target null. No route or owner was changed.

The uploaded master prompt, README_FIRST, COMMUNICATION_PROTOCOL (BLAZE-COMMS/1), repository AGENTS.md, issue #172, cleanup issue #266, Master PR #288, the current role PRs and COE #26 were re-read. The root AGENTS.md blob is d8777e3b58efc41caa5aa3c969c932aee9103d5f.

## 2. COE RELEASE #35 — new exact-head descriptor cleanup

Current child branch: phoenix/release-build-script-publication-safety-20261117.
- Current PR/docs HEAD: 09e6e508f0813096d64f4a7ea7804f9239690010.
- Exact source/test HEAD: ef869aee3578241bfcae6fda8ed77bb560bebe2c.
- Parent #31/base: 59ed44d0b911e176f1a95b9cf5585ef811ffd31b.
- Current PR remains OPEN / DRAFT / UNMERGED.

The RELEASE-owned fix addresses two descriptor-cleanup failure paths in package_appliance_firmware.py::_open_file_without_symlink_parents(): a parent-directory close failure must not replace the primary file-open exception, and a successfully opened file descriptor must not be orphaned when parent close fails. The correction uses the existing close-preserving policy and does not retry an uncertain interrupted close.

**Test-first and exact evidence**
- Corrected expected RED: [#45664238239](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45664238239), 230 tests, one expected error and one expected failure.
- Exact source/test run: [#45664453496](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45664453496), 230 tests OK / 2 intentional skips; descriptor regressions passed and the single synthetic staged profile passed. The overall shared job then failed closed on 10/10 real appliance profiles because approved site-scoped RFC4193 ULA /48 authority is not defined; ESP32/ESP8266 compile jobs were skipped.
- Current docs-head shared run: [#45664743895](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45664743895), same 230 tests OK / 2 skips, then 10/10 ULA admission failures.
- Mandatory sandbox: [#45664744065](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45664744065), 40/40 host-preflight tests PASS, then Bubblewrap absent (exit 125); namespace and packaging stages did not execute.
- Case-collision guard: [#45664743921](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45664743921) PASS.

The current COE #35 PR description is stale: it still names docs HEAD f611c960 and source/test 237618f4. Its RELEASE_PACKAGER_HANDOVER.md now contains the UTC17 source/test and run evidence; RELEASE must refresh the PR description. PHX-QA must independently review source/test ef869aee. PHX-INFRA/COE must provide an authorized disposable Bubblewrap-capable runner. PHX-CORE and the COE integration owner must decide durable site-scoped ULA /48 authority and distribution semantics; RELEASE must not invent a prefix.

Architecture contract §6.9.1 already states that ULA is installation/site identity, shared by devices on the same LAN, unique across sites, durable across reboot/upgrade/restore, and not a hardware-profile constant. Master owns the contract and gate, not implementation.

## 3. Experiments RELEASE #291 — freshness gate and canonical handover divergence

Current branch: phoenix/release-publisher-isolation-20261115.
- Current PR HEAD: 5e3670f375117d9a6053b921961476684dd34b46.
- Base: draft/softtimer-future-release-signing-pipeline-20261029 at 734b89d9e7792247e8376335c3f3685500ab3f89.
- PR remains OPEN / DRAFT / UNMERGED, 32 changed paths.

Exact current-head CI:
- [Windows #45659245510](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45659245510): handover freshness failed; Windows build and publisher skipped.
- [ESP32 compatibility #45659245624](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45659245624): both pinned core legs PASS.
- [BlazePwifi build #45659246220](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45659246220): mandatory validation failed at handover freshness; Android and all 14 target/platform jobs passed; update bundle, simulations, signing, import and publication skipped.

The failed gate log states that source/workflow changes are newer than experiment/openwrt/BlazePwifi/docs/handover/CURRENT_STATE.md; last checkpoint commit d85eb6a2766781b6cac1807cef461993d8216b84. It lists blazepisonet-softtimer-release.yml, blazepwifi-build.yml, blazepwifi-v053-release.yml and blazerental-v053-lineage2-sign.yml. The gate must not be bypassed.

The three canonical handover files differ between the active v0.6 development branch and #291:
| File | Active v0.6 branch 2fbd2475 | #291 HEAD 5e3670f |
|---|---|---|
| CURRENT_STATE.md | 86d49e27a3e646a084329f4d03e79668464380a5 | 85dd3c1e9254d947c4e75daaeaf3351ef3e105e3 |
| PROJECT_HANDOVER.md | 88ef13d89409104e152254c25aa9b998186fbed9 | 59f8cb183daefb111ccf09f64ac78905d25a4628 |
| CHANGE_LEDGER.md | f16d5774366cf3a4c358dd2a0c2e7ee5e945f668 (empty) | 1950335a062f8f41c65fb60d79fd314afad39b9e |

The v0.6 HANDOVER_POLICY.md says PROJECT_HANDOVER is the top status, CURRENT_STATE is the authoritative current work tree/next action, and CHANGE_LEDGER is append-only; meaningful transitions must be synchronized and CI must not be bypassed. This branch/blob divergence is a reconciliation hazard, not by itself proof of unauthorized editing. Master did not edit any subsystem handover. CORE must publish the canonical current-state/project handover on the active development branch; RELEASE must reconcile its branch and handover records against that exact owner-approved SHA, refresh its stale PR description, then rerun Full and Windows.

The latest #291 PR description still opens with a 2026-11-24 UTC17 snapshot. Its latest docs-only commit 5e3670f adds a CHANGE_LEDGER entry referring to older run IDs #45624183036/#45624182986, not the current #456592 runs. RELEASE owns the refresh.

## 4. HARDWARE #352 and COE #26 — exact migration provenance recheck

Current HARDWARE #352 docs/PR HEAD: 6d743ae16bbb9f1cf604aa3e2a1553083e32a5ec.
Exact source/test HEAD: 1ab1be503bfe11dcfaa522348bc469d52fd040ed.
Parent #349: 2a5c997add4f49fcd74f753101d3a9daac0040bf.

Exact source/test focused CI on 1ab1be503:
- Quarantine [#45657612249](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45657612249) PASS.
- Relay [#45657612290](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45657612290) PASS.
- ESP8266 core [#45657612432](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45657612432) PASS.
- ESP32 core matrix [#45657612283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45657612283) PASS / PASS.

Current docs-head focused CI on 6d743ae:
- Quarantine #45659213057, Relay #45659212875, ESP8266 #45659213036 and ESP32 #45659212997 PASS.
- Full [#45659212942](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45659212942) FAIL at Controller protocol parity: “Missing poll signature check” in the ESP8266 sketch. All 14 target/Android jobs passed; downstream update/simulation/signing/publication jobs were skipped. This remains CORE/QA-owned; no synthetic signature or firmware relaxation was added.

Both exact recursive trees are non-truncated:
- Experiments #352 source: 2,557 entries / 1,978 blobs.
- COE #26 destination: 286 entries / 207 blobs.
- Source ESP32/ESP8266 subtrees: 16 / 60 blobs; destination Hardware/esp32 and Hardware/esp8266: one blob each.
- Source board-local Python helpers: 64; destination: zero.
- Mapped tests: source 47, destination 19; four same-path files, one exact blob and three divergent blobs; 43 source-only and 15 destination-only.
- ESP32 sketch source 1412cf57b70c6ee3061da9831b8d9abf6d58d94e vs destination 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 — different.
- ESP8266 sketch source b99f1f21d8ad1e6df0e403b2b34507f97bd90c16 vs destination c8be98f72596681e36a3ad1f8939bf8046c96887 — different.

License/provenance:
- Product LICENSE matches at 1ee55b94183417be977ca287cd7391f9a6f7e721.
- QRCode LICENSE and TailAdmin LICENSE/NOTICE match at mapped paths.
- Repository root NOTICE.md is absent in COE #26; Tabler LICENSE is absent; BlazeRentalLauncher LICENSE is absent from the candidate tree (the launcher is a Rental surface, not a Hardware subtree).
- The 11-route manifest remains DRAFT_REVIEW_ONLY, with Master target null. COE #26 has five workflows QUEUED / zero jobs and remains FROZEN.

No destination staging, copy, move, overwrite, migration proposal or COE write was performed. Exact blob, licence, import-completeness and test-identity differences remain blockers.

## 5. Other live owner PRs and exact-head CI

| Owner / PR | Exact head | Current evidence / disposition |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build #42698139210 PASS; older scoped evidence only, not financial acceptance. |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | APK identity #45622918340, API21/23 #45622918364, auth/recovery #45622918551 PASS; shared build #45622918468 FAIL. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Synthetic Windows #42462978704 PASS; native COM not invoked. |
| HARDWARE parent #349 | 2a5c997add4f49fcd74f753101d3a9daac0040bf | Quarantine #45603969253 and Relay #45603968961 PASS; Full #45603969181 FAIL. |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Windows #43633486963 PASS; native COM not invoked. |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered runs. |
| RELEASE #291 | 5e3670f375117d9a6053b921961476684dd34b46 | Full/Windows fail at handover freshness; ESP32 compatibility PASS. |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Overlay/Shell #44295049727 and case guard #44295049903 PASS; focused only. |
| COE INTERCON #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage 5.1 #44646341873 and case guard #44646341992 PASS; shared ESP32 #44646341922 FAIL. |
| COE RELEASE #35 | 09e6e508f0813096d64f4a7ea7804f9239690010 | Source/test ef869aee; 230 tests PASS / 2 skips, then ULA gate fails; sandbox blocked by missing Bubblewrap. |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows QUEUED / zero jobs; FROZEN. |

## 6. Registry, cleanup, automation and local execution

- Cleanup issue #266 remains OPEN / 0-of-7. Hardware's narrow cleanup contribution does not complete the seven-role gate; Master checkbox remains unchecked.
- The canonical private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not recovered. No Google Drive connector was exposed; exact-name Library search did not surface v11. Older snapshots/checkpoints were not substituted. No private registry contents or IDs were published.
- The visible “Blaze Hourly Production Development” automation is PHX-HARDWARE, not CORE. The exact title “Blaze Production Continuation” was not surfaced in the visible automation inventory. CORE remains reserved per the owner instruction; no CORE branch or worker was touched or duplicated.
- Local git ls-remote failed because github.com DNS could not resolve. Master Python unittest suite and verify_coordination.py were NOT RUN. No Master Actions run exists. GitHub role CI above is owner-executed remote evidence, not a Master test execution.

## 7. Next exact owner actions

1. PHX-CORE publishes the canonical CURRENT_STATE.md and top PROJECT_HANDOVER.md on active v0.6 development at an exact new SHA, recording current source/workflow changes and one next action.
2. PHX-RELEASE reconciles #291 handover blobs against that canonical CORE SHA, refreshes the stale PR body/ledger evidence, then reruns Full and Windows; do not bypass the freshness gate.
3. PHX-QA independently reviews COE #35 source/test ef869aee and reconciles the HARDWARE poll-signature assertion against the approved CORE producer contract.
4. PHX-CORE and the COE integration owner define durable site-scoped ULA /48 authority, persistence, backup/restore and same-site distribution. PHX-RELEASE implements only that approved interface.
5. PHX-INFRA/COE supplies an authorized disposable Bubblewrap-capable runner with unprivileged namespace support; rerun the mandatory sandbox.
6. COE integration owner completes Hardware-specific source intake, license/NOTICE provenance and exact test/toolchain mapping; keep #26 frozen until exact-source review and owner authorization.
7. Registry custodian restores authorized read-only access to private v11 and newer corrections.
8. PHX-MASTER retries its local coordination validators when GitHub DNS/local checkout access is available.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and explicit owner-authorized release gates remain mandatory and unverified. No merge, release, signing, secret provisioning, firmware flash, physical test, real-payment operation or financial migration occurred.
