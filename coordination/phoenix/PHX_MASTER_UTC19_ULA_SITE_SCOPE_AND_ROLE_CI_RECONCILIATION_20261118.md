# PHX-MASTER — UTC19 ULA site-scope and role/CI reconciliation

**Audit timestamp:** 2026-11-18T19:35:13Z  
**Role:** PHX-MASTER — coordination, architecture/interface contracts, migration provenance and integration matrix only  
**Disposition:** OPEN / DRAFT / UNMERGED · **PRODUCTION NO-GO**

## 1. Authority and live source pins

Read this activation: uploaded `00_MASTER_PROJECT_PHOENIX(1).txt`; latest Library `README_FIRST(10).md` and `COMMUNICATION_PROTOCOL(10).md`; Experiments root `AGENTS.md` blob `d8777e3b58efc41caa5aa3c969c932aee9103d5f`; repository README blob `feb909e3f74ffb7b5b22df50399ccd127ada3b95`; current control-plane issue #172, cleanup issue #266, Master PR #288, role routing manifest, role PRs/CI, COE main and integration PR #26. The AGENTS-linked cloud artifact policy and storage handover could not be read through the current GitHub connector path; this is not treated as evidence that the restricted Drive mirror is empty.

| Ref | Exact SHA / state |
|---|---|
| Experiments default `main` | `f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Experiments development/audit branch `blazepwifi-v0.6.0-audit-foundation` | `2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Experiments Master `phoenix/master-coordination` before this commit | `d2cb869d76b1e0ef694a8b9ce6bb7c0d427d4243` |
| COE default `main` | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE integration PR #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` |

Master PR #288 is OPEN / DRAFT, base `main@f4e8a891...`, with 86 changed paths; an exact changed-filename read found all 86 under `coordination/phoenix/` and zero outside. No PR-triggered workflow run was returned for the Master head. The routing manifest is unchanged at blob `e4db324315a1b3543fec17a148fbf960170fcb29`, status `DRAFT_REVIEW_ONLY`, PHX-MASTER target `null`. No source ownership or migration route is changed.

## 2. New architecture contract finding — COE #44 ULA site identity

Architecture contract §6.9 requires a locally assigned RFC 4193 `fd00::/8` /48 that is durable across reboot/upgrade/restore, unique between independent sites, and **shared by all devices on the same LAN/site**. It is installation/site identity, not a reusable hardware-profile value.

COE Release child PR #44 is OPEN / DRAFT / UNMERGED at `0ad58f0388dc8e4e9309e64098b439bf368a3558`, based on current Release parent #35 at `1a5be48d2845781b0b07bad39a37f8440cea4d4f`. Its current patch adds a first-boot script that obtains a random 40-bit ID from `/dev/urandom`, generates an `fd...` /48, validates the syntax, and persists `network.globals.ula_prefix` through UCI. Tests cover generic-image omission of a baked prefix and preservation of unrelated pending network changes when the ULA commit fails.

That is a useful correction to the invalid shared placeholder in the earlier packager, but **per-install random generation alone does not prove same-site sharing across multiple independently installed appliances**. Two appliances at the same site could generate different /48s unless a site-scoped authority/assignment mechanism coordinates them. The Release checkpoint itself leaves site-level multi-appliance ULA authority pending.

**Master decision:** retain §6.9 unchanged as the normative contract; add §6.30 clarifying this acceptance gap. Do not approve #44 as contract-complete until the owner defines how one site identity is assigned/reused by all same-site appliances and how independent sites remain distinct. No Master source implementation is requested.

Required evidence from owners:
1. A site-scoped authority or explicit provisioning input that supplies the same prefix to every appliance on one LAN/site; no globally shared static fallback.
2. Exact-source tests showing two appliances assigned to one site receive the same /48, two independent sites receive distinct /48s, and reboot/upgrade/restore preserve the assigned value.
3. Missing, malformed, unavailable or conflicting authority must fail closed before network services consume a prefix.
4. PHX-QA independently verifies the same exact candidate SHA; PHX-HARDWARE validates target behavior only after authorization.

Ownership: PHX-RELEASE implements its packager/first-boot portion; COE integration owner controls destination staging; PHX-CORE/COE owners define site authority and provisioning semantics; PHX-QA independently verifies; PHX-HARDWARE owns target validation. PHX-MASTER owns only the contract and integration gate.

### COE #44 exact-head CI

| Workflow | Run | Result |
|---|---:|---|
| Shared Hardware/contracts | [44380663938](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44380663938) | SUCCESS |
| Case-collision guard | [44380663872](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44380663872) | SUCCESS |
| Mandatory ImageBuilder sandbox | [44380664237](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44380664237) | FAILURE |

The mandatory sandbox job ran 14/14 host-preflight tests successfully, then exited 125 because `bwrap` is not installed on the runner. No unsandboxed fallback was used. These results do not establish site-level ULA behavior or target acceptance.

## 3. Hardware #327 exact-head reconciliation

Hardware #327 remains OPEN / DRAFT / UNMERGED, branch `phoenix/hardware-prepoll-edge-abort-20261119`, docs head `0a26468022d25746fdc38525c0c0979da098f6d4`, exact source/test SHA `e774420c3404141ffe4ec7b9c002c14d3c2286b8`, based on #326 `58c558fb6a237935214621adc3dee65a10fe1a51` / #323 `988904e8bcd058b62a9fac4aa6319a9b7c5b2470`.

The current patch:
- Compares the ISR edge sequence again after the quiet-drain window and before synchronous HTTP poll dispatch.
- On a newly captured edge, latches the fault and persists the marker before any poll request.
- Adds a same-boot RAM latch after ambiguous NVS/EEPROM set/commit/reopen/readback failure, preventing a dirty cache from being treated as durable or retried as if the write were certain.

Exact docs-head focused CI:
- Quarantine/readback [44373742439](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373742439): SUCCESS.
- Relay/output [44373742382](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373742382): SUCCESS.
- Full build [44373742348](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373742348): FAILURE.

The Full validation job fails at the inherited QA-owned `Missing poll signature check` in the ESP8266 sketch. The Android job separately cannot resolve `com.google.protobuf:protobuf-gradle-plugin:0.8.3` from the configured repositories. All 14 firmware/platform target jobs completed SUCCESS; downstream simulations, update bundle, signing, candidate and publishing jobs were SKIPPED. Preserve the firmware's deny-only poll/coin disposition; do not add synthetic positive signatures to satisfy the stale fixture.

The source-extracted dual-store test proves current-boot denial only when both stores fail; reboot durability is NOT ESTABLISHED. These host/fake-I/O runs are SIMULATED / CI VERIFIED only, not physical ISR, acceptor, relay, flash or power-cut acceptance.

## 4. Live role-owner and CI matrix

| Owner | Current candidate / exact head | Exact-head evidence and next action |
|---|---|---|
| PHX-MASTER | #288 `d2cb869d...` before this commit | 86 changed paths, all coordination-only; no Master CI run returned. |
| PHX-CORE | Experiments #252 `c82705f2de865c89ab733b10efa84f26f56a5cc4`; COE #45 `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | Experiments [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) SUCCESS (scoped). COE #45 [44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) and [44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) SUCCESS (scoped contract/overlay checks). CORE ownership remains separate; Master did not edit CORE. |
| PHX-RENTAL | #289 `68928774d0d7cf65adb26bc6b54199a3159d066c` | [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) and [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229) SUCCESS (scoped). |
| PHX-PISONET | #255 `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) SUCCESS (scoped build); native COM/device acceptance is not established. |
| PHX-HARDWARE | #323 `988904e8...` → #326 `58c558fb...` → #327 `0a264680...` (source/test `e774420c...`) | Focused #327 labs PASS; Full [44373742348](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44373742348) FAILS at QA poll fixture and Android dependency resolution. Keep draft; same-SHA independent QA pending. |
| PHX-QA | #290 `5c29d15994cee1279058f1eca12f2a3180704292`; #292 `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | #290 [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) SUCCESS for build/handover, but its workflow does not invoke NativeComInterfaceHandleLab. #292 has no workflow runs and is based on stale Master `b1ca02e2087f3b1a7169ceab9c34e52646e700df`, not current `d2cb869...`. QA must rebase/retest #292 and replace the positive poll-signature fixture with negative deny-behavior tests. |
| PHX-RELEASE | Experiments #291 `691ed55dbe39a79a88eac45f6eebff81cee5e628`; COE #35 `1a5be48d...` → child #44 `0ad58f03...` | #291 [44353380470](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44353380470) SUCCESS, privileged publisher skipped. COE #35 shared/case [44370198378](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44370198378) / [44370198334](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44370198334) SUCCESS; sandbox [44370198386](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44370198386) FAILS for missing bubblewrap. Child #44 shared/case PASS; sandbox fails for the same runner limitation. Resolve site ULA authority and obtain an authorized bubblewrap-capable runner; no privileged install or unsandboxed fallback. |
| COE integration owner | #26 `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows remain QUEUED / zero jobs. Existing exact provenance audit remains current because #26 head is unchanged: source/destination firmware blobs differ, source board labs are not imported/invoked, destination test identity is not source-equivalent, and Hardware license/NOTICE scope remains unresolved. No migration proposal. |

## 5. Cleanup, governance and restricted registry

- Cleanup issue #266 remains OPEN, last updated 2026-11-14. Its checklist still references historical PRs (#248/#252, #240, #238/#255, #239/#254, #242) and older source snapshots; refresh its owner/task pins before using it as a current cleanup completion record. No mass move or cleanup was attempted.
- Branch-object reads report `protected=false` for Experiments `main`, development `blazepwifi-v0.6.0-audit-foundation`, Master, and COE `main`; both repository rulesets reads returned empty arrays. Repository administrator must configure and independently verify required branch protection/status checks.
- The exact private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not found by exact-title Library search. The current tool surface exposes no Google Drive connector; older v3–v7 Library snapshots were not substituted. No private registry content or IDs were published.
- The AGENTS-linked cloud artifact policy and storage handover could not be read using the current GitHub connector path; do not treat this as a successful Drive readback.
- CORE remains untouched under its separate continuation. No competing CORE worker, source takeover, merge, rebase, release, signer provisioning, secret, hardware flash, physical test or real-payment operation occurred.

## 6. Verification and disposition

**Source/tree inspection:** completed for current refs, Master docs, routing manifest, role PRs, Hardware #327 patch, COE #44 patch, and exact-head CI/job logs.  
**Actual GitHub CI:** role results are linked above.  
**Master-specific tests:** no PR-triggered Master workflow run returned; the full Master Python suite was NOT RUN because no repository checkout/test runner is exposed in this run.  
**Authoring assertions:** 14/14 bounded metadata/ownership/CI consistency assertions passed before commit; these are not the Master Python suite.  
**Physical acceptance:** NOT TESTED.

**Next exact action:** PHX-RELEASE and the COE integration owner must define a site-scoped ULA assignment/authority that gives all appliances on one LAN the same /48, preserves it across reboot/upgrade/restore, and distinguishes independent sites; PHX-QA must independently verify that exact candidate. Keep #44 and #26 DRAFT / NO-GO until then.

**Final status: PRODUCTION NO-GO.** Independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates remain mandatory.
