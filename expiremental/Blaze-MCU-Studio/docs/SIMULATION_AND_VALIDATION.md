# Logic simulation and validation — v0.4.0

## Implemented

- Deterministic, bounded virtual execution of active node graph or structured flowchart. No arbitrary C++ evaluation and no real firmware execution.
- Virtual GPIO states HIGH/LOW and configured modes; unset inputs **explicitly default to LOW** for repeatable demonstration, not because LOW was measured.
- Virtual time advanced by Delay actions; no claim about actual CPU timing or electrical propagation.
- Stepping, run-with-budget, trace of executed block identities and effects, before-block breakpoints, pause/resume, reset, virtual input injection between steps.
- Flowchart branch, bounded repeat, write, setOutput, comment, wait, end; node-graph pinMode/digitalWrite/delay/comment.
- Bounded session state and trace history. Unknown library code, flowchart `callNodes`, physical sensor output, and interrupts are not emulated. `callNodes` is explicitly marked as not emulated (code generation still supports it).

## Verification distinctions

1. **Logic simulation** tests this interpreter only. These results do not validate program binaries or electrical safety.
2. **Real compilation** invokes Arduino CLI with a specified installed board FQBN; this checks source/toolchain compatibility, not physical behavior.
3. **Physical hardware acceptance** requires actual connected MCU and peripherals. None is claimed for v0.4.0.

The GUI's smoke test exercises real IPC between packaged Electron renderer and main process for create/open/codegen/logic simulation/resource forecast, but is not a hardware simulator acceptance test.
