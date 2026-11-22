# PHX-HARDWARE — ESP8266 remote-pin recovery lab exercises the actual JSON tuple

**Date:** 2026-11-22 UTC17  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#343](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/343) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-esp8266-pin-recovery-20261122-utc16`  
**Parent:** PR #342 exact base `e7815297b1a8780b7868bc9b28f45011ec419dce`  
**Production sketch fix:** `b254531fafa2903bc614896b7587e9ab19262e11`  
**Test-only RED:** `cbdec71165242911168f608833ebf0864f55cb6e`  
**Source/test GREEN:** `ea437956543aaadb1181edcf76a921ae67674cfe`

## Defect in the host regression

The first #343 recovery lab called `applyRemoteConfig(String("{}"))` while replacing the production `jsonInt()` with a stub that always returned fallback values (except one forced relay-pin negative case). The test therefore reconfigured the existing default tuple; it did not prove that a distinct valid tuple from JSON was parsed and applied.

The test-only commit changed the valid case to request coin GPIO 3, relay GPIO 12 and LED GPIO 13. The stub continued returning defaults, so the regression failed with exit 2 as intended:

- RED Quarantine [run #45048415916](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45048415916), job `137287978044`: **FAILURE (expected RED)**.
- Log: `ESP8266 remote-config recovery lab failed with exit 2`.

## Correction

The host lab now extracts the actual production `jsonInt()` implementation along with `applyRemoteConfig()`, and the minimal Arduino `String` stub implements the required `indexOf`, `substring` and `toInt` operations. The test supplies an actual JSON text tuple rather than bypassing the parser.

The three exact-source cases are:

1. **Valid non-default tuple:** JSON applies coin=3, relay=12, LED=13; both output pins reach OUTPUT only after the validated logical-OFF latch is preloaded, and remain OFF.
2. **Unknown local polarity:** the same valid tuple cannot override unknown local output polarity; relay/LED remain INPUT and `pinConfigSafe` is revoked.
3. **Invalid GPIO:** relay=99 is rejected; the existing runtime tuple is not replaced and neither output is enabled.

The test also fails if the `pinConfigSafe` publication is moved back after `configureRuntimePins()`, because the extracted helper will leave the output pins INPUT.

## Exact-source evidence

- Source/test SHA `ea437956543aaadb1181edcf76a921ae67674cfe`.
- Focused Quarantine [run #45048644447](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45048644447), job `137288677136`: **SUCCESS**. Logs:
  - `ESP8266_REMOTE_CONFIG_PIN_RECOVERY_LAB_PASS 3/3`
  - `ESP8266_REMOTE_CONFIG_VALID_PIN_RECOVERY_PASS`
  - `ESP8266_REMOTE_CONFIG_UNKNOWN_POLARITY_DENY_PASS`
  - `ESP8266_REMOTE_CONFIG_UNSAFE_PIN_DENY_PASS`
  - Both-board source quarantine `36/36`; EEPROM end/reopen failure deny; pulse-capture `17/17` per board; boot-polarity lab PASS.
- Relay/output [run #45048644451](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45048644451): **SUCCESS**, jobs `137288677225` and `137288677404`.
- Full build [run #45048644456](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45048644456): **FAILURE** at validation job `137288730612`, inherited `Controller protocol parity` / `Missing poll signature check`. All 14 target/platform build jobs completed SUCCESS (including ESP8266, ESP32, OpenWrt targets and Android). Downstream simulation, candidate, signing and publication jobs were skipped.

## Safety and limitations

- The remote-config consumer remains intentionally dormant: logs state `REMOTE_CONFIG_APPLIED_FROM_REGISTER=0`.
- This is source-extracted host simulation, not proof of authenticated remote configuration or physical pin voltage.
- Logs explicitly report `SIMULATED_ONLY=1`, `PHYSICAL_COIN_ACCEPTOR_VERIFIED=0`, `PHYSICAL_POWER_CUT_VERIFIED=0`, and no financial production authorization.
- No register/poll API, CORE ledger, coin POST, relay authorization contract, signer/witness, migration, QA assertion, Release workflow, customer device or physical hardware was changed or used.
- Coin admission remains deny-only. Hardware acceptance remains NOT TESTED; production remains NO-GO.

## Next exact action

PHX-CORE must publish the approved authenticated configuration envelope and event-bound response contract; PHX-QA must independently validate exact positive/negative vectors. Until that contract is accepted, keep the remote-config consumer dormant. PHX-HARDWARE should revalidate this child and its parent heads before any further source change.


## Follow-up — ESP32 unknown-polarity revocation must survive caller return (2026-11-22 UTC18)

**Exact branch before this follow-up:** \`90f3c8044acd4f140091d1a9ef3461278ba8d5f5\`  
**Parent stack:** #327 \`fadac4ed3bc837cf729753264b9427fa3fd312b9\` → #342 \`e7815297b1a8780b7868bc9b28f45011ec419dce\` → #343.

### Defect and expected RED

The new dual-board revision lab initially stubbed \`configureRuntimePins()\`, so it could not observe a safety flag being revoked by the real helper.

The actual ESP32 \`configureRuntimePins()\` sets \`pinConfigSafe=false\` and leaves relay/LED pins in INPUT when \`outputPolarityKnown=false\`. Its caller then set \`pinConfigSafe=true\` **after** the helper returned, overwriting that fail-closed result. ESP8266 already published the validated map before calling its helper, allowing the helper to revoke the flag.

- Test-only commit: \`1425f82519767fd763bce10877303ab73c4493a2\`.
- Expected RED: Quarantine [run #45054586349](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45054586349), job \`137306878468\`; exact failure \`ESP32 exact-source: expected exit 0, got 14\`. ESP8266 passed the new 5/5 cases; ESP32 failed the unknown-polarity postcondition as intended.

### Correction

Source commit: \`90f3c8044acd4f140091d1a9ef3461278ba8d5f5\`.

The ESP32 \`applyRemoteConfig()\` helper now sets \`pinConfigSafe=true\` **before** \`configureRuntimePins()\`. The helper can therefore revoke it when local output polarity is unknown. This matches the ESP8266 ordering. No register/poll authentication, remote-config callsite, coin admission, relay authorization, or shared contract was enabled or changed.

The revision lab now extracts the actual production \`writeLogical()\`, GPIO validators, \`runtimePinsSafe()\`, \`configureRuntimePins()\`, \`jsonInt()\`, and \`applyRemoteConfig()\`; it no longer stubs the safety-critical pin helper.

### Exact-source evidence

- Quarantine [run #45054895869](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45054895869), job \`137307832284\`, **SUCCESS** at source/test SHA \`90f3c8044acd4f140091d1a9ef3461278ba8d5f5\`.
- Both boards: \`REMOTE_CONFIG_REVISION_GUARD_PASS 5/5\`, including stale/equal/zero revision denial, newer revision control, and \`REMOTE_CONFIG_UNKNOWN_POLARITY_DENY_PASS\`.
- Existing poll-edge/fault, EEPROM/NVS, quarantine, pulse-capture and cold-boot polarity labs also passed in that focused job.
- The job explicitly reports \`REMOTE_CONFIG_AUTHORIZATION_ENABLED=0\`, \`PHYSICAL_HARDWARE_ACCEPTANCE=0\`, \`PHYSICAL_POWER_CUT_VERIFIED=0\`.
- Full PR run [#45054895849](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45054895849) has validation job \`137307908217\` **FAILED** at the inherited QA-owned \`Controller protocol parity / Missing poll signature check\`; target jobs were still running when this handover was prepared. No Full PASS is claimed.

### Disposition

This is a source-extracted host/CI correction for a dormant helper, **SIMULATED / CI VERIFIED only**. It does not authorize remote configuration, relay actuation, coin admission, physical testing, finance, migration, release, or deployment. Hardware acceptance remains NOT TESTED; production remains NO-GO.


## Follow-up — protect the dormant remote-configuration trust boundary (2026-11-22 UTC19)

**Exact source/test commit:** `fae8398946fcb2c35c1d831620128f2777bc05d5`  
**PR:** [#343](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/343), still OPEN / DRAFT / UNMERGED.  
**Scope:** test infrastructure only; no ESP sketch or controller API behavior changed.

### Gap closed

Master Architecture Contract §6.4 requires `applyRemoteConfig()` to remain uncalled from register/ping or poll responses until CORE publishes a separately authenticated configuration envelope and QA approves exact positive/negative vectors. Both sketches currently have the helper definition but no active callsite. The revision lab previously tested revision monotonicity and GPIO safety but did not protect that dormant state against a future callsite regression.

### Regression and failure injection

`remote_config_revision_lab.py` now imports the shared `mask_active_cpp_code()` and `mask_non_code()` helpers. For each board it requires exactly one active `applyRemoteConfig()` occurrence (the function definition), ignoring comments, literals and inactive preprocessor branches.

The test then injects forbidden calls into both `connectSta()` and `loop()`. The guard must reject both mutations. This prevents a future unauthenticated register/poll path from silently activating remote configuration.

### Exact-source evidence

- Source/test SHA: `fae8398946fcb2c35c1d831620128f2777bc05d5`.
- Relay/output workflow [#45062314769](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062314769), job `137330746787`: **SUCCESS**. Logs show for ESP8266 and ESP32:
  - `REMOTE_CONFIG_CONSUMER_DORMANT_PASS`
  - `REMOTE_CONFIG_CALLSITE_MUTATIONS_REJECTED 2/2`
  - revision guard `5/5`, stale/equal/zero denial, newer-revision control, unknown-polarity denial
  - poll-window, ISR-edge, pulse-capture and relay-output regression/mutation checks pass.
- Quarantine workflow [#45062314763](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062314763), job `137330746755`: **SUCCESS**. Exact-source fake-LittleFS, EEPROM/config-read recovery, poll-drain pulse capture and cold-boot polarity checks pass. Logs explicitly retain `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`.
- Full PR build [#45062314768](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45062314768), validation job `137330748316`: **FAILURE**, inherited `Missing poll signature check` in the ESP8266 sketch. This is the QA-owned legacy positive fixture; no signature was invented and no default-deny behavior was weakened. Platform jobs were still running when this handover was written; no Full pass is claimed.

### Disposition

The remote-config consumer remains dormant. This is host source-analysis / CI evidence only, not authenticated configuration acceptance or physical hardware acceptance. No finance, coin admission, relay authorization, signer/witness, migration, device, production deployment or release state changed.

**Next exact action:** PHX-CORE publishes the canonical authenticated configuration envelope and canonical bytes; PHX-QA independently approves positive/negative golden vectors; PHX-HARDWARE keeps the consumer definition-only until both are accepted.
