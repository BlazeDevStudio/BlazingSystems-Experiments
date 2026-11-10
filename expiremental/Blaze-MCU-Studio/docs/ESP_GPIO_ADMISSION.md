# v0.4.4 — board-aware ESP GPIO admission and compiler gate

Scope: ESP8266 Generic, NodeMCU 1.0 (ESP-12E), classic ESP32 Dev Module. Other S2/S3/C3/C6/H2/P boards are **Unknown / Verification Required**. The same reviewed map is served by backend and Pin Manager; future pin databases must carry per-core and carrier provenance.

## GPIO contracts

- ESP8266 raw GPIO4 selected by default. GPIO6..11 are refused by generic/NodeMCU visual-code generation because they ordinarily connect the SPI flash. GPIO0/2/15 carry boot-strap warnings; GPIO1/3 share UART; GPIO16 internal pullup and PWM are not assumed. D aliases on carrier PCB are **not** silently treated as raw GPIOs.
- Classic ESP32 raw GPIO21 selected by default. GPIO6..11 cannot be used for code output; GPIO34..39 are input-only (GPIO34-39 cannot be driven or internally pulled up); GPIO0/2/4/5/12/15 are boot-strap sensitive; GPIO1/3 normally share UART. GPIO16/17 are module/PSRAM dependent, and omitted from curated general output subset for now.
- Both use 3.3V logic; compilation does **not** establish safe wiring, actual breakout availability, flash/PSRAM module layout, power conditions, or protection against damaging a connected load.
- User-owned manual source passes through unchanged; static restrictions apply to generated visual nodes/flowchart, not arbitrary custom C++ that cannot be analyzed safely.

## Sources (consult official references, verify actual board revisions)

- https://arduino-esp8266.readthedocs.io/en/latest/reference.html
- https://docs.espressif.com/projects/arduino-esp32/en/latest/boards/ESP32-DevKitC-1.html
- https://documentation.espressif.com/esp32_datasheet_en.html

## Build evidence gate

`esp-core-compile` installs pinned ESP8266 Arduino 3.1.2 and ESP32 Arduino 3.0.7 using the original package indexes and compiles generated Blink projects for each. These tests run **separately** from Windows packaging so one platform's failed toolchain download cannot become a false positive. The version numbers in this document describe intended CI inputs, **not passing evidence** until exact-head jobs succeed.
