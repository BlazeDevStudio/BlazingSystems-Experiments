# Rebuild the bundled Vendo source

Each firmware artifact includes a `source/` directory with the sketch and its
local Arduino libraries. `BlazePendingSequence` contains the exact
`v060_pending_sequence.h` used by that build. Keep the sketch directory and
`libraries/` together; the top-level `.ino` is retained for compatibility.

Install Arduino CLI and the appropriate board core, then open a terminal in
this `source/` directory. Use the core version recorded in the originating CI
job's installation log when reproducing that build; the CI core installation
currently follows the upstream core release rather than pinning its version.

For the ESP8266 / NodeMCU artifact:

```sh
arduino-cli config add board_manager.additional_urls https://arduino.esp8266.com/stable/package_esp8266com_index.json
arduino-cli core update-index
arduino-cli core install esp8266:esp8266
arduino-cli compile --fqbn esp8266:esp8266:nodemcuv2 --libraries libraries --output-dir ../rebuilt BlazePwifiVendo
```

For the ESP32 artifact:

```sh
arduino-cli config add board_manager.additional_urls https://espressif.github.io/arduino-esp32/package_esp32_index.json
arduino-cli core update-index
arduino-cli core install esp32:esp32
arduino-cli compile --fqbn esp32:esp32:esp32 --libraries libraries --output-dir ../rebuilt BlazePwifiVendo32
```

To select a particular installed core version, append `@VERSION` to its
`core install` argument. CI compiles directly from this bundled source layout;
the artifact's root `SHA256SUMS` covers the source, libraries and build outputs.

Compilation and source completeness do not establish physical coin timing,
GPIO safety, crash durability or permission to enable customer payments.
