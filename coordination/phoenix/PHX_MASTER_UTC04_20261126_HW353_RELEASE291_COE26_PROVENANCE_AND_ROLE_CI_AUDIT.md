# PHX-MASTER UTC04 — exact-head role/CI, active poll-auth P0 and COE #26 migration provenance audit

**Observed:** 2026-11-26T04:53:01Z (Asia/Manila 12:53:01 +0800)  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Execution:** Strict NO CODEX. GitHub connector + ordinary source/tree inspection only; no Codex app, CLI, API, agent or workflow.

## 1. Live control-plane and branch state

- CONTROL PLANE issue [#172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172) remains OPEN. Latest role activity includes HARDWARE UTC04 comment [#7182863193](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-7182863193) and RELEASE UTC04 comment [#7182372031](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-7182372031). No current-date PHX-MASTER UTC04 checkpoint existed at start; this report is the single Master UTC04 checkpoint.
- Cleanup issue [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266) remains OPEN / 0-of-7. MASTER's broad duplicate/dead-code inventory is not complete; no mass move/deletion.
- Experiments refs: default `main@6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`; development `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`; Master `phoenix/master-coordination@3b7198d1d1ddc1651f95bb8065253ba8e68ae46b`.
- [PR #288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288) remains OPEN / DRAFT / UNMERGED. Its head equals the remote Master branch. Base is `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; current main has advanced to `6be5d19b`. Compare: 599 ahead / 1 behind, merge base `f4e8a891`. All existing PR paths are under `coordination/phoenix/`.
- COE default `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`; integration [PR #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26) remains OPEN / DRAFT / FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- Current [OWNERSHIP_ROUTES.json](OWNERSHIP_ROUTES.json) blob `e4db324315a1b3543fec17a148fbf960170fcb29`: 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER target null. It is a routing map, not a copy/move authorization. Its source_ref is the historical merge-base baseline, not current #353 source.
- The visible automation inventory showed Master, Release and Hardware continuations enabled; it did not surface a separate task with the stated CORE-continuation title. CORE was nevertheless left fully owner-reserved; no CORE source or task was taken over.

## 2. Owner PR and exact-head CI reconciliation

| Role / PR | Exact head(s) | Evidence / state |
|---|---|---|
| CORE #252 | `c82705f2` | Scoped build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; not financial acceptance. CORE remains owner-reserved. |
| RENTAL #328 | `10fc200b` | API21/23, auth/installer and APK identity focused checks PASS; shared build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL. |
| PISONET #255 | `d01fd164` | Synthetic Windows [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM NOT TESTED. |
| HARDWARE #340 | docs `f70f6af7`; source/test `d1380acf` | ESP32 core 4.0.0 compile [#45747192648](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747192648) PASS; final Full [#45747758154](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747758154) PASS (26 success / 4 intentional production import/sign/publication skips). Reproducible binary identity still unproven. |
| HARDWARE #348 | `93afd483` | Full [#45731176586](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45731176586) FAIL at missing `mbedtls/sha256.h` on ESP32 core 4.0.0. |
| HARDWARE #349 | `1a2ecf5f` | Full [#45724609215](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45724609215) FAIL at Missing poll signature check. |
| HARDWARE #352 | `2fa3b7db` | Focused Quarantine/Relay/core compiles PASS; Full [#45745420916](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45745420916) FAIL at validation. |
| HARDWARE #353 | docs `cb1787ac`; source/test `ed2f77d5`; parent #352 `2fa3b7db` | 29 ahead / 0 behind. Quarantine [#45756942179](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45756942179) and Relay [#45756942276](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45756942276) PASS. Full PR [#45756942184](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45756942184) and push [#45756939994](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45756939994) FAIL at the inherited ESP8266 `Missing poll signature check`. All 14 firmware/platform jobs and Android pass; downstream stages skip. UTC04 owner change is docs/workflow/handover only; no production .ino change. |
| QA #290 / #292 | `5c29d159` / `75a3f66d` | #290 synthetic Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; native COM not invoked. #292 has no PR-triggered runs. |
| RELEASE #242 | `a7e27fe5` | No exact-head PR-triggered run returned; PowerShell negative self-test not run. |
| RELEASE #291 | docs `0441a8e5`; source/test `f556769b` | 873 ahead / 9 behind #242, merge base `734b89d9`. Exact head has zero PR/push workflow runs and zero combined statuses. Static lock/verifier/workflow checks are reported PASS; hosted verification, artifact retention and reproducibility remain UNVERIFIED. |
| COE #35 / #45 / #49 | `b6ec4ba7` / `9d76a134` / `aeb8ff11` | #35 shared ULA admission and sandbox/Bubblewrap fail; case guard passes. #45 Overlay/Shell + case guard pass. #49 Stage 5.1 + case guard pass, shared ESP32 compile fails missing `mbedtls/sha256.h`. |
| COE #26 | `b382d233` | Five workflows QUEUED / zero jobs. Candidate remains FROZEN; no destination writes. |

## 3. Active v0.6 register/poll trust-boundary P0

Exact active branch: `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`.

- ESP32 sketch blob: `29f1125d52ff474a0d028ad41f7af201be1f0f9d`.
- ESP8266 sketch blob: `12c4bb82b6fddafe813674a0b5f692c1d3634073`.
- CGI blob: `db58041c0575ad0a1101d99cb85403e03c8dcb22`.

Both sketches synchronously POST `poll`, consume `insert` and `target_nonce`, and call `applyRemoteConfig`. The CGI poll response body contains `ok`, `insert`, `target_nonce`, `expires` and `controller`, but no `response_sig`. The same CGI has signatures for member endpoints; those do not authenticate poll.

**Disposition:** P0 OPEN. CORE must publish the approved authenticated register/poll envelope, canonical serialization, mandatory nonempty key provisioning, controller/target binding, freshness and replay rules. HARDWARE implements only after that contract; QA independently verifies both boards and negative/replay cases. Do not add an invented signature or weaken the Full assertion.

## 4. Exact #353 → COE #26 migration provenance

Both recursive trees were complete and non-truncated: source #353 **2,572 entries**, destination #26 **286 entries**.

| Ownership route | Source blobs | Destination blobs | Common relative paths | Exact blob matches | Divergent | Source-only | Destination-only |
|---|---:|---:|---:|---:|---:|---:|---:|
| ESP32 → Hardware/esp32 | 16 | 1 | 1 | 0 | 1 | 15 | 0 |
| ESP8266 → Hardware/esp8266 | 67 | 1 | 1 | 0 | 1 | 66 | 0 |
| tests → Pisowifi/tests | 47 | 19 | 4 | 1 | 3 | 43 | 15 |

- Source product `BlazePwifi/LICENSE` and destination `Pisowifi/LICENSE` are byte-identical Git blob `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- Source root `NOTICE.md` exists (blob `f6d92cd21465312be5993631fe26977219be0fb9`); COE #26 has no root NOTICE counterpart.
- In the destination's exact ESP32 blob `3cc7ec54...` and ESP8266 blob `c8be98f7...`, both sketches initialize `sigOk=true` and verify `response_sig` only if the controller key is nonempty. With an empty key, the default true value can admit an `ok:true` response to `applyRemoteConfig`. This is a keyless verification bypass on both boards.

**Decision:** COE #26 remains FROZEN. No staging, copy, move, overwrite, cherry-pick or destination modification. The product LICENSE match does not close root NOTICE or per-file licensing; test and firmware identity remain incomplete.

## 5. Private registry and storage-policy boundary

- Re-read repo root `AGENTS.md`, the linked public cloud artifact policy and storage handover. GitHub remains source-code authority; Drive mirror requires exact source SHA, size/SHA-256 and remote readback.
- Library title search surfaced historical registry v3–v7 only; exact `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not found.
- No Google Drive connector is exposed in this runtime. The Library is not treated as Google Drive and older registry snapshots are not substituted. No private IDs, registry content or credentials were copied to GitHub.

## 6. Changes, verification and limitations

Master-only coordination commit updates `ROLE_ASSIGNMENTS.md`, `INTEGRATION_MATRIX.md`, `AUDIT_SUMMARY.md`, `INDEX.md`, and adds this report. `OWNERSHIP_ROUTES.json` and `ARCHITECTURE_CONTRACTS.md` remain unchanged; no new shared interface contract was authorized.

- Coordinator static assertions: manifest JSON parse, 11 routes, Master target null, exact branch/PR head equality, report uniqueness, source/destination tree counts, mapped blob identity, license/NOTICE presence, active v0.6 source markers, COE keyless bypass markers and UTC04 checkpoint deduplication — PASS.
- Master Python unittest suite and `verify_coordination.py`: NOT RUN; no authenticated local checkout is available.
- Master GitHub Actions: 0 runs. Owner CI above was inspected at exact SHAs; Master did not execute those jobs.
- Native COM, physical hardware, power-cut, 30-device soak, payment and migration tests: NOT TESTED.

No subsystem source, COE destination, payment state, secrets, signing identity, firmware device or release state changed.

## 7. Next exact actions

1. CORE: publish authenticated register/poll envelope, mandatory key provisioning, canonical serialization, controller/target binding, freshness and replay rules.
2. HARDWARE: implement only against the approved contract; preserve relay/coin default-deny and exact branch ancestry.
3. QA: independently test both boards, missing/empty key, bad signature, wrong controller/target, stale/replayed nonce and timeout/failure cases at exact final SHA.
4. RELEASE/INFRA: dispatch the two named #291 workflows on exact head `0441a8e5`, retain binary/ELF/manifest artifacts and run the two-clean-build reproducibility comparison; QA review independently.
5. COE integration owner: complete per-file source/license/test identity map and restore executable destination CI before proposing any staging.
6. Registry custodian: restore authorized provenance-only access to actual private v11 and newer corrections.
7. Repository administrator: independently verify protected branch and required-check enforcement.

**PRODUCTION NO-GO** until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and explicit owner-authorized release gates are independently evidenced.

No merge, release, signer operation, secret provisioning, firmware flash, physical test, real-payment operation, customer cutover or financial migration occurred.
