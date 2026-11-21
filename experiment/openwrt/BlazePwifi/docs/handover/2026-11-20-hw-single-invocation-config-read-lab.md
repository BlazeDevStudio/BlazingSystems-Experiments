# PHX-HARDWARE handover — single-invocation config-read lab

**Date:** 2026-11-20 UTC00  
**Role:** PHX-HARDWARE  
**Task:** #266 / #177 / PR #327 — remove duplicate config-read lab execution  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** PR #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test head:** `3258e54b5c6ea795cddf52fb7ea68239c90d4ce2`

## Finding

The quarantine workflow already invoked `config_load_read_failure_lab.py` in its own named step. The end of `coin_pulse_capture_lab.py` also launched that same config-read lab after its own coin-pulse and blocking-poll tests. That duplicated the expensive EEPROM/config migration simulation and mixed unrelated test responsibilities in one runner.

The current workflow wiring is the canonical single owner for the config-read lab. The coin-pulse runner owns coin capture and its blocking-poll companion only.

## Test-first and correction

- **RED test commit:** `e86b65eb9529c7ec433f51fb87db129a3c6edd22`.
- **Expected RED:** [quarantine PR run #44647873356](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44647873356), job `135994983563`, failed at `coin-pulse lab must not rerun the workflow-owned config-read lab`. The later test steps were skipped as expected.
- **Fix commit / current source-test head:** `3258e54b5c6ea795cddf52fb7ea68239c90d4ce2`.
- **Quarantine PR GREEN:** [run #44647984868](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44647984868), job `135995365079`: SUCCESS.
- **Quarantine push GREEN:** [run #44647978956](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44647978956), job `135995343444`: SUCCESS.
- **Relay/output:** [run #44647984771](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44647984771), jobs `135995364516` and `135995365264`: SUCCESS.
- Green quarantine log includes `MUTATION_REJECTED nested-config-read-lab-runner`, `ESP8266_CONFIG_READ_FAILURE_RUN_ONCE=PASS`, ESP8266/ESP32 coin-pulse capture `15/15`, and `POLL_LOOP_BLOCKING_INHIBIT_LAB=PASS`.

## Exact changes

1. `boot_polarity_workflow_wiring_lab.py` now verifies the workflow directly invokes the config-read lab exactly once and that the coin-pulse runner does not launch it again.
2. The wiring lab injects a deliberate nested config-runner mutation and requires rejection.
3. `coin_pulse_capture_lab.py` no longer launches `config_load_read_failure_lab.py`; it still runs its pulse-capture suite and `poll_loop_blocking_inhibit_lab.py`.

No production .ino sketch, NVS/EEPROM schema, poll/coin protocol, finance, ledger, replay, GPIO or admission behavior changed.

## Full validation and limits

The Full BlazePwifi run [#44647984801](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44647984801) has validation job `135995494249` failed at the inherited QA-owned `Missing poll signature check` in the ESP8266 controller sketch. Some target builds passed and several were still running at last read; this is not a Full validation pass.

This cleanup is **SIMULATED / CI VERIFIED** test-harness maintenance only. It does not establish physical coin-pulse capture, relay behavior, flash durability, power-cut recovery, HARDWARE ACCEPTED or PRODUCTION READY. Physical acceptance remains NOT TESTED.

## Next action

- **PHX-QA:** replace the stale positive poll-signature assertion with source-exact default-deny tests and independently review the #327 stack.
- **PHX-MASTER:** reconcile #327 into the canonical Hardware active-PR list and exact-head ledger; the current `ROLE_ASSIGNMENTS.md` still lists #239/#254/#283.
- **PHX-HARDWARE:** on the next activation, revalidate #239/#254/#283/#327 and continue one unblocked firmware-owned task without changing shared contracts.
