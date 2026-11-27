# BlazeSystems ESP8266 Arcade — Public-Safe Shell

**Project Status:** EXPERIMENTAL / RECOVERED-DESIGN DERIVATIVE

## Purpose

This project preserves the safe engineering core of an earlier ESP8266 captive-arcade experiment: an ESP8266 creates its own Wi-Fi access point, redirects connected clients to a local browser interface, optionally joins an upstream network, and can expose NAPT Internet sharing when supported by the selected ESP8266 core.

The public edition deliberately uses an original mini-game rather than emulator/ROM content.

## Why This Is a Derivative

A complete private firmware artifact was recovered. Its embedded portal contained third-party emulator/runtime references and ROM-library workflows. That raw artifact remains outside public GitHub.

This directory is a separate publication-safe implementation derived from the architecture, not a byte-for-byte copy of the recovered firmware.

## Features

- ESP8266 captive access point
- per-device generated AP credentials
- captive DNS redirects
- local HTTP arcade page stored in PROGMEM
- original dependency-free browser mini-game
- optional upstream STA connection
- optional NAPT support when provided by the selected ESP8266 Arduino core
- JSON status endpoint

## Deliberately Excluded

- ROM files
- BIOS files
- third-party emulator cores
- copied commercial game assets
- user/private Wi-Fi credentials
- browser runtime downloads or cache installers

## Build

1. Open `BlazeSystems_ESP8266_Arcade_Public.ino` in Arduino IDE.
2. Install/select the ESP8266 Arduino core.
3. Choose the target ESP8266 board.
4. Leave `STA_SSID` and `STA_PASSWORD` blank for standalone mode, or insert your own local test network values before compiling.
5. Compile and flash.
6. Join the generated `BlazeArcade-XXXXXX` access point and open the captive portal.

NAPT is conditional on the selected core/lwIP build and must be tested on the exact target board.

## Validation

The source has been reviewed for publication safety, but target-board compilation and hardware/network validation remain.

## Known Limitations

- this public edition is an arcade-shell demonstration, not a multi-system emulator;
- upstream credentials are compile-time user values;
- captive portal detection differs by operating system;
- NAPT availability depends on ESP8266 core/lwIP configuration;
- generated AP credentials are printed to serial output for setup convenience.

## Future Work

- web-configurable upstream Wi-Fi stored safely on-device;
- first-boot credential reset flow;
- LittleFS support for original/public-domain mini-games only;
- exact-board compile and long-duration client testing.
