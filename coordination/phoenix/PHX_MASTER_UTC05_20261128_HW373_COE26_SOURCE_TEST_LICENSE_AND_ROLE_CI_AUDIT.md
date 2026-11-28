# PHX-MASTER UTC05 — Hardware #373, COE #26 and cross-role exact-head audit

**Task:** `PHX-MASTER-20261128T05Z-HW373-COE26-EXACT-TEST-LICENSE-ROLE-CI`  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, cross-repo provenance and integration matrices only.  
**Audit-start:** `phoenix/master-coordination@2af334464185b0e8439a85812fbadf6d3ab79675`.  
**Policy:** Strict NO CODEX. All writes in this activation are restricted to `coordination/phoenix/`.

## 1. Live refs and governance

| Repository / ref | Exact HEAD |
|---|---|
| Experiments `main` | `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5` |
| Experiments `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Experiments `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master `phoenix/master-coordination` audit-start | `2af334464185b0e8439a85812fbadf6d3ab79675` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE #26 candidate | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

- Control-plane issue [#172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172) is OPEN. No Master UTC05 message ID existed at audit start; this activation posts one final checkpoint.
- Cleanup issue [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) remains OPEN, 0/7 accepted. No mass move, rename or deletion is authorized.
- Existing Master PR [#288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) remains OPEN / DRAFT / UNMERGED, base `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`. Master ownership remains `coordination/phoenix/` only.
- `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, 11 routes, `DRAFT_REVIEW_ONLY`; PHX-MASTER target remains null. No route was promoted.
- Branch endpoints report `protected=false` for Experiments main/development/v0.6 and COE main; rulesets lists are empty and classic branch-protection reads return 403. Effective enforcement is UNKNOWN; repository administration must verify it.

## 2. Current role-owned PRs and exact-head CI

| Owner / PR | Exact head | Current evidence |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; CORE left read-only to its separate owner. |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | Build [#43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) and native auth [#43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS. |
| RENTAL #328 | `10fc200b6dbf470a95e679d3acc58aff4ab2a67f` | APK [#45622918340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340), API [#45622918364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), native auth [#45622918551](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551) PASS; Build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows synthetic [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM NOT TESTED. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | Windows synthetic [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; not native COM acceptance. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No exact-head workflow run. |
| RELEASE #291 | `bf339a76964a1abe2412fac45392fe06a8e66418` | No exact-head workflow run. |
| RELEASE #242 | `36c0d0bb3e58786359555b307bb784f720f023ce` | No exact-head workflow run. |
| HARDWARE #373 | `7ed2a1e9bb84d00ae73909231e93939f0eb5d4a6` | Focused [#46111743260](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46111743260) PASS; Mbed [#46111743270](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46111743270) 3/3 PASS; Full [#46111743275](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46111743275) terminal FAIL at QA-owned validation job `140876618433`, `tests/controllers.sh:21`. |

HARDWARE #373 source/test commit is `8d33f53396a9357f4e2d2dd931e66ce2bfc91765`; it is a cleanup-first host-lab/template extraction stacked on #372. Full CI-0701 and handover freshness passed; all 14/14 target/platform jobs completed PASS, including Android job `140876618444`. The downstream simulation, update, signing and publication jobs were skipped. The PR body still says Android was in progress at its last poll; HARDWARE owns refreshing its PR body and existing handover in place. No production `.ino`, shared API, financial logic or COE path changed.

COE role drafts were also re-read at exact heads: #35 `bc57ba8ecc5245ce538c6770a45bb25e2b8b5ef3` — case-collision PASS, ImageBuilder FAIL (Bubblewrap unavailable), Hardware/Shared FAIL (approved ULA /48 missing); #45 `9d76a134c1f6512aa40c20ec4d247306a71a8cce` — overlay/shell and case-collision PASS; #49 `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` — Stage 5.1 and case-collision PASS, Hardware/Shared FAIL (`mbedtls/sha256.h` unavailable).

## 3. COE #26 exact source, test and license provenance

PR [#26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) remains OPEN / DRAFT / FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`. Recursive trees are complete and non-truncated: pinned Experiments source commit `6d4c9b487af4d768c4d7627654d119417fcc6e00` has 2,391 entries; the candidate has 286 entries; COE main has only 3 entries. All five #26 candidate workflows are CANCELLED: [#43096752563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563), [#43096752800](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800), [#43096752557](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557), [#43096752609](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609), [#43096752632](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632).

- `SOURCE_INTAKE.json` declares 61 runtime files. Exact source and destination Git blob SHA plus mode checks passed 61/61. Actual classification is 46 byte-identical / 15 derived; the manifest summary incorrectly reports 47 / 14.
- Four original test rows are present: `portal.sh` and `security.sh` byte-identical; `config.sh` and `integration.sh` derived. Fifteen additional derived tests are declared and all 15 destination blobs/modes match the intake. Eleven are `NOT_RUN`; four are `PENDING_CI_RUN`.
- `MIGRATION_MAP.md` contains 18 test rows (four original plus 14 derived), omitting `tests/voucher_txn_journal.sh`. Its `run_focus.sh` and `member_txn_journal.sh` hashes disagree with SOURCE_INTAKE and actual destination blobs; the latter match SOURCE_INTAKE, so the map is stale.
- The source `experiment/openwrt/BlazePwifi/tests/` subtree contains 149 blobs; candidate `Pisowifi/tests/` contains 19. This is not a one-to-one missing-file count: only four original tests and fifteen derived tests are explicitly mapped. A complete per-file test inventory is still absent, so full source test import completeness cannot be claimed.
- The pinned source tree contains 11 LICENSE/NOTICE/COPYING path artifacts; candidate contains four exact path counterparts. Seven are missing: Rental Launcher `LICENSE`, `MODULE_LICENSE_APACHE2`, `assets/license.html`; R281 rental QR license; jsqr vendor `LICENSE`; UI QRCode `LICENSE`; UI Tabler `LICENSE`.
- `SOURCE_INTAKE.json` pins destination branch `feature/pisowifi-cleanup-stabilization`, while live PR #26 uses `integration/ecosystem-nonproprietary-candidate-20261111`. `OWNERSHIP_ROUTES.json` source_ref `f4e8a891` also differs from SOURCE_INTAKE source commit `6d4c9b48`. These are unresolved provenance pins, not permission to rewrite the manifests.

**Disposition:** no staging, copying, moving, overwriting, cherry-picking or route promotion. The COE owner must reconcile the source/destination branch pins, runtime summary, missing map row, stale map hashes, test inventory and seven license paths before any proposed migration.

## 4. P0 #177 and production gates

Live v0.6 source re-read at `2fbd2475e9f54878c316fa7cea2f228386b0e859`: ESP8266 blob `12c4bb82b6fddafe813674a0b5f692c1d3634073` retains 3,500 ms timeout at line 263, synchronous `post("poll")` at line 354, first coin sample at line 357. ESP32 blob `29f1125d52ff474a0d028ad41f7af201be1f0f9d` retains 3,500 ms timeout at line 230, poll at line 314, first sample at line 318. P0 #177 remains OPEN; this is source inspection, not electrical acceptance.

Production remains NO-GO pending independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates.

## 5. Execution limitations and owner actions

- Executed: exact branch/PR/issue reads; complete source and destination recursive tree reads; 61/61 runtime blob/mode comparisons; test-map reconciliation; license path inventory; exact-head workflow/job reads.
- Not executed: Master Python suite and `verify_coordination.py`; no local non-Codex checkout/test environment was available. No Master workflow was triggered.
- Canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not recovered. Library search surfaced older v3-v7 snapshots and a separate checkpoint only; no Google Drive connector/action is exposed. No older registry was substituted, and no private content or IDs were published.
- QA owns replacing the obsolete literal `config_revision` assertion with source-linked deny-only vectors and rerunning Full CI on the exact successor SHA. HARDWARE owns refreshing #373's terminal PR/ledger state. CORE remains reserved to its separate owner; no competing CORE task was created.
- COE integration owner owns manifest/test/license/branch-pin reconciliation. Registry custodian owns authorized v11 recovery. Repository administrator owns effective branch-protection verification and a non-Codex Master test environment.

No subsystem source, COE destination, private record, secret, signer, release artifact, hardware device, payment system or customer data was changed or operated. No merge, release, signing, flash, physical test or financial migration occurred.