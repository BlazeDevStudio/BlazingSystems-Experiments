# PHX-HARDWARE handover — keyless poll-response denial (UTC13)

**Status:** SOURCE COMMITTED / FOCUSED CI VERIFIED / FULL INTEGRATION BLOCKED / PHYSICAL HARDWARE NOT TESTED

- Repository: `BlazeDevStudio/BlazingSystems-Experiments`
- Role: `PHX-HARDWARE`
- Task: `#177` / control plane `#172` / existing DRAFT PR `#349`
- Branch: `phoenix/hw-json-array-primitive-guard-20261124-utc00`
- Base branch: `phoenix/hw-coin-ingress-config-helper-reconciled-20261123-utc13`
- Base SHA: `960184670379f01e20f0e7e8bc23b3e5eedacd3f`
- Starting head: `bdb2e5c36059a7eef99368a2047d7860449d7059`
- Source/test head: `387fa429cc3fc6fb8d6409df1ed521d2b70fde4b`
- PR: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349

## Scope and change

Only Hardware-owned host/source-extracted regression infrastructure changed:

1. `poll_loop_blocking_inhibit_lab_runtime_fixtures.py` models the controller key with the board-shaped type: ESP8266 fixed char array and ESP32 String. Explicit clear/empty helpers are test-only.
2. `poll_loop_blocking_inhibit_lab_response_fixtures.py` adds a keyless no-edge response-denial scenario.
3. `poll_loop_blocking_inhibit_lab.py` injects an untrusted positive `ok/insert/target` response with a `response_sig`-looking placeholder while the controller key is empty. The placeholder is deliberately **not** a valid signature or protocol vector.
4. Both active-high and active-low relay configurations are exercised on both boards.
5. A fail-open mutation that accepts the keyless response is injected and must fail with expected exit 90.

No production `.ino`, CGI producer, shared wire format, cryptographic verifier, controller API, coin/relay actuation, finance, signer, witness or migration source was changed.

## Exact CI evidence — source/test SHA

- Quarantine Byte Readback: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45401282766
  - Job `138470233131`: PASS.
  - Logs show ESP8266 and ESP32 keyless-response denial PASS for active-high and active-low; all four keyless fail-open mutations rejected with expected exit 90.
- Relay Output Polarity: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45401282768
  - Job `138470234242`: PASS.
  - ESP32 boot-polarity job `138470234846`: PASS.
  - Same four board/polarity keyless scenarios and fail-open mutations are present in the exact-head log.
- Full BlazePwifi: https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45401282779
  - Validation job `138470395251`: FAIL at inherited `Missing poll signature check` in the ESP8266 controller sketch.
  - 14/14 firmware/platform + Android jobs PASS.
  - Update bundle, simulations, candidate gate, production signing/handoff and publication were skipped.

Local tests were NOT RUN; the focused evidence is from GitHub Actions on the exact source/test SHA above.

## Evidence classification and blockers

- Host/source-extracted regression: SIMULATED.
- Focused CI: CI VERIFIED.
- Physical coin, relay polarity, electrical pulse/recovery, LittleFS power-loss and noncustomer-device acceptance: NOT TESTED.
- 150 controlled power cuts and 30-device 24-hour soak: NOT TESTED.
- Authenticated controller response envelope: NOT APPROVED by CORE/QA; the lab remains deny-only.
- Production: NO-GO.

The exact private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not surfaced by the available Library search. An accessible checkpoint references v11, but that checkpoint is not the registry itself. No older registry was substituted and no Drive promotion was attempted.

## Next exact action

PHX-MASTER refreshes the #349 source/test pin to `387fa429cc3fc6fb8d6409df1ed521d2b70fde4b`. PHX-CORE publishes the versioned authenticated register/poll envelope and golden vectors. PHX-QA independently reconciles the inherited validation assertion without weakening negative/default-deny tests. PHX-HARDWARE reruns Full only against the approved exact contract SHA. No physical acceptance or production authority is implied.
