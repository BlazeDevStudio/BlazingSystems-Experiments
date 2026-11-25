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


## UTC15 follow-up — ISR IRAM attribute cleanup

Source/test HEAD: `bb519e6a2129f79723b9f7fb5903b4443149fcd0`. PR #352 remains OPEN / DRAFT / UNMERGED, stacked on #349 at `2a5c997add4f49fcd74f753101d3a9daac0040bf`.

The pinned ESP8266 core 3.1.2 baseline warned: `Use IRAM_ATTR in place of ICACHE_RAM_ATTR to move functions into IRAM` ([#45636378388](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45636378388), job `139282821711`). Both sketches now use `IRAM_ATTR` for both conditional ISR definitions. IRAM placement is preserved; ISR logic and coin sequence arithmetic are unchanged.

Test-first: guard commit [`236650a7`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/236650a78a2334abd8f7290ce1ce75a44013f305); RED [Relay #45647551685](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45647551685), job `139322538860`. Source commits: ESP8266 [`15e46f67`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/15e46f67f8ddc8aa3d8fe8d4ffa8736540e8afdf), ESP32 parity [`7db52843`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/7db52843760deaf82fd61ae2b31a117a61d49384), regression injection [`bb519e6a`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/bb519e6a2129f79723b9f7fb5903b4443149fcd0).

Exact final-head CI:
- Quarantine #45647993474 / job `139324111900`: PASS.
- Relay #45647993495 / jobs `139324111495`, `139324111984`: PASS / PASS.
- ESP8266 core 3.1.2 #45647993389 / job `139325441149`: PASS.
- ESP32 cores 3.3.13 / 4.0.0 #45647993395 / jobs `139324111769`, `139324112411`: PASS / PASS.
- Full #45647993676 / validation job `139324173309`: FAIL at inherited `Missing poll signature check`; 14 build jobs PASS, 12 downstream jobs SKIPPED.

Focused logs: poll safety parity 19/19; synthetic deprecated-attribute mutation rejected on both boards; coin pulse capture 18/18 on both boards. Final exact core logs contain no deprecated ISR attribute warning.

Binary SHA-256: ESP8266 core 3.1.2, 363728 bytes, `cad045f77cbc9b1384d6bf10b40b10236080037c1ab015bb6a07188e59e475d5`; ESP32 core 3.3.13, 1045808 bytes, `831cc5168640cd4da03d42546047f49639cd52c21813318991bf9fd7c9bb5362`; ESP32 core 4.0.0, 1100016 bytes, `8ee176f8174ee0bccdbae6824b0f5c82cbc680951eb3c894d499aff6899dfa14`.

**CI VERIFIED / SIMULATED ONLY.** Physical coin/relay/electrical acceptance, LittleFS/EEPROM power cuts, 150 cuts and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED: NO. PRODUCTION READY: NO-GO. CORE owns the authenticated register/poll contract; QA owns assertion reconciliation; Hardware will not invent a signature or weaken deny-default.

Next: CORE publishes canonical register/poll/coin contract and vectors; QA reconciles Full validation; MASTER reconciles stack ancestry; Hardware re-reads live heads before its next task. No flash, device reset, live-money operation, signer provisioning, production migration, release tag, merge, force-push or deployment.


---

## Latest UTC16 continuation — active conditional coin ISR selection

**Role:** PHX-HARDWARE  
**PR:** #352 — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-exact-arduino-core-matrix-20261125-utc11`  
**Source/test HEAD:** `1ab1be503bfe11dcfaa522348bc469d52fd040ed`  
**PR HEAD immediately before this documentation-only update:** `1ab1be503bfe11dcfaa522348bc469d52fd040ed`  
**Parent PR #349 HEAD:** `2a5c997add4f49fcd74f753101d3a9daac0040bf`

### Proven test-fidelity defect

`extract_board_coin_edge_isr()` always returned `definitions[0][1]` for both boards. Each sketch has two conditional definitions: the first is active under `#if defined(ESP8266)`; the second is the `#else` implementation used by ESP32. Consequently the ESP32 host lab compiled the inactive ESP8266 ISR body. The two current bodies happen to be identical, so prior green runs did not reveal the selection defect; a future ESP32-only ISR regression could have escaped the host fixture.

### Test-first evidence

- Initial synthetic-probe commit `1cfff2b44d2049d08a06debf006ec69b633fdab4` was rejected as an invalid RED: the tiny probe did not satisfy the shared source extractor and failed with `expected both conditional coinEdgeISR definitions, found 0`. This was a test-construction failure, not accepted defect evidence.
- Corrected full-sketch probe commit `6561a65b675f6c794afa84f6c030fceda61b5fe0` produced the intended RED:
  - [Relay run #45657134285](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45657134285), job `139356729139`: FAIL — `ESP32 lab selected the inactive conditional coinEdgeISR branch`.
  - [Quarantine run #45657134691](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45657134691), job `139356728976`: same FAIL.
  - ESP8266's active branch passed 18/18 in that RED run.

### Fix in source/test commit `1ab1be503bfe11dcfaa522348bc469d52fd040ed`

- Added explicit board-to-conditional-definition selection: ESP8266 → first definition; ESP32 → second; unsupported board names fail closed.
- The host fixture now compiles the target's active ISR definition rather than always compiling the first definition.
- Deprecated-attribute failure injection now mutates the active definition by source offset, not the first textual occurrence.
- Added a full-sketch in-memory branch mutation: the `#else` ISR body is changed to a distinct increment and each board must select its own active body.
- This UTC16 source/test commit changes **only** `coin_pulse_capture_lab.py`; no `.ino` firmware, relay, coin, accounting, controller API, signer, witness, replay, downgrade or migration behavior changed.

### Exact-source GREEN evidence on `1ab1be503bfe11dcfaa522348bc469d52fd040ed`

- [Quarantine Byte Readback LAB #45657612249](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45657612249), job `139358418600`: **PASS**.
- [Relay Output Polarity LAB #45657612290](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45657612290), job `139358417976`: **PASS**.
- Both exact-head logs report `ESP8266_ACTIVE_ISR_BRANCH_SELECTION_PASS`, `ESP32_ACTIVE_ISR_BRANCH_SELECTION_PASS`, `ESP8266_COIN_PULSE_CAPTURE_PASS 18/18`, `ESP32_COIN_PULSE_CAPTURE_PASS 18/18`, and rejection of the deprecated-attribute mutation on both boards.
- [ESP8266 core 3.1.2 #45657612432](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45657612432), job `139358420185`: **PASS**, exact checkout SHA verified; binary 363,728 bytes, SHA-256 `cad045f77cbc9b1384d6bf10b40b10236080037c1ab015bb6a07188e59e475d5`.
- [ESP32 core matrix #45657612283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45657612283), jobs `139358419268` (core 3.3.13) and `139358418800` (core 4.0.0): **PASS / PASS**; binaries 1,045,808 bytes / SHA-256 `6d491fdf56e9ff63e6ad7d1620a71daa930095429a2a5bc306d0e6f03fe1da13`, and 1,100,016 bytes / SHA-256 `5de875f31616900f60e26ff54a818d3684353625f3ef3aa4206ba36780fca1ac`.
- [Full BlazePwifi #45657612303](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45657612303), validation job `139358595850`: **FAIL** at inherited `Missing poll signature check` in the ESP8266 sketch. The 13 other build jobs completed PASS; the ESP32 full-matrix job was still running at this handover snapshot. Downstream update bundle, simulations, candidate/signing handoff and publication jobs were skipped. This is the existing CORE/QA register/poll producer-consumer contract blocker, not a regression from this test-only change.

### Evidence boundary and next action

This contribution is **CI VERIFIED / SIMULATED**, not hardware acceptance. Physical coin pulse, relay/electrical recovery, power-cut persistence, 150 controlled power cuts, 30-device/24-hour soak, protected anti-rollback witness, durable accounting/replay and v1-to-v2 migration remain **NOT TESTED / NOT ACCEPTED**. All workflow logs explicitly retain physical-acceptance flags at zero.

**Next exact action:** CORE publishes the approved authenticated register/poll/coin response contract and canonical vectors; QA independently reconciles the Full validation assertion; MASTER coordinates the stacked ancestry. PHX-HARDWARE re-reads all live heads before its next owned task. No flash, reset, live-money operation, signer provisioning, production migration, release tag, merge, force-push or deployment.
