# PHX-HARDWARE — ESP8266 UART0 pin reservation

**Updated:** 2026-11-27T11:55:43Z  
**Role:** PHX-HARDWARE  
**Repository:** \`BlazeDevStudio/BlazingSystems-Experiments\`  
**PR:** [#358](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/358) — OPEN / DRAFT / UNMERGED  
**Branch:** \`phoenix/hw-esp8266-strap-pin-guard-20261127-utc08\`  
**Base PR:** #353 at \`f527b33c9e391a9a66490388d96f06d6c8761dfa\`  
**Source/test SHA:** \`a37376b7f47da2e4d8192b9076f29c4281c0ef0f\`

## Defect

The ESP8266 sketch uses \`Serial.begin(115200)\` and does not call \`Serial.swap()\`. The ESP8266 Arduino Core maps the default UART0 to GPIO1/TX and GPIO3/RX ([official reference](https://arduino-esp8266.readthedocs.io/en/latest/reference.html#serial)). The current validators accepted these pins for coin input, relay output and LED output. That permits serial RX/bootloader traffic to become coin-input edges and serial TX traffic to drive a configured output.

## Changes

- \`validInputPullupPin()\` now reserves GPIO1 and GPIO3.
- \`validOutputPin()\` now reserves GPIO1 and GPIO3.
- \`esp8266_boot_polarity_lab.py\` adds a six-case matrix: GPIO1/GPIO3 rejected independently as coin, relay and LED assignments.
- The lab injects independent removal mutations for the input and output UART guards; both must fail.
- Existing ROM strap policy remains 10/10 with the original strap-guard removal mutation.
- \`remote_config_pin_recovery_lab.py\` changes its positive recovery tuple from coin GPIO3 to coin GPIO4 (relay GPIO12 / LED GPIO13), because the old fixture is no longer valid under the stronger UART policy.

Commit sequence:
- Test-only RED: [\`5ddcbdcf\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/5ddcbdcfd494e94f99429d7bc43b614e7392646f)
- Firmware guard: [\`48d3d2a0\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/48d3d2a034c10b9e26f507c3ab2bee3c185e73d8)
- Recovery fixture correction: [\`a37376b7\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/a37376b7f47da2e4d8192b9076f29c4281c0ef0f)

## Exact-head CI evidence

At source/test SHA \`a37376b7f47da2e4d8192b9076f29c4281c0ef0f\`:

- Relay Output Polarity [run #45993762703](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45993762703), job \`140487873440\`: **PASS**. Log markers: \`ESP8266_BOOTSTRAP_GPIO_POLICY_PASS 10/10\`, \`ESP8266_UART0_RESERVED_PIN_POLICY_PASS 6/6\`, UART input/output guard-removal mutations rejected, and \`ESP8266_REMOTE_CONFIG_PIN_RECOVERY_LAB_PASS 3/3\`.
- Quarantine Byte Readback [run #45993762758](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45993762758), job \`140487873271\`: **PASS**, with the same GPIO policy and recovery fixture markers.
- Full BlazePwifi [run #45993762783](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45993762783), validation job \`140487999545\`: **FAIL** at inherited \`Missing poll signature check\` in ESP8266. All 14 firmware target/platform jobs and Android passed. Production import, signing, publication and simulation/candidate stages were skipped.
- Test-first RED: Relay [#45993169775](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45993169775), job \`140485862247\`, and Quarantine [#45993169664](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45993169664), job \`140485861617\`, both failed at the expected missing UART0 input guard before firmware implementation.

All host evidence is SIMULATED / CI VERIFIED. Logs explicitly report \`PHYSICAL_RELAY_POLARITY_VERIFIED=0\`, \`PHYSICAL_COIN_PULSE_ACCEPTANCE=0\`, \`PHYSICAL_POWER_CUT_VERIFIED=0\`, and \`FINANCIAL_PRODUCTION_AUTHORIZED=0\`.

## Scope and safety

Only the Hardware-owned ESP8266 sketch and host labs were changed. No ESP32 source, shared API, CGI producer, financial authority, signer, witness, migration, COE source, pending disposition or positive coin admission was changed. No physical board, relay, coin acceptor, router or customer device was operated.

The UART0 pin reservation is a board-configuration safety guard. It does **not** resolve P0 #177's active-v0.6 synchronous poll-before-first-sample ordering, does not authenticate poll responses, and does not constitute hardware acceptance.

## Next exact action

PHX-QA independently reviews the six UART0 role denials and two failure-injection mutations. PHX-MASTER records #358 and its ancestry in the role/integration matrices. PHX-CORE publishes the authenticated register/poll/receipt/disposition contract; Hardware retains deny-default behavior until that contract and P0 intake protection are accepted.

**Classification:** SIMULATED / CI VERIFIED; physical acceptance NOT TESTED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
