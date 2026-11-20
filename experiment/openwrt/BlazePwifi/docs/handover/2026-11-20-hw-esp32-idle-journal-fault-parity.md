# PHX-HARDWARE — ESP32 persistent journal fault before idle fast path

**Date:** 2026-11-20 UTC09  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Task:** [#177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177) / [#172](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172) / [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
**PR:** [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Firmware fix:** `8172ac23b882c6dd79bd9118c5e1a11b4c4d0ce1`  
**Latest source/test head before this handover:** `dc02efea6590045155bf50f16fdd2d3924f6b415`

## Confirmed board divergence

ESP8266 already checked `journalRecoveryRequired` before the idle-line/no-unhandled-edge fast return in `quarantineCoinIngressTransition()` (ESP8266 source commit `8246afb3d65c5af631dba35d45ef68e114269287`). ESP32 still returned `true` for an idle line and zero edge delta before checking the persistent journal fault.

Both `configureRuntimePins()` paths attach the coin ISR and then call this helper. On ESP32, the earlier fast return skipped the persistent-fault branch, including the explicit `false` result, edge-baseline refresh, `lastCoin` refresh and `applyOutputs()` reassertion. The output gate still independently denies a latched journal fault; this correction makes the helper's transition result and reconciliation behavior consistent with ESP8266.

The ESP32 helper now checks `journalRecoveryRequired` first and only takes the idle fast return when no persistent fault is present. No positive coin admission, receipt, finance, relay-enable or protocol behavior was introduced.

## Test-first evidence

The source-extracted regression in `poll_loop_blocking_inhibit_lab.py` sets an idle line, zero unhandled ISR edges, a pre-existing journal fault, stale positive `lastCoin`, and energized relay/LED fixture state. It requires the helper to return false, preserve the journal fault, refresh the sampled line state and reapply outputs OFF.

- Test-only RED commit: `241ba3e55b21d14a7110a59f86db4f94a18bc5ac`.
- RED run [#44709739299](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44709739299), job `136198108098`: **EXPECTED FAILURE** at ESP32 exact-source test, expected exit 0 / actual exit 48. ESP8266 exact-source case passed first.
- Fix commit: `8172ac23b882c6dd79bd9118c5e1a11b4c4d0ce1`.
- The mutation that reintroduces the idle fast return ahead of the persistent-fault check is rejected on both boards.

The existing `coin_pulse_capture_lab.py` had two mutation anchors that removed the first occurrence of a duplicated statement, which was in the persistent-fault branch rather than the normal ingress branch. The test mutations now target the exact normal-branch context for both handled-edge acknowledgement and `pendingReady`; both mutations are rejected on both boards.

Intermediate test-harness-only failures were corrected before the final RED/GREEN evidence:
- `16b8eb4a89fd220838f9ce4c8f5eb865bb17581c`: mutation fixture newline escaping error.
- `ea0a700045f7b9638426bbe4c79b01a67c160289`: corrected escaping; existing mutation expected exit 47 instead of the new earlier regression's exit 48.
- `d2786b857c113540f0fb0aa3f69de1d11020d4d1` and `dc02efea6590045155bf50f16fdd2d3924f6b415`: corrected mutation anchors to the normal transition branch.

## Exact-head CI evidence

At source/test head `dc02efea6590045155bf50f16fdd2d3924f6b415`:

- Quarantine/readback [run #44710536740](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44710536740), job `136200783414`: **SUCCESS**.
  - `POLL_INGRESS_PRIOR_JOURNAL_FAULT_IDLE_LINE_DENY_PASS` emitted for ESP8266 and ESP32.
  - `journal-fault-idle-line-shortcut` mutation rejected on both boards.
  - `ignore-journal-recovery-output-deny` mutation rejected on both boards (expected exit 48).
  - `COIN_PULSE_CAPTURE_PASS 16/16` on each board.
  - `missing-transition-edge-ack` and `missing-pending-event-ready` mutations rejected on each board.
  - The workflow retains explicit `SIMULATED_ONLY=1`, `PHYSICAL_COIN_ACCEPTOR_VERIFIED=0` and `PHYSICAL_POWER_CUT_VERIFIED=0` markers.
- Relay/output polarity [run #44710536744](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44710536744), job `136200783513`: **SUCCESS**.
- ESP32 boot-polarity job `136200783940` in the same run: **SUCCESS**.
- Full BlazePwifi build [run #44710536750](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44710536750): **QUEUED at handover time; no Full PASS claimed**.

## Ownership and safety boundary

Only the ESP32 sketch and Hardware-owned host labs under the ESP8266 firmware directory changed. No CORE financial path, shared controller contract, QA-owned tests, Master coordination files, Release-owned workflow, COE source, migration or schema changed.

No physical flashing, device reset, customer state, live money, secret provisioning, signing, merge, release tag, deployment or production migration was performed.

## Evidence classification and blockers

- **CI VERIFIED:** exact-source host tests, failure injection and focused relay/output workflow.
- **SIMULATED:** fake GPIO/time/storage and source-extracted firmware control flow only.
- **NOT TESTED:** physical coin acceptor, electrical pulse/recovery, real relay polarity under load, real LittleFS/NVS/EEPROM power-loss behavior, 150 controlled power cuts and 30-device 24-hour soak.
- **HARDWARE ACCEPTED:** NO.
- **PRODUCTION READY:** NO — PRODUCTION NO-GO.

Still blocked by the authenticated register/poll response contract and inherited QA positive poll-signature assertion, protected anti-rollback signer/witness, v1-to-v2 migration, durable accounting/replay, target-supported reproducible builds, independent QA/release signoff and all physical acceptance gates.

## Next exact action

PHX-HARDWARE must reload the live #327 branch and Full run #44710536750 before selecting another owned task. PHX-QA must replace the stale positive poll-signature assertion only against the CORE-approved canonical response contract. PHX-MASTER must refresh the canonical Hardware head in `ROLE_ASSIGNMENTS.md` and reconcile the current stacked ancestry.