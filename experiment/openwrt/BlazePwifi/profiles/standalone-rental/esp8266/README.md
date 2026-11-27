# ESP Standalone Rental Server — rc.3

One firmware, three persistent operating modes:

1. **Rental Server** — authoritative BlazeRental server with manual credit and support for separately paired remote ESP coin interfaces. No local coinslot is required.
2. **Rental Server + Local Coin Slot** — same rental server plus **one** configurable local physical coinslot. Remote ESP coin interfaces are still supported.
3. **Remote Coin Slot Interface** — the local rental database is left dormant and the ESP becomes one authenticated remote coinslot for either a Standalone Rental Server or a full BlazePwifi server.

The default hardware model is **one physical coinslot per ESP**, dynamically assigned to whichever rental phone opens a coin window. Multi-slot-per-board is intentionally not part of this rental branch.

## First boot and recovery

First boot starts `BlazeRental-Setup-<chip>`. Open `http://192.168.4.1/`, scan/select Wi-Fi, enter credentials and an administrator password. The firmware tests association + DHCP **before saving**. On success it shows the assigned IP, persists configuration, and reboots.

Normal boots make five bounded attempts to connect to saved Wi-Fi. If all five fail, the ESP marks recovery, reboots once, and returns to the setup AP. An ISP/DNS outage does not disable the local rental service as long as Wi-Fi association and DHCP succeeded.

After setup the administrator uses only:

```
http://<assigned-ip>/
```

The BlazeRental application protocol remains at `/cgi-bin/rental`; remote coin interfaces use `/cgi-bin/vendo`.

## Remote coin binding

Rental Server modes show a generated **Remote coin binding key** in the root admin console. Put the server IP/URL and that key into another ESP running **Remote Coin Slot Interface** mode. The interface then uses the same signed BlazePwifi vendo protocol used by OpenWrt/full BlazePwifi.

No external Arduino libraries are required beyond the ESP8266/ESP32 board core and LittleFS support included with those cores.

**Electrical safety:** use an isolated/dry-contact or properly level-shifted coinslot signal. Never connect a 12 V coin acceptor directly to an ESP GPIO.
