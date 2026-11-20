# PHX-HARDWARE handover — pending identity minimums

Date: 2026-11-15 UTC  
Role: PHX-HARDWARE  
Task: #266 cleanup-first, bounded journal identity repair  
Branch: `phoenix/hardware-pending-identity-min-20261115`  
Base: `phoenix/hardware-pending-identity-bounds-20261115@8029c583f185736e770e3412308416d5ac87c976`

## Proven defect

The production `readPendingFile()` parser rejects a persisted nonce or target
shorter than eight characters. Both `savePending()` implementations only
required those RAM strings to be nonempty. They could therefore report a
successful durable save for a record that the same firmware would classify as
corrupt and recovery-lock after reboot.

The locally generated nonce is 16 characters. The target is parsed from a
network response and did not share the durable parser's lower bound, so the
mismatch crossed the network-to-persistence trust boundary.

## Change

- Require both pending nonce and target to be at least eight characters before
  constructing or writing the durable record.
- Perform the check before any LittleFS open, create, remove or rename.
- Retain the existing upper-bound rejection from the parent draft.
- Extend the exact-source ASan/UBSan fake-LittleFS lab from fifteen to seventeen
  scenarios per board with seven-character nonce and target cases.
- Keep journal binary layout, filenames, ACK/schema, controller API, server and
  finance behavior unchanged.

No shared API, migration target, GPIO, destination repository or release file
changed.

## Evidence classification

CI status is pending at handover creation. Boundary injection is **SIMULATED**.
Physical flash persistence, reboot/brownout behavior, electrical pulses, 150
power cuts and 30-device/24-hour soak remain **NOT TESTED**.

## Review request

PHX-QA should independently inject seven-character nonce and target values and
verify that no filesystem path is opened or mutated. PHX-CORE should review the
shared target-nonce minimum separately before any protocol change; this draft
only aligns firmware save behavior with its existing reboot parser.

Standing **PRODUCTION NO-GO** remains. No merge, flash, reset, migration,
payment action, deployment or release was performed.
