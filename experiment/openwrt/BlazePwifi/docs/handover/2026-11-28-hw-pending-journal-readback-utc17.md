# PHX-HARDWARE UTC17 — pending-journal write/readback verification

- **Issue:** #177
- **PR:** #363 (OPEN / DRAFT / UNMERGED)
- **Branch:** `phoenix/hw-pending-persist-io-failure-guard-20261127-utc16`
- **Parent PR/base:** #362 at `eeddfc37d24d20ebc14641dfe3ffa247bbbc1ebd`
- **Source/test SHA:** `cca859a859c748a3a06653bbe217af7d81749eba`

## Defect and correction

The previous writer trusted a full-length `File.write()` result after `flush()/close()`, then rotated the canonical journal without verifying that the closed `/pending.new` record could be read back intact. A full-length but corrupted write was not covered by the prior harness.

Both ESP8266 and ESP32 now call the existing `readPendingFile("/pending.new", verified, legacy)` before any backup removal or canonical rotation. The record must be v2 and match every persisted field (magic, version, reserved, acked sequence, sequence, pulses, nonce, target and checksum). Any readback open/short/corrupt/mismatch condition returns false before filesystem rotation or RAM authority publication; candidates are preserved for fail-closed recovery.

## Test-first evidence

- Old-source RED: [#46044749729](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46044749729), job `140661084265`, harness exit 14 on the full-length corrupt-write case.
- Corrected source/test: `cca859a859c748a3a06653bbe217af7d81749eba`.
- Focused push: [#46044948992](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46044948992), job `140661750430`, PASS.
- Focused PR: [#46044956444](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46044956444), job `140661774727`, PASS.
- ESP8266: 17 persistence scenarios PASS.
- ESP32: 17 persistence scenarios PASS.
- 9 unsafe source mutations per board rejected; 18 total.
- Mbed TLS [#46044956381](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46044956381): 3/3 PASS (source contract, Arduino cores 3.3.13 and 4.0.0).
- Full source-head [#46044956380](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46044956380): failed only at the handover-freshness gate because this source SHA had not yet been recorded. ESP8266/ESP32, Android and 11 firmware target jobs passed; downstream validations were skipped. Re-run after this checkpoint.
- Native [#46044956397](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46044956397), job `140661775342`: inherited QA-owned PAY-0745 failure.

## Limits

Immediate filesystem readback and fake-LittleFS failure injection are SIMULATED / CI VERIFIED only; not proof of flash durability across power loss. Physical LittleFS/electrical acceptance, 150 power cuts and 30-device/24-hour soak remain NOT TESTED. No coin/relay enable, finance, shared API, migration, signer, witness, COE, physical device, merge or deployment.

**Disposition:** HARDWARE ACCEPTED = NO · PRODUCTION READY = NO-GO.
