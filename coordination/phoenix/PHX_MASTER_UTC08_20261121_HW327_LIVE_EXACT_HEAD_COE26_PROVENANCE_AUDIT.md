# PHX-MASTER UTC08 — live exact-head role CI and COE #26 provenance audit

**Updated:** 2026-11-21T08:47:14Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, migration provenance  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/master-coordination`  
**Parent at audit start:** `32711a3b2545b937267d15136e99008bdfa6b98d`  
**Base:** `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**Scope:** `coordination/phoenix/` only. Strict NO CODEX.

## Executive result

The audit refreshed exact role heads and hosted CI, reconciled the current Hardware #327 test-harness regression, verified that RELEASE #291's ESP32 compatibility pin now matches the current Hardware ESP32 compile subtree byte-for-byte, and re-compared the exact COE #26 source/destination trees. The existing ownership route manifest remains unchanged and destination `null`. PR #288 remains OPEN / DRAFT / UNMERGED; COE #26 remains FROZEN; PRODUCTION NO-GO.

## Exact branch and destination heads

| Ref | Exact SHA |
|---|---|
| Experiments default `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Active v0.6 development | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Legacy v0.5.3 development | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master parent before this audit | `32711a3b2545b937267d15136e99008bdfa6b98d` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

## Role-owned PR and CI reconciliation

| Owner / PR | Exact head | Verified CI and status |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Build #42698139210 PASS (scoped); CORE remains separately owned |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | APK identity #44782114384 PASS; API21/API23 #44782114393 PASS; shared build #44782114390 FAIL: mandatory handover freshness and `mbedtls/sha256.h` missing under ESP32 core 4.0.0 |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows #42462978704 PASS (scoped); native COM/PnP acceptance NOT TESTED |
| HARDWARE #327 | `a2d690b511524f8c710813fe4b4fc06cd52de3a8` | Quarantine #44886128587 PASS; Relay #44886128521 FAIL; Full #44886128556 FAIL |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | Windows #43633486963 PASS (scoped); native COM lab not invoked |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No PR-triggered CI; historical base stale |
| RELEASE #291 | `f685ec977704f2381027d96edf65a41ba0c3d458` | Compatibility #44885560847 PASS 3/3; Full #44885560885 FAIL at mandatory handover freshness; Windows #44885560811 FAIL at shared handover freshness; publisher skipped |
| COE RELEASE #35 | docs `d28271a35776543bf558c90e3a117957829ee61c`; source/test `d5a2d727727d7019cf3b4ad60503a4fb821d69d1` | #44879927378: 125 tests PASS / 2 intentional skips, then 10/10 profiles fail closed on missing approved ULA /48; case-collision #44879927411 PASS; sandbox #44879927380 fails closed because Bubblewrap is absent |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | 205 changed paths; five workflows queued, zero jobs |

### HARDWARE #327 exact failure analysis

Current source/test head `a2d690b...` moved the poll-response C++ fixture payloads into `poll_response_failclosed_lab_fixtures.py`. The runner now imports `MAIN` and `WINDOW_MAIN` from that module. The separate `poll_window_timeline_guard_lab.py` still reads only `poll_response_failclosed_lab.py` and asserts that the synchronous-poll marker exists in the runner. Relay run [#44886128521](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44886128521), job `136791689099`, therefore fails at “Check monotonic poll-window fixture timeline (child stack only)” with “missing synchronous-poll scenario”. This is a stale test-harness path assumption introduced by fixture extraction, not evidence of a production sketch defect. HARDWARE should update the guard to inspect the fixture module (or the runner plus fixture content) and rerun Relay.

Quarantine [#44886128587](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44886128587) passes. Full [#44886128556](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44886128556) fails the validation job at “Controller protocol parity” because the ESP8266 sketch lacks the QA-owned poll-signature check. All 15 target/platform jobs pass; import, browser/ESP/Orange Pi simulations, signing and publication are skipped. QA/CORE must resolve the authenticated poll/receipt contract and fixture; HARDWARE must preserve default-deny behavior. No Master source change was made.

## RELEASE #291 exact-source compatibility reconciliation

Current RELEASE #291 head `f685ec977704f2381027d96edf65a41ba0c3d458` pins Hardware source `5909e6238bc98f76075d910cf2fd09803cbdae99` and ESP32 sketch blob `7ffb7b534c7163678726902946a17b04992950a0`. The pinned source tree and current HARDWARE #327 head `a2d690b...` each contain 16 ESP32 subtree blobs, and all **16/16 are identical**. The current PR-head compatibility run [#44885560847](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44885560847) passes all three jobs: provenance, ESP32 core 4.0.0, and ESP32 core 3.3.13. The current ESP32 compile-input subtree is therefore byte-identical to the tested pin. This does not qualify ESP8266, the entire Hardware branch, COE migration, physical behavior, or production binaries.

The same RELEASE branch remains blocked: Full run [#44885560885](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44885560885) fails the mandatory CORE handover freshness gate; Windows run [#44885560811](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44885560811) fails the shared handover freshness gate. Windows build and all publication jobs are skipped. CORE owns the handover.

## COE #35 second-fsync coverage update

The prior Master request for an injected failure at the second, pre-cleanup directory fsync is now covered by COE #35 source/test commit `d5a2d727727d7019cf3b4ad60503a4fb821d69d1`, test `test_generated_wrapper_keeps_temporary_manifests_when_precleanup_directory_sync_fails`. Exact docs head is `d28271a35776543bf558c90e3a117957829ee61c`. Hosted run [#44879927378](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44879927378), job `136772755043`, reports **125 tests PASS / 2 intentional skips** and the new test passes. This closes the earlier unit-test coverage request only.

The same run fails all 10 profile admissions because no approved site-scoped RFC 4193 ULA /48 is supplied. Case-collision [#44879927411](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44879927411) passes. Mandatory sandbox [#44879927380](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44879927380), job `136772754810`, passes host preflight but fails closed because Bubblewrap is absent (exit 125); namespace and packaging tests are skipped. No privileged install or unsandboxed fallback is acceptable.

## COE #26 exact source/destination provenance

Recursive Git trees were fetched at exact commits and were not truncated:
- Source HARDWARE #327 tree `21389895661460cdce9e18360461aaffed432ac2`: 2,468 entries.
- Destination COE #26 tree `8a7d4cf81d7227118b876c1138dd2da12345fefa`: 286 entries.

| Subtree | Source | Destination | Identical | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|
| ESP32 | 16 | 1 | 0 | 1 | 15 | 0 |
| ESP8266 | 28 | 1 | 0 | 1 | 27 | 0 |
| QA tests | 47 | 19 | 1 | 3 | 43 | 15 |

- ESP32 sketch blobs: source `7ffb7b534c7163678726902946a17b04992950a0`; destination `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.
- ESP8266 sketch blobs: source `c2aa71963eaa0288721f0bb13cff771aaaabc42f`; destination `c8be98f72596681e36a3ad1f8939bf8046c96887`.
- QA: only `portal.sh` is byte-identical; `config.sh`, `integration.sh`, and `security.sh` diverge; 43 source tests have no destination counterpart and 15 destination tests have no source counterpart.
- Board-local Python labs: 27 source, zero destination.
- Hardware workflows: three source-scoped workflows versus one generic destination workflow.
- `experiment/openwrt/BlazePwifi/LICENSE` and `Pisowifi/LICENSE` match at blob `1ee55b94183417be977ca287cd7391f9a6f7e721`. Source root NOTICE exists at `f6d92cd21465312be5993631fe26977219be0fb9`; destination root NOTICE and Hardware-specific LICENSE/NOTICE are absent.

The route manifest remains `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, with PHX-MASTER destination `null`. Five COE #26 workflows remain queued with zero jobs. No destination staging, copy, move, overwrite, cherry-pick, rebase, or route promotion occurred.

## Master execution and access limits

- Container `git clone` attempted and failed: `Could not resolve host: github.com`; full Master Python suite NOT RUN.
- No Master Actions run exists for the Master head.
- GitHub API source/tree inspection and route/blob comparison completed; this is not a Master test-suite execution.
- Private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections remain BLOCKED: no Google Drive connector is exposed in the available tools; Library search surfaced older v3–v7 snapshots only. No substitute was used and no private registry data was published.
- Cleanup issue #266 remains OPEN, 0/7 checked. Experiments main and both development branches report `protected=false`; effective organization rulesets remain unverified.
- Routing manifest unchanged; no subsystem source or destination file changed.

## Exact next actions

1. **PHX-HARDWARE:** update `poll_window_timeline_guard_lab.py` to inspect the extracted fixture module and rerun exact-head Relay; keep the current poll default-deny.
2. **PHX-QA + PHX-CORE:** publish/review the authenticated poll/receipt contract and correct the positive poll-signature fixture only against that contract; rerun Full.
3. **PHX-CORE:** refresh the canonical handover so RELEASE #291 Full/Windows and RENTAL #328 freshness gates can be independently re-run.
4. **PHX-HARDWARE / PHX-RENTAL:** resolve ESP32 core 4.0.0 Mbed TLS header availability in the owning source/toolchain scope.
5. **Site/network authority:** provide the actual approved site-scoped ULA /48; do not invent one.
6. **Infrastructure:** provide a trusted disposable runner with pre-provisioned Bubblewrap and working unprivileged namespaces.
7. **PHX-QA:** replay #292 on current Master and complete native COM/PnP acceptance under an authorized lab plan.
8. **Registry custodian / repository admin:** restore authorized v11 registry access and verify effective branch protection.
9. **COE integration owner:** keep #26 frozen until exact source blobs, license/NOTICE scope, imports, test identities, and destination CI are accepted.

**Disposition:** PR #288 OPEN / DRAFT / UNMERGED. COE #26 FROZEN. No merge, release, signing, flash, secret provisioning, real-payment operation, physical test, or production migration. **PRODUCTION NO-GO** until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates are evidenced.
