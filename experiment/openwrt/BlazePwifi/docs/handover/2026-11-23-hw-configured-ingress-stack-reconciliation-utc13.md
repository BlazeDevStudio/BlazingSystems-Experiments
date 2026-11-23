# PHX-HARDWARE UTC13 — configured coin-ingress predicate stack reconciliation

**Observed:** 2026-11-23T13:10:00Z (scheduled activation; exact host timestamp is not available from GitHub)
**Role:** PHX-HARDWARE
**Task:** #177 — preserve coin-line edges and fail-closed admission
**Parent:** PR #345, exact parent HEAD `ca72497ed386c9ac4e50d3f811827bef51e296ad`
**Child branch:** `phoenix/hw-coin-ingress-config-helper-reconciled-20261123-utc13`
**Source/test HEAD after first reconciliation:** `59de2e122f57559804ecb2929b56903b6486c694`  
**Source/test HEAD after CI correction:** `724d892e980f878903425837226c45b321638793`
**PR:** pending creation as a DRAFT child of #345

## Why this reconciliation exists

Master's UTC11 audit found that PR #346 was based on the older #345 snapshot `797dece76c18d464a7c0580658b5db9351cb8e15`, while #345 had advanced to `ca72497ed386c9ac4e50d3f811827bef51e296ad`. The child also changed the same poll-loop lab as the parent and did not contain the parent's newly added `pending_clear_failure_lab.py` file.

Rather than rebase or force-push the existing #346 branch, Hardware created this new child from the current #345 head and reapplied the narrow configured-ingress predicate changes. PR #346 remains untouched and OPEN/DRAFT pending Master disposition.

## Changes on the reconciled child

- Both ESP8266 and ESP32 sketches now define one file-local `coinIngressConfigurationAllows()` predicate and reuse it from `sampleCoinPulseEdge()` and `applyOutputs()`.
- The predicate remains exactly `controllerEnabled && coinEnabled && relayEnabled`; poll-time intake suspension remains a separate runtime state.
- All source-extraction labs that compile or compare `applyOutputs()` now include the helper explicitly.
- The poll-loop lab has a dedicated one-edge disabled-ingress main for controller, coin and relay. It runs an unmutated deny baseline first, then independently mutates each predicate term and expects the specific fail-open exit (64/62/60).
- The output-path mutation remains independent. The sample-path test forces only the output admission helper false, retaining the real output function and its side effects, so the scenario isolates credit admission rather than reusing unrelated positive-output tests.

## Parent changes preserved

This branch starts from the live #345 head, so it retains the parent-only:
- `pending_clear_failure_lab.py` and its failure-injection coverage;
- poll-loop invocation of `run_pending_clear_failure_lab()`;
- `quarantinePending()` parity and mutation coverage added by #345;
- all three parent handovers and the parent's source/test state.

The shared `poll_loop_blocking_inhibit_lab.py` was updated in-place on this new child by adding the ingress helper while preserving the parent-only quarantine and pending-clear logic. No files under Master, CORE, QA, RELEASE, rental, or Pisonet ownership were edited.

## Paths changed

- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/coin_pulse_capture_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/esp8266_boot_polarity_lab.py`
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/esp32_boot_polarity_lab.py`
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/journal_mount_failclosed_lab.py`
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/pending_journal_recovery_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_fault_latch_edge_count_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_response_failclosed_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_response_keyless_authority_red.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_window_drain_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/relay_output_polarity_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/remote_config_pin_recovery_lab.py`

## Validation

- Local shell/compiler execution: NOT AVAILABLE in this activation.
- Exact-head Quarantine run [#45182191780](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45182191780) was in progress at the first PR head.
- Exact-head Relay/Output run [#45182191910](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45182191910) **FAILED** in `coin_pulse_capture_lab.py`: the child had inserted `coinIngressConfigurationAllows` into `FUNCTION_NAMES` but not the parallel `SIGNATURES` tuple, so mutation indexes shifted and the `missing-edge-latch` anchor was not found. The 17/17 positive coin-pulse markers still printed, but the job exited 1. This was a proven test-harness defect, not a firmware failure.
- Correction commit `724d892e980f878903425837226c45b321638793` adds the helper signature in the matching position, restoring positional parity. The failed run is retained as evidence; it is not relabeled PASS.
- Full run [#45182191977](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45182191977) validation job `137718519049` **FAILED** at the inherited QA-owned `Missing poll signature check`; ESP8266 target build job `137718518772` passed. Other target jobs were still running when checked.
- New exact-head Quarantine/Relay/Full runs after correction SHA `724d892` are pending and must be read separately.
- Parent #345 exact-head Quarantine run #45165015610 and Relay run #45165015665: PASS.
- Parent #345 Full run #45165015859: FAIL at inherited QA-owned poll-signature/controller protocol assertion; 14 target/platform jobs passed and validation-dependent stages did not pass.
- #346 had no PR-triggered runs at its then-current head `bd3fd6e85717395f768aae26a310b647cdd72a7e`; it remains a stale, unreconciled sibling candidate.

## Safety / release status

The change centralizes a configuration predicate and its tests; it does not add remote authority or permit unsigned poll responses. The firmware remains fail-closed. The CORE producer/consumer `response_sig` contract and QA golden vectors remain unresolved. Host tests are SIMULATED; physical coin acceptor, relay contacts, LittleFS durability and electrical pulse behavior are NOT TESTED. The 150 power-cut trials, 30-device 24-hour soak and electrical pulse/recovery remain NOT TESTED. HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.

## Next exact action

Open/reuse a DRAFT child PR targeting the live #345 branch, then fetch the resulting workflow runs and job logs for the exact final source/test SHA. Do not retarget, rebase or force-push #346; ask Master to mark it superseded only after reviewing the reconciled child.
