# PHX-HARDWARE handover — verified pending-journal clear

Date: 2026-11-15 UTC  
Role: PHX-HARDWARE  
Task: #266 cleanup-first, bounded replay-safety repair  
Branch: `phoenix/hardware-journal-clear-verify-20261115`  
Base: `phoenix/hardware-esp32-timing-bounds-20261115@7e57ffdb3fc647beee484003922cf326b0016b4a`

## Proven defect

Both sketches cleared the in-memory pending coin event before checking whether
LittleFS removed `/pending.dat`, `/pending.new` and `/pending.bak`.
Removal return values and post-delete existence were ignored. A failed delete
could therefore leave a durable event that reappears after reboot while the
running firmware falsely reports no pending event.

## Change

- `clearPending()` now returns success/failure.
- Require LittleFS availability before any clear.
- Remove and verify absence of every journal candidate before changing RAM.
- On any removal or verification failure, retain the RAM event, enter
  `journalRecoveryRequired`, disable relay admission through existing output
  gates, and suppress further coin POST attempts.
- Quarantine reports clear success only when the pending journal was actually
  removed.
- Added source-extracted ASan/UBSan host failure injection: successful clear,
  delete failure, unavailable filesystem, pre-existing recovery lock, and a
  partial multi-candidate delete failure, with exact ESP32/ESP8266 parity.

No ACK/signature schema, finance authority, journal record format, quarantine
record format, server source, migration destination or release configuration
changed.

## Evidence classification

CI status is pending at handover creation. Failure injection is SIMULATED.
LittleFS behavior under physical power loss, flash wear, brownout, electrical
coin pulses, 150 power cuts and 30-device/24-hour soak remain NOT TESTED.

## Review request

PHX-QA should independently run the exact-head five-case harness and inspect the
delete-before-RAM-clear order. CORE must separately prove nonce idempotency and
signed durable ACK semantics; this firmware repair does not claim that shared
contract complete.

Standing PRODUCTION NO-GO remains. No merge, flash, reset, migration, customer
deployment, real money, signer, release or promotion is authorized.
