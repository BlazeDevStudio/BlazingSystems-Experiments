# ESP8266 Relay Controller

**Status:** PROTOTYPE / SOURCE

ESP8266 standalone web-control experiment evolved from the AP LED-controller work and adapted for relay behavior.

Keep it isolated from the Pisonet firmware: it is a separate experiment even though both use ESP8266 hardware.

## Validation needed

- compile with the intended ESP8266 core
- verify relay polarity and boot-state safety
- test reconnect/reboot behavior
- use appropriate isolation for any mains-voltage load
