# Source-to-visual navigator (v0.4.8)

This feature is inspired by the **learning workflow** in [ESP Labs Web](https://github.com/agharsallah/esp-labs-web), an independently maintained MIT-licensed ESP32-S3 bench guide (copyright 2026 Abderrehmen Gharsallah). **No ESP Labs code, designs, images, icons, or firmware were copied or bundled.** The UI and source-attribution implementation here are original to Blaze MCU Studio. If future versions incorporate third-party source/assets, retain original LICENSE and attribution according to MIT and the actual asset licenses.

In a visually generated project, open **C++ Source**. The navigator enumerates *only generator-owned statements* (node and flowchart IDs). Click the chip to select the exact `.ino` line, or **Block** to focus the visual source. In the graph Inspector click **Show generated C++**; flowchart blocks have a **C++ source** action. Clicking generated code reveals its confirmed source block; it does not attempt to understand arbitrary C++ or user-owned code.

**Trust boundary:** the compiler emission process supplies the trusted `setup`, `loop`, and optional `blazeNodesTick` statement arrays. Source line mappings are derived from these exact arrays and checked for byte-for-byte identity against emitted lines. Source comments in `userPrelude`, `userSetup`, `userLoop`, or full manual-mode code are never parsed for visual attribution, even if they contain `// node:id` or `// flow:id`. Neither the source navigator nor a simulator claims the firmware actually ran on physical hardware.

**Performance:** no Monaco, React, 3D engine, network fetch, or cloud processing is added. Mapping is O(generated source lines), with the visual chip list bounded to the first 200 blocks. Full manual C++ stays editable and is never reverse-translated.

**Current limits:** compiler diagnostics are not yet remapped to exact nodes; only generator-owned statements with explicit ID markers are navigable; user-authored lines and Arduino core internals are not inferred. Requires packaged GUI acceptance, Arduino CLI compilation, and separate physical device testing for hardware claims.
