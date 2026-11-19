# PHX-MASTER UTC21 — COE #35 hard-link output admission, site ULA, sandbox, and exact-head role CI

**Observed:** 2026-11-19T21:36:25Z  
**Role:** PHX-MASTER · coordination-only  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Pre-change Master HEAD:** `e0e499b4fd8f1e6ae3b15c7a22e3fa12559daf10`  
**Existing PR:** #288 OPEN / DRAFT · base `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**Destination:** BlazeDevStudio/CoinOperatedEcosystem  
**Disposition:** migration BLOCKED · PRODUCTION NO-GO

## 1. Exact refs and ownership

- Experiments default branch: `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Development candidates: `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` and `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- **Control-plane designation conflict:** the opening/current-state text in issue #172 labels v0.5.3 as development and v0.6.0 comparison-only, while later UTC13/UTC15 sections call v0.6.0 the current development reference and v0.5.3 legacy. Both branch refs were read at the exact SHAs above. Master does not choose or promote one; the control-plane owner must correct the canonical designation.
- Master branch: `phoenix/master-coordination@e0e499b4fd8f1e6ae3b15c7a22e3fa12559daf10`.
- COE main: `main@a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- COE integration #26: `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- COE #31 parent: `59ed44d0b911e176f1a95b9cf5585ef811ffd31b`.
- COE #35 release child: docs head `7b9706d898fb5f36c6ed96504aefd04dc59bdc1b`; source/test commit `6f007699a513e46d6d45bfca6693d91c02c03b5e`.
- COE #44 ULA installer: `582fd5d5e83e36b36546ac28534740298ba94af4`, based on older #35 head `1a5be48d2845781b0b07bad39a37f8440cea4d4f`; it is not stacked on current #35.
- Separate COE #27 hardware/shared candidate: `009f70cc2c2775039a5fb072c9d4fdedee76cfc7`; not integrated into #26.
- `coordination/phoenix/OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`; PHX-MASTER destination remains null. No source-owner route changed.

## 2. COE #35 hard-linked output admission — bounded fix verified, stack still blocked

The release-owned generated ImageBuilder wrapper previously accepted a regular firmware candidate with `st_nlink > 1`. A Makefile could hard-link a cached file into the expected target output tree, after which the checksum-manifest scan could describe the aliased payload.

- Test-first RED: [#44617273391](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617273391). The wrapper returned success and wrote a manifest for a hard-linked output.
- Release source/test fix: [`6f007699`](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/commit/6f007699a513e46d6d45bfca6693d91c02c03b5e) rejects firmware candidates with link count greater than one before empty-file validation and checksum-manifest creation.
- Exact docs-head shared run [#44617782050](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617782050), job `135890991067`: `test_generated_wrapper_denies_hardlinked_firmware_output` PASS; **118 packaging/tool tests PASS, 2 intentional skips**. The overall workflow is still FAILURE because the subsequent profile-admission step rejects all 10 appliance profiles without an approved site-scoped RFC 4193 ULA /48. ESP32 and ESP8266 compile jobs were skipped.
- Exact docs-head sandbox run [#44617781877](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617781877), job `135890990425`: host preflight passed; Bubblewrap is absent, so the mandatory runner stops with exit 125. Namespace and sandbox packaging tests were skipped. No privileged install or unsandboxed fallback.
- Case-collision guard [#44617783021](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44617783021): PASS.

This is a bounded release-packager fix with exact-host CI evidence. It is **not** a complete ImageBuilder run, firmware build, signed provenance attestation, hardware acceptance, or release authorization.

## 3. Site ULA and separate #44 candidate

At COE #35 source/test SHA `6f007699...`, `APPROVED_SITE_ULA_PREFIX` intentionally remains `None`. The synthetic `fd12:3456:789a::/48` in unit tests is a fixture only and is not a production site allocation.

The exact #44617782050 profile step rejects all ten profiles with the explicit missing approved site-scoped RFC 4193 ULA /48 error. Do not inject a guessed prefix or reuse the synthetic test value.

COE #44 is a separate first-boot ULA installer draft. Its exact-head shared CI [#44390136309](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136309) and case-collision [#44390136296](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136296) pass; its mandatory sandbox [#44390136327](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44390136327) fails closed because Bubblewrap is unavailable. Its synthetic UCI/first-boot behavior does not establish durable site-wide authority, same-site sharing, distinct-site separation, or restore/upgrade identity. It is based on an older #35 head and was not rebased or merged.

COE #31 parent exact-head evidence: shared [#44222517238](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517238) PASS, case collision [#44222517258](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517258) PASS, mandatory sandbox [#44222517263](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44222517263) FAIL. The parent/child CI does not waive the current #35 site-prefix or runner gates.

## 4. Current role PR and exact-head CI matrix

| Role / PR | Exact current head | Exact-head evidence | Disposition |
|---|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS | Scoped owner CI; CORE remains separately owned |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | [43653329229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329229), [43653329235](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43653329235) PASS | Scoped owner CI |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS | Scoped owner CI |
| HARDWARE #327 | `20c73090f8b3b819e4fb345c336f8e9275feeaaa` | [44612105093](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44612105093) relay PASS; [44612105234](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44612105234) quarantine PASS; [44612105221](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44612105221) Full FAIL | QA-owned positive poll-signature fixture remains stale; firmware stays deny-only |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS | Scoped native COM QA |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No exact-head workflow run returned | Draft base is stale relative to current Master; QA must refresh/re-run |
| RELEASE #291 | `3bffd9d14de42abf2c2f6079632e0348127ad025` | [44612586860](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44612586860) ESP32 PASS; [44612586896](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44612586896) BlazePwifi PASS; [44612586795](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44612586795) Windows FAIL | PISONET-owned `negative-selftest.ps1` reads uninitialized `$buildWorkflow`; publisher skipped |

The Windows failure log confirms handover freshness passed and package-parity checks passed before the PISONET-owned negative self-test failed. PISONET owns that test path; RELEASE must rerun its consumer after the owner fix.

## 5. COE destination status and migration gate

- COE #26 remains OPEN / DRAFT at `b382d233...`; five unique PR workflows are QUEUED with zero jobs. No destination acceptance is established.
- COE #27 remains a separate draft; its two scoped runs [43079646264](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43079646264) and [43079646393](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/43079646393) pass, but it is not part of #26.
- The prior exact source/destination firmware, test-identity, license/NOTICE and import-completeness gaps recorded in UTC20 remain open. The hard-link packager correction does not resolve those migration gaps.
- No copy, move, overwrite, rebase, cherry-pick, merge, or destination staging was performed.

## 6. Governance, registry, and execution limits

Branch API readback reports `protected=false`, `protection.enabled=false`, and required-status-check enforcement `off` for Experiments `main`, v0.6.0 audit-foundation, v0.5.3 development, `phoenix/master-coordination`, and COE `main`. Both repositories' rulesets endpoints returned empty lists. No settings were changed; repository administrators must establish and independently verify required protections/checks.

The canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not surfaced by Library search; only older snapshots appeared. No Google Drive connector was exposed, no older snapshot was substituted, and no private registry contents were copied or published. The AGENTS-linked Cloud Artifact Policy / Storage Handover could not be retrieved through the connected GitHub file wrapper (no file metadata/SHA returned); no Drive write was attempted.

Master exact-head Actions: no runs returned. Full Master Python suite: NOT RUN; the local clone attempt failed because the runtime could not resolve `github.com`. The role CI results above are not a Master-suite pass. No physical hardware tests, real power cuts, device soak, firmware flash, signing, secret provisioning, payment operation, migration, or release occurred.

**Final status: MIGRATION BLOCKED / PRODUCTION NO-GO.**

## 7. Next owner actions

1. **PHX-CORE / COE integration authority:** define and approve the durable site-scoped ULA authority and its persistence/restore contract; do not use the synthetic test prefix.
2. **PHX-INFRA:** provide an authorized disposable, no-secret runner with pre-provisioned Bubblewrap and working unprivileged user namespaces; no fallback.
3. **PHX-QA:** independently review the #35 hard-link admission test at source/test SHA `6f007699...`; replace the obsolete positive poll-marker assertion with negative/default-deny behavior tests on the current #327 source.
4. **PHX-PISONET:** fix its owned `$buildWorkflow` self-test variable; **PHX-RELEASE** reruns #291 afterward.
5. **COE integration owner:** keep #26 blocked until per-file source/test/license/toolchain provenance and executable exact-destination CI are complete.
6. **Repository administrators:** enable and verify branch protection and required checks on the protected source and destination branches.
7. **Registry custodian:** restore authorized private v11/newer-correction access.
8. **PHX-MASTER / control-plane owner:** resolve the contradictory v0.5.3 vs v0.6.0 development designation in issue #172.

**No subsystem source ownership changed.** The separate CORE continuation retains CORE implementation ownership.
