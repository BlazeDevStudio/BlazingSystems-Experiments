# PHX-MASTER UTC00 — exact-head role CI and COE #26 provenance audit

**Recorded:** 2026-11-28T00:38Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Task:** `PHX-MASTER-20261128T00Z-EXACT-HEAD-COE26-ROLE-CI`  
**Execution:** Strictly NO CODEX. Read-only source inspection plus coordination-only documentation changes. No subsystem source, destination staging, payment, signing, release or hardware action.

## 1. Live refs and Master branch integrity

| Ref | Exact HEAD |
|---|---|
| Experiments `main` (default) | `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5` |
| `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| `phoenix/master-coordination` (pre-change) | `9f6f6fe34395ecfbb82eecf0a989e434d4c8322a` |
| COE `main` (default) | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE PR #26 candidate | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

Experiments PR #288 is OPEN / DRAFT / UNMERGED, base `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`, with 263 changed paths, all under `coordination/phoenix/`. Comparing its pre-change head with live main gives 688 commits ahead / 1 behind; merge base remains `f4e8a891`. The only main-side commit is `6be5d19b` (`Create promp CallerID`, root path `promp CallerID`). Do not rebase or retarget this coordination branch as part of this task. The PR body had a stale first-line “Final Master head” (`79bd7a6f`) despite its later UTC23 section naming the actual `9f6f6fe`; the PR description is corrected in this run.

The current `OWNERSHIP_ROUTES.json` remains schema v1, 11 routes, `DRAFT_REVIEW_ONLY`; PHX-MASTER is `coordination/phoenix/` only with null runtime destination. Its source pin is historical, not a copy authorization. COE candidate PR #26 and its recorded candidate SHA still match. No route or owner changed.

## 2. Cleanup gate and role-owned PRs

Cleanup issue [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) remains OPEN with 0/7 accepted checkboxes. The broad Master duplicate/dead-code inventory is not complete; no cleanup gate is claimed complete.

| Owner | PR / exact head | Exact-head evidence and disposition |
|---|---|---|
| CORE | [#252](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/252) `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Scoped build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; not full production acceptance |
| RENTAL | [#289](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/289) `68928774d0d7cf65adb26bc6b54199a3159d066c` | Build [#43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) and native auth [#43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS |
| RENTAL | [#328](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/328) `10fc200b6dbf470a95e679d3acc58aff4ab2a67f` | API smoke, native auth and APK identity runs PASS; shared build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL: handover freshness validation and ESP32 compile. ESP32 log: missing `mbedtls/sha256.h`. |
| PISONET | [#255](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/255) `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows synthetic [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM device acceptance NOT TESTED |
| HARDWARE | [#367](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/367) `778220aa999d31da2c7d47074eed96377c04155a` | Focused [#46084788298](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46084788298) PASS; Mbed [#46084788312](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46084788312) PASS; Full [#46084788285](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46084788285) FAIL at QA-owned Controller protocol parity. All 14 firmware/Android target jobs pass; downstream simulation/sign/publish jobs are skipped. |
| HARDWARE | [#354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/354) `fc842342596786e072630179acfbbc4feeb2ba02` | Focused #45864684458 and Mbed #45864684325 PASS; Full #45864684497 and Native #45864684295 FAIL |
| HARDWARE | [#357](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/357) `963c37135797e0d570ef910596c098bb9d902779` | Focused #46067421658 and Mbed #46067421664 PASS; Full #46067421812 and Native #46067421738 FAIL |
| QA | [#290](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/290) `5c29d15994cee1279058f1eca12f2a3180704292` | Windows synthetic [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS |
| QA | [#292](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/292) `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No exact-head workflow run |
| RELEASE | [#291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/291) `bf339a76964a1abe2412fac45392fe06a8e66418`; [#242](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/242) `36c0d0bb3e58786359555b307bb784f720f023ce` | No exact-head workflow runs/statuses; #242 mergeable=false |
| MASTER | [#288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) | No exact-head Master Actions run or combined status |

### HARDWARE #367 handover freshness

The current #367 PR body still names older docs/source pins (`3f1f7424` / `183650be`) rather than the live PR head `778220aa` and current source/test identity `1922dcba`. The branch's current `PROJECT_HANDOVER.md` and `CURRENT_STATE.md` top blocks still describe `f7abed43` and an in-progress Mbed/Full state, while the current-head Full run is now terminal FAIL. HARDWARE must refresh its own PR description and canonical handover; MASTER did not edit the Hardware branch.

The Full failure is step “Controller protocol parity”. The current deny-only candidate intentionally omits unauthenticated `config_revision`; QA's existing assertion still requires it. QA must replace token-presence parity with source-linked deny-only vectors. Do not add a placeholder field or weaken fail-closed behavior.

## 3. P0 #177 — current source still polls before first coin sample

The live v0.6 development branch remains `2fbd2475e9f54878c316fa7cea2f228386b0e859`.

| Board | Current source blob | Blocking poll | First coin sample |
|---|---|---:|---:|
| ESP8266 | `12c4bb82b6fddafe813674a0b5f692c1d3634073` | line 354 | line 357 |
| ESP32 | `29f1125d52ff474a0d028ad41f7af201be1f0f9d` | line 314 | line 318 |

Both call synchronous `post("poll")` before the first `digitalRead(runCoinPin)`; the configured poll wait is 3,500 ms. Issue #177 remains OPEN. Current main CGI blob `2e3a1430d08cc6606429a042df3b5848f53c7267` has controller `register|ping` and `poll` blocks at lines 63 and 68 without controller `response_sig`; later member endpoint signatures do not authenticate those controller responses. CORE owns the authenticated controller contract, HARDWARE owns firmware, QA owns independent regression vectors. No source change was made.

## 4. COE #26 — exact pinned tree, current-main drift, tests and licenses

COE main is a three-entry scaffold (3 entries / 2 blobs). Draft PR #26 is OPEN / DRAFT / UNMERGED at `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12`. All five candidate workflows remain CANCELLED: [#43096752563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563), [#43096752800](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800), [#43096752557](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557), [#43096752609](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609), [#43096752632](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632).

All recursive trees were non-truncated:

| Tree | Entries | Blobs |
|---|---:|---:|
| Historical source pin `6d4c9b48` | 2,391 | 1,845 |
| Current Experiments main `6be5d19b` | 2,341 | 1,765 |
| COE #26 destination `b382d233` | 286 | 207 |

The pinned-source route comparison is path-mapped and requires manual review; it is not an approval to copy:

| Route | Source blobs | Destination blobs | Exact | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| CORE library | 20 | 20 | 14 | 6 | 0 | 0 |
| CORE CGI | 1 | 1 | 0 | 1 | 0 | 0 |
| RENTAL Android | 983 | 8 | 0 | 0 | 983 | 8 |
| PISONET | 44 | 47 | 16 | 9 | 19 | 22 |
| ESP32 | 3 | 1 | 0 | 1 | 2 | 0 |
| ESP8266 | 3 | 1 | 0 | 1 | 2 | 0 |
| QA tests | 149 | 19 | 2 | 2 | 145 | 15 |

The 61 SOURCE_INTAKE runtime rows were compared against the actual pinned source and destination trees by Git blob and mode: 61/61 source records match; 61/61 destination records match. Actual row classification is 46 byte-identical / 15 derived, but schema-8 SOURCE_INTAKE summary claims 47 / 14. The four original test rows match source/destination blobs and modes 4/4 (two identical, two derived).

All 15 derived-test destination blobs/modes match SOURCE_INTAKE; 11 are `NOT_RUN`, four `PENDING_CI_RUN`. MIGRATION_MAP has only 14 derived rows and is inconsistent in two blob IDs:
- Missing `tests/voucher_txn_journal.sh`.
- `tests/run_focus.sh`: manifest `2b7b861e...`, map `fa1f4f2c...`.
- `tests/member_txn_journal.sh`: manifest `d04df3c6...`, map `01dc9c65...`.

The manifest still pins destination branch `feature/pisowifi-cleanup-stabilization` and prior destination head `cf59b41e...`, not the live PR #26 branch/head. Current-main source comparison against the historical manifest pin finds 33/61 runtime blobs unchanged, 20 divergent and 8 absent; original tests are 2/4 unchanged. Do not silently replace the historical source pin: the COE integration owner must choose the intended baseline and reconcile it explicitly.

Ten source LICENSE/NOTICE artifacts were found in the pinned project/repository scope; four exact destination counterparts exist. Six destination counterparts are missing: root `NOTICE.md`; Android Launcher `LICENSE`; Android Launcher `assets/license.html`; tests/vendor/jsqr-1.4.0 `LICENSE`; UI vendor/qrcode `LICENSE`; UI vendor/tabler `LICENSE`. PisoWiFi's first-party LICENSE is exact.

The existing Master validators contain checks for the rootfs summary mismatch and derived-test map missing/extra/blob-mismatch conditions, but the repository test suite was not run in this environment. These live Git tree/blob/mode comparisons are read-only evidence, not CI or test-suite executions. No staging, copying, moving, overwriting, cherry-picking or migration occurred.

## 5. Registry, automation and execution limitations

The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not recovered. Library search surfaced older snapshots and a checkpoint reference, not canonical bytes. No Google Drive connector/action is exposed in this runtime. No private IDs or registry contents are copied into this public report.

The visible active automation inventory shows `Blaze Hourly Production Development` assigned PHX-HARDWARE. The exact named `Blaze Production Continuation` CORE automation was not surfaced. CORE was left untouched and no competing CORE worker/automation was created.

No local Git checkout exists in the execution container. Master Python tests, `verify_coordination.py`, and the committed migration-validator tests were NOT RUN. Master exact-head Actions and combined statuses remain absent. The in-memory tree/blob/mode audit above was executed against live GitHub API trees. Branch metadata reports the Experiments main and development refs as unprotected; visible rulesets list is empty, while the direct branch-protection endpoint returned 403, so repository-admin confirmation is still required.

## 6. Exact next owner actions

1. **PHX-QA:** replace the stale `config_revision` presence assertion with source-linked deny-only vectors; rerun Full at the exact #367 head after the owner handover refresh.
2. **PHX-HARDWARE:** refresh #367's PR body, `PROJECT_HANDOVER.md` and `CURRENT_STATE.md` to the actual current source/docs/PR heads; retain coin/relay deny.
3. **PHX-RENTAL:** fix the #328 ESP32 Mbed TLS include/toolchain mismatch and stale handover gate, then rerun Full on exact head.
4. **COE integration owner:** correct 46/15 summary counts, destination branch/head pins, missing voucher test row, two derived-test blob IDs, and six license/notice counterparts; select the source baseline before any staging.
5. **PHX-CORE + PHX-HARDWARE + PHX-QA:** publish and independently verify authenticated controller register/poll/receipt/disposition semantics; resolve P0 #177 without accepting an untrusted poll response.
6. **Registry custodian / repository admin:** restore authorized canonical registry v11 and newer corrections, expose the approved Drive connector and a non-Codex Master checkout/test path, and verify branch protection.

## 7. Release gate

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain unverified. No merge, release, signer operation, secret provisioning, hardware flash, physical test, real payment operation or financial migration occurred.
