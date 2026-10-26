# Blaze MCU Studio — v0.1.0 Preview (development)

**Blaze Systems · Windows 10/11 x64 · offline-first Arduino graphical IDE**

An independently implemented, lightweight Electron desktop foundation with a node canvas, project history, a target-board picker based on Arduino CLI, conservative pin checks, user-owned C++ source preservation, real compiler invocation and standard `.ino` export.

**Important status:** Initial code is development-stage. No physical board verification is claimed. See [TEST_REPORT](docs/TEST_REPORT.md) for actual evidence. No public release should be labeled working until a Windows runner produces an EXE and the required Arduino Uno compile passes.

## Build / run

Install Node.js 22+ and Git, then run `npm install`, `npm test`, `npm start`. The Windows build workflow packages a **portable EXE**, not a PowerShell launcher, with a bundled Arduino CLI binary (board cores must be installed or cached). Run `npm run dist:win` on Windows to build the EXE. When CLI binaries/board cores are already installed, normal sketch editing and compilation are offline.

## First complete example

1. Create a project named `Blink` and select **Arduino Uno** (or another installed FQBN).
2. If the Arduino AVR core is missing, open **Board Manager** and install `arduino:avr`. This step requires connectivity unless packages are already cached.
3. In **Nodes**, inspect `Loop Start → Pin Mode D13 OUTPUT → Write HIGH → Delay 1000 → Write LOW → Delay 1000`.
4. Select **Validate**. Switch to **C++ Source** to review generated `.ino` and optionally insert user-owned code.
5. Select **Compile** to invoke the installed actual Arduino toolchain. Output and errors appear in the diagnostic panel.
6. Select **Export .ino** and choose a folder; open `<folder>/Blink/Blink.ino` in Arduino IDE. The export operates without the studio running. Existing exported sketch folders are never overwritten; choose a new destination.

## Scope and safeguards

The preview supports a *linear execution chain*; branches, conditional semantics, flowchart round-tripping, hardware simulation, external library semantic indexing and WYSIWYG web composition are scheduled for later milestones. Switching to manual-source ownership stores an independent full sketch and never reverse-parses C++. Unknown pin profiles are explicitly reported as unknown. No hidden firmware upload or hardware switching is performed by the studio.

All source files are original except third-party runtime/toolchain dependencies downloaded during the controlled Windows build. Electron is MIT licensed. Arduino CLI is Apache-2.0 licensed. The application includes no copied Arduino IDE images or official logos.
