# PHX-HARDWARE handover — verified invalid temporary-journal cleanup

Date: 2026-11-15 UTC  
Role: PHX-HARDWARE  
Task: #266 cleanup-first, bounded pending-journal repair  
Branch: `phoenix/hardware-pending-temp-cleanup-20261115`  
Base: `phoenix/hardware-pending-rotation-verify-20261115@1689e215e36f377ddc98c66abdee3d3dffec438f`

## Proven defect

After a short LittleFS write or failed production-parser readback, both ESP
sketches called `LittleFS.remove("/pending.new")` without checking the return
value or confirming path absence. The current caller disables filesystem
admission and relay on `savePending()` failure, so this was already fail-closed
for the active boot. However, a surviving invalid temporary candidate was not
explicitly marked recovery-required until reboot and could coexist with a prior
primary journal.

## Change

- Reuse the existing human-readable `removePendingCandidate()` helper for both
  pre-rotation failure paths.
- Set `journalRecoveryRequired` when invalid temporary-record removal cannot be
  proven.
- Preserve the invalid file as evidence instead of pretending cleanup
  succeeded.
- Extend the exact-source ASan/UBSan fake-LittleFS lab from eleven to thirteen
  scenarios per board with removal failures after a short write and after a
  short read.
- Keep journal names, binary record format, rotation order, ACK/schema,
  controller API, server and finance behavior unchanged.

No shared API, migration target, GPIO, destination repository or release file
changed.

## Evidence classification

CI status is pending at handover creation. Failure injection is **SIMULATED**.
Physical flash persistence, reboot/brownout behavior, electrical pulses, 150
power cuts and 30-device/24-hour soak remain **NOT TESTED**.

## Review request

PHX-QA should independently inject removal failures after short write and
readback failure, verify that the invalid file remains preserved, and confirm
that recovery-required prevents further coin admission. PHX-CORE still owns
durable signed event ACK and ledger idempotency.

Standing **PRODUCTION NO-GO** remains. No merge, flash, reset, migration,
payment action, deployment or release was performed.
