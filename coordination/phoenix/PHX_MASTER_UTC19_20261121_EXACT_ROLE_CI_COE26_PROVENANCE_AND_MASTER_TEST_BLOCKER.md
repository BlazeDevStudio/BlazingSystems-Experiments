# PHX-MASTER UTC19 — exact role/CI, COE #26 provenance, and Master test blocker

**Audit time:** 2026-11-21T19:07:56Z  
**Role:** PHX-MASTER — coordination, architecture contracts, ownership routing, integration provenance  
**Mode:** strict NO CODEX  
**Production:** **NO-GO**

## 1. Exact repository refs

| Ref | Exact SHA / state |
|---|---|
| Experiments default `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Active v0.6 audit/development | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Legacy v0.5.3 development | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Master audit-start head | `phoenix/master-coordination@cbe37870e30f6f469f76f7d421dcf9103187228b` |
| Master PR #288 | OPEN / DRAFT / UNMERGED; base `main@f4e8a891...`; 156 changed paths, all under `coordination/phoenix/` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | OPEN / DRAFT / FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| Routing manifest | `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29`; `DRAFT_REVIEW_ONLY`; PHX-MASTER target `null` |

The live branch refs and PR metadata were read before changes. No branch was force-pushed, rebased or retargeted.

## 2. Current owner PRs and exact-head CI

| Owner | PR / exact head | Exact-head CI observation |
|---|---|---|
| CORE | Experiments #252 `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) build PASS. CORE source ownership remains with its separate owner. |
| RENTAL | #328 `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | APK identity [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) PASS; API21/API23 [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS; build [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAILS at missing `mbedtls/sha256.h` and stale handover freshness checkpoint `468adc8129ea311e13f4c5c63eb6bb01ca67ecb0`. |
| PISONET | #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | Windows synthetic CI [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS; native COM/PnP acceptance NOT TESTED. |
| HARDWARE | #335 `d09b0c9dafad8dbbcda5723d8094f4975c14a274` | Quarantine [#44932969401](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44932969401) PASS; Relay [#44932969391](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44932969391) PASS; Full [#44932969438](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44932969438) FAILS at `Controller protocol parity` / `Missing poll signature check`. Fourteen target/Android jobs passed; downstream signing/publishing gates skipped. |
| QA | #290 `5c29d15994cee1279058f1eca12f2a3180704292`; #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 Windows [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS; #292 no PR-triggered workflow run returned. |
| RELEASE | #291 `42797e2f3d65c30a1070caf49c93aebec149d897` | ESP32 compatibility [#44894604453](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604453) PASS; Full [#44894604464](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604464) and Windows [#44894604466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44894604466) FAIL at mandatory handover freshness; checkpoint `adcae8141e673dc2147fcad50521ef3a23084d71` predates current source/workflow changes. |
| COE CORE candidate | #45 `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Overlay [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and case collision [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS, scoped only. |
| COE PISONET / QA | #28 `b21b04617d38a177260258de2d56b24382822117`; #30 `4897348d94a0cf7884ecd53244bfcd59e7bf2fbc`; #32 `29b6fe08b10688182d981a66745f482758bd6630` | Windows synthetic runs [#43632393888](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43632393888), [#43653415598](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653415598), [#43653540607](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43653540607) PASS; not combined migration acceptance. |
| COE RELEASE | #35 `756f7b38e302b958166d7006d1e98a86bb273303` | Sandbox [#44935351368](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44935351368) FAILS closed: Bubblewrap absent, exit 125; case collision [#44935351391](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44935351391) PASS; shared/profile validation [#44935351403](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44935351403) FAILS closed for all ten appliance profiles without approved site-scoped ULA /48. |
| COE Stage 5 | #48 `8286548e395366f2332830025fed00ceebdfb24a` | Stage [#44643670696](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44643670696) and case [#44643670679](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44643670679) PASS; shared [#44643670685](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44643670685) FAILS ESP32 compile at missing `mbedtls/sha256.h`. |
| COE Stage 5.1 | #49 `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | Stage [#44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) and case [#44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) PASS; shared [#44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAILS ESP32 compile at missing `mbedtls/sha256.h`. |
| COE integration | #26 `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows remain QUEUED with zero jobs: [#43096752609](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752609), [#43096752632](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752632), [#43096752800](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752800), [#43096752563](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752563), [#43096752557](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43096752557). |

Master #288 has no PR-triggered workflow runs at the audit-start head. Scoped PASS results above do not establish full integration, hardware acceptance or production readiness.

## 3. Exact source/destination provenance — COE #26 remains frozen

Complete recursive trees, not truncated:

| Exact tree | Entries | Blobs |
|---|---:|---:|
| Experiments main `f4e8a891...` (manifest source ref) | 2,340 | 1,764 |
| HARDWARE #335 candidate `d09b0c9...` | 2,471 | 1,892 |
| COE #26 destination `b382d233...` | 286 | 207 |

At current HARDWARE #335 head, the source ESP32 sketch blob is `53b27aa80fa4a91aabac71de57f550a8eef2cb61`; COE #26 destination is `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`. The source ESP8266 sketch blob is `71160ac8ebd5163b19a56d6c9e229a5429975fc8`; destination is `c8be98f72596681e36a3ad1f8939bf8046c96887`. Both firmware sketches diverge.

The #335 tree contains 32 board-local Python lab/helper files across ESP32/ESP8266; COE #26 contains zero. The #335 source test tree has 47 entries, while COE `Hardware/tests/` contains one test file. The source QA poll fixture `v05_firmware_hardening_test.sh` blob `41211b2c110ab409f6d9d1812ef12fda73b13211` differs from destination `Hardware/tests/test_firmware_hardening.sh` blob `f921c56cecc19cab1989507b9b4ade1f45dac54e`. Both retain positive response-signature/poll assertions and are not accepted test-identity parity for the current deny-only firmware contract.

License and notice evidence:
- Source `experiment/openwrt/BlazePwifi/LICENSE` and destination `Pisowifi/LICENSE` are byte-identical at blob `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- Source root `NOTICE.md` exists at `f6d92cd21465312be5993631fe26977219be0fb9`; COE #26 root NOTICE is absent.
- COE #26 `Hardware/LICENSE` and `Hardware/NOTICE` are absent; applicability and notice scope require owner/legal review.
- Source and destination firmware, QA fixture, workflow, imports and licenses are not collectively equivalent.

The routing manifest remains `DRAFT_REVIEW_ONLY`; PHX-MASTER destination is null. No copy, move, staging, rebase, cherry-pick, overwrite, route promotion or COE destination edit occurred. Keep #26 FROZEN.

## 4. Master test execution and governance

- Master branch and PR #288 were re-read at audit-start SHA `cbe37870e30f6f469f76f7d421dcf9103187228b`; 156/156 changed paths are under `coordination/phoenix/`.
- No Master PR-triggered workflow run was returned.
- Full local coordination unittest suite: **NOT RUN**. An authenticated checkout was unavailable in this execution environment; the GitHub clone attempt could not resolve the GitHub host. Source/tree inspection is not represented as test execution.
- Cleanup issue #266 remains OPEN; the Master cleanup inventory is incomplete and its checkbox remains unchecked.
- Canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not surfaced in Library search; only older v7/v6 snapshots appeared. No Google Drive connector is available in the current tool surface. Older snapshots were not substituted and no private contents were published.
- Cloud Artifact Policy / Storage Handover links referenced by AGENTS.md did not return readable file content through the connected GitHub surface; no Drive write was attempted.

## 5. Next actions

1. Run `python3 -m unittest discover -s coordination/phoenix -p 'test_*.py' -v` from an authenticated checkout of the final Master PR head and record the exact result.
2. PHX-QA replaces the inherited positive poll-signature fixture with source-linked negative/default-deny tests; do not add a response signature to firmware to satisfy the stale fixture.
3. PHX-CORE publishes the approved authenticated register/poll and event-bound receipt contract; keep CORE implementation with its separate owner.
4. PHX-HARDWARE reruns Full only after QA/CORE fixture-contract alignment.
5. PHX-RENTAL resolves the Mbed TLS header baseline and refreshes its handover; PHX-RELEASE refreshes the stale handover and obtains a Bubblewrap-capable runner; site authority supplies the approved ULA /48.
6. Registry custodian restores authorized v11/newer-correction access; repository administrator supplies effective branch-protection evidence.
7. Keep COE #26 frozen until per-file provenance, licenses, test identity, import completeness and exact-head CI are independently accepted.

**No subsystem source changes, merge, release, signer provisioning, hardware flash, real-payment operation, physical test or production approval occurred. PRODUCTION NO-GO.**
