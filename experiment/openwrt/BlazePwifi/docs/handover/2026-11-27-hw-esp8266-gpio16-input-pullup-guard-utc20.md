# PHX-HARDWARE — ESP8266 GPIO16 coin-input capability guard

**Updated:** 2026-11-27T20:36:10Z  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-runtime-pin-config-guard-20261127-utc04`  
**Parent PR:** [#357 — Validate board GPIO roles before Vendo configuration persistence](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/357)  
**Base branch:** `phoenix/hw-poll-preflight-lab-modules-20261127-utc18` at `9f7a8ecb915cf199a82c0b4d37c56c40d722037b`  
**Source/test commit:** `750af995e28d7977dcac8ea4cc800f71c71d27d8`  
**Status:** SCOPED CI VERIFIED; FULL INTEGRATION BLOCKED.

## Finding

The ESP8266 runtime pin validator accepted GPIO16 as the coin-input role. The sketch configures that input with `pinMode(runCoinPin, INPUT_PULLUP)`, but the official ESP8266 Arduino Core reference lists GPIO16 as supporting `INPUT`, `OUTPUT`, and `INPUT_PULLDOWN_16`; GPIO0–15 support `INPUT_PULLUP`. GPIO16 therefore cannot satisfy the firmware's configured coin-input bias using the internal pull-up.

Reference: https://arduino-esp8266.readthedocs.io/en/latest/reference.html

## Change

- ESP8266 `validRuntimePins()` now rejects GPIO16 only when assigned to the coin-input role.
- GPIO16 remains allowed for relay and LED output roles because the core documents output support.
- Existing default tuple (coin 4 / LED 14 / relay 5) is unchanged.
- Invalid stored tuples continue through the existing safe-default path.
- ESP32 source and shared controller/finance contracts were not changed.

## Regression coverage

- Reject `validRuntimePins(16,5,14)`.
- Continue accepting GPIO16 as relay output: `validRuntimePins(4,16,14)`.
- Continue accepting GPIO16 as LED output: `validRuntimePins(4,5,16)`.
- Require the source to retain the `INPUT_PULLUP` setup that motivates the role restriction.
- Inject removal of the GPIO16 guard and require the host lab to reject the mutation.

The source-extracted host lab is SIMULATED evidence only. It does not measure input voltage, external resistor values, board revisions, relay contacts, or coin-slot pulses.

## Test status

- Source/test commit: `750af995e28d7977dcac8ea4cc800f71c71d27d8`.
- Focused GitHub Actions on final documentation head: PENDING.
- Firmware target builds: PENDING exact-head Actions.
- Physical GPIO / electrical acceptance: NOT TESTED.

## Blockers and next action

The deny-only v0.6 stack remains OPEN / DRAFT / UNMERGED. P0 poll/pulse mitigation, authenticated CORE register/poll/receipt/disposition, QA controller parity, physical wiring/polarity acceptance, 150 power cuts, 30-device/24-hour soak, signer/witness, durable accounting/replay, v1-to-v2 migration, and independent release signoff remain unaccepted.

**Next exact action:** run and inspect the exact-head `PHX-HARDWARE Active v0.6 Poll Intake Deny` workflow; then request Master to register PR #357's new source/test SHA in the role and integration matrices. Do not merge or enable coin/relay admission.


## Exact CI results

- Focused PR #46065708272: PASS, job 140730384339, source/test SHA 750af995e28d7977dcac8ea4cc800f71c71d27d8.
- Focused docs-head #46065796271: PASS, job 140730661656, docs SHA 022c3100a3b04acc02960ac00b7ac2933494da75.
- Mbed TLS #46065708312: PASS 3/3 (source contract 140730385175, core 3.3.13 job 140730384776, core 4.0.0 job 140730385291).
- Native #46065708271: FAIL at QA-owned PAY-0745 literal `clearPending(true/false)` assertion; the pending-sequence check itself passed. No unsafe clear call was added.
- Full build #46065702850: FAIL at handover freshness on source SHA 750af995 because the workflow checkout predated the docs sync; all 14 firmware target/platform jobs and Android passed, downstream bundles/simulations/sign/publish/candidate stages skipped.
- The source+handover checkpoint was co-committed after 5025a318 so a new Full run can see the synchronized record. Physical GPIO/electrical acceptance remains NOT TESTED.


## PHX-HARDWARE UTC20 — final GPIO16 capability evidence (SCOPED CI VERIFIED; FULL CONTROLLER PARITY BLOCKED)

**Role:** PHX-HARDWARE · **Repo:** `BlazeDevStudio/BlazingSystems-Experiments` · **PR:** [#357](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/357) OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-runtime-pin-config-guard-20261127-utc04` · **tested source+handover head:** `cfc251d3b947982ec3d24ba6a4875bdfaf6fbdcd`  
**Substantive source/test commit:** `750af995e28d7977dcac8ea4cc800f71c71d27d8` · **base #355:** `9f7a8ecb915cf199a82c0b4d37c56c40d722037b`

### Final exact-head results
- Focused push [#46066316984](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46066316984), job `140732371645`: PASS at `cfc251d3...`.
- Focused PR [#46066323699](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46066323699), job `140732392213`: PASS at `cfc251d3...`.
- Focused log: `RUNTIME_GPIO_CAPABILITY_PASS ESP8266 coin16=DENY relay16=ALLOW led16=ALLOW`; removal mutation rejected; append-only ledger guard PASS (`base_bytes=1132798`, `appended_bytes=34141`).
- Mbed TLS [#46065708312](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46065708312): PASS 3/3 at source/test SHA `750af995...` — source contract `140730385175`, core 3.3.13 `140730384776`, core 4.0.0 `140730385291`. The final-head rerun [#46066323347](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46066323347) had source-contract PASS; target builds were still IN PROGRESS at the last read.
- Native [#46066323479](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46066323479), job `140732392015`: FAIL at QA-owned `tests/v060_vendo_sequence_contract.py` assertion requiring literal `clearPending(true/false)` callsites, after the Vendo pending sequence contract passed. No unsafe callsite was added.
- Full build [#46066316962](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46066316962): mandatory handover gate and CI-0701 PASS; validation job `140732545614` FAIL at Controller protocol parity. The QA-owned `tests/controllers.sh:21` requires `config_revision`; exact current PR #357 ESP8266 and ESP32 sketches both lack it, while current main contains it. This is a shared controller-contract dependency; Hardware did not invent the field. All 13 firmware target jobs PASS; Android job `140732545663` was still IN PROGRESS at last read. Update-bundle and v0.4 simulation jobs were skipped; signing/import/publish/candidate remained skipped. Overall Full run was still IN PROGRESS at last read.
- Full PR run [#46066323413](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46066323413) remained IN PROGRESS at last read.

### Scope and release status
GPIO16 is rejected only for the ESP8266 coin-input role because the sketch uses `INPUT_PULLUP`; the official core reference does not list that mode for GPIO16. GPIO16 remains allowed for relay/LED output roles. Default tuple 4/14/5 is unchanged. This is source-extracted SIMULATED / CI VERIFIED behavior only.

P0 #177 remains OPEN (PHX-L-VERIFY's pulse-loss reproduction); deny-only v0.6 stack #354/#355 remains unmerged. Physical GPIO/electrical acceptance, 150 power cuts, 30-device/24-hour soak, protected signer/witness, durable accounting/replay, v1→v2 migration and independent QA/release acceptance remain NOT TESTED / NOT ACCEPTED. No production admission, flash, device reset, migration, signing, release, merge or deployment.

**Next exact action:** PHX-MASTER refresh #357's exact head `cfc251d3b947982ec3d24ba6a4875bdfaf6fbdcd` in the integration matrix; PHX-CORE publishes the approved `config_revision` contract; PHX-QA reconciles PAY-0745 without unsafe clear callsites. Hardware keeps coin/relay admission denied.
