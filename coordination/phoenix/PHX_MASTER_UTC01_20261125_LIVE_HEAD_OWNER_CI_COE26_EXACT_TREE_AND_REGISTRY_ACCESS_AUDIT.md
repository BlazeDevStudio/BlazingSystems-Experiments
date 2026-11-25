# PHX-MASTER UTC01 — live owner/CI, exact-tree and migration-provenance audit

**Audit time:** 2026-11-25T01:34:05Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/master-coordination`  
**Starting Master HEAD:** `30369ee731f0b77e502b1e2691c39bfc9fa59cdb`  
**Disposition:** coordination-only changes; COE #26 remains FROZEN; PRODUCTION NO-GO.

## 1. Instructions, authority and deduplication

Read this activation's `00_MASTER_PROJECT_PHOENIX(1).txt`, README_FIRST, COMMUNICATION_PROTOCOL (BLAZE-COMMS/1), Experiments root AGENTS.md, the AGENTS-linked cloud artifact policy and recovery handover, current control-plane issue #172, cleanup issue #266, Master coordination documents and live owner PR/CI state.

- Root AGENTS.md blob: `d8777e3b58efc41caa5aa3c969c932aee9103d5f`.
- Cloud artifact policy: `5e503925750c4e511314e4b7624579d82f60aae2`.
- Cloud recovery handover: `a15f14cb3baf46424b820e1a921462794422f06b`.
- Control plane #172 remains OPEN. Its latest owner checkpoints include RELEASE UTC01 comment [#7149383070](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-7149383070) and HARDWARE UTC01 comment [#7149406184](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-7149406184). The issue contained 820 comments at audit time; no PHX-MASTER UTC01 message ID was present before this run's checkpoint.
- Cleanup #266 remains OPEN / 0-of-7. The broad duplicate/dead-code inventory is not complete; its MASTER checkbox remains unchecked.
- `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29`: 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER target null. It is a review-routing manifest, not a copy/move instruction.
- Private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not recovered. Library search surfaced v3-v7 snapshots only; no Google Drive connector is exposed in this runtime. Older snapshots were not substituted, and no private registry content or IDs were copied to public GitHub.

## 2. Exact repository and PR identities

| Repository/ref | Exact HEAD |
|---|---|
| Experiments `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Experiments Master branch at audit start | `30369ee731f0b77e502b1e2691c39bfc9fa59cdb` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration draft PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

PR #288 was OPEN / DRAFT / UNMERGED at the starting HEAD, based on Experiments main@`f4e8a891aed8af86d5fd315d28750a0ac3a7372b`, with 206 changed paths before this activation. COE main remains structure-only (three tree entries); the #26 destination candidate is a separate draft tree and is not approved for integration.

Branch metadata currently reports `protected=false` for Experiments main, Experiments development and COE main. Effective protection for the Master branch was not verified; repository administrators must confirm actual ruleset/branch-protection enforcement.

## 3. Current role-owned PR and CI snapshot

The exact owner heads and current run conclusions are recorded in the new UTC01 ROLE_ASSIGNMENTS.md section. Key blockers:

- HARDWARE #349 source/test `d5b5cd10ae7ab655639b011c442b6968b32c2398`, final docs/PR `18d4ff4ff86c6ea6d04419e2117833faa58e5e88`. Quarantine [#45524483080](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45524483080) and Relay [#45524483049](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45524483049) PASS. Full [#45524483050](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45524483050) fails at inherited `Missing poll signature check`; all 14/14 firmware/platform + Android builds pass, downstream stages are skipped. CORE owns the authenticated poll producer contract; QA owns independent assertion reconciliation.
- RELEASE #291 remains at `53fc8a1c558f80adde19dc675b879c78797f0cd5`. Windows [#45485465901](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45485465901) and build [#45485465992](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45485465992) fail at mandatory shared-handover freshness; ESP32 compatibility [#45485465888](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45485465888) passes. CORE owns the canonical CURRENT_STATE / PROJECT_HANDOVER update; Master did not edit it.
- RENTAL #328 build [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) fails the mandatory handover freshness gate and ESP32 compile due to missing `mbedtls/sha256.h`; APK/API runs pass. HARDWARE #348 has the same missing-header build failure despite its focused header check passing.
- COE RELEASE #35 source/test `eda86d1f2c6f6bef8e6ff1111329d3f1775e043b`, final docs/PR `02561ba1ed60e0eb827946f76d8749a26943eaaf`. Shared [#45525928379](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45525928379) ran 220 tests (218 pass, 2 intentional skips), then failed closed on all 10 profiles for missing approved site-scoped RFC 4193 ULA /48 authority. Sandbox [#45525928381](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45525928381) passed 40/40 host preflight tests, then exited 125 because Bubblewrap is absent. Case guard [#45525928403](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45525928403) passes.
- CORE #252 scoped build, PISONET #255 synthetic Windows, QA #290 Windows, COE CORE #45 overlay/case, and COE INTERCON #49 Stage 5.1/case checks pass at their recorded heads. #292 has no PR-triggered runs. HARDWARE #347 has three failing runs; #340's focused checks pass. No owner result is transferred across PRs or SHAs.
- COE #26 has five workflows QUEUED and zero jobs/statuses.

## 4. Exact-tree and migration-provenance comparison

All recursive trees below were complete and non-truncated:

| Tree | Exact ref | Entries |
|---|---|---:|
| Historical intake source | Experiments `6d4c9b487af4d768c4d7627654d119417fcc6e00` | 2,391 |
| Current HARDWARE #349 source/test | `d5b5cd10ae7ab655639b011c442b6968b32c2398` | 2,532 |
| HARDWARE #349 final docs head | `18d4ff4ff86c6ea6d04419e2117833faa58e5e88` | 2,533 |
| COE #26 destination | `b382d233ff06c8791b1028bed3c617cc7b670d12` | 286 |

The #349 source/test and docs trees differ only at two file paths: `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md` and the new UTC01 handover `experiment/openwrt/BlazePwifi/docs/handover/2026-11-25-hw-cpp-fixture-stem-containment-utc01.md`. No source/test path changed after `d5b5cd`.

### SOURCE_INTAKE and runtime provenance

- `Pisowifi/SOURCE_INTAKE.json` blob: `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f`, schema 8.
- Historical source pin: `6d4c9b487af4d768c4d7627654d119417fcc6e00`; project root `experiment/openwrt/BlazePwifi`; destination root `Pisowifi/`.
- All 61/61 recorded historical source blob/mode pins and all 61/61 destination blob/mode pins match the exact trees.
- Actual row classification is 46 byte-identical / 15 derived; the JSON summary still claims 47 / 14.
- Against current #349 source/test, 33 runtime rows remain unchanged, 20 have changed blobs, and 8 source paths are absent. Historical source pins must not be silently rewritten to current main.

### Test identity and completeness

- Historical source tree: 149 tests; destination: 19. Among same-path original tests, 2 are exact and 2 divergent; 145 historical tests are source-only and 15 destination tests are destination-only.
- Current #349 source/test: 47 tests; destination: 19. Same-path comparison: 1 exact, 3 divergent, 43 source-only and 15 destination-only. `portal.sh` is exact; `config.sh`, `integration.sh` and `security.sh` differ.
- `MIGRATION_MAP.md` blob `b54fc15d83bc2269de03db8aadd0e76259fd13d9` has 18 test rows (4 original + 14 derived), while SOURCE_INTAKE lists 15 derived tests. `voucher_txn_journal.sh` is missing from the map. Map hashes for `run_focus.sh` and `member_txn_journal.sh` are stale relative to destination blobs `2b7b861e...` and `d04df3c6...`.

### Hardware and license parity

- Current source board subtree: 65 ESP32/ESP8266 files; destination Hardware subtree: 2 sketches.
- Current source board/lab Python helpers: 53; destination: 0.
- ESP32 source blob `adfd2f110d88243d03f2195658fb456b154dcb84` differs from destination `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.
- ESP8266 source blob `8a0b458b6c7fb99c0913df16c5b4ca94dbcdc50e` differs from destination `c8be98f72596681e36a3ad1f8939bf8046c96887`.
- Product LICENSE, QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE counterparts match exactly. Experiments root NOTICE.md and Tabler LICENSE have no destination counterparts. BlazeRentalLauncher licensing remains a separate RENTAL route.

**Disposition:** COE #26 remains FROZEN. No staging, copy, move, overwrite, rebase, cherry-pick, retarget or destination write occurred.

## 5. Audit execution and limitations

- **14/14 static audit assertions PASS** for complete trees, exact source/destination blob+mode pins, actual vs declared runtime classification, source drift, historical/current test identities, board/helper parity, migration-map rows/hashes, and license counterpart identities.
- Recursive Git trees, Git blob/mode identities, JSON/Markdown migration rows, owner PR heads, exact-head workflow runs and failed-job logs were inspected.
- Targeted exact-source synthetic verifier tests: **23/23 PASS**. The four fetched files were Git-blob verified against this Master commit before execution: `verify_migration_map.py` `55c01b75b5597eb46426f7c6406396c16eb58990`, `test_verify_migration_map.py` `88d24f9b85218d3546500f18e3ff70d76248f6aa`, `verify_source_intake_manifest.py` `f85c3005ba907c726d8270f10e0451b381e2a544`, and `test_verify_source_intake_manifest.py` `c4b097930bf5deaebe0bf186b515f140161c1c93`. Tests ran in an isolated temporary directory; they exercise verifier logic and are not a full repository checkout or product test.
- Full Master Python unittest discovery and `verify_coordination.py`: **NOT RUN**; no full authenticated checkout or dedicated Master validation workflow. No Master Actions run is claimed.
- This is a source/tree/provenance audit plus owner CI inspection, not a product build, independent QA pass, hardware acceptance or production approval.

## 6. Next owner actions

1. CORE publishes the canonical authenticated poll producer contract/golden vectors and refreshes canonical CURRENT_STATE / PROJECT_HANDOVER; do not bypass #291 freshness.
2. QA independently reconciles `Missing poll signature check` against the exact deny-only contract.
3. HARDWARE resolves the #348 supported Mbed TLS 4 / PSA provider decision with RELEASE and keeps #349 handovers current.
4. RENTAL resolves its missing-header/build and handover blockers.
5. RELEASE/COE owners obtain approved site-scoped ULA authority and an authorized Bubblewrap-capable runner; QA reviews #35 source/test `eda86d1f`.
6. COE integration owner reconciles SOURCE_INTAKE 46/15, adds the missing voucher map row, refreshes two test hashes, and completes board/helper/sketch/license provenance before any staging proposal.
7. Registry custodian restores authorized private v11/newer-correction access; repository administrators verify effective branch protection.

## 7. Production gate

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and explicit owner-authorized release gates remain unverified. No merge, release, signing, secret provisioning, hardware flash, physical test, real-payment operation, customer cutover or financial migration occurred.
