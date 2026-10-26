## v0.4.3 source acceptance checkpoint
- 101/101 Node.js 22 tests passed locally in current implementation checkpoint.
- New tests cover typed variable declarations, undeclared references, literal injection rejection, analog A0–A5 bounds, template scoping, per-session ADC injection, virtual threshold output, Wire/analog resource collision, project persistence and non-overwriting Arduino sketch export.
- Host C++ syntax check against explicit Arduino stub was executed, **not counted as real Arduino compilation**.
- Real Windows Arduino CLI Uno sensor/threshold compilation and Mega/Nano Blink compilations are **pending exact-head GitHub CI**.
- Packaged Windows DOM interaction/IPC test extended with Variables tab and sensor-to-output pipeline; **pending exact-head GitHub CI**.
- Still no physical MCU or 2 GB Windows acceptance.

# v0.4.1 interaction repair — source and Windows gate

- Source-based local Node.js 22 test runner: run `npm test`; inspect persisted log in `evidence/local-tests.txt`.
- New regression coverage: bounded simulation, virtual input injection and defaults, pause/resume breakpoints, branch/repeat/end semantics, memory text parser, 7/30-day storage forecasting, unknown board capacities, I2C address duplication, SPI bus sharing versus chip select collisions, active graph GPIO conflicts, and UI selector coverage.
- Windows CI: see `.github/workflows/blaze-mcu-studio-preview.yml` for exact steps; **results must be verified against an actual workflow run**. It compiles generated Blink and generated branch/repeat sketches with the actual Arduino CLI and packages a portable Windows EXE.
- Packaged GUI smoke sends IPC calls through the actual renderer/preload/main chain after `did-finish-load` for create/open project, code generation, virtual logic simulation, resource forecast. CI must fail if no GUI sentinel or failed test.
- No real board-level electrical/hardware tests or 2 GB Windows physical benchmark exist. Hardware emulator remains not implemented.

## v0.4.1 interaction repair

- Local Node.js 22 suite: 76/76 PASS; board discovery parser, installed/uninstalled status, platform core library scanning, graph serialization, and the original 71 regression cases.
- Windows workflow includes actual Electron GUI event checks for New Project modal, ESP8266 starter target visibility, drag/drop palette item, canvas block selection, inspector edit, save and reopen, in addition to source generation and core compilation.
- These **new** Windows checks are PENDING until associated exact-head CI completes; source unit tests do not substitute for packaged GUI behavior.
