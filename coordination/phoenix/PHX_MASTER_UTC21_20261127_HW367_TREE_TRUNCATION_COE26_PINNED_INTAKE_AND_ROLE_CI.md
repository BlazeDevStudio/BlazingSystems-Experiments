# PHX-MASTER UTC21 — #367 tree truncation, pinned COE intake, and live role CI

**Updated:** 2026-11-27T21:42:24Z  
**Task:** PHX-MASTER-20261127T21-PR367-TREE-INTEGRITY-COE26-PINNED-INTAKE  
**Role:** PHX-MASTER — coordination, interface contracts, migration provenance, integration matrix  
**Execution:** Strict NO CODEX. No subsystem source branch was modified.

## 1. Live control plane and exact refs

- Issue #172 remains the single BLAZE-COMMS/1 control plane. The latest Master checkpoint before this run was UTC20 comment [#7227942223](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-7227942223); the latest role checkpoint was HARDWARE UTC21 [#7228371188](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-7228371188). No PHX-MASTER UTC21 checkpoint existed at audit start.
- Cleanup issue #266 remains OPEN / 0-of-7 accepted role gates; last visible cleanup progress is Hardware-only and does not complete the global checklist.
- Experiments refs: main 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5; legacy v0.5.3 development aad3aade72c1156eecba1fed30907c6d0283b2c5; active v0.6 development 2fbd2475e9f54878c316fa7cea2f228386b0e859; Master branch phoenix/master-coordination ba7653f45328add655db7a2106034894dfa9acd9.
- COE refs: main a6513ab4412b4c014eee2863e45cbe32d06cb243; integration candidate branch integration/ecosystem-nonproprietary-candidate-20261111 at b382d233ff06c8791b1028bed3c617cc7b670d12.
- Root AGENTS.md was re-read at blob d8777e3b58efc41caa5aa3c969c932aee9103d5f. The latest Library copies of README_FIRST and COMMUNICATION_PROTOCOL were read; MASTER remains the global dispatcher and release gate, and comments are deduplicated by role plus UTC hour.
- OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29: schema v1, 11 routes, DRAFT_REVIEW_ONLY, PHX-MASTER target null. Its source_ref f4e8a891 is the historical migration baseline, not a live source head.

## 2. Critical new finding — Hardware PR #367 has a truncated Git tree

[Hardware PR #367](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/367) is OPEN / DRAFT / UNMERGED. Its current branch head is fb8ea5a496c81e4d13f2f48fdb143de32565faab, based on #366 head 07fef4e8e1055c06cf5e5c3a0d3829c52be31cc9.

Exact, non-truncated recursive Git tree comparison:

| Tree | Entries | Blobs | Tree nodes |
|---|---:|---:|---:|
| #366 base 07fef4e8 | 2,435 | 1,889 | 546 |
| #367 current head fb8ea5a | 13 | 6 | 7 |

The #367 head removes 1,884 blobs and 539 tree nodes, modifies 5 blobs, and adds 1 handover blob. GitHub reports 1,890 changed files, matching the blob-level delta. The six remaining blobs are two poll-preflight Python test modules plus four handover/project-state documents; no complete firmware/source tree remains in this branch.

The first truncating commit is c97f6460b9340c009ee680e4d42c7103ba05d290 (parent 3f1f7424efe6285f023aee1e0e0a385e5aec2c4b): its tree drops from 2,436 entries to 7. Later commits 32644d14 and fb8ea5a preserve the truncated tree. The PR description is stale: it still names 183650be as source/test head and 3f1f7424 as docs head, while the live head is fb8ea5a. No exact-head Actions runs or combined statuses were returned for fb8ea5a.

**Disposition:** do not merge or use #367 as a migration source. PHX-HARDWARE must restore the full #366 base tree and reapply only the intended test/contract and handover files, then update the PR body and rerun exact-head CI. PHX-MASTER did not edit the Hardware branch.

## 3. P0 #177 and controller interface recheck

Issue #177 remains OPEN. The live active-v0.6 sketches still perform a blocking poll before the first coin-input sample:

| Board | Exact source blob | 3,500 ms timeout | Blocking poll | First coin sample |
|---|---|---:|---:|---:|
| ESP8266 | 12c4bb82b6fddafe813674a0b5f692c1d3634073 | line 263 | line 354 | line 357 |
| ESP32 | 29f1125d52ff474a0d028ad41f7af201be1f0f9d | line 230 | line 314 | line 318 |

The current main CGI producer blob 2e3a1430d08cc6606429a042df3b5848f53c7267 has register|ping at line 63 and poll at line 68, but neither controller response block emits response_sig. The later response_sig fields at member snapshot/auth/mutation endpoints authenticate member operations, not controller poll or disposition. CORE owns the canonical authenticated contract; HARDWARE owns firmware; QA owns independent vectors and regression semantics. Keep controller admission and coin/relay actuation deny-only until those owners resolve the contract.

## 4. Current owner PRs and exact-head CI

| Owner PR | Live head | Exact evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build [#42698139210 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210), scoped only |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | API [#45622918364 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), auth/installer [#45622918551 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551), APK identity [#45622918340 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340); shared build [#45622918468 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) at mandatory handover freshness and ESP32 compile |
| RENTAL #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | Build [#43653329229 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229), native auth [#43653329235 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows synthetic [#42462978704 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704); native COM acceptance NOT TESTED |
| HARDWARE #367 | fb8ea5a496c81e4d13f2f48fdb143de32565faab | No exact-head run or combined status; destructive 1,890-file PR diff |
| HARDWARE #357 | 963c37135797e0d570ef910596c098bb9d902779 | Poll-intake [#46067421658 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46067421658); Mbed [#46067421664 PASS, 3/3](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46067421664); Native [#46067421738 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46067421738) at PAY-0745; Full [#46067421812 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46067421812) at Controller protocol parity |
| HARDWARE #354 | fc842342596786e072630179acfbbc4feeb2ba02 | Poll-intake [#45864684458 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684458); Mbed [#45864684325 PASS, 3/3](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684325); Full [#45864684497 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684497); Native [#45864684295 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684295) at PAY-0745 |
| QA #290 / #292 | 5c29d15994cee1279058f1eca12f2a3180704292 / 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #290 Windows synthetic [#43633486963 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963); #292 no exact-head run/status |
| RELEASE #291 | bf339a76964a1abe2412fac45392fe06a8e66418 | No exact-head run/status; PR reports mergeable=false |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Shell [#44295049727 PASS](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727); case-collision [#44295049903 PASS](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) |
| COE RELEASE #35 | bc57ba8ecc5245ce538c6770a45bb25e2b8b5ef3 | Case-collision [#45897198239 PASS](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45897198239); ImageBuilder [#45897198204 FAIL](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45897198204) because bubblewrap is unavailable; Hardware/Shared [#45897198326 FAIL](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45897198326) at profile staging |
| COE QA #32 / PISONET #30 / #28 | 29b6fe08b10688182d981a66745f482758bd6630 / 4897348d94a0cf7884ecd53244bfcd59e7bf2fbc / b21b04617d38a177260258de2d56b24382822117 | Windows synthetic [#43653540607 PASS](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653540607), [#43653415598 PASS](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653415598), [#43632393888 PASS](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43632393888) |

COE #26 remains OPEN / DRAFT / FROZEN. Its five candidate workflows are CANCELLED: #43096752563, #43096752800, #43096752557, #43096752609, #43096752632. Master #288 has no exact-head workflow run or combined status.

## 5. COE #26 pinned intake and exact route provenance

Both exact recursive trees are non-truncated. The source pin declared by SOURCE_INTAKE schema 8 is 6d4c9b487af4d768c4d7627654d119417fcc6e00 (2,391 entries / 1,845 blobs); the live #366 source baseline used for current route review is 07fef4e8e1055c06cf5e5c3a0d3829c52be31cc9 (2,435 / 1,889); COE #26 is b382d233ff06c8791b1028bed3c617cc7b670d12 (286 / 207).

SOURCE_INTAKE blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f has 61 runtime rows. Every row's declared source blob, destination blob and mode matches the actual pinned-source and #26 trees (0 mismatches). Its summary is off by one: the 61 rows count 46 byte-identical and 15 derived, not the declared 47 and 14. The destination branch field still names feature/pisowifi-cleanup-stabilization rather than the live #26 branch; the exact row blobs are nevertheless present at #26. Only one of those 61 runtime files has drifted between the pinned source and current #366 source: openwrt/rootfs/usr/lib/blazepwifi/common.sh (pinned 4ccb1077; current 50fa2d02).

The intake test map has 4 rows (2 byte-identical, 2 derived), all exact source/destination blob+mode rows. It also lists 15 derived tests; 11 remain NOT_RUN with no hardware evidence. The intake's hardware_tested/full_ci_tested fields do not constitute acceptance. The #26 candidate workflows remain cancelled.

Current #366 source-tree to #26 route comparison:

| Route | Source blobs | Destination blobs | Exact | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| CORE library | 20 | 20 | 14 | 6 | 0 | 0 |
| CORE Vendo CGI | 1 | 1 | 0 | 1 | 0 | 0 |
| RENTAL Android | 983 | 8 | 0 | 0 | 983 | 8 |
| RENTAL standalone profiles (manual overlapping Rental/ route) | 30 | 19 | 0 | 2 | 28 | 17 |
| RENTAL standalone server | 12 | 4 | 0 | 1 | 11 | 3 |
| PISONET SoftTimer | 44 | 47 | 16 | 9 | 19 | 22 |
| HARDWARE ESP32 | 4 | 1 | 0 | 1 | 3 | 0 |
| HARDWARE ESP8266 | 18 | 1 | 0 | 1 | 17 | 0 |
| QA PisoWiFi tests | 151 | 19 | 2 | 2 | 147 | 15 |
| RELEASE workflow reimplementation | 1 | 1 | 0 | 1 | 0 | 0 |

The broad RENTAL target prefix overlaps Rental/android and Rental/openwrt and is explicitly manual-file-mapping-required / copy_permitted=false; do not aggregate or recursively copy it. The ten source LICENSE/NOTICE artifacts have only four destination counterparts; six source notice/license paths are missing. HARDWARE_FIRMWARE_AUDIT.md contradicts itself: its first section says controller sketches were not copied, while its later addendum says they were migrated via PR #27; the exact #26 tree contains one divergent sketch under each board route. No migration staging, copying, moving, overwriting, cherry-picking, rebase or retarget was performed.

## 6. Private registry and automation deconfliction

Exact Library title search did not find canonical BLAZE_PROJECT_REGISTRY_v11_20261027.json or newer corrections. It surfaced v3–v7 snapshots, October 26 artifact-manifest/sync-ledger snapshots, and a November 9 checkpoint reference to v11. No dedicated Google Drive connector is exposed in this runtime. These older records were not substituted, and no private registry contents or IDs were published.

The automation inventory contains 17 tasks. The active Blaze Hourly Production Development task is explicitly PHX-HARDWARE. No exact-title Blaze Production Continuation entry surfaced, so the separately described CORE automation is not independently confirmed by the inventory. CORE #252 was left untouched; no competing CORE worker or automation was created or modified.

## 7. Master execution and disposition

PR #288 remains OPEN / DRAFT / UNMERGED on phoenix/master-coordination. It has 260 changed paths, all under coordination/phoenix/. Compared with live main 6be5d19b, it is 676 commits ahead / 1 behind with merge base f4e8a891. No rebase, retarget or merge was performed. Master Python tests and verify_coordination.py were NOT RUN because no local checkout/test runner was available; the tree and manifest comparisons above are read-only Git/API audits, not repository test executions. No exact-head Master Actions/status exists.

**Next actions**
1. PHX-HARDWARE: restore the complete #366 tree on #367, reapply only the intended deny-latch contract/tests and handover, update the PR body, and rerun exact-head focused/Full CI.
2. PHX-QA: repair Controller protocol parity and PAY-0745 assertions without adding decoy config fields or weakening fail-closed behavior.
3. PHX-CORE + PHX-HARDWARE + PHX-QA: publish and independently verify authenticated controller register/poll/receipt/disposition semantics.
4. COE integration owner: correct SOURCE_INTAKE summary counts and destination branch pin, reconcile all missing/divergent route blobs, tests and licenses, and keep #26 frozen until owner-reviewed provenance is complete.
5. Registry custodian: provide authorized canonical v11 and newer corrections plus current manifest/ledger; repository administrator: expose an authorized Drive connector and a non-Codex Master checkout/test path.

**Production remains NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain unverified. No merge, release, signing, secret provisioning, flash, physical test, real payment operation or financial migration occurred.
