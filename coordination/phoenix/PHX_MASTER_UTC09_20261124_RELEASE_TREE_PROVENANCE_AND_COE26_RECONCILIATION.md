# PHX-MASTER UTC09 — release tree provenance, owner collisions, and COE #26

**Timestamp:** 2026-11-24T09:37:39Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Scope:** coordination/phoenix/, architecture/interface contracts, cross-repository provenance and integration matrices only. Strict NO CODEX.

## Starting live state

| Ref | Exact SHA / state |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Experiments development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| PHX-MASTER branch / PR #288 head | 4a21f3b6114c6242c77d2738dd6805af697ac0aa |
| PR #288 base | main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 |

PR #288 is OPEN / DRAFT / UNMERGED, 193 changed paths, all under coordination/phoenix/. Current Master head 4a21f3b is newer than the UTC07 head recorded in the #172 issue body. The current branch API reports protected=false; ruleset enforcement was not verified. Cleanup #266 remains OPEN / 0-of-7. OWNERSHIP_ROUTES.json is blob e4db324315a1b3543fec17a148fbf960170fcb29: 11 routes, DRAFT_REVIEW_ONLY, PHX-MASTER target null.

## Current role PRs and exact-head CI

| Role | PR / exact head | Evidence |
|---|---|---|
| CORE | #252 / c82705f2de865c89ab733b10efa84f26f56a5cc4 | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; scoped software only |
| RENTAL | #328 / 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | [APK #44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) PASS; [API #44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS; [build #44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAIL |
| PISONET | #255 / d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; synthetic Windows |
| HARDWARE | #347 / 960184670379f01e20f0e7e8bc23b3e5eedacd3f | [Quarantine #45299741995](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45299741995), [Relay #45299742437](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45299742437), [build #45299741993](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45299741993): all FAIL |
| HARDWARE | #348 / eb7afcb2ba0d1e84054c052c8b129cb51a91d062 | [focused #45352513178](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45352513178) PASS; [build #45352513177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45352513177) FAIL, ESP32 mbedtls/sha256.h unavailable |
| HARDWARE | #349 / dbb7d5393ae40347b9d1148775c2ece9142d67ff | [Quarantine #45360524109](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45360524109) PASS; [Relay #45360524001](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45360524001) PASS; [build #45360524080](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45360524080) FAIL at Controller protocol parity / Missing poll signature check |
| QA | #290 / 5c29d15994cee1279058f1eca12f2a3180704292 | [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS |
| QA | #292 / 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered runs; NOT VERIFIED |
| RELEASE | #291 / 9d45ee19b2d8e3ef6623b3b0f0db3da56b1616e8 | [Windows #45366410925](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45366410925) FAIL at PISONET negative-selftest.ps1:326; [build #45366411182](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45366411182) 26 jobs PASS / 4 SKIPPED; [ESP32 #45366411198](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45366411198) PASS |

HARDWARE #349's PR description still cites older e4ab80dc / 8dd8b12c refs, while its actual PR head is dbb7d539. Its UTC08 handover says exact-head CI is pending, but current runs are terminal. The current register/poll CGI payload omits response_sig; Hardware remains deny-only until CORE publishes an approved versioned envelope and QA reconciles the inherited assertion. PHX-HARDWARE should refresh its own handover and PR description.

## RELEASE #291 source-tree provenance review

The RELEASE source/test commit is cfd34e2b178455313210962f48ae4560d83be096; the final docs/PR head is 9d45ee19b2d8e3ef6623b3b0f0db3da56b1616e8. The exact source commit tree 0be529f79674137dbdec4437abd622946595e983 contains:
- OpenWrt rootfs tree f4a923aaacf1374e90c7bab5f335efe6c6ec55cf.
- Linux-agent tree da87d556b16bd7650c440083c9f0f929d57d1274.

Both Git tree objects were read back from GitHub. The source writer records these tree identities and target-specific helper blobs; it rejects tracked drift, untracked inputs and non-tree objects. Static comparison of the writer target set, build script case labels and workflow matrices passed: all 11 names match. The existing Python suite covers representative ruijie, x86_64 and orangepi_zero3 classes, not every target; a table-driven all-target mapping test is a reasonable RELEASE-owned follow-up.

At final #291 head, the provenance suite passed 50 tests, Arduino CLI archive verifier passed 10 tests, and immutable action-pin checks passed for 52 + 4 + 6 invocations. The build workflow had 26 successful jobs and four skipped jobs; ESP32 compatibility passed. Windows still fails the PISONET-owned negative self-test and publisher is skipped. Git tree identities are not artifact readback, detached signatures, complete licensing provenance, or hardware acceptance.

## Cross-owner path and blob conflicts

The current #291 accumulated diff has 27 paths and includes CORE-owned PROJECT_HANDOVER.md, CHANGE_LEDGER.md and CURRENT_STATE.md, plus PISONET-owned negative-selftest.ps1 and PublisherMockCli.ps1. The two PISONET test paths exist in #291 at blobs 8b69174bf519154e43f7e12e4a9fa2c0e75d350f and 7d56522b4fd678a26a2d7ea39e9b51dc8e52612d, but both return 404 at PISONET #255 exact head.

| Shared path | CORE #252 | PISONET #255 | QA #290 | RELEASE #291 |
|---|---|---|---|---|
| PROJECT_HANDOVER.md | 72e8e487d333a9488f77c2c3e68652d1a650ff85 | d3e66608280644af8c42635168a7e27c8fba8f31 | 83db03cf387f280ba2d595ff6e9d58ffa23417c5 | 0c951973eefd2321acf214cc1f58b87f4fcfcc07 |
| CHANGE_LEDGER.md | df50981c1596838b1abf544e94f68e89ad556b7d | 02963d32018ea09ad2a6a5a95b487de1f65ff4f2 | 3180e1a93c852e5c983f947e8ca45a897df0479f | ec7c0bdc560006d1b5ff63940a8da6d736aa5d1a |
| CURRENT_STATE.md | 72c38aeb93377f3aedb758c91d670ff1150e87bd | 47e07b7c0e06766d0d4ebb18bc13bfb274adfe22 | 73b9d1d6acbd8b58c13f2d1b9d17512c392f444a | 85dd3c1e9254d947c4e75daaeaf3351ef3e105e3 |

The latest #291 commit changes only .github/PHX_RELEASE_HANDOVER.md, but its accumulated diff still has these overlaps. Require CORE and PISONET review; do not overwrite or silently transfer ownership.

## COE #26 exact-tree migration audit

Non-truncated recursive trees: source #349 = 2,503 entries; COE #26 = 286; COE main = 3. Source board directories contain ESP8266 41 entries and ESP32 17; destination Hardware directories contain two each. There are 44 board-local Python labs at source and zero at destination.

Source QA tests: 47; destination: 19. Four same-relative-path pairs exist: one exact blob+mode match, three divergent. Forty-three source tests lack same-relative-path counterparts; 15 destination tests are destination-only. Both firmware sketches differ:
- ESP8266 source 2f87a9de84ac53dbb0d2718b5c79a4662b63de8f vs destination c8be98f72596681e36a3ad1f8939bf8046c96887.
- ESP32 source a9a1c2fecb001d71f8f22b43952edbd160aacaf8 vs destination 3cc7ec54b476943dc04a8d1af5e2df5fe054e422.

Product LICENSE, QRCode LICENSE, and TailAdmin LICENSE/NOTICE match exactly. Root NOTICE.md, Tabler ui/vendor/tabler/LICENSE, and BlazeRentalLauncher LICENSE are missing at mapped destination paths. No complete license/import proof exists.

COE #26 has five queued workflow runs—43096752609, 43096752632, 43096752800, 43096752563 and 43096752557—with zero jobs each and zero commit statuses. COE #35 has case PASS, shared-contract FAIL and ImageBuilder sandbox FAIL; #45 overlay and case PASS; #49 case and Stage 5.1 bridge PASS but shared contracts FAIL. No destination staging, copy, move, overwrite, rebase, cherry-pick or promotion occurred. The complete historical 61-row intake audit was not rerun.

## Governance, access, and test limitations

README_FIRST selects the full seven-role team; BLAZE-COMMS/1 makes GitHub issue #172 the shared mailbox. Repository AGENTS.md blob d8777e3b58efc41caa5aa3c969c932aee9103d5f and its linked Cloud Artifact Policy blob 5e503925750c4e511314e4b7624579d82f60aae2 and Storage Handover blob a15f14cb3baf46424b820e1a921462794422f06b were read. They require the private registry/ledger before Drive artifact work and exact remote readback before calling an artifact verified.

The canonical private Drive registry v11 and newer corrections were not accessible through the available connector surface; Library search/list did not surface the requested v11 file. Older Library snapshots were not substituted. No private registry contents or identifiers are disclosed. Master Python unittest suite and verify_coordination.py were NOT RUN: an ordinary shallow sparse git clone failed because the runner could not resolve github.com. Master PR #288 has zero workflow runs/statuses at its current head. JavaScript static checks and GitHub source/tree inspections did execute; they are not a replacement for the Python suite.

No subsystem source, COE destination, ownership manifest, signer, secret, financial state, hardware, release artifact or production configuration changed. No merge, release, flash, physical test, payment operation or customer cutover occurred.

## Next owner actions

1. PHX-PISONET and PHX-RELEASE isolate both release/tag API lookups in the negative self-test; preserve production fail-closed semantics; rerun Windows CI.
2. PHX-HARDWARE refresh #349's stale handover/PR pins; PHX-CORE publish the approved versioned register/poll response envelope and golden vectors; PHX-QA reconcile the inherited parity assertion without inventing a signature.
3. CORE and PISONET review the cross-owner paths in #291; preserve role-specific handover history.
4. COE integration owner supplies per-file source/destination provenance, licenses, test identities and exact-head CI before any staging.
5. Registry custodian restores authorized private v11 access; authorized human runner executes Master Python tests after local GitHub access is restored.

**Disposition: OPEN / DRAFT / UNMERGED. COE #26 FROZEN. PRODUCTION NO-GO.**
