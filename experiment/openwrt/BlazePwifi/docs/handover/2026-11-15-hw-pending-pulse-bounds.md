# PHX-HARDWARE handover — pending pulse-count bounds

Date: 2026-11-15 UTC  
Role: PHX-HARDWARE  
Task: #266 cleanup-first, bounded journal record repair  
Branch: `phoenix/hardware-pending-pulse-bounds-20261115`  
Base: `phoenix/hardware-pending-identity-min-20261115@94b5247a9d457baf8c2eecc5a0b4ced5c2783812`

## Proven defect

The production `readPendingFile()` parser rejects persisted pulse counts above
20. Both `savePending()` implementations rejected zero but did not apply the
same upper bound. Normal GPIO intake currently stops incrementing at 20, but a
corrupted RAM value or later alternate caller could still be accepted as
durable and then rejected as corrupt by the same firmware after reboot.

## Change

- Reject `pendingPulses > 20` before constructing or writing a durable record.
- Perform the check before any LittleFS open, create, remove or rename.
- Retain the existing identity lower- and upper-bound checks from the parent
  drafts.
- Extend the exact-source ASan/UBSan fake-LittleFS lab from seventeen to
  eighteen scenarios per board with a 21-pulse case.
- Keep journal binary layout, filenames, ACK/schema, controller API, server and
  finance behavior unchanged.

No shared API, migration target, GPIO behavior, destination repository or
release file changed.

## Evidence classification

CI status is pending at handover creation. Boundary injection is **SIMULATED**.
Physical flash persistence, reboot/brownout behavior, electrical pulses, 150
power cuts and 30-device/24-hour soak remain **NOT TESTED**.

## Review request

PHX-QA should independently inject a 21-pulse RAM value and verify that no
filesystem path is opened or mutated. PHX-CORE continues to own shared
accounting and signed durable ACK semantics.

Standing **PRODUCTION NO-GO** remains. No merge, flash, reset, migration,
payment action, deployment or release was performed.
