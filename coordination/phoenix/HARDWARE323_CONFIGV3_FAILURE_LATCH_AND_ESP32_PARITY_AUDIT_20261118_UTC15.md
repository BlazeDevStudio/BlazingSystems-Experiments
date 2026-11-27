# HARDWARE #323 ConfigV3 failure-latch and ESP32 parity audit

**Snapshot:** 2026-11-18 UTC15  
**Role:** PHX-MASTER — coordination/architecture/integration provenance only  
**Disposition:** BLOCKED / OPEN-DRAFT / PRODUCTION NO-GO  
**Source candidate:** [Experiments PR #323](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/323)  
**Destination candidate:** [COE integration PR #26](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/pull/26)

## Executive decision

The previous boot-polarity workflow-wiring defect is corrected at the current #323 head: the workflow uses a block scalar and the Actions log shows the relay lab and boot-polarity lab executed as separate Python commands. The new boot lab is therefore genuinely running, but it fails at the simulated EEPROM commit-failure case:

`Assertion `journalRecoveryRequired` failed`

Do not mark the boot-polarity regression green. The exact ESP8266 source visibly routes failed default-configuration persistence through `latchConfigPersistenceFailure()`, which sets `journalRecoveryRequired=true`; the source-extracted test reports that the expected latch is absent. This contradiction is unresolved. It may be a harness/extraction/stub mismatch or a source-path defect not yet isolated. Master does not choose between those explanations without a reproducible trace.

A second board-parity gap is present: the ESP32 sketch does not contain the ESP8266 ConfigV3 unknown-polarity gate. Its Preferences reads default relay/LED polarity to active-high when keys are absent, then `setup()` calls `configureRuntimePins()` before `setupPortal()`. That routine preloads logical OFF using the default polarity and enables OUTPUT. For active-low hardware, the first LOW write can be an active level. The local setup page exposes polarity fields, but that does not protect the earlier first-boot output configuration. This is a source-level safety gap, not a physical observation.

## Exact source and test identities

| Item | Exact identity | Observation |
|---|---|---|
| #323 branch HEAD | `bc0447f013698a2e45c154b0ae69a098b0e75fe5` | OPEN / DRAFT; child of #322 |
| Parent #322 | `50d93e0de3d682550b6f02fb43484e76ad9c7e08` | Existing Hardware-owned parent |
| ESP8266 firmware | blob `283dbe329a5445931cc9fe7096561a68b9c8bf62` | ConfigV3, checksum, local polarity-known state and fail-closed latch present |
| ESP8266 boot lab | blob `25fe2f6040f59c4fa74c9d88c821aed9804d3fe2` | Executes V1/V2/V3, missing/corrupt/future-schema and persistence-failure assertions |
| Relay-output workflow | blob `1140daf71d5218c9c58cdf74ae4cc3ab3822c51a` | Separate block-scalar commands; boot lab is invoked |
| ESP32 firmware | blob `bd74b11c1496b0943404ff387ee72bb45d4743e5` | No ConfigV3 / outputPolarityKnown / outputPolarityConfigured equivalent |

### ESP8266 failure path visible in source

At the exact ESP8266 blob:

- `loadCfg()` begins EEPROM and determines whether the required region is available.
- On erased/missing configuration, it calls `defaults()`, then `saveCfg()`.
- If commit/readback fails, it calls `latchConfigPersistenceFailure()`.
- That latch clears output-polarity authority, keeps GPIO configuration unsafe, disables insertion, clears the active target and sets `journalRecoveryRequired=true`.
- V1/V2 migration failure uses the same latch.

The lab's fake EEPROM returns false from `commit()` when `failCommit` is set. Its failing case resets state, sets `EEPROM.failCommit=true`, calls `loadCfg()`, checks unknown polarity, then expects `journalRecoveryRequired`. The Actions assertion fails at that expectation. The current run proves the test is executed; it does not yet prove which side of the source/harness boundary is wrong.

### ESP32 parity gap visible in source

At the exact ESP32 blob:

- `Config` defaults `relayActiveHigh=true` and `ledActiveHigh=true`.
- `loadConfig()` reads `prefs.getBool("relayhi", true)` and `prefs.getBool("ledhi", true)`; absent keys therefore resolve to active-high.
- `setup()` calls `loadConfig()`, assigns those values, then calls `configureRuntimePins()` before `setupPortal()`.
- `configureRuntimePins()` writes logical OFF using those values and then enables the relay/LED pins as OUTPUT.
- There is no `outputPolarityKnown`, `outputPolarityConfigured`, ConfigV3 version/checksum or unknown-polarity INPUT hold in this ESP32 source.
- The `applyRemoteConfig()` definition has no call site in this file; it is not an authenticated polarity authority.

The local setup form is not a substitute for a boot-time unknown state because runtime pins are configured before the setup portal is started.

## Exact-head CI

| Run | Result | Meaning |
|---|---|---|
| [44330729133](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44330729133) | SUCCESS | Quarantine/readback focused lab |
| [44330729195](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44330729195) | FAILURE | Relay-output lab passed 48/48 scenarios on both boards; boot lab then failed at `journalRecoveryRequired` after injected EEPROM commit failure |
| [44330728928](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44330728928) | FAILURE | Full validation failed at inherited QA assertion `Missing poll signature check`; ESP32, ESP8266, 13 firmware targets and Android completed successfully; downstream simulations, update bundle, candidate gate, signing and publishing were skipped |

The relay log explicitly reports `PHYSICAL_RELAY_POLARITY_VERIFIED=0`, `PHYSICAL_POWER_CUT_VERIFIED=0` and `FINANCIAL_PRODUCTION_AUTHORIZED=0`. These are host-simulation results only.

## Candidate and destination context

- #321 head `4c54d6299388617e9ff3d41d5501358ea545c54a`: focused relay/quarantine PASS; Full build run 44294008523 FAIL.
- #322 head `50d93e0de3d682550b6f02fb43484e76ad9c7e08`: focused relay/quarantine PASS; Full build run 44232877624 FAIL.
- #323 head `bc0447f013698a2e45c154b0ae69a098b0e75fe5`: focused quarantine PASS, relay/boot FAIL, Full FAIL.
- #324 head `8e7f02201cb9295f15672dc21f8a75fc4e5cd0ba`: focused relay/quarantine PASS; Full build run 44290338340 FAIL.
- #325 head `f66b45ecbae8cdc6e4d78db976903bb41c7a75b0`: focused pending-clear/quarantine PASS; Full build run 44311211166 FAIL.

These are separate owner branches and exact-head results; do not compose them by assumption.

COE main is `a6513ab4412b4c014eee2863e45cbe32d06cb243`. COE #26 remains `b382d233ff06c8791b1028bed3c617cc7b670d12`, OPEN / DRAFT, with five workflows QUEUED and zero jobs. The current COE #35 release candidate is `77cc0af71c04a75462e544b8ec945a8ffe8a3363`: shared/hardware and case-collision runs 44334235762 / 44334235743 passed; mandatory sandbox run [44334235787](https://github.com/BlazeDevStudio/CoinOperatedEcosystem/actions/runs/44334235787) ran 13 host preflight tests successfully, then failed closed because bubblewrap is absent (exit 125). No unsandboxed fallback was used.

## Other role heads and bounded CI

| Role | Current PR HEAD | Exact-head observation |
|---|---|---|
| CORE #252 | `c82705f2de865c89ab733b10efa84f26f56a5cc4` | 42698139210 SUCCESS, scoped; separate CORE automation retains implementation |
| RENTAL #289 | `68928774d0d7cf65adb26bc6b54199a3159d066c` | 43653329235 and 43653329229 SUCCESS, scoped |
| PISONET #255 | `d01fd1642c105b3b0f6cd3343d1c9b67291f6e09` | 42462978704 SUCCESS, scoped |
| QA #290 | `5c29d15994cee1279058f1eca12f2a3180704292` | 43633486963 SUCCESS, scoped |
| QA #292 | `75a3f66d9563e38a0a48b9cf487b0b057a91ea96` | No PR-triggered run returned |
| RELEASE #291 | `ed3565395bd70c4de696e49a84f0bb454efebc8b` | 44328674893 SUCCESS; privileged publisher skipped |

No role source branch was changed by PHX-MASTER. The separate CORE continuation remains the sole CORE implementation owner.

## Governance, registry and migration

- Experiments main `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`, development `aad3aade72c1156eecba1fed30907c6d0283b2c5`, and COE main `a6513ab4412b4c014eee2863e45cbe32d06cb243` report `protected=false` in the branch objects. Dedicated protection endpoints return 403; both repositories' rulesets endpoints return empty lists. Master branch protection detail also returned 403. Repository admin must configure and independently verify protected refs and required checks.
- COE root `AGENTS.md` returns 404.
- The canonical private Drive `BLAZE_PROJECT_REGISTRY_v11_20261027.json` and newer corrections were not found in the complete accessible Library listing; no Google Drive connector is exposed. No older registry was substituted and no private IDs or contents were published.
- `OWNERSHIP_ROUTES.json` remains blob `e4db324315a1b3543fec17a148fbf960170fcb29`, `DRAFT_REVIEW_ONLY`, with PHX-MASTER target null.
- No source/destination blob migration comparison, license review, import-completeness approval or move is proposed in this audit. COE #26 remains a draft candidate, not integrated acceptance.

## Required owner actions

1. **PHX-HARDWARE:** instrument the fake EEPROM commit/readback path and the extracted `loadCfg`/latch functions so the failed-commit test proves whether the fake commit was called, whether `saveCfg()` returned false, and whether the actual latch body ran. Correct only the confirmed defect on #323. Add the equivalent ESP32 unknown-polarity/INPUT-before-local-confirmation gate; verify persistence readback and boot ordering before claiming board parity.
2. **PHX-QA:** independently run the boot-polarity and negative poll-deny tests at the same immutable source SHA. Replace the inherited positive poll-signature assertion with negative deny-behavior tests; do not weaken firmware default-deny.
3. **PHX-RELEASE / infrastructure:** provide an authorized bubblewrap-capable runner for COE #35; keep sandbox failure fail-closed.
4. **Repository administrator:** configure branch protection and required checks, then provide independent readback.
5. **Registry custodian:** restore authorized access to the private v11 registry and newer corrections before any migration staging.

## Verification classification

- GitHub source/tree and exact blob inspection: COMPLETED.
- Existing GitHub Actions logs: inspected at the exact SHAs listed above.
- New Master documentation assertions: executed in the authoring run; they are not the repository's full Python suite.
- Full Master Python suite: NOT RUN.
- Physical GPIO/relay/coin acceptance, power cuts and device soak: NOT TESTED.

**Final decision:** retain all role PRs as drafts; no migration, merge, release, signing, secret provisioning, hardware flash, physical test or live-payment operation. **PRODUCTION NO-GO.**
