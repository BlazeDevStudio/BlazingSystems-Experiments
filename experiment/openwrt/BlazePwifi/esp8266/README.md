# BlazePwifi — ESP8266 Vendo Firmware

Embedded companion firmware for the external coin/vendo role.

The ESP8266 communicates with the OpenWrt service through the documented BlazePwifi protocol. Coin pulse timing, electrical interfacing and recovery behavior require physical validation.

- [BlazePwifiVendo](BlazePwifiVendo/) — Arduino firmware source

[← BlazePwifi](../README.md)

## NodeMCU coin-acceptor GPIO safety (ESP8266-GPIO-20261022)

The hardware-facing ESP8266 sketch now permits only **GPIO4 (D2), GPIO5
(D1), GPIO12 (D6), GPIO13 (D7), and GPIO14 (D5)** for the coin input, relay
output and indicator LED. The three roles **must use different pins**.
The factory wiring remains coin GPIO4 / relay GPIO5 / LED GPIO14.

GPIO0/2/15 can alter boot strapping, GPIO6–11 connect to SPI flash,
GPIO1/3 are the serial port, and GPIO16 has special pull-up behavior.
Do **not** connect a coin-acceptor or relay load directly to an ESP8266
pin: use properly isolated, voltage-compatible interfaces, flyback
suppression and independent power protection verified for the hardware.

If a saved legacy pin configuration or new admin-provided pin assignment
is unsupported, the ESP8266 **rejects it and turns off coin acceptance**
instead of silently substituting and charging through the wrong GPIO.
An operator must inspect and rewire the real hardware if needed before
resuming; the firmware does not rewrite previous EEPROM configuration or
the LittleFS pending-coin journal. Remote config and the local setup
portal cannot bypass the GPIO role guard.

**Unsafe EEPROM recovery:** a rejected saved pin mapping now latches coin
acceptance off for the entire boot session, even when the server later sends
valid-looking remote GPIO overrides. Correct the physical wiring, submit a
supported, distinct pin mapping through the protected local setup portal,
and reboot; the new EEPROM wiring is evaluated again on startup. Remote
polling cannot clear this latch. Neither a reboot alone with unchanged
unsafe EEPROM nor a controller flag toggle enables paid coin collection.

**Verification limit:** host policy test and Arduino compilation do not
prove real boot, GPIO polarity, pulse-width/debounce, relay isolation or
coin accounting. A supervised physical electrical/power-cut test remains
mandatory before owner-authorized installation or paid operation.

## Owner-supervised ESP8266 acceptance matrix (unexecuted, 2026-10-23)

**Status: planning only; NO physical PASS.** This test is for a bench-only
NodeMCU and an electrically isolated, voltage-compatible coin pulse source.
Never attach customer coin funds, a live public acceptor, mains voltage,
production hardware, or actual account balances to this evaluation.
Document hardware schematic, active-high/low driver circuitry and a physical
relay fail-safe before even attaching the pulse generator.

| Test | Stimulus and required evidence | Pass condition / stop criterion |
| --- | --- | --- |
| Cold boot and relay polarity | Record a logic-analyzer trace at GPIO5 and at the actual relay driver, both active-high and active-low configurations; include bootloader/startup and first server registration | Do not approve if the physical coin gate can energize before it is explicitly authorized; raw GPIO level is not sufficient evidence |
| Unsafe EEPROM and recovery | Start with unsupported or overlapping saved pins, send a safe-looking remote override; then save supported distinct pins locally and reboot in a separate run | Reject all paid pulses and keep the physical gate inactive throughout the unsafe boot, including after remote polling; only a verified local correction/reboot may recover |
| Normal GPIO mapping and polarity transition | Exercise default coin GPIO4, relay GPIO5, LED GPIO14, then a distinct allowed alternate mapping on isolated hardware; record signal polarity before/during change | No uncommanded relay energization, double edge or unsafe bootstrap; otherwise STOP |
| Slow network poll during active coin window | Introduce controlled HTTP latency to the bench server while sending independently numbered short coin pulses, including pulses within the blocking interval | Physical acceptor must not accept a pulse absent from the durable pending record and matching server receipt; a missing pulse is **P0 NO-GO** |
| Grouping, debounce and reconnect | Vary pulse spacing around configured debounce/grouping settings, retry the same receipt across Wi-Fi loss/reconnect; compare capture trace, on-flash pending state and server ACK | Each accepted coin pulse is credited once and only once; no implicit refund/drop/replay ACK |
| Sudden power cut | On bench equipment only, interrupt power near pulse arrival, LittleFS persistence, retry and ACK; preserve flash backup for audit | Never silently discard an accepted coin or double-credit a replay; unresolved evidence is NO-GO |

**Source-level investigation required before a hardware claim:** `post()`
uses a synchronous `HTTPClient::POST` (configured timeout 3500 ms), but
`loop()` only samples `digitalRead(runCoinPin)` when control returns from
network operations. `applyOutputs()` may leave the acceptor relay in an
accepting state while a poll is blocked. This is a **potential lost-pulse
window**, not an observed incident. Do not assume relay-off timing, add an
ISR, or change coin accounting based on a source-only test: first capture the
isolated gate behavior and compare physical pulse count, journal sequence
and signed server receipt in the same trial.

**Minimum record:** bench date, board/driver revision, wiring and driver
polarity, firmware commit SHA + compiled binary SHA256, oscilloscope/logic
trace ID, pulse-generator count, journal state before/after, server receipt
IDs, relay activation times, failure mode and operator sign-off. Mark each
case PASS/FAIL/NOT RUN explicitly. Any NOT RUN or FAIL blocks physical
acceptance, production integration and release.

