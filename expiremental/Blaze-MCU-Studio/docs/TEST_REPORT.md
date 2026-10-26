# v0.4.0 test report — source checkpoint, pre-Windows gate

- Source-based local Node.js 22 test runner: run `npm test`; inspect persisted log in `evidence/local-tests.txt`.
- New regression coverage: bounded simulation, virtual input injection and defaults, pause/resume breakpoints, branch/repeat/end semantics, memory text parser, 7/30-day storage forecasting, unknown board capacities, I2C address duplication, SPI bus sharing versus chip select collisions, active graph GPIO conflicts, and UI selector coverage.
- Windows CI: see `.github/workflows/blaze-mcu-studio-preview.yml` for exact steps; **results must be verified against an actual workflow run**. It compiles generated Blink and generated branch/repeat sketches with the actual Arduino CLI and packages a portable Windows EXE.
- Packaged GUI smoke sends IPC calls through the actual renderer/preload/main chain after `did-finish-load` for create/open project, code generation, virtual logic simulation, resource forecast. CI must fail if no GUI sentinel or failed test.
- No real board-level electrical/hardware tests or 2 GB Windows physical benchmark exist. Hardware emulator remains not implemented.
