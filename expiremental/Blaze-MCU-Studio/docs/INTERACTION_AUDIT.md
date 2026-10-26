# First-use workflow audit — v0.4.1

## Defects reproduced from user screenshots (2026-10-26)

1. **Only Uno appears** despite Arduino CLI being detected. Root cause: old `board listall` only lists boards whose package cores are installed, then replaced an empty response with one hardcoded Uno option. Repair: dynamic CLI installed catalog plus clearly labeled *uninstalled* starter targets, core-selection/install controls and free text filtering. Installed != electrical capability verified.
2. **Palette does not drag**. Root cause: palette buttons had onclick only, lacking `draggable`, `dragstart`, canvas `dragover` and `drop`. Repair: real HTML DragEvent/DataTransfer event handlers and scoped project-owned node insert, with click fallback.
3. **Cannot select/edit blocks in first-run**. Selecting a canvas node required an open project, which was obstructed by the missing boards. Repair includes board-independent new-project selection and automated create/drag/select/inspector/save/reopen GUI acceptance.
4. **Libraries empty**. Root cause: scan only examined Documents/Arduino/libraries, omitting Arduino15 installed platform bundled libraries. Repair adds bounded, read-only platform library enumeration; signature interpretation remains inferred, not compile-verified.

## Release gate

Local unit tests passing is necessary but insufficient. Windows acceptance must prove actual packed Electron `newProject -> boardSearch -> confirmNew -> drag palette block -> inspector edit -> save -> reload` plus real Arduino Uno compile, all on one exact commit and with attached logs. No production acceptance or v0.5 milestone claim.

## Remaining limitations

Does not convert C++ libraries into verified executable nodes; only four palette block types, no arbitrary graph branches, no ESP library/cross-target compilation guarantee, no physical hardware tests, no RAM footprint measurement. No automatic privilege bypass or unsafe external package execution on import. Board-specific electrical pin maps not universal.
