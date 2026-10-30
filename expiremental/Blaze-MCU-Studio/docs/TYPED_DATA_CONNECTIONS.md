# Typed scalar data wires — v0.4.5

## Implemented (narrow, executable first step)

The visual **Nodes** canvas now has separate execution ports and amber **Value Out → Value In** sockets. A user can click the output and input in sequence, or drag the output socket onto an input. Currently supported producers: **Analog Sample** (`long`) and **Set Variable** (`long` or `float`); supported consumer: **Threshold Output** (`numeric measurement`). The linked producer's declared variable overrides the consumer's manual variable selector while the wire is present. Disconnecting restores the saved manual selector. This is a consciously limited, working subset, not an arbitrary multi-port graph framework.

The shared `graph.dataEdges` IR contains explicit records `{from,to,out:'value',input:'measurement'}`; historical projects without the field continue to load. Connections are represented by the saved project, C++ generation, virtual simulation and the canvas from the same record. Manual source ownership always preserves the original text. Exported Arduino `.ino` firmware does not rely on Blaze MCU Studio running.

## Fail-closed invariants

- Only a recognized output socket may connect to a recognized numeric input. Boolean outputs cannot feed numeric thresholds; unsupported arbitrary C++ expressions are never accepted as links.
- Exactly **one** data wire may drive a measurement input. Dangling endpoints and unknown socket types are errors.
- The producer must execute **before** the consumer in the current linear execution sequence; a late or unreachable producer cannot silently supply stale data.
- Variable names and types must be valid through the existing typed variable IR. Invalid data wiring prevents **visual** source generation, compilation and logic simulation until corrected.
- Connections cannot promote unverified board capabilities or physical safety. No electrical I/O, real sensor status or custom C++ reverse translation is implied.

## Evidence gates

`tests/typed-data-links.test.cjs` exercises codegen that **changes the compared C++ variable**, virtual behavior that switches from HIGH to LOW, invalid types, malformed/dangling sockets, order, multiple writers, import/export persistence, legacy compatibility and manual-source preservation.

`npm test` must pass alongside `node --check renderer/app.js`. Windows CI must compile `GeneratedTypedDataWire.ino` through the actual Arduino Uno core, then launch a packaged EXE and execute an actual renderer click → connect → inspector → save/reopen test. Synthetic browser events exercise real handlers but **do not prove all physical mouse or accessibility interactions**.

## Still missing

Multi-output typed math, reusable custom node interfaces, control-flow branching/reconvergence within Nodes, named functions, a first-class unit type system, arbitrary library-defined connectors, visual reverse-parsing of custom C++, and board-specific behavior beyond the existing supported profiles remain future work. The present implementation does not mislabel any of them as accepted.
