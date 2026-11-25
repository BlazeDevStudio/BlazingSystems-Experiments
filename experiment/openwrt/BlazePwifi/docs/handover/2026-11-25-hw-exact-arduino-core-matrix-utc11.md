# PHX-HARDWARE — exact Arduino core matrix for current poll-window firmware

**Date:** 2026-11-25  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Parent:** [PR #349](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349)  
**Parent branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Parent HEAD at branch creation:** `2a5c997add4f49fcd74f753101d3a9daac0040bf`  
**Working branch:** `phoenix/hw-exact-arduino-core-matrix-20261125-utc11`  
**Scope:** exact, pinned Arduino CLI compilation of the current ESP8266 and ESP32 Vendo sketches, plus existing source-extracted safety regressions.

## Why this increment exists

The current Hardware candidate has source-extracted poll-window, pending-journal, output-polarity, Mbed TLS selector, and mutation coverage. The broad target matrix is useful but does not independently record the exact Arduino board-package versions used to compile these two current sketches. The earlier #340 pinned-core workflows compile an older, separate source stack; their results cannot be transferred to #349.

This child adds read-only, exact-source build workflows to the current #349 source tree. It changes no firmware runtime code, shared CORE API, accounting, witness, migration, or COE destination.

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
- Require a non-empty compiled binary and print its size and SHA-256.
- Upload no artifacts, publish no binaries, access no secrets, and perform no deployment.

## Evidence classification

The workflows are newly added. Their exact-PR-head runs are pending at the time this handover was authored. No compile pass is claimed until each job reaches a terminal SUCCESS on the final PR head. A failed or cancelled matrix leg remains a failure/blocker; it must not be summarized as a pass.

Even successful hosted builds are **CI VERIFIED / SIMULATED ONLY**. They do not establish board electrical behavior, relay polarity under load, pulse capture on physical coin acceptors, flash durability, or hardware acceptance.

## Explicit safety boundary

No production sketch behavior changed. No coin/relay admission, poll signature, replay, quarantine clearing, durable accounting, signer, witness, downgrade, or migration behavior was altered. No flashing, device reset, live money, production migration, merge, release tag, or deployment occurred.

## Next exact action

After the PR-triggered workflows finish, record exact PR-head SHA, run IDs, job IDs, core versions, binary sizes and SHA-256 values. Keep any failed matrix leg visible. Request independent QA review of the build evidence and PHX-MASTER reconciliation of the parent stack; do not merge or retarget this child.
