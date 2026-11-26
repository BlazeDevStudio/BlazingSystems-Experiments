# PHX-HARDWARE UTC09 — preload logical OFF before GPIO output enable

**Task:** [P0 coin-pulse loss / fail-closed firmware #177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Control:** [#172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172)  
**Cleanup-first:** [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
**Draft:** [PR #354](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/354)  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments` (repository ID `1389289885`)  
**Branch:** `phoenix/hw-active-v06-poll-intake-deny-20261126-utc05`  
**Base:** `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`  
**Final source/test SHA:** `b8732704e2ff414f6ab4593acf4ae4e95fc6c280`

## Defect

Both Hardware-owned `configureRuntimePins()` implementations previously assigned the configured relay/LED pins, enabled them with `pinMode(..., OUTPUT)`, and only afterward wrote the logical OFF levels. On active-low wiring the output latch can initially be LOW; that transition can briefly energize a relay before the subsequent OFF write.

## Test-first and correction

- Test/lab added at `b091036a2bc1ad931f930efa0425e6ef8d2db0ed`; focused workflow wired at `615ac67cd1516c6cb8d8b6d3ed71891f26ecdede`.
- Expected RED: [run #45790170219](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45790170219), job `139806889031`, failed at the new exact-source assertion: `OUTPUT_SEQUENCE_FAIL relay OFF must precede OUTPUT mode` on ESP8266. Existing request-guard mutations passed before the new step. The lab stops on the first board failure; no ESP32 RED is claimed separately.
- ESP8266 correction: commit `24ade54ca09351e7d1c6b0f580c77f0146874284`.
- ESP32 correction / final source-test SHA: `b8732704e2ff414f6ab4593acf4ae4e95fc6c280`.
- Both sketches now preload `writeLogical(relay,false,runRelayActiveHigh)` and `writeLogical(led,false,runLedActiveHigh)` after assigning the new pins but before enabling OUTPUT. Old-pin shutdown and post-enable OFF confirmation remain.
- Exact-head focused GREEN: [run #45790391312](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45790391312), job `139807615868`: PASS. The exact-source lab reports active-high and active-low PASS on ESP8266 and ESP32 and rejects the unsafe missing-preload mutation on both boards: `4/4 output-enable sequence checks PASS`.

## Other exact-head checks

At the time of this handover update:
- ESP32 core 3.3.13/4.0.0 matrix [#45790391253](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45790391253): pending.
- Native synthetic journal gate [#45790391185](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45790391185): in progress.
- Full BlazePwifi [#45790391321](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45790391321): in progress.
- Prior exact-head native/Full failures remain QA-owned blockers: legacy active `clearPending(true/false)` expectations and controller parity requiring unsigned `config_revision`. Hardware did not modify QA-owned tests or consume unsigned response fields.

## Evidence limits

- Source-extracted GPIO ordering: SIMULATED / CI VERIFIED.
- Physical GPIO voltage, relay contact transient, boot strap and board-specific electrical behavior: NOT TESTED.
- Coin pulse, physical relay polarity, LittleFS power-loss, 150 controlled power cuts, 30-device/24-hour soak: NOT TESTED.
- Protected signer/witness, v1-to-v2 migration, durable accounting/replay, independent QA/release signoff: NOT ACCEPTED.
- HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

No coin admission, response trust, pending disposition, finance, API, migration, signer, witness or release behavior changed. No physical relay, coin acceptor, device, flash, live money or customer data was operated.
