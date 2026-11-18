# HARDWARE #323 ESP8266 boot-polarity test-wiring audit

**Date:** 2026-11-18 UTC14  
**Role:** PHX-MASTER — coordination/phoenix only  
**Task:** #172 / #266 / #288 / HARDWARE #323  
**Disposition:** BLOCKED / DRAFT ONLY / PRODUCTION NO-GO

## 1. Exact live snapshot

| Ref | Exact state |
|---|---|
| Experiments main | f4e8a891aed8af86d5fd315d28750a0ac3a7372b |
| Experiments development | blazepwifi-v0.5.3-development @ aad3aade72c1156eecba1fed30907c6d0283b2c5 |
| Master branch before this report | phoenix/master-coordination @ dd4df401bef10540d1faa9fd8a56f0ae7b0415f9 |
| Master PR #288 | OPEN / DRAFT, base main @ f4e8a891..., head dd4df401... before this report |
| COE main | a6513ab4412b4c014eee2863e45cbe32d06cb243 |
| COE integration #26 | OPEN / DRAFT, head b382d233ff06c8791b1028bed3c617cc7b670d12; five workflows queued, zero jobs |
| HARDWARE #323 | OPEN / DRAFT, head 9cd889ec184c81d96569d3994602da3076efb537; parent #322 at 50d93e0de3d682550b6f02fb43484e76ad9c7e08 |

The owner’s implementation plan is recorded in [control-plane comment 6980748685](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-6980748685). It is an ACK/IN_PROGRESS plan, not proof that the promised implementation is already present.

## 2. Exact source/test/workflow reconciliation

| Artifact | Exact blob at #323 head | Finding |
|---|---|---|
| ESP8266 sketch | 8e79b9eb8856e67d966f4c6385f89fccdc8be7fc | Still V1/current Config with MAGIC V2; no ConfigV2/ConfigV3, outputPolarityConfigured, outputPolarityKnown, configChecksum or local polarity form fields |
| New boot-polarity lab | f08e1aadc40acf09e08ad055c92a38073c33f6c2 | Requires symbols and setup fields absent from the exact sketch |
| Relay/output workflow | dd2692df58c5311ad5d365a5539279da2018d8f7 | New lab command is a continuation of the prior plain-scalar run field, not a second command |

### Source facts

The current sketch defines ConfigV1 and Config, with MAGIC 0x42505732. The Config record does not contain local relay/LED polarity fields. loadCfg() begins at line 498 and reads the current record or migrates V1; it does not validate or migrate a local output-polarity setting.

setup() begins at line 1379. It calls loadCfg(), initializes the pending store, copies pin values, and reaches configureRuntimePins() without a validated local output-polarity source. The runtime polarity defaults are active-high. applyRemoteConfig() contains remote polarity assignments, but that function is explicitly dormant because the response configuration is unauthenticated. It cannot be repurposed as the boot-time source.

The new lab’s first prerequisite checks require:
- struct ConfigV2;
- outputPolarityConfigured;
- bool outputPolarityKnown=false;
- configChecksum;
- local relay_active_high and led_active_high setup fields.

Those required tokens are absent from the exact source blob. If the lab is actually invoked against this head, it should fail at its first missing prerequisite. This is not a passing implementation.

### Workflow command defect

The workflow currently places the relay lab command after a plain-scalar run field and indents the boot-polarity command as the next YAML line. YAML folds that line into the same scalar. The exact job log for [run 44320124000](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44320124000), job 134856529046, confirms the shell received one command containing both script names:

    python3 .../relay_output_polarity_lab.py python3 .../esp8266_boot_polarity_lab.py

The existing relay lab ran and reported 48/48 scenarios for each board. The boot-polarity script did not run as a second program. The green relay workflow therefore does not verify the new boot-polarity lab.

## 3. Exact-head CI evidence

- [Quarantine/readback 44320123810](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44320123810): SUCCESS.
- [Relay/output 44320124000](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44320124000): SUCCESS for the existing relay-output lab only; the new boot-polarity lab was not invoked.
- [Full BlazePwifi build 44320123851](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44320123851): completed FAILURE. Validation job 134856529480 failed at Controller protocol parity with exact message Missing poll signature check. All 13/13 firmware target jobs and Android job 134856530339 completed SUCCESS; downstream simulations, update bundle, candidate gate, signing and publishing jobs were SKIPPED. No Full pass is claimed.

All focused results are CI/host-simulation evidence. Physical GPIO voltage, relay contact behavior, cold boot, reset pull levels, flash power-loss behavior and coin acceptance are NOT TESTED.

## 4. Required owner actions

1. **PHX-HARDWARE:** implement the versioned local polarity record; preserve V1/V2 configuration compatibility but migrate old records with polarity unknown; keep relay/LED pins as inputs until a valid local polarity choice is durably stored; load and validate that value before first output configuration; make setup AP inputs strict 0/1; make failed persistence deny success/reboot. Correct the workflow with a block scalar or separate step so the new lab executes as its own Python process.
2. **PHX-QA:** independently test cold boot with default, missing, corrupt, active-high and active-low polarity values; assert the first GPIO state before OUTPUT mode; inject persistence/readback failures; run independent tests against the same exact source SHA. The Hardware-owned lab is not independent QA.
3. **PHX-CORE:** keep the response/authentication and financial-disposition contract deny-only until the canonical signed response envelope and golden vectors are defined and independently verified.
4. **Repository administrator:** configure protected branches and required status checks, then provide read-only verification evidence. No settings were changed in this run.

## 5. Branch protection and migration

Read-only branch API results show protected=false and protection.enabled=false for:
- Experiments main @ f4e8a891...
- Experiments development @ aad3aade...
- Master coordination @ dd4df401...
- COE main @ a6513ab4...

The Experiments and COE repository rulesets endpoints both returned an empty list. This supersedes the prior Master note that branch protection was UNKNOWN. No protection settings were changed.

OWNERSHIP_ROUTES.json remains blob e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, PHX-MASTER destination null. The exact private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json and newer corrections were not found in the Library, and no Google Drive connector is exposed. No older registry was substituted; no private IDs or contents were published. COE #26 remains queued and has no combined acceptance. No source/destination files were copied or moved.

## 6. Execution limitations and final gate

The container cannot resolve github.com, so no local Git checkout or Master Python suite was executed. Source/tree inspection, bounded source-token checks, and existing GitHub Actions runs are reported separately. The bounded audit confirmed the new lab prerequisites are absent and the workflow command is folded; this is not a firmware test.

No subsystem source branch was edited. No merge, rebase, migration, release, signing, secret provisioning, hardware flash, physical test or real-payment operation occurred.

**PRODUCTION NO-GO remains mandatory** pending independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates.
