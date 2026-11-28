# PHX-MASTER UTC22 — exact intake, test identity, Hardware #355 and role-CI audit

**Audit time:** 2026-11-26T22:34Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Scope:** `coordination/phoenix/`, architecture/interface contract review, cross-repository provenance and integration evidence only.  
**Starting Master HEAD:** `phoenix/master-coordination@7a852ab038b9956cbee7f87ee85510c404bed998`

## Decision

**PR #288 OPEN / DRAFT / UNMERGED. COE #26 FROZEN. Cleanup #266 OPEN / 0-of-7. PRODUCTION NO-GO.**

This activation refreshed exact refs, owner PR heads and CI, the route manifest, the candidate's exact source-intake and migration-map pins, source/destination recursive trees, mapped test identities, selected licence/NOTICE blobs and current CI failure logs. No subsystem source, role-owned branch, ownership manifest, COE destination or production state was changed.

## Live refs and coordination

| Ref | Exact SHA / state |
|---|---|
| Experiments `main` | `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5` |
| Experiments `blazepwifi-v0.5.3-development` | `aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Experiments active v0.6 foundation | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master `phoenix/master-coordination` | `7a852ab038b9956cbee7f87ee85510c404bed998` |
| COE `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

The inspected branch metadata reports `protected=false` for Experiments main, v0.5.3 development, v0.6 foundation, Master coordination and COE main. Do not treat branch names or CI as a protected signing witness.

CONTROL PLANE #172 remains OPEN (last updated 2026-11-26T22:18:56Z). Cleanup #266 remains OPEN; its seven role checkboxes remain 0/7. The Master PR #288 is based on main, currently 645 commits ahead / 1 behind current main, with 241 changed paths at audit start, all under `coordination/phoenix/`. No exact-head Master workflow runs, combined statuses or check-runs exist at the starting SHA.

The current `OWNERSHIP_ROUTES.json` blob is `e4db324315a1b3543fec17a148fbf960170fcb29`, schema `phoenix/ownership-routes/v1`, 11 routes, `DRAFT_REVIEW_ONLY`, source pin `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`, destination candidate PR #26 / `b382d233ff06c8791b1028bed3c617cc7b670d12`. PHX-MASTER remains `coordination/phoenix/` with `target: null`; the broad Rental route remains `manual-file-mapping-required` and `copy_permitted: false`. Eleven read-only structural assertions passed. These assertions do not authorize migration.

## COE #26 — exact source-intake and test-identity discrepancies

Candidate files at exact #26 head:
- `Pisowifi/SOURCE_INTAKE.json`, blob `1b9018ff944f7f673934d0fc2a97e0a0090d3f5f`, schema 8.
- `Pisowifi/MIGRATION_MAP.md`, blob `b54fc15d83bc2269de03db8aadd0e76259fd13d9`.
- `docs/audits/HARDWARE_FIRMWARE_AUDIT.md`, blob `86c06e7574761465b80482430296eb712d985367`.

The intake pins source Experiments commit `6d4c9b487af4d768c4d7627654d119417fcc6e00` and destination branch `feature/pisowifi-cleanup-stabilization`. The live #26 PR branch is instead `integration/ecosystem-nonproprietary-candidate-20261111`. The migration map repeats the old destination branch. Reconcile this branch/source lineage before any stage.

The 61 runtime intake rows classify **46 byte-identical / 15 derived**, while the declared summary says **47 identical / 14 derived**. The declared rootfs recovered count is 61/61 with zero unrecovered; that does not resolve the row-classification contradiction.

Recursive trees at the exact pinned source and destination SHAs are 2,391 / 286 entries (1,845 / 207 blobs). The mapped test directories contain:
- Source `experiment/openwrt/BlazePwifi/tests/`: 149 files.
- Destination `Pisowifi/tests/`: 19 files.
- Exact blob identities: 2; divergent same-path blobs: 2; source-only identities: 145; destination-only identities: 15.

The current candidate therefore does not preserve the pinned source test identities. Its PR body describes 21 passing shell suites, but the exact #26 candidate has eight queued workflow runs, zero completed jobs and zero check-runs; those PR-body statements are not current exact-head CI evidence.

## Hardware source and destination provenance

At intake source commit `6d4c9b487af4d768c4d7627654d119417fcc6e00`:
- ESP32 sketch blob: `29f1125d52ff474a0d028ad41f7af201be1f0f9d`.
- ESP8266 sketch blob: `12c4bb82b6fddafe813674a0b5f692c1d3634073`.

At COE #26:
- ESP32 destination blob: `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`.
- ESP8266 destination blob: `c8be98f72596681e36a3ad1f8939bf8046c96887`.

Both destination sketches differ from the intake-pinned source.

The current Hardware-owned PR #355 has advanced to docs/PR HEAD `51bd21451a964cf2f608abd2287a89925fe9f930`, source/test SHA `68416f69bc10dde8b2afa2948b312d4010507ad5`, stacked on #354 `fc842342596786e072630179acfbbc4feeb2ba02`. Its ESP32/ESP8266 sketch blobs are `a0da7aa072f404fc3c1b098227308f50306e45f9` / `9f0f4829cf57a6a12f4d940b051f17035e0a1670`; it contains 11 board-local Python lab/support files. COE #26 Hardware contains zero board-local Python labs and only the two divergent sketches plus one shell hardening test. This current owner-branch delta is not represented by the older intake pin.

The COE Hardware audit says the sketches were not copied pending P0-1, but both sketches are present in the candidate tree with different blobs. Its recorded source hashes `117c6e937e8f12f3890ace2ae23b3a23ff1c3df0` / `bfb94920eb0a189ca01d52e5443954fa133f5423` also differ from the intake-pinned source hashes above. The audit's source pin and its “not copied” statement require owner correction.

## Selected licence and NOTICE readback

Exact matches: PisoWiFi project LICENSE, QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE. Missing destination counterparts: source root NOTICE, Tabler LICENSE and BlazeRentalLauncher LICENSE. No files were copied to repair these gaps; broader licence review remains with the destination owner.

## Exact-head CI and owner boundaries

- HARDWARE #355: Poll-intake deny [#45901141684 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45901141684); Mbed TLS matrix [#45901141615 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45901141615); Full [#45901141748 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45901141748) at QA-owned Controller protocol parity; Native [#45901142284 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45901142284) because PAY-0745 requires active `clearPending(true/false)` callsites. Preserve deny-only behavior; do not add unsafe clears to satisfy the assertion.
- HARDWARE #354: Poll-deny [#45864684458 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684458), Mbed [#45864684325 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684325), Native [#45864684295 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684295), Full [#45864684497 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45864684497).
- HARDWARE #353: Relay [#45871096516 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45871096516), Quarantine [#45871096480 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45871096480), Full [#45871096425 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45871096425) on missing ESP8266 poll-signature parity.
- COE RELEASE #35 at `bc57ba8ecc5245ce538c6770a45bb25e2b8b5ef3`: case guard [#45897198239 PASS](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45897198239); shared validation [#45897198326 FAIL](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45897198326), 10/10 appliance profiles fail closed because approved site-scoped RFC 4193 ULA /48 authority is absent; sandbox [#45897198204 FAIL](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45897198204), with 48 host tests passing before the gate rejects missing trusted `bwrap` and private host-mask target. Firmware compile jobs skipped.
- RENTAL #328: API21/API23, auth/installer and APK identity focused runs PASS; shared build [#45622918468 FAIL](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) at handover freshness and ESP32 `mbedtls/sha256.h` missing.
- CORE #252 build [#42698139210 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210); PISONET #255 Windows synthetic [#42462978704 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704), not native COM acceptance; QA #290 Windows synthetic [#43633486963 PASS](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963); QA #292 has no exact-head run.
- RELEASE #242 / #291 have no current exact-head PR workflow runs. COE CORE #45 focused overlay/case checks PASS; INTERCON #49 Stage 5.1/case checks PASS but Shared Contracts FAIL.
- COE #26 exact head has 8 queued runs (5 pull_request + 3 push), zero jobs and zero check-runs.

## Execution and access limits

Eleven ownership-manifest structural assertions passed. They are not product tests. Master Python tests and `verify_coordination.py` were NOT RUN: a direct `git ls-remote` attempt failed because this execution environment could not resolve `github.com`; no exact-head Master Actions/check-runs exist.

The private Google Drive v11 registry and newer corrections were NOT RECOVERED. The available file Library search did not return the requested registry, and no Google Drive connector is exposed in this run. The linked Cloud Artifact Policy and Storage Handover required by AGENTS.md were also not accessible through the connected GitHub integration. No older registry or private IDs/content were substituted or published.

The active automation inventory shows the separate `Blaze Hourly Production Development` task is PHX-HARDWARE; the specifically named CORE continuation was not visible in the active list. CORE source remained untouched; no competing CORE work was started.

## Next owner actions

1. COE integration owner reconciles the intake source commit, destination branch, 46/15 versus 47/14 counts, test identities, firmware audit contradiction and missing licence/NOTICE counterparts. Keep #26 FROZEN; do not stage or move files.
2. HARDWARE owner refreshes #355 handover/PR body to docs head `51bd2145` and source/test SHA `68416f69`; preserve deny-only behavior.
3. CORE and QA reconcile authenticated pending disposition and PAY-0745 without adding unsigned poll trust or unsafe pending clears.
4. RELEASE owner refreshes and runs #242/#291 at exact heads; CORE remains owner of shared financial handover.
5. Registry custodian supplies read-only access to v11 and newer corrections through an authorized Drive connector.
6. MASTER reruns the repository test suite and `verify_coordination.py` after an authenticated checkout or Master CI path is available.

Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory. No merge, release, signing, secret provisioning, flash, physical test, real payment operation, customer cutover or financial migration occurred.
