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
