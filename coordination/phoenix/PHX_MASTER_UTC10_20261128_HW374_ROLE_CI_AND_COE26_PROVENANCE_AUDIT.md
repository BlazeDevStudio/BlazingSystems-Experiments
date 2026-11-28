# PHX-MASTER UTC10 — exact-head role CI, routing and COE #26 provenance

**Observed:** 2026-11-28T10:40:48Z  
**Task:** `PHX-MASTER-20261128T10Z-HW374-COE26-ROLE-CI-ROUTES`  
**Role:** PHX-MASTER · **Branch:** `phoenix/master-coordination`  
**Audit-start HEAD:** `c7798bf63d7f545b98bbbb7c8db68d57f0f36559` · **PR base:** `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**Scope:** `coordination/phoenix/` only

## Live repository and PR state

- Experiments default `main@6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`; development `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`; comparison-only v0.6 audit foundation `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- PHX-MASTER PR #288 remains OPEN / DRAFT / UNMERGED at audit start `c7798bf63d7f545b98bbbb7c8db68d57f0f36559`, based on `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; compare is 707 ahead / 1 behind, merge base `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`, 271 changed paths, all under `coordination/phoenix/`. No PR-triggered workflow runs were returned for the exact Master head.
- COE default `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`; draft integration PR #26 remains OPEN / DRAFT / UNMERGED at `b382d233ff06c8791b1028bed3c617cc7b670d12`, base `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`, 205 changed files / 85 commits. Five exact-candidate workflows are terminal CANCELLED; no destination CI success is claimed.
- Cleanup issue #266 remains OPEN / 0-of-7; P0 issue #177 remains OPEN. No source-owner transfer, staging or destination write was performed.

## Current role PRs and exact-head CI

| Role / PR | Current exact head | Exact-head evidence / state |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | BlazePwifi build #42698139210 SUCCESS. CORE implementation was not touched. |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | BlazePwifi build #43653329229 SUCCESS; isolated native status-auth #43653329235 SUCCESS. |
| RENTAL #328 | `10fc200b6dbf470a95e679d3acc58aff4ab2a67f` | API21/23 smoke #45622918364, native auth #45622918551 and APK identity #45622918340 SUCCESS; BlazePwifi build #45622918468 FAILURE. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows synthetic #42462978704 SUCCESS; native COM acceptance NOT TESTED. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | Windows synthetic #43633486963 SUCCESS; not native acceptance. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No exact-head workflow run. |
| RELEASE #291 | `bf339a76964a1abe2412fac45392fe06a8e66418` | No exact-head workflow run. |
| HARDWARE #373 | `3783654a3c9862598bbb714268c536fb8b34578b` | Poll Intake Deny #46118310162 SUCCESS; Mbed #46118310195 SUCCESS 3/3; Full #46118310135 FAILURE at QA-owned controller parity after 14/14 target builds passed. |
| HARDWARE #374 | `09374c8b232f925424d15bce830b1c375e11e024` | Poll Intake Deny #46132251089 SUCCESS; Mbed #46132251056 SUCCESS 3/3; Native #46132251066 FAILURE at PAY-0745 assertion “corrupt persisted state must halt startup”; Full #46132251064 FAILURE at QA-owned Controller protocol parity. All 14/14 target/platform jobs and Android passed; downstream simulation/update/sign/publication jobs were skipped. |

The #374 result above is for its current PR head `09374c8b232f925424d15bce830b1c375e11e024`, not the earlier `44334e37` or `bdd69c75` snapshots. The Native failure is a test assertion, not proof that production payment state was corrupted. The Full result is not a hardware acceptance result.

## Ownership and migration provenance

- Current `OWNERSHIP_ROUTES.json` blob: `e4db324315a1b3543fec17a148fbf960170fcb29`; schema v1, 11 routes, status `DRAFT_REVIEW_ONLY`. PHX-MASTER target remains null. The broad Rental route is manual-file-mapping-only with `copy_permitted=false`; the two intentional Rental target-prefix overlaps remain blocked.
- Five in-memory static route checks passed (schema, route count, Master target null, broad Rental manual-only, and expected Rental prefix overlap count). This is a bounded manifest check, **not** the repository test suite.
- Last complete source/destination audit recorded in the UTC09 Master matrix remains the migration baseline: 61/61 pinned runtime rows match source/destination blob+mode; actual classification is 46 identical / 15 derived while SOURCE_INTAKE says 47/14; source test tree has 149 blobs vs 19 candidate blobs; 15 derived test files exist but MIGRATION_MAP has 14 rows, omits `voucher_txn_journal.sh`, and has two stale hashes; 7 of 11 project-scoped LICENSE/NOTICE path counterparts are missing. Candidate branch pin in the map still disagrees with live PR #26 branch. These are unresolved provenance/completeness defects, so #26 remains FROZEN.
- The private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not accessible. The available Library search surfaced only older v3–v7 snapshots; none was substituted. No private Drive IDs or contents were copied to GitHub.

## Test execution and limits

- EXECUTED: live issue/PR/ref reads; exact-head workflow-run reads for the listed role heads; #374 failed-job log inspection; current routing-manifest read and 5/5 bounded static assertions.
- NOT RUN: Master Python suite, `verify_coordination.py`, local shell/native suites, and Master Actions. No authenticated non-Codex local checkout is available in this runtime; worker CI is not a Master test.
- No Codex, subsystem source edit, COE destination staging, merge, release, signer operation, secret provisioning, hardware flash, physical test, payment operation or customer cutover occurred.

## Blockers and next owner actions

1. PHX-HARDWARE owns the #374 implementation/handover and exact-head refresh; keep coin/relay admission denied.
2. PHX-QA owns the PAY-0745 corrupt-persisted-state assertion and controller protocol parity tests; replace stale literal assumptions with source-linked semantic deny-only vectors, then rerun exact-head Native and Full.
3. COE integration owner must reconcile the 46/15 vs 47/14 count, add the missing voucher test-map row, correct stale hashes, restore missing project LICENSE/NOTICE counterparts and pin the actual #26 source branch before any staging proposal.
4. Registry custodian must provide the canonical private v11 registry and newer corrections through an approved Drive connection; repository admin must provide an authenticated non-Codex checkout for the Master suite.
5. Keep CORE read-only to its separately assigned owner; PHX-MASTER does not implement CORE or modify its source branch.

**Disposition: BLOCKED / PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.
