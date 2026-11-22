# PHX-MASTER UTC01 — Hardware candidate lineages, role CI and COE #26 provenance

**Updated:** 2026-11-22T01:56:13.205Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, migration provenance and integration matrix  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/master-coordination`  
**Audit-start HEAD:** `f4e375ffca2bd0a17160d1fd41ead7c50274cdab`  
**Base:** `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**PR:** [#288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) — OPEN / DRAFT / UNMERGED  
**Execution:** strict NO CODEX; no Codex app, CLI, API, agent or workflow.

## 1. Live control plane and branch refs

- [CONTROL PLANE #172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172) is OPEN. The last PHX-MASTER checkpoint before this run is UTC00; no PHX-MASTER UTC01 message ID existed at audit start.
- [Cleanup-first #266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) is OPEN, 0/7 tracks complete. MASTER coordination checkbox remains intentionally unchecked; broad duplicate/dead-code inventory is not complete.
- Experiments default `main`: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` (branch API reports `protected=false`).
- Literal v0.5.3 development branch `blazepwifi-v0.5.3-development`: `aad3aade72c1156eecba1fed30907c6d0283b2c5` (`protected=false`).
- Current v0.6 audit-foundation branch `blazepwifi-v0.6.0-audit-foundation`: `2fbd2475e9f54878c316fa7cea2f228386b0e859` (`protected=false`); there is no branch literally named `development`.
- Master branch at audit start: `f4e375ffca2bd0a17160d1fd41ead7c50274cdab`; PR #288 head matched the branch ref. Existing 160 changed paths were all under `coordination/phoenix/`, zero out-of-scope.
- COE default `main`: `a6513ab4412b4c014eee2863e45cbe32d06cb243` (`protected=false`). COE #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN / DRAFT, 205 changed files, five workflows QUEUED / zero jobs.

The root [AGENTS.md](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/blob/main/AGENTS.md) was re-read at blob `d8777e3b58efc41caa5aa3c969c932aee9103d5f`; root README at `feb909e3f74ffb7b5b22df50399ccd127ada3b95`. The Master prompt, README_FIRST and BLAZE-COMMS/1 protocol were also re-read. Master coordination docs were read at their audit-start blobs: ROLE_ASSIGNMENTS `621e41c6...`, INTEGRATION_MATRIX `58904619...`, AUDIT_SUMMARY `c37051e9...`, REPOSITORY_ROUTING `2f89f0e7...`, INDEX `259bedee...`.

## 2. Routing manifest and ownership

`coordination/phoenix/OWNERSHIP_ROUTES.json` remains unchanged at blob `e4db324315a1b3543fec17a148fbf960170fcb29`, schema `phoenix/ownership-routes/v1`, 11 routes, `DRAFT_REVIEW_ONLY`. PHX-MASTER owns `coordination/phoenix/` only; its target remains `null`. No route promotion or ownership transfer occurred.

## 3. Current owner PRs and CI

| Role | Exact owner head | Current exact evidence |
|---|---|---|
| CORE | Experiments #252 `c82705f2de865c89ab733b10efa84f26f56a5cc4`; COE #45 `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | #252 build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS. #45 overlay [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS. These are scoped checks, not financial acceptance. |
| RENTAL | Experiments #328 `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | APK identity [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) and API21/API23 smoke [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS; build [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAILS at missing `mbedtls/sha256.h` and stale handover freshness. |
| PISONET | Experiments #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows synthetic [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS. Native COM/PnP/real adapter acceptance NOT TESTED. |
| QA | #290 `5c29d15994cee1279058f1eca12f2a3180704292`; #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS but does not invoke `NativeComInterfaceHandleLab`; #292 has no PR-triggered runs and stale base `b1ca02e2087f3b1a7169ceab9c34e52646e700df`. |
| RELEASE | Experiments #291 `42797e2f3d65c30a1070caf49c93aebec149d897`; COE #35 `048c6d2f11ef9635c93f22caa3258a25e819a644` | #291 ESP32 compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) PASS; Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) and Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) FAIL on handover freshness. COE #35 case [#44971464630](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44971464630) PASS; shared [#44971464620](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44971464620) runs 169 tests PASS / 2 skips then all ten profiles fail closed for missing approved site-scoped ULA /48; sandbox [#44971464640](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44971464640) runs 31/31 host tests PASS then exits 125 because Bubblewrap is absent. |
| COE Stage 5 | #48 `8286548e395366f2332830025fed00ceebdfb24a`; #49 `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | #48 Stage [#44643670696](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44643670696) and case [#44643670679](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44643670679) PASS; shared [#44643670685](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44643670685) FAILS Mbed TLS header. #49 Stage [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAILS the same compile. |
| COE integration | #26 `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows QUEUED / zero jobs; FROZEN, no combined acceptance. |

## 4. Hardware candidate lineage reconciliation

### Primary poll/edge stack

The active Hardware chain is #327 → #329 → #335 → #336 → #337 → #338 → #339. PR #339 is OPEN / DRAFT / UNMERGED at final docs head `5777b4320e3b70ac8a2d3f9399383f9438d4a715`, base #338 `1a6a7cacf95722a78330d70de057e858143520f2`. Its current source/test commit is `041f48cc5ea4fdb621cc3dd141dc51d0136542d4`; the preceding test-only RED is `71440776079c3d26e433410334ffc8552a8bd5d0`.

The source/test correction teaches the C++ parity normalizer to recognize the `%:` digraph as a preprocessing directive only at a logical-line start, excluding `%:%:` token-paste. Test-first Quarantine [#44972530105](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44972530105) reproduced the expected RED. Exact-source Quarantine [#44972640271](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44972640271) passed: normalizer 20/20, ESP8266 and ESP32 pulse capture 17/17 each, plus existing journal/pending/readback/poll/boot-polarity mutation labs. Final docs-head Quarantine [#44972910501](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44972910501) is SUCCESS and logs retain `SIMULATED_ONLY=1` and physical acceptance flags = 0.

Final docs-head Full [#44972910569](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44972910569) is still in progress overall. Its validation job `137056371116` is terminal FAILURE at the inherited QA-owned `Missing poll signature check`; at readback, 12/14 target/platform jobs had passed and Android/Orange Pi One were still running. Downstream update/signing/publication gates are skipped. Do not invent `response_sig` or weaken default-deny.

### Separate pre-poll deny candidate

PR #340 is OPEN / DRAFT / UNMERGED at `b0d3688c92745b3d571fb659154bf7d09aa5c5db`, branch `phoenix/hardware-prepoll-intake-deny-20261122-utc01`, based on #283 `88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d`. It is **not** a child of #339 and is not a replacement for the #327→#339 pulse/edge-reconciliation implementation.

Both ESP32 and ESP8266 sketches add the existing `denyRemoteControl()` immediately before synchronous `post("poll")`, retaining the post-poll deny and leaving pending journal state untouched. Source commits: ESP8266 `35aded4e54f247466b7b01472a462a8f2af950eb`; ESP32 `1909037f121b0615fd0dcfcebdd8a004b436b959`; harness index correction `d2737e7d42228462c9d2e6f19af1ccef31f5583c`. Focused exact-source [#44971548956](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44971548956) PASS: both board source-extracted guards, 2/2 relay polarities per board, fail-open mutations rejected and pre-poll-order mutations rejected. Full [#44971548978](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44971548978) FAILS at ESP32 compile `mbedtls/sha256.h` missing; 13/14 platform jobs pass. This remains SIMULATED / CI VERIFIED only; no physical acceptance.

CORE still owns the authenticated register/poll/receipt contract; QA owns the positive/negative poll fixture. The pre-poll deny does not establish a signed response, financial admission, or credit.

## 5. Exact source-to-destination provenance

Recursive Git trees were read at exact refs; all four responses were complete (`truncated=false`): Experiments main 2,340 entries / 1,764 blobs; #339 2,479 / 1,900; #340 2,359 / 1,780; COE #26 286 / 207.

### Canonical main-to-COE #26 mapped routes

| Route | Source | Destination | Identical | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| CORE runtime | 15 | 20 | 6 | 9 | 0 | 5 |
| CORE CGI | 1 | 1 | 0 | 1 | 0 | 0 |
| RENTAL Android | 983 | 8 | 0 | 0 | 983 | 8 |
| RENTAL server | 7 | 4 | 0 | 1 | 6 | 3 |
| PISONET | 32 | 47 | 13 | 11 | 8 | 23 |
| HARDWARE ESP32 | 3 | 1 | 0 | 1 | 2 | 0 |
| HARDWARE ESP8266 | 3 | 1 | 0 | 1 | 2 | 0 |
| QA tests | 38 | 19 | 1 | 3 | 34 | 15 |
| RELEASE workflow | 1 | 1 | 0 | 1 | 0 | 0 |

RENTAL standalone remains `manual-file-mapping-required` and was not treated as copy-safe.

### Current Hardware candidate vs COE #26

| Candidate | Route | Source | Destination | Identical | Divergent | Source-only |
|---|---|---:|---:|---:|---:|---:|
| #339 | ESP32 | 18 | 1 | 0 | 1 | 17 |
| #339 | ESP8266 | 30 | 1 | 0 | 1 | 29 |
| #340 | ESP32 | 8 | 1 | 0 | 1 | 7 |
| #340 | ESP8266 | 4 | 1 | 0 | 1 | 3 |

Exact sketch blobs (source main / #339 / #340 / COE #26):
- ESP32: `117c6e937e8f12f3890ace2ae23b3a23ff1c3df0` / `53b27aa80fa4a91aabac71de57f550a8eef2cb61` / `b102a79656690fbd49d7268092ab1980579c1cfd` / `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.
- ESP8266: `bfb94920eb0a189ca01d52e5443954fa133f5423` / `71160ac8ebd5163b19a56d6c9e229a5429975fc8` / `fdd4e45b2346957ce5f55ae529734854e4c78c7f` / `c8be98f72596681e36a3ad1f8939bf8046c96887`.

The #339 normalizer lab blob `ef4da32716411e8e556e0b0c3df0df4fedf9aca8` and #340 pre-poll lab blob `56452f06bd0c335de4ceedf4de063b358d3da3bb` have no COE #26 equivalent. QA tests remain 38 source / 19 destination, 1 identical, 3 divergent, 34 source-only, 15 destination-only.

License/notice evidence: source `experiment/openwrt/BlazePwifi/LICENSE` and COE `Pisowifi/LICENSE` match exactly at `1ee55b94183417be977ca287cd7391f9a6f7e721`. Source root `NOTICE.md` exists at `f6d92cd21465312be5993631fe26977219be0fb9`; COE root `NOTICE.md`, COE `Hardware/LICENSE` and `Hardware/NOTICE.md` are absent.

**Disposition:** COE #26 remains FROZEN. No staging, copy, move, cherry-pick, overwrite, rebase, destination edit or route promotion occurred.

## 6. Tests, access and branch protection

- Master-specific static audit: **13/13 assertions PASS** (branch/PR equality, PR scope, route manifest schema/ownership, #339/#340 ancestry separation, #26 review-only state, cleanup gate, checkpoint dedupe and current coordination-doc state).
- Recursive tree reads: **4/4 complete**, `truncated=false`; exact route/blob/license/test identity comparisons completed.
- Full Master coordination unittest suite: **NOT RUN**. Ordinary `git ls-remote` attempt failed before checkout with `Could not resolve host: github.com`; current Master commit has no PR-triggered workflow runs.
- Private Drive registry: exact Library search returned older v3–v7 snapshots and unrelated checkpoint files; requested `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not found. No Google Drive connector is exposed. No older registry was substituted; no private registry contents were published.
- Branch protection: Experiments main, v0.6 and v0.5.3 branch APIs report `protected=false`; COE main reports `protected=false`; effective Master branch protection remains UNKNOWN.

## 7. Next exact actions

1. PHX-MASTER: run the full coordination unittest suite from an authenticated checkout at the final commit produced by this report.
2. PHX-CORE / PHX-QA: publish the canonical authenticated register/poll response-signature and event-bound receipt contract; update the QA fixture only after independent contract review. Preserve default-deny.
3. PHX-RENTAL: resolve Mbed TLS header compatibility and refresh the canonical handover.
4. PHX-RELEASE / Infrastructure: refresh #291 handover; supply approved site-scoped ULA /48 authority and a trusted Bubblewrap-capable runner.
5. Repository administrator: provide effective branch-protection evidence.
6. Registry custodian: restore authorized private v11/newer-correction access.
7. COE integration owner: complete per-file provenance, license/NOTICE, test identity, import completeness and exact-head CI review before any migration proposal.

## 8. Safety decision

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain unverified. No merge, release, signer provisioning, secrets, firmware flash, real payment operation, physical test or customer deployment was performed.


## UTC01 CI completion correction — 2026-11-22T02:01:01.691Z

The final-docs-head HARDWARE #339 Full run [#44972910569](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44972910569) is now terminal **FAILURE**. Validation job `137056371116` fails at the inherited QA-owned `Missing poll signature check`. All **14/14 target/platform jobs completed SUCCESS** (ESP8266, ESP32, Android, Ruijie, x86_64 and Orange Pi variants). Browser/device simulations, candidate gate, update bundle, signing handoff and publication were skipped after validation failure. This supersedes the earlier readback note that 12/14 targets had completed and two remained in progress. Final-docs-head Quarantine [#44972910501](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44972910501) remains SUCCESS. No positive response signature was invented and default-deny was not weakened.
