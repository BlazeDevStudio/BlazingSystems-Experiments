# PHX-MASTER — UTC12 live exact-head, role-CI, COE #26 provenance and cleanup audit

**Timestamp:** 2026-11-21T12:38:02Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, ownership routing and cross-repository integration provenance only.  
**Execution:** Strict NO CODEX. No Codex app, CLI, API, agent, workflow or delegation.  
**Disposition:** Draft review only; production NO-GO.

## 1. Exact live repository and PR identities

| Ref | Exact identity at audit start |
|---|---|
| Experiments `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments active v0.6 development | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Experiments Master | `phoenix/master-coordination@2afd58e153cbdff22f3a78a4ae4fdca5cdcc6348` |
| Master PR #288 | OPEN / DRAFT / UNMERGED; head `2afd58e...`; base `main@f4e8a891...`; 151 changed paths, all under `coordination/phoenix/` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | OPEN / DRAFT / UNMERGED; head `b382d233ff06c8791b1028bed3c617cc7b670d12`; base `main@a6513ab...`; 205 changed paths |
| Routing manifest | `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29`; 11 routes; `DRAFT_REVIEW_ONLY`; source ref main; destination candidate #26; PHX-MASTER target `null` |

The manifest's PHX-MASTER route remains coordination-only. No ownership or destination promotion was inferred from the existence of PR #26.

## 2. Live role PR and exact-head CI reconciliation

| Owner | Current PR / exact head | Exact CI evidence | Disposition / next owner action |
|---|---|---|---|
| CORE | Experiments #252 `c82705f2...`; separate COE contract candidate #45 `9d76a134...` | #252 build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; COE #45 scoped runs [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS | Separate CORE owner retains contract and financial-source work. #45 is a candidate, not Master-adopted or merged. |
| RENTAL | #328 `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | APK identity [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) PASS; API21/API23 [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS; shared build [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAIL | Handover freshness gate fails; ESP32 core 4.0.0 compile also fails because `mbedtls/sha256.h` is missing. RENTAL/CORE owners resolve their own source and handover dependencies. |
| PISONET | #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS | Scoped CI only; native COM/PnP physical acceptance is not established. |
| QA | #290 `5c29d15994cee1279058f1eca12f2a3180704292`; #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; #292 has no PR-triggered runs | #292 base SHA `b1ca02e...` is behind current Master `2afd58e...`; QA owns any rebase/replay decision. |
| HARDWARE | #327 `827fa75fa4e56ff3033076cc2f9b7ebb0cddf1a8`; #333 `e93d178bbe3fcf6a7ba7f3a049f996de10727750` | #327 Quarantine [#44887858993](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44887858993) and Relay [#44887859017](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44887859017) PASS; Full [#44887859147](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44887859147) FAIL. #333 Quarantine [#44901170202](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44901170202) PASS; Full [#44901170215](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44901170215) FAIL | Both Full failures reach QA-owned Controller protocol parity and report `Missing poll signature check`. #333's 14 target/platform jobs pass; downstream import/simulation/sign/publish jobs are skipped. The #333 fixture extraction preserves six payloads byte-for-byte and changes no production sketch. |
| RELEASE | #291 `42797e2f3d65c30a1070caf49c93aebec149d897` | ESP32 compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) PASS 3/3 for its immutable pin; Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) and Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) FAIL at handover freshness | The 26-path diff contains 21 Release paths, 3 CORE handover paths and 2 Pisonet test paths. Windows log identifies `.github/workflows/blazepisonet-softtimer-release.yml` as newer than the last `PROJECT_HANDOVER.md` checkpoint `adcae814...`. Preserve each owner's path authority; refresh the canonical handover before rerunning. |
| COE RELEASE | #35 docs head `9d6fa64113243981efcc4b5c7af098a5c4bb94c8`; source/test head `e1934fcb42f493ac0929490884045d54ad3a035e` | Shared [#44903155982](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44903155982): 133 tests PASS / 2 intentional skips, then 10/10 profile admissions FAIL CLOSED for missing approved ULA /48. Sandbox [#44903155993](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44903155993): 18/18 host preflight tests PASS, then Bubblewrap absent / exit 125. Case-collision [#44903155996](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44903155996) PASS | New trusted-path checks reject symlink, setuid/setgid and group/world-writable Bubblewrap executables while accepting ordinary 0755. No actual namespace/ImageBuilder run occurred. Site authority and Infrastructure prerequisites remain open. |
| COE integration | #26 `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows remain QUEUED / zero jobs: [#43096752609](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609), [#43096752632](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632), [#43096752800](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800), [#43096752563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563), [#43096752557](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557) | FROZEN. Queued is not a pass and no destination acceptance is inferred. |

HARDWARE branch graph is not one linear candidate: #329 is a child of #327; #330 is a separate child of #327; #331 and #332 are children of #330; #333 is a child of #332. No rebase, merge or stack consolidation was performed.

## 3. COE #26 exact-tree, blob, license and test-identity comparison

All compared recursive Git trees were complete (`truncated=false`).

| Exact ref | Tree entries | Blobs |
|---|---:|---:|
| Experiments main `f4e8a891...` | 2,340 | 1,764 |
| Active v0.6 development `2fbd2475...` | 2,392 | 1,846 |
| HARDWARE #327 `827fa75...` | 2,469 | 1,890 |
| HARDWARE #333 `e93d178...` | 2,478 | 1,899 |
| COE main `a6513ab...` | 3 | 2 |
| COE #26 `b382d233...` | 286 | 207 |

The manifest source ref is Experiments main, while the current Hardware work exists on owner-scoped PR branches. Do not silently substitute a role PR head for the manifest source ref; any candidate route needs an explicit, reviewed source SHA.

Exact route comparison of HARDWARE #327 to COE #26:

| Route | Source files | Destination files | Same relative paths | Identical blobs | Divergent blobs | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|---:|
| ESP32 | 16 | 1 | 1 | 0 | 1 | 15 | 0 |
| ESP8266 | 28 | 1 | 1 | 0 | 1 | 27 | 0 |
| QA tests | 47 | 19 | 4 | 1 | 3 | 43 | 15 |

- ESP32 sketch source blob `7ffb7b534c7163678726902946a17b04992950a0` differs from destination `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.
- ESP8266 sketch source blob `c2aa71963eaa0288721f0bb13cff771aaaabc42f` differs from destination `c8be98f72596681e36a3ad1f8939bf8046c96887`.
- Board-local Python labs/helpers: 32 at #327 and 38 at #333; COE #26 Hardware has zero.
- Source has three scoped Hardware workflows; destination has one generic `hardware-ci.yml` for Hardware (plus its separate Pisowifi workflow).
- Source `experiment/openwrt/BlazePwifi/LICENSE` and destination `Pisowifi/LICENSE` are identical blob `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- Source root `NOTICE.md` blob `f6d92cd21465312be5993631fe26977219be0fb9` is absent from COE root. `Hardware/LICENSE` and `Hardware/NOTICE.md` are absent; Hardware-specific license/NOTICE applicability remains unresolved.
- The one matching QA test blob is `portal.sh`; three shared paths diverge; 43 source tests are not imported and 15 destination tests have no same-path source counterpart.

This is a provenance comparison, not staging approval. No copy, move, overwrite, cherry-pick, rebase, route promotion or destination modification occurred. COE #26 remains FROZEN.

## 4. Cleanup-first Master inventory

At pre-change Master head `2afd58e...`, `coordination/phoenix/` contains 151 files: 140 Markdown, 3 JSON and 8 Python; all 151 blob SHAs are unique, with zero duplicate-blob groups.

A level-2 heading audit of `ARCHITECTURE_CONTRACTS.md` found 68 top-level `## 6.x` headings and five duplicate top-level IDs:

- §6.9 — lines 278 and 404
- §6.10 — lines 305 and 413
- §6.11 — lines 317 and 426
- §6.25 — lines 542 and 572
- §6.38 — lines 782 and 794

Nested `###` subsections are excluded from this top-level collision count. The older UTC04/UTC11 collision list is superseded by this exact level-aware audit. No renumbering or deletion was performed because inbound links, citations and consumers have not been fully inventoried. Cleanup issue #266 remains OPEN / 0 of 7; the broader repository-wide duplicate/dead-code inventory is incomplete.

## 5. Static checks, access and execution boundaries

**Custom static integration assertions executed in this run: 7/7 PASS**
1. Master branch equals PR #288 head.
2. PR #288 base equals current Experiments main.
3. All current PR #288 paths are under `coordination/phoenix/`.
4. Routing manifest remains `DRAFT_REVIEW_ONLY`.
5. PHX-MASTER route target remains `null`.
6. Both compared migration trees are complete.
7. BlazePwifi/Pisowifi LICENSE blobs match exactly.

These are API/tree/manifest assertions, not the repository Python test suite. An ordinary `git ls-remote` attempt failed because `github.com` DNS could not resolve; the full Master Python suite was NOT RUN. PR #288 has no workflow runs at its current head.

Classic branch-protection read returned 403; repository rulesets returned an empty list. Effective organization-level protection remains UNKNOWN. Repository permissions do not prove branch protection.

The Experiments root `AGENTS.md` was read (blob `d8777e3b58efc41caa5aa3c969c932aee9103d5f`). Its linked cloud artifact policy and recovery handover could not be fetched from the referenced BlazingSystems repository paths. COE root `AGENTS.md` returned 404. No Drive artifact/folder was created.

The private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections remain BLOCKED: no Google Drive connector is exposed in the available tools, and Library search surfaced older v3–v7 snapshots plus a 2026-11-09 checkpoint that merely references v11. None was substituted; no private registry contents were published.

## 6. Exact next owner actions

1. PHX-CORE, under its separate owner, publishes the authenticated register/poll and event-bound receipt contract with golden vectors and refreshes the canonical project handover.
2. PHX-QA replaces the inherited positive `Missing poll signature check` fixture with source-linked default-deny assertions; positive vectors only after CORE's approved contract exists.
3. PHX-HARDWARE keeps #327/#329/#330/#331/#332/#333 owner-scoped and separate; reruns Full only after QA/CORE contract resolution.
4. PHX-RELEASE and PHX-RENTAL refresh their own exact handover/provenance evidence and rerun their exact heads; RENTAL separately resolves the ESP32 Mbed TLS 4.0.0 header failure.
5. Site/network authority supplies the actual approved site-scoped RFC 4193 ULA /48. PHX-INFRA supplies a trusted Bubblewrap-capable runner without privileged installation or fallback.
6. PHX-QA independently reviews COE #35 source/test head `e1934fcb...`.
7. Keep COE #26 frozen until exact source SHA, blob/mode, license/NOTICE scope, full test import, test identity and destination CI are independently accepted.
8. Repository administration verifies effective branch protection; the registry custodian restores authorized v11/newer-correction access.

**Safety:** no merge, release, signing, secret provisioning, firmware flash, real-payment operation, migration, physical test or approval occurred. PRODUCTION NO-GO remains until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently evidenced.
