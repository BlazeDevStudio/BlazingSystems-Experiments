# PHX-MASTER UTC13 — live head, role CI and COE provenance revalidation

**Observed:** 2026-11-27T13:11:40Z  
**Role / task:** PHX-MASTER / PHX-MASTER-UTC13-20261127  
**Execution:** connected GitHub API, exact branch/PR/issue/workflow readback, recursive Git tree and blob comparison; no Codex.  
**Disposition:** coordination-only; PR #288 OPEN / DRAFT / UNMERGED; COE #26 FROZEN; cleanup #266 OPEN / 0-of-7; P0 #177 OPEN; **PRODUCTION NO-GO**.

This checkpoint is the first PHX-MASTER UTC13 message found on issue #172 for 2026-11-27. CORE remains reserved to its separate continuation. No CORE or other subsystem source branch was modified.

## 1. Exact repository refs and Master PR

| Ref | Exact SHA / state |
|---|---|
| Experiments default branch main | 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5 |
| Active development blazepwifi-v0.6.0-audit-foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Legacy development blazepwifi-v0.5.3-development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Master branch at audit start phoenix/master-coordination | fa6f16038e535fbca36d4906bebe3d79632370e4 |
| COE default branch main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration PR #26 | OPEN / DRAFT / UNMERGED; integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12 |

Master PR #288 is OPEN / DRAFT / UNMERGED, head fa6f16038e535fbca36d4906bebe3d79632370e4, base main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b. At audit start it had 662 commits and 252 changed paths; all 252 paths were under coordination/phoenix/. Exact-head Master workflow runs and combined statuses are empty. The new report and four existing coordination-document refreshes are committed only to this existing Master branch; no rebase, retarget, merge or force-push is authorized.

## 2. Live role PRs and exact-head CI

| Role / PR | Exact head | Exact-head evidence and disposition |
|---|---|---|
| MASTER #288 | fa6f16038e535fbca36d4906bebe3d79632370e4 | No workflow runs or combined statuses. Coordination-only. |
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build #42698139210 PASS (scoped build only). CORE implementation remains with the separate active CORE continuation. |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | API21/23 #45622918364 PASS; auth/installer #45622918551 PASS; APK identity #45622918340 PASS; shared Build #45622918468 FAIL. RENTAL owns the shared build/handover correction. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows synthetic #42462978704 PASS. Native COM adapter/device acceptance remains NOT TESTED. |
| HARDWARE #358 | fc8b429b9c73a6fee0b0732f6d82b2c5c550e75c | Relay #46001496577 PASS; Quarantine #46001496578 PASS; Full #46001496571 FAIL at Controller protocol parity. |
| HARDWARE #359 | 47357aab2ff7910b38ca538a46dfa01bdbca01e8 | Poll #45997708842 PASS; Mbed #45997708753 PASS; Full #45997708895 FAIL at Controller protocol parity; Native #45997708911 FAIL at PAY-0745. |
| HARDWARE #360 | b1a709c2281f958ed295139523a52817af4459fd | Poll #45997731187 PASS; Mbed #45997731166 PASS; Full #45997731177 FAIL at Controller protocol parity. |
| QA #290 / #292 | 5c29d15994cee1279058f1eca12f2a3180704292 / 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #290 Windows synthetic #43633486963 PASS, but its workflow does not invoke the native COM lab. #292 has zero PR-triggered workflow runs. |
| RELEASE #291 | bf339a76964a1abe2412fac45392fe06a8e66418 | Zero PR-triggered workflow runs returned for this exact head. |

Run links:  
- HARDWARE #358: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46001496577 · https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46001496578 · https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46001496571  
- HARDWARE #359: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997708842 · https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997708753 · https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997708895 · https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997708911  
- HARDWARE #360: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997731187 · https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997731166 · https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997731177  

These are existing owner-run CI results at the listed exact heads. They are not Master suite execution, native hardware acceptance or production authorization. All role PRs remain draft/unmerged.

## 3. Cleanup gate and active-v0.6 P0 source readback

- Cleanup issue #266 remains OPEN / 0-of-7. Its MASTER checkbox is intentionally not claimed complete; no mass move, rename, deletion or whole-repository cleanup was performed.
- P0 issue #177 remains OPEN. The active development branch was re-read at 2fbd2475e9f54878c316fa7cea2f228386b0e859, not inferred from the issue's older reproduction pin.
- ESP8266 blob 12c4bb82b6fddafe813674a0b5f692c1d3634073 calls post("poll") at line 354 before the first digitalRead(runCoinPin) at line 357; timeout is 3,500 ms.
- ESP32 blob 29f1125d52ff474a0d028ad41f7af201be1f0f9d calls post("poll") at line 314 before the first digitalRead(runCoinPin) at line 318; timeout is 3,500 ms.
- This confirms the blocking poll-before-sample ordering at the active branch. No coin slot, relay, physical power, device or money state was operated. HARDWARE owns firmware intake protection, CORE owns authenticated receipt/disposition and durable financial authority, QA owns independent semantic tests, and MASTER owns only cross-role interface coordination.

## 4. COE #26 exact source/destination provenance revalidation — FROZEN

The complete recursive trees were fetched at exact immutable commits and were not truncated:

| Tree | Commit | Tree SHA | Entries | Blob entries |
|---|---|---|---:|---:|
| HARDWARE #358 source candidate | fc8b429b9c73a6fee0b0732f6d82b2c5c550e75c | 64ee06a5d2a858b7b2728c1fe44b458d1913a1a6 | 2,575 | 1,996 |
| COE #26 destination candidate | b382d233ff06c8791b1028bed3c617cc7b670d12 | 8a7d4cf81d7227118b876c1138dd2da12345fefa | 286 | 207 |

### Firmware and test identity

- ESP32 sketch: source blob 8154297e30e72d82692987ed5690983df4955aea; destination blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422. Divergent.
- ESP8266 sketch: source blob 64faba024f0edd6b88b5331ce043745f74a8b3e2; destination blob c8be98f72596681e36a3ad1f8939bf8046c96887. Divergent.
- PisoWiFi test route: source 47 files / destination 19; 1 exact blob, 3 divergent, 43 source-only, 15 destination-only. This is path/blob identity, not behavioral equivalence.

### License/NOTICE identity

After deduplicating the source's repeated QRCode license blob, the product source contains 8 unique LICENSE/NOTICE artifacts and the candidate destination contains 4. Four exact counterparts exist (PisoWiFi LICENSE, QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE). Four unique source artifacts lack exact destination counterparts: repository-root NOTICE.md, Tabler LICENSE, Android Launcher LICENSE and Android assets/license.html. This is provenance evidence, not legal approval.

### Intake, test-map and audit-document inconsistencies

- Pisowifi/SOURCE_INTAKE.json blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f has 61 runtime rows. Its summary claims 47 byte-identical / 14 derived; actual rows are 46 byte-identical / 15 derived.
- SOURCE_INTAKE lists 15 derived tests. Pisowifi/MIGRATION_MAP.md blob b54fc15d83bc2269de03db8aadd0e76259fd13d9 contains 14 derived-test rows and omits voucher_txn_journal.sh.
- The run_focus.sh test blob differs: intake 2b7b861ec63cf811d18d0e63b11a65efd1bec0e9 vs map fa1f4f2c6393504499d50659d8bf980caf7ff85b.
- The member_txn_journal.sh test blob differs: intake d04df3c6f3ada60b9fda8c8c04230dd31e37019a vs map 01dc9c65ae9d74eaafb403d47aebcd20edd14390.
- docs/audits/HARDWARE_FIRMWARE_AUDIT.md blob 86c06e7574761465b80482430296eb712d985367 says the two sketches have not been copied, but the exact current COE #26 tree contains one divergent sketch under each board directory.

### Routing and CI disposition

- OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29, 11 routes, DRAFT_REVIEW_ONLY; PHX-MASTER target is null. Its source_ref f4e8a891aed8af86d5fd315d28750a0ac3a7372b is historical relative to current Experiments main 6be5d19b. It is not a source-selection or copy authorization.
- SOURCE_INTAKE/MIGRATION_MAP still name source snapshot 6d4c9b487af4d768c4d7627654d119417fcc6e00 and destination branch feature/pisowifi-cleanup-stabilization. Live PR #26 instead targets integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12.
- All five COE #26 workflows are CANCELLED: https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609 · https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632 · https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800 · https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563 · https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557.
- No candidate exact-head CI acceptance exists. Keep #26 FROZEN. Do not copy, move, overwrite, rebase, cherry-pick, retarget or stage any destination file.

## 5. Private registry, tests and blockers

The canonical private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not available through the current tool surface. Library search surfaced older registry snapshots and a later checkpoint summary naming v11, but not the actual canonical v11 file or newer corrections. No Google Drive connector action is exposed. No older snapshot was substituted, and no private Drive identifiers or contents were copied into public GitHub.

Master's Python suite and verify_coordination.py were NOT RUN because no authenticated local repository checkout is available; ordinary GitHub clone access previously failed DNS resolution. The current Master head has no exact-head workflow runs or combined statuses. No project test is claimed from the tree/blob comparisons above.

Next actions:
1. Registry custodian: provide authorized read access to the canonical v11 registry, artifact manifest, sync ledger and newer corrections; do not use the older Library snapshots as substitutes.
2. COE integration owner: reconcile the source/destination branch pins, every mapped blob, the 61-row intake counts, all 15 derived-test identities and license/NOTICE paths; then run all five destination workflows on one immutable candidate SHA before requesting any staging review.
3. HARDWARE/CORE/QA owners: resolve the poll-response/receipt/disposition contract and semantic validation failures on their own branches; keep coin admission deny-only until independently verified.
4. Repository admin: provide an authenticated local checkout or dedicated non-Codex Master CI path for the project suite and verify_coordination.py.
5. Independent QA and authorized release owners: obtain protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, native acceptance, 150 real power cuts, 30-device/24-hour soak and explicit owner-authorized release gates.

No subsystem source, ownership manifest, COE destination file, financial state, secret, firmware, hardware device or release artifact was changed or operated. **PRODUCTION NO-GO.**
