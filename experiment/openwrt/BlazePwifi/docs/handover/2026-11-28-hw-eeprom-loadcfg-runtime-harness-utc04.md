# PHX-HARDWARE — EEPROM loadCfg runtime harness

- Work item: PHX-HW-EEPROM-LOADCFG-RUNTIME-20261128T04Z
- PR: [#372](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/372), OPEN / DRAFT / UNMERGED
- Parent: [#371](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/371), exact base `18a3fa470970e729a02920607562f4b9a1e50d34`
- Branch: `phoenix/hw-eeprom-loadcfg-runtime-harness-20261128-utc04`
- Latest source/test head: `6a29509079b0e4383b4305a75197bd72e6874066`

## Implementation

The EEPROM integrity runner now executes the actual source-extracted `loadCfg()`, `defaults()`, and `saveCfg()` functions in a native C++11 fixture. A fake EEPROM models durable bytes separately from staged writes; a failed `commit()` leaves durable bytes unchanged.

Runtime matrix:
- Valid current Config accepted without rewriting EEPROM: 1/1.
- Unterminated current fields rejected and defaults persisted: 6/6.
- Valid ConfigV1 migrated and persisted as current Config: 1/1.
- Unterminated legacy fields rejected before copying: 5/5.
- Failed legacy migration commit preserves durable v1 and retries next boot: PASS.
- Failed defaults commit preserves corrupt durable image and retries next boot: PASS.

The source contract requires both migration and defaults branches to check the `saveCfg()` result. Two new mutation cases reject removing either check.

## Exact CI

- Focused [#46109901701](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46109901701), job `140870890653`: PASS at `6a29509079b0e4383b4305a75197bd72e6874066`; 7/7 source mutations rejected and all runtime scenarios passed.
- Mbed [#46109906713](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46109906713): source-contract PASS; target builds were running when this checkpoint was written.
- Full [#46109901702](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46109901702) and PR [#46109906747](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46109906747): validation failed at mandatory handover freshness because canonical records were stale after the source commit. These attempts did not reach controller parity; target jobs were still running. Rerun after this docs update.

## Boundaries and disposition

Host-only source-extracted simulation. No production sketches, config schema, shared controller/finance contract, QA-owned assertion, signer/witness, migration runtime, COE files, physical device, EEPROM/NVS brown-out, or release surface changed. No flash, reset, live money, merge, release tag, or deployment.

Physical EEPROM/NVS brown-out, GPIO/relay, LittleFS power loss, 150 power cuts, 30-device/24-hour soak and electrical pulse/recovery: NOT TESTED. HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO.

Next: verify Mbed terminal status, rerun Full after the canonical docs refresh, and update the same PHX-HARDWARE UTC04 BLAZE-COMMS checkpoint in place.


## Terminal CI readback — 2026-11-28T05:04:25.085Z

- Focused push #46110090617 / job 140871475900: PASS at docs head 2bf108d6f4b46263376dcc99ded4b0fc3b7eceb6.
- Focused PR #46110095250 / job 140871489774: PASS at the same docs head. Runtime matrix: current Config 1/1; current unterminated 6/6 rejected; ConfigV1 migration 1/1; legacy unterminated 5/5 rejected; migration/default commit failure retry 2/2; source mutations 7/7 rejected. CHANGE_LEDGER append-only guard PASS (base 1,132,798 bytes; append 53,642 bytes).
- Mbed #46109906713: 3/3 PASS at source/test SHA 6a29509079b0e4383b4305a75197bd72e6874066 (source contract, ESP32 core 3.3.13, 4.0.0).
- Full #46110095274: terminal FAILURE. CI-0701 and handover freshness PASS; validation job 140871599695 fails at QA-owned `tests/controllers.sh:21` literal `config_revision` assertion. All 14/14 target/platform jobs PASS (ESP8266, ESP32, Android, Ruijie, x86_64, Orange Pi and optional targets). v0.4 simulations/update/signing/publication skipped after validation failure.
- This Full failure is not a failure in the new EEPROM runtime fixture or target compilation. QA owns the controller assertion; Hardware did not modify it or add a placeholder field.
- Host simulation only. Physical EEPROM/NVS brown-out and all required hardware acceptance remain NOT TESTED. HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO.
- Exact Full run URL: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46110095274
