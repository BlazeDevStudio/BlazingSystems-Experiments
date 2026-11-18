# PHX-MASTER UTC17 — COE #26 Hardware import, license and test-identity audit

**As of:** 2026-11-18T17:09:24Z  
**Role:** PHX-MASTER — coordination/phoenix, architecture/interface contracts, provenance and integration gates only  
**Disposition:** SOURCE-TO-DESTINATION PARITY NOT ESTABLISHED / MIGRATION BLOCKED / PRODUCTION NO-GO

## 1. Exact refs re-read

| Item | Exact ref |
|---|---|
| Experiments main | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments development | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master branch before this audit | `phoenix/master-coordination@dacde8ba60bd47e4d549d4000a1e37b5409e4a9f` |
| Master PR #288 | OPEN / DRAFT, base main `f4e8a891...`, head `dacde8ba...` |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | OPEN / DRAFT, `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| Hardware PR #323 | OPEN / DRAFT, head `988904e8bcd058b62a9fac4aa6319a9b7c5b2470`, parent #322 `50d93e0de3d682550b6f02fb43484e76ad9c7e08` |
| Hardware #323 source/test tree | `359bd8f685a2a464f4a77b84501fcf4055944d5c` |
| Ownership manifest | `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29` |

The manifest remains `DRAFT_REVIEW_ONLY`, source-ref pinned to Experiments main, destination PR #26, and PHX-MASTER target null. It is not a copy instruction. The v0.5.3 development branch still exists, but the actual current development branch is v0.6.0 at the SHA above.

## 2. Exact Hardware source versus COE #26 destination

The current #323 source tree contains 14 files under ESP32 and 14 under ESP8266, including 17 source-extracted Python lab files. COE #26's mapped Hardware subtree currently contains only two firmware sketches and one generic shell test.

| Component | Experiments #323 source blob | COE #26 destination blob | Result |
|---|---|---|---|
| ESP32 sketch | `7ebf0d3489c87abb52ca980f862cd6314a20af6e` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` | DIFFERENT |
| ESP8266 sketch | `312884c534637a3179180b432b9e345b36dc6af9` | `c8be98f72596681e36a3ad1f8939bf8046c96887` | DIFFERENT |
| Source ESP32 boot-polarity lab | `17f45e30402c1481983d3710336f7252f484ac6b` | absent | NOT IMPORTED |
| Source ESP8266 boot-polarity lab | `db0ac51115638d567d73e0dbfdff1129ef5efd3d` | absent | NOT IMPORTED |
| Source dual-store poll-fault lab | `25f5e8bd1a344d69acc0505324156f66a1abffa4` | absent | NOT IMPORTED |
| Source generic test | `41211b2c110ab409f6d9d1812ef12fda73b13211` | `f921c56cecc19cab1989507b9b4ade1f45dac54e` | DIFFERENT |

All 17 source board lab files are absent from the corresponding COE #26 Hardware target paths. The destination's `Hardware/tests/test_firmware_hardening.sh` is a different file from the source test. It asserts the presence of `response_sig` and `|poll|` strings. That positive-presence fixture is incompatible with the current #323 deny-only poll-response and coin-POST behavior and matches the current Full CI failure. Do not add a fake signature or weaken firmware default-deny to satisfy it.

The current #323 source has ConfigV3/local output-polarity gates on both boards; the staged COE #26 ESP32 sketch still defaults relay/LED active-high and lacks the local unknown-polarity gate, while its ESP8266 sketch is ConfigV2 and lacks ConfigV3. This is a material behavior gap, not a filename-only difference.

## 3. License and notice provenance

- Source project license: `experiment/openwrt/BlazePwifi/LICENSE`, blob `1ee55b94183417be977ca287cd7391f9a6f7e721`, MIT.
- COE #26 has the byte-identical blob only at `Pisowifi/LICENSE`; there is no root `LICENSE` and no `Hardware/LICENSE`.
- Source repository `NOTICE.md` blob `f6d92cd21465312be5993631fe26977219be0fb9` is absent from COE #26.
- Third-party vendor license/notice files exist under the Pisowifi target, but they do not settle the Hardware subtree's project-level license/notice mapping.

This is an unresolved destination license-scope/provenance gate. No legal conclusion is inferred from the presence of a license file in a sibling product directory. COE integration owner and repository/registry custodian must confirm the intended scope and stage the appropriate license/notice files before any Hardware copy.

## 4. Exact CI evidence

### Experiments Hardware #323

| Run | Result | Scope |
|---|---|---|
| [44347847077](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44347847077) | SUCCESS | Quarantine/readback focused lab |
| [44347847191](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44347847191) | SUCCESS | ESP8266 + ESP32 source-extracted boot/output-polarity labs |
| [44347846832](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44347846832) | FAILURE | Full validation fails at QA-owned `Missing poll signature check`; firmware targets and Android succeeded, downstream simulation/signing/publishing skipped |

The focused runs are SIMULATED host evidence only. Physical relay/electrical acceptance, real power cuts and native board acceptance remain NOT TESTED. #323 is a selected review candidate, not a canonical/accepted Hardware stack promotion. #318 remains non-mergeable; #324 is a sibling candidate; no source stack was composed.

### COE destination/release

- COE #26 still has five queued workflows and zero jobs: case-collision, Pisonet, Hardware/shared, Rental and PisoWiFi. There is no combined destination CI result.
- COE Release #35 head `b398906e23f95400ed39d08507e8a3ea1966dbff`: shared [44345859504](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44345859504) SUCCESS; case [44345859677](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44345859677) SUCCESS; mandatory sandbox [44345859641](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44345859641) FAILED CLOSED because bubblewrap is absent (13/13 host preflight tests passed first).
- Experiments Release #291 head `691ed55dbe39a79a88eac45f6eebff81cee5e628`: [44353380470](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44353380470) handover/build SUCCESS, privileged publisher SKIPPED.

### Other role heads and bounded exact-head CI

| Role | PR / head | CI observation |
|---|---|---|
| CORE | #252 `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS, scoped |
| RENTAL | #289 `68928774d0d7cf65adb26bc6b54199a3159d066c` | [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) SUCCESS, scoped |
| PISONET | #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS, scoped |
| QA | #290 `5c29d15994cee1279058f1eca12f2a3180704292` | [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS, Pisonet scope; #292 `75a3f66d...` has no run returned |
| RELEASE | #291 `691ed55dbe39a79a88eac45f6eebff81cee5e628` | [44353380470](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44353380470) SUCCESS with publisher skipped |

CORE source was not touched; the separate CORE continuation remains outside this Master run.

## 5. Static provenance assertions

Fourteen connector-side static assertions passed against the exact source/destination trees and fetched file blobs:

1. Both firmware sketch blobs differ.
2. Source ESP32/ESP8266 have the current local-polarity/ConfigV3 gates.
3. Destination ESP32/ESP8266 do not have those gates.
4. The 17 source board labs are absent from mapped COE Hardware paths.
5. Source and destination generic test blobs differ.
6. Destination test still contains positive `response_sig` and `|poll|` assertions.
7. The MIT source license blob is present only under the Pisowifi target; Hardware/root license is absent.
8. Source NOTICE is absent from COE #26.

These are source/tree assertions, not Python-suite execution, destination CI, independent QA or physical acceptance.

## 6. Required next actions

1. **COE integration owner:** do not copy/overwrite. Build a per-file mapping for the two firmware sketches, 17 missing labs/docs, test harness and exact blob provenance; identify which destination deltas are intentionally newer and which are stale.
2. **PHX-HARDWARE:** maintain the #323 review candidate; publish an owner-approved migration manifest for ConfigV3 and its test dependencies without taking over COE files.
3. **PHX-QA:** replace the stale positive poll-signature string-presence assertion with negative deny-only response tests; independently verify the exact #323 source/test SHA and the destination candidate SHA.
4. **Registry custodian / repository admin:** restore authorized access to canonical private Drive v11 and newer corrections; confirm the intended MIT/NOTICE scope for Hardware.
5. **PHX-RELEASE / infrastructure:** provide an authorized bubblewrap-capable runner for COE #35; no unsandboxed fallback.
6. **Repository administrator:** verify branch protection and required checks. Current branch objects report `protected=false` for Experiments main, current development and COE main; Master branch protection was not independently confirmed in this read.

No files were copied, moved, overwritten or deleted. No merge, rebase, release, signing, flashing, physical test, real-payment operation or production approval occurred.

**PRODUCTION NO-GO** remains mandatory: independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates.


## Later UTC17 live role-head reconciliation — 2026-11-18

### PHX-HARDWARE child PR #326

The current Hardware candidate has advanced beyond the initial #323-only snapshot. PR #326 is OPEN / DRAFT, child of #323 at base `988904e8bcd058b62a9fac4aa6319a9b7c5b2470`; current head is `28e13fc82a250821e815fd84b5fd61f1769e7106`.

Current changed blobs:
- ESP32 firmware `921a3ef4b7f06e199b957ec33421460154109a8f`.
- ESP8266 firmware `a4345f0a8338fdf4d921a7851fc2d537d582a42a`.
- ESP8266 pulse-capture lab `e6dfe3f5fdc0fea38357e7c3f87e1904179d6415`.
- ESP8266 poll-loop lab `ea912a56d4d3c5a88a69f7e04edb88ae87bcad47`.
- Hardware handover `1a8d30336228ae56d00b21977238e4b01b077a44`.

The source patch calls `latchPollPulseFault(pendingPulses)` before setting `fsReady=false` after a failed pending-journal write, and generalizes the marker text to `COIN_INGRESS_UNRESOLVED`. This is a Hardware-owned runtime change; Master has not edited it.

A previous #326 head `02a4429adfd02ab80ced7a1fcabe9f73039038a2` produced two focused failures because the mutation anchor `ignored-save-failure` was not found, despite the 8/8 pulse scenarios themselves passing. The current head `28e13fc82a250821e815fd84b5fd61f1769e7106` has current focused runs [44357779192](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44357779192) and [44357779195](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44357779195) IN PROGRESS; Full [44357779219](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44357779219) is also IN PROGRESS. No latest-head pass is claimed. The Hardware role's earlier UTC17 lock said no firmware runtime change was planned, while the current PR diff includes both firmware sketches; the PR diff/head is authoritative, and the owner should refresh its checkpoint to match.

### PHX-RELEASE COE #35 current head

COE #35 has advanced from `b398906e...` to current head `462d02fb01e689556efcf5bf1019af951807b130`, base #31 `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.

- Case-collision [44357449403](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44357449403): SUCCESS.
- Mandatory sandbox [44357449505](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44357449505): FAILED CLOSED because bubblewrap is absent, after 13/13 host-preflight tests passed; exit 125.
- Shared validation [44357449644](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44357449644): FAILED, 101 tests with one failure: `test_stage_overlay_rejects_parent_swapped_to_symlink_during_copy`. The assertion observed `generated-overlay` under the operator-owned external parent after the injected parent-to-symlink swap. ESP32/ESP8266 compile jobs were skipped.

This is a release-owned security regression under the test's injected race; PHX-RELEASE must fix and rerun exact-head tests. Master did not modify COE #35 source or tests. No unsandboxed fallback is permitted.

