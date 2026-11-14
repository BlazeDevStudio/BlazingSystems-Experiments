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
