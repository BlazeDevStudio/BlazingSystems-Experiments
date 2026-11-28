# PHX-MASTER UTC21 — live owner heads and COE #26 exact-tree migration audit

**Updated:** 2026-11-24T21:51:25Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Execution:** Strict NO CODEX; GitHub read-only inspection plus Master-owned coordination documentation.  
**Disposition:** PR #288 remains OPEN / DRAFT / UNMERGED; COE #26 remains FROZEN; PRODUCTION NO-GO.

## 1. Exact repository references

| Repository/ref | Exact SHA | State |
|---|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b | Default branch |
| Experiments development | blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5 | Current named development branch |
| Experiments Master | phoenix/master-coordination@c0a465d157d491afbb2a06eaea8fdd4ab81a3615 | Existing branch reused |
| Master PR #288 | base main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b | OPEN / DRAFT / UNMERGED; 202 paths before this commit, all coordination/phoenix |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 | Default branch |
| COE integration PR #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | OPEN / DRAFT / FROZEN; 205 changed paths |

Issue #172 is OPEN. Cleanup issue #266 is OPEN, 0/7. OWNERSHIP_ROUTES.json blob e4db324315a1b3543fec17a148fbf960170fcb29 has 11 routes, DRAFT_REVIEW_ONLY, and null PHX-MASTER target.

## 2. Latest owner heads and exact-head CI

### Experiments role PRs

| Owner | Current ref | CI evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) scoped build PASS |
| RENTAL #328 | 0e0da62acd47c6a1ce287f8a30fc700d603fa070 | [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) APK PASS; [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) API PASS; [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) build FAIL |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) synthetic Windows PASS |
| HARDWARE #347 | 960184670379f01e20f0e7e8bc23b3e5eedacd3f | [#45299741995](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45299741995), [#45299742437](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45299742437), [#45299741993](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45299741993): all FAIL |
| HARDWARE #348 | eb7afcb2ba0d1e84054c052c8b129cb51a91d062 | [#45352513178](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45352513178) header PASS; [#45352513177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45352513177) build FAIL |
| HARDWARE #349 | source/test 8c0626942815f1782211b6be784cf995ac5c5038; docs/PR 2381c9708dab32a1e1d751a6638dfc355baa0e8c | [Relay #45484860111](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45484860111) PASS; [Quarantine #45484859902](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45484859902) PASS; [build #45484860124](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45484860124) FAIL in validate job 138767419364: Missing poll signature check. 14 target/platform jobs + Android pass; dependent stages skip. PR body still names older 639635c / 05d91c8 and must be refreshed by HARDWARE. |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) Windows PASS |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No PR-triggered runs; no pass claimed |
| RELEASE #291 | current PR/docs HEAD 53fc8a1c558f80adde19dc675b879c78797f0cd5 | [Windows #45485465901](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45485465901) FAIL at shared handover freshness; [build #45485465992](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45485465992) FAIL at mandatory handover freshness; [ESP32 compatibility #45485465888](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45485465888) PASS. Canonical CURRENT_STATE.md remains blob 85dd3c1e9254d947c4e75daaeaf3351ef3e105e3, last checkpoint d85eb6a2766781b6cac1807cef461993d8216b84. CORE owns that file; RELEASE owns workflows; PISONET owns inherited tests; QA reviews. PR body still lags live head. |

### COE release/integration PRs

| PR | Current exact head | Exact-head CI |
|---|---|---|
| #35 release infrastructure | source/test d7a6b806e2d05a13f4d117d93828feb2953b36ca; final handover/PR ab0fabf0e565ae31c8f69b110d1d63bb3af4df4f | [Shared/firmware #45493927846](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45493927846): 213/215 tests pass, 2 skipped; shared contracts 18/18 and manifest durability pass; all ten appliance profiles fail closed without approved site-scoped RFC 4193 ULA /48; compile jobs skipped. [Sandbox #45493927821](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45493927821): 40/40 host preflight tests pass; Bubblewrap absent, exit 125; namespace/package steps skipped. [Case guard #45493927854](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45493927854) PASS. PR body remains UTC15 and is stale. |
| #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | [Overlay #44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) + [case #44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS |
| #49 | aeb8ff11b2f5db9a5f86280ab62ab988245f3919 | [Stage 5.1 #44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) + [case #44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; [shared hardware #44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL |
| #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows QUEUED, zero jobs/statuses; destination frozen |

## 3. Exact COE #26 migration provenance

### Tree identities

| Ref | Tree SHA | Entries |
|---|---|---:|
| Historical source pin 6d4c9b487af4d768c4d7627654d119417fcc6e00 | 9b0ec594cb5d2bfe62d09d4a7fb9a254b9ffad3f | 2,391 |
| Current #349 source/test 8c0626942815f1782211b6be784cf995ac5c5038 | 06e48c6ce1015850921769a9e80886f4036be749 | 2,527 |
| COE #26 destination b382d233ff06c8791b1028bed3c617cc7b670d12 | 8a7d4cf81d7227118b876c1138dd2da12345fefa | 286 |

All trees were recursive and non-truncated.

### Intake row checks

- Pisowifi/SOURCE_INTAKE.json blob 1b9018ff944f7f673934d0fc2a97e0a0090d3f5f has 61 runtime rows. Every row matches the historical source blob/mode and destination blob/mode: 61/61 each.
- Actual runtime classification: 46 byte-identical, 15 derived. The JSON summary says 47 identical / 14 derived. This one-row mismatch blocks staging until the COE intake owner fixes the summary.
- Current #349 source/test differs from historical source pin on 28/61 runtime paths: 20 changed blobs, 8 missing. Do not rebase the intake pin silently.

### Tests and migration map

- Current #349 test subtree: 47 entries (46 executable tests + README); COE destination: 19 executable tests. Exact path/blob/mode comparison: 1 exact, 3 divergent, 42 source-only, 15 destination-only. Divergent paths: config.sh, integration.sh, security.sh.
- SOURCE_INTAKE.derived_tests has 15 entries; MIGRATION_MAP.md has 18 test rows total (four original + 14 derived). voucher_txn_journal.sh is absent from the map.
- Stale map hashes: run_focus.sh claims fa1f4f2c6393504499d50659d8bf980caf7ff85b, actual destination 2b7b861ec63cf811d18e0d63b11a65efd1bec0e9; member_txn_journal.sh claims 01dc9c65ae9d74eaafb403d47aebcd20edd14390, actual d04df3c6f3ada60b9fda8c8c04230dd31e37019a.

### Board imports and licenses

- Source ESP32/ESP8266 subtrees: 66 entries, including 52 Python lab/helper files. COE Hardware/esp32 + Hardware/esp8266: four entries only; zero Python helpers. Both sketches differ: ESP32 adfd2f11 vs 3cc7ec54; ESP8266 8a0b458b vs c8be98f7.
- Exact license/notice counterparts: Pisowifi/LICENSE, rootfs QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE.
- Missing/unrouted counterparts: UI QRCode LICENSE and UI Tabler LICENSE (no UI route in manifest); BlazeRentalLauncher LICENSE and assets/license.html (separate Rental/android route). These require owner route/license disposition; no Master copy.

**COE #26 remains frozen.** No staging, copy, move, overwrite, rebase, cherry-pick or destination write was performed.

## 4. Governance and access

- OWNERSHIP_ROUTES.json: 11 routes, DRAFT_REVIEW_ONLY, PHX-MASTER target null.
- Experiments main, development and COE main branch records report protected=false; both repositories' ruleset lists are empty. Branch-protection detail endpoint returned 403; Master branch protection not independently established.
- Root AGENTS.md was read at f4e8a891. It requires private Drive registry/manifest/ledger before new mirror artifacts and forbids public disclosure of private IDs.
- Canonical private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections are NOT_RECOVERED; no Drive connector was exposed and no older Library snapshot was substituted.
- Separate CORE continuation automation remains outside Master; no parallel CORE work was started.

## 5. Tests and execution distinction

**Executed:** exact branch/PR/issue reads; complete recursive Git trees; historical/current/destination blob+mode comparisons; intake/map row checks; license/path checks; exact-head GitHub Actions status and failed-job log inspection; Master document scope inspection.

**Not executed:** Master Python unittest suite; verify_coordination.py; Master PR Actions (zero runs/statuses); any local product build; physical test, power cut, device soak, financial migration, signing or release.

These are read-only source/tree/CI inspections, not a Master test-suite pass.

## 6. Next owner actions

1. CORE updates canonical CURRENT_STATE.md and supplies the authenticated poll/register producer contract; RELEASE reruns #291 exact-head Windows/build only after the canonical checkpoint is fresh.
2. HARDWARE refreshes #349 PR body to 8c062694 / 2381c970; QA independently reconciles the missing poll-signature assertion without weakening deny-default.
3. COE release owner updates #35 PR body to d7a6b806 / ab0fabf0, obtains approved site-scoped ULA /48 authority, and arranges an authorized disposable Bubblewrap runner.
4. COE integration owner corrects 46/15 summary, 15-vs-14 derived test mapping, missing voucher row, two stale hashes, 28 source drift rows, board helper/sketch gaps, and license routing before any staging proposal.
5. Registry custodian restores authorized private v11 access; repository administrators establish effective branch protection.
6. Authorized human runner executes Master Python tests and the coordination verifier.

## 7. Safety disposition

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device 24-hour soak, and owner-authorized release gates remain unverified.

No merge, release, signing, secret provisioning, hardware flash, physical test, real payment operation, customer cutover or financial migration occurred.
