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
