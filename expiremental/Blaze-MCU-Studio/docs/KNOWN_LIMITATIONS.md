# Known limitations — v0.1.0 development

- Windows packaging and Windows GUI launch must be verified by an actual Actions run; do not call this a release without success logs.
- Only linear connected nodes are compiled; no conditional edge types, typed socket network, events beyond repeat-loop, or flowchart canvas.
- Source editor is a basic multiline C++ editor without Monaco completion or navigation. Visual code is read-only; advanced users may switch to full manual ownership.
- Project browser can create/open; save history and export are implemented. Rename, delete, duplicate, ZIP import, manual recovery UI and multi-tab workspace remain pending.
- Uno R3 digital pins D0–D13 have a partial profile. Other boards can be discovered/compiled if CLI has a core, but pins are marked unverified.
- Arduino CLI binary is packaged on Windows CI from pinned releases; MCU board cores are not bundled, and first install may require internet.
- Hardware-level safety, simulator fidelity, RAM under 2 GB, system-wide browser controls, and a clean Windows GUI run have not been measured until specific acceptance runs prove them.

- Arduino CLI host binary cannot currently be downloaded in the local execution container (DNS resolution of github.com fails); Arduino compilations require a Windows GitHub Actions runner or other authorized host.
- Windows GUI and 2-GB-RAM performance are not verified. No EXE was built locally.
- Export always refuses existing sketch directories to preserve user code; overwrite reconciliation UI is future work.
