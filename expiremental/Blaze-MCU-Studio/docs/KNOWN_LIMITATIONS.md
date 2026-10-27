# Known limitations — 0.4.0 Preview

A passing Windows build does not mean the universal MCU IDE is complete. **Source-level verified subset:** structured flowchart + linear nodes, incomplete library scanning, actual Arduino CLI compile and export, virtual logic simulation, basic resource forecast and bus planning.

- No instruction-level MCU simulation, electrical simulation, hardware peripheral emulation, real-world physical verification or timing accuracy. Simulator cannot execute user-owned manual C++ or `callNodes` body; simulation is source-logic only.
- No fully implemented BALIE adapters, compiler-conditional C++ AST, typed node connectors, broad hardware pinout profile catalog or pin-level voltage safety verification.
- No Monaco editor, general purpose arbitrary flowchart reconvergence, general interrupts/events/state-machine compilation, WYSIWYG HTML interface editor, multimedia processing or smart widget auto-binding.
- No automatic SD firmware/mount/error handling; planner creates only verified Uno-style pin reservation proposals.
- Boards discovered from Arduino CLI can be compiled **if** compatible platforms are installed, but board pin capabilities may be unknown.
- No verified performance on a 2 GB Windows machine. No signed EXE. No verified physical MCU flash or device upload.
- Other project management functions such as ZIP import/export, workspace tabs and snapshot GUI remain incomplete.
- Arduino CLI and board cores are third-party executables; treat installed dependencies and build scripts as potentially untrusted.
- File integrity and recovery are not yet fully journaled/durable against sudden storage failure; backups are recommended.

## v0.4.5 data-wiring scope
The new value sockets accept only declared numeric outputs from `readAnalog`/`setVariable` into the `thresholdOutput` measurement socket, and require producer-before-consumer in a linear active graph. They do not implement general graph branching, math nodes, concurrent subscriptions, user-defined functions or reverse C++ parsing. GUI drag/drop is tested using renderer events and not every physical HID environment.
