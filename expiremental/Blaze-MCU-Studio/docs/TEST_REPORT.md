# Test evidence ledger

## Local Linux

2026-10-26: `npm test` on Node.js v22.16.0: 24/24 passed after correcting a real export-parent-directory regression. `node --check renderer/app.js`, `node --check electron/main.cjs`, and `node --check scripts/export-example.cjs` completed without syntax errors. `node scripts/export-example.cjs <temp directory>` generated `GeneratedBlink/GeneratedBlink.ino` through project IR. See `evidence/local-tests.txt`.

Actual Arduino CLI board compilation remains **not run**: CLI unavailable locally, and this sandbox lacks DNS access to GitHub release artifacts. Windows GUI and portable EXE have not been tested or built.

## Windows

When run successfully, the Windows build job outputs portable `Blaze-MCU-Studio-0.1.0-Windows-x64.exe`; the workflow explicitly fails if an EXE is missing. It also downloads a pinned Arduino CLI, installs `arduino:avr`, compiles an independent Blink sketch, and uploads CLI logs plus SHA-256. This is a compile-only check, not a physical board flash or full GUI smoke test. An Actions *artifact* is not a GitHub Release.

## Post-audit corrections (2026-10-26)

- Export refuses existing sketch directories rather than replacing a user-owned `.ino`.
- Windows workflow now compiles both an IR-generated `GeneratedBlink` sketch and the independent checked-in Blink reference. The previously configured workflow compiled only the reference sketch.
- Project validation rejects whitespace-only names and invalid layout coordinates.
- GUI autosave serializes pending saves, snapshots each payload, and uses change revisions to avoid silently dropping edits during an in-flight save; board changes first persist the previous project.
- These changes require fresh local test evidence and a Windows runner before release.
