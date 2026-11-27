# PHX-HARDWARE — ESP8266 UART0 pin reservation, terminal docs-head evidence

**Updated:** 2026-11-27T12:32:21Z  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#358](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/358) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-esp8266-strap-pin-guard-20261127-utc08`  
**Base PR:** #353 at `f527b33c9e391a9a66490388d96f06d6c8761dfa`  
**Source/test SHA:** `a37376b7f47da2e4d8192b9076f29c4281c0ef0f`  
**Prior docs HEAD:** `530d038f0379f4b5cbcf4d9ff222616969f86875`

## Scope and source audit

This is an exact-head evidence reconciliation for the existing Hardware-owned ESP8266 UART0 reservation. No new firmware or test source was required in this activation.

The ESP8266 sketch uses `Serial.begin(115200)` and does not call `Serial.swap()`. The host lab already asserts both conditions, rejects GPIO1/TX and GPIO3/RX for all coin/relay/LED roles, and independently injects removal of the input and output guards. It also verifies the GPIO0/GPIO2/GPIO15 boot-strap policy. No duplicate test was added.

## Terminal docs-head CI

| Workflow | Exact run | Job | Result |
|---|---:|---:|---|
| Relay Output Polarity | [#45994581501](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45994581501) | 140490652923 / 140490653386 | PASS / PASS |
| Quarantine Byte Readback | [#45994581522](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45994581522) | 140490652724 | PASS |
| Full BlazePwifi | [#45994581572](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45994581572) | 140490654224 | FAIL |

Focused log markers:
- `ESP8266_BOOTSTRAP_GPIO_POLICY_PASS 10/10`
- `ESP8266_UART0_RESERVED_PIN_POLICY_PASS 6/6`
- UART input and output guard-removal mutations rejected
- ESP8266 and ESP32 remote-config revision checks 5/5 each
- ESP8266 pin-recovery 3/3
- Quarantine job additionally confirms ISR wiring and 18/18 pulse-capture host scenarios per board

Full validation failure:
- `tests/controllers.sh` reports `Missing poll signature check` in the ESP8266 sketch.
- All 14 firmware target/platform jobs and Android completed PASS.
- Production import, signing, update bundle, candidate, simulation and publication stages were SKIPPED.
- This is an inherited controller-contract validation failure, not a UART0 guard or target-build failure.

## Remaining P0 and safety boundary

Active v0.6 still performs synchronous poll before the first coin sample: ESP8266 lines 354/357 and ESP32 lines 314/318, with a 3,500 ms timeout. PR #358 does not resolve P0 #177. CORE owns the authenticated register/poll/receipt/disposition contract; QA owns independent assertion semantics; MASTER owns global assignments.

No ESP32 production source, shared API, CGI producer, finance, replay, signer, witness, migration, COE, pending disposition, positive coin admission, relay actuation, physical device or customer data changed.

**Classification:** host/SIMULATED and CI VERIFIED only. Physical boot/GPIO/relay/coin/electrical acceptance, 150 controlled power cuts, and 30-device/24-hour soak are NOT TESTED. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

## Next exact action

PHX-QA independently reviews the six UART0 role denials and guard-removal mutations; PHX-CORE publishes the authenticated controller contract; PHX-MASTER records the #358 head and ancestry. Hardware keeps coin/relay admission fail-closed.
