# PHX-MASTER UTC22 — cross-owner path-overlap and live CI audit

**Updated:** 2026-11-22T22:38:20Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Mode:** Strict NO CODEX · coordination-only · PRODUCTION NO-GO

## 1. Exact repository state

- Experiments `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`.
- Experiments development `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5`.
- Master `phoenix/master-coordination@1675fe82b12b5309f12df12ec1a4ab2d979d6ac4`.
- Master PR #288: OPEN / DRAFT / UNMERGED, base main, 176 changed paths.
- COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243`.
- COE integration #26 `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN / DRAFT / FROZEN.
- `OWNERSHIP_ROUTES.json` blob `e4db324315a1b3543fec17a148fbf960170fcb29`, 11 routes, `DRAFT_REVIEW_ONLY`, PHX-MASTER target `null`.

Master #288's 176 changed filenames are all under `coordination/phoenix/`; exact filename-set comparison found zero overlap with the selected owner PRs. No subsystem source or COE destination path was changed by Master.

## 2. Exact-head owner CI

| Owner / PR | Exact head | Exact-head CI | Classification |
|---|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | [#42698139210](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42698139210) PASS | Scoped build only |
| RENTAL #328 | `0e0da62acd47c6a1ce287f8a30fc700d603fa070` | [#44782114390](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114390) FAIL; [#44782114384](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114384) and [#44782114393](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44782114393) PASS | Handover freshness fails; ESP32 compile lacks `mbedtls/sha256.h` |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | [#42462978704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/42462978704) PASS | Windows Release only; no physical adapter acceptance |
| HARDWARE #283 | `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30` | [Quarantine #45057637178](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45057637178) PASS; [Full #45057637196](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45057637196) FAIL | ESP32 compile lacks `mbedtls/sha256.h` |
| HARDWARE #327 | `fadac4ed3bc837cf729753264b9427fa3fd312b9` | [Quarantine #45029851960](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029851960) and [Relay #45029852010](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029852010) PASS; [Full #45029851959](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45029851959) FAIL | Full fails at QA-owned Controller protocol parity |
| HARDWARE #343 | `dfeff7d5f63e699de7bc296c7641f2493f1e0e13` | [Quarantine #45062595339](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062595339) and [Relay #45062595335](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062595335) PASS; [Full #45062595995](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062595995) FAIL | Full fails at inherited poll-signature assertion |
| HARDWARE #341 | `4368435ad762d507a907e72a9c739c7bddbc3a81` | [Quarantine #45060591705](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45060591705) PASS; [Full #45060591630](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45060591630) FAIL | Full fails at same QA-owned assertion |
| HARDWARE #344 | `accac7b383d2819ba13af43cb699ec5081cd9e4a` | [Quarantine #45074396465](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45074396465) PASS; [Full #45074396411](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45074396411) FAIL | Full fails at same QA-owned assertion |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | [#43633486963](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/43633486963) PASS | Windows handover/build only; does not execute NativeComInterfaceHandleLab |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No workflow runs or combined statuses | Base `b1ca02e2087f3b1a7169ceab9c34e52646e700df` is stale vs current Master `1675fe82b12b5309f12df12ec1a4ab2d979d6ac4`; historical host tests are not current integration |
| RELEASE #291 | `cb5e5450a4fc2afc7f38cf426e51b390859a1dd0` | [Windows #45071305811](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45071305811) and [Full #45071305854](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45071305854) FAIL at handover freshness; [ESP32 compatibility #45071305891](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45071305891) PASS | Aggregate release blocked |
| COE #26 | `b382d233ff06c8791b1028bed3c617cc7b670d12` | Five workflows QUEUED, zero jobs/statuses | FROZEN; no integration acceptance |
| COE RELEASE #35 | `ed2ada0dfd2ac84669bbd84edee91aa873bbeb32` | [Case #45077987734](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45077987734) PASS; [Sandbox #45077987754](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45077987754) FAIL; [Shared #45077987795](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/45077987795) FAIL | Bubblewrap absent (exit 125); all 10 appliance profiles fail closed without approved site ULA /48 |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | [Overlay #44295049727](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049727) and [case #44295049903](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44295049903) PASS | Scoped candidate only |
| COE Stage 5.1 #49 | `aeb8ff11b2f5db9a5f86280ab62ab988245f3919` | [Case #44646341992](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341992) and [Stage 5.1 #44646341873](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341873) PASS; [Shared #44646341922](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44646341922) FAIL | Separate candidate; shared CI ESP32 compile fails |

Master #288 exact-head Actions and combined statuses both return zero. Full Master unittest discovery and `verify_coordination.py` were NOT RUN.

## 3. Cross-owner path-overlap inventory

Static exact changed-filename sets for 16 open PRs (12 Experiments, 4 COE) produced 14 pairwise overlap relationships. These are review/stacking signals, not proof of a textual conflict or permission to merge.

### A. Shared BlazePwifi handover cluster

CORE #252, PISONET #255, QA #290 and RELEASE #291 all touch:

- `experiment/openwrt/BlazePwifi/PROJECT_HANDOVER.md`
- `experiment/openwrt/BlazePwifi/docs/handover/CHANGE_LEDGER.md`
- `experiment/openwrt/BlazePwifi/docs/handover/CURRENT_STATE.md`

Six pairwise PR overlaps exist across the four owners. RELEASE #291 has 27 changed paths: 22 RELEASE, 3 CORE and 2 PISONET. Its three shared handover files require explicit CORE/PISONET review before #291 is considered isolated RELEASE work. Do not assign these files to one role by inference.

### B. PISONET / QA test overlay

PISONET #255 and QA #290 also share:

- `experiment/windows/BlazePisonet-SoftTimer/tests/NativeComInterfaceHandleLab/NativePulseCaptureCases.cs`
- `experiment/windows/BlazePisonet-SoftTimer/tests/NativeComInterfaceHandleLab/Program.cs`

The Windows workflow does not execute this native lab; its tests remain NOT RUN on the current QA head.

### C. Separate Hardware source lineages

- #283 (base main), #327 (base #326) and #343 (base #342) touch both ESP32 and ESP8266 sketch files.
- #327 and #343 additionally share `poll_loop_blocking_inhibit_lab.py`.
- #327 and #341 share `poll_fault_dual_store_lab.py` and `poll_fault_dual_store_lab_fixtures.py`.
- #327 and #344 share those two files plus `firmware_lab_source.py`.
- #341 and #344 share the two dual-store lab files; this is expected parent/child lineage because #344 is based on #341.

Keep #283, #327→#343 and #338→#339→#341→#344 distinct. The #327 vs #341/#344 shared lab files require owner reconciliation before stack selection. Do not weaken default-deny to satisfy the inherited positive poll-signature assertion.

### D. COE destination candidates

- COE #26 and #35 share `.github/workflows/hardware-ci.yml`, `tools/package_appliance_firmware.py`, and `tools/test_package_appliance_firmware.py`.
- COE #26 and #45 share `Pisowifi/MIGRATION_MAP.md`, `Pisowifi/SOURCE_INTAKE.json`, and `Pisowifi/tests/run_focus.sh`.
- COE #49 has no changed-path overlap with #26 in the current filename sets.

These are separate candidates, not combined acceptance. Keep #26 FROZEN until provenance, tests, imports, licenses/NOTICE and terminal exact-head CI reconcile.

## 4. Verification method and limits

- Evidence source: live GitHub branch refs, PR heads, exact changed-filename lists, workflow runs, failed-job steps/logs and current Master documents.
- Static comparison: 16 PR path sets; 14 pairwise overlaps; zero Master-to-owner path overlaps.
- This is a static path/CI audit, not a repository unit-test execution. No local authenticated checkout was available for Master unittest discovery or `verify_coordination.py`.
- `AGENTS.md` storage policy and public recovery handover were read from BlazeDevStudio/BlazingSystems (policy blob `5e503925750c4e511314e4b7624579d82f60aae2`; handover blob `a15f14cb3baf46424b820e1a921462794422f06b`). No Drive artifact was created or changed.
- Canonical private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not accessible through the current Google Drive/connector surface. Library search exposed older v3–v7 snapshots only; none was substituted. No private registry contents or IDs were copied to GitHub.
- Classic branch-protection detail returns HTTP 403 for Experiments main/development and COE main; rulesets endpoint returns an empty list. Effective required-check policy remains ADMIN-VERIFICATION-REQUIRED.

## 5. Cleanup and release disposition

- Cleanup issue #266 remains OPEN. Master cleanup is PARTIALLY ADDRESSED, not complete: this path-overlap inventory is now available, but duplicate/dead-code and canonical-module review remains unfinished. Do not check the Master track complete.
- Routing manifest remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, Master target null.
- No source branch, COE destination, migration staging, license, artifact, secret, payment system, firmware device or physical test was modified or exercised.

**PRODUCTION NO-GO** remains mandatory until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device 24-hour soak and explicit owner-authorized release gates have independently verified evidence.

## 6. Next owner actions

1. CORE/PISONET/RELEASE: reconcile the three shared BlazePwifi handover files; RELEASE must obtain explicit review for its 3 CORE and 2 PISONET paths.
2. HARDWARE: reconcile sketch and lab-file lineages before any merge; preserve fail-closed behavior.
3. QA: execute NativeComInterfaceHandleLab on exact #290, refresh #292 against current Master, and replace the stale poll-signature assertion with source-linked negative/default-deny tests.
4. RENTAL: fix the Mbed TLS header/toolchain mismatch and refresh the required handover after source changes.
5. COE integration: keep #26 frozen; reconcile #26/#35/#45 shared paths and exact provenance/test/license evidence before staging.
6. Repository administrators: verify effective branch protection and required checks.
7. Registry custodian: restore authorized v11/newer-correction access.
8. Human runner: execute Master unittest discovery and `verify_coordination.py` in an authenticated checkout.

No merge, release, signer provisioning, hardware flash, customer deployment, real payment operation, financial migration or physical hardware test occurred.
