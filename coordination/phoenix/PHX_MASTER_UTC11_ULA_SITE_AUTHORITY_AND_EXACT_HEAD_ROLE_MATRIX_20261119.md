# PHX-MASTER UTC11 — ULA site authority, exact-head role matrix, and COE #26 provenance

**Date:** 2026-11-19 UTC11  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Governing inbox:** [Experiments issue #172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)  
**Cleanup gate:** [Experiments issue #266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
**Existing Master draft:** [Experiments PR #288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/288), OPEN / DRAFT / UNMERGED  
**Existing destination candidate:** [COE PR #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26), OPEN / DRAFT / UNMERGED  
**Disposition:** Master documentation and contract regression updated; destination migration BLOCKED; PRODUCTION NO-GO.

## 1. Live identities and coordination

| Ref | Exact value at read |
|---|---|
| Experiments default `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments development | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` |
| Comparison-only foundation | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Master branch before this activation | `phoenix/master-coordination@9a7a8f855913e6a74cdead136631a1b317a62eb1` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |
| Ownership manifest | `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29` |

Issue #172 is OPEN and issue #266 is OPEN. The last current-day Master checkpoint before this activation was UTC10; no PHX-MASTER UTC11 checkpoint for 2026-11-19 existed at the final deduplication read. The latest worker locks were PHX-RELEASE UTC11 and PHX-HARDWARE UTC11; no CORE work was started or duplicated. The separate CORE continuation retains implementation ownership.

The machine-readable route manifest remains `DRAFT_REVIEW_ONLY`, source-pinned to Experiments main and destination-pinned to COE #26, with PHX-MASTER target `null`. No route was promoted.

## 2. P0 ULA finding — COE #44 is not a site authority

COE RELEASE #44 is at docs/PR head `582fd5d5e83e36b36546ac28534740298ba94af4`, base `1a5be48d2845781b0b07bad39a37f8440cea4d4f`, with source/test head `81cb1747342b0335d586184c5ba58cb138d6201a`. Current COE #35 is `5047af8b5a8296e06294bbda6bf42a6baea2294d`. Exact compare from current #35 to #44 reports **diverged: 15 ahead / 25 behind**, merge base `1a5be48d2845781b0b07bad39a37f8440cea4d4f`. #44 is not based on the current #35 head.

At #44 packager blob `f2c2467f37137c38856abcad1b101436e50d3970`, `generate_ula_firstboot_script()`:
- reads five random bytes from `/dev/urandom` for a 40-bit Global ID on each appliance first boot;
- constructs an `fd00::/8` /48;
- writes `network.globals.ula_prefix` through UCI; and
- requires persisted readback.

This is an appliance-local allocation mechanism. Two independent routers on the same LAN can generate different /48s. It does not provide one prefix shared by all appliances at one site, and no site-level distribution authority is present in this code.

The exact #44 test blob `6d8853f325efe08a065937df527abc4c709e52b3` includes:
- `test_generic_overlay_defers_ula_to_installation_first_boot`;
- `test_ula_firstboot_commit_failure_preserves_unrelated_pending_network_changes`; and
- `test_ula_firstboot_rejects_wrong_globals_section_type_before_accepting_prefix`.

Those are useful local provisioning/rollback tests. They do not test same-site multi-appliance sharing, distinct-site distribution, concurrent first boot, or multi-device backup/restore identity.

Exact-head COE #44 evidence:
- Shared PR [#44390136309](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136309): SUCCESS — 109 packaging tests (two intentional sandbox-only skips), 18 hardening/shared checks, 10/10 profiles, ESP32/ESP8266 compile and artifact-upload jobs.
- Case collision [#44390136296](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136296): SUCCESS.
- Mandatory sandbox [#44390136327](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136327): FAIL CLOSED — host preflight 14/14, then Bubblewrap missing; exit 125. Identity/namespace/Bubblewrap packaging regressions were skipped, not passed.

Master added Architecture Contracts §6.9.1 to define “installation” as the LAN/site identity boundary, not each physical router. It requires one durable site authority, same-site sharing, distinct-site separation, concurrent first-boot convergence or fail-closed behavior, and persistence through reboot/upgrade/backup/restore. It does not select the authority design.

## 3. Exact COE #26 Hardware provenance refresh

The current source is Experiments HARDWARE #327 head `82fef49d945aeb64da76e89ef12126784a4c64b2`; destination is COE #26 head `b382d233ff06c8791b1028bed3c617cc7b670d12`.

| Item | Source | Destination | Finding |
|---|---|---|---|
| ESP32 sketch | `528187f68aaad7d76a690bbf1cbe338165ad3839`, 64,308 bytes | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422`, 18,505 bytes | Different Git blobs |
| ESP8266 sketch | `aa021588b610f928f7af4f5fefb3f32114e6b5ae`, 68,127 bytes | `c8be98f72596681e36a3ad1f8939bf8046c96887`, 18,394 bytes | Different Git blobs |
| License | `BlazePwifi/LICENSE` blob `1ee55b94183417be977ca287cd7391f9a6f7e721` | `Pisowifi/LICENSE` same blob | Pisowifi license match only |
| Notice / Hardware license | Source `BlazePwifi/NOTICE.md` absent | `Hardware/LICENSE` and `Hardware/NOTICE.md` absent | Hardware licensing scope unresolved |
| Test inventory | `tests/`: 46 scripts (8 Python, 38 shell); board-local: 22 Python labs (9 ESP32, 13 ESP8266) plus one shared extraction helper | `Hardware/tests/test_firmware_hardening.sh`: one shell file, blob `f921c56cecc19cab1989507b9b4ade1f45dac54e`, 4,118 bytes | Import completeness and test equivalence NOT established |

The source legacy `v05_firmware_hardening_test.sh` blob `41211b2c110ab409f6d9d1812ef12fda73b13211` and the destination shell test both still require positive `response_sig`, `|register|` and `|poll|` markers. Current #327 firmware deliberately remains default-deny for poll admission and coin disposition. The inherited positive-presence assertion is therefore not a valid acceptance contract. The destination test is not equivalent to the 22 board-local labs and does not independently verify current #327 behavior.

COE #26 still has five workflows queued with zero jobs:
- case-collision;
- Windows SoftTimer;
- Hardware/shared contracts;
- Rental; and
- Pisowifi.

No destination file was copied, moved, overwritten, staged, rebased, cherry-picked or merged. The matching Pisowifi license does not establish the Hardware subtree license. Migration remains BLOCKED.

## 4. Other current exact-head role/CI reconciliation

| Role / PR | Current exact head | Evidence and disposition |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS, scoped. CORE continuation retains ownership |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | [#43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [#43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) SUCCESS, scoped; no physical Android acceptance |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS, scoped; native COM/serial acceptance not established |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS, scoped |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No PR-triggered run returned; base Master SHA `b1ca02e2087f3b1a7169ceab9c34e52646e700df` predates UTC11 Master work |
| HARDWARE #327 | `82fef49d945aeb64da76e89ef12126784a4c64b2` | Focused quarantine [#44510401511](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44510401511) PASS; relay/output [#44510401561](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44510401561) PASS; Full [#44510401548](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44510401548) FAIL at QA-owned `Missing poll signature check`. Thirteen firmware/platform targets and Android PASS; downstream simulation/signing/publishing skipped |
| RELEASE #291 | `6ce1ee152d49de330ed0f31c3786799284545474` | Windows [#44516920755](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44516920755) FAIL at shared handover freshness; BlazePwifi [#44516920733](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44516920733) QUEUED; ESP32 [#44516920957](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44516920957) QUEUED. Log says source/workflow changes are newer than `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md`; build/publisher skipped. The PR description and earlier UTC11 issue checkpoint cite older heads |
| COE RELEASE #35 | `5047af8b5a8296e06294bbda6bf42a6baea2294d` | Shared [#44465377784](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44465377784) PASS; case [#44465377781](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44465377781) PASS; sandbox [#44465377807](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44465377807) FAIL closed because Bubblewrap is missing after 14/14 host preflight |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | [#44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and [#44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) SUCCESS; synthetic receipt-v1 vectors only |

HARDWARE #327's PR description still names an older API head `47eceaf2...`; the current PR API head and latest Hardware role lock are `82fef49d...`. RELEASE #291's latest PR API head is `6ce1ee...`, while the #172 UTC11 role lock reports `19998bc7...`; its current Windows run is newer and fails at the handover gate. Master does not rewrite Hardware or Release-owned handovers.

## 5. Master changes and verification

UTC11 commits on the existing Master branch:
- Architecture §6.9.1 clarification: [ebe5f851](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/ebe5f851d8f259007df6a945ea60f244f8da46f0).
- Regression assertion in `test_architecture_contracts.py`: [f30430b3](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/f30430b3c2c455b90c221ce7abf8c1c4374a4b4a).
- Integration matrix and current role refs: [d9b3cdb5](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/d9b3cdb55c5f16da732aaafb78365c427f2eb744).
- Role assignment refresh: [b020132c](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/b020132c4f016816c1c0625e7fbecfdb4dc0d9ab).
- Routing hold: [462d18f0](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/462d18f0f5d4c4dfd30bd47504a1ae5254cd496e).
- Audit summary refresh: [72f6b796](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/72f6b796fc6b09a5e92903da33fc760980b9c1ff).
- Exact Hardware provenance additions: [32c1124d](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/32c1124d20df6c0679bab840043f5de8c9096106), [33e630c6](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/33e630c68bbe482488b0a61e8b676b62dfbdf000), [e6c56b1e](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/e6c56b1e00c0606497f81e6cf5dbe009a3eb5be7).

**Local targeted check:** five Python assertions over the new site-scope contract text passed. This validates the new contract wording only; it is not the repository's full Master suite.

**Not run:** the full `coordination/phoenix` Python suite. Direct `git ls-remote` failed because the execution runtime could not resolve `github.com`; no local repository checkout was available. Master PR #288 returned no PR-triggered Actions runs. Source/tree inspection and role CI are not represented as Master-suite passes.

## 6. Governance, access and production boundary

- Experiments `main`, development and COE `main` branch objects report `protected=false`; both repositories' rulesets endpoints return empty arrays. Effective protection/required-check enforcement needs administrator verification.
- Experiments `AGENTS.md` was read. Its linked Cloud Artifact Policy and Storage Handover could not be retrieved through available GitHub/web surfaces. COE root `AGENTS.md` returned 404.
- The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not found in the current Files Library search, and no Google Drive connector is exposed in this runtime. Older v5–v7 snapshots were not substituted. No private registry contents or identifiers were published.
- No subsystem source branch, destination source, financial state, signer, secret, customer device or payment system was changed.
- No merge, release, tag, signing, publication, hardware flash, production migration, physical power-cut test or soak was performed.

## 7. Owner actions

1. **PHX-CORE + COE integration owner:** select the durable site-prefix authority and distribution semantics; keep the separate CORE continuation as sole CORE implementation owner.
2. **PHX-RELEASE:** reconcile COE #44 onto current #35 without force-push, only after authority is agreed; update #291 handover/PR/checkpoint to exact head `6ce1ee...` and resolve the current freshness gate in Release-owned files.
3. **PHX-QA:** independently test same-site prefix sharing, distinct-site separation, concurrent first boot, persistence/restore and fail-closed UCI failures; replace the obsolete positive poll-signature fixture with negative/default-deny tests.
4. **PHX-HARDWARE:** retain fail-closed behavior and refresh #327 PR description to current `82fef49...`; no target validation until authorization.
5. **PHX-INFRA:** provide an authorized disposable Bubblewrap runner; do not use privileged namespace setup or unsandboxed fallback.
6. **COE integration owner:** complete exact per-file provenance, test import/equivalence, Hardware licensing and runnable #26 CI before any staging proposal.
7. **Repository administrator:** verify branch protections and required checks.
8. **Registry custodian:** restore authorized read-only v11/newer-correction access.

**PRODUCTION NO-GO** remains mandatory until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible financial migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently verified.
