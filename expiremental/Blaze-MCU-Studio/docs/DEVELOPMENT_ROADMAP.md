# Milestone roadmap (requirements preserved)

A feature is **not implemented** until its acceptance evidence exists. No future-version feature is implied by this file.

| Version | Deliverables and acceptance | Status |
|---|---|---|
| 0.1.0 | Windows portable EXE, project manager, workspace structure, CLI-based board discovery/core install, pin manager foundation, node canvas, basic C++ editor, project IR, graph validation, actual UNO compilation, `.ino` export | In development; per-test gates pending |
| 0.2.0 | BALIE installed/ZIP/core/repository library discovery; `library.properties`, libclang board-conditional API parsing; Verified/Inferred/Unresolved semantics; dynamic library nodes; typed sockets, dependencies, adapter metadata, cached hashes | Partial: metadata scanner, header inference, curated Wire adapter, typed numeric/boolean IR variables; no libclang/universal adapter codegen |
| 0.3.0 | Real flowchart semantics with shared IR, double-click editing to visual/source, function blocks, branches, loops, events/interrupts, breakpoint tracing, graph/flowchart arbitration | Partial: structured decisions, repeats, call-graph and bounded trace; graph adds Uno ADC/threshold comparisons; no arbitrary connector flowchart engine |
| 0.4.0 | Logic step simulator, virtual I/O, optional supported hardware simulator adapters, pin/peripheral model expansion, measured/estimated resource advisor, growth forecast with retention/rotation, SD recommendations | Partial preview: working virtual logic and forecast, no hardware simulator or SD codegen |
| 0.5.0 | Capability-driven WYSIWYG Web UI composer, responsive layout, layers, states, provisional `???` bindings, semantic widgets and auto-binding, asset optimization/import, live device/browser preview | Planned |
| 0.6.0 | Audio/sound feedback conversion: buzzer/PWM/DAC/I²S/SD/web; reusable smart components, asset hash deduplication, guided SD bus/integration, board migration report and snapshots; workspace links | Planned |
| 0.7–0.9 | Multi-target compatibility + per-core pin provenance and voltage checks; isolation/CLI supply-chain audit; manual code reconciliation, test fixture growth, multi-file source, perf/2GB benchmarking, portable Windows packaging | Planned |
| 1.0.0 | External hardware acceptance, vetted licenses, signed distribution where available, clean Windows tests, complete Arduino IDE export and recovery validation | Planned |

**Cross-cutting requirements:** project CRUD + templates/recent/workspaces/ZIP/snapshots; offline library platform installation from cached packages; peripherals ADC/DAC/I²C/SPI/UART/I²S/SDMMC; safe shared-resource identification; full Monaco-like code tooling; WYSIWYG state, groups and remote security; original assets/fonts; serial monitor and debugger; asset deduplication; filesystem rollover and power loss; multi-device workspace targets, firmware stability and reliable source maps. These remain explicit backlog items, not silently dropped.

**Preview constraints:** currently one project active at a time, basic listing and create/open/save/snapshots/export; no delete, rename, ZIP or crash-journal replay GUI; generated-only pin profiles have only Uno R3 partial trusted mapping. Do not treat graph checks as complete resource collision proof.
