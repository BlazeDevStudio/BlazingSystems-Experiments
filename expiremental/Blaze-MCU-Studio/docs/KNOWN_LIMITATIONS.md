# Known limitations — v0.3.0 Preview

- Windows packaging and Windows GUI launch must be verified by an actual Actions run; do not call this a release without success logs.
- Node graph remains linear, but structured flowchart supports if/else, bounded repeat, call-graph, and GPIO. General typed connectors, arbitrary reconvergence, events/interrupts and graph-to-flowchart round-tripping are not implemented.
- Source editor is a basic multiline C++ editor without Monaco completion or navigation. Visual code is read-only; advanced users may switch to full manual ownership.
- Project browser can create/open; save history and export are implemented. Rename, recoverable delete and duplicate are implemented. ZIP import, multi-tab workspaces and manual snapshot GUI remain pending.
- Uno R3 digital pins D0–D13 have a partial profile. Other boards can be discovered/compiled if CLI has a core, but pins are marked unverified.
- Arduino CLI binary is packaged on Windows CI from pinned releases; MCU board cores are not bundled, and first install may require internet.
- Hardware-level safety, simulator fidelity, RAM under 2 GB, system-wide browser controls, and a clean Windows GUI run have not been measured until specific acceptance runs prove them.

- Arduino CLI host binary cannot currently be downloaded in the local execution container (DNS resolution of github.com fails); Arduino compilations require a Windows GitHub Actions runner or other authorized host.
- Windows GUI and 2-GB-RAM performance are not verified. No EXE was built locally.
- Export always refuses existing sketch directories to preserve user code; overwrite reconciliation UI is future work.

- BALIE is bounded read-only header scanning; it cannot semantically model templates/macros or guarantee constructor/initialization sequencing. Its dynamic library node candidates are not executable until verified adapter codegen exists.
- Board migration preflight does not rewrite code or resolve library incompatibilities automatically.
- No clean Windows GUI runtime smoke test, 2GB RAM peak test, or physical MCU tests have yet passed for v0.3.0.
- Bundle size largely reflects Electron/Chromium and the Arduino CLI binary. It is not a measure of board catalog or feature coverage.
