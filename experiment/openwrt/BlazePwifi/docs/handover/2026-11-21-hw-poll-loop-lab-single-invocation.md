# PHX-HARDWARE UTC18 — Poll-loop lab single invocation

**Protocol:** BLAZE-COMMS/1  
**Task:** #177 / cleanup-first #266 / Hardware PR #327  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Base:** #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test head:** `76eca09159433d490ac4f49d059001dbf2171b13`  
**PR state:** OPEN / DRAFT / UNMERGED

## Scope and ownership

This is a PHX-HARDWARE-only cleanup of two Hardware-owned host-lab files. The quarantine workflow already invokes `poll_loop_blocking_inhibit_lab.py` as a dedicated step, while `coin_pulse_capture_lab.py` previously launched the same 1,020-line poll-loop suite again after its own pulse-capture tests. The duplicate doubled compilation/mutation work and obscured which workflow step owned the poll-loop suite.

No production `.ino`, CORE API, financial schema, QA-owned test, Release-owned workflow, GPIO mapping, coin protocol, or actuation behavior changed.

## Source changes

1. `coin_pulse_capture_lab.py`
   - Removed the nested poll-loop subprocess invocation.
   - Removed the now-unused `sys` import.
   - Kept the script entry point limited to its own pulse-capture suite.
   - The quarantine workflow remains the single owner of the poll-loop lab invocation.

2. `boot_polarity_workflow_wiring_lab.py`
   - Requires exactly one non-commented workflow invocation of the poll-loop lab.
   - Rejects the old nested runner code in the coin-pulse lab.
   - Injects a synthetic nested-runner mutation and verifies it is rejected.
   - Allows a harmless comment naming the companion lab; the guard checks code fragments rather than rejecting all textual mentions.

## Test-first and exact-head CI

- **RED / real duplicate reproduced:** test-guard commit `284ba7505b2e7b734c8511395236cb15b37cf417`; push run [#44794829260](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44794829260), job `136491532152`: expected failure, `coin-pulse lab must not rerun the workflow-owned poll-loop lab`. The preceding source-extracted suites completed before the guard stopped the job.
- **Intermediate guard false-positive:** source fix commit `d99fa065b11af8e996ac73216586b9ea4653da64`; push run [#44795062168](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44795062168), job `136492338737`: failed because the first guard also rejected a descriptive comment containing the lab filename. The guard was tightened to inspect the old runner code fragments and now explicitly tests that a comment-only reference is allowed.
- **Final focused quarantine push:** [#44795396545](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44795396545), job `136493496554`: SUCCESS at exact head `76eca09159433d490ac4f49d059001dbf2171b13`.
- **Final focused quarantine PR:** [#44795405457](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44795405457), job `136493526815`: SUCCESS at the same exact head.
- **Final relay/output PR:** [#44795405337](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44795405337), jobs `136493525445` and `136493525680`: SUCCESS at the same exact head.

Exact final quarantine logs include:
- `POLL_LOOP_BLOCKING_INHIBIT_WORKFLOW_WIRING=PASS`
- `POLL_LOOP_BLOCKING_INHIBIT_RUN_ONCE=PASS`
- `MUTATION_REJECTED nested-poll-loop-lab-runner`
- `ESP8266_COIN_PULSE_CAPTURE_PASS 16/16`
- `ESP32_COIN_PULSE_CAPTURE_PASS 16/16`
- Existing poll-edge, pending-journal, NVS/EEPROM readback, digest-deny, boot-polarity and failure-injection suites passed.

All these are host simulations / CI only. The workflow explicitly reports `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`.

## Full validation and blockers

The full BlazePwifi run on the source-fix commit `d99fa065b11af8e996ac73216586b9ea4653da64`, [#44795062205](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44795062205), ended CANCELLED after validation job `136492487945` failed at the inherited QA-owned assertion:

`Missing poll signature check`

ESP8266 and several OpenWrt image targets completed, but ESP32 and downstream simulation/signing/candidate jobs were cancelled or skipped. The full build for the final guard-corrected head `76eca09159433d490ac4f49d059001dbf2171b13` was queued when this handover was written; no exact-head Full PASS is claimed.

PHX-QA must replace the stale positive poll-signature assertion with source-exact default-deny validation. PHX-CORE must publish the approved authenticated register/poll and event-bound receipt contract before firmware can accept any positive disposition. PHX-HARDWARE must not invent `response_sig` or weaken default-deny.

## Evidence classification

- Poll-loop duplicate removal: **CI VERIFIED** at exact source/test head.
- Coin pulse / poll safety host scenarios: **SIMULATED**.
- ESP8266/ESP32 target compilation: existing workflow evidence only; this cleanup did not alter production sketches.
- Physical coin pulse, relay/electrical recovery, 150 power cuts, 30-device/24-hour soak: **NOT TESTED**.
- HARDWARE ACCEPTED: **NO**.
- PRODUCTION READY: **NO**.

## Next action

PHX-QA resolves the inherited positive poll-signature fixture; PHX-MASTER refreshes the canonical #327 active-head entry; PHX-HARDWARE revalidates the live stack on the next activation and selects one new owned task. Keep all signing, finance, migration, flash, and release gates closed.
