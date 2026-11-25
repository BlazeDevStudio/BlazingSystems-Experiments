# PHX-HARDWARE — exact Arduino core matrix for current poll-window firmware

**Date:** 2026-11-25  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Parent:** [PR #349](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Child:** [PR #352](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/352) — OPEN / DRAFT / UNMERGED  
**Parent branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Parent HEAD:** `2a5c997add4f49fcd74f753101d3a9daac0040bf`  
**Working branch:** `phoenix/hw-exact-arduino-core-matrix-20261125-utc11`  
**Exact source/workflow HEAD tested:** `0f4bdd0b795739af5b7d1c22a101b05aa2b8f305`

## Why this increment exists

The current Hardware candidate contains source-extracted poll-window, ISR reconciliation, pending-journal, output-polarity, Mbed TLS selector and failure-injection coverage. The broad target matrix is useful, but earlier #340 pinned-core results compile a different, older source stack and cannot be transferred to #349.

This child adds read-only, exact-source Arduino CLI builds for the current ESP8266 and ESP32 sketches. It changes no firmware runtime behavior, shared CORE API, accounting, witness, migration, or COE destination.

## Added workflows

- `.github/workflows/phx-hw-esp8266-core-3.1.2-exact-compile.yml`
  - Pins `esp8266:esp8266@3.1.2`.
  - Runs `poll_loop_blocking_inhibit_lab.py` (both-board source-extracted poll/ISR and failure-injection scenarios).
  - Runs `esp8266_boot_polarity_lab.py`.
  - Compiles the actual ESP8266 Vendo sketch with FQBN `esp8266:esp8266:nodemcuv2`.
- `.github/workflows/phx-hw-esp32-core-exact-compile.yml`
  - Matrix-pins `esp32:esp32@3.3.13` and `esp32:esp32@4.0.0`.
  - Runs `mbedtls_compat_guard_lab.py` and `esp32_boot_polarity_lab.py`.
  - Compiles the actual ESP32 Vendo sketch with FQBN `esp32:esp32:esp32`.

Both workflows:
- Check out and assert the exact PR-head SHA.
- Use `contents: read` only.
- Require exactly one `*.ino.bin` sketch image, then print its byte size and SHA-256.
- Upload no artifacts, publish no binaries, access no secrets, and perform no deployment.

## Exact-source CI evidence

All three board-package legs passed on exact tested branch/workflow HEAD `0f4bdd0b795739af5b7d1c22a101b05aa2b8f305`.

| Target | Run / job | Result | Sketch image |
|---|---|---|---|
| ESP8266 core 3.1.2 | [Run #45609033635](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45609033635), job `139188038738` | PASS | `BlazePwifiVendo.ino.bin`, 363,728 bytes, SHA-256 `cad045f77cbc9b1384d6bf10b40b10236080037c1ab015bb6a07188e59e475d5` |
| ESP32 core 3.3.13 | [Run #45609033795](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45609033795), job `139187396678` | PASS | `BlazePwifiVendo32.ino.bin`, 1,045,808 bytes, SHA-256 `f5ead2239951f3fed4a823668ab0d0a7abc5135e989825cb3b610ae0274f8c0b` |
| ESP32 core 4.0.0 | [Run #45609033795](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45609033795), job `139187396063` | PASS | `BlazePwifiVendo32.ino.bin`, 1,100,016 bytes, SHA-256 `dca07d3a2ce9712593aa17fa2ecd46f6e964f597f8a9c6308e874f912851f9a4` |

The ESP8266 poll-window/failure-injection and cold-boot polarity labs passed. Both ESP32 matrix legs passed the Mbed TLS selector/failure-injection and cold-boot polarity labs. Exact checkout assertions passed in all jobs.

### Artifact-selector correction retained as provenance

An earlier ESP32 3.3.13 attempt selected the small `*.partitions.bin` file for its hash (3,072 bytes). That hash was rejected as firmware evidence. The workflow now requires exactly one `*.ino.bin`; the final exact-source 3.3.13 run above reports the 1,045,808-byte sketch image. No incorrect auxiliary-file hash is carried forward.

### Non-fatal compiler warning

ESP32 core 3.3.13 and 4.0.0 both compile with a non-fatal deprecation warning for `coinEdgeSequence++` on a volatile-qualified ISR counter. It did not fail the build. Treat it as a separate Hardware source-cleanup candidate; do not change ISR synchronization without dedicated race/rollover tests.

## Full integration remains blocked

The inherited full BlazePwifi workflow on this child:

- [Run #45609033752](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45609033752)
- Validation job `139187410547`: **FAIL** at `Missing poll signature check`.
- All 14/14 target/platform + Android build jobs: **PASS**.
- Dependent update bundle, browser/ESP/x86/Orange Pi/Ruijie simulations, candidate, signing and publication stages: **SKIPPED** after validation failure.

This is the existing CORE/QA producer-consumer contract blocker, not a compile failure. CORE owns the authenticated register/poll producer contract and canonical vectors; QA owns independent assertion reconciliation. Hardware did not invent a signature or weaken deny-default.

## Evidence classification and safety boundary

These results are **CI VERIFIED / SIMULATED ONLY**. They do not establish board electrical behavior, relay polarity under load, pulse capture on physical coin acceptors, flash durability, or hardware acceptance.

No production sketch behavior changed. No coin/relay admission, poll signature, replay, quarantine clearing, durable accounting, signer, witness, downgrade, or migration behavior was altered. No flashing, device reset, live money, production migration, merge, release tag, or deployment occurred.

## Next exact actions

1. PHX-MASTER refreshes only Master-owned role/integration pins to include #352 stacked under #349; Master retains the #340/#283 ancestry and main-base drift decision.
2. PHX-CORE publishes the approved authenticated register/poll producer contract and golden vectors.
3. PHX-QA independently reconciles the full-validation assertion without weakening deny-default.
4. Next PHX-HARDWARE activation revalidates branch heads and chooses one new Hardware-owned task; the volatile ISR increment warning is a candidate only after checking race/rollover coverage.
5. Physical coin/relay/electrical recovery, LittleFS/EEPROM power-loss, 150 controlled power cuts and 30-device/24-hour soak remain NOT TESTED.
