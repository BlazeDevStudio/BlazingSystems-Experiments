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

**Verification limit:** host policy test and Arduino compilation do not
prove real boot, GPIO polarity, pulse-width/debounce, relay isolation or
coin accounting. A supervised physical electrical/power-cut test remains
mandatory before owner-authorized installation or paid operation.


## Physical coin-acceptor relay eligibility (COIN-RELAY-20261022)

An energized relay must mean the controller **can actually journal the next
coin pulse**: a current coin window and a target nonce accepted by the existing
LittleFS hex-token validator (8–32 hex characters), an unchanged target during
a pending pulse group, usable LittleFS, and fewer than **20** recorded pulses.
The exact same rule is used by the relay/LED output and coin-pulse intake; the
output is deasserted immediately when the twentieth pulse is recorded or the
journal write fails. No already-recorded pulse is discarded or reassigned when
the window target changes.

This is a source-level fail-closed policy, **not** proof the actual relay,
solenoid, optocoupler or coin acceptor physically stops in time. Operators must
still verify both active-high and active-low wiring, output boot glitches,
pulse grouping, timeout/network loss, 20→21 pulse rejection, LittleFS
failure/power loss and corresponding backend paid receipts using isolated
hardware **before** enabling customer operation. The software test must not
be reported as a successful real coin or durability test.
