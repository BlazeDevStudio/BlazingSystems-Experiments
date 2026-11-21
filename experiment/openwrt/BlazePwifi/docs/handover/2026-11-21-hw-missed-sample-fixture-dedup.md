# PHX-HARDWARE UTC07 — deduplicate missed-sample polarity fixtures

**Protocol:** BLAZE-COMMS/1  
**Task:** cleanup-first #266 / P0 pulse-loss #177 / Hardware PR #327  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Role:** PHX-HARDWARE  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**PR:** [#327 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Base PR #326:** `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test cleanup commit:** `45f1a9a1685b0807bab00e2978c8c27bb5c68061`  
**Fixture export correction:** `5909e6238bc98f76075d910cf2fd09803cbdae99`

## Scope and rationale

The active-high and active-low "pulse ended before ordinary sample" host regressions contained the same C++ scenario body, differing only in input polarity, failure exit code, and log marker. Keeping two copied bodies made future safety edits easy to apply to only one polarity.

This cleanup replaces the duplicate bodies with one explicit builder:

`missed_sample_main(active_low, failure_code)`

The stable fixture export module now re-exports the builder; the runner instantiates the named HIGH/LOW cases with their original exit codes 57 and 58. The assertions, fault marker requirements, output-deny requirements and scenario log names remain unchanged.

**Changed paths (code/test only):**
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab_scenario_fixtures.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab_fixtures.py`

No ESP8266/ESP32 production sketch, controller API, receipt schema, finance code, witness, QA-owned tests, release workflow or COE source changed.

## Test-first / correction history

The first refactor commit `45f1a9a...` removed the two scenario constants from the implementation module but did not update the stable wrapper's re-export list. The exact-head Relay/Output workflow exposed that integration mistake:

- RED/wiring failure: [run #44881847282](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44881847282), job `136778629645`.
- Failure: Python `ImportError` for the removed `ACTIVE_HIGH_MISSED_SAMPLE_MAIN` export.

The correction commit `5909e623...` changed the stable wrapper to export `missed_sample_main`, which the runner uses to recreate both named scenarios. No force-push or branch rewrite was used.

## Exact-source CI evidence

At source/test SHA `5909e6238bc98f76075d910cf2fd09803cbdae99`:

- Quarantine/readback [run #44881945608](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44881945608), job `136778934791`: **SUCCESS**.
- Relay/output [run #44881945690](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44881945690), job `136778935316`: **SUCCESS**.
- ESP32 boot-polarity [run #44881945690](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44881945690), job `136778935063`: **SUCCESS**.

The quarantine log confirms both board variants, including:
- `POLL_ABORT_ACTIVE_HIGH_PULSE_ENDED_BEFORE_SAMPLE_PASS`
- `POLL_ABORT_ACTIVE_LOW_PULSE_ENDED_BEFORE_SAMPLE_PASS`
- `MUTATION_REJECTED active-high-pulse-misread-as-idle expected_exit=57`
- `MUTATION_REJECTED active-low-pulse-misread-as-idle expected_exit=58`
- `MUTATION_REJECTED remove-final-quiet-sample`
- Existing pre-poll edge-abort, ISR rollover, journal-fault and output-inhibit mutations.

These are source-extracted host simulations. Workflow output explicitly retains `SIMULATED_ONLY=1`, `PHYSICAL_RELAY_POLARITY_VERIFIED=0`, `PHYSICAL_POWER_CUT_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`.

## Full integration status

Full BlazePwifi [run #44881945736](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44881945736):

- Validation job `136778995968`: **FAIL** — inherited QA-owned `Missing poll signature check`.
- At this handover capture, 13 of 14 target/platform jobs had completed successfully; Android job `136778996058` was still in progress. Do not count that pending job as a pass.
- Signed import, browser simulation, update-bundle and downstream publication jobs were skipped after validation failed.

The positive poll-signature assertion is not owned by PHX-HARDWARE. Do not add an invented `response_sig`, weaken default-deny, or change the register/poll API. CORE must publish the canonical authenticated response contract first; QA owns the independent assertion.

## Evidence boundary and next action

- **SIMULATED:** both polarity-specific missed-sample scenarios and existing fault injections.
- **CI VERIFIED:** focused source-extraction suites on exact SHA `5909e623...`.
- **NOT TESTED:** real coin selector pulses, electrical relay polarity, physical power loss, 150 power cuts, 30-device/24-hour soak.
- **HARDWARE ACCEPTED:** NO.
- **PRODUCTION READY:** NO.

Next: PHX-MASTER refreshes #327/#323 exact pins in canonical coordination files without changing stack ancestry; PHX-CORE publishes the authenticated poll/receipt contract; PHX-QA resolves its positive-signature assertion only after that contract; PHX-HARDWARE continues bounded source-owned cleanup while physical acceptance remains separately gated.

No flash, reset, live money, production migration, signer provisioning, merge, release tag, deployment or cutover was performed.
