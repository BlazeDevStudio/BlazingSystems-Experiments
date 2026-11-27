# PHX-MASTER UTC14 — live exact-head, owner CI, P0 and COE #26 provenance audit

**Updated:** 2026-11-27T14:57:39Z  
**Role / task:** PHX-MASTER / `PHX-MASTER-UTC14-20261127`  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Working branch at audit start:** `phoenix/master-coordination`  
**Audit-start HEAD:** `47834257ab409b205a80e21eaabee63bb5bd55f4`  
**Disposition:** coordination audit completed; private-registry and Master test execution remain BLOCKED; PR #288 stays DRAFT; COE #26 stays FROZEN; PRODUCTION NO-GO.

This report records source/tree inspection and existing owner CI separately. It does not claim a local Master test run, hardware acceptance, migration approval, or release approval.

## 1. Live refs re-read

| Ref | Exact SHA |
|---|---|
| Experiments default `main` | `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5` |
| Active development `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Legacy development `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master coordination branch at audit start | `47834257ab409b205a80e21eaabee63bb5bd55f4` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

PR #288 remains OPEN / DRAFT / UNMERGED, based on `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`. Comparing current `main` to `phoenix/master-coordination` reports 663 ahead / 1 behind, merge base `f4e8a891`. Its 253 pre-update paths were all under `coordination/phoenix/`; this report adds one coordination-only path. No rebase, retarget, merge, or source-branch edit was performed. Master exact-head workflow runs and combined statuses are empty. The rulesets endpoint returned an empty list; the branch-protection endpoint returned 403, so branch protection was not independently verified.

## 2. Control plane and cleanup

- Issue #172 was re-read. The latest comment at audit time is HARDWARE UTC14 (#361); the latest PHX-MASTER checkpoint is UTC13. This activation is the single PHX-MASTER UTC14 checkpoint for this role/hour.
- Cleanup issue #266 remains OPEN / 0-of-7. Its latest contribution records HARDWARE #361's harness work but explicitly does not complete any role gate. No cleanup checkbox was changed or claimed complete.
- P0 issue #177 remains OPEN. Its body still pins source `9df0a7e7cae31fc06d098d5a0ea7ae27f56a75ed`, while the live active-v0.6 branch is `2fbd2475e9f54878c316fa7cea2f228386b0e859`; the issue's embedded source pin is stale.

### Active v0.6 poll-order readback

The active branch was read at its live HEAD. The current sketch blobs and exact source ordering are:

| Board | Source blob | `post("poll")` index | first `digitalRead(runCoinPin)` index | 3,500 ms timeout |
|---|---|---:|---:|---|
| ESP8266 | `12c4bb82b6fddafe813674a0b5f692c1d3634073` | 14,913 | 15,074 | present |
| ESP32 | `29f1125d52ff474a0d028ad41f7af201be1f0f9d` | 15,497 | 15,668 | present |

Both live sources still synchronously poll before the first coin input sample. This confirms the P0 source-ordering risk; it does not establish a physical coin-loss event in this run. HARDWARE owns firmware intake/relay behavior, CORE owns authenticated receipt/disposition and durable financial authority, QA owns independent semantic regression, and MASTER owns only the cross-role contract.

## 3. Owner PR and exact-head CI reconciliation

All owner PRs below remain DRAFT / UNMERGED. Existing workflow runs are evidence for the exact commit queried; they are not Master-run tests or physical acceptance.

| Role / PR | Current head | Exact-head evidence and owner boundary |
|---|---|---|
| MASTER #288 | `47834257ab409b205a80e21eaabee63bb5bd55f4` at audit start | No PR-triggered runs or combined statuses. Coordination-only. |
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [Build #42698139210 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210), scoped build only. CORE ownership unchanged; no CORE source work by MASTER. |
| RENTAL #328 | `10fc200b6dbf470a95e679d3acc58aff4ab2a67f` | [API #45622918364 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), [auth/installer #45622918551 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551), [APK identity #45622918340 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340), [shared build #45622918468 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468); its validation and ESP32 jobs fail. RENTAL owns correction. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [Windows synthetic #42462978704 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704). Native COM/device acceptance NOT TESTED. |
| HARDWARE #358 | `fc8b429b9c73a6fee0b0732f6d82b2c5c550e75c` | [Relay #46001496577 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46001496577), [Quarantine #46001496578 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46001496578), [Full #46001496571 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46001496571). Physical GPIO/strap acceptance NOT TESTED. |
| HARDWARE #359 | `47357aab2ff7910b38ca538a46dfa01bdbca01e8` | [Poll #45997708842 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997708842), [Mbed #45997708753 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997708753), [Full #45997708895 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997708895), [Native #45997708911 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997708911). HARDWARE owns recovery source; QA/CORE own semantic disposition. |
| HARDWARE #360 | `b1a709c2281f958ed295139523a52817af4459fd` | [Poll #45997731187 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997731187), [Mbed #45997731166 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997731166), [Full #45997731177 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45997731177). No P0 resolution. |
| HARDWARE #361 | `8a1999ccdcab02445ef93c153316e519d9476210` | Source/test SHA `4a85070a1f6a1caa417570a91dcdf355ff072fcc`; [focused #46016953274 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46016953274) (11 recovery scenarios, 16 mutations rejected); [final-head Poll #46018576706 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46018576706); [final-head Mbed #46018576254 PASS, 3/3](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46018576254); [final-head build #46018576372 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46018576372) at QA-owned `tests/controllers.sh:21` (`config_revision` literal parity). The 13 firmware target jobs and Android pass; production import, signing, update, simulation and publication jobs are skipped. The final-head run is a docs-only sync proof plus validation/build matrix; focused harness evidence remains pinned to the earlier tested docs head `8b687a0407d8b53e8ae7213c7db05c7d89778501`. The PR body says no Full rerun was triggered for the final docs head, while the exact-head workflow lookup returns #46018576372; HARDWARE should reconcile the handover/description. QA owns the assertion; do not add a decoy token or weaken deny-only behavior. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [Windows synthetic #43633486963 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963); native COM lab is not invoked. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No PR-triggered run. Base is stale Master `b1ca02e2087f3b1a7169ceab9c34e52646e700df`; QA owns any restack and exact-head test. |
| RELEASE #291 | `bf339a76964a1abe2412fac45392fe06a8e66418` | No exact-head PR-triggered runs. RELEASE owns publisher/signing evidence. |
| RELEASE #242 | `36c0d0bb3e58786359555b307bb784f720f023ce` | No exact-head PR-triggered runs. RELEASE owns signing/admission evidence. |

The separate active automation visible in the automation inventory is **Blaze Hourly Production Development**, whose saved prompt explicitly assigns PHX-HARDWARE and PR #361. The exact title **Blaze Production Continuation** was not present in that inventory. MASTER did not start a competing CORE worker or modify CORE's branch; CORE #252 remains untouched.

## 4. COE #26 destination staging and exact provenance

COE main is `a6513ab4412b4c014eee2863e45cbe32d06cb243`. PR #26 remains OPEN / DRAFT / UNMERGED on `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12`, based on main. Its exact recursive tree is `8a7d4cf81d7227118b876c1138dd2da12345fefa` (286 entries / 207 blobs, not truncated). Current Experiments main tree is `3c32720a899da535849ac9cebb99d47241b712e2` (2,341 entries / 1,765 blobs); current HARDWARE #361 tree is `371da983142eaa20a0479858ebc54d6c7a7facf4` (2,427 entries / 1,881 blobs). All three tree reads were complete and non-truncated.

The following route comparisons are file-path/blob comparisons only, not a selected or approved migration plan. Experiments main is used for CORE/RENTAL/PISONET/QA/RELEASE routes; HARDWARE #361 is used for the two current firmware routes.

| Route | Source files | Destination files | Identical | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| CORE library (main) | 15 | 20 | 6 | 9 | 0 | 5 |
| Vendo CGI (main) | 1 | 1 | 0 | 1 | 0 | 0 |
| Rental Android (main) | 983 | 8 | 0 | 0 | 983 | 8 |
| Standalone rental profiles (main) | 31 | 19 | 0 | 2 | 29 | 17 |
| Rental server (main) | 7 | 4 | 0 | 1 | 6 | 3 |
| Pisonet SoftTimer (main) | 32 | 47 | 13 | 11 | 8 | 23 |
| ESP32 (HARDWARE #361) | 4 | 1 | 0 | 1 | 3 | 0 |
| ESP8266 (HARDWARE #361) | 15 | 1 | 0 | 1 | 14 | 0 |
| PisoWiFi tests (main) | 38 | 19 | 1 | 3 | 34 | 15 |
| Release workflow (main) | 1 | 1 | 0 | 1 | 0 | 0 |

Exact current firmware sketch blobs diverge:
- ESP32 source `d031b0b79b2a50b88318992c7c9312a042ca95a9` vs COE `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.
- ESP8266 source `25d9494ed5109286c5478605cf5b725fbeab6d9d` vs COE `c8be98f72596681e36a3ad1f8939bf8046c96887`.

### Intake, test identity, and license discrepancies

- COE `Pisowifi/SOURCE_INTAKE.json` is blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f`. It pins source commit `6d4c9b487af4d768c4d7627654d119417fcc6e00` and destination branch `feature/pisowifi-cleanup-stabilization` / pre-manifest head `cf59b41e5273bcc42acf59a7971481670e4b2611`. Neither matches the current #26 destination branch/head.
- The intake summary claims 47 byte-identical / 14 derived runtime files. Counting the 61 runtime rows at the exact #26 blob yields 46 byte-identical / 15 derived.
- Intake lists 15 derived tests; `Pisowifi/MIGRATION_MAP.md` blob `b54fc15d83bc2269de03db8aadd0e76259fd13d9` lists 14. The missing map row is `tests/voucher_txn_journal.sh`.
- The `run_focus.sh` blob differs between intake `2b7b861ec63cf811d18d0e63b11a65efd1bec0e9` and map `fa1f4f2c6393504499d50659d8bf980caf7ff85b`; `member_txn_journal.sh` differs between intake `d04df3c6f3ada60b9fda8c8c04230dd31e37019a` and map `01dc9c65ae9d74eaafb403d47aebcd20edd14390`.
- The #361 source tree contains 10 relevant LICENSE/NOTICE paths representing 8 unique blobs. The destination tree has 3 license paths with exact counterparts for the first-party PisoWiFi LICENSE, QRCode LICENSE and TailAdmin LICENSE. Five unique source license/notice blobs have no destination counterpart: repository NOTICE, Android Launcher LICENSE, Android launcher `license.html`, jsQR LICENSE and Tabler LICENSE. This is a provenance gap, not legal approval.
- The routing manifest remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, schema v1, 11 routes, `DRAFT_REVIEW_ONLY`; PHX-MASTER target remains null.

All five exact PR #26 candidate workflows are CANCELLED: [Rental #43096752563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563), [Hardware/Shared #43096752800](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800), [PisoWiFi #43096752557](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557), [case-collision #43096752609](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609), and [SoftTimer #43096752632](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632). The exact destination commit has no combined statuses. **No staging, copy, move, overwrite, cherry-pick, rebase, or retarget was performed. Keep #26 FROZEN.**

## 5. Private registry and execution limits

The canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not accessible. The Library listing contains older v3–v7 snapshots only; no v11 or newer correction was surfaced. A Google Drive connector is not exposed in this execution environment. Per AGENTS.md, no older snapshot was substituted, no private Drive identifiers/content were published, and no artifact was marked verified.

No authenticated local checkout was available for the Master Python suite or `verify_coordination.py`; no Master exact-head CI run exists. The tree and manifest comparisons above are source/tree inspections plus a bounded structural audit, not executions of the repository test suite. No tests were fabricated or reported as run.



### AGENTS.md linked cloud policy and recovery handover — not accessible

The current root `AGENTS.md` requires reading `BLAZE_CLOUD_ARTIFACT_POLICY.md` and `BLAZE_CLOUD_STORAGE_HANDOVER.md` from the legacy `BlazingSystems/BlazingSystems` repository. GitHub fetch of both linked files returned HTTP 400 (no file SHA/metadata), and organization code search surfaced only the AGENTS.md references, not either document. These two required documents are therefore **NOT READ / BLOCKED**, not assumed absent from the owner's private storage. No Drive artifact, folder, binary or registry was created or modified. Human action: repository admin should restore the canonical links or provide the current policy and verified handover through an authorized repository/Drive connection.

## 6. Exact next human actions

1. **QA:** review `tests/controllers.sh:21` against the current deny-only controller contract. Replace or formally retire the stale `config_revision` token-presence assertion only with an approved semantic contract; do not add a decoy token. Run independent tests at the exact current source SHA.
2. **CORE + HARDWARE + QA:** reconcile authenticated poll receipt/disposition, pending preservation, and the P0 #177 poll-before-first-sample ordering. Preserve owner boundaries.
3. **COE integration owner:** reconcile source/destination branch pins, runtime counts, missing derived-test row, test blob mismatches, board sketch divergence and missing license/NOTICE artifacts before any staging review.
4. **Registry custodian:** provide authorized access to the canonical v11 registry and all newer corrections through the restricted Drive path.
5. **Repository admin:** provide a non-Codex authenticated local checkout or a dedicated non-Codex Master CI path so `verify_coordination.py` and the Master suite can execute on the exact branch SHA.
6. **MASTER:** preserve this audit and continue coordination-only work; do not take over subsystem source branches.

## 7. Standing release gate

**PRODUCTION NO-GO.** No independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA approval, native acceptance, 150 real power cuts, 30-device/24-hour soak, or owner-authorized release gate is claimed complete. No merge, release, flash, secret provisioning, live payment, financial migration, device reset or physical test occurred.
