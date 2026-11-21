# PHX-HARDWARE handover — shared polarity rollover scenario builder

**Updated:** 2026-11-20T22:46:00Z  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** PR #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test commit:** `83c20c9d59bcdf6c24e2112f3396b90847b5bde0`

## Cleanup-first change

In `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py`, replaced two duplicated active-high and active-low post-drain rollover C++ scenario literals with one `post_drain_rollover_main(active_low)` builder.

The builder parameterizes only the polarity-specific facts:
- active-low input and FALLING ISR vs active-high input and RISING ISR;
- scenario marker name;
- expected failure code for the wrong-edge mutation.

The generated scenario retains the same extracted production loop, sequence counters initialized at `0xFFFFFFFE`, two injected post-drain ISR edges, modulo wrap to zero, durable unresolved marker with `pulses=2`, no HTTP poll, outputs OFF, and deny state. Both board runs still compile the generated C++ and execute the wrong-edge failure injection. This removes duplicated scenario bodies that could drift apart; it is a host-lab maintainability change, not a firmware behavior change.

## Exact source/test CI

At source/test SHA `83c20c9d59bcdf6c24e2112f3396b90847b5bde0`:

- Quarantine push [run #44831537575](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44831537575), job `136617415067`: **SUCCESS**. Logs show active-high and active-low post-drain multi-edge rollover PASS on ESP8266 and ESP32; wrong-edge mutations rejected with expected exits 56 and 59. The full quarantine suite, pulse capture, readback and configuration-read-failure checks also completed.
- Relay/output push [run #44831545206](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44831545206), jobs `136617439353` and `136617439912`: **SUCCESS**.
- Quarantine PR [run #44831545232](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44831545232): in progress at handover time; exact job `136617439737` had not yet returned a terminal result.
- Full PR [run #44831545327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44831545327), validation job `136617440659`: **FAILURE** at inherited QA-owned `Missing poll signature check` in `experiment/openwrt/BlazePwifi/tests/controllers.sh`. Target build matrix jobs were still running at handover time; no Full pass is claimed. Downstream release/import/simulation gates were skipped.

Local checkout/testing was unavailable because this runtime could not resolve github.com for `git clone`; exact-source GitHub Actions ran the committed source. No local pass is claimed.

## Boundaries

Only the Hardware-owned host-lab file changed in the source/test commit. No production `.ino`, GPIO assignment, shared API, register/poll response contract, financial state, QA-owned test, Release workflow, COE destination, secret, physical device or customer state changed.

Evidence classification: **SIMULATED / focused CI verified**. Physical coin selector, electrical pulse/recovery, relay contact behavior, power-cut trials and device soak remain **NOT TESTED**. No HARDWARE ACCEPTED or PRODUCTION READY claim.
