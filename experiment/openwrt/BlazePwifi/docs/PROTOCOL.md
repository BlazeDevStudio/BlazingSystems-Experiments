# Blaze Vendo protocol v2

Transport: HTTP POST, application/x-www-form-urlencoded, default LAN TCP port 4455.

Endpoint: /cgi-bin/vendo

## Fields

- action: register, ping, poll, or coin
- id: configured Vendo identifier
- nonce: 8–32 hexadecimal request/event identifier
- pulses: decimal pulse count; 0 for non-coin requests
- target: active coin-window target nonce for coin events; blank for register/ping/poll
- sig: keyed SHA-256 digest

## Signature input

    VENDO_KEY|action|id|nonce|pulses|target|VENDO_KEY

The shared Vendo key is never placed in the request body.

This is a compact keyed-digest construction for the isolated Vendo LAN. It is not a replacement for TLS on an untrusted network.

## Poll

A selected Vendo receives a response containing:

    {"ok":true,"insert":1,"target_nonce":"...","expires":1234567890}

The ESP remembers target_nonce before accepting pulses.

## Coin event

Before reporting a pulse burst, the ESP journals the event nonce, target and pulse count to LittleFS. It then sends that exact event. If the response is lost—or the ESP reboots—the same event is recovered and retried.

The server persists an event marker in the same atomic account update as the credit. A retry returns ok with duplicate=true and credited_cents=0 rather than adding money again.

The target nonce also prevents a delayed/replayed event from being attached to a different customer's later coin window. The router stores the active target in persistent state for the short insertion window, so a router reboot does not automatically lose the customer association.

## Provisioning and upgrade

The ESP starts a WPA2 setup AP named BlazePwifi-Vendo-<chipid>. A generated per-device setup password is printed on serial during provisioning. Once the Vendo has joined the configured Wi-Fi, its setup AP shuts down automatically after ten minutes.

Firmware v0.2 migrates the prior v0.1 stored SSID, password, server, Vendo key, ID and GPIO mapping instead of resetting them.

## Network security

Keep Vendos on a trusted LAN or dedicated management/VLAN segment. Port 4455 is authenticated but intentionally remains HTTP to keep the ESP8266 client small; it must not be published to WAN.


## Controller implementations

The protocol is platform-neutral. BlazePwifi v0.3 uses the same authenticated, target-bound coin semantics for:

- **ESP8266** — compact controller using EEPROM configuration and LittleFS pending-event journal.
- **ESP32** — controller using Preferences/NVS configuration and LittleFS pending-event journal, with configurable polarity, debounce and pulse grouping.
- **Linux GPIO** — Orange Pi/SBC agent using the GPIO character-device stack through libgpiod tools.

No server action is ESP32-only. A deployment can mix ESP8266, ESP32 and Linux GPIO controllers while retaining one accounting protocol.

Hardware pins and polarities are deployment configuration, not protocol constants.
