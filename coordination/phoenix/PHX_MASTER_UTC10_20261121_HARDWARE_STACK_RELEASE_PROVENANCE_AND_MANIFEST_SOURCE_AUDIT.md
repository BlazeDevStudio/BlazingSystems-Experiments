# PHX-MASTER UTC10 — hardware stack, release provenance, and manifest-source audit

**Observed UTC:** 2026-11-21T10:23Z  
**Role:** PHX-MASTER — architecture, coordination, cross-repository provenance.  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/master-coordination`  
**Parent HEAD:** `783c97ce997b6bfd0706f4d11e1b97fff588140e`  
**PR:** [#288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288), OPEN / DRAFT / UNMERGED.  
**Execution:** Strict NO CODEX. No Codex app, CLI, API, agent, workflow, or delegation.

## 1. Live repository and control-plane refs

| Ref | Exact SHA | API branch protection |
|---|---|---|
| Experiments default `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` | `protected=false` |
| Experiments v0.5.3 development | `aad3aade72c1156eecba1fed30907c6d0283b2c5` | `protected=false` |
| Experiments v0.6.0 audit foundation | `2fbd2475e9f54878c316fa7cea2f228386b0e859` | `protected=false` |
| Master coordination | `783c97ce997b6bfd0706f4d11e1b97fff588140e` | `protected=false` |
| CoinOperatedEcosystem `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` | `protected=false` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | OPEN / DRAFT / FROZEN |

PR #288 is based on Experiments main `f4e8a891...`, with 150 changed paths at audit start, all under `coordination/phoenix/`. This update changes only Master-owned coordination documents and adds one report.

The control-plane issue is [#172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172). Cleanup gate [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) remains OPEN with 0/7 checkboxes complete. The Master cleanup checkbox stays unchecked: a complete duplicate/dead-code/canonical-module inventory has not been performed.

The live routing manifest `coordination/phoenix/OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`; source ref is Experiments main `f4e8a891...`, destination candidate is COE #26 `b382d233...`, and PHX-MASTER destination remains `null`.

## 2. Hardware ownership stack and current parallel drafts

The active Hardware lineage is:

`#322 → #323 → #326 → #327`

- #322: `50d93e0de3d682550b6f02fb43484e76ad9c7e08`
- #323: `988904e8bcd058b62a9fac4aa6319a9b7c5b2470`
- #326: `58c558fb6a237935214621adc3dee65a10fe1a51`
- #327: branch `phoenix/hardware-prepoll-edge-abort-20261119`, docs HEAD `827fa75fa4e56ff3033076cc2f9b7ebb0cddf1a8`, source/test anchor `3110a42886bb595e28ba7ddeac16a51c2b86bd1c`.

Two newer drafts are **siblings**, both based on #327 at the same parent SHA; neither is a child of the other:

| PR | Branch | Source/test SHA | Docs/current HEAD | Exact-head CI |
|---|---|---|---|---|
| [#329](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/329) | `phoenix/hardware-quarantine-parity-20261121` | `aaf1a0e7c8012873a3b86c69e3329ed06f1f3beb` | `29c7f61a6f28f48efa8fdeaec5aba8524bc7c213` | Quarantine [#44892233094](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44892233094) PASS; Relay [#44892233067](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44892233067) PASS; Full [#44892233150](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44892233150) FAIL at Controller protocol parity |
| [#330](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/330) | `phoenix/hardware-dual-store-fixture-modules-20261121` | `5133def2a358b6c3c0f0d18f31b9a483018a3a60` | `1a1e5e25834748fbba95d6253eb668f29b6c82f8` | Quarantine [#44893767890](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44893767890) PASS; Full [#44893767929](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44893767929) FAIL at Controller protocol parity |

#327 docs-head Quarantine [#44887859017](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44887859017) and Relay [#44887858993](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44887858993) PASS; Full [#44887859147](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44887859147) FAIL at Controller protocol parity. The #327 source/test focused runs [#44887543799](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44887543799) and [#44887543780](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44887543780) PASS.

The three Full failures are QA/CORE contract blockers; all 14 target/platform jobs in each captured Full run completed successfully, while downstream simulation, update, import, signing and publication jobs were skipped. This is source-extracted lab/hosted CI evidence only, not physical acceptance.

Separate open Hardware drafts #239, #254 and #283 are not part of the #322→#327 active stack. #254's focused header run [#44683629378](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629378) PASS, while Full [#44683629491](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629491) fails on ESP32 `mbedtls/sha256.h`. Hardware's #288 request reports #283 Full [#44219099256](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44219099256) PASS but identifies a separate source-level review gap: `quarantinePending()` has no active callsite and the current `sig` grep can match comments rather than an authenticated response producer/consumer. That owner-reported audit is not represented as Master-reexecuted test evidence.

No rebase, retarget, merge, branch rewrite, or ownership transfer was performed.

## 3. RELEASE #291 — current provenance regression

[RELEASE PR #291](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/291) is OPEN / DRAFT on `phoenix/release-publisher-isolation-20261115`, base #242 `734b89d9e7792247e8376335c3f3685500ab3f89`, current head `e2628dfedbd4220c7885c0b2b0e060b808ca25b0`.

Exact current-head runs:

- Full [#44892584693](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44892584693): CI-0701 provenance suite fails, 3 of 35 tests.
- ESP32 compatibility [#44892584579](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44892584579): both ESP32 core compile legs pass, but the provenance regression suite fails; this is not an overall compatibility qualification pass.
- Windows [#44892584643](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44892584643): fails at the shared handover freshness gate; build/publisher are skipped.

The three failing tests are:

1. `test_arduino_provenance_records_all_staged_compile_inputs_by_git_blob` — manifest omits exact source blobs for `experiment/openwrt/BlazePwifi/esp/REBUILD.md`, `esp/libraries/BlazePendingSequence/library.properties`, and `esp/libraries/BlazePendingSequence/src/v060_pending_sequence.h`.
2. `test_arduino_provenance_rejects_staged_library_tree_drift_before_manifest` — expected `ProvenanceError` is not raised.
3. `test_arduino_provenance_rejects_staged_sketch_tree_drift_before_manifest` — expected `ProvenanceError` is not raised.

The current 26-path #291 diff is 21 RELEASE paths, three CORE-owned handover paths (`PROJECT_HANDOVER.md`, `CHANGE_LEDGER.md`, `CURRENT_STATE.md`), and two PISONET-owned Windows test paths. The Windows log reports the shared `PROJECT_HANDOVER.md` is older than source/workflow changes; last recorded checkpoint is `adcae8141e673dc2147fcad50521ef3a23084d71`. These cross-owner paths remain with CORE/PISONET; Master did not edit them.

PHX-RELEASE already owns the UTC10 provenance task and posted [its active checkpoint #7061114867](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-7061114867). Master records the finding and does not duplicate the Release implementation or role lock.

## 4. Other live role PRs and CI

| Owner | Current PR/head | Evidence and boundary |
|---|---|---|
| CORE | [#252](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/252) `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Scoped build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS. CORE remains separately owned; no Master work or branch edits. |
| RENTAL | [#328](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/328) `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | APK contract [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) and API21/API23 smoke [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS; Full [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) fails handover freshness. |
| PISONET | [#255](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/255) `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows CI [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM/PnP acceptance remains NOT TESTED. |
| QA | [#290](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/290) `5c29d15994cee1279058f1eca12f2a3180704292`; [#292](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/292) `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 Windows scoped run [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS but does not invoke native COM acceptance; #292 has no PR-triggered workflow run. |
| COE RELEASE | [#35](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/35) `d28271a35776543bf558c90e3a117957829ee61c` | Packaging suite [#44879927378](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44879927378): 125 tests PASS / 2 skips, then all ten profiles fail closed because approved site ULA /48 is absent. Case collision [#44879927411](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44879927411) PASS. Sandbox [#44879927380](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44879927380) fails closed because Bubblewrap is unavailable (exit 125). |
| COE integration | [#26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows QUEUED / zero jobs. FROZEN; no destination CI acceptance. |

## 5. Exact migration provenance — manifest source vs destination

All three recursive trees were complete (`truncated=false`):

| Exact tree | Entries | Blobs |
|---|---:|---:|
| Manifest source Experiments main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` | 2,340 | 1,764 |
| Active Hardware #327 docs HEAD `827fa75fa4e56ff3033076cc2f9b7ebb0cddf1a8` | 2,469 | 1,890 |
| COE #26 destination `b382d233ff06c8791b1028bed3c617cc7b670d12` | 286 | 207 |

The manifest's source ref is **main**, not the active Hardware PR #327 branch. Those are different source trees; #327 must not be silently treated as already imported or as the manifest's source SHA.

### Manifest-pinned source main → COE #26

| Route | Source | Destination | Identical | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| ESP32 | 3 | 1 | 0 | 1 | 2 | 0 |
| ESP8266 | 3 | 1 | 0 | 1 | 2 | 0 |
| QA tests | 38 | 19 | 1 | 3 | 34 | 15 |
| CORE library | 15 | 20 | 6 | 9 | 0 | 5 |
| Vendo CGI | 1 | 1 | 0 | 1 | 0 | 0 |
| Rental Android (selective review) | 983 | 8 | 0 | 0 | 983 | 8 |
| Rental server | 7 | 4 | 0 | 1 | 6 | 3 |
| Pisonet SoftTimer | 32 | 47 | 13 | 11 | 8 | 23 |

The Rental Android count is a path-set comparison, not an instruction to copy all 983 files; the route remains selective-review. The standalone-rental profile route remains manual mapping. Test identities and import completeness are not established by basename overlap.

### Active Hardware #327 branch → COE #26

- ESP32: 16 source / 1 destination; 0 identical, 1 divergent, 15 source-only.
- ESP8266: 28 source / 1 destination; 0 identical, 1 divergent, 27 source-only.
- QA: 47 source / 19 destination; 1 identical, 3 divergent, 43 source-only, 15 destination-only.
- Board-local Python labs: 32 in #327 (9 ESP32 + 23 ESP8266); zero in COE Hardware.
- Scoped PHX-HARDWARE workflows: three in #327; COE has one generic `hardware-ci.yml`.

### License and notice boundary

- Source `experiment/openwrt/BlazePwifi/LICENSE` and destination `Pisowifi/LICENSE` are byte-identical at `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- Source root `NOTICE.md` blob `f6d92cd21465312be5993631fe26977219be0fb9` is absent from COE #26.
- COE `Hardware/LICENSE` and `Hardware/NOTICE.md` are absent. The sibling Pisowifi MIT license does not establish Hardware subtree notice scope.

**Disposition:** COE #26 remains FROZEN. Keep `OWNERSHIP_ROUTES.json` unchanged at `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, PHX-MASTER destination `null`. No copy, move, overwrite, rebase, cherry-pick, staging, route promotion, or destination edit.

## 6. Access, tests, and governance limits

- The requested private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections did not surface through the authorized Library search/list. Only older v3–v7 Library snapshots appeared; none was substituted. No Google Drive connector is exposed in this run.
- AGENTS.md's linked cloud-policy and recovery-handover files could not be fetched from the linked GitHub repository; older Library copies are not treated as current authority.
- Full Master Python suite: NOT RUN. An ordinary `git ls-remote` attempt failed because the container could not resolve `github.com`. No Master workflow run exists for the inspected Master head.
- API branch metadata reports `protected=false` for Experiments main, both inspected development refs, Master coordination, and COE main. Organization rulesets were not independently verified.
- This report is GitHub API source/tree/CI inspection plus coordinator-side tree comparisons. Hosted CI results above are attributed to their exact run/commit; no Master repository test is claimed.
- No physical COM test, router/ESP flash, electrical acceptance, real power cut, or device soak was run.

## 7. Production disposition and next exact actions

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates remain mandatory.

1. PHX-HARDWARE preserves #322→#323→#326→#327 and treats #329/#330 as sibling drafts; no independent child merge.
2. PHX-QA/PHX-CORE resolve the authenticated poll/receipt contract and source-linked positive/negative tests without weakening default-deny.
3. PHX-RELEASE completes the current #291 sketch/library tree provenance fix and exact-head reruns; CORE/PISONET review only their own inherited paths.
4. PHX-RENTAL refreshes its owned handover after code changes.
5. COE integration owner supplies complete exact-source import/test/license/NOTICE provenance and terminal destination CI before #26 can be reconsidered.
6. Registry custodian restores authorized Drive v11/newer-correction access; repository administrator verifies effective branch protection/rulesets.
7. QA and hardware owners schedule native COM, real power-cut and 30-device/24-hour acceptance on approved equipment.

No merge, release, signing, secret provisioning, financial migration, hardware flash, or production operation was performed.
