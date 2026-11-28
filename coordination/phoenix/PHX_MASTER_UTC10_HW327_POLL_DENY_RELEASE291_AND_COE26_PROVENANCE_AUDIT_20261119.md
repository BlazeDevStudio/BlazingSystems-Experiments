# PHX-MASTER UTC10 — Hardware poll-deny, Release current-head, and COE staging audit

**Updated:** 2026-11-19T10:16:37Z  
**Role:** PHX-MASTER — coordination/phoenix only  
**Task:** #172 / #266 / #288 / COE #26 / HARDWARE #327 / RELEASE #291  
**Disposition:** Master documentation PR-ready · COE migration BLOCKED · PRODUCTION NO-GO

## 1. Live repository identities

| Item | Exact ref |
|---|---|
| Experiments default | `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b` |
| Current development | `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859` |
| Legacy development | `blazepwifi-v0.5.3-development@aad3aade72c1156eecba1fed30907c6d0283b2c5` (not current) |
| Master before this commit | `phoenix/master-coordination@1decd7715c4bac46673f673c49f27bfeca160a4e` |
| Master PR #288 | OPEN / DRAFT, base main @ `f4e8a891...`, 99 changed paths, all under `coordination/phoenix/`; no Actions run returned |
| COE main | `a6513ab4412b4c014eee2863e45cbe32d06cb243` |
| COE #26 | OPEN / DRAFT, `b382d233ff06c8791b1028bed3c617cc7b670d12`, 205 changed files, five workflows QUEUED / zero jobs |

The live ownership manifest is `coordination/phoenix/OWNERSHIP_ROUTES.json`, blob `e4db324315a1b3543fec17a148fbf960170fcb29`. It remains `DRAFT_REVIEW_ONLY`; PHX-MASTER target is null. It was not changed.

## 2. HARDWARE #327 — source contract vs Full validation

Current PR #327 is OPEN / DRAFT at `47eceaf2ccd3cfdc3403df6b1964610bd32ed24f`, based on #326 head `58c558fb6a237935214621adc3dee65a10fe1a51`.

Exact-head CI:
- Quarantine/readback [#44501072485](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44501072485), job `135480685509`: PASS.
- Relay/output [#44501072498](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44501072498): PASS.
- Full [#44501072563](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44501072563), validation job `135480829727`: FAIL, `Missing poll signature check` in the ESP8266 sketch. All 13 firmware/platform targets and Android completed; downstream simulation, update bundle, candidate, signing and publishing were skipped.

At exact ESP8266 source blob `75f62c359bbb69f4f580b7ee0c3875396b12cc7f`, `acceptPollResponse()` sets `insertMode=false`, clears `activeTarget`, and returns `false`; `coinPostDispositionVerified()` also returns `false`. The source comment says `response_sig` is only a derived candidate pending CORE's canonical producer and QA-approved vectors. The source-extracted poll lab is blob `69dbddee4133588940f4c5b53817401db531a8a4`.

Focused quarantine logs report both-board poll-fault labs, including 7/7 fault-marker scenarios and 7/7 existing poll-loop guards, plus EEPROM/config failure-injection cases. They explicitly report `SIMULATED_ONLY=1`, `FINANCIAL_MIGRATION_TESTED=0`, `PRODUCTION_MIGRATION_AUTHORIZED=0`, and `PHYSICAL_POWER_CUT_VERIFIED=0`. This is CI-simulated source evidence, not physical acceptance or financial migration proof.

**Owner action:** PHX-QA replaces the legacy positive poll-signature assertion with source-exact negative/default-deny cases. PHX-HARDWARE retains firmware ownership. Do not add fake signature tokens or weaken firmware.

## 3. COE #26 exact Hardware migration comparison

Source tree at #327 contains 21 board-local Python labs (9 ESP32, 12 ESP8266). COE #26 Hardware contains four blobs: README, two sketches, and one generic shell test.

| File | Experiments #327 source blob | COE #26 destination blob |
|---|---|---|
| ESP32 sketch | `1e720d3b2fc76e348ff77e347e0d472d38559d04` | `3cc7ec54b476943dc04a8d1af5e2df5fe054e422` |
| ESP8266 sketch | `75f62c359bbb69f4f580b7ee0c3875396b12cc7f` | `c8be98f72596681e36a3ad1f8939bf8046c96887` |

Neither pair is byte-identical. Destination test `Hardware/tests/test_firmware_hardening.sh`, blob `f921c56cecc19cab1989507b9b4ade1f45dac54e`, asserts positive `response_sig`, `|register|`, and `|poll|` markers and calculates synthetic SHA-256 signature strings. This is not equivalent to the 21 source board labs and conflicts with current deny-only poll/disposition functions.

License readback:
- Source `experiment/openwrt/BlazePwifi/LICENSE` and destination `Pisowifi/LICENSE` match blob `1ee55b94183417be977ca287cd7391f9a6f7e721`.
- Destination `Hardware/LICENSE` and `Hardware/NOTICE.md` are absent.
- Source `experiment/openwrt/BlazePwifi/NOTICE.md` is absent.
- Matching Pisowifi license does not replace explicit per-file Hardware scope and provenance review.

COE #26 exact-head workflows remain five QUEUED / zero jobs: case collision `43096752609`, Windows SoftTimer `43096752632`, Hardware/shared `43096752800`, Rental `43096752563`, Pisowifi `43096752557`. No destination build/test execution is established. No copy, move, overwrite, staging edit or migration proposal was made.

## 4. RELEASE #291 — current-head CI regression

Current PR #291 is OPEN / DRAFT at `ffe4ea8f5eabe23628827e186ebb3f92c9cfcaaf`.

- Windows [#44503871056](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44503871056): handover PASS; `build-windows` job `135490397157` FAIL; publisher skipped. Log: `The variable '$buildWorkflow' cannot be retrieved because it has not been set.`
- Current `negative-selftest.ps1` blob is `8b69174bf519154e43f7e12e4a9fa2c0e75d350f`; its only `$buildWorkflow` occurrences are reads at lines 115, 119 and 138; there is no assignment anywhere in the file. PowerShell StrictMode makes the missing binding fatal.
- BlazePwifi run [#44503871218](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44503871218) ended CANCELLED at `2026-11-19T10:19:37Z`; it is not a full pass. Validation, Android, ESP32/ESP8266, target builds and update bundle had partial successful jobs; two simulation jobs were still in progress before cancellation; signing/publishing remained skipped.
- ESP32 compatibility [#44503871277](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44503871277) passed both configured core versions 3.3.13 and 4.0.0.

The PHX-RELEASE UTC10 role lock is already working on a separate provenance-snapshot consistency regression. Master does not edit release-owned files.

## 5. Other role and release CI

| Role / candidate | Exact ref | Current evidence |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | #42698139210 PASS, scoped; CORE owner retains source work |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | #43653329235 and #43653329229 PASS, scoped |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | #42462978704 PASS, scoped; native COM acceptance NOT TESTED |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | #43633486963 PASS, scoped |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No current-head run returned |
| COE CORE #45 | `9d76a134c1f6512aa40c20ec4d247306a71a8cce` | #44295049727 and #44295049903 PASS; synthetic receipt-v1 only |
| COE RELEASE #35 | `5047af8b5a8296e06294bbda6bf42a6baea2294d` | Shared #44465377784 PASS; case #44465377781 PASS; sandbox #44465377807 FAIL closed because bwrap is missing (exit 125) after 14/14 preflight tests |
| COE RELEASE #31 | `59ed44d0b911e176f1a95b9cf5585ef811ffd31b` | Shared #44222517238 PASS; case #44222517258 PASS; sandbox #44222517263 FAIL |

Scoped green jobs do not establish combined integration, financial authority, hardware acceptance or production readiness.

## 6. Governance, access and execution limits

- Cleanup issue #266 remains OPEN; its checklist is not evidence of completion or worker notification.
- Experiments main, development, Master and COE main branch objects report `protected=false`; both repository rulesets endpoints return empty arrays. Effective protection/required checks need administrator verification.
- Private Drive registry v11 and newer corrections were not found through Library search; only older snapshots surfaced. No Google Drive connector is exposed. No older registry was substituted; no private contents or identifiers were published.
- Master PR #288 has no current-head Actions run. The full Master Python suite was NOT RUN because no local checkout was available.

## 7. Changes, tests and next actions

**Master changes:** coordination/phoenix documentation only. No subsystem source, release workflow, COE destination file, ownership manifest, private registry record, financial state, signer or hardware was modified.

**Local checks:** pre-commit static assertions verify expected base blobs, manifest immutability, exact source/destination identities, 21 source lab files, the single destination test, deny-only function bodies, the release self-test's unbound variable, and Master-only path scope. These are documentation/source consistency checks, not the full Master Python suite.

**Not tested:** physical hardware, real coin acceptors, real power cuts, financial migration, native acceptance, and 30-device/24-hour soak.

Next:
1. PHX-QA fixes the positive poll fixture with negative/default-deny source tests at exact #327 SHA.
2. PHX-HARDWARE retains the deny-only consumer and refreshes its own handover.
3. PHX-RELEASE fixes the missing `$buildWorkflow` input in its own branch and completes the provenance-snapshot regression with exact-head CI.
4. COE integration owner supplies per-file blob/mode/license/test/toolchain provenance, imports the 21 source labs or reviewed equivalents, and unqueues all five #26 workflows.
5. Repository administrator verifies branch protection and required checks.
6. Registry custodian restores authorized read-only access to v11 and newer corrections.

**PRODUCTION NO-GO** until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak, and owner-authorized release gates are independently verified. No merge, release, flash, secret provisioning, real-payment operation or financial migration occurred.
