# Visual programming — current implementation

Node graph currently generates a linear sequence (pinMode, digitalWrite, delay, comment). Flowchart is a *distinct editor over the same persisted project IR*, selectable as the visual firmware source. Structured flowchart blocks: setOutput, write, wait, branch (digitalRead HIGH/LOW), bounded repeat, comment, end, optional callNodes.

Flowchart setup emits `pinMode` and input initialization, loop emits typed control flow. The optional callNodes invokes a generated function from the linear node graph; it fails closed when node validation fails. User-authored manual C++ remains immutable when switching visual modes. Logic trace is a bounded value-level interpreter and does not emulate the MCU, clock or electrical signals.

Not yet delivered: arbitrary directed graph joins, function definitions, data sockets, interrupt handlers, breakpoints tied to firmware PC, full round-trip source/flowchart synchronization, live node-glow stepping.
