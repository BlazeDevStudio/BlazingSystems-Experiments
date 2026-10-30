## v0.4.5 — actual scalar node socket connections (under Windows acceptance)

- Draw amber scalar data wires from Analog Sample/Set Variable outputs to Threshold Output measurement inputs. The executable C++ and virtual simulator now resolve the linked variable instead of using a merely decorative wire.
- The GUI permits click-to-link and native drag/drop, rejects unsupported numeric types and late producers, and preserves links in saved projects.
- This is a first bounded **typed numeric link** foundation, **not** completed universal graph branching or multi-socket library intelligence.
- A new Windows compiler gate builds the exported typed-link Uno sketch and the packaged GUI gate connects and persists a wire.
- See `docs/TYPED_DATA_CONNECTIONS.md` for the contract and verification limits.

## v0.4.4 development checkpoint — ESP8266/ESP32 GPIO correctness

ESP8266 Generic/NodeMCU and classic ESP32 now have conservatively reviewed GPIO admission, safer startup Blink templates and a Pin Manager that surfaces boot-sensitive, input-only and flash-reserved pins. `docs/ESP_GPIO_ADMISSION.md` records evidence and limitations. The actual Arduino CLI ESP compile gate must succeed before firmware compatibility can be described as verified.

## v0.4.3 — typed state and sensor-to-output control (development, requires Windows acceptance)

- **Variables tab:** add persistent `long`, `float`, `bool` project variables with literal initial values, identity validation and dependency-aware deletion. Variables survive save/reload/export, use namespaced `blazeVar_` symbols, and are not reverse-parsed from custom C++.
- **Three executable graph blocks:** Set Variable, Analog Sample (Uno A0–A5 to `long`), Threshold Output (numeric comparison drives Uno D0–D13, plus warning on UART pins). All generate Arduino C++ through the shared engine and are available in the node canvas Inspector.
- **Template:** choose **Uno Analog Threshold Controller** during New Project to get an immediately connected A0→`sensorValue`≥512→D8 control circuit; the existing Blink and an Empty visual template remain.
- **Logic simulator:** inject independent virtual analog readings (0..1023), see typed variable state and resulting HIGH/LOW output; unset analog inputs are explicitly simulated as zero, **not measured values**.
- **Safety:** known conflicts with `Wire` on Uno A4/A5 are rejected; variables reject arbitrary C++ expressions; mismatched target types and unknown board mappings fail closed. No electrical behavior or analog noise is emulated.
- **Toolchain gate:** real Arduino CLI must compile the generated sensor threshold on Uno, plus generated Blink projects for Arduino Mega and Nano. Mega/Nano compilation does not certify electrical pin mapping. Actual Windows GUI input/edit/persist/virtual behavior acceptance required.

**Remaining:** full typed multi-port graph, graph branching/reconvergence, BALIE universal verified adapters, hardware simulation, WYSIWYG web editor, resource measurements on 2 GB PCs, and ESP8266/ESP32 compiler gating. This is not a production release.

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
