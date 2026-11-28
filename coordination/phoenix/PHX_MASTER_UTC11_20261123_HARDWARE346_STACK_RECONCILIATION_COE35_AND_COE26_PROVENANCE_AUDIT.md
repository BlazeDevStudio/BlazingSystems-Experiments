# PHX-MASTER UTC11 — Hardware #346 stack reconciliation, COE #35 exact-head CI, and COE #26 provenance

**Observed:** 2026-11-23T11:53:18Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Scope:** coordination/phoenix/ only  
**Execution:** Strict NO CODEX. Connected GitHub reads/writes and ordinary JavaScript source/tree validation only.

## 1. Exact repository and control-plane state

- Experiments default main: f4e8a891aed8af86d5fd315d28750a0ac3a7372b.
- Experiments development: blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5.
- PHX-MASTER starting branch: phoenix/master-coordination@8eb2475c9dbfa2f53d9f11786c3f3d7503cb7132.
- Phoenix Master PR #288: OPEN / DRAFT / UNMERGED; base main; 187 pre-update paths, all under coordination/phoenix/; zero PR-triggered Actions runs and zero combined statuses at the starting head.
- COE main: a6513ab4412b4c014eee2863e45cbe32d06cb243; integration #26: OPEN / DRAFT / FROZEN at b382d233ff06c8791b1028bed3c617cc7b670d12.
- Cleanup #266 remains OPEN; all seven cleanup-first role checkboxes remain unchecked.
- The current #172 history had the PHX-MASTER UTC10 checkpoint #7098585033 and newer Hardware/Release UTC11 role checkpoints, but no PHX-MASTER checkpoint for 2026-11-23 UTC11. One Master checkpoint is posted after this commit.

The live OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29: 11 routes, DRAFT_REVIEW_ONLY, source baseline main f4e8, destination candidate #26 b382, and PHX-MASTER target null.

## 2. HARDWARE #345 / #346 — exact stack review

### Parent #345

- Current PR head: ca72497ed386c9ac4e50d3f811827bef51e296ad.
- Base: dfeff7d5f63e699de7bc296c7641f2493f1e0e13.
- Exact-head Quarantine #45165015610: PASS.
- Exact-head Relay/Output #45165015665: PASS.
- Exact-head Full #45165015859: FAIL at the inherited QA-owned Controller protocol parity / Missing poll signature check. All 14 target/platform jobs pass; validation-dependent downstream stages are skipped.
- PR #345's body still pins 4c4653e5...; this is stale relative to live head ca72497. Hardware must refresh its own description/handover.

### Child #346

- Current head: bd3fd6e85717395f768aae26a310b647cdd72a7e.
- Base ref: phoenix/hw-coin-intake-armed-gate-20261122-utc23@797dece76c18d464a7c0580658b5db9351cb8e15.
- Parent #345 is now ca72497...; compare reports parent four commits ahead, zero behind.
- Parent-only changes since the child's base: added docs/handover/2026-11-23-hw-quarantine-append-failure-preservation.md; modified pending_clear_failure_lab.py; modified the same poll_loop_blocking_inhibit_lab.py that child #346 also changes.
- Exact lab blobs: base bf11921c5e4430bfdade37e50689d9325739fdcd; parent current 896e967102e6bd2cbb6861b7e0e412ed44be71c4; child current 34b371a27bf99abae925e769a65fb7a41dd571e3. Parent's new pending_clear_failure_lab.py blob is 1b754837fa3265137fb4473c9856d3f70e4c5586 and is absent from child #346's changed-file list.
- The ESP32 and ESP8266 sketches are unchanged between parent base 797dece and current parent ca72497 (blobs 21821cac40a054bfa4fad27c5f9795d533c57823 and 0c17d7f1474babc72fbbe1e1e416593731d6bee8 respectively). Child #346 changes them to blobs 717336b84d434d51eb24beac1ed8efce8e719f69 and fa8ed828026396db89aab2889bf6a61d6cf6bbac.
- Source/test commits: predicate refactor b18d5588f0335c06e84f2118851db46d859c2435; isolated mutation scenarios 61f2b5469522135c29b2e146f24b9b2458d0a2ba; final assertion head bd3.
- Source inspection confirms both sketches define coinIngressConfigurationAllows() as controllerEnabled && coinEnabled && relayEnabled, then reuse it in sampleCoinPulseEdge() and applyOutputs(). Poll-time suspension remains a separate runtime condition. The latest host fixture isolates one disabled edge per flag and checks no pending pulse/save, empty pending nonce/target, cleared active admission identity, sticky journal deny latch, and relay/LED OFF.
- No exact-head Quarantine/Relay run exists for bd3fd6e. Full build #45167004815 is at earlier source/test SHA 61f2b54 and fails the inherited poll-signature assertion before the Hardware host-lab commands; it is not final-head verification.

Master disposition: #346 is a stacked review candidate, not integration-ready. The child is four commits behind its parent and has an overlapping poll-lab change plus a missing parent failure lab. PHX-HARDWARE must reconcile the stack in its own branch, preserve the parent-only failure test, refresh its handover, and obtain Quarantine/Relay/Full results at the final exact head. QA owns the inherited poll-signature assertion; CORE owns the producer contract. Do not fabricate a positive response_sig or weaken default-deny. Master did not rebase, retarget, cherry-pick, or modify Hardware source.

## 3. COE RELEASE #35 — exact current-head CI

Current PR head: d97501a1a325dd304afd1f1c227ccd5d28d2ae9f.

- Case-collision #45164877481: PASS.
- Sandbox #45164877476: FAIL at mandatory Bubblewrap availability. Host preflight unit tests pass; namespace and packaging stages are skipped.
- Shared/firmware #45164877480: 198 tests PASS / 2 intentional skips, then all ten appliance profiles fail closed because an approved site-scoped RFC 4193 ULA /48 is not defined. ESP32/ESP8266 compile jobs are skipped.
- PR #35 description still starts with an old 2026-11-18 head 77cc0af7...; it does not describe current d97501a. RELEASE must refresh its own PR body/handover.

No Bubblewrap bypass or invented ULA prefix is permitted. This remains a blocker, not a green packaging result.

## 4. COE #26 — source/destination provenance revalidation

Exact complete trees:
- Experiments main f4e8: 2,340 entries, non-truncated.
- COE #26 b382: 286 entries, non-truncated.
- COE main remains a three-entry structure-only scaffold at a6513ab.
- Candidate #26 has five queued workflows / zero jobs.

### Current route-by-route comparison

The 11-route manifest remains review-only. Exact file/mode comparison at source main f4e8 and destination #26 b382:

| Route | Source | Destination | Identical | Different | Missing | Extra |
|---|---:|---:|---:|---:|---:|---:|
| CORE rootfs library | 15 | 20 | 6 | 9 | 0 | 5 |
| CORE Vendo CGI | 1 | 1 | 0 | 1 | 0 | 0 |
| Rental Android | 983 | 8 | 0 | 0 | 983 | 8 |
| Standalone Rental profiles (manual map only) | 31 | 19 | 0 | 2 | 29 | 17 |
| Rental server | 7 | 4 | 0 | 1 | 6 | 3 |
| Pisonet SoftTimer | 32 | 47 | 13 | 11 | 8 | 23 |
| Hardware ESP32 | 3 | 1 | 0 | 1 | 2 | 0 |
| Hardware ESP8266 | 3 | 1 | 0 | 1 | 2 | 0 |
| QA tests | 38 | 19 | 1 | 3 | 34 | 15 |
| RELEASE workflow | reimplementation review | reimplementation review | not byte-copy comparable | — | — | — |

The broad Rental route remains manual-file-mapping-only and is not a recursive copy plan.

### PisoWiFi SOURCE_INTAKE / MIGRATION_MAP

- Current Pisowifi/SOURCE_INTAKE.json blob: 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f, schema 8, historical source pin 6d4c9b487af4d768c4d7627654d119417fcc6e00.
- Runtime table: 61 rows = 46 byte-identical / 15 derived; summary still claims 47 / 14.
- Recomputed at exact pinned source, current source main and COE #26 trees: all 61 recorded source blobs match the historical pin; all 61 destination blobs match the recorded candidate; 33/61 pinned source blobs still match current main, 28 have drifted. All recorded file modes match.
- Intake declares 15 derived tests, but MIGRATION_MAP.md lists only 14: tests/voucher_txn_journal.sh is omitted; tests/run_focus.sh and tests/member_txn_journal.sh map SHAs are stale.
- Exact current destination blobs: voucher 4277a56af800b930135745bb942d62b6d580cb99; run_focus 2b7b861ec63cf811d18d0e63b11a65efd1bec0e9; member journal d04df3c6f3ada60b9fda8c8c04230dd31e37019a. The intake's derived-test rows match these current destination identities; the migration-map rows do not. Their intake statuses remain NOT_RUN / PENDING_CI_RUN, not current #26 CI passes.
- PisoWiFi LICENSE source/destination blob 1ee55b94183417be977ca287cd7391f9a6f7e721 matches exactly. Experiments root NOTICE blob f6d92cd21465312be5993631fe26977219be0fb9 exists; COE candidate root NOTICE.md returns 404.

Routing decision: #26 remains FROZEN. No destination staging, copy, move, overwrite, cherry-pick, rebase, retarget, or destination write occurred. The source intake's historical pin is not rewritten to conceal drift from current main.

## 5. Governance, tests and access limits

- Master branch tree at audit start: 2,529 entries, non-truncated; PR #288 had 187 changed paths, all under coordination/phoenix/.
- Master Actions at starting head: zero PR-triggered runs and zero combined statuses.
- Master Python suite and verify_coordination.py: NOT RUN; no authenticated local checkout was available. This activation did execute read-only JavaScript tree, route, manifest and blob-identity assertions against complete GitHub API trees.
- Branch API reports protected:false for Experiments main, development and Master, and COE main; classic protection details remain inaccessible to this connector (403) and administrator confirmation is required.
- Canonical private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not found in Library search; no Google Drive connector/action is exposed. Older v3–v7 registry snapshots and the 2026-11-09 checkpoint are not substitutes. No private registry data or IDs were published.
- CORE remains separately owned; no CORE source branch, owner PR, or CORE automation was invoked or modified.

## 6. Required next actions

1. PHX-HARDWARE: reconcile #346 against #345's four newer commits, retain pending_clear_failure_lab.py, resolve the shared poll-lab overlap, update the child base/handover and run exact-head Quarantine/Relay/Full.
2. PHX-QA + PHX-CORE: resolve the inherited poll-signature test/producer-contract boundary without inventing a positive signature or weakening default-deny.
3. COE integration owner: correct 46/15 vs 47/14, add the omitted voucher fixture, repair the two stale map blob IDs, and complete license/NOTICE and import review.
4. PHX-RELEASE / COE infrastructure: provide an approved site-scoped ULA /48 and a trusted Bubblewrap-capable disposable runner; rerun #35 at exact head.
5. Registry custodian: restore authorized read access to canonical private Drive v11 and newer corrections.
6. Human runner: execute full Master validation and verify_coordination.py at the final PR #288 head.

## 7. Release disposition

PRODUCTION NO-GO. Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device 24-hour soak and explicit owner-authorized release gates remain unverified.

No merge, release, signer/secret provisioning, firmware flash, physical test, live payment, customer cutover or financial migration occurred.
