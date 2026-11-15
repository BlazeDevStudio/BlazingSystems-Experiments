# PHX-HARDWARE handover — quarantine reboot idempotency

Date: 2026-11-15 UTC  
Branch: `phoenix/hardware-quarantine-reboot-idempotency-20261115`  
Base: `phoenix/hardware-quarantine-ambiguity-latch-20261115@da18da4c2afc3f42037ee3ac4cfa48bdba4f4f01`

## Proven defect

The recovery latch added by the parent is volatile. If power is lost after a
short quarantine append, reboot clears the RAM latch and the next attempt can
append after an unterminated record. If the append completed but verification
or pending-journal deletion failed, reboot can append the same event again
before clearing the pending journal.

Both outcomes make unpaid-coin reconciliation ambiguous.

## Change

- Stream and validate the bounded quarantine log before every append.
- Require every prior record to be structurally recognizable and newline
  terminated; malformed or torn tails latch recovery and block mutation.
- Identify an already committed event by the stable persisted
  pulse/nonce/target prefix and reuse that record instead of appending twice.
- Avoid loading the 32 KiB log into RAM; inspection uses one 320-byte line
  buffer on ESP32 and ESP8266.
- Replace overflow-prone addition with subtraction-based capacity validation.
- Extend the exact-source fake-LittleFS lab from fourteen to sixteen scenarios
  per board.
- Simulate reboot after short write, lost newline, same-size tail corruption,
  verification-open failure, verification-read fault and pending-clear failure.
- Prove torn tails remain fail-closed and complete records recover
  idempotently without changing quarantine bytes.

No shared API, server, finance, GPIO, pending-record layout, migration target,
CoinOperatedEcosystem destination, dependency, license or release file changed.

## Evidence classification

Failure and reboot injection are **SIMULATED**. Exact-source host tests and
target compiles become **CI VERIFIED** only after exact-head jobs pass. Real
flash durability, electrical pulse/recovery, controlled power cuts and device
behavior remain **NOT TESTED**.

## Migration boundary

Master UTC20/UTC21 holds remain in force. COE draft #26 has different firmware
blobs and stale queued workflows. This source repair is not migration parity,
license/dependency approval, a copy request or destination promotion.

## Mandatory remaining gates

- Independent QA reproduces torn-tail rejection and complete-record
  idempotency at the exact PR head.
- Per-file source/destination blob, mode, dependency, license and test parity.
- Physical noncustomer electrical pulse/recovery testing.
- 150 controlled power cuts.
- 30-device 24-hour soak.
- Protected antirollback signer and independent witness.
- Durable v1-to-v2 accounting/replay migration.
- Independent QA, release and Master acceptance plus owner approval.

No merge, flash, reset, live money, production migration, deployment, signing,
release tagging or production-readiness claim is authorized.
