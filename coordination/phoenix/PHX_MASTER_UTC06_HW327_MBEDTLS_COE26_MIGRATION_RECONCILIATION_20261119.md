# PHX-MASTER UTC06 — Hardware #327 Mbed TLS and COE #26 migration reconciliation

**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Task:** exact-head Hardware source/destination, test identity, toolchain, release-stack and role-CI reconciliation  
**Branch:** phoenix/master-coordination  
**Parent HEAD:** 8d98f7c61e01bbde9fbafb79e22b6fa01f09acd2  
**Base:** main f4e8a891aed8af86d5fd315d28750a0ac3a7372b  
**Disposition:** Master documentation updated; COE #26 migration BLOCKED; PR #288 remains DRAFT; PRODUCTION NO-GO.

## 1. Instructions and live control-plane re-read

At activation, PHX-MASTER re-read:

- Uploaded 00_MASTER_PROJECT_PHOENIX(1).txt and the latest README_FIRST handover.
- BLAZE-COMMS/1 COMMUNICATION_PROTOCOL.
- Experiments AGENTS.md on main and phoenix/master-coordination.
- Live [#172 control plane](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172) and [#266 cleanup-first gate](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266).
- Exact Experiments main, current v0.6.0 development candidate, legacy v0.5.3 branch and Master branch heads.
- Existing [Master PR #288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288), ownership manifest, latest role PRs and exact-head Actions.
- COE main and [integration PR #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26), release candidates #31/#35/#44, CORE #45 and INTERCON #39–#43.

Experiments AGENTS.md is blob d8777e3b58efc41caa5aa3c969c932aee9103d5f on both main and the Master branch. COE root AGENTS.md returns 404. The AGENTS-linked BLAZE_CLOUD_ARTIFACT_POLICY.md and BLAZE_CLOUD_STORAGE_HANDOVER.md could not be read through the available GitHub file surface.

The canonical private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not found in the accessible Library; no Google Drive connector is exposed. An older v7 snapshot is the newest matching registry surfaced by Library search, but it was not substituted. No private registry contents or IDs were copied into public GitHub.

## 2. Exact branch and PR authority

| Ref | Exact head | State |
|---|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b | Default branch |
| v0.6.0 development candidate | 2fbd2475e9f54878c316fa7cea2f228386b0e859 | 1,876 ahead / 22 behind main |
| v0.5.3 legacy branch | aad3aade72c1156eecba1fed30907c6d0283b2c5 | 293 behind / 0 ahead main |
| Literal development branch | 404 | Not found; no guessed substitute |
| Master branch before this commit | 8d98f7c61e01bbde9fbafb79e22b6fa01f09acd2 | Existing branch reused |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 | Default branch |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | OPEN / DRAFT |

Before this update, PR #288 was OPEN / DRAFT against main, with 96 changed paths, all under coordination/phoenix. The Master branch compared to main as 193 commits ahead / 0 behind. The current branch head and PR #288 head matched exactly.

The routing manifest OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29, status DRAFT_REVIEW_ONLY, with PHX-MASTER destination null. It was not modified.

## 3. Experiments Hardware #327 — current source and exact CI

Current [Hardware PR #327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327):

- Branch: phoenix/hardware-prepoll-edge-abort-20261119
- Current docs/PR head: ba4c0cb0c5eae4be5e014c0df6f5abe20a67b0bf
- Source/test commit: 0e5514adb0088649eca8bec9df6215faa50b556c
- Parent PR #326 head: 58c558fb6a237935214621adc3dee65a10fe1a51
- ESP32 sketch blob: c29483f0761ca6e2db0573bd12d6bfa502f12434, 61,807 bytes
- ESP8266 sketch blob: 1b32cb90be11da79ba7ea1155f128aee9e495dd2, 67,300 bytes

### Mbed TLS contract

The ESP32 sketch now selects PSA Crypto for Mbed TLS 4, the legacy SHA-256 API for Mbed TLS 3, and rejects all other major versions with a compile-time error.

Both board sketches deliberately deny poll admission and coin POST disposition. The current acceptPollResponse() and coinPostDispositionVerified() helpers return false. The source's response_sig mention is explanatory comment text, not a positive poll consumer.

The focused Mbed TLS lab blob is 51dc3c6674812c7fc1cd53e5b195a0b5219fd12c. Exact-head quarantine/readback run [#44468941707](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44468941707), job 135373435174, completed SUCCESS. Its log reports:

- Mbed TLS 3 selector/digest PASS.
- Mbed TLS 4 selector/digest PASS.
- Unsupported major 2 rejected.
- Unsupported major 5 rejected.
- Coin POST gate, poll-window, pulse-capture, request-digest and local EEPROM configuration labs passed their stated host/fake-I/O cases.

The lab explicitly reports STUB_API_ONLY=1 and EXACT_ESP32_CORE_3_3_13_BUILD_REQUIRED=1. It is not a real ESP32 core 3.3.13 compile.

### Exact current-head CI

- Focused quarantine/readback [#44468941707](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44468941707): SUCCESS.
- Relay/output [#44468941718](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44468941718): SUCCESS.
- Full [#44468941728](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44468941728), validation job 135373435914: FAILURE.

The Full log identifies the failing step as the inherited source test v05_firmware_hardening_test.sh, blob 41211b2c110ab409f6d9d1812ef12fda73b13211. That fixture still requires response_sig, |register| and |poll| string presence. The current failure is “Missing poll signature check” because the current source intentionally has no positive |poll| consumer. Do not add an unauthenticated positive signature or fake token to make this legacy test green.

The 13 firmware/platform targets and Android completed successfully; downstream simulations, candidate admission, signing and publishing were skipped. The Full run resolved ESP32 core 4.0.0 and ESP8266 core 3.1.2. The source build workflow blob 2cd6ce83b01c65fd78df091e502b68bf4fd277dc still installs unversioned cores, so this is observed resolution, not a pinned reproducible build.

Local EEPROM configuration migration tests in the focused log remain local device-configuration evidence only. The lab reports FINANCIAL_MIGRATION_TESTED=0 and PHYSICAL_POWER_CUT_VERIFIED=0. They do not satisfy the financial ledger v1-to-v2 migration or real power-cut gate.

## 4. COE #26 exact destination comparison

COE #26 remains OPEN / DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12. The destination Hardware files do not match current source:

| Item | Experiments #327 | COE #26 |
|---|---|---|
| ESP8266 sketch | 1b32cb90be11da79ba7ea1155f128aee9e495dd2 / 67,300 bytes | c8be98f72596681e36a3ad1f8939bf8046c96887 / 18,394 bytes |
| ESP32 sketch | c29483f0761ca6e2db0573bd12d6bfa502f12434 / 61,807 bytes | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 / 18,505 bytes |
| Mbed TLS | Major 3/4 selector; unsupported majors rejected | No version selector; legacy mbedtls/sha256.h include |
| Poll consumer | Default-deny; acceptPollResponse() returns false | Positive response_sig and |poll| consumer |
| Test inventory | Nine Python lab files in #327 changed-path inventory | One generic shell test |
| Toolchain | Current run resolved ESP32 4.0.0 / ESP8266 3.1.2; source workflow still floats | Workflow floats both cores; README says ESP32 3.3.12 / ESP8266 3.1.2 |

The destination sketch blob is 3cc7ec54b476943dc04a8d1af5e2df5fe054e422. Its Hardware test blob f921c56cecc19cab1989507b9b4ade1f45dac54e asserts positive response_sig, |register| and |poll| presence. This is not equivalent to the current source contract or its failure-injection labs.

COE #26 hardware-ci.yml blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793 installs unversioned ESP8266/ESP32 cores. Hardware/README.md blob 99af3e5b46cd8b6f35c6479b204683f60c55ebcb documents ESP32 3.3.12 and ESP8266 3.1.2, but the workflow does not enforce those versions. Five #26 workflows remain QUEUED with zero jobs:

- Case collision #43096752609
- Windows SoftTimer #43096752632
- Hardware/shared contracts #43096752800
- Rental #43096752563
- Pisowifi #43096752557

No destination build or test has executed at this candidate head.

### License scope

Source BlazePwifi/LICENSE and destination Pisowifi/LICENSE are the same MIT blob 1ee55b94183417be977ca287cd7391f9a6f7e721. COE Hardware/LICENSE and Hardware/NOTICE.md are absent at #26. No source BlazePwifi/NOTICE.md was found at the inspected root. The matching Pisowifi license does not establish Hardware subtree license/NOTICE scope. The PR narrative claim that the licensing gate is resolved is not independently accepted as migration evidence.

## 5. Release stack and other integration candidates

COE Release #35 current head is 5047af8b5a8296e06294bbda6bf42a6baea2294d, based on #31 at 59ed44d0b911e176f1a95b9cf5585ef811ffd31b. It is 108 commits ahead / 0 behind its parent. Its release workflow pins Arduino CLI 1.6.0, ESP8266 3.1.2 and ESP32 3.3.13. Exact shared/firmware run #44465377784 and case-collision #44465377781 pass. Mandatory sandbox run #44465377807 fails closed because bubblewrap is absent after 14/14 host-preflight tests; no unsandboxed fallback is allowed. These pins do not exist on #26.

COE Release #44 is 582fd5d5e83e36b36546ac28534740298ba94af4, based on older #35 commit 1a5be48d2845781b0b07bad39a37f8440cea4d4. Compare #35 → #44 is DIVERGED, 15 ahead / 25 behind, and PR #44 reports mergeable=false. RELEASE owns history-preserving reconciliation.

COE INTERCON candidates remain separate:
- #39 head 33e87fbd7f287955d85509cbb05ff5ca20a26a4b: 64-byte Stage-3 journal; runs #44234479271/#44234479266/#44234479329 pass.
- #40 head 85f38c6e2ba879fca9f26f708c1cbeb1736dd01c: 76-byte Stage-3 journal; runs #44235077999/#44235077989/#44235078142 pass.
- #42 head a35672fb60228fb8f84801405d032293f0266023: 92-byte Stage-3 journal; runs #44235625165/#44235625122/#44235625147 pass.
- #41 head 021e2474c5bc8df37ab016a586db516fb4f2445f: shadow-credit only, based on #39; runs #44235451605/#44235451492/#44235451542 pass.
- #43 head 8f5eec790dc2a3e25c219a6f51651113cd1c90cd: live timer/relay behavior based on #42; runs #44246962253/#44246962346/#44246962243 pass.

These are host/simulation and compile evidence. They do not prove real flash atomicity, physical power-cut behavior, protected key custody or native acceptance. No canonical Stage-3 or Stage-4 candidate is selected.

## 6. Other role PR and CI freshness

| Role | Exact head | Evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Run 42698139210 scoped SUCCESS; separate CORE continuation retains ownership |
| RENTAL #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | Runs 43653329235 and 43653329229 SUCCESS |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Run 42462978704 SUCCESS, scoped |
| HARDWARE #327 | ba4c0cb0c5eae4be5e014c0df6f5abe20a67b0bf | Focused runs pass; Full fails at QA-owned poll fixture |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Run 43633486963 SUCCESS, scoped |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No exact-head runs returned; base stale |
| RELEASE #291 | a8710d5d47dde40ac3273743ca39eaa4cace84b0 | Windows run #44461380937 fails at negative-selftest.ps1 because $buildWorkflow is uninitialized; BlazePwifi run #44461381052 succeeds; publisher/signing skipped |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Synthetic receipt-v1 runs #44295049727 and #44295049903 pass; not Master-v2 adoption |

RELEASE and PISONET must coordinate the release test ownership/fix within their authorized scopes. Master did not edit the Pisonet test or Release workflow.

## 7. Governance, verification and changes

Experiments main, v0.6.0 and COE main branch objects report protected=false. Both repositories' rulesets endpoints return empty arrays; classic branch-protection reads return 403 to this integration. Repository administrators must verify effective protections and required checks.

Cleanup issue #266 remains OPEN with historical source pins; it is not proof that all seven cleanup tracks completed. COE AGENTS.md is unavailable. The linked cloud policy/storage handover and private registry v11/newer corrections remain blocked by connector access.

Bounded source assertions executed against exact GitHub-fetched source/destination blobs: **17/17 PASS**. These are static source/provenance assertions, not the full Master Python suite. The full Master Python suite was NOT RUN in this activation; no Master PR #288 Actions runs were returned. Physical hardware, native acceptance, real power cuts and 30-device/24-hour soak were NOT TESTED.

This Master update changes coordination/phoenix documentation only. No subsystem source, COE destination source, ownership manifest, workflow, financial state, signer, hardware or release artifact was modified.

## 8. Owner actions and release gate

1. PHX-QA: replace positive poll-presence assertions with negative/default-deny behavior tests on the exact #327 source; independently verify Mbed TLS 3/4 and per-key NVS failure paths.
2. PHX-HARDWARE: retain deny-only firmware and provide an actual ESP32 core 3.3.13 build on the exact source.
3. PHX-RELEASE: pin the actual #26 destination toolchain; reconcile #44/#35 without force-push; obtain an authorized bubblewrap-capable runner.
4. PHX-RELEASE + PHX-PISONET: repair the $buildWorkflow negative self-test within agreed ownership.
5. COE integration owner: complete per-file source/destination provenance, test import mapping, explicit Hardware license/NOTICE scope and runnable exact-head #26 CI.
6. COE INTERCON owner + QA: select one Stage-3 and one Stage-4 candidate only after format/replay/key custody review and real hardware acceptance.
7. Repository administrator: verify branch protection and required checks.
8. Registry custodian: restore authorized read-only access to private registry v11 and newer corrections.

**PRODUCTION NO-GO** remains until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible financial migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently verified.

No merge, rebase, release, signing, secret provisioning, hardware flash, physical test, real-payment operation or financial migration occurred.