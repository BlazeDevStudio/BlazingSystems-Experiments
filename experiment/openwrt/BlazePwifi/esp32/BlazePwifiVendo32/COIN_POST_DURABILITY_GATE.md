# Coin POST — no dispatch of unpersisted RAM-only pulse data

## Verified risk
In the previous ESP32 and ESP8266 draft sketches, failure to persist a
pulse in `savePending()` set `fsReady=false` and `pendingReady=true`
to stop the physical coin relay, but a separate `post("coin")` branch
could still transmit the unpersisted pulse from RAM and clear the pending
memory on a substring `"ok":true` response. The outgoing event could
then disappear on reboot without a reliable local journal.

## Change
Both sketches now call a single `canAttemptCoinPost()` gate from their
coin HTTP dispatch branch. It returns true **only** when:
- the filesystem is mounted and journal storage has not been marked failed;
- `journalRecoveryRequired` is false (no corrupt/multiple boot candidates);
- a nonzero pulse count is pending and grouped as ready.

This prevents network dispatch after a failed flash write or ambiguous
boot recovery and complements separate GPIO/relay lockout. It does **not**
prove a successful flash write survives sudden power loss or that an HTTP
reply is an authenticated, durable financial receipt. PHX-CORE owns the
event-bound signed receipt/ACK specification; until reviewed, real paid
coin input must remain NO-GO.

## Reproduce exact-source host test
```sh
python3 experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/coin_post_gate_lab.py
```
The lab compiles each board's genuine helper and checks nine positive/
negative truth-table cases (18 total), plus source-level verification
that both live network call sites invoke the helper and failed flash
saves disable `fsReady`. No device flashes, real payments, or power
cuts are claimed.


## One-shot POST attempt marker — 2026-11-17 DRAFT

Both board sketches persist `/pending.attempt` with the exact pending event identity and verify it by readback **before** the first `post("coin")` call. The marker uses the existing PendingRecord magic/checksum and binds pulse count, nonce and target; it is local crash-state evidence, not a cryptographic witness.

- A verified marker makes `canAttemptCoinPost()` false for the rest of the boot.
- On reboot, matching, corrupt, mismatched or orphan markers set `journalRecoveryRequired`; no automatic duplicate POST is allowed.
- A marker open/write/readback failure prevents network dispatch in the current boot.
- Empty, timed-out, malformed or unknown responses retain the marker and block automatic retry because the server may have committed.
- The pending record is removed first and the marker last, only after the existing successful receipt or successful quarantine-append path. A failed marker removal leaves an orphan marker that blocks the next boot.

The hardware-owned source lab injects marker open, short-write, readback, mismatch, corruption, orphan, pending-delete and marker-delete failures on both boards. These are host simulations. LittleFS flush/readback has **not** been proven across physical power loss; no 150-cut, electrical or soak acceptance is implied. PHX-CORE must review the uncertain/reconciliation semantics and PHX-QA must independently verify the exact combined SHA before acceptance.
