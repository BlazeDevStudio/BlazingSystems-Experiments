## v0.4.2 executable library work (new checkpoint)

- Added user-editable **Wire I2C register-write** node restricted to Arduino Uno pending a real CI compilation gate; bounded address/register/value and captured endTransmission status.
- Added **PWM write** and **Serial print** editable nodes with generated Arduino C++ and virtual-trace semantics.
- The Libraries view includes a separate curated Wire adapter insertion control, alongside BALIE read-only signature discovery.
- Acceptance requires compiling generated Wire/PWM/Serial firmware through actual AVR core, and Windows GUI click/edit/save tests. **A Linux Node test pass alone is not proof of that gate.**
- See [curated adapter contract](docs/CURATED_LIBRARY_ADAPTERS.md).

# Blaze MCU Studio v0.4.2 — Interaction Repair (development branch)

**This update repairs concrete failures demonstrated on Windows v0.4.0. It is not a complete universal visual MCU IDE or production release.**

## First-run and board selection

- The New Project dialog now lists *installed* board FQBNs discovered from Arduino CLI and seven explicitly labeled **uninstalled starter targets**, including ESP8266 Generic, NodeMCU, ESP32 Dev Module, and ESP32-S3 Dev Module. Starter targets are only installation entry points, **not a claim of installed support**.
- Search/filter board names or FQBNs in the New Project dialog. The selected target is changeable later through migration warnings.
- **Install selected core** runs real Arduino CLI index refresh and core installation after user confirmation. The ESP8266 and ESP32 paths use official third-party package URLs passed per invocation instead of silently changing Arduino global configuration. Installation needs network access unless cached.
- Installing the platform reveals the actual dynamic board list returned by Arduino CLI. Future boards are not hardcoded; unrecognized boards may be supplied by installed package cores.
- The IDE can create a project targeting an uninstalled board, but **compilation will fail until the matching toolchain is installed**.

## Visual block interaction

- On an open visual project, **drag Pin mode, Digital write, Delay or Comment from the left palette onto Nodes**. Blocks are inserted at the drop position, appended to a supported linear execution chain, selected and their properties shown in Inspector.
- A simple click on a palette item also appends a block, for keyboard and pointer fallback. Click a canvas node or Edit to select it; change values in Inspector and save; select Output and Input connectors to reconnect a linear chain; drag an existing node header to reposition it.
- Visual modes are intentionally limited to linear node chains and a separately structured flowchart. This is **not** the future full typed multi-port programming network.

## Library discovery

Read-only BALIE now searches installed sketchbook libraries and installed Arduino package-core `libraries/` folders from Arduino15, plus manually inspected library directories. Header signatures remain **inferred** and cannot be inserted as verified executable adapter nodes. No third-party code is executed during scanning.

## Evidence and limitations

Source regression coverage includes board status parsing, source ownership, graphs, simulators, peripheral resource checks, and actual library roots. The Windows workflow runs a packaged Electron **DOM interaction gate** for create-project dialog, board catalog, palette drag-and-drop, inspector editing and persistence, in addition to actual Arduino Uno firmware compilation and EXE packaging. A synthetic DOM drag is not proof of every physical mouse or touch driver behavior, but tests real application UI handlers rather than only IPC.

No ESP8266/ESP32 core or library is preinstalled in the portable executable. RAM use on a physical 2 GB machine, physical MCU flashing, verified third-party library adapters, arbitrary graph branches, hardware emulation, and WYSIWYG remain unverified or unimplemented. Source is MIT and Electron/Arduino CLI retain their respective licenses.
