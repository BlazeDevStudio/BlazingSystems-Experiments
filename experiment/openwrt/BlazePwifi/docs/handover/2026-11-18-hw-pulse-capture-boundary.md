# PHX-HARDWARE — poll-drain to durable coin-pulse capture

**Date:** 2026-11-17 UTC20  
**Task:** [P0 issue #177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177), cleanup-first #266  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** `phoenix/hardware-clear-pending-marker-match-20261117`  
**PR:** [#317 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/317)  
**Base:** `2e20e21d1129c5b85493c1b48566d7e663fa6ba4`

## Finding

The exact-source poll-drain lab proved that a pulse during the inhibit-settle window aborts the synchronous poll and restores relay/LED outputs. It did not prove the next normal loop sample actually increments the pending event and calls `savePending()`. The coin-edge capture block was inline in both `loop()` functions, so the critical handoff from poll abort to durable journal write was not independently source-extracted.

## Hardware-owned change

Both ESP8266 and ESP32 sketches now call a small `sampleCoinPulseEdge(bool active)` helper from the existing loop. The helper is a behavior-preserving extraction of the prior inline logic: it retains active-level interpretation at the caller, rising-edge latch, unsigned debounce timing, target binding, 20-pulse cap, nonce reuse, and fail-closed handling when `savePending()` fails.

No wire format, register/poll contract, receipt authority, financial schema, GPIO assignment, relay polarity, QA-owned file, or shared API changed.

## Exact-source failure-injection lab

New `coin_pulse_capture_lab.py` extracts the production poll-window and pulse-capture functions from both sketches, compiles them with C++17 fake GPIO/time/storage, and checks:

- 30–100 ms pulse observation during the poll-drain abort;
- active-low and active-high input mapping;
- exact 250 ms drain boundary and configured 300 ms debounce;
- uint32 millis rollover;
- the next sample increments the pending event and invokes `savePending()`;
- sustained-high input is not double-counted; a released second edge reuses the same event identity;
- save failure disables filesystem admission and relay/LED output;
- recovery, pending, target, debounce and pulse-count gates deny unsafe capture.

Four deliberate source mutations must be rejected: missing edge latch, inclusive debounce boundary, missing target binding, and ignored save failure.

The focused hardware workflow now runs this lab after the existing quarantine, journal, POST-deny and poll-drain labs.

## Evidence classification and next action

At initial commit time, the new lab is **CI PENDING**. It is a host simulation, not physical coin-pulse acceptance. It must not be represented as relay/electrical acceptance or as evidence for the 150-power-cut or 30-device/24-hour gates.

Next: inspect the focused run at the exact final PR HEAD, then request PHX-QA review of the source-extracted capture boundary and PHX-MASTER review of the #317/#318 stack. Physical noncustomer pulse waveform, relay-contact, electrical recovery, power-cut and soak evidence remain **NOT TESTED**. Production remains **NO-GO**.
