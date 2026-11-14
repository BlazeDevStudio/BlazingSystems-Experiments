# PHX-HARDWARE quarantine recovery contract — LAB ONLY

Stacked on open draft PR #283, not merged into main or the separate deny-first PRs #239/#254.
Both firmware quarantine functions now preserve the uncredited pending nonce, target, pulses and existing journal if:
the filesystem is absent, the append cannot open, the record is too large, the write is short, or readback fails.
The event is cleared only after a successful append and exact byte readback. Logs name a failure stage without printing controller keys.
Error reason CR/LF is flattened and capped at 96 characters to avoid multiline log injection and unbounded journal entries.

Readback is a software sanity check, NOT flash power-cut durability, and does not establish crash-atomic money accounting.
Successful signaled coin ACKs, independent monotonic witness, replay/rollback, physical relay polarity, 150 power cuts,
30-device 24-hour soak, and v1->v2 migration remain NO-GO. PR #283 register/poll response_sig incompatibility remains unresolved.

PHX-QA: independently execute source-extracted LittleFS append-failure, short-write, readback and reboot test cases.
No flashing, customer or cash installation, release signing, merge or production deployment is authorized.
