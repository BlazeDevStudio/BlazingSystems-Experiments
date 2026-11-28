# PHX-MASTER UTC12 — poll-fixture / producer boundary and live role CI

**Snapshot:** 2026-11-22T12:03Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/master-coordination`  
**Pre-update HEAD:** `72c04de5521eadc8e4741d9b5a7eb67a7b333e97`  
**Base:** `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**PR #288:** OPEN / DRAFT / UNMERGED; pre-update 167 changed paths, all under `coordination/phoenix/`.

## 1. Bounded task completed

Re-read the live control-plane issue #172, cleanup issue #266, Experiments main/development/v0.6 refs, Master PR #288 and routing manifest, current role PR heads and exact-head CI, COE main and frozen integration PR #26, repository AGENTS.md, Master coordination documents, Master directive, README_FIRST and BLAZE-COMMS/1. Rechecked the private Library for the canonical Drive registry and newer corrections. No subsystem source or destination branch was changed.

The highest-value delta since UTC11 is the live HARDWARE #327 head: `14339cb7a22c75d4bc80a8bc1eb5208ee86559e7`, a host-lab-only fix for inactive debounce callsite decoys. Focused Quarantine and Relay CI pass, but Full still fails at the inherited QA poll-signature assertion. The exact current source/test blobs explain why; see §2.

## 2. Exact poll-fixture / producer mismatch

| Artifact | Exact blob | Source-grounded finding |
|---|---|---|
| Experiments hardening test | `41211b2c110ab409f6d9d1812ef12fda73b13211` | Requires `response_sig`, `|register|`, and `|poll|` strings in both sketches and simulates the legacy SHA-256 `key|poll|...` tuple. |
| ESP8266 sketch | `c2aa71963eaa0288721f0bb13cff771aaaabc42f` | Retains register response authentication, has no legacy `|poll|` canonical string, and both `acceptPollResponse()` and `coinPostDispositionVerified()` return false. |
| ESP32 sketch | `7ffb7b534c7163678726902946a17b04992950a0` | Same default-deny behavior; no legacy poll tuple; both consumers return false. |
| CORE #252 Vendo CGI | `16eb4105c15569dfd77b19a276ee05a25768083e` | Uses nested `config_auth` via `bp_controller_lab_response_v1` for register/poll; separate member snapshot/mutation endpoints still use `response_sig`. |
| COE #26 Hardware test | `f921c56cecc19cab1989507b9b4ade1f45dac54e` | Still requires legacy `response_sig` and `|poll|` expectations. |

The Full #327 log at [run #45019896838](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45019896838) fails at `Controller protocol parity` with the exact message `Missing poll signature check` in the ESP8266 sketch. The inherited test's `grep -q '|poll|'` is the failing assertion. This is not evidence that a poll response should be accepted. The register/member `response_sig` is not poll authorization.

**Owner boundary:** QA owns the test assertion; CORE owns the producer contract; HARDWARE owns the consumer. Master records the mismatch only. Do not edit the QA test, CORE producer or Hardware source from this role, and do not weaken default-deny. QA should replace the stale positive poll assertion with source-linked negative/default-deny cases after CORE publishes the versioned producer schema and golden vectors. COE #26 stays frozen until owner-reviewed reimplementation and exact provenance/CI review.

## 3. Exact-head role CI

| Role / PR | Current head | Result |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [Build #42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; no dedicated response-auth workflow returned. |
| RENTAL #240 | `a7d113fb8ae3f0c5e838e64d31cae7a154e37b56` | Build #40910311159 and isolated auth instrumentation #40910311141 PASS. |
| RENTAL #287 | `a4fffd01c8fb1818c32a53522e0590c1dc8a77cd` | R281 entropy contract #43754089203 PASS. |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | Build #43653329229 and isolated auth instrumentation #43653329235 PASS. |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | APK identity #44782114384 and API21/API23 #44782114393 PASS; Full #44782114390 fails mandatory handover freshness and ESP32 compile. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows synthetic #42462978704 PASS; native COM acceptance NOT TESTED. |
| HARDWARE #327 | `14339cb7a22c75d4bc80a8bc1eb5208ee86559e7` | Quarantine #45019896729 and Relay #45019896769 PASS; Full #45019896838 FAIL at inherited `Missing poll signature check`. |
| HARDWARE #339 | `b3e1558845ae2cd508e42d0d4722fdcd28293e32` | Quarantine #44986635350 PASS; Full #44986635417 FAIL at same poll-signature assertion. |
| HARDWARE #340 | `20c5889fc4ceeb95ab0b05c7c11952704caff36b` | Six exact-head workflows including Full #44983396262 PASS; signing/publication skipped, physical acceptance NOT TESTED. |
| HARDWARE #341 | `a655d0b5c144535a3ad8e48009fc4498318ff5e3` | Quarantine #45014156653 PASS; Full #45014156658 FAIL at inherited poll-signature assertion. Separate child of #339. |
| QA #290 / #292 | `5c29d15994cee1279058f1eca12f2a3180704292` / `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 Windows #43633486963 PASS; #292 has zero PR-triggered runs and stale Master base. |
| RELEASE #291 | `42797e2f3d65c30a1070caf49c93aebec149d897` | Compatibility #44894604453 PASS; Full #44894604464 fails mandatory handover freshness; Windows #44894604466 fails shared handover freshness; publisher skipped. |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Golden-vector / POSIX+BusyBox suite #44295049727 and case guard #44295049903 PASS; contract-only, runtime-deny. |
| COE RELEASE #35 | `756e2aa159fdb76e838c5f8dd9c9925b7aeeeb32` | Case guard #45016923703 PASS. Shared #45016923699 runs 181 tests, then all ten profiles fail closed for missing approved site ULA /48. Sandbox #45016923701 runs 33 host tests, then Bubblewrap absence blocks with exit 125. |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | OPEN / DRAFT / FROZEN; five workflows QUEUED, zero jobs. |

## 4. Refs, ownership and migration

- Experiments main: `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Literal development branch: `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Separate v0.6 audit-foundation: `2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- COE main: `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- Routing manifest `OWNERSHIP_ROUTES.json`: blob `e4db324315a1b3543fec17a148fbf960170fcb29`, 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER destination `null`.
- COE #26 remains at `b382d233...`; no destination file was staged or edited. No copy, move, overwrite, rebase, cherry-pick, route promotion or merge occurred.

## 5. Tests and execution limits

- **15/15 bounded static source assertions PASS** against the exact test, sketch, CORE producer and COE destination blobs. These are source assertions, not product tests or compilation.
- Exact-head GitHub Actions results are linked above.
- Master PR #288 pre-update head `72c04de5521eadc8e4741d9b5a7eb67a7b333e97` has zero PR-triggered workflows and zero combined status checks. This is NOT RUN.
- Local `git ls-remote` was attempted; exit 128: `Could not resolve host: github.com`. No local checkout exists. The full Master unittest discovery and `verify_coordination.py` were NOT RUN.

## 6. Registry and cleanup blockers

- Canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections are not available in the Library; search surfaced only v3-v7 snapshots and a 2026-11-09 checkpoint. Older files were not substituted. No Google Drive connector is exposed. The public cloud artifact policy and recovery handover were read; no Drive readback/write, upload, folder creation or sharing change occurred.
- Cleanup issue #266 remains OPEN, 0/7. Master duplicate/dead-code inventory is incomplete; no mass move or deletion.
- The full control-plane checkpoint is deduplicated by role/hour: no PHX-MASTER UTC12 message existed before this update.

## 7. Disposition

PR #288 remains OPEN / DRAFT / UNMERGED. No subsystem source, COE destination, private registry, secret, signer, payment system or hardware device was changed or used. No merge, release, flash, financial migration, physical test or production approval occurred.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.

**Next:** QA owner updates the inherited poll-signature fixture to reflect the approved default-deny boundary after CORE publishes the versioned producer schema/golden vectors; Master reruns the exact-head matrix after owner checkpoints and registry/test access are restored.
