# Changelog

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
