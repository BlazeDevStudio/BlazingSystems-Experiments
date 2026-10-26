# Blaze MCU Studio 0.4.0 — Windows Preview

Blaze Systems · Offline-first Arduino-compatible desktop IDE · **preview, not production or a universal hardware simulator**.

## Actual work you can do with this build

1. Create a project and choose an installed Arduino CLI board FQBN.
2. Use the node editor or structured flowchart to assemble pin output, timed behaviors and conditional input logic. Flowcharts generate Arduino C++ and are independently checked by real Arduino CLI compilation on a Windows runner.
3. Use **Simulate** for step-by-step virtual GPIO state, branching, virtual time, breakpoints, and replay of the currently selected visual program. Change D2 from LOW to HIGH and watch a decision change paths. This models visual logic, not MCU instructions or electrical behavior.
4. Use **Resources** to inspect compiler-reported flash/global RAM (after an actual successful compilation), estimate storage growth with configurable logging interval/record size/free space/retention, and validate an I2C/SPI GPIO resource plan. `Plan SPI SD card` proposes physical Uno R3 pins only when conflict-free; it does not generate SD firmware.
5. Compile using actual Arduino CLI, then export standard Arduino IDE-compatible `.ino` sketches. Your manual C++ code remains user-owned, while generated code is read-only with protected custom regions.
6. Inspect installed Arduino libraries with BALIE's **inferred, read-only** C++ signature scanner; it does NOT yet generate universal executable library adapters.
7. Rename/duplicate/deactivate/recover local projects. No cloud login is needed.

## What's *not* supported

- No full board electrical simulator, timing-accurate MCU emulator, Arduino peripheral driver emulation or physical hardware verification.
- Board pin profiles are conservative; Uno R3 digital pins and Uno SPI/I²C planning only, unknown board GPIO is **Unknown / Verification Required**. Board compilation capability and pinout verification are distinct.
- No full Clang-based BALIE or automatic initialization logic, no arbitrary typed multi-branch graph reconstruction, no advanced Monaco editor, no WYSIWYG web UI designer, no multimedia asset studio.
- RAM budget on physical 2 GB Windows devices is not benchmarked; 99 MB EXE size is largely Electron/Arduino CLI packaging and is **not** feature-completion evidence.
- No SD driver/codegen or power-loss safe filesystem logger. SD increases data storage only, never program flash or SRAM.

## Operating instructions

Portable Windows EXE: launch directly, no Python or PowerShell script is needed. Board cores are installed through Arduino CLI as needed (requires connectivity for first install). The binary is unsigned. The project uses local storage and makes no unauthorized changes to devices; physical flashing remains optional outside the studio.

For source development, install Node.js 22+, run `npm install && npm test && npm start`; `npm run dist:win` packages Windows portable EXE. The GitHub CI job additionally compiles two generated Arduino Uno programs and performs packaged GUI IPC smoke testing (see exact CI evidence before relying on any result).

## License / sources

Application source MIT; Electron MIT; Arduino CLI Apache-2.0; installed Arduino libraries and board packages carry their own licenses. No third-party graphical assets are embedded. UI graphics are CSS and simple original shapes. The master roadmap is in `docs/DEVELOPMENT_ROADMAP.md`; version labels do **not** certify missing features.
