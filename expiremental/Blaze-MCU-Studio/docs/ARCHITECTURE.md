# Architecture v0.3.0

**Reasoned stack choice:** Electron/Chromium + plain JavaScript/HTML/CSS for the v0.1.0 vertical slice instead of the initially proposed Tauri 2 + React + Monaco + Rete. This retains a normal Windows EXE and OS-native dialogs while avoiding multiple UI runtimes and Rust dependencies in the foundational release; runtime RAM under 2 GB is an unverified target, not a measured claim. Electron single instance WebContents; renderer sandbox with context isolation, narrowly allowed IPC channels, no network surface. Assets are pure CSS, no proprietary icon dependencies. Future editor replacements retain the versioned IR.

- `renderer/` UI node canvas, property inspector, board manager, source editor and diagnostics.
- `electron/` audited IPC allowlist, dialogs and isolated preload.
- `core/project.cjs` shared backward-compatible project IR, compile codegen and conservative static validation.
- `core/storage.cjs` local project storage, atomic JSON replacement, bounded snapshots and deterministic sketch export.
- `core/flowchart.cjs` structured branch/repeat AST, validation, C++ and bounded logic trace; shares target/source ownership with node engine.
- `core/balie.cjs` read-only library metadata/header indexing; no code execution; inferred confidence only.
- `core/board.cjs` migration preflight, conservative per-FQBN pin support.
- `core/arduino.cjs` process-isolated argv-only invocation, bounded output/time and dynamic board discovery.
- `tests/` Node built-in test runner, no external testing dependency.

Project JSON contains `id, name, fqbn, graph.nodes, graph.edges, source.mode, source.manualSource, source.userPrelude, source.userSetup, source.userLoop, pins, libraryDependencies`. The visual graph is a sequence of typed execution actions. If `source.mode=manual`, generation uses the user-owned code verbatim. No ambiguous bidirectional C++ parser is claimed. Generated code remains read-only. Source snapshots are kept in each project `history/`; board changes do not rewrite code. Sketch compilation generates temporary source in OS temp and calls actual `arduino-cli compile --fqbn ...` with no shell. Projects persist in Electron userData `projects/`.

**Boundaries:** validation is model-level, not firmware-emulation or physical acceptance. A real compiler failure is reported as failure. Arbitrary imported C++ can perform machine-controlled toolchain behavior during compilation; users must not compile untrusted third-party projects on a privileged machine. Core installs download official platform dependencies through Arduino CLI only on user action.
