# PHX-MASTER UTC17 — live exact-head, poll-deny, Windows release and COE migration provenance

**Checkpoint:** 2026-11-19T17:42:36Z  
**Role:** PHX-MASTER — architecture, coordination and cross-repository provenance only  
**Execution:** No Codex app, CLI, API, agent, workflow or delegated Codex implementation  
**Disposition:** OPEN / DRAFT / MIGRATION BLOCKED / PRODUCTION NO-GO

## 1. Exact repository and coordination state

| Ref | Exact state |
|---|---|
| Experiments default branch | `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Named development ref | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Comparison-only ref | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master PR #288 | `phoenix/master-coordination@b1a38cea83a9bfe877acd795730079d65ed3bf25`, base `main@f4e8a891...`, OPEN/DRAFT |
| Master PR #288 tree | 105 changed paths; all are under `coordination/phoenix/` |
| COE default branch | `main@a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `integration/ecosystem-nonproprietary-candidate-20261111@b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN/DRAFT, 205 changed paths |
| Ownership manifest | `OWNERSHIP_ROUTES.json@e4db324315a1b3543fec17a148fbf960170fcb29`; `DRAFT_REVIEW_ONLY`; PHX-MASTER target `null` |

The named development branch remains v0.5.3; v0.6.0 is a comparison-only audit foundation in the current control-plane contract. Do not silently promote either branch or treat a development ref as production.

GitHub branch metadata currently reports `protected=false` for the queried main/development refs. Classic branch-protection reads are permission-denied (403), so effective required-check enforcement still needs repository-administrator verification. No protection setting was changed.

## 2. Current role PRs and exact-head CI observations

| Role | Current PR/API head | Exact CI observation |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS, scoped. Separate CORE continuation retains implementation ownership. |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) SUCCESS, scoped. |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS, scoped; native COM acceptance remains unverified. |
| HARDWARE #327 | API head `43a8d511fc1fb6f238f5e7ea24036659fb2ab71a`; latest owner-declared source/test SHA `ad421e48b2908fab48dc85b40c169450d9c0239c` | Quarantine [44580223038](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44580223038) SUCCESS; Relay/output [44580223257](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44580223257) IN_PROGRESS; shared BlazePwifi build [44580223115](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44580223115) validation FAILED at the QA-owned `Missing poll signature check`; other matrix jobs were still running at the read. |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS, scoped. |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No current-head run returned; status UNKNOWN, not PASS. |
| RELEASE #291 | API/docs head `110f89985703e5685b193e4398492d3a16b26cdd`; source/test SHA `36056d08b4ff7de6f692c5c83b55c1e335cda070` | Full shared build [44576439303](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44576439303): 27 SUCCESS / 5 intentionally SKIPPED / 0 failed; signing/publisher jobs skipped. Windows [44578334600](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44578334600) FAILED in PISONET-owned `negative-selftest.ps1`; publisher skipped. |

### HARDWARE poll-deny contract — confirmed source behavior

At exact source/test SHA `ad421e48b2908fab48dc85b40c169450d9c0239c`, both board sketches have explicit deny-only behavior:

- `acceptPollResponse(const String &response)` ignores the unapproved response, sets `insertMode=false`, clears `activeTarget`, and returns `false`.
- `coinPostDispositionVerified(...)` returns `false` until CORE publishes an approved event-bound receipt/disposition contract and QA approves its vectors; pending journal and one-shot attempt evidence must remain.
- The source comments state that the current `response_sig` expression is only a derived candidate, not an approved poll authorization contract. A literal `|poll|` signature marker is absent.

The inherited QA-owned `experiment/openwrt/BlazePwifi/tests/v05_firmware_hardening_test.sh` blob `41211b2c110ab409f6d9d1812ef12fda73b13211` still requires both `response_sig` and `|poll|` markers. The current shared build fails exactly at `Missing poll signature check`. Do not add a fake marker or weaken firmware deny behavior. QA should replace marker-presence with source-linked negative tests proving unsigned/malformed poll responses cannot set `insertMode`, set `activeTarget`, clear pending evidence, credit time, or energize output.

HARDWARE quarantine is CI-verified; relay/output is still in progress; the shared validation failure is not a Full acceptance result. No physical board, relay load, coin acceptor, EEPROM/NVS power cut or hardware soak was tested.

### RELEASE Windows ownership defect

Windows run [44578334600](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44578334600), job `135751984409`, passed handover freshness and package parity, then failed in:

- Path: `experiment/windows/BlazePisonet-SoftTimer/tests/ReleaseSigning/negative-selftest.ps1`
- Blob: `8b69174bf519154e43f7e12e4a9fa2c0e75d350f`
- Failure: `$buildWorkflow` is read under StrictMode without an earlier assignment.
- The PR #291 patch adds these references in the PISONET-owned file; no assignment is present in the inspected source.

The path belongs to PHX-PISONET under the current routing manifest. PISONET must review/correct its test, and RELEASE must rerun its consumer workflow. PR #291 also contains CORE-owned handover paths; CORE review is required. RELEASE does not acquire ownership of either subsystem's files. No source-owner branch was modified by Master.

## 3. COE #26 — exact migration provenance recheck

COE #26 remains OPEN/DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`. Its five exact candidate workflows are still QUEUED with zero jobs:

- Case collision: [43096752609](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609)
- PISONET Windows: [43096752632](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632)
- Hardware/Shared: [43096752800](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800)
- Rental: [43096752563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563)
- Pisowifi: [43096752557](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557)

### Exact board blobs and sizes

| Board | Experiments source SHA/blob | Source bytes | COE #26 destination blob | Destination bytes |
|---|---|---:|---|---:|
| ESP32 | source file blob `f89bc561b2093328286d7633da794667b2ab06de` | 66,899 | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | 18,505 |
| ESP8266 | source file blob `284f4337bc9e2aa4d78c61f0d7e4c4163ffb0a82` | 70,585 | `c8be98f72596681e36a3ad1f8939bf8046c96887` | 18,394 |

Both source/destination pairs are different Git blobs and materially different sizes. The source tree at the current Hardware owner source/test SHA contains 9 ESP32 and 15 ESP8266 Python files (24 Python files total, including helpers and a RED fixture); the destination Hardware area contains one generic shell test. This is not test-import equivalence.

Destination `Hardware/tests/test_firmware_hardening.sh` blob `f921c56cecc19cab1989507b9b4ade1f45dac54e` positively requires `response_sig`, `|register|`, and `|poll|`. That test identity conflicts with the current source's explicit deny-only poll/coin-post disposition until the canonical producer/consumer contract is approved.

### Licensing and NOTICE

- Source `experiment/openwrt/BlazePwifi/LICENSE` and destination `Pisowifi/LICENSE` both have blob `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- Source `experiment/openwrt/BlazePwifi/NOTICE.md` is absent.
- Destination `Hardware/LICENSE` and `Hardware/NOTICE.md` are absent.

The matching Pisowifi MIT license does not establish Hardware licensing/NOTICE scope.

### COE owner candidates — scoped CI only

| Candidate | Exact head | Returned current-head runs |
|---|---|---|
| #28 PISONET | `b21b04617d38a177260258de2d56b24382822117` | [43632393888](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43632393888) SUCCESS |
| #29 CORE | `d0830332dee8a1844a85606150681b41d91fe796` | [43653906676](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653906676), [43653906675](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653906675) SUCCESS |
| #30 PISONET | `4897348d94a0cf7884ecd53244bfcd59e7bf2fbc` | [43653415598](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653415598) SUCCESS |
| #31 RELEASE | `59ed44d0b911e176f1a95b9cf5585ef811ffd31b` | Shared [44222517238](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517238) and case [44222517258](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517258) SUCCESS; mandatory sandbox [44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) FAILED closed. |
| #32 QA | `29b6fe08b10688182d981a66745f482758bd6630` | [43653540607](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653540607) SUCCESS |
| #45 CORE | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | [44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903), [44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) SUCCESS |

These are separate scoped candidate checks, not a combined COE #26 acceptance run.

COE #35 remains OPEN/DRAFT at `0e3662b9aef4b2a2248e3a064b07d07e9097be1b`: shared/hardware [44543625272](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44543625272) FAILED, case [44543625541](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44543625541) PASS, sandbox [44543625389](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44543625389) FAILED closed because Bubblewrap is unavailable. The packager intentionally has no approved production site ULA configured; all ten profiles fail closed. COE #44 at `582fd5d5e83e36b36546ac28534740298ba94af4` remains a per-appliance identity candidate, not proof of one durable site-wide prefix.

No COE file was copied, moved, overwritten, rebased, cherry-picked, merged or staged.

## 4. Private registry and governance

The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not surfaced by the authorized Library search. Older v5-v7 snapshots surfaced, but were not substituted. No Google Drive connector is exposed in this runtime. No private Drive identifiers or contents were copied to public GitHub.

Experiments AGENTS.md was read at the current Master ref. It requires the private registry, artifact manifest and sync ledger before artifact writes; this activation made no Drive/artifact writes. COE root AGENTS.md returned 404 at COE main. Cleanup issue #266 remains OPEN; the Master cleanup track is still partial, not complete.

## 5. Master execution and next actions

- Master branch: `phoenix/master-coordination`; parent before this update: `b1a38cea83a9bfe877acd795730079d65ed3bf25`.
- Master Actions: no exact-head run returned.
- Full Master Python suite: NOT RUN.
- This activation performed GitHub source/tree inspection, exact blob and size comparison, current PR/CI metadata inspection, and job-log inspection. It did not execute the full checked-out Master Python suite.
- No subsystem source files, owner branches, route manifest, binaries, hardware, payment systems, secrets or production settings were changed.

**Next owner actions:**
1. PHX-QA replaces the obsolete positive `|poll|` marker assertion with negative/default-deny tests and independently verifies both board sketches at the exact source SHA.
2. PHX-PISONET reviews/fixes the uninitialized `$buildWorkflow` read in its owned negative self-test; PHX-RELEASE reruns Windows #291 after the owner correction.
3. PHX-CORE and COE integration owner decide the durable site-wide ULA provisioning authority; #35 remains fail-closed until then.
4. COE integration owner completes per-file source/destination blob, license/NOTICE, test identity, import completeness and executable destination CI evidence before proposing any move.
5. PHX-INFRA supplies an authorized Bubblewrap-capable runner; repository administrator verifies effective branch protection; registry custodian restores authorized v11/newer-correction access.

**PRODUCTION NO-GO** remains mandatory: independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible financial migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates.
