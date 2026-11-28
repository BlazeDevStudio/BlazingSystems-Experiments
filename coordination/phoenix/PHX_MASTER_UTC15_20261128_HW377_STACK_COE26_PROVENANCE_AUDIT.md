# PHX-MASTER UTC15 — HARDWARE stack integration, shared handovers, and COE provenance

**Audit time:** 2026-11-28T15:36:30Z  
**Role/task:** PHX-MASTER · `PHX-MASTER-20261128T15Z-HW377-COE26-PROVENANCE-376-OVERLAP`  
**Scope:** `coordination/phoenix/`, architecture/interface contracts, exact-head role matrix, and cross-repository migration provenance only. Strict NO CODEX.

## 1. Live refs and governance

| Ref | Exact SHA / state |
|---|---|
| Experiments `main` | `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5` |
| Experiments `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Active v0.6 foundation | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master input head | `76084627e5dd7555f1d01343726b0528768d7b98` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

PR #288 remains OPEN / DRAFT / UNMERGED. At the audited input head it compares 717 ahead / 1 behind current main, merge base `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`, with 273 changed paths, all under `coordination/phoenix/`. `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER target `null`.

Re-read the uploaded `00_MASTER_PROJECT_PHOENIX(1).txt`, README_FIRST, BLAZE-COMMS/1 protocol, Experiments root `AGENTS.md`, current Master documents, issue #172, cleanup issue #266, role PRs/CI, COE main and PR #26. The AGENTS-linked cloud policy and storage handover were located in the current `BlazeDevStudio/BlazingSystems` repository after the old `BlazingSystems/BlazingSystems` owner URL redirected.

## 2. HARDWARE #374/#375 integration is now represented by #377

PR #377 is OPEN / DRAFT / UNMERGED at `95e54790ab986dab3c1b3723ea9603a3d125c0d6`, based on #374 `cfb19ed5df920bf5fa7e33e08dc73a25f8b14db9`. Its integration merge commit `4d99c023aa65ed84c6e80d705acc3da044d13075` has first parent #374 and second parent #375 `94b1231c631eb32da0f019604ce00a4a0851a471`. This verifies the previously requested sequence: #366 → #373 → #374, then a child of #374 carrying #375. The original #375 branch was preserved; no force-push or merge occurred.

All nine #374/#375 overlapping paths are reconciled in #377's two-parent integration commit. PR #377 has eight commits and 13 changed paths (the nine shared paths plus four new handover records).

Exact-child CI on #377:
- Poll [#46158944089](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46158944089): PASS; both boards' deny-only/polarity and EEPROM/pending-recovery host matrices pass. Explicitly simulated-only.
- Mbed TLS [#46158944181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46158944181): 3/3 PASS (source contract, ESP32 core 3.3.13 and 4.0.0).
- Native [#46158944131](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46158944131): FAIL at QA-owned PAY-0745 literal assertion `assert "if(any) return false;" in text`.
- Full [#46158944182](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46158944182): validation fails at QA-owned `tests/controllers.sh` Controller parity requiring `config_revision`; all 14/14 target/platform jobs pass. Update bundle, simulations, signer and publish stages are skipped.

QA owns PAY-0745 and Controller parity semantics. HARDWARE owns firmware, branch sequencing and append-only handovers. CORE owns authenticated register/poll/receipt/disposition contracts. No QA, CORE or HARDWARE source/test file was modified by Master.

## 3. New unresolved #376/#377 shared-handover collision

PR #376 is OPEN / DRAFT at `22ff6eb054b9578daf74a30d5c04d51fd754917e`, based on #356 `0ea32d31ed5c902b2187d98c181aab14bc9fdeae`. Its focused run [#46157303529](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46157303529), Mbed 3/4 [#46157303545](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46157303545), and Full [#46157303505](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46157303505) are all PASS. The Full run completed target builds, update bundle and v0.4 simulations; release publication, production signing handoff and prerelease publication were skipped.

Exact changed-file intersection between #376 and #377 is three append-only records:
- `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md`
- `experiment/openwrt/BlazePwifi/docs/handover/CURRENT_STATE.md`
- `experiment/openwrt/BlazePwifi/docs/handover/CHANGE_LEDGER.md`

Their ancestry is divergent, not a simple parent/child relationship: #356 `0ea32d31...` versus #374 `cfb19ed5...` compare as 280 ahead / 26 behind with merge base active v0.6 `2fbd2475...`. The changed source/tool/workflow paths are otherwise disjoint. No automatic sequence is prescribed. HARDWARE must choose and document a canonical integration order, reconcile these three records without deleting/replacing history, preserve both draft branches, then rerun exact-head CI. Master did not edit either branch.

## 4. Other live role heads and exact-head CI

| Role / PR | Exact head | Current evidence |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; CORE untouched. |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | Build [#43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) and native auth [#43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS. |
| RENTAL #328 | `10fc200b6dbf470a95e679d3acc58aff4ab2a67f` | Build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL; API21/23 smoke [#45622918364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), native auth/recovery [#45622918551](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551), APK identity [#45622918340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340) PASS. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows release [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM acceptance not established. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | Windows synthetic [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No exact-head workflow run. |
| RELEASE #291 | `bf339a76964a1abe2412fac45392fe06a8e66418` | No exact-head workflow run. |

## 5. Active v0.6 P0 remains unchanged

At active v0.6 `2fbd2475...`, ESP8266 performs a 3,500 ms synchronous `post("poll")` at line 354 before the first `digitalRead(runCoinPin)` at line 357. ESP32 does the same at lines 314 and 318; its 3,500 ms timeout is at line 230. Issue #177 remains OPEN. #377 is an unmerged deny-only candidate and does not fix the active branch's poll-before-first-sample race or prove durable pulse retention.

## 6. COE #26 exact migration provenance — corrected licensing scope

COE main remains `a6513ab4412b4c014eee2863e45cbe32d06cb243`; PR #26 remains OPEN / DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`, branch `integration/ecosystem-nonproprietary-candidate-20261111`, 205 changed files. `SOURCE_INTAKE.json` still pins destination branch `feature/pisowifi-cleanup-stabilization`, which is stale.

Non-truncated recursive trees: pinned source 2,391 entries; current Experiments main 2,341; COE candidate 286.

- Runtime manifest: 61/61 rows match exact pinned source and candidate destination blob + mode. Actual classification is 46 identical / 15 derived, not the manifest summary's 47 / 14.
- Pinned-source to current-main runtime drift: 33 unchanged, 20 changed, 8 absent.
- Original tests: 4/4 source/destination blob + mode identities match. Derived tests: 15/15 candidate blobs + modes match `derived_tests`.
- `MIGRATION_MAP.md` has only 14 derived-test rows; it omits `voucher_txn_journal.sh`. Two recorded hashes are stale: `run_focus.sh` (`fa1f4f2c...` recorded vs `2b7b861e...` actual) and `member_txn_journal.sh` (`01dc9c65...` recorded vs `d04df3c6...` actual).
- Licensing correction: the source project contains 11 legal artifacts and the candidate contains four. All four that belong to this PisoWiFi intake (first-party `Pisowifi/LICENSE` plus the three runtime qrcode/tailadmin LICENSE/NOTICE files) match the exact source blobs. The other seven source legal artifacts are under Android, R281 Rental, tests/vendor/jsqr and UI vendor paths outside this 61-file PisoWiFi runtime + test intake. They are not missing counterparts for this scoped import. Earlier Master wording that counted all seven as missing migration counterparts was overbroad and is superseded by this exact scope audit.
- All five candidate workflows are CANCELLED; candidate exact-head CI is not established. Intake flags remain `release_authorized=false`, `hardware_tested=false`, `full_ci_tested=false`, `source_admission_complete=false`.

No destination staging, copy, move or write occurred. COE #26 remains FROZEN.

## 7. Registry, tests, cleanup and production gates

The private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not recovered. The complete ChatGPT Library listing contains registry versions v3–v7 only; no Google Drive connector/action is available in this runtime. Per the current Cloud Artifact Policy, registry/sync work is BLOCKED rather than substituted with an older version. No private registry contents or IDs were copied to GitHub.

Cleanup issue #266 remains OPEN / 0 of 7. Master local repository suite, `verify_coordination.py`, and Master GitHub Actions were NOT RUN because no authenticated non-Codex checkout is available. The nine bounded in-memory/source-tree assertions for runtime, test identity, licensing scope, tree completeness and merge parents PASS; these are audit assertions, not repository test-suite execution.

CORE remained read-only; no competing CORE work was started. No ownership route was changed.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain unverified. No merge, release, signing, secrets, flash, physical test, payment operation, financial migration or customer cutover occurred.

## 8. Next owner actions

1. HARDWARE: resolve the three #376/#377 shared append-only records, choose a canonical integration order for the divergent branches, preserve both histories, and rerun exact-head CI.
2. QA: replace PAY-0745 and Controller parity literal source-shape assertions with semantic, source-linked default-deny tests; rerun Native and Full.
3. COE integration owner: correct the 46/15 intake summary, add the voucher test map row, refresh two stale test hashes and the destination branch pin, then obtain candidate CI before any staging proposal.
4. Registry custodian: provide the canonical private v11 registry and newer corrections through approved Drive access.
5. Repository administrator: provide a usable authenticated non-Codex checkout and verify effective branch protection / required-check enforcement.