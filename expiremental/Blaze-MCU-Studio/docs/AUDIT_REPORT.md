# v0.3.0 independent source reconciliation and acceptance findings

## What 100 MB did and did not mean

The v0.1.0 portable 99 MB Windows EXE was predominantly the Electron/Chromium runtime plus the Arduino CLI executable. It did not contain hundreds of board cores or a semantic-library understanding engine. Size is not proportional to implemented functionality. Bundling every toolchain would dramatically expand the package and create update/licensing/offline maintenance problems; dynamic install/cache is the intended design.

## Previous baseline P0/P1 functional gaps

- P0: No BALIE at all; library intelligence documentation was a roadmap placeholder.
- P0: No conditional control-flow node graph or executable flowchart.
- P1: Only Uno D0–D13 partial mapping, no ESP pin safety.
- P1: No user-facing rename/duplicate/recovery.
- P1: No 2 GB RAM benchmark, clean Windows GUI start, full-platform evidence.
- P1: No rich C++ code editor, no hardware simulation, no WYSIWYG designer.

## v0.3.0 technical corrections

- `core/balie.cjs`: bounded library metadata/header scanning, architecture declarations and SHA256 fingerprints, untrusted imported code never executed by scanner. **Syntax confidence only**, not full semantic understanding.
- `core/flowchart.cjs`: bounded recursive AST, deterministic C++ branch/repeat and logic trace, strict type/pin/size validation and explicit handling of an optional node-chain call.
- `core/project.cjs`: source owner remains manual or visual. Visual selection is nodes or flowchart, preserving existing projects. Same source generation is used by Arduino CLI and export.
- `core/board.cjs`: migration preflight never invents verified pin capabilities.
- Project CRUD: rename, duplicate and move-to-recovery; no data destruction in normal delete action.
- UI: dedicated flowchart control-flow and library signature inspector; original vector-like CSS decorations used rather than unlicensed asset copies.

## Scope still incomplete (not hidden under a v0.3 label)

- BALIE not Clang-backed; no verified automatic C++ call-node codegen or dependency installations from ZIP.
- Flowchart is structured branches, loops and sequence, not an arbitrary general wire/join editor. No interrupt handlers, variables or breakpoints.
- No Monaco editor; no end-to-end code ↔ visual round-trip parser.
- No physical MCU simulation or peripheral hardware verification.
- No complete board electrical pin map or safe power electronics commissioning.
- No clean Windows GUI user-journey smoke or measured 2 GB peak working-set acceptance.

## Test evidence standard

Node built-in tests, host syntax checks, and static GUI surface checks are recorded separately from actual Arduino CLI Uno compile and real Windows EXE packaging. The latter require exact GitHub Actions run IDs and checksums. All claims that are not actually executed remain unverified. Do not treat package generation as production acceptance.
