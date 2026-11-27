# PHX-MASTER UTC06 — Hardware #345 clear-window race, exact owner CI and Master index reconciliation

**Updated:** 2026-11-23T06:50:43.021Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Task:** #172 / #266  
**Branch:** phoenix/master-coordination  
**Starting HEAD:** 98bd48df64759b0cd1ddafc9fc77ad9fc66bf136  
**Base:** main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b  
**Disposition:** coordination-only; PR #288 remains OPEN / DRAFT / UNMERGED; COE #26 remains FROZEN; PRODUCTION NO-GO.

## 1. Live source and control-plane refs

- Experiments default branch: `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Experiments development branch: `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Master branch at write preflight: `phoenix/master-coordination@98bd48df64759b0cd1ddafc9fc77ad9fc66bf136`; the branch was re-read immediately before the atomic Git tree/commit/ref update.
- Master PR #288: OPEN / DRAFT / UNMERGED, base main@f4e8a891..., 183 starting changed paths; all were under `coordination/phoenix/`. Exact PR head matched the branch before write.
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- COE integration PR #26: OPEN / DRAFT / FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`, base COE main; five exact-head workflows QUEUED and zero jobs.
- Ownership manifest blob: `e4db324315a1b3543fec17a148fbf960170fcb29`; 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER target `null`.
- Root AGENTS.md blob: `d8777e3b58efc41caa5aa3c969c932aee9103d5f`; it requires private registry preflight before storage changes and prohibits publishing private Drive identifiers. Root README blob: `feb909e3f74ffb7b5b22df50399ccd127ada3b95`.
- README_FIRST and COMMUNICATION_PROTOCOL BLAZE-COMMS/1 were re-read. The protocol defines a single registered role recipient or literal `ALL`.

## 2. New Hardware #345 evidence — §6.69 post-clear ISR invariant

Current PR #345 is OPEN / DRAFT / UNMERGED at `e385a26fecd36e2696b5be1dcfcce601609614ff`, branch `phoenix/hw-coin-intake-armed-gate-20261122-utc23`, based on `phoenix/hw-esp8266-pin-recovery-20261122-utc16@dfeff7d5f63e699de7bc296c7641f2493f1e0e13`.

The current UTC06 source/test commit is `edff098446247d3b2851af643d31673921cae03f`; final PR/docs head is `e385a26f...`. The bounded test-only increment injects `coinEdgeISR()` while `clearPending()` is in progress, then verifies that the post-clear reconciliation observes the new edge, latches `journalRecoveryRequired`, writes the fake `/pollpulse.fault` marker with `pulses=1`, and leaves relay/ready outputs OFF. A mutation removing the second `reconcileUnobservedCoinEdges()` check is rejected with expected exit 54 on both extracted board sources.

The test compiles exact extracted production ISR, reconciliation, fault-latch, output and response-handler functions. Its positive disposition is a test-only stub override; production `coinPostDispositionVerified()` remains default-deny. The latest increment changed host-lab fixtures and handover documentation only; it did not modify production `.ino` files, shared APIs, CORE code or QA-owned files.

**Current final docs-head CI:**
- Quarantine [#45125188884](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45125188884): SUCCESS.
- Relay [#45125188887](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45125188887): SUCCESS.
- Full [#45125188863](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45125188863): FAILURE; validation job `137527796899` fails at `Controller protocol parity` / `Missing poll signature check` in the ESP8266 sketch. All 14 configured target/platform jobs pass; downstream simulation, update bundle, candidate, signing and publication stages are skipped.

Earlier exact source/test CI at `edff098...`: Quarantine [#45124661252](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45124661252) PASS; Relay [#45124661167](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45124661167) PASS; Full [#45124661259](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45124661259) FAIL at the same inherited assertion.

**Classification:** source-extracted host lab / CI only. This does not establish physical ISR timing, LittleFS crash durability, relay electrical acceptance, physical hardware acceptance, 150 power cuts or a 30-device/24-hour soak. PHX-HARDWARE owns implementation; PHX-QA owns independent fixture review and the stale assertion; PHX-CORE owns the authenticated producer contract; PHX-MASTER owns the cross-role invariant and assignment pointer only.

## 3. Current owner PR and CI matrix

| Owner | Current candidate | Exact-head CI / disposition |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) scoped Build PASS. CORE source remains separately owned. |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | APK identity [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) PASS; build [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAIL; API21/API23 smoke [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) Windows synthetic PASS; native COM/physical acceptance NOT TESTED. |
| HARDWARE #345 | `e385a26fecd36e2696b5be1dcfcce601609614ff` | Quarantine [#45125188884](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45125188884) PASS; Relay [#45125188887](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45125188887) PASS; Full [#45125188863](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45125188863) FAIL at inherited QA poll-signature assertion. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) Windows PASS. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No workflow runs; base is older Master commit `b1ca02e2087f3b1a7169ceab9c34e52646e700df`. Keep draft until QA runs unchanged tests against current verifier at an exact SHA. |
| RELEASE #291 | `886cabfc5080c3fbef03c2a3b1afe9d52dea6f60` | ESP32 compatibility [#45117006790](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45117006790): core 3.3.13 and provenance pass, core 4.0.0 archive verification fails. Windows [#45117006843](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45117006843) fails CORE-owned handover freshness. Full [#45117006794](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45117006794) fails mandatory handover freshness; 14 target jobs pass and downstream stages are skipped. |
| COE #35 | `adbb3894ac222ab615cd681ffe893163dc9214c2` | Sandbox [#45124298956](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45124298956): 39/39 host preflight tests pass, then fails closed because Bubblewrap is absent (exit 125). Shared [#45124298960](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45124298960): all 10 profiles fail closed without approved site-scoped ULA /48 authority; firmware compile jobs skipped. Case-collision [#45124298967](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45124298967) PASS. |
| COE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Shell suite [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case-collision [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS; scoped candidate only. |
| COE #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | Case-collision [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) and INTERCON [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) PASS; Hardware/Shared [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL. |
| COE #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows QUEUED / zero jobs. Remains FROZEN; no migration staging or destination write. |

CORE remains owned by the separate active production-development automation. PHX-MASTER did not modify CORE, RENTAL, PISONET, HARDWARE, QA, RELEASE source branches, or COE destination files.

## 4. Master cleanup audit — index duplicates corrected

A fresh complete recursive tree read at the starting Master head returned 2,525 entries, 183 files under `coordination/phoenix/`, and 98 `PHX_MASTER_*.md` reports. The existing `INDEX.md` contained 100 report-link occurrences but only 98 unique targets. Two historical reports were each linked twice:
- `PHX_MASTER_UTC17_20261121_EXACT_HEAD_ROLE_CI_COE26_SOURCE_MAIN_PROVENANCE_AUDIT.md`
- `PHX_MASTER_UTC20_20261121_EXACT_HEAD_ROLE_CI_COE26_MANIFEST_BASELINE_CANDIDATE_AUDIT.md`

All 98 report files were already indexed at least once; there were no dangling targets and no unindexed reports. UTC06 removes only the two duplicate link occurrences, preserves both historical files and their canonical earlier entries, and adds this report. Post-write static verification is recorded separately after remote readback.

The earlier UTC05 statement of 97/97 index coverage was not sufficiently precise: it did not catch these duplicate occurrences. This UTC06 audit corrects that count from the actual tree and link targets.

## 5. Governance, private registry and execution limits

- Cleanup issue #266 remains OPEN; the Master cleanup-first checkbox remains unchecked because the broader duplicate/dead-code inventory is incomplete.
- Branch metadata for Experiments main, `blazepwifi-v0.5.3-development`, Master branch, and COE main reports `protected=false` with required-check enforcement off. Ruleset lists for both repositories are empty. Repository administrators must configure and independently verify protected branches and required checks.
- Master PR #288 has zero Actions runs and zero combined statuses. Full Master unittest discovery and `verify_coordination.py` were NOT RUN.
- The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not surfaced by the authorized Library search. No Google Drive connector is exposed in this runtime. Older v3–v7 snapshots and a historical checkpoint summary are not substitutes. No private registry contents or identifiers are included here.
- No source migration was staged, copied, moved, overwritten, rebased or cherry-picked. COE #26 remains frozen.
- No secrets, signer, payment system, firmware, hardware or production environment was touched.

## 6. Next exact actions

1. PHX-QA: independently review Hardware #345's clear-window ISR fixture and resolve the inherited poll-signature assertion with source-linked evidence; do not synthesize `response_sig` or weaken default-deny.
2. PHX-CORE: refresh its owned shared handover and publish the canonical authenticated poll/receipt contract; PHX-RELEASE then reruns #291 freshness and ESP32 core 4.0.0 archive checks.
3. COE RELEASE/Infrastructure: provide the approved site-scoped ULA /48 authority and a runner with trusted Bubblewrap; do not bypass either fail-closed gate.
4. Repository administrators: enable branch protection and required checks for Experiments main/development/Master and COE main.
5. Registry custodian: restore authorized access to canonical v11 and newer corrections.
6. Human Master test runner: execute the full Master suite and `verify_coordination.py` at the resulting exact PR #288 HEAD.

**Production remains NO-GO:** independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native hardware acceptance, 150 real power cuts, 30-device/24-hour soak and explicit owner-authorized release gates remain mandatory.
