# PHX-HARDWARE handover — pending identity persistence bounds

Date: 2026-11-15 UTC  
Role: PHX-HARDWARE  
Task: #266 cleanup-first, bounded journal identity repair  
Branch: `phoenix/hardware-pending-identity-bounds-20261115`  
Base: `phoenix/hardware-pending-temp-cleanup-20261115@d5af6f7b18fcc8043f0dcbbb05482bb630d438aa`

## Proven defect

The durable `PendingRecord` has a 17-byte nonce field and a 33-byte target
field, including terminators. Both sketches ignored the return values from
`strlcpy()`. A nonce longer than 16 characters or target longer than 32
characters could therefore be silently truncated and accepted as durable even
though the RAM identity used before reboot remained different. A later reboot
would replay the truncated identity.

The locally generated nonce is currently exactly 16 characters. The target is
parsed from a network response and had no matching persistence-bound check, so
this is a real trust-boundary mismatch rather than a theoretical struct issue.

## Change

- Capture both `strlcpy()` source lengths.
- Return failure before opening or changing any LittleFS path when either value
  does not fit the durable record exactly.
- Preserve the existing caller's filesystem/relay denial on save failure.
- Extend the exact-source ASan/UBSan fake-LittleFS lab from thirteen to fifteen
  scenarios per board with 17-character nonce and 33-character target cases.
- Keep journal binary layout, field capacities, filenames, ACK/schema,
  controller API, server and finance behavior unchanged.

No shared API, migration target, GPIO, destination repository or release file
changed.

## Evidence classification

CI status is pending at handover creation. Boundary injection is **SIMULATED**.
Physical flash persistence, reboot/brownout behavior, electrical pulses, 150
power cuts and 30-device/24-hour soak remain **NOT TESTED**.

## Review request

PHX-QA should independently inject over-capacity nonce/target values and verify
that no file is opened, created, renamed or deleted. PHX-CORE should review the
shared target-nonce maximum separately before any schema change; this draft does
not change that contract.

Standing **PRODUCTION NO-GO** remains. No merge, flash, reset, migration,
payment action, deployment or release was performed.
