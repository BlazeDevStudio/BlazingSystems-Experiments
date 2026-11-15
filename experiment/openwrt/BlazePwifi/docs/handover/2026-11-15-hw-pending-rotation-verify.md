# PHX-HARDWARE handover — verified pending-journal rotation

Date: 2026-11-15 UTC  
Role: PHX-HARDWARE  
Task: #266 cleanup-first, bounded journal-rotation repair  
Branch: `phoenix/hardware-pending-rotation-verify-20261115`  
Base: `phoenix/hardware-pending-write-readback-20261115@b73403d6daa6f136f136c46d8a90cd99d648e401`

## Proven defect

Both ESP sketches ignored LittleFS results while removing a stale
`/pending.bak`, moving `/pending.dat` to backup, restoring after a failed
promotion, and deleting the backup after promotion. The function could report
success while two different unpaid-coin journal candidates remained. On reboot,
the existing recovery policy would correctly lock intake, but the preceding
success result was false durability evidence.

## Change

- Add a small `removePendingCandidate()` helper that verifies both the remove
  result and path absence.
- Refuse rotation and set `journalRecoveryRequired` when a stale backup cannot
  be removed.
- Verify primary-to-backup and temporary-to-primary postconditions.
- On promotion failure, remove the unpromoted temporary candidate and verify
  restoration of the prior primary; set recovery-required if cleanup or
  restoration cannot be proven.
- After successful promotion, require verified backup deletion before reporting
  success. A cleanup failure preserves both candidates and locks recovery.
- Extend the exact-source ASan/UBSan fake-LittleFS lab from six to eleven
  scenarios per board, adding stale-backup deletion, primary rename, promotion,
  rollback, and final-backup deletion failures.
- Keep journal filenames, binary record format, ACK/schema, controller API,
  finance behavior and migration targets unchanged.

No shared API, server, finance, GPIO, destination-repository or release file
changed.

## Evidence classification

CI status is pending at handover creation. Fault injection is **SIMULATED**.
Physical LittleFS behavior, reboot/brownout persistence, electrical pulses, 150
power cuts and 30-device/24-hour soak remain **NOT TESTED**.

## Review request

PHX-QA should independently inject every remove/rename failure and verify that
no ambiguous journal state is returned as success. PHX-CORE still owns durable
signed event ACK and ledger idempotency. PHX-MASTER controls any later per-file
migration after exact blob/mode/license/dependency/test-identity review.

Standing **PRODUCTION NO-GO** remains. No merge, flash, reset, migration,
payment action, deployment or release was performed.
