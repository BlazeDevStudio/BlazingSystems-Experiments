# BlazePwifi ESP32 Vendo

Reference firmware for an ESP32-based external coin controller.

It uses only Arduino-ESP32 core components:
- WiFi / WebServer / HTTPClient
- Preferences (NVS) for configuration
- LittleFS for the unacknowledged coin-event journal
- mbedTLS SHA-256

Defaults are examples only. Coin GPIO, relay GPIO, LED GPIO, active polarity, debounce, pulse grouping, server address, controller ID and credentials are configurable through the temporary WPA2 setup AP.

The server protocol is the same as ESP8266. A pending coin event keeps the same nonce and target until acknowledged so retries remain idempotent.
