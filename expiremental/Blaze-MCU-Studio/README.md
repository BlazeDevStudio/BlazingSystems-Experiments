# Blaze MCU Studio — v0.3.0 Preview (Development, not production)

Blaze Systems · Windows 10/11 x64 · offline-first visual Arduino firmware IDE.

**Readiness:** Expanded beyond v0.1.0 but NOT the complete master-directive product. A version label is not a claim of 50% functionality. The project deliberately lacks full Clang-based C++ understanding, trusted universal pin mappings, a general purpose typed node graph, mature graphical flowchart editor, and physical board acceptance. Consult `docs/KNOWN_LIMITATIONS.md` before use.

## Implemented in this preview

- Real portable Windows desktop EXE packaging (Electron), local project creation/open/save, rename, duplicate, recoverable deletion, five history snapshots, non-overwriting `.ino` export.
- Selected target FQBN via dynamic Arduino CLI discovery; installed board-core management and real Arduino CLI firmware compilation with actual target compiler.
- Arduino Uno partial digital pin model, deterministic linear node C++ generation, user-owned manual C++ editing and protected custom C++ regions.
- **Structured flowchart editor** with executable steps, GPIO output, delay, digital-input branch, bounded repeat, return and optional graph function call; the same source exporter/compiler pipeline; bounded step traces, not hardware simulation.
- **BALIE read-only foundation:** installed-sketchbook and explicitly chosen library directory indexing, `library.properties` architecture metadata, bounded C++ header declaration inspection, SHA-256 fingerprint, candidate function-node definitions. Output is **inferred** and requires a verified adapter before code generation; no arbitrary imported library execution during indexing.
- Board migration warning report before switching, unknown board pin model never silently verified.

## Installation / operation

Windows users: download the portable `Blaze-MCU-Studio-0.3.0-Windows-x64.exe` from the verified GitHub Actions artifact/Google Drive. No Node/Python/PowerShell is needed to start the application. The executable is unsigned; Windows may warn. The Arduino CLI binary is bundled, but board cores and third-party libraries must be installed or cached separately. Initial installs can require internet; subsequent editing and compilation can be offline.

Source: Node.js 22+; `npm install`, `npm test`, `npm start`, `npm run dist:win`. No subscription or cloud login required.

## Critical boundaries

- Full user-owned manual C++ never reverse-parsed; visual edits cannot silently overwrite it.
- Flowchart decision and repeat are structured AST blocks; arbitrary wire-based reconvergence and interrupt handling are not implemented.
- BALIE header signatures can be incomplete or incorrect under preprocessor macros, overloads and templates. Marked Inferred, never Verified without board compilation.
- Digital-input flowchart branch defaults to `INPUT`, requiring external circuit stabilization. Electrical safety requires physical inspection.
- Core installation and firmware compilation may execute code from third-party platforms; never use untrusted dependencies without isolation.
- Project deletion moves data to a local recoverable `_recovery` folder; backup that folder with your projects.
- Do not interpret passing Windows build/tests as hardware simulation, 2 GB memory certification, or a production release.

Documentation and tests live under `docs/` and `tests/`.
