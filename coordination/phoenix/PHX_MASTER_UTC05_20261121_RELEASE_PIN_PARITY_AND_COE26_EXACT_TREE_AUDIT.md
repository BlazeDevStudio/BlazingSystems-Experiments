# PHX-MASTER UTC05 — exact role heads, Release ESP32 subtree parity, and COE #26 tree audit

**Audit time:** 2026-11-21T05:33:41Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, integration provenance  
**Execution:** strict NO CODEX; GitHub connector and ordinary GitHub Actions evidence only

## 1. Authority and exact repository snapshot

| Object | Exact identity | State |
|---|---|---|
| Experiments default branch | `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b` | current default |
| Experiments development branch | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` | current development |
| Master branch / PR #288 | `phoenix/master-coordination@0af23331efc66c6385586e03ca5cd2257a857cac` | OPEN / DRAFT / UNMERGED before this audit commit |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` | structure-only baseline |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | OPEN / DRAFT / FROZEN; 205 changed files |
| Cleanup issue #266 | current issue read | OPEN; 0/7 Master cleanup gate items checked |
| Routing manifest | `OWNERSHIP_ROUTES.json@e4db324315a1b3543fec17a148fbf960170fcb29` | `DRAFT_REVIEW_ONLY`; source ref main `f4e8...`; destination #26 `b382...`; PHX-MASTER target `null` |

The routing manifest was read from the live Master branch. It was not edited. It is not a copy/move authorization and does not pin the current Hardware PR #327 source/test tree.

The current Master PR had 146 changed paths at audit start; the complete changed-path listing showed every path under `coordination/phoenix/`. The PR base remains `main@f4e8...`.

## 2. Current role PRs and exact-head CI

| Owner / PR | Exact current head | Current evidence and disposition |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS, scoped. The separate **Blaze Production Continuation** retains CORE implementation; Master made no CORE source change. |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | APK identity [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) PASS; API21/API23 [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS; shared build [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAIL. The CORE-owned handover freshness gate fails; the ESP32 core 4.0.0 leg separately fails to find `mbedtls/sha256.h`. Rental retains its six Android-owned paths. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows run [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS, scoped. Physical USB-RS232/PnP/race acceptance remains NOT TESTED. |
| HARDWARE #327 | PR/docs head `bef313ef7d676bb52e91ee8b3aa8327297f8a8b7`; source/test `0f4cf65b33b0f0fa6bc1889b9f7b14025c610245`; base #326 `58c558fb6a237935214621adc3dee65a10fe1a51` | The current handover identifies source/test `0f4cf65...`; the two commits after it are documentation-only. Exact-source Quarantine [#44868064907](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44868064907) PASS and Relay/output [#44868064885](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44868064885) PASS. Full PR [#44868421623](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44868421623) FAILS at QA-owned `Missing poll signature check` in `experiment/openwrt/BlazePwifi/tests/controllers.sh`; all 14/14 firmware-target + Android build jobs passed, downstream import/update/simulation/sign/publish jobs were skipped. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | Windows run [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; native COM lab was not invoked. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96`; historical base `b1ca02e2087f3b1a7169ceab9c34e52646e700df` | No PR-triggered workflow runs. The old base is not current Master `0af233...`; QA must replay/rebase the unchanged recipient regression and run exact-head CI. Prior 4/4 source-linked checks are not current-head hosted CI. |
| RELEASE #291 | `f06ac4df2f61b9c39a03a6ff6009b32948b94778` | ESP32 compatibility [#44862405800](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44862405800) PASS 3/3; Full [#44862406950](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44862406950) FAIL at CORE-owned `PROJECT_HANDOVER.md` freshness; Windows [#44862405809](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44862405809) fails the same handover gate and skips build/publisher. |
| COE RELEASE #35 | `9a20f90b7abc9dced9f545733d59801d746bf088`; base #31 `59ed44d0b911e176f1a95b9cf5585ef811ffd31b` | Case-collision [#44870760313](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44870760313) PASS. Shared/profile [#44870760442](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44870760442) executes 122 host tests successfully, then fails all ten profiles because no approved site-scoped RFC 4193 ULA /48 is configured. Sandbox [#44870760338](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44870760338) fails closed with exit 125 because Bubblewrap is absent from the trusted runner. |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows remain QUEUED / zero jobs: case-collision, Windows, Hardware/shared, Rental, and Pisowifi. No candidate-head destination CI has executed. |

### Ownership boundaries

RELEASE #291 still has 26 changed paths: 21 RELEASE paths, three CORE-owned product handover/ledger/state files, and two PISONET-owned ReleaseSigning test files. PR membership does not transfer ownership. Master did not edit any of those paths.

## 3. RELEASE #291 compatibility pin — exact scope, not an overclaim

The current #291 workflow and test pin HARDWARE source commit `268ca9bde6d3710b418134ffd328060250fad42f` and ESP32 sketch blob `09c02d589ae15b0c8a4f2a3bbcdee20c41d2cb79`. The exact-head compatibility run [#44862405800](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44862405800) ran on RELEASE head `f06ac4df...`; both core jobs logged `PHX-HARDWARE-SOURCE-PASS` for that pinned source/blob.

Current HARDWARE #327 source/test is `0f4cf65b33b0f0fa6bc1889b9f7b14025c610245` (PR/docs head `bef313ef...`). A recursive Git-tree comparison of the entire ESP32 sketch directory at old pin `268ca9...` versus current source/test `0f4cf65...` found **15/15 files with identical blob SHAs**, zero divergent, zero source-only and zero destination-only. Both trees were complete and untruncated. The exact ESP32 sketch blob remains `09c02d...`.

Therefore the 3/3 compatibility pass remains valid for the **exact ESP32 compile directory** now present in #327. It is not proof that the entire Hardware branch is the same, does not qualify the ESP8266 target, and is not physical acceptance. RELEASE may update the source/test pin to current `0f4cf65...` for full branch provenance, or explicitly record the 15/15 subtree identity; Master does not edit RELEASE-owned workflow/test/handover paths.

## 4. COE #26 — complete exact-tree and provenance comparison

Exact source: Experiments HARDWARE #327 source/test `0f4cf65b33b0f0fa6bc1889b9f7b14025c610245`, tree `822b3238725caf43225795cdda5b5976e4dea0ec`.  
Exact destination: COE PR #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`, tree `8a7d4cf81d7227118b876c1138dd2da12345fefa`.

Both recursive trees were complete (`truncated=false`): source 2,461 entries / 1,882 blobs; destination 286 entries / 207 blobs.

| Routed item | Current source blob | COE #26 destination blob | Result |
|---|---|---|---|
| ESP32 sketch | `09c02d589ae15b0c8a4f2a3bbcdee20c41d2cb79` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | DIFFERENT |
| ESP8266 sketch | `dbb289f8d2cb8eedd72742b45dfeb518a4a7afa5` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | DIFFERENT |
| Firmware hardening test | `41211b2c110ab409f6d9d1812ef12fda73b13211` at `tests/v05_firmware_hardening_test.sh` | `f921c56cecc19cab1989507b9b4ade1f45dac54e` at `Hardware/tests/test_firmware_hardening.sh` | DIFFERENT |
| Pisowifi root LICENSE | `1ee55b94183417be977ca287cd7391f9a6f7e721` | `1ee55b94183417be977ca287cd7391f9a6f7e721` | IDENTICAL |
| Repository root NOTICE | `f6d92cd21465312be5993631fe26977219be0fb9` | no root `NOTICE.md` | MISSING AT DESTINATION |

The current source tree contains **30 board-local Python lab/helper files** under the ESP32/ESP8266 trees; COE `Hardware/` contains **zero Python files**. Source has three scoped `phx-hardware-*.yml` workflows; COE has one generic `hardware-ci.yml`. The source and destination hardening tests are different identities, not imported source-exact tests. Hardware-specific license/NOTICE applicability remains unresolved; the matching Pisowifi LICENSE alone does not settle the Hardware subtree.

COE #26's PR description claims broad module unification and 95% software readiness, but the exact source/destination blobs, missing lab/workflow identities, missing root NOTICE, and zero destination jobs do not establish that readiness. Keep #26 FROZEN. Do not copy, move, overwrite, cherry-pick, rebase, stage, or promote any route.

## 5. Required owner actions and release gates

1. **PHX-QA:** replace the inherited positive poll-signature assertion only after CORE publishes the approved authenticated poll-response and event-bound receipt contract. Keep negative/default-deny tests; do not make Hardware firmware pass by weakening admission.
2. **PHX-CORE:** resolve its own canonical handover freshness and publish the authoritative register/poll/receipt contract. CORE remains with the separate Blaze Production Continuation owner.
3. **PHX-RELEASE:** review the current #327 source/test anchor `0f4cf65...` and the 15/15 ESP32 subtree parity; refresh its provenance anchor if required. Resolve its own workflow/handover without editing CORE/PISONET-owned paths.
4. **PHX-RENTAL / Hardware / Release owners:** resolve the inherited ESP32 core 4.0.0 Mbed TLS header incompatibility and stale handover without crossing ownership.
5. **COE site/network authority:** supply the real approved site-scoped ULA /48; do not invent one.
6. **COE runner owner:** provide Bubblewrap in the trusted runner image and verify unprivileged namespace behavior; no privileged install or unsandboxed fallback.
7. **Registry custodian:** restore authorized access to private Drive v11 and newer corrections. The exposed Library search returned older v3–v7 snapshots only; none was substituted.
8. **Repository administrator:** verify effective branch protection in GitHub Settings. The classic protection endpoint returned 403 for this integration and repository rulesets returned `[]`; effective protection remains UNKNOWN.

## 6. Execution limits and disposition

- Actual hosted CI runs and job logs are cited above. Git-tree/blob checks are source inspection, not tests.
- A local exact-head clone/test attempt failed because this runtime could not resolve `github.com`; the full Master Python suite was NOT RUN. Master has no exact-head Actions run verified.
- The private Google Drive registry v11 and newer corrections were not accessible through an exposed Drive connector; no private registry content or IDs were copied to GitHub.
- No physical hardware, electrical/COM acceptance, real power cuts, 30-device/24-hour soak, signer, financial migration, payment system, flash, release, or deployment was invoked.

**Disposition:** PHX-MASTER coordination update only. COE #26 remains FROZEN; PR #288 remains DRAFT / UNMERGED. Production remains **NO-GO** until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates all have independent evidence.
