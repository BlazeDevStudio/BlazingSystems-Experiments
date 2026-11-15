# PHX-HARDWARE handover — quarantine append ambiguity latch

Date: 2026-11-15 UTC  
Branch: `phoenix/hardware-quarantine-ambiguity-latch-20261115`  
Base: `phoenix/hardware-pending-canonical-fields-20261115@df0a239db926f1c68fcbe8e3dbc603c4e0929bf6`

## Proven defect

A short LittleFS append or failed post-write readback retained the pending coin
journal, but did not enter recovery mode. A later loop retry could append a
second record to an already partial or unverifiable quarantine log and then
clear the pending journal. That converted an ambiguous write into destructive
evidence loss without operator reconciliation.

## Change

- Refuse quarantine appends while `journalRecoveryRequired` is set.
- Latch recovery mode after a short append, verification-open failure, size
  mismatch, seek failure, byte mismatch, or failed readback.
- Keep the pending coin journal and relay fail-closed behavior unchanged.
- Extend the exact-source fake-LittleFS lab from thirteen to fourteen scenarios
  per board.
- For every post-write ambiguity, retry with the injected fault removed and
  prove the log bytes and clear-attempt count remain unchanged.
- Cover an already-latched recovery state explicitly.

No shared API, ACK/schema, server, finance, GPIO, persistent record layout,
migration target or release file changed.

## Evidence classification

The failure injection is **SIMULATED**. Exact-source host tests and target
compiles become **CI VERIFIED** only after exact-head jobs pass. Physical
LittleFS durability, electrical pulse/recovery and power-cut behavior remain
**NOT TESTED**.

## Mandatory remaining gates

- Independent QA reproduces the ambiguity latch and non-mutating retry at the
  exact PR head.
- Physical noncustomer electrical pulse/recovery testing.
- 150 controlled power cuts.
- 30-device 24-hour soak.
- Protected antirollback signer and independent witness.
- Durable v1-to-v2 accounting/replay migration.
- Independent QA, release and Master acceptance plus owner approval.

No merge, flash, reset, live money, production migration, deployment, signing,
release tagging or production-readiness claim is authorized.
