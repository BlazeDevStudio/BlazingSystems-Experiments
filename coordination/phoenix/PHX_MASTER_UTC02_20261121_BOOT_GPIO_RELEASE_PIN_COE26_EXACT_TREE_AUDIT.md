# PHX-MASTER UTC02 — 2026-11-21T02:41Z
## Live role, CI, boot-order and COE destination audit

**Role:** PHX-MASTER — coordination, architecture/interface contracts, migration provenance and integration gates only.  
**Execution:** Strict NO CODEX. No Codex application, CLI, API, agent, workflow or delegation.

## 1. Exact refs re-read

| Ref | Exact value | State |
|---|---|---|
| Experiments default `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` | Read |
| Experiments active development `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` | Read |
| Master branch at audit start | `fcb3f1d5ad6d9dbe0c9e8431910277fc97693b03` | Read |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` | Read |
| Experiments PR #288 | `fcb3f1d5ad6d9dbe0c9e8431910277fc97693b03` | OPEN / DRAFT / UNMERGED |
| COE PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | OPEN / DRAFT / FROZEN |
| Cleanup issue #266 | OPEN | 0/7 complete |
| Ownership route manifest | `e4db324315a1b3543fec17a148fbf960170fcb29` | DRAFT_REVIEW_ONLY; PHX-MASTER target null |

PR #288 was at 143 changed paths, all under `coordination/phoenix/`. Its base is Experiments `main@f4e8a891...`. The current branch-filtered Actions query returned no Master run. Issue #172 was re-read; no PHX-MASTER UTC02 checkpoint existed at audit start.

## 2. HARDWARE #327 — new boot-order mitigation, still not accepted

- PR/docs head: `1db9855aadb1aeeab797c9e298a850546b66037f`.
- Exact source/test SHA: `2d10db5db8ad95f15abf335f25cbbbb2d02c7fae`.
- Firmware behavior commit: `ebadec9aaed3113c632a0776a2ac71238ecd0d13`.
- Base #326: `58c558fb6a237935214621adc3dee65a10fe1a51`.

After local configuration and the secondary EEPROM/NVS backup is initialized, both ESP8266 and ESP32 now preload relay/LED outputs OFF and attach the coin ISR before `initPendingStore()` mounts LittleFS. The source handover explicitly limits the claim: source order reduces the interval before firmware OFF preload; it does not prove physical relay state during reset or that a pulse was lost.

Exact PR-head hosted CI:
- [Quarantine #44854558168](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44854558168): SUCCESS.
- [Relay/output #44854558206](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44854558206): SUCCESS.
- [Full #44854558160](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44854558160): FAILURE at QA-owned `Missing poll signature check` in controller protocol parity. The 14 firmware-target jobs and Android job passed; downstream simulations, signing and publication were skipped.

Classification remains SIMULATED / FOCUSED-CI-VERIFIED only. No physical relay, electrical, coin-ingress, 150-power-cut or 30-device/24-hour acceptance is established. Keep poll/coin admission deny-only.

## 3. RELEASE #291 — exact current Hardware source compatibility is now qualified

- PR head: `b1a0743d0c211571f6dc7511393ef0f85c18896b`.
- Base #242: `734b89d9e7792247e8376335c3f3685500ab3f89`.
- Current diff: 26 paths — 21 RELEASE, 3 CORE handover/ledger/state, 2 PISONET release-test paths. PR membership does not transfer ownership.

[Compatibility #44855121706](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44855121706) completed 3/3 successfully. It checked out exact HARDWARE source/test `2d10db5...`, verified the current ESP32 sketch blob `142e1ac098aef2844f7d553771720871ee51d5e9`, and completed both ESP32 core 3.3.13 and 4.0.0 reproducibility jobs plus the release provenance suite. This qualifies that exact source/blob and toolchain matrix only; it is not physical acceptance or release approval.

Two separate blockers remain:
- [Full/Windows run #44855121644](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44855121644) fails at the shared handover freshness gate. It identifies `.github/workflows/blazepisonet-softtimer-release.yml` newer than `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md`; last recorded checkpoint is `adcae8141e673dc2147fcad50521ef3a23084d71`. Windows build and publisher were skipped.
- [CI-0701 run #44855121676](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44855121676) fails at `PHX-RELEASE-HANDOVER-ANCHOR-RED`: the release handover must record one exact-source 3/3 compatibility Actions run. The successful run #44855121706 arrived after the current handover anchor. The Release owner should update its own handover and rerun the guard; Master will not edit Release files.

## 4. Other live role boundaries

| Role | Live ref | Current evidence / next owner |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Separate Blaze Production Continuation owns CORE implementation; no competing work started. |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070`, base #289 `68928774...` | APK identity and API21/API23 checks PASS; last shared build #44782114390 FAIL at CORE handover freshness and inherited ESP32 core-4.0.0 `mbedtls/sha256.h` absence. Rental retains Android paths. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Scoped Windows evidence exists; physical USB-RS232/PnP/race acceptance remains NOT TESTED. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | Scoped Windows result only; native COM lab was not invoked. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96`, historical base `b1ca02e...` | No PR-triggered CI. QA must replay/rebase its unchanged recipient regression on current Master and run exact-head CI. |
| HARDWARE #254 / #283 / #318 | `84c442a...` / `830c355...` / `de428b7...` | Separate open candidates, not a substitute for #327 or a merged canonical stack. |
| COE RELEASE #35 | `580855b6a45a6d3cf506a6aa9320bc4782efc246` | Prior exact runs: 120 packaging/tool tests PASS / 2 skipped; profile admission fails without approved site ULA /48; Bubblewrap sandbox unavailable; case guard PASS. |
| COE RELEASE #44 | `582fd5d5e83e36b36546ac28534740298ba94af4` | Shared/case checks PASS; sandbox remains blocked by missing Bubblewrap. |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Contract-vector work only; no financial acceptance. |
| COE INTERCON #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | Separate Stage 5.1 draft: bounded Stage 5.1/case runs PASS; shared ESP32 build fails on missing Mbed TLS header. No Hardware ownership route. |

## 5. COE #26 exact-tree and migration-provenance audit

Recursive Git trees were fetched at exact refs and both reported `truncated=false`:
- Source PR/docs tree #327 `1db9855...`: 2,457 entries.
- Source/test tree #327 `2d10db5...`: 2,456 entries. The intervening docs commit adds the single 81-line boot-order handover only.
- Destination candidate tree COE #26 `b382d233...`: 286 entries.
- COE main remains structure-only at `a6513ab...`.

| Routed subtree | Experiments source | COE #26 destination | Exact comparison |
|---|---:|---:|---|
| ESP32 | 16 | 1 | 0 identical; 1 divergent; 15 source-only |
| ESP8266 | 24 | 1 | 0 identical; 1 divergent; 23 source-only |
| QA tests | 47 | 19 | 1 identical; 3 divergent; 43 source-only; 15 destination-only |
| OpenWrt overlay | 54 | 62 | 25 identical; 28 divergent; 1 source-only; 9 destination-only |
| Rental Android | 983 | 8 | 0 identical; 983 source-only; 8 destination-only |
| Standalone rental | 31 | 19 | 2 divergent; 29 source-only; 17 destination-only |
| Rental server | 7 | 4 | 1 divergent; 6 source-only; 3 destination-only |

There are 28 board-local Python lab/helper files in the source ESP32/ESP8266 trees and zero under destination `Hardware/`. Source Hardware has three scoped workflows; destination has one generic workflow.

Exact current blobs:
- ESP32 sketch: source `142e1ac098aef2844f7d553771720871ee51d5e9`; destination `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.
- ESP8266 sketch: source `b515b0d00a445eb0c9843659fbbd8c667803b87f`; destination `c8be98f72596681e36a3ad1f8939bf8046c96887`.
- Hardening test: source `41211b2c110ab409f6d9d1812ef12fda73b13211`; destination `f921c56cecc19cab1989507b9b4ade1f45dac54e`.

License/notice:
- BlazePwifi source LICENSE and COE `Pisowifi/LICENSE` are byte-identical: `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- Experiments root NOTICE exists at `f6d92cd21465312be5993631fe26977219be0fb9`; COE root NOTICE is absent.
- No Hardware-specific LICENSE/NOTICE was found at the checked board paths. Applicability remains unresolved; this is not a legal conclusion.

COE #26 remains OPEN / DRAFT / FROZEN, 205 changed paths, five workflow runs QUEUED / zero jobs. The route manifest remains `e4db324...`, `DRAFT_REVIEW_ONLY`, PHX-MASTER target `null`. No copy, move, overwrite, cherry-pick, rebase, staging, route promotion or destination edit occurred.

## 6. Governance, access and test limits

- Branch metadata reports `protected=false` for Experiments main/development/Master and COE main; the Experiments repository-level rulesets endpoint returned an empty list. Branch-protection detail endpoints return 403, so effective organization-level enforcement remains unverified.
- The private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not found in the exposed Library search. No Google Drive connector is exposed in this runtime. Older registry snapshots were not substituted; no private registry contents or identifiers were copied publicly.
- Local `git ls-remote` failed because this runtime cannot resolve `github.com`. Full Master Python suite was NOT RUN. Master-specific Actions runs at the audit-start head: none returned. Hosted worker CI links above are actual runs; GitHub tree/blob inspection is not represented as a test.
- No subsystem source, COE destination, secret, financial state, hardware device or release workflow was modified.

**Disposition:** PR #288 remains DRAFT / UNMERGED. COE #26 remains FROZEN. Project Phoenix remains **PRODUCTION NO-GO** pending independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates.
