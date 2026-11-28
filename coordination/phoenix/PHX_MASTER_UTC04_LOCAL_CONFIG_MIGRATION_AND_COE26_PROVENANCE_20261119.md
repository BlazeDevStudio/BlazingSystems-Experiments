# PHX-MASTER UTC04 — local configuration evidence boundary, Hardware provenance, and release handover freshness

**Run date:** 2026-11-19 UTC04  
**Task:** PHX-MASTER-UTC04-20261119-LOCAL-CONFIG-AND-COE26-PROVENANCE  
**Role:** PHX-MASTER — Master auditor / integration coordinator  
**Master branch before this update:** phoenix/master-coordination at d26000d4498739f87bb99ef2037ddcf5020d8a99  
**Existing PR:** #288 OPEN / DRAFT, base main at f4e8a891aed8af86d5fd315d28750a0ac3a7372b  
**Disposition:** Master coordination updated; destination migration BLOCKED; PRODUCTION NO-GO.

This run used connected GitHub, the accessible Files Library, and ordinary tool execution only. No Codex app, CLI, API, agent, workflow or Codex-delegated implementation was used. Scope remained coordination/phoenix, architecture/interface contracts, role routing, integration matrices and cross-repository provenance. No subsystem source branch, COE destination file, ownership route, financial system, hardware or secret was modified.

## 1. First-read and live control-plane state

The uploaded 00_MASTER_PROJECT_PHOENIX(1).txt, current README_FIRST, COMMUNICATION_PROTOCOL (BLAZE-COMMS/1), Experiments AGENTS.md, current Master coordination files, canonical cloud artifact policy and cloud-storage recovery handover were read.

| Authority | Current exact state |
|---|---|
| Experiments default main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Current development label, v0.6.0 audit foundation | 2fbd2475e9f54878c316fa7cea2f228386b0e859 |
| Legacy v0.5.3 development | aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Literal branch named development | 404 / does not exist |
| Master branch before update | d26000d4498739f87bb99ef2037ddcf5020d8a99 |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| Master PR #288 | OPEN / DRAFT; base main |
| COE integration PR #26 | OPEN / DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12 |
| Cleanup issue #266 | OPEN; historical cleanup checklist pins remain |

The ownership manifest remains unchanged at e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, with PHX-MASTER destination null. No branch promotion or source selection is authorized by this update.

## 2. Hardware #327 — exact current branch and test evidence

Current #327 branch/docs head is e799b0f042889b97ba7bae2ae2e06c1ec76392d6, a documentation-only commit recording the Mbed TLS 3/4 compatibility evidence. Parent/base #326 is 58c558fb6a237935214621adc3dee65a10fe1a51. The firmware source correction is commit 11fae729df415cc26b9e1675b1758cd8e4d22648; the exact source/test lab head recorded by Hardware is 071a711d6598c67124e84ffd995fd48aa7d9f054.

The #327 PR body still says its current head is a3597125fef3964ab08f05b3300c8de3e47516ae. That body is stale; the latest Hardware control-plane checkpoint identifies e799b0f correctly. HARDWARE owns refreshing the PR body. Master did not edit the Hardware PR or handover.

### Exact current-head CI

| Workflow | Evidence | Result |
|---|---|---|
| Quarantine/readback | [#44453718564](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44453718564), job 135323579699 | PASS |
| Relay/output polarity | [#44453718633](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44453718633) | PASS |
| Full BlazePwifi build | [#44453718661](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44453718661), validation job 135323581119 | FAIL at QA-owned Missing poll signature check |

The Full run's ESP8266, ESP32, 13 firmware/platform targets and Android jobs completed successfully. Validation failed; downstream simulation, update-bundle, signing, candidate and publishing jobs were skipped. This is not a Full workflow pass or release acceptance.

The ESP32 source explicitly selects PSA SHA-256 for Mbed TLS 4, legacy SHA-256 for Mbed TLS 3, and compile-time rejects unsupported majors. The current 4.0.0 build path has compile evidence. An exact-head ESP32 core 3.3.13 rebuild and an executable unsupported-major rejection test have not been returned. RELEASE owns the build-workflow pinning; HARDWARE owns firmware; QA owns independent verification.

### Local configuration failure lab is actually executed — but is not financial migration

A source review initially needs to distinguish direct workflow invocation from transitive test invocation:

- config_load_read_failure_lab.py blob: 40dfa46e48d8288bf94ad8c5579bf0d7436d4df6.
- coin_pulse_capture_lab.py blob: cdc6d85aed5e5a0c85b154afa67c302023ec20b9; it invokes poll_loop_blocking_inhibit_lab.py and config_load_read_failure_lab.py at lines 332–339.
- Quarantine workflow blob: fe98e5e41dbf73e22fbd34479dbc971f008d18c9; it invokes coin_pulse_capture_lab.py.

The exact #44453718564 job log confirms the configuration lab ran. It reports full-image EEPROM read failure/recovery, cold-boot deny, persistent read failure/no commit, stale same-size buffer denial, malformed v1/v2 and unknown-schema setup-save denial, valid local v1/v2 migration marker preservation, and failed local migration commit same-boot denial/cold-boot retry.

The lab emits these explicit classifications:
- LOCAL_CONFIG_MIGRATION_LAB_ONLY=1
- FINANCIAL_MIGRATION_TESTED=0
- PRODUCTION_MIGRATION_AUTHORIZED=0
- SIMULATED_ONLY=1
- PHYSICAL_POWER_CUT_VERIFIED=0

Therefore this is source-extracted fake-I/O evidence for local ESP8266 device configuration v1/v2-to-v3 only. It is not a financial ledger v1-to-v2 migration test, not a physical EEPROM durability test, and not production migration acceptance. The Master architecture contract now explicitly preserves this distinction.

## 3. Exact Hardware source/destination provenance at current refs

| Item | Experiments #327 source | COE #26 destination | Finding |
|---|---|---|---|
| ESP8266 sketch | 1b32cb90be11da79ba7ea1155f128aee9e495dd2 / 67,300 bytes | c8be98f72596681e36a3ad1f8939bf8046c96887 / 18,394 bytes | Different blob and size |
| ESP32 sketch | f54805b17cac45388dfacc5e65eff9b731234316 / 60,326 bytes | 3cc7ec54b476943dc04a8d1af5e2df5fe054e422 / 18,505 bytes | Different blob and size |
| Source test corpus | Eight Hardware-owned Python labs, including the indirectly invoked local config lab | One generic Hardware/tests/test_firmware_hardening.sh blob f921c56cecc19cab1989507b9b4ade1f45dac54e / 4,118 bytes | Not import-complete or test-equivalent |
| Poll admission contract | Source acceptPollResponse() returns false and preserves default-deny | Destination shell test positively requires response_sig, |register| and |poll| strings | Contract/test conflict |
| Hardware workflow | Source-side quarantine lab workflow | COE hardware-ci.yml blob fe79adbdb3745a22c5ef6d1f0c87c868b7785793 installs unversioned ESP8266/ESP32 cores | Not reproducible |
| Hardware README | Source-side current handover/toolchain evidence | COE README blob 99af3e5b46cd8b6f35c6479b204683f60c55ebcb says ESP32 3.3.12 and ESP8266 3.1.2 | Does not match #35's pinned ESP32 3.3.13 |
| License | BlazePwifi/LICENSE blob 1ee55b94183417be977ca287cd7391f9a6f7e721 | Pisowifi/LICENSE same blob; Hardware/LICENSE and Hardware/NOTICE.md return 404 | Hardware subtree scope unresolved |

The COE #26 description claims the licensing/privacy conflict is resolved and software readiness is 95%. The exact Hardware license/NOTICE paths remain absent and all five current #26 workflows are queued with zero jobs. Those narrative claims are not migration evidence.

No Hardware file was copied, moved, overwritten, cherry-picked, rebased, or staged. The ownership manifest remains unchanged.

## 4. Release and cross-role reconciliation

| Role / candidate | Exact head | Current evidence |
|---|---|---|
| CORE #252 | c82705f2de865c89ab733b10efa84f26f56a5cc4 | Scoped run 42698139210 PASS; separate CORE continuation retains implementation |
| RENTAL #289 | 68928774d0d7cf65adb26bc6b54199a3159d066c | Scoped runs 43653329235 / 43653329229 PASS |
| PISONET #255 | d01fd1642c105b3b0f6cd3343d1c9b67291f6e09 | Scoped run 42462978704 PASS |
| QA #290 | 5c29d15994cee1279058f1eca12f2a3180704292 | Scoped run 43633486963 PASS |
| QA #292 | 75a3f66d9563e38a0a48b9cf487b0b057a91ea96 | No exact-head runs returned; base is stale |
| RELEASE #291 | 63f9952ce783a007546b09daa5ea4847f32fb505 | Windows #44458671016 fails shared handover freshness; build-windows/publisher skipped. BlazePwifi #44458671105 fails Mandatory handover freshness; target builds and Android pass, downstream gates skipped |
| COE RELEASE #35 | a270b547fb5ff570bd2bc49c2e96219043d7c9bd | Shared/firmware #44451317780 PASS; case #44451317996 PASS; mandatory sandbox #44451317807 FAIL CLOSED because bwrap is absent after 14/14 preflight, exit 125 |
| COE RELEASE #44 | 582fd5d5e83e36b36546ac28534740298ba94af4 | Shared #44390136309 PASS; case #44390136296 PASS; sandbox #44390136327 FAIL CLOSED; 15 ahead / 21 behind #35 |
| COE CORE #45 | 9d76a134c1f6512aa40c20ec4d247306a71a8cce | Synthetic receipt-v1 runs #44295049727 / #44295049903 PASS; no approved Master-v2 mapping |
| COE integration #26 | b382d233ff06c8791b1028bed3c617cc7b670d12 | Five workflows QUEUED / zero jobs |

RELEASE's current UTC04 checkpoint reports its archive-integrity implementation verified, while shared validation remains blocked by CORE handover freshness. The exact #291 runs confirm the mandatory handover freshness gate is failing after release workflow changes. CORE and RELEASE must coordinate the canonical PROJECT_HANDOVER.md refresh; Master did not edit CORE-owned handover files or release workflows.

COE #35's toolchain pins are Arduino CLI 1.6.0, ESP8266 core 3.1.2 and ESP32 core 3.3.13. This correction exists on #35 only; it is not present on #26. COE #44 remains divergent from #35 and is not reconciled by Master.

## 5. Governance, registry and safety

- Experiments main and v0.6.0 branch objects report protected=false; COE main reports protected=false.
- Classic branch-protection endpoints return 403 to this integration; repository rulesets return an empty list. Effective required-check enforcement needs repository-administrator verification.
- Cleanup issue #266 remains OPEN with historical checklist pins. It is not proof that all seven cleanup tracks completed.
- The requested private BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not found in the accessible Files Library. No Google Drive connector is exposed in this runtime. No older registry snapshot was substituted. No private Drive IDs or contents were published.
- The public cloud artifact policy and recovery handover were read. GitHub remains source-code authority; Drive artifacts require exact source identity and independent remote readback.

## 6. Verification and limits

| Check | Result |
|---|---|
| Live issue/PR/branch/manifest refresh | Completed |
| Exact source/destination blob inspection | Completed |
| Exact role CI/job inspection | Completed |
| Hardware focused quarantine and relay CI | PASS at exact current branch head |
| Hardware Full workflow | FAIL at QA-owned Missing poll signature check |
| COE #26 destination CI | Five queued, zero jobs |
| Master Python suite | NOT RUN |
| Master GitHub Actions | No runs returned |
| Physical flash/EEPROM/relay/coin acceptance | NOT TESTED |
| Real power cuts / 30-device 24-hour soak | NOT TESTED |
| Financial migration / real payment systems | NOT TESTED / NOT AUTHORIZED |

No production signing, secret provisioning, hardware flashing, real payment operation, merge, rebase, release, financial migration or owner gate approval occurred.

## 7. Next exact owner actions

1. PHX-HARDWARE: refresh PR #327 description to current branch/docs head e799b0; obtain exact-head Mbed TLS 3.3.13 evidence and unsupported-major compile rejection; retain default-deny.
2. PHX-QA: independently review source/test head 071a711d and local config-read failure lab; replace the positive poll-signature fixture with negative/default-deny assertions without enabling unauthenticated admission.
3. PHX-CORE and PHX-RELEASE: coordinate canonical PROJECT_HANDOVER.md freshness after release workflow changes; CORE retains its source and handover ownership.
4. PHX-RELEASE: keep #35 pins, keep sandbox fail-closed until an authorized bwrap-capable runner exists, reconcile #44/#35 without force-push.
5. COE integration owner: complete per-file blob/mode provenance, Hardware license/NOTICE scope, eight-lab import/test identity, pinned CLI/core/FQBN/options and executable exact-head #26 CI before any staging.
6. Repository administrator: verify main/development branch protection and required checks.
7. Registry custodian: restore authorized private v11 and newer-correction access.

**PRODUCTION NO-GO** remains mandatory until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible financial migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently verified.
