# PHX-MASTER UTC12 — live exact-head, role CI and COE #26 provenance audit

**Observed:** 2026-11-27T12:41:33Z  
**Role / task:** PHX-MASTER / PHX-MASTER-UTC12-20261127  
**Execution:** connected GitHub API and repository tree/blob readback; no Codex; no authenticated local checkout; no Google Drive connector exposed.  
**Disposition:** coordination-only; PR #288 OPEN / DRAFT / UNMERGED; COE #26 FROZEN; cleanup #266 OPEN / 0-of-7; P0 #177 OPEN; **PRODUCTION NO-GO**.

## History integrity correction

The first documentation commit, cfb1a86ba78b0cb71c6bd913dfddf430ac72e7c3, was accidentally created without the original base tree and briefly exposed an incomplete tree containing only the new coordination paths. It was immediately followed by restoration commit 56b5d13e1d9852fb58c726edab968bf3b22b522a, which rebuilt from the original parent tree 9c34673a0374c2538ed762882c831bb9169750df and reapplied the seven intended coordination-file changes.

Direct blob-tree comparison from pre-update parent abdc32e0989c6a88ac8daa01b1b13b503f8bf037 to the restored state verified the full repository tree (2,594 entries) and exactly seven file changes: six coordination documents modified and this audit report added; zero non-coordination files changed. No force-push or history rewrite was used. The intermediate commit remains in history, but it is not the current branch tree. The current branch was verified at 56b5d13e1d9852fb58c726edab968bf3b22b522a before this correction note.

## 1. Live repository refs and Master PR

- Experiments default branch: main at 6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5.
- Active v0.6 development branch: blazepwifi-v0.6.0-audit-foundation at 2fbd2475e9f54878c316fa7cea2f228386b0e859.
- Legacy v0.5.3 development branch: blazepwifi-v0.5.3-development at aad3aade72c1156eecba1fed30907c6d0283b2c5.
- Master branch before this commit: phoenix/master-coordination at abdc32e0989c6a88ac8daa01b1b13b503f8bf037.
- COE default branch: main at a6513ab4412b4c014eee2863e45cbe32d06cb243.
- COE integration PR #26: integration/ecosystem-nonproprietary-candidate-20261111 at b382d233ff06c8791b1028bed3c617cc7b670d12, based on COE main a6513ab.

Master PR #288 remains OPEN / DRAFT / UNMERGED, head abdc32e0989c6a88ac8daa01b1b13b503f8bf037, base main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b. Compare against the live main head reports 659 ahead / 1 behind, merge base f4e8a891. All 251 changed paths are under coordination/phoenix/. No rebase, retarget or merge was performed. Exact-head Master workflow runs and combined statuses are both empty; no Master CI pass is claimed.

## 2. Ownership and cleanup

- OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29, schema v1, 11 routes, status DRAFT_REVIEW_ONLY. PHX-MASTER target remains null. No route or owner was changed.
- Cleanup issue #266 remains OPEN and 0-of-7. The broad cleanup inventory is not complete; no source mass-move, rename or deletion is authorized by this checkpoint.
- CORE, RENTAL, PISONET, HARDWARE, QA and RELEASE source ownership remains with their assigned roles. PHX-MASTER changed no subsystem source branch and did not edit COE destination files.

## 3. Live role PRs and exact-head CI

| Role / PR | Exact head | Current exact-head evidence | Owner boundary / next action |
|---|---|---|---|
| MASTER #288 | abdc32e0989c6a88ac8daa01b1b13b503f8bf037 | No workflow runs; zero combined statuses. 251 paths are coordination-only. | MASTER owns coordination/architecture/provenance; no rebase or merge. |
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Build #42698139210 PASS (scoped build only). | CORE remains reserved to its separate owner; no MASTER source work. |
| RENTAL #328 | 10fc200b6dbf470a95e679d3acc58aff4ab2a67f | API21/23 #45622918364 PASS; auth/installer #45622918551 PASS; APK identity #45622918340 PASS; shared build #45622918468 FAIL. | RENTAL owns shared build and handover correction. |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Windows synthetic #42462978704 PASS. | Native COM/device acceptance remains NOT TESTED. |
| HARDWARE #358 | fc8b429b9c73a6fee0b0732f6d82b2c5c550e75c | Relay #46001496577 PASS; Quarantine #46001496578 PASS; build #46001496571 FAIL at Controller protocol parity. ESP32/ESP8266 and listed target jobs pass; downstream release/signing stages skip. | HARDWARE owns its ESP8266 source/fixture and handover; QA/CORE own the semantic protocol assertion. |
| HARDWARE #359 | 47357aab2ff7910b38ca538a46dfa01bdbca01e8 | Poll #45997708842 PASS; Mbed #45997708753 PASS; build #45997708895 FAIL at Controller protocol parity; Native #45997708911 FAIL at PAY-0745 durable Vendo pending-sequence/corruption contract. | HARDWARE owns recovery source; QA/CORE reconcile semantic disposition without adding unsafe clear calls. |
| HARDWARE #360 | b1a709c2281f958ed295139523a52817af4459fd | Poll #45997731187 PASS; Mbed #45997731166 PASS; Full #45997731177 FAIL at Controller protocol parity. | HARDWARE owns the no-actuation outcome matrix; it does not resolve the blocking-poll P0. |
| QA #290 / #292 | 5c29d15994cee1279058f1eca12f2a3180704292 / 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | #290 Windows synthetic #43633486963 PASS; #292 has no PR-triggered workflow run. | QA must independently verify the current semantic contract; older green checks do not transfer to #292. |
| RELEASE #291 | bf339a76964a1abe2412fac45392fe06a8e66418 | No exact-head PR workflow run returned. | RELEASE owns signing/publisher and exact-head release evidence. |

CI run URLs:
- #358: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46001496577 · https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46001496578 · https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46001496571
- #359: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997708842 · https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997708753 · https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997708895 · https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997708911
- #360: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997731187 · https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997731166 · https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997731177

These are owner-run CI results at the listed exact PR heads, not Master test execution or physical acceptance.

## 4. COE #26 destination provenance — frozen, no staging

Read-only recursive trees are complete and non-truncated:

| Tree | Exact SHA | Entries | Blob entries |
|---|---|---:|---:|
| Hardware source candidate #358 | fc8b429b9c73a6fee0b0732f6d82b2c5c550e75c | 2,575 | 1,996 |
| COE destination #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | 286 | 207 |

The two destination controller sketches are not byte-identical to the current #358 source candidate:
- ESP32 source blob 8154297e30e72d82692987ed5690983df4955aea; COE blob 3cc7ec54b476943dc04a8d1af5e2df5fe054e422.
- ESP8266 source blob 64faba024f0edd6b88b5331ce043745f74a8b3e2; COE blob c8be98f72596681e36a3ad1f8939bf8046c96887.

Mapped PisoWiFi tests: source 47 / destination 19; 1 identical, 3 divergent, 43 source-only, 15 destination-only. The source candidate also has 32 board-local Python lab files absent from the destination test route. This is a path/blob identity comparison, not proof that any derived test is behaviorally equivalent.

Formal project LICENSE/NOTICE path comparison: 8 source paths / 4 destination paths; 4 exact path/blob counterparts and 4 source paths without exact destination counterparts. The UI QRCode license path duplicates the blob already mapped under the OpenWrt QRCode path. The source also contains an Android license.html asset without a mapped destination counterpart. This is provenance evidence, not legal approval.

COE SOURCE_INTAKE.json blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f has 61 runtime rows. Its summary says 47 byte-identical / 14 derived, while the actual rows are 46 / 15. It lists 15 derived tests; MIGRATION_MAP.md blob b54fc15d83bc2269de03db8aadd0e76259fd13d9 contains only 14 test rows and omits voucher_txn_journal.sh. The run_focus.sh and member_txn_journal.sh hashes also disagree between the two documents. SOURCE_INTAKE names destination branch feature/pisowifi-cleanup-stabilization, while live PR #26 targets integration/ecosystem-nonproprietary-candidate-20261111. The destination HARDWARE_FIRMWARE_AUDIT.md says the two sketches were not copied, but the exact current COE tree contains one divergent sketch under each board directory.

All five COE #26 workflows are CANCELLED with zero jobs and the candidate commit has zero combined statuses:
- https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609
- https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632
- https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800
- https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563
- https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557

Disposition: keep #26 FROZEN. Do not copy, move, overwrite, rebase, cherry-pick, retarget or stage files. The COE integration owner must reconcile the branch pins, exact firmware blobs, 46/15 versus 47/14 counts, derived-test identities/hashes, missing test imports and license/notice paths before requesting a new same-SHA review.

## 5. Active P0 and production gates

Issue #177 remains OPEN. The active v0.6 source branch is still 2fbd2475e9f54878c316fa7cea2f228386b0e859:
- ESP8266 blob 12c4bb82b6fddafe813674a0b5f692c1d3634073: synchronous poll at line 354 precedes the first coin sample at line 357; HTTP timeout is 3,500 ms.
- ESP32 blob 29f1125d52ff474a0d028ad41f7af201be1f0f9d: synchronous poll at line 314 precedes the first coin sample at line 318; HTTP timeout is 3,500 ms.

The active source readback confirms the ordering is still present; no physical coin pulse, relay, power cut or payment was operated. Financial durability issues #31 and #32, independent freshness witness issue #43, and physical acceptance issue #34 remain OPEN. The required 150 real power cuts and 30-device / 24-hour soak have NOT been performed or independently accepted.

Production remains NO-GO pending protected signing and independent anti-rollback witness, crash-atomic durable financial state and replay handling, reversible migration tests, independent QA, native target acceptance, physical acceptance, and owner-authorized release gates. No signing, secret provisioning, firmware flash, payment operation, customer migration, release or merge occurred.

## 6. Execution limitations and next exact actions

- The private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not recovered. The connected Library surfaced only older registry snapshots; no older snapshot was substituted. The available tool surface exposes no Google Drive connector, so private Drive registry review is BLOCKED. Registry custodian: restore authorized Drive access or provide the current private registry and append-only corrections through an approved private channel.
- No authenticated local checkout is available. The Master Python suite and verify_coordination.py were NOT RUN; no Master exact-head CI run exists. Read-only GitHub tree/blob inspection is not a substitute for those tests.
- COE integration owner: reconcile #26 intake/map branch pins, row counts, test identities, firmware and license/notice provenance; rerun only after a proposed immutable candidate SHA is agreed.
- PHX-CORE and PHX-QA: approve and independently test the poll-response signature, receipt/disposition and durable-clear contract; preserve deny-only behavior while unresolved.
- PHX-HARDWARE: resolve the current #358/#359/#360 owned CI failures and update its handovers; no Master source takeover.
- PHX-MASTER: rerun local coordination validators when an authenticated checkout is available and keep the release gate NO-GO until all independent evidence is supplied.

No subsystem source, ownership manifest, COE destination, firmware, payment state or release artifact was modified in this audit.
