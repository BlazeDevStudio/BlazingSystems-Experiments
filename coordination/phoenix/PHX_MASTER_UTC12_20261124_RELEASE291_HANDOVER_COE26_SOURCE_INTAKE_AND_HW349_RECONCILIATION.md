# PHX-MASTER UTC12 — RELEASE #291, HARDWARE #349, shared handover and COE #26 reconciliation

**Updated:** 2026-11-24T12:37:40Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, migration provenance and integration matrix only  
**Status:** PR-ready coordination audit; production remains NO-GO

## 1. Exact live references

| Item | Exact state |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Experiments development branch | blazepwifi-v0.5.3-development @ aad3aade (exact branch ref read) |
| Master branch at start | phoenix/master-coordination @ e72c47d2be6fd77628fe3882f9dc8f532da1535a |
| Master PR #288 | OPEN / DRAFT / UNMERGED; base main @ f4e8a891; 196 changed paths, all under coordination/phoenix/ |
| Control plane #172 | OPEN; 789 comments at read |
| Cleanup #266 | OPEN; 0/7 tracks checked |
| Ownership routing manifest | coordination/phoenix/OWNERSHIP_ROUTES.json @ e4db324315a1b3543fec17a148fbf960170fcb29; 11 routes; DRAFT_REVIEW_ONLY; PHX-MASTER target null |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | OPEN / DRAFT / FROZEN; head b382d233ff06c8791b1028bed3c617cc7b670d12; five workflows QUEUED, zero jobs and zero commit statuses |

The private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer Drive corrections were not available through the connected tools. A complete accessible Library listing contained no v11 registry entry, and no Google Drive connector was exposed. The available private checkpoint is not a substitute for the canonical registry. No private registry contents were copied into this public repository or checkpoint.

Root AGENTS.md, README_FIRST, 00_MASTER_PROJECT_PHOENIX(1).txt and COMMUNICATION_PROTOCOL were read. AGENTS.md-linked Cloud Artifact Policy / Storage Handover references could not be resolved through the current GitHub connector; no policy exception was assumed.

## 2. RELEASE #291 — exact final-head CI and ownership overlap

**PR head:** 8fe31d906e982c147366f5cff9e4a767a96677e9  
**Source/test head:** 0779a633e351f2ab3e8abdc651f530f63de772d6  
**Accumulated PR diff:** 29 paths — 24 RELEASE-owned paths, three shared handover paths, and two PISONET-owned PublisherMockCli/negative-selftest paths. The latest UTC12 owner checkpoint's four newly touched paths do not describe the entire accumulated PR diff.

| Final-head workflow | Result | Finding |
|---|---|---|
| Windows #45392342756 | FAIL | Handover job fails; build-windows and publish-release skipped |
| BlazePwifi build #45392342882 | FAIL | validate fails at the shared handover gate; target/platform jobs complete successfully, downstream simulation/update/signing/publication skipped |
| ESP32 compatibility #45392342904 | PASS | Provenance regression and both ESP32 core legs pass |

The exact Windows log identifies the last shared PROJECT_HANDOVER checkpoint as c058e30e2611d433e260e9eaa682c1390a5d194f and names two newer workflow paths: .github/workflows/blazepwifi-v053-release.yml and .github/workflows/blazerental-v053-lineage2-sign.yml. The RELEASE owner checkpoint also reports the separate CURRENT_STATE checkpoint d85eb6a2766781b6cac1807cef461993d8216b84 as stale. The latest Windows log specifically fails PROJECT_HANDOVER freshness; it does not prove that the separate CURRENT_STATE condition has been independently repaired.

The ESP32 compatibility workflow pins Hardware source commit 6ce423783b306411bdb7e7217081c050cb4cbec4 and ESP32 sketch blob a9a1c2fecb001d71f8f22b43952edbd160aacaf8. The current HARDWARE #349 source/test head bb064e1cd0548a476ab2b685f0f8c2b625df0cf5 contains the same ESP32 sketch blob. Thus the pinned ESP32 sketch identity remains exact even though the pinned repository commit is older than the current Hardware lab/test head. This compatibility pass does not validate the newer Hardware lab tests.

**Owner routing:** PHX-CORE owns the canonical shared handover set; PHX-RELEASE owns release workflow and publisher changes; PHX-PISONET owns the two SoftTimer publisher test files; PHX-QA independently reviews release admission and evidence. CORE must refresh the required handover records after the workflow changes; RELEASE then reruns Windows/full build at the resulting exact PR head. Do not bypass the freshness gate.

## 3. HARDWARE #349 — current exact docs-head result

**Source/test head:** bb064e1cd0548a476ab2b685f0f8c2b625df0cf5  
**Final docs/PR head:** b4f03e75cd0c5b5ebade5b82c1eb10e0a25ec9f0

- Quarantine #45393480743 — PASS.
- Relay #45393480540 — PASS.
- Full #45393480768 — FAIL in validation job 138443001004 at inherited “Missing poll signature check”.
- All 14 target/platform jobs, including Android, pass; dependent simulation, update, signing and publication stages are skipped.
- Physical relay/electrical testing was NOT performed. No production hardware acceptance is implied.

CORE must publish the approved authenticated register/poll response contract; QA must reconcile the assertion independently; HARDWARE retains deny-only behavior until that contract is approved. The UTC12 Hardware cleanup contribution does not close any #266 track: issue #266 remains 0/7.

## 4. COE #26 — exact pinned-source and destination staging audit

**Destination candidate:** CoinOperatedEcosystem PR #26 @ b382d233ff06c8791b1028bed3c617cc7b670d12  
**SOURCE_INTAKE.json blob:** 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f  
**MIGRATION_MAP.md blob:** b54fc15d83bc2269de03db8aadd0e76259fd13d9  
**Declared source snapshot:** Experiments commit 6d4c9b487af4d768c4d7627654d119417fcc6e00

### Rootfs identity and manifest consistency

| Measure | Exact result |
|---|---:|
| Pinned source rootfs files | 61 |
| Destination rootfs files | 62 |
| Exact source/destination blob + mode matches | 46 |
| Derived same-path source files | 15 |
| Source-only files | 0 |
| Destination-only files | 1 |

All 61 SOURCE_INTAKE runtime rows match the actual pinned source and destination blob identities and modes. The extra destination-only path is Pisowifi/openwrt/rootfs/usr/sbin/blaze-appliance-diag; it is not represented by a source intake row.

The SOURCE_INTAKE summary says 47 byte-identical and 14 locally derived. Its own 61 runtime rows and the MIGRATION_MAP table instead resolve to 46 unchanged plus 15 derived (13 intentionally edited and two locally derived). The one-row summary discrepancy must be corrected by the COE integration owner before the manifest can be treated as internally consistent. This is a metadata/provenance defect, not evidence that any of the 61 mapped rows is missing or has an incorrect recorded blob.

### Pinned source is not current source

At current HARDWARE #349 source/test head bb064e1cd0548a476ab2b685f0f8c2b625df0cf5, the current rootfs contains 53 files. Compared with the declared 6d4c9b snapshot: 33 same blobs/modes, 20 changed, eight pinned-only, zero current-only. The candidate is therefore a deliberately pinned historical snapshot, not a live mirror of current Experiments source. Do not silently refresh or rebase it; any source-pin change needs owner review and a new complete provenance comparison.

### Test identity and import completeness

| Comparison | Source | Destination | Exact | Different | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| Declared original test tree (top-level files) | 143 | 19 | 2 | 2 | 139 | 15 |
| Current #349 source tests | 47 | 19 | 1 | 3 | 43 | 15 |

The declared original test tree's two unchanged tests match SOURCE_INTAKE unchanged_original_test_count=2. This does not establish complete test import. The three current same-name divergent tests are config.sh, integration.sh and security.sh; portal.sh is the one exact current match. Destination-only tests and source-only tests require explicit owner mapping and test-identity disposition.

### Firmware and lab helpers

- Current source board tree: 54 files across ESP32 and ESP8266, including 44 Python lab helpers; destination board tree contains only two firmware sketches and no Python lab helpers.
- ESP32 sketch source blob a9a1c2fecb001d71f8f22b43952edbd160aacaf8 differs from destination blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422.
- ESP8266 sketch source blob 2f87a9de84ac53dbb0d2718b5c79a4662b63de8f differs from destination blob c8be98f72596681e36a3ad1f8939bf8046c96887.

### Licence and notice provenance

Present/matching: product LICENSE, QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE. Missing destination counterparts: source root NOTICE.md, UI vendor Tabler LICENSE and BlazeRentalLauncher LICENSE. These remain unresolved licence/provenance obligations.

**Disposition:** COE #26 remains FROZEN. No destination file was staged, copied, moved, overwritten, rebased, cherry-picked or promoted. No migration is approved.

## 5. Cross-role shared handover identity matrix

The following paths have different exact blob identities across role PR heads; they must not be treated as interchangeable snapshots.

| Role PR | PROJECT_HANDOVER.md | CHANGE_LEDGER.md | CURRENT_STATE.md |
|---|---|---|---|
| CORE #252 @ c82705f2 | 72e8e487 | df50981c | 72c38aeb |
| PISONET #255 @ d01fd164 | d3e66608 | 02963d32 | 47e07b7c |
| QA #290 @ 5c29d159 | 83db03cf | 3180e1a9 | 73b9d1d6 |
| RELEASE #291 @ 8fe31d90 | 3658da63 | 7f2ad6dd | 85dd3c1e |
| HARDWARE #349 @ b4f03e75 | 4aaa9817 | absent | absent |

These are branch-local blobs, not an instruction to select one branch as canonical. CORE must reconcile the canonical shared handover; each role retains its own source/test ownership. The release workflow freshness gate must be satisfied by the exact canonical file set at the final PR head.

## 6. Other owner PRs and exact-head CI

| Owner / PR | Exact head | Current evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build #42698139210 PASS (scoped) |
| RENTAL #328 | 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | APK #44782114384 PASS; API #44782114393 PASS; build #44782114390 FAIL at handover validation and ESP32 compile missing mbedtls/sha256.h |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows synthetic #42462978704 PASS |
| HARDWARE #347 | 960184670379f01e20f0e7e8bc23b3e5eedacd3f | Quarantine #45299741995 FAIL; Relay #45299742437 FAIL; build #45299741993 FAIL |
| HARDWARE #348 | eb7afcb2ba0d1e84054c052c8b129cb51a91d062 | Header #45352513178 PASS; build #45352513177 FAIL at missing mbedtls/sha256.h |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Windows #43633486963 PASS |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered workflow runs |
| COE #35 | e7801818b00854f34a5a88955d979c601ec96404 | Case guard PASS; shared contracts and sandbox FAIL |
| COE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Overlay/shell and case-collision PASS |
| COE #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | Stage 5.1 and case-collision PASS; shared contracts FAIL |

All results are tied to the exact heads listed. Scoped/synthetic passes are not production acceptance.

## 7. Execution record and limitations

**Executed:** live issue/PR/branch reads; exact owner PR metadata and changed-path inspection; exact-head GitHub Actions runs/jobs/logs; complete non-truncated recursive source/destination trees; blob/mode comparisons for pinned source intake, rootfs, tests, firmware and licenses; shared handover blob comparison across role PRs; static manifest row/count assertions.

**Not executed:** Master Python unittest suite and verify_coordination.py. An ordinary git ls-remote attempt failed because the runner could not resolve github.com; no authenticated local checkout was available. No new Master CI was dispatched. No hardware, physical, payment, signing or migration tests were performed.

No subsystem source, COE destination, ownership manifest, private registry, secret, signer, financial state, hardware or release artifact was changed.

## 8. Next owner actions

1. PHX-CORE refresh the canonical PROJECT_HANDOVER / CURRENT_STATE / CHANGE_LEDGER set after the release workflow changes and reconcile shared blobs without overwriting other role work.
2. PHX-RELEASE rerun #291 Windows and full build at the resulting exact docs/PR head; preserve the existing ESP32 sketch blob provenance.
3. PHX-CORE + PHX-HARDWARE + PHX-QA coordinate with the COE integration owner to correct SOURCE_INTAKE summary counters, explicitly disposition blaze-appliance-diag, map all source/destination test identities, and resolve missing licence notices before any migration proposal.
4. PHX-CORE and PHX-QA resolve the authenticated poll-response contract and inherited signature assertion; HARDWARE reruns Full only against the approved contract SHA.
5. Registry custodian restores authorized access to the canonical private Drive v11 registry and newer corrections; do not substitute older snapshots.
6. An authorized runner executes the Master Python suite and coordination verifier after obtaining a working checkout.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device 24-hour soak and owner-authorized release gates remain unverified.

## UTC12 post-checkpoint exact owner-head refresh — 2026-11-24T13:00:15Z

This addendum supersedes the earlier read-time owner heads in Sections 2, 3 and 5; the COE #26 provenance comparison and its frozen disposition did not change.

### RELEASE #291 advanced after the Master checkpoint

- New final PR/docs head: b154e845b27006afe16433743548fb3d0016f8e2; three commits ahead / zero behind the previously inspected 8fe31d90 head.
- Latest commit message: docs(phx-release): audit action-pin workflow coverage. Its latest commit changes only CHANGE_LEDGER.md; the three-commit delta also changes .github/PHX_RELEASE_HANDOVER.md and PROJECT_HANDOVER.md.
- Current shared blobs: PROJECT_HANDOVER f1c5404b; CHANGE_LEDGER df9a2804; CURRENT_STATE remains 85dd3c1e, last checkpoint d85eb6a2766781b6cac1807cef461993d8216b84.
- Windows [#45397890521](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45397890521) completed FAILURE at handover job 138458435778. The exact log says CURRENT_STATE checkpoint d85eb6a2 is older than three workflow paths: SoftTimer release, BlazePwifi v0.5.3 release and Rental Lineage2 signing. build-windows and publish-release are skipped.
- BlazePwifi build [#45397890507](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45397890507) completed FAILURE at validate job 138458573494 for the same CURRENT_STATE gate; target jobs mostly succeeded, optional jobs were still being reconciled at the read, and update/simulation/signing/publication gates skipped.
- ESP32 compatibility [#45397890553](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45397890553) PASS, 3/3 jobs. The compatibility pin still uses source commit 6ce42378; its ESP32 sketch blob is identical to the current #349 source sketch, but it does not test the newer Hardware lab fixture changes.

**Action:** CORE must advance the canonical CURRENT_STATE after the workflow changes; RELEASE reruns Windows and full build at the resulting exact head. Do not bypass the gate.

### HARDWARE #349 advanced after the Master checkpoint

- New final PR head: dce158b3eb6c0d953900284207f349518205f1d2; two commits ahead / zero behind the previously inspected b4f03e75 docs head.
- The delta adds/updates only the source-extracted poll-loop lab and its response fixture; no production .ino, financial contract or handover file changed.
- Relay [#45398283830](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45398283830) PASS; Quarantine [#45398283765](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45398283765) PASS.
- Build [#45398283752](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45398283752) remained IN PROGRESS at read time. Validation job 138459962150 had already FAILED at “Missing poll signature check” in the ESP8266 production sketch; several target jobs were still running. Do not label the build run complete or infer Full acceptance from focused passes.
- Current #349 PROJECT_HANDOVER blob remains 4aaa9817; CHANGE_LEDGER and CURRENT_STATE are absent on this branch.

**Action:** CORE/QA must reconcile the approved authenticated poll-response contract and assertion; HARDWARE keeps deny-only behavior. Physical hardware remains NOT TESTED.

### Same-activation deduplication

The existing UTC12 Master issue #172 comment and PR #288 comment are updated in place with this owner-head refresh. No second UTC12 Master checkpoint is created. COE #26 remains at b382d233 and its pinned-source audit is unchanged.
