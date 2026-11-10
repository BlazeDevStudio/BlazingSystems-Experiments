# BALIE — implemented foundation and limits

Implemented: read-only `library.properties` parsing, bounded public `.h/.hpp` declaration scanning, SHA-256 source fingerprint, architecture declaration compatibility, dynamic candidate node metadata, explicit `Inferred` confidence, scan of typical Arduino sketchbook libraries and user-selected library directories. No imported C++ is executed during indexing.

Not implemented: conditional compiler analysis with the board's real compile flags, AST/libclang semantics, class instance creation, initialization sequencing, advanced dependency resolution, repository or ZIP imports, verified dynamic function-call code generation, platform-core library enumeration, adapter persistence. The current candidate palette is informational and **not compile-authorized**.

A syntax-derived signature cannot establish hardware correctness. The `Verified` state is reserved for compile-confirmed selected board configurations and verified adapters.


## Curated adapter exception (v0.4.2)
The separate, explicitly reviewed Uno `Wire` register-write node is executable as defined in `CURATED_LIBRARY_ADAPTERS.md`, subject to real compile evidence. This does **not** promote syntactically inferred BALIE APIs to executable nodes.
