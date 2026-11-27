# PHX-MASTER UTC15 — exact owner CI, route-mapped COE #26 provenance, and cleanup inventory

**Updated:** 2026-11-22T15:35:21Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, migration provenance only  
**Task:** PHX-MASTER-UTC15-EXACT-OWNER-CI-ROUTE-PROVENANCE-CLEANUP  
**Disposition:** MASTER COORDINATION VERIFIED · COE #26 FROZEN · MASTER TESTS NOT RUN · PRODUCTION NO-GO

## 1. Live repository refs and ownership

- Experiments default branch: `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Active v0.6 audit/development branch: `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- Legacy v0.5.3 development branch: `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- PHX-MASTER: `phoenix/master-coordination@63342787fc1e55a7a55289ef7bff5e8e36493c5e`; parent `b7c6bb66d5603447d06fb8559c61457ee587c372`; base `main@f4e8a891...`.
- Experiments PR #288: OPEN / DRAFT / UNMERGED; 170 changed paths, all under `coordination/phoenix/`; zero out-of-scope paths.
- COE default branch: `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- COE integration PR #26: OPEN / DRAFT / UNMERGED at `b382d233ff06c8791b1028bed3c617cc7b670d12`, base `main@a6513ab...`.
- Machine-readable routing manifest: `coordination/phoenix/OWNERSHIP_ROUTES.json@e4db324315a1b3543fec17a148fbf960170fcb29`, schema `phoenix/ownership-routes/v1`, 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER destination `null`.

The separate active `Blaze Production Continuation` retains CORE implementation ownership. PHX-MASTER inspected CORE evidence only; no CORE source branch, task or implementation was taken over.

## 2. Current owner PR heads and exact-head CI

| Owner / PR | Current exact head | Exact-head evidence and disposition |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | General build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; dedicated PHX-CORE-G authenticated-controller lab [#42698124709](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698124709) PASS. CORE remains separately owned. |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | APK identity [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) and API21/API23 smoke [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS; shared build [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAIL. RENTAL owns the Mbed TLS / handover repair. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) and source-linked native GUID COM lab [#42462975460](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462975460) PASS; physical adapter acceptance NOT TESTED. |
| HARDWARE #327 | `fadac4ed3bc837cf729753264b9427fa3fd312b9` | Relay [#45029852010](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029852010) and Quarantine [#45029851960](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029851960) PASS; aggregate build [#45029851959](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029851959) FAIL. |
| HARDWARE #339 | `b3e1558845ae2cd508e42d0d4722fdcd28293e32` | Quarantine [#44986635350](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44986635350) PASS; aggregate build [#44986635417](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44986635417) FAIL. |
| HARDWARE #340 | `20c5889fc4ceeb95ab0b05c7c11952704caff36b` | ESP32 Mbed TLS guard, ESP8266 core 3.1.2 compile, ESP32 core 3.3.13 compile, Quarantine, Relay and aggregate candidate build all PASS; see [#44983396262](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44983396262). Candidate remains deny-only; signing/publication skipped and physical acceptance NOT TESTED. |
| HARDWARE #341 | `a655d0b5c144535a3ad8e48009fc4498318ff5e3` | Quarantine [#45014156653](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45014156653) PASS; aggregate build [#45014156658](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45014156658) FAIL. |
| HARDWARE #342 | `047925b60a91c9fa1dee892e8765fc2867c28c68` | Quarantine [#45034960304](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45034960304) PASS. Aggregate build [#45034960308](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45034960308) FAILS at `Controller protocol parity`; 14 target/platform jobs completed PASS, while downstream simulation/candidate/signing/publication jobs were skipped. |
| QA #290 / #292 | `5c29d15994cee1279058f1eca12f2a3180704292` / `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS. #292 has no PR-triggered runs and retains stale base `b1ca02e...`; QA owns any rebase/retirement. |
| RELEASE #291 | `42797e2f3d65c30a1070caf49c93aebec149d897` | ESP32 compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) PASS; aggregate build [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) and Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) FAIL at inherited handover/build gates. |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Receipt contract golden vectors [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case guard [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS; contract-only, runtime DENY. |
| COE Stage 5.1 #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | Separate router-bridge candidate; prior isolated stage run PASS, shared ESP32 compatibility remains FAIL at the inherited Mbed TLS header. It does not change #26's firmware/test. |
| COE RELEASE #35 | `a8b95f815df7507f2191382de6688f9e969e5ae4` | Final case guard [#45037388556](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45037388556) PASS. Shared validation [#45037388567](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45037388567): 186 tests PASS / 2 intentional skips, then all ten appliance profiles fail closed at site-ULA admission. Sandbox [#45037388594](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45037388594): 33/33 host-preflight tests PASS; Bubblewrap unavailable, exit 125; mandatory sandbox steps skipped. |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Eight queued run entries across five unique workflow names; all eight job-list endpoints returned zero jobs. No integration CI acceptance exists. |

The #342 aggregate failure is a validation failure, not a target compilation failure. The inherited test source still explicitly requires legacy `response_sig`, `|register|` and `|poll|` strings. Current firmware/CORE contract separation must be preserved; QA owns the stale assertion. No fake positive poll signature is authorized.

## 3. Correct route-mapped source/destination provenance

The route manifest maps source prefixes to different COE destination prefixes. A raw same-path comparison is therefore insufficient. Both recursive trees were complete (`truncated=false`): HARDWARE candidate #342 = 2,478 entries / 1,899 blobs; COE #26 = 286 entries / 207 blobs.

| Manifest route | Source files | Destination files | Exact relative-path result |
|---|---:|---:|---|
| HARDWARE ESP32 → `Hardware/esp32/` | 16 | 1 | One same-path sketch, divergent blob; 15 source-only. |
| HARDWARE ESP8266 → `Hardware/esp8266/` | 28 | 1 | One same-path sketch, divergent blob; 27 source-only. |
| QA tests → `Pisowifi/tests/` | 47 | 19 | 4 mapped: 1 identical (`portal.sh`), 3 divergent (`config.sh`, `integration.sh`, `security.sh`); 43 source-only and 15 destination-only. |
| CORE library → `Pisowifi/openwrt/rootfs/usr/lib/blazepwifi/` | 15 | 20 | 15 mapped: 6 identical, 9 divergent; 5 destination-only. |
| PISONET → `Pisonet/SoftTimer/` | 32 | 47 | 24 mapped: 13 identical, 11 divergent; 8 source-only and 23 destination-only. |
| RENTAL standalone → `Rental/openwrt/` | 7 | 4 | One mapped `install.sh`, divergent; 6 source-only and 3 destination-only. |
| RENTAL Android → `Rental/android/` | 983 | 8 | Literal prefix mapping yields zero matches because source is nested under `BlazeRental/` while destination is flattened under `app/`; this is a path-map mismatch, NOT proof that 983 files are simply missing. Requires per-file provenance mapping. |

Additional exact test/license evidence:

- Source QA test `experiment/openwrt/BlazePwifi/tests/v05_firmware_hardening_test.sh` is blob `41211b2c110ab409f6d9d1812ef12fda73b13211`.
- COE Hardware test `Hardware/tests/test_firmware_hardening.sh` is blob `f921c56cecc19cab1989507b9b4ade1f45dac54e`; it is not the mapped `Pisowifi/tests/` target and is not byte-identical to the source test.
- Both test files still assert legacy `response_sig`, `|register|` and `|poll|` expectations. Their test identities and consumer assumptions must be reconciled by QA/owners before any migration.
- Source `experiment/openwrt/BlazePwifi/LICENSE` and destination `Pisowifi/LICENSE` are byte-identical at `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- Experiments root `NOTICE.md` exists at blob `f6d92cd21465312be5993631fe26977219be0fb9`; COE root NOTICE and Hardware-local LICENSE/NOTICE are absent from the #26 tree. The PisoWiFi LICENSE match does not by itself resolve Hardware-local notice/provenance scope.
- The manifest's broad Rental Android route is selective-review, not a path-preserving copy plan; its source/destination layouts need a separate file-level map.

**Migration decision: NO MIGRATION.** No route promotion, staging, copy, move, overwrite, cherry-pick, rebase, retarget, COE destination edit or integration proposal occurred. Keep #26 FROZEN.

## 4. Master-owned cleanup inventory

At current Master HEAD:

- `coordination/phoenix/` contains 170 blobs; exact blob-SHA inventory found **zero byte-identical duplicate blobs** within that directory.
- There are 85 `PHX_MASTER_*.md` report files; 32 report filenames are not linked from the current `INDEX.md`. This is an index/archive review queue, not proof that those reports are dead or safe to delete.
- No report was deleted, renamed, moved or rewritten. Existing audit history is preserved.
- PR #288's 170 changed paths are all under `coordination/phoenix/`.
- Cleanup issue #266 remains OPEN, 0/7 tracks complete. The Master track is PARTIAL: the coordination subtree has an exact-blob inventory, but the wider repository duplicate/dead-code/overlapping-source inventory is not complete. Keep its checkbox open.

## 5. Execution and access limitations

- Exact GitHub refs, PR metadata, recursive trees, blobs and Actions run/job metadata were inspected remotely.
- A local `git ls-remote` attempt failed: `Could not resolve host: github.com`. Full Master unittest discovery, `verify_coordination.py`, `verify_migration_map.py` and `verify_source_intake_manifest.py` were NOT RUN.
- Remote subsystem Actions results above are CI evidence for their exact owner heads; they are not Master-suite execution.
- No Master PR-triggered Actions run or combined status was returned.
- Private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections remain inaccessible. Library search surfaced older v3–v7 snapshots and a 2026-11-09 checkpoint referencing v11 by filename, not the canonical v11 contents. No Google Drive connector is exposed in this session; no older snapshot was substituted and no private registry data/IDs were published.
- Effective branch-protection/ruleset state remains UNKNOWN.

## 6. Next owner actions

1. PHX-QA: correct the inherited positive poll-signature fixture with source-linked negative/default-deny tests; do not weaken firmware fail-closed behavior.
2. PHX-CORE: keep producer-contract implementation under its separate continuation; publish/maintain the canonical versioned controller-response contract and exact-head test evidence.
3. PHX-HARDWARE: preserve deny-only behavior and owner-controlled #342 lab work; no physical acceptance claim.
4. COE owner + subsystem owners: keep #26 frozen; produce a per-file route map for divergent/flattened paths, license/NOTICE decisions, test identity and exact-head CI before any destination staging.
5. Registry custodian: restore authorized private v11 and newer-correction access.
6. Human runner: restore authenticated GitHub network access and execute the full Master suite at the resulting exact head.
7. PHX-MASTER: continue the wider #266 duplicate/dead-code inventory and review the 32 unindexed historical reports without deleting them.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native hardware acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.

No subsystem source, COE destination, private registry, secret, signer, payment system or hardware device was modified or used. No merge, release, signing, secret provisioning, firmware flash, financial migration, physical test or production approval occurred.
