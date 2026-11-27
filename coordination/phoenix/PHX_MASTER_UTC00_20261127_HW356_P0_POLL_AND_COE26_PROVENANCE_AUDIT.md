# PHX-MASTER UTC00 — exact-head Hardware #356, P0 poll sequence and COE #26 provenance audit

**Audit time:** 2026-11-27T00:47:02.187Z  
**Role:** PHX-MASTER — coordination, interface contracts, migration provenance and integration matrix only.  
**Disposition:** BLOCKED / COE #26 FROZEN / PRODUCTION NO-GO.  
**Execution boundary:** No Codex. No subsystem source edits, no migration staging, no merge, no release, no flash, no secrets, no payment operation and no physical test.

## 1. Live refs and coordination state

| Ref | Exact state |
|---|---|
| Experiments default main | 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 |
| Experiments blazepwifi-v0.5.3-development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Active v0.6 audit foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Master phoenix/master-coordination at audit start | a56750fb5fa52e190139901c36f89b4351ca8c3e |
| COE default main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |

PR #288 is OPEN / DRAFT / UNMERGED. Before this UTC00 update it compares 647 commits ahead / 1 behind current main and has 243 changed paths. The Master tree contains exactly 243 coordination/phoenix entries. The ownership route manifest remains blob e4db324315a1b3543fec17a148fbf960170fcb29, 11 routes, DRAFT_REVIEW_ONLY, with the PHX-MASTER target null. Its source_ref remains the historical f4e8a891..., not current main or the active v0.6 source; its destination pin remains PR #26 b382d233.... The manifest was not silently rewritten.

Issue #172's latest PHX-MASTER checkpoint before this run is UTC23 comment [#7205896060](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-7205896060). No PHX-MASTER UTC00 message ID was present at pre-write deduplication. Cleanup issue #266 remains OPEN / 0-of-7.

## 2. P0 coin-pulse sequence revalidated at current v0.6 HEAD

The current blazepwifi-v0.6.0-audit-foundation at 2fbd2475 still performs synchronous poll before the next coin input sample:

| Board | 3.5-second HTTP timeout | Poll call | Next input sample |
|---|---:|---:|---:|
| ESP8266 | line 263 | line 354 | line 357 |
| ESP32 | line 230 | line 314 | line 318 |

Issue #177 still describes a host-simulated missed pulse. Its body pins older source 9df0a7e7...; the current source was re-read at 2fbd2475... and the ordering remains. This is a source-level P0 risk, not physical acceptance. No coin slot, relay, money state, power-loss test or hardware was operated.

Ownership remains: HARDWARE owns local intake inhibit/nonblocking capture; CORE owns authenticated poll/receipt/disposition; QA independently verifies the same exact source SHA. MASTER owns only the cross-role contract and evidence gate.

## 3. Current Hardware PR #356 — exact-source failure is now a parent-topology gap

Live PR #356 head advanced during this audit to 660660aebc164fdc1958547d0d5e8f82656fd47e, branch phoenix/hardware-storage-preflight-device-separation-20261126-utc23, based on v0.6 2fbd2475....

- Exact-source run [#45918239625](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45918239625), job 140242513035: FAIL. The synthetic test reports unsafe physical-parent layout accepted: scratch sibling partition shares root disk.
- The current tools/v060_lab_block_parent_guard.sh only compares the scratch major:minor string against the protected root/overlay/ROM/boot major:minor strings. It does not resolve /sys/dev/block ancestry or parent partitions. It therefore accepts a sibling partition on the same physical disk, despite the test requiring that layout to fail closed. The current test fixture now has real newline formatting; the earlier escaped-newline defect was corrected in commit 660660a.
- Full run [#45918239713](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45918239713) was IN_PROGRESS at readback. Its validate job 140242649128 already FAILED the mandatory handover freshness gate because the canonical checkpoint remains b58b59536e08e49d73ecb6c5e3bbbf7bf492048e; ESP8266 and some optional firmware jobs had passed, while ESP32/Android and several firmware jobs were still running. Do not treat this as a terminal Full result.
- PR #356 description still cites the older b58b595 docs head and earlier CI, so its body/handover is stale relative to 660660a.

**Hardware next action:** resolve the actual sysfs parent/partition ancestry (and reject unsupported device-mapper topology) or fail closed; add tests for sibling partitions and overlay upper storage; update the canonical handover and PR body at the exact new source SHA; then rerun exact-source and Full CI. MASTER did not edit the Hardware branch.

## 4. Other live owner PR/CI evidence

| Role / PR | Exact head | Current observed evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Scoped build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; no financial acceptance implied |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | API21/API23 [#45622918364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), native auth [#45622918551](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551), APK identity [#45622918340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340) PASS; shared build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows synthetic [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM acceptance NOT TESTED |
| HARDWARE #353 | f527b33c9e391a9a66490388d96f06d6c8761dfa | Relay [#45871096516](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45871096516) and Quarantine [#45871096480](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45871096480) PASS; Full [#45871096425](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45871096425) FAIL |
| HARDWARE #354 | fc842342596786e072630179acfbbc4feeb2ba02 | Poll-deny [#45864684458](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684458) and Mbed TLS [#45864684325](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684325) PASS; Full [#45864684497](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684497) and Native [#45864684295](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684295) FAIL at inherited QA contract assertions |
| HARDWARE #355 | fa33bd1841494e0c271f99b18fbe244546ebd0b9 | Poll [#45907943770](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45907943770) and Mbed TLS [#45907943783](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45907943783) PASS; Full [#45907943784](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45907943784) and Native [#45907943785](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45907943785) FAIL |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Windows synthetic [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No workflow run at exact head |
| RELEASE #242 | 36c0d0bb3e58786359555b307bb784f720f023ce | No workflow run at exact head; latest UTC23 report is local RED/GREEN only |
| RELEASE #291 | bf339a76964a1abe2412fac45392fe06a8e66418 | No workflow run at exact head |

These are exact-head run observations, not cross-PR acceptance. No source branch owned by these roles was changed by MASTER.

## 5. COE #26 destination candidate remains FROZEN

Exact recursive trees: source Hardware #356 head 660660a = 2395 entries; COE PR #26 head b382d233 = 286 entries.

**Test identity under the manifest's explicit experiment/openwrt/BlazePwifi/tests/ → Pisowifi/tests/ route:**

| Identity | Count |
|---|---:|
| Source test files | 153 |
| Destination test files | 19 |
| Byte-identical mapped tests | 2 |
| Divergent mapped tests | 2 |
| Source-only tests | 149 |
| Destination-only tests | 15 |

Firmware blobs remain different:

- experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino → Hardware/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino: source 29f1125d52ff474a0d028ad41f7af201be1f0f9d, destination 3cc7ec54b476943dc04a8d1af5e2df5fe054e422, identical=false
- experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino → Hardware/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino: source 12c4bb82b6fddafe813674a0b5f692c1d3634073, destination c8be98f72596681e36a3ad1f8939bf8046c96887, identical=false

The current source has 9 BlazePwifi license/notice files in the inspected subtree; the destination tree has only 4 license/notice paths overall: Pisowifi/LICENSE, QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE. Root NOTICE, Tabler LICENSE, BlazeRentalLauncher LICENSE and test-vendor jsQR LICENSE counterparts are absent. The new #356 storage-preflight test, parent guard, mountinfo guard and workflow are not mapped by the 11-route manifest and have no corresponding candidate destination paths. No move is proposed.

COE #26 still has five queued workflow runs at its exact head; no completed exact-head result was observed. The candidate remains DRAFT / FROZEN. Do not stage or copy until source pins, per-file blobs, test identities, licence/NOTICE scope, imports and executable CI are reconciled by the integration owner.

## 6. Policy, registry and execution limitations

- Read the current public BLAZE_CLOUD_ARTIFACT_POLICY.md and BLAZE_CLOUD_STORAGE_HANDOVER.md from BlazeDevStudio/BlazingSystems. They require the canonical restricted Drive registry and explicitly say to report BLOCKED if the Drive connector is unavailable.
- The exact private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not available through the connected Drive/Library surface. Search surfaced older snapshots only. No substitute was used and no private Drive IDs or contents were copied into GitHub.
- The Master product Python suite and verify_coordination.py were NOT RUN; no authenticated local checkout or exact-head Master Actions result is available. This report's recursive-tree/blob comparisons are source inspection, not product tests.
- GitHub branch metadata reports protected=false for Experiments main, v0.5.3 development, active v0.6 and COE main; this is not a complete ruleset audit.
- Cleanup #266 remains OPEN / 0-of-7. No role cleanup gate is claimed complete.

## 7. Next owner actions

1. HARDWARE fixes the #356 sysfs parent/partition gap, refreshes its handover/PR body and reruns exact-head tests.
2. HARDWARE + CORE + QA revalidate issue #177 against current v0.6 2fbd2475; implement local intake protection and the authenticated poll/receipt/disposition contract without unsigned re-enable or unsafe pending clear.
3. COE integration owner reconciles #26's exact source pins, firmware/test blobs, import completeness, licenses and five queued workflows before proposing any staging.
4. Registry custodian restores authorized private Drive access to v11 and newer corrections.
5. MASTER reruns its own coordination validators when an authenticated checkout or Master CI is available.

**PRODUCTION NO-GO remains mandatory:** independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates. No merge, release, flash, secret provisioning, payment operation or physical test occurred.
