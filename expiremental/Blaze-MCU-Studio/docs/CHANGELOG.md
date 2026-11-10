## v0.4.5 — first executable typed numeric data sockets (Windows gate pending)
- Added saved `graph.dataEdges` IR for explicit scalar source/consumer ports.
- Connected Analog Sample/Set Variable values override Threshold Output measurement source consistently in validation, C++ export and virtual simulation.
- Added amber data-wire UI, link and disconnect controls, type/ordering/conflicting-driver diagnostics, legacy/manual preservation.
- Added 8 deterministic wiring regressions, a generated Uno Arduino-CLI compile fixture and packaged Windows GUI port-link acceptance.
- No arbitrary math graph, branching reconvergence, or unverified library auto-adapters claimed.

## v0.4.4 — ESP family pin safety and real core compile gates (pending acceptance)
- Curated conservative GPIO maps for generic ESP8266, NodeMCU 1.0 and classic ESP32 only, with source provenance, flash pin no-go, input-only outputs blocked, bootstrap/UART warnings.
- Board-specific safe default Blink GPIO (ESP8266 GPIO4; ESP32 GPIO21) and matching flowchart; unchanged Uno 13.
- Pin Manager retrieves same board-profile source as backend; unsupported ESP32 variants explicitly unknown.
- Separate Linux CI for ESP8266 3.1.2 and ESP32 3.0.7 actual compiler installations; Windows packaged GUI acceptance now tests ESP pin map.
- Physical electrical testing, 2 GB RAM, full BALIE and S3/C-series maps still missing.

## v0.4.3 — typed-state source and sensor control (Windows gate pending)
- Typed global variables with safe numeric/boolean literals, declaration manager, persistence and scoped symbols.
- Analog Uno A0–A5 sampling into long variables; conditional threshold output with actual comparison C++.
- Virtual ADC injection and typed variable debugger; explicit unmodeled physical peripherals.
- First-use sensor threshold project template; separate empty visual template.
- Wire/ADC shared A4/A5 conflicts validated; Arduino AVR Uno/Mega/Nano compilation gates extended.
- Packaged GUI smoke extended with full typed variable create, graph block insertion, save/reopen, C++ generation and virtual sensor/output test.

## v0.4.2 — curated executable Arduino library adapter under testing
- Wire I2C register-write Uno adapter, PWM output, Serial print, strict byte validation and dependency-aware .ino export.
- Added virtual unsupported-peripheral warnings and compiler-gated sample; expanded GUI smoke to library insertion and source edit.
- Full BALIE/automatic universal adapters remain incomplete.

## v0.4.1 — first-use interaction repair (source awaiting CI)

- Discover actual installed boards; add clearly marked uninstalled ESP/Arduino starter targets and core installer with verified upstream ESP package index URLs.
- Enable drag-and-drop palette onto node canvas, visible selection, inspector editing and persistence in UI acceptance tests.
- Scan installed platform-core libraries in Arduino15 for BALIE read-only indexing.
- Require packaged Windows renderer interaction gate before artifact acceptance.
- See INTERACTION_AUDIT.md for defects and known gaps.

# Changelog

## 0.3.0 Preview — source under test

- Added BALIE read-only Arduino library metadata/header index, library function candidate descriptors and source hashing.
- Added flowchart AST, executable Arduino `if`/`else` and bounded `for`, typed GPIO output and delay, optional node function call, and bounded logic trace.
- Added flowchart and library browser to Windows GUI; source ownership and Arduino export remain common.
- Added project rename/duplicate/recoverable delete, board migration report, and regression tests.
- Windows build workflow expanded with actual compiler gate on a flowchart-generated sketch.
- Honest gaps: no Clang AST, no verified generic library adapters, no graph reconvergence, no circuit/hardware simulator, no 2 GB peak benchmark.

## 0.1.0 (foundation in development)

- Implement project JSON IR, graph validation and deterministic Arduino C++ generation.
- Add Electron desktop UI with node canvas, pin review and board/core management.
- Add manual/visual source ownership and preserved custom regions.
- Add offline-local saves with snapshot history and Arduino-compatible sketch export.
- Add separated Arduino CLI runner and Windows portable packaging workflow.

### Development continuation, 2026-10-26
- Refuse export overwrites of existing directories; regression test.
- Add actual node-generated Arduino CLI compilation gate to Windows workflow.
- Remove duplicated renderer-only code generator, retain core as sole generation authority.
- Harden autosave concurrency, stale source requests, and project model validation.

## 0.4.0 Preview (2026-10-26)

- Added bounded logic execution sessions for node and flowchart editors, virtual GPIO inputs/outputs, timing, step/run, breakpoints, trace and reset.
- Added compiler-measured program flash/static SRAM parsing and unknown-aware board capacities.
- Added configurable logging storage forecast, retention guidance and explicit SD-vs-RAM/flash distinction.
- Added I2C/SPI/GPIO resource planner with known collision detection and allowed shared-bus semantics; detects active visual GPIO collisions.
- Added Simulate and Resources UI tabs, virtual input injection, planning controls, and Uno SD SPI pin proposal (planning only, no drivers generated).
- Added packaged Windows GUI smoke gate (renderer DOM, IPC, project create/open, generated source, simulator, advisor) in CI, in addition to actual Arduino CLI firmware compilation.
- Added model-level regressions; full physical MCU simulation, executable BALIE adapters, memory benchmark and all later milestones remain not implemented.
