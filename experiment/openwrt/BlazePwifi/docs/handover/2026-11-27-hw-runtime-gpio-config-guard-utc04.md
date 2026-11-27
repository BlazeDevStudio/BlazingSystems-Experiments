# PHX-HARDWARE — runtime GPIO configuration guard

**Date:** 2026-11-27 UTC04  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** \`phoenix/hw-runtime-pin-config-guard-20261127-utc04\`  
**PR:** [#357](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/357), OPEN / DRAFT / UNMERGED  
**Base:** PR #355 branch at \`0adb541ae43143d6fc242f3746f56f71a3040d47\`  
**Source/test SHA:** \`ede3acab5dd8f3aefc1a3d3d2780c00fb8bc3c04\`

## Defect and risk

The ESP8266 and ESP32 setup portals accepted pin strings through permissive \`toInt()\` conversion and persisted the values without checking whether coin input, relay output and LED output collided or referenced flash-reserved GPIOs. A malformed form value could silently become GPIO0; overlapping roles could make the coin input and an output share a pin. Stored invalid tuples were also used during startup pin configuration.

This task is local Hardware scope. It does not change the CORE-owned authenticated controller API or coin/pending disposition contract.

## Code changes

- Added \`parseGpioNumber(const char*, int, int&)\`: rejects empty, non-decimal, negative and out-of-range input without integer overflow.
- Added \`validRuntimePins(int,int,int)\` to both sketches:
  - ESP8266: GPIO 0–16, excluding flash GPIO 6–11.
  - ESP32: GPIO 0–33, excluding flash GPIO 6–11. GPIO 34–39 are excluded because the coin input uses \`INPUT_PULLUP\` and those pins lack internal pull-ups / output capability.
  - Coin, relay and LED roles must be pairwise distinct.
- Startup checks persisted tuples before \`configureRuntimePins\`. Invalid tuples use the board's default pin map in RAM; no existing EEPROM/NVS bytes are rewritten. ESP32 also sets \`configStoreValid=false\`, so STA registration and poll remain disabled until a valid configuration is saved.
- Both \`/save\` handlers validate all three fields before Wi-Fi verification and persistence. Invalid tuples return HTTP 400 and are not saved.
- Added \`runtime_pin_config_lab.py\`, which extracts the real helpers, compiles a C++11 ASan/UBSan harness, exercises board-specific positive/negative matrices, and injects duplicate-role, flash-pin, nonnumeric and ESP32 output-capability regressions.
- The first implementation compile exposed ESP8266 Arduino auto-prototype ordering: helpers were initially before \`LegacyPendingRecord\`. They were moved after the record type; the lab now asserts this ordering.

## Test evidence

| Evidence | Exact SHA / job | Result |
|---|---|---|
| Expected RED | #45938629972 / job 140307550045 | FAIL as expected: missing helper |
| Focused push | #45939247440 / job 140309505531 | PASS |
| Focused PR | #45939251952 / job 140309520133 | PASS |
| ESP32 Mbed TLS 3/4 | #45939251950 / jobs 140310207299, 140310207551, 140310207553 | 3/3 PASS |
| Full ESP8266 target | #45939247661 / job 140309655278 | PASS |
| Full ESP32 target | #45939247661 / job 140309655084 | PASS |
| Full validation | #45939247661 / job 140309655083 | FAIL before docs sync: mandatory handover freshness gate |
| Native synthetic journal | #45939251963 / job 140309520462 | FAIL at QA-owned PAY-0745 |

Focused log markers:
- \`RUNTIME_GPIO_POLICY_PASS ESP8266\`
- \`RUNTIME_GPIO_POLICY_PASS ESP32\`
- \`RUNTIME_GPIO_MUTATION_REJECTED\` for duplicate-role, flash-pin and ESP32 input-only/output-role regressions
- \`RUNTIME_GPIO_CONFIG_SIMULATED_ONLY=1\`
- \`PHYSICAL_GPIO_OR_RELAY_ACCEPTANCE=0\`

## Current blockers

- Post-documentation Full CI is still required to clear the freshness gate and verify all integrated targets.
- Native PAY-0745 belongs to QA/CORE contract reconciliation; Hardware did not add unsafe pending-clear behavior.
- P0 #177 remains open: synchronous poll-before-sample risk and authenticated poll/receipt/disposition contract are not resolved by this GPIO config guard.
- Master #288 at \`f426d567c5dfdd94ec1be464b0a9fd619e0e02e8\` has not yet listed PR #357 in the role matrix.
- Private Google Drive \`BLAZE_PROJECT_REGISTRY_v11_20261027.json\` was not recovered; no older registry was substituted.

## Safety boundary

**SIMULATED / CI VERIFIED only.** Board strap behavior, external pull-ups, electrical voltage, relay contact state, physical coin pulses, brownout/power-cut recovery, 150 power cuts and 30-device/24-hour soak are NOT TESTED. No physical flashing, device reset, live money, production migration, deployment, signing or release tagging occurred.

## Next exact action

Run post-handover Full CI on the new documentation head, then request independent QA review of PR #357 and ask Master to refresh the role/integration matrix. CORE retains ownership of authenticated poll/receipt/disposition authority.