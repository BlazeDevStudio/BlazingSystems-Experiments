# PHX-MASTER UTC18 — #380 canonical child decision and COE #26 exact-tree audit

**Date:** 2026-11-28 UTC18  
**Task:** `PHX-MASTER-20261128T18Z-HW380-COE26-EXACT-TREE-AUDIT`  
**Role:** PHX-MASTER — coordination, cross-role contracts, migration provenance and integration matrices only  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch / parent:** `phoenix/master-coordination@78a8f09a73d8d3e2945c7f97b559f8f9091a3897`  
**Scope:** coordination/phoenix only. No subsystem source branch, COE destination, hardware, payment system, secret, signer or release state was changed.

## 1. Live control-plane snapshot

| Ref | Exact observed value |
|---|---|
| Experiments default branch | `main@6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5` |
| Experiments development branch | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Active v0.6 source branch | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master branch before this update | `phoenix/master-coordination@78a8f09a73d8d3e2945c7f97b559f8f9091a3897` |
| Master PR #288 | OPEN / DRAFT / UNMERGED; 276 changed paths, all under `coordination/phoenix/` |
| PR #288 comparison | 720 ahead / 1 behind current main; merge base `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | OPEN / DRAFT / UNMERGED; candidate `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12` |
| Cleanup #266 | OPEN; 7 unchecked tracks, 0/7 complete |
| P0 #177 | OPEN; issue-body source pin is stale relative to active v0.6 branch |

The live `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, schema `phoenix/ownership-routes/v1`, 11 routes. PHX-MASTER remains `coordination/phoenix/`, target `null`, kind `coordination-only`. The manifest was not changed.

## 2. HARDWARE stack decision — #380 is the canonical combined successor

**Decision:** pin HARDWARE PR #380 as the single reconciled *candidate child* of current #377 for the combined #378 post-deny GPIO escape guard and #379 centralized writer-authority guard. This is an integration-order decision only; it is not a merge, hardware acceptance or production approval.

- #377 current base/head: `95ace1236c2b3e4816515c372edd4853ceeed064`.
- #378 remains OPEN/DRAFT at `3f67ba41dc3e087f868d3c57f6604e69f7a0e17b`, based on stale #377 snapshot `95e54790...`, mergeable=false.
- #379 remains OPEN/DRAFT at `5ac75dbb53bc36abc161fb276b6e7e80534e9b28`, stacked on #378.
- #380 is OPEN/DRAFT/UNMERGED at actual API head `a4ec03835fb8ad3483d0447d105436f0f38071e3`, based directly on current #377 head `95ace123...`, mergeable=true.
- #378 and #379 remain untouched and open for history/provenance. Do not integrate them separately after #380 is the canonical successor. #376 remains a separate storage-preflight line.

### Exact source-blob review

| File | #377 | #378 | #379 | #380 |
|---|---|---|---|---|
| `poll_preflight_inhibit_lab_contract.py` | `837b4df5` | `837b4df5` | `bb14c16e` | `bb14c16e` |
| `poll_preflight_inhibit_lab_cases.py` | `ef91b15f` | `02f965ff` | `9b4afb22` | `9b4afb22` |

The #380 contract contains `gpio_write_authority_locations()`: exactly one executable `digitalWrite()` is required inside `writeLogical()`; six startup writes are logical OFF; four output writes are limited to the existing accepting-gated LED/relay call set. Its case module retains the direct post-deny GPIO-ON mutation and the eight writer-authority mutation cases. Thus #380's exact source blobs carry both #378 and #379 test scope while being based on the live #377 head.

### Handover preservation

- `PROJECT_HANDOVER.md`: exact current #377 content is a prefix of #380 content.
- `docs/handover/CURRENT_STATE.md`: exact current #377 content is a prefix of #380 content.
- `docs/handover/CHANGE_LEDGER.md`: the PR patch appends three UTC17 reconciliation records at EOF; no prior ledger lines are deleted or rewritten in the patch.
- One new HARDWARE handover report is added.

No HARDWARE-owned file was modified by PHX-MASTER.

### Exact-head CI at current #380 head

- Poll Intake Deny [#46173865754](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173865754): PASS; exact-source job passed.
- ESP32 Mbed TLS [#46173865768](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173865768): 3/3 PASS (source contract, ESP32 core 3.3.13 and 4.0.0 clean builds).
- Full [#46173865781](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173865781): FAIL at QA-owned Controller protocol parity. All 14 target/platform jobs passed; downstream update bundle, simulations, signing and publication were skipped.
- Native Synthetic Journal: NOT RUN because the path filter excludes the two host-lab Python files and handover paths. The available GitHub connector exposes no workflow-dispatch action.

The Full failure is not a source-build failure: the validation step reaches Controller protocol parity and fails on the missing `config_revision` contract. The issue #177 HARDWARE checkpoint records the same failure. No decoy field or invented `response_sig` is permitted. CORE owns the authenticated controller envelope; QA owns the semantic parity assertion; HARDWARE owns its consumer and handovers.

The #380 PR body still cites the earlier exact-tested docs head `8b9a9d12...`; the live PR API head is now `a4ec0383...`. HARDWARE must refresh the PR description/handover with the current head and current three exact-head workflow results. Keep #380 DRAFT.

## 3. Active v0.6 P0 poll-order recheck

Source files were read at active branch `2fbd2475e9f54878c316fa7cea2f228386b0e859`.

| Board | Timeout | Synchronous poll | First coin sample |
|---|---:|---:|---:|
| ESP8266 | line 263 | line 354 | line 357 |
| ESP32 | line 230 | line 314 | line 318 |

Both boards still block before the first coin input sample. This is source inspection, not physical pulse testing. P0 #177 remains OPEN; its embedded source pin `9df0a7e7...` is stale. #380 does not fix active-v0.6 pulse loss.

## 4. Other role PRs and exact-head CI

| Owner | PR / exact head | Current evidence |
|---|---|---|
| CORE | #252 `c82705f2...` | BlazePwifi build PASS; CORE remained read-only to Master |
| RENTAL | #289 `68928774...` | Build and native status-auth instrumentation PASS |
| RENTAL | #328 `10fc200b...` | Build FAIL (handover freshness and ESP32 compile); emulator smoke, native auth/recovery instrumentation and APK identity PASS |
| PISONET | #255 `d01fd164...` | Windows Release workflow PASS |
| QA | #290 `5c29d159...` | Windows Release workflow PASS |
| QA | #292 `75a3f66d...` | No exact-head workflow |
| RELEASE | #291 `bf339a76...` | No exact-head workflow; mergeable=false |
| HARDWARE | #376 `0f5968b2...` | Poll PASS; Mbed 3/3 PASS; Full PASS; no physical acceptance |
| HARDWARE | #377 `95ace123...` | Poll PASS; Mbed 3/3 PASS; Native PAY-0745 FAIL; Full Controller parity FAIL |
| HARDWARE | #378 `3f67ba41...` | Poll PASS; Mbed 3/3 PASS; Full CANCELLED; Native NOT RUN |
| HARDWARE | #379 `5ac75dbb...` | Poll PASS; Mbed 3/3 PASS; Full Controller parity FAIL |
| HARDWARE | #380 `a4ec0383...` | Poll PASS; Mbed 3/3 PASS; Full Controller parity FAIL; Native NOT RUN |

## 5. COE #26 exact-tree, test and license provenance

Current refs: COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243`; PR #26 candidate `b382d233ff06c8791b1028bed3c617cc7b670d12`. PR #26 remains OPEN/DRAFT/NO-GO with 205 changed files.

Recursive trees were complete and non-truncated:

| Tree | Entries |
|---|---:|
| Pinned source `BlazingSystems-Experiments@6d4c9b487af4d768c4d7627654d119417fcc6e00` | 2,391 |
| Current Experiments main `6be5d19b...` | 2,341 |
| COE PR #26 candidate | 286 |
| COE main | 3 |

### Runtime import

- All 61 runtime rows match the actual pinned-source and destination Git blob SHAs and file modes.
- Actual classification: 46 byte-identical / 15 derived.
- `SOURCE_INTAKE.json` per-file status rows also classify 46/15, but its summary counters still say 47/14. The summary is stale by one; the exact tree and row-level manifest agree at 46/15.
- Relative to current Experiments main, the pinned 61-file source set has 33 unchanged, 20 changed and 8 absent paths. The destination is still pinned to the older source snapshot; this is not authorization to refresh or copy.

### Test identities and mapping

- Four original tests: 4/4 exact source/destination blob-and-mode identities; two unchanged (`portal.sh`, `security.sh`) and two derived (`config.sh`, `integration.sh`).
- Fifteen derived test entries: 15/15 actual destination blob-and-mode identities match `SOURCE_INTAKE.json`.
- `MIGRATION_MAP.md` maps only 14/15 derived tests; `tests/voucher_txn_journal.sh` is missing.
- The map's `run_focus.sh` hash is stale (`fa1f4f2c...`; actual destination/manifest `2b7b861e...`).
- The map's `member_txn_journal.sh` hash is stale (`01dc9c65...`; actual destination/manifest `d04df3c6...`).
- The manifest's current derived-test hashes match the destination tree; the stale values are in the human migration map.

### License scope

The source project tree contains 11 license/notice artifacts; the destination contains four. All four legal artifacts within the current PisoWiFi import scope are exact source/destination blob matches: first-party `Pisowifi/LICENSE`, QR-code vendor LICENSE, TailAdmin LICENSE and TailAdmin NOTICE. The other seven source legal artifacts belong to Android Launcher, R281 Rental, jsqr test vendor and UI vendor paths outside this PisoWiFi-only intake. No in-scope license counterpart is missing.

### Candidate CI and branch pin

All five PR #26 candidate workflows are CANCELLED; the exact candidate combined status list is empty. No CI pass is claimed.

`SOURCE_INTAKE.json` still names destination branch `feature/pisowifi-cleanup-stabilization`, while the live PR #26 head branch is `integration/ecosystem-nonproprietary-candidate-20261111`. This is a stale destination branch pin. No staging, copy, move, overwrite, rebase, cherry-pick or destination write was performed.

## 6. Governance, registry access and execution limits

- Experiments root `AGENTS.md`, README, `README_FIRST`, `COMMUNICATION_PROTOCOL` (BLAZE-COMMS/1), Cloud Artifact Policy and Cloud Storage Recovery Handover were read.
- The Cloud Artifact Policy requires the canonical private registry and sync ledger before mirror/artifact work. The exact private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not recovered from Library search; only historical v3–v7 copies were found. No Google Drive connector/action is exposed. No older registry was substituted and no private IDs/data were copied to GitHub. No mirror artifact/folder was created.
- COE root `AGENTS.md` returned 404; its README is only a title line.
- Branch-protection reads returned 403 for Experiments main, development, Master and COE main. Effective protection/required-check enforcement remains UNKNOWN; repository administrator must verify.
- Automation inventory exposes active `Phoenix Master Hourly Development` and `Blaze Hourly Production Development`; the exact named CORE automation `Blaze Production Continuation` was not visible. CORE remained read-only; no competing worker or automation was created, changed or disabled.
- No authenticated non-Codex local checkout was available. Master `verify_coordination.py`, `test_verify_coordination.py`, full Python/shell/native suite and Master CI were NOT RUN. In-memory tree/manifest/blob comparisons above are static source checks, not repository test executions. Master exact-head combined status was empty.

## 7. Required next actions

1. HARDWARE: refresh #380 PR body and handover to current head `a4ec0383...`; retain #380 as the canonical DRAFT successor of #377; keep #378/#379 open and unmerged.
2. CORE: publish the canonical versioned authenticated controller configuration envelope. No positive admission until reviewed.
3. QA: resolve Controller protocol parity semantically and PAY-0745 independently; add/route Native coverage only through the QA-owned workflow/source scope.
4. COE integration owner: correct the 46/15 summary, add the missing voucher map row, refresh the two stale map hashes and destination branch pin, then obtain new exact-head CI.
5. Registry custodian: provide authorized access to private v11 and newer corrections.
6. Repository administrator: verify effective branch protection and provide a non-Codex validation checkout.

**Disposition: PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory. No merge, release, signing, secret provisioning, flashing, physical testing, real payment operation, financial migration or customer cutover occurred.
