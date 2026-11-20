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

## Poll admission authority hold — 2026-11-17 UTC08

The ESP32/ESP8266 consumer must not treat the current derived response_sig expression as an approved authorization contract. Master Architecture Contracts §6.3 requires a canonical producer and independent positive/negative golden vectors at pinned SHAs before configured-key coin admission can be enabled. Until that gate is satisfied, acceptPollResponse() explicitly clears stale target/admission state and returns DENY on both boards. This is a safety hold, not a completed authentication protocol. Do not enable coin intake by toggling a local flag or copying the COE candidate; obtain CORE/QA/Master approval first.

## Exact-head poll authority hold evidence — 2026-11-17 UTC08

Test-first RED: [run 44051036806](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44051036806), job 133928606170, corrected test SHA 491cd094e77c264b2c8053aff0c59913f0faa229; both board poll labs failed at the positive-looking unapproved-candidate assertion. The preceding 44050812024 run is a C++ literal compile error and is not counted as RED.

Source fix: commit 3c2ccc09dcc0d2eab01c1bdaae5aa7548f245798. Focused exact-head [run 44051446853](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44051446853), job 133930014829, SUCCESS. Poll-response fail-closed 11/11 per board; strict root JSON 13/13; coin POST ACK root 4/4; disposition default-deny 4/4; register-config denial 7/7; inherited quarantine 19/19 per board and all other journal/POST labs passed.

Full validation [run 44051446855](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44051446855), job 133930149201, FAILED because QA-owned tests/controllers.sh still requires an active poll signature check. Update that test to assert default-deny while the contract is unapproved; do not restore the unapproved candidate verifier merely to satisfy the stale assertion. The QA loop-extractor issue remains independent.


## Final exact-head reconciliation — 2026-11-17 UTC09

Final PR head before this documentation-only checkpoint: 9c30d8c97763b610c4ab2d0df0168b4ace9cf8a3. Focused [run 44051895971](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44051895971), job 133931499416, completed SUCCESS at that exact head. Both ESP boards passed poll-response fail-closed 11/11, strict root JSON 13/13, coin POST ACK root 4/4, disposition default-deny 4/4, register-config denial 7/7, quarantine 19/19 and pending-attempt marker 19/19. All tests are source-extracted host/fake-LittleFS simulations.

Full [run 44051896075](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44051896075) at the same exact head is now COMPLETED FAILURE. Validation job 133931629492 failed in QA-owned tests/controllers.sh because it requires an active poll signature check. This is incompatible with Master §6.3 default-deny; do not restore the unapproved candidate to satisfy the test. The separate v060_esp_poll_intake_guard.py extractor issue remains unresolved and was not reached. ESP8266, ESP32, Android, Ruijie, x86_64 and all returned Orange Pi target jobs completed PASS. Production import/sign, update bundle, v0.4 simulations/candidate gate and release publication were skipped.

Final status remains SIMULATED / CI VERIFIED only. Physical relay/coin acceptance, 150 power cuts, 30-device 24-hour soak, electrical pulse/recovery, protected signer/witness, durable accounting/replay, v1-to-v2 migration and independent release signoff remain unproven. PRODUCTION NO-GO.
