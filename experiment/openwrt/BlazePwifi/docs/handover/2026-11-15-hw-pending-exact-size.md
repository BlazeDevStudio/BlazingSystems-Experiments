# PHX-HARDWARE handover — exact pending journal size

Date: 2026-11-15 UTC  
Branch: `phoenix/hardware-pending-exact-size-20261115`  
Base: `phoenix/hardware-pending-pulse-bounds-20261115@22f7a113c5ab2c85bdc13a702177c46838032f47`

## Proven defect

Both production `readPendingFile()` implementations read exactly
`sizeof(PendingRecord)` bytes and validated the prefix checksum, but did not
check the complete file size. A checksum-valid fixed record followed by one or
more trailing bytes was therefore accepted as an authorized pending coin
record. Firmware writers only create fixed-size records, so a longer file is an
ambiguous/corrupt journal and must fail closed for reconciliation rather than
silently ignore the tail.

## Change

- Capture `File::size()` before reading each pending journal.
- Require the stored size and bytes read to equal `sizeof(PendingRecord)`.
- Keep checksum, pulse, nonce, target, journal layout, filenames and recovery
  behavior unchanged.
- Extend the exact-source ASan/UBSan fake-LittleFS lab from eighteen to
  nineteen scenarios per board.
- The new negative case appends one byte to a checksum-valid record and proves
  parser rejection with zero removal, rename or recovery-state mutation.

No shared API, ACK/schema, server, finance, GPIO, migration target or release
file changed.

## Evidence classification

The host lab and Arduino target compiles are **CI VERIFIED** only after the
exact-head jobs pass. The injected oversized record is **SIMULATED**.
LittleFS power-loss durability and all physical device behavior remain
**NOT TESTED**.

## Mandatory remaining gates

- Independent QA reproduces the one-byte-tail rejection at the exact PR head.
- Physical noncustomer electrical pulse/recovery testing.
- 150 controlled power cuts.
- 30-device 24-hour soak.
- Protected antirollback signer and independent witness.
- Durable v1-to-v2 accounting/replay migration.
- Independent QA, release and Master acceptance plus owner approval.

No merge, flash, reset, live money, production migration, deployment, signing,
release tagging or production-readiness claim is authorized.
