# PHX-HARDWARE handover — pending write readback before rotation

Date: 2026-11-15 UTC  
Role: PHX-HARDWARE  
Task: #266 cleanup-first, bounded journal-persistence repair  
Branch: `phoenix/hardware-pending-write-readback-20261115`  
Base: `phoenix/hardware-quarantine-log-encoding-20261115@d3d1caf1931a0433d43d5007a184fc3fd5d947ad`

## Proven defect

Both sketches treated a LittleFS `write()` returning the requested byte count as
sufficient proof that `/pending.new` contained the intended coin record. They
then rotated that unverified file into `/pending.dat`. Same-size corruption,
a failed read-open, or a short read could therefore be accepted as durable
until a later reboot detected an unreadable journal and locked recovery.

## Change

- Read `/pending.new` back through the production `readPendingFile()` parser
  before any rename.
- Compare the complete zero-initialized record with the intended record.
- Remove the temporary candidate and return failure on parser/readback/byte
  mismatch; the existing caller then disables filesystem admission and relay.
- Keep journal names, binary record format, rotation order, ACK/schema, server
  and finance behavior unchanged.
- Add an exact-source ASan/UBSan fake-LittleFS lab covering successful creation,
  same-size post-close mutation, short write, short read, read-open failure and
  verified replacement of an existing primary record for both ESP targets.
- Run the new lab in the focused hardware workflow and the full controller
  validation suite.

No shared API, ACK signature, server, finance, migration, GPIO, quarantine
format, destination repository or release file changed.

## Evidence classification

CI status is pending at handover creation. Filesystem corruption injection is
SIMULATED. Physical flash persistence, reboot/brownout behavior, electrical
pulses, 150 power cuts and 30-device/24-hour soak remain NOT TESTED.

## Review request

PHX-QA should independently reproduce every exact-source failure case and
inspect that no `/pending.new` rename occurs before successful readback.
PHX-CORE still owns durable signed event ACK and ledger idempotency.

Standing PRODUCTION NO-GO remains. No merge, flash, reset, migration, customer
deployment, real money, signer, release or promotion is authorized.
