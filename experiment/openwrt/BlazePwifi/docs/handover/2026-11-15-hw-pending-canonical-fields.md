# PHX-HARDWARE handover — canonical pending identity fields

Date: 2026-11-15 UTC  
Branch: `phoenix/hardware-pending-canonical-fields-20261115`  
Base: `phoenix/hardware-pending-exact-size-20261115@12d374d3332fbf8774ea5efdf7cdf5e95611b0a5`

## Proven defect

The pending-record writer zero-initializes `PendingRecord` before copying nonce
and target. The reboot parser required a NUL terminator and a minimum visible
length, but accepted nonzero bytes after that first terminator. Loading through
`String(char*)` discarded the suffix, allowing distinct checksum-valid disk
records to collapse to the same transmitted nonce or target identity.

That representation cannot be emitted by either production writer and is
ambiguous/corrupt evidence. It must fail closed for reconciliation.

## Change

- Require every byte after the first nonce terminator to remain zero.
- Apply the same canonical zero-tail rule to the target field.
- Preserve exact file-size, pulse-range, visible-length and checksum checks.
- Extend the exact-source ASan/UBSan fake-LittleFS lab from nineteen to
  twenty-one scenarios per board.
- Add separate checksum-valid dirty-nonce-tail and dirty-target-tail cases.
- Prove rejection without removal, rename or recovery-state mutation.

No journal layout, filenames, shared API, ACK/schema, server, finance, GPIO,
migration target or release file changed.

## Evidence classification

The failure injection is **SIMULATED**. Host-lab and Arduino compile status
become **CI VERIFIED** only after exact-head jobs pass. Physical LittleFS,
electrical pulse/recovery and device behavior remain **NOT TESTED**.

## Mandatory remaining gates

- Independent QA reproduces both hidden-suffix rejections at the exact PR head.
- Physical noncustomer electrical pulse/recovery testing.
- 150 controlled power cuts.
- 30-device 24-hour soak.
- Protected antirollback signer and independent witness.
- Durable v1-to-v2 accounting/replay migration.
- Independent QA, release and Master acceptance plus owner approval.

No merge, flash, reset, live money, production migration, deployment, signing,
release tagging or production-readiness claim is authorized.
