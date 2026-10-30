# Codebase cleanup — Electron boundary (October 31, 2026)

## Refactor already applied

- `electron/main.cjs`: app lifecycle, BrowserWindow security defaults, module composition only. No embedded GUI test script or long IPC handler registry.
- `electron/ipc-routes.cjs`: one owned-window gate for all 39 existing IPC channels, now grouped by capability. Untrusted webContents senders are denied; channel names and wire contracts are retained. Variable-validation results are computed once.
- `electron/gui-smoke.cjs`: original packaged-GUI acceptance logic, installed only when the explicit `BLAZE_MCU_SMOKE_FILE` environment variable is set.
- `tests/architecture-cleanup.test.cjs`: source-boundary checks and a mocked IPC contract test exercising sender rejection and route registration.

## Preservation rules

This is a behavior-preserving cleanup, **not** a feature milestone. No change to sketch generation, Arduino core versions, board safety profiles, manual C++ ownership, project format, or release artifacts. No production signing or main-branch merge.

## Remaining cleanup debt

- The renderer `renderer/app.js` is still a large controller mixing graph rendering, state, persistence, library UI, and event listeners. Split by domain only after integration tests verify real editing and save/reload on the target branch.
- Project and flowchart generation contain compact functions that need documented error boundaries; do not rewrite them while compiler gates are unstable.
- Core source files and imported libraries must remain offline-first and deny unsafe automatic execution.

## Verification gate

Source syntax/architecture and existing test suites must pass first, followed by exact-head Windows packaged UI acceptance and independent ESP compiler jobs. Do not claim CI passing based on previously successful heads.
