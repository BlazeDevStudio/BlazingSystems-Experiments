# PHX-MASTER UTC19 — current HARDWARE #352 head, COE #26 provenance and owner CI audit

**Observed:** 2026-11-25T19:17:34Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Task:** exact-head owner/CI refresh and reversible source-to-candidate provenance audit; no new task ID assigned.  
**Starting branch:** `phoenix/master-coordination@503661e6bae7db49765f11081972cf4c0a39e1f2`  
**Mode:** strict NO CODEX.

## 1. Live repository and control-plane identities

- Experiments default branch: `main@6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`.
- Active v0.6 development: `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`.
- Legacy v0.5.3 development: `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Master starting HEAD: `503661e6bae7db49765f11081972cf4c0a39e1f2`.
- COE default branch: `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`; its exact tree has only three entries (`README.md`, `Pisonet/README.md`, `Pisonet/`) and is a scaffold.
- COE integration candidate: PR #26, branch `integration/ecosystem-nonproprietary-candidate-20261111`, exact head `b382d233ff06c8791b1028bed3c617cc7b670d12`, base `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- Master PR #288: OPEN / DRAFT / UNMERGED; at the starting HEAD the live compare was 574 ahead / 1 behind, merge base `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`, 219 changed paths, all under `coordination/phoenix/`. Combined commit status and PR-triggered workflow runs at the starting HEAD were empty.
- `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29`: 11 routes, `DRAFT_REVIEW_ONLY`; PHX-MASTER is coordination-only with `target: null`.
- Control plane #172 is OPEN; cleanup #266 is OPEN and all seven cleanup tracks remain unchecked (0/7). The latest observed issue comment before this activation was RELEASE UTC18; no PHX-MASTER UTC19 message ID existed.

## 2. New owner activity — HARDWARE #352

- PR #352 branch: `phoenix/hw-exact-arduino-core-matrix-20261125-utc11`.
- Current PR/source-test HEAD: `f837146bc2522f88d2b8020ae8b94555d70e7ac3`; preceding source/test HEAD was `8eab82606ab8bf7ae5c598edde739d7b47e7c7a2`, with docs head `8daccf67e939dbd331c9111c91cb7bfb96d1cc94`.
- New test-only/refactor commits: `032e65170cff1c6b9bb097c6a4963c87b179bbe9` adds ordered section specifications; `f837146bc2522f88d2b8020ae8b94555d70e7ac3` splits the ESP8266 coin-pulse C++ host fixture into ordered literal sections. The commit diff is confined to the Hardware host-test lab; neither board `.ino` sketch changed.
- Exact current-head focused runs:
  - [Quarantine #45682323606](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45682323606) — PASS.
  - [Relay #45682323660](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45682323660) — PASS.
  - [ESP8266 core 3.1.2 #45682323487](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45682323487) — PASS.
  - [ESP32 core #45682323583](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45682323583) — PASS.
  - [Full #45682323745](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45682323745) — overall CANCELLED; validation job `139445965049` failed at the inherited `Missing poll signature check` in the ESP8266 sketch. Other downstream work was skipped/cancelled.
- The PR description still pins the previous docs/source-test heads `8daccf67` / `8eab8260`; HARDWARE owns its handover and PR-body refresh. Master did not modify the owner branch.

## 3. Exact HARDWARE source vs COE #26 candidate tree

Both GitHub recursive trees were complete and non-truncated, read at the exact current owner/candidate refs above.

| Measure | Experiments #352 source | COE #26 candidate |
|---|---:|---:|
| Complete tree entries | 2,564 | 286 |
| Git blobs | 1,985 | 207 |
| ESP32 + ESP8266 subtree entries | 84 | 4 |
| ESP32 + ESP8266 subtree blobs | 82 | 2 |
| Board-local Python helpers | 70 | 0 |

Exact firmware blob identities remain different:

| Firmware | Experiments source | COE #26 destination |
|---|---|---|
| ESP32 | `1412cf57b70c6ee3061da9831b8d9abf6d58d94e` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` |
| ESP8266 | `b99f1f21d8ad1e6df0e403b2b34507f97bd90c16` | `c8be98f72596681e36a3ad1f8939bf8046c96887` |

The mapped test-directory identity comparison (`experiment/openwrt/BlazePwifi/tests/` → `Pisowifi/tests/`) is:

- 47 source files / 19 destination files.
- 1 exact same-relative-path blob+mode match.
- 3 divergent same-relative-path blobs.
- 43 source-only paths.
- 15 destination-only paths.

No filename-only or similarly named test was counted as equivalent. This is a path/blob inventory, not an assertion that the smaller destination suite provides equivalent coverage.

## 4. Intake and licensing boundary

- COE #26 contains `Pisowifi/SOURCE_INTAKE.json` and `Pisowifi/MIGRATION_MAP.md`; no Hardware-specific SOURCE_INTAKE or MIGRATION_MAP exists in its candidate tree.
- The existing schema-8 PisoWiFi intake pins historical source commit `6d4c9b487af4d768c4d7627654d119417fcc6e00` and destination branch `feature/pisowifi-cleanup-stabilization`, not the current #26 integration branch. It covers the PisoWiFi rootfs, not the Hardware subtree.
- Its declared summary is 47 byte-identical / 14 derived, while its 61 runtime rows recount to 46 byte-identical / 15 derived; `derived_tests` contains 15. The current MIGRATION_MAP repeats the historical source/branch identity. This discrepancy remains COE integration-owner work.
- Experiments root `NOTICE.md` and `ui/vendor/tabler/LICENSE` are present at source but absent from COE #26. Product LICENSE, QRCode LICENSE, TailAdmin LICENSE and TailAdmin NOTICE have counterparts. `BlazeRentalLauncher/LICENSE` is under the separate RENTAL route and is not a Hardware/PisoWiFi destination license.
- The current 11-route manifest remains review-only; the Hardware routes are selective review, not copy permission. No staging, copy, move, overwrite, rebase, cherry-pick, retarget or destination write occurred. COE #26 remains FROZEN.

## 5. Current role PRs and exact-head CI

| Owner / PR | Current exact head | Current evidence / disposition |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | Build [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS; older scoped evidence, not financial acceptance. CORE retains finance, producer and canonical handover ownership. |
| RENTAL #328 | `10fc200b6dbf470a95e679d3acc58aff4ab2a67f` | APK [#45622918340](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918340), API [#45622918364](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918364), auth/recovery [#45622918551](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918551) PASS; shared build [#45622918468](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45622918468) FAIL. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Synthetic Windows [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM not invoked. |
| HARDWARE parent #349 | `2a5c997add4f49fcd74f753101d3a9daac0040bf` | Quarantine [#45603969253](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45603969253) and Relay [#45603968961](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45603968961) PASS; Full [#45603969181](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45603969181) FAIL. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; native COM not invoked. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No PR-triggered runs. |
| RELEASE #291 | `9b928c9eaa72cb26fdcf3f0e50a0ec024f4e3c30` | Windows [#45669599214](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45669599214) and Full [#45669599438](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45669599438) FAIL at CORE CURRENT_STATE freshness checkpoint `d85eb6a2766781b6cac1807cef461993d8216b84`; ESP32 compatibility [#45669599322](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45669599322) PASS. Four workflow files are newer than the checkpoint; CORE owns canonical CURRENT_STATE, RELEASE owns its branch/workflow refresh and rerun. |
| COE RELEASE #35 | docs `28da39c6db9953630400a12701621c5c824b90b0`; source/test `10f19a28fbdd7eccb7b78ab11b3cbd4a49f37d74` | Shared [#45673818111](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45673818111): 231 tests PASS / 2 skips, then all 10 appliance profiles fail closed for missing approved site-scoped RFC4193 ULA /48. Sandbox [#45673815489](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45673815489): 40 host tests PASS, then Bubblewrap unavailable / exit 125. Case guard [#45673815464](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45673815464) PASS. |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Overlay/Shell [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case guard [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS; focused only. |
| COE INTERCON #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | Stage 5.1 [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case guard [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared Hardware/contracts [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL (the owner report identifies the missing `mbedtls/sha256.h` include). |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows QUEUED / zero jobs; FROZEN. Queued/no-job is not a pass. |

## 6. Registry, tests and execution limitations

- Experiments `AGENTS.md`, the BLAZE cloud artifact policy and the public storage handover were read. The policy requires authorized private registry/ledger access before any Drive artifact creation and readback before verification.
- No Google Drive connector was exposed. Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections remain NOT_RECOVERED; older v5–v7 Library snapshots were not substituted. No private registry contents or IDs were copied into public GitHub.
- GitHub branch/PR/ref, complete recursive-tree, blob, test-identity, license-path, owner-CI and workflow-log inspections executed. A read-only in-memory audit ran 21/21 consistency assertions PASS (tree completeness, exact source/destination counts, test identity, firmware divergence, license gaps, manifest route count and PR path ownership). These are coordination assertions, not product tests.
- Master Python suite and `verify_coordination.py` were NOT RUN because no authenticated local checkout was available; Master exact-head Actions/statuses returned zero. Remote owner CI is not a Master test pass. No physical/native hardware test was run.

## 7. Next exact owner actions

1. HARDWARE refreshes PR #352 handover/description to current head `f837146b`, records the ordered fixture refactor, and preserves the Full validation failure; QA reviews the poll-signature assertion and CORE owns the producer contract.
2. CORE publishes the canonical CURRENT_STATE / PROJECT_HANDOVER and authenticated poll/register producer contract; RELEASE reconciles #291 against that owner-approved SHA and reruns its exact-head workflows.
3. QA independently reviews COE #35 and the current Hardware assertion; COE/CORE define approved site-scoped ULA authority and INFRA provides a Bubblewrap-capable runner.
4. COE integration owner creates a Hardware-specific per-file source/blob/mode/license/test map and resolves the existing PisoWiFi intake 47/14 versus 46/15 discrepancy before any staging review.
5. Registry custodian restores authorized private v11 and newer-correction access. Do not create Drive artifacts until that read succeeds.

**PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory. No merge, release, signing, secret provisioning, flash, physical test, real-payment operation or financial migration occurred.
