# PHX-MASTER UTC16 — live COE #35 manifest publication recheck, COE #26 exact-tree provenance, and owner CI reconciliation

**Observed:** 2026-11-25T16:35:07Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Scope:** coordination/phoenix/, architecture/interface contracts, cross-repository provenance and integration matrices only. Strict NO CODEX.

## 1. Live repository identities

| Ref | Exact SHA | State |
|---|---|---|
| Experiments default main | 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 | default branch |
| Active v0.6 development blazepwifi-v0.6.0-audit-foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 | development |
| Legacy v0.5.3 development | aad3aade72c1156eecba1fed30907c6d0283b2c5 | legacy development |
| Master phoenix/master-coordination | 97bf3a52d58ac9f6a6f4dcfb66231a797da931e4 | pre-update HEAD |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 | destination default |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | OPEN / DRAFT / FROZEN |

Experiments main...Master is 566 ahead / 1 behind, merge base f4e8a891aed8af86d5fd315d28750a0ac3a7372b. The one main-only commit is the unrelated CallerID prompt addition. No merge, rebase, cherry-pick, retarget or synchronization was performed.

Master PR #288 is OPEN / DRAFT / UNMERGED, base main at f4e8a891, 216 changed paths, all within coordination/phoenix/. Exact Master-head PR workflow query returned zero runs. The branch metadata endpoint reports protected=false for main, active development and Master; do not assume effective required-check enforcement.

## 2. Current owner PRs and exact-head CI

These are remote owner workflow results, not tests executed by PHX-MASTER.

| Owner / PR | Current exact head | Exact-head evidence and disposition |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; old scoped evidence only, not financial acceptance. CORE source and canonical handover remain reserved to the separate owner. |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | APK [#45622918340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340), API [#45622918364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), auth/recovery [#45622918551](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551) PASS. Shared build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL: the validate job reports source/workflow newer than the CORE-owned docs/handover/CURRENT_STATE.md; ESP32 job also failed, with root cause not established from the retrieved job summary. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Synthetic Windows [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM acceptance not invoked. |
| HARDWARE #352 | PR/docs 1d376d3b9b5fec11c4e21776a96462c5c05706f9; source/test bb519e6a2129f79723b9f7fb5903b4443149fcd0 | Quarantine [#45648827942](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45648827942), Relay [#45648827985](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45648827985), ESP8266 [#45648827975](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45648827975), ESP32 [#45648828161](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45648828161) PASS. Full [#45648828144](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45648828144) FAIL at the inherited Missing poll signature check in the ESP8266 sketch. The PR description is stale: it still pins a19cb235 / d3e36ae. HARDWARE owns its PR-description refresh; CORE owns the producer contract; QA owns independent assertion reconciliation. |
| HARDWARE parent #349 | 2a5c997add4f49fcd74f753101d3a9daac0040bf | Quarantine [#45603969253](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45603969253) and Relay [#45603968961](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45603968961) PASS; Full [#45603969181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45603969181) FAIL. Parent results are not transferred to child #352. |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; native COM lab not invoked. |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered runs; no pass claimed. |
| RELEASE #291 | b3e4fa22c4f4b8cd3009437a06a7eec56420d411 | ESP32 compatibility [#45624182886](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45624182886) PASS. Full [#45624183036](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45624183036) and Windows [#45624182986](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45624182986) FAIL at the CORE-owned CURRENT_STATE freshness gate; target build/publisher stages skip. |
| COE RELEASE #35 | PR/docs 204084307b257154470934a17da4efb5794bdb69; source/test a05188c632e207c022319277d6c11bce7e348e65 | Current-head shared [#45653690960](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45653690960): 228 tests PASS / 2 intentional skips, then 10/10 appliance profiles fail closed because approved site-scoped RFC 4193 ULA /48 authority is missing; ESP32/ESP8266 compile jobs skip. Sandbox [#45653685548](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45653685548): 40/40 host tests PASS, then Bubblewrap unavailable (exit 125); namespace and packaging steps skip. Case-collision [#45653687424](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45653687424) PASS. |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Overlay/Shell [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case-collision [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS; focused only. |
| COE INTERCON #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case guard [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared ESP32 compile [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL. |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows remain QUEUED / zero jobs. Candidate remains FROZEN. |

## 3. New COE #35 owner delta — audited, not taken over

COE #35 advanced from 50f5fa17 to docs/PR HEAD 204084307b. Its source/test correction is a05188c6; the final 2040843 commit changes only the RELEASE handover.

The RELEASE-owned defect was a same-UID artifact mutation window between the initial artifact scan and durable manifest-pair publication. The test-first regression mutates firmware.bin after the initial scan. The corrected writer re-scans the pinned artifact directory after writing the manifest pair, excludes only the two metadata outputs created by this invocation after device/inode identity checks, compares remaining path/size/SHA-256 records and rolls back only the invocation's metadata pair on mismatch.

Evidence:
- Expected RED [#45652864580](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45652864580): one expected regression failure, 2 intentional skips.
- Superseded first source attempt [#45653007798](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45653007798): 3 failures, 2 errors, 2 skips; not accepted.
- Corrected source/test [#45653320352](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45653320352): 228 tests PASS / 2 skips.
- Current docs-head run [#45653690960](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45653690960) repeats 228 PASS / 2 skips, then fails closed at 10/10 ULA profiles.
- Sandbox [#45653685548](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45653685548): 40 host tests PASS, Bubblewrap absent / exit 125.
- Case guard [#45653687424](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45653687424): PASS.

The post-publication recheck does not make the staging tree immutable after the function returns; downstream consumers must still verify published checksums and the staging directory must remain private to the build invocation. PHX-QA must independently review source/test SHA a05188c6. RELEASE must refresh its own PR description and handover pointers to 2040843. MASTER does not edit RELEASE source or its branch.

## 4. COE #26 exact source/destination audit — no staging

Both recursive Git trees were read at exact commits and were non-truncated.

| Measure | Experiments HARDWARE #352 source | COE #26 destination |
|---|---:|---:|
| Complete tree entries | 2,557 | 286 |
| Blob entries | 1,978 | 207 |
| ESP32 board-subtree blobs | 16 | 1 |
| ESP8266 board-subtree blobs | 60 | 1 |
| Board-local Python helpers | 64 | 0 |
| Tests under mapped test roots | 47 | 19 |

Mapped test identity: one same-relative-path exact blob, three same-path divergent blobs, 43 source-only files and 15 destination-only files.

| Artifact | Current source blob | COE #26 destination blob | Finding |
|---|---|---|---|
| ESP32 sketch | 1412cf57b70c6ee3061da9831b8d9abf6d58d94e | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 | Different |
| ESP8266 sketch | b99f1f21d8ad1e6df0e403b2b34507f97bd90c16 | c8be98f72596681e36a3ad1f8939bf8046c96887 | Different |
| Root NOTICE.md | f6d92cd21465312be5993631fe26977219be0fb9 | Missing | Gap |
| Product LICENSE | 1ee55b94183417be977ca287cd7391f9a6f7e721 | Pisowifi/LICENSE, same blob | Match |
| TailAdmin LICENSE / NOTICE | cb92d4176b21b0594e5a6caf94d79340505e3d33 / f0425bbbe34c1227311098173b1eae0c3e2a807b | Same blobs at mapped vendor paths | Match |
| Tabler LICENSE | 22ee8122400915cbff18e5f69368fa9eea6145eb | Missing | Gap |
| BlazeRentalLauncher LICENSE | c5b1efa7aac764ae6d8da63476a2d5cec02a6a5d | Missing | Gap |

The destination contains Pisowifi/SOURCE_INTAKE.json and Pisowifi/MIGRATION_MAP.md, but no Hardware-specific SOURCE_INTAKE or MIGRATION_MAP. The 11-route OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29, status DRAFT_REVIEW_ONLY; PHX-MASTER target is null and both Hardware board routes are selective-review only. This is not recursive-copy authority.

No source files were staged, copied, moved, overwritten or proposed for migration. COE #26 remains frozen.

## 5. Coordination, registry, tests and disposition

- Control plane #172 remains the canonical BLAZE-COMMS/1 inbox. The preceding PHX-MASTER checkpoint is UTC15; this UTC16 checkpoint is a new scheduled-hour message.
- Cleanup #266 remains OPEN / 0-of-7. The Master cleanup checkbox remains unchecked because the duplicate/dead-code inventory is not complete.
- Experiments root AGENTS.md and README, README_FIRST, COMMUNICATION_PROTOCOL, current Master INDEX, ROLE_ASSIGNMENTS, INTEGRATION_MATRIX, ARCHITECTURE_CONTRACTS, REPOSITORY_ROUTING, AUDIT_SUMMARY and OWNERSHIP_ROUTES were re-read. COE main README is present; COE root AGENTS.md returned 404.
- Private BLAZE_PROJECT_REGISTRY_v11 and newer corrections remain NOT_RECOVERED. Authorized Library search found older registry snapshots only; no substitute was used, no private contents or identifiers were published, and no Google Drive connector was exposed.
- The automation inventory exposes the active PHX-MASTER task and an active Blaze Hourly Production Development task whose prompt acts as PHX-HARDWARE. It did not expose a task with the exact title Blaze Production Continuation. Per the owner directive, CORE remains reserved and untouched; no competing CORE worker or source edit was started.
- Remote role CI above was inspected. Master exact-head workflow query returned zero runs. Master Python unittest suite and verify_coordination.py were NOT RUN because no authenticated local checkout is available; prior ordinary Git access failed DNS resolution. Read-only GitHub tree/blob/PR/CI inspection is not a product test.
- No subsystem source, COE destination, signer, secret, payment system, firmware, hardware or customer data was modified.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible financial migration tests, independent QA, native hardware acceptance, 150 real power cuts, 30-device/24-hour soak and explicit owner-authorized release gates remain mandatory.

## 6. Next owner actions

1. PHX-RELEASE refreshes COE #35 PR/handover pointers to current PR/docs HEAD 2040843 and preserves source/test SHA a05188c6.
2. PHX-QA independently reviews the artifact-mutation publication regression at a05188c6 and reconciles the inherited Hardware poll-signature assertion without weakening default-deny.
3. PHX-CORE publishes the canonical CURRENT_STATE freshness checkpoint and the authenticated poll/register producer contract; RELEASE then reruns #291 against that exact source.
4. PHX-HARDWARE refreshes #352's own PR description to 1d376d3 / bb519e6; QA owns the assertion review.
5. COE integration owner adds Hardware-specific intake/map, exact toolchain/test/license provenance and resolves destination CI queueing before any migration proposal.
6. PHX-CORE / MASTER / COE owner define approved durable site-scoped ULA /48 authority; PHX-INFRA supplies an authorized disposable runner with Bubblewrap and unprivileged namespace support.
7. Registry custodian restores authorized provenance-only access to private Drive v11 and newer corrections.

**Final Master state at report creation:** phoenix/master-coordination@97bf3a52d58ac9f6a6f4dcfb66231a797da931e4; PR #288 OPEN / DRAFT / UNMERGED. This report is a coordination-only audit; no production gate is approved.
