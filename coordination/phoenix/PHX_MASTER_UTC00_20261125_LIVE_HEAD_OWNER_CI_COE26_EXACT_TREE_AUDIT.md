# PHX-MASTER UTC00 — live owner CI, COE #26 exact-tree and registry-access audit

**Observed:** 2026-11-25T00:37:39Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Execution:** Strict NO CODEX. Read-only inspection of owner branches and COE destination; coordination-only writes in this PR.

## 1. Exact repository and control-plane state

- Experiments default branch: main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Experiments development branch: blazepwifi-v0.5.3-development at aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Master coordination branch starting HEAD: 263c679248aeb0eaeeefeb4190060defa07aee02.
- COE default branch: main at a6513ab4412b4c014eee2863e45cbe32d06cb243.
- COE integration candidate: PR #26 at b382d233ff06c8791b1028bed3c617cc7b670d12, OPEN / DRAFT / FROZEN.
- Master PR #288 was OPEN / DRAFT / UNMERGED at the starting HEAD, with 205 changed paths, all under coordination/phoenix/.
- Control-plane issue #172 remains OPEN. Cleanup issue #266 remains OPEN / 0-of-7.
- OWNERSHIP_ROUTES.json is unchanged at blob e4db324315a1b3543fec17a148fbf960170fcb29: 11 routes, DRAFT_REVIEW_ONLY, PHX-MASTER target null. It is a routing proposal, not copy/move authorization.
- Branch API records report protected=false for Experiments main, Experiments development and COE main. Direct protection endpoints returned 403; Master-branch protection and effective ruleset enforcement remain UNVERIFIED.

## 2. Current owner PRs and exact-head CI

| Owner / PR | Exact source/test and PR head | Current evidence | Required owner action |
|---|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Scoped build #42698139210 SUCCESS | CORE retains financial/poll contract and canonical CURRENT_STATE. Separate CORE continuation not touched. |
| RENTAL #328 | 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | APK #44782114384 PASS; API #44782114393 PASS; build #44782114390 FAIL | RENTAL owns its source/build blocker. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Synthetic Windows #42462978704 PASS | PISONET retains COM/SoftTimer source and inherited tests. |
| HARDWARE #347 | 960184670379f01e20f0e7e8bc23b3e5eedacd3f | Quarantine #45299741995 FAIL; Relay #45299742437 FAIL; build #45299741993 FAIL | HARDWARE owns the parent branch; child #349 results do not transfer to #347. |
| HARDWARE #348 | eb7afcb2ba0d1e84054c052c8b129cb51a91d062 | Header-focused #45352513178 PASS; build #45352513177 FAIL at missing mbedtls/sha256.h | HARDWARE owns the compile dependency correction. |
| HARDWARE #349 | Source/test 353231c60fe09e4694fa73e3a3a1e64c5d21353d; final docs/PR 2fd939ef90db4f68b12f33732733697606c36f9b | Source Quarantine #45512634485 PASS; Relay #45512634525 PASS; Full #45512634648 FAIL. Docs-head Quarantine #45513508003 PASS; Relay #45513508200 PASS; Full #45513508008 FAIL at inherited Missing poll signature check. All 14/14 firmware/platform plus Android jobs passed; dependent release stages skipped. | HARDWARE keeps deny-default and records the terminal Full failure. CORE owns the authenticated poll producer contract; QA owns independent assertion review. PR body currently carries the current source/test and docs-head tuple. |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Windows #43633486963 PASS | QA retains independent native COM review. |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered runs returned | No pass claimed; QA retains recipient regression. |
| RELEASE #291 | 53fc8a1c558f80adde19dc675b879c78797f0cd5 | Windows #45485465901 FAIL; build #45485465992 FAIL at CORE-owned CURRENT_STATE freshness; ESP32 compatibility #45485465888 PASS | CORE refreshes canonical handover; RELEASE reruns exact-head workflows; PISONET retains its tests; QA independently reviews. |
| COE RELEASE #35 | Source/test a514e57d789d821cea0f0a29e3e864dad0570046; final handover/PR ecc1d3d4ad0c4564743a17e8155d524d805738de | Source/test shared #45517568556 and PR #45517576258: 217 PASS / 2 intentional skips, then 10/10 profiles fail closed for missing approved site ULA /48. Source/test sandbox #45517576269: 40/40 host preflight PASS, then Bubblewrap missing / exit 125. Source/test case #45517576300 PASS. Docs-head shared #45518588715: 219 total tests (217 pass, 2 skipped), then 10/10 ULA failures. Docs-head sandbox #45518588755: 40 tests pass, then Bubblewrap missing / exit 125. Docs-head case #45518588828 PASS. | RELEASE handover is updated at UTC00, but the PR description still advertises UTC15 and old pins. RELEASE must refresh its own PR body. Obtain approved site ULA authority and a disposable Bubblewrap runner; do not invent a prefix or bypass sandbox. |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Overlay #44295049727 PASS; case guard #44295049903 PASS | CORE retains its separate COE contract work. |
| COE INTERCON #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage 5.1 #44646341873 PASS; case #44646341992 PASS; shared Hardware #44646341922 FAIL | Keep the lab bridge separate from production finance and hardware acceptance. |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows queued: #43096752609, #43096752632, #43096752800, #43096752563, #43096752557. Zero completed jobs/statuses. | Integration owner repairs provenance, tests and licenses before any staging proposal. |

## 3. HARDWARE #349 exact source/test and docs-head reconciliation

The current source/test anchor is 353231c60fe09e4694fa73e3a3a1e64c5d21353d; final docs/PR HEAD is 2fd939ef90db4f68b12f33732733697606c36f9b. The five-commit compare from the earlier 0aba4cd source pin changes two handover documents and one existing lab file; it does not change the production sketches.

The current source lab file experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab_edge_race_contracts.py has blob 6b58d3b25614242109043b482e335cdf124c5a70. The routed COE Hardware/esp8266 subtree has no corresponding Python helper; it contains only one destination sketch. This is another source-only test/lab artifact, not a proposed migration.

The Full failure is the inherited QA-owned Missing poll signature check. Focused Relay/Quarantine CI and target compilation are SIMULATED / CI VERIFIED evidence only. Do not synthesize response_sig, weaken the assertion, or enable positive poll/coin admission. Physical coin/relay/electrical acceptance remains NOT TESTED.

## 4. COE #35 exact-source versus final PR-head freshness

The current RELEASE-owned handover blob is 663b968ae8eea9b757338f3d5bc9fd72e452c470 at final handover/PR HEAD ecc1d3d4. Its UTC00 block identifies source/test HEAD a514e57d. The PR description is stale at UTC15 and does not identify this current source/test and final docs/PR tuple. A current handover does not silently refresh the PR description; RELEASE owns that update.

At exact source/test HEAD a514e57d, the shared/firmware tests pass (217 passed, two intentional skips) before all ten appliance profiles fail closed because no approved site-scoped RFC 4193 ULA /48 is defined. The sandbox host preflight passes 40/40, then the required Bubblewrap gate exits 125 because Bubblewrap is absent. The case-collision guard passes.

At final PR HEAD ecc1d3d, exact-head shared CI again records 217 passing tests and two skips before the same 10/10 ULA authority failure; sandbox again fails closed at missing Bubblewrap; case-collision passes. No firmware compile, ImageBuilder output, approved binary, signer or publication is produced by these failing workflows.

## 5. COE #26 exact recursive tree, source intake, tests, hardware and licensing

All three recursive trees were non-truncated at the exact refs:
- Historical intake source 6d4c9b487af4d768c4d7627654d119417fcc6e00: 2,391 entries.
- Current HARDWARE #349 source/test 353231c60fe09e4694fa73e3a3a1e64c5d21353d: 2,530 entries.
- COE #26 destination b382d233ff06c8791b1028bed3c617cc7b670d12: 286 entries.

The ownership route manifest names Experiments main@f4e8a891 as a high-level source reference, while Pisowifi/SOURCE_INTAKE.json (blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f) pins historical source 6d4c9b. Keep these provenance anchors separate.

SOURCE_INTAKE has 61 runtime rows. All 61 source blobs/modes match the historical pinned tree and all 61 destination blobs/modes match the declared destination pins. Recomputed classification is 46 byte-identical / 15 derived, while the JSON summary claims 47 / 14. Against current source/test 353231c, 33 rows remain unchanged, 20 changed and 8 are absent. The historical intake is not a current-source mirror.

Exact mapped subtree comparisons:
- OpenWrt library rootfs/usr/lib/blazepwifi: 15 source / 20 destination; 6 exact, 9 divergent, 5 destination-only.
- Vendo CGI: 1 source / 1 destination, different blobs.
- Tests: 47 source / 19 destination; 1 exact, 3 divergent, 43 source-only, 15 destination-only. The three divergent same-path tests are config.sh, integration.sh and security.sh.
- ESP32: 16 source files / 1 destination sketch; sketch differs.
- ESP8266: 49 source files / 1 destination sketch; sketch differs.
- Board-local Python labs/helpers: 53 source / 0 destination.

Firmware sketch identities remain different: ESP8266 source 8a0b458b6c7fb99c0913df16c5b4ca94dbcdc50e vs destination c8be98f72596681e36a3ad1f8939bf8046c96887; ESP32 source adfd2f110d88243d03f2195658fb456b154dcb84 vs destination 3cc7ec54b476943dc04a8d1af5e2df5fe054e422.

MIGRATION_MAP.md blob b54fc15d83bc2269de03db8aadd0e76259fd13d9 still has stale hashes for run_focus.sh (map fa1f4f2c6393504499d50659d8bf980caf7ff85b vs destination 2b7b861ec63cf811d18d0e63b11a65efd1bec0e9) and member_txn_journal.sh (map 01dc9c65ae9d74eaafb403d47aebcd20edd14390 vs destination d04df3c6f3ada60b9fda8c8c04230dd31e37019a). Destination voucher_txn_journal.sh blob 4277a56af800b930135745bb942d62b6d580cb99 has no migration-map row.

License/notice readback: PisoWiFi product LICENSE, QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE have exact destination counterparts. Experiments root NOTICE.md and Tabler LICENSE have no COE counterpart. BlazeRentalLauncher LICENSE is part of the separate RENTAL route and is not reclassified as PisoWiFi. Matching license files do not establish complete legal or import provenance.

COE #26 remains FROZEN. No staging, copying, moving, overwriting, cherry-picking, rebasing, retargeting or destination write occurred.

## 6. Registry, branch protection and execution limits

The canonical private Drive registry v11 and newer corrections were not surfaced by authorized Library retrieval. A later private checkpoint is not the canonical registry and was not substituted. No Google Drive connector is exposed in this runtime. No private registry contents or identifiers were copied into this public coordination report.

Experiments main, Experiments development and COE main branch objects report protected=false; direct branch-protection endpoints return 403. Master branch protection is unverified. Repository administrators must confirm effective rulesets and required checks.

Master Python tests and verify_coordination.py were NOT RUN. A local git ls-remote attempt failed because github.com DNS resolution is unavailable in the container; the current branch has no dedicated Master validation workflow. Exact GitHub tree/blob/mode comparisons, manifest-row checks, owner PR/CI inspection and failed-job log inspection were executed. This is not a Master product-test pass.

## 7. Next owner actions

1. HARDWARE refreshes its own #349 records after the current Full failure; CORE supplies the authenticated poll producer contract; QA independently reconciles the assertion.
2. CORE updates the canonical CURRENT_STATE handover for RELEASE #291; RELEASE reruns exact-head Windows/build after that owner update.
3. RELEASE refreshes COE #35 PR description to source/test a514e57d and final PR/head ecc1d3d4; obtains approved site ULA authority and a disposable Bubblewrap-capable runner.
4. COE integration owner reconciles the 46/15 summary, test map, source drift, hardware helpers/sketches and license/notice closure. Keep #26 frozen.
5. Registry custodian restores authorized access to private v11 and newer corrections; administrators verify branch protection.
6. Master Python suite and verify_coordination.py run when an authenticated checkout or a dedicated validation runner is available.

## 8. Final disposition

Master owns coordination/phoenix/ only. No CORE, RENTAL, PISONET, HARDWARE, QA or RELEASE source files, shared handovers, workflow files, COE destination files, financial records or hardware were modified. PR #288 remains OPEN / DRAFT / UNMERGED. COE #26 remains FROZEN. **PRODUCTION NO-GO.**

Mandatory release evidence remains independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and explicit owner-authorized release gates.
