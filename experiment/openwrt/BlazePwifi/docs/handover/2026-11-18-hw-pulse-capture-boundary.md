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

Both ESP8266 and ESP32 sketches now call a small `sampleCoinPulseEdge(bool active)` helper from the existing loop. The helper retains active-level interpretation at the caller, rising-edge latch, unsigned debounce timing, target binding, 20-pulse cap, and nonce reuse. Test-first failure injection exposed a separate fail-closed defect: when `savePending()` failed, both sketches set `fsReady=false` and `pendingReady=true` but did not call `applyOutputs()`, so the relay/LED remained in their prior accepting state. The helper now calls `applyOutputs()` immediately after latching the failed write and before logging.

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

Test-first RED: commit [`67d3ff96`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/67d3ff96b44af90f6908ab530234805308a274f8), focused run [#44172599058](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44172599058), job `134355386347`: **FAILED AS EXPECTED** on both boards because the relay/LED remained enabled immediately after injected `savePending()` failure.

Source/test HEAD: `a65a0cb1d4ef542f56264d44059da22165a6f2de`.

Focused GREEN: [run #44172807861](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44172807861), job `134356105499`. The new pulse-capture lab passed `8/8` top-level scenarios on each board; five mutations were rejected on each board (missing edge latch, inclusive debounce, missing target binding, ignored save failure, and missing immediate output inhibit). Existing source-extracted suites also passed: quarantine `35/35` per board, pending-attempt marker `28/28` per board, mount `7/7` per board, boot recovery `16/16` per board, pending clear `17/17` per board, pending write/readback `22/22` per board, coin POST gate `10/10` per board, and poll-window drain `11/11` per board.

Relay polarity GREEN: [run #44172807677](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44172807677), job `134356105060`: `48/48` scenarios per board; inverted-write and removed-poll-inhibit mutations rejected.

Full build: [run #44172807702](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44172807702), same source/test HEAD. Validation job `134356401718` **FAILED** at the QA-owned `tests/controllers.sh` assertion `Missing poll signature check`. Target build jobs were still running at the time of this handover update; no target-build pass is claimed here. Signed APK, update bundle and browser simulation stages were skipped after validation failure.

All lab outputs explicitly retain `SIMULATED_ONLY=1`, `PHYSICAL_COIN_PULSE_ACCEPTANCE=0`, `PHYSICAL_RELAY_ACCEPTANCE=0`, and `PHYSICAL_POWER_CUT_ACCEPTANCE=0`. It must not be represented as relay/electrical acceptance or as evidence for the 150-power-cut or 30-device/24-hour gates.

Next: PHX-QA must reconcile the stale positive poll-signature fixture with the approved default-deny contract; PHX-MASTER must reconcile #317/#318 and refresh the role-assignment manifest. PHX-HARDWARE should not transplant the divergent ISR child without that coordination. Physical noncustomer pulse waveform, relay-contact, electrical recovery, 150 power cuts and 30-device/24-hour soak remain **NOT TESTED**. Production remains **NO-GO**.
