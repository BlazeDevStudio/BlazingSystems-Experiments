# PHX-HARDWARE UTC18 — C++ literal fidelity in ESP8266/ESP32 poll-safety parity

**Date:** 2026-11-25 UTC  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#352](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/352), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-exact-arduino-core-matrix-20261125-utc11`  
**Parent PR:** [#349](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/349), branch `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Parent exact HEAD:** `2a5c997add4f49fcd74f753101d3a9daac0040bf`  
**Source/test HEAD:** `8eab82606ab8bf7ae5c598edde739d7b47e7c7a2`

## One bounded task

The poll-safety board-parity helper used `" ".join(body.split())`. That normalized whitespace inside C++ string/character/raw literals as if it were formatting. A board-specific diagnostic or literal could therefore drift while the parity check remained green.

The regression fixture constructs equivalent `applyOutputs()` bodies whose string literal differs only by one internal space:

- ESP8266: `"FAULT  LATCHED"`
- ESP32: `"FAULT LATCHED"`

Those are different literal bytes and must not compare equal.

## Test-first and implementation history

1. **Test-only RED:** commit [`458afbef`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/458afbef288e356ccc2ded0334fdf22edc1f4424) added the full-source parity regression. Quarantine [run #45671637783](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45671637783), job `139408168966`, failed with `POLL_SAFETY_LITERAL_WHITESPACE_MUTATION_SURVIVED`. ESP8266 exact-source workflow [run #45671637663](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45671637663), job `139408169778`, independently stopped at the same expected RED.
2. **First implementation attempt:** commit [`87eb48d9`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/87eb48d9906562562cf009d0e51b988baa1b1ad7) switched parity to the existing C++ token normalizer. It exposed a second test-harness assumption: the existing failure-injection matrix used raw string replacement and could not mutate token tuples. Relay [run #45671944802](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45671944802), job `139409276179`, failed at `ESP32 applyOutputs parity mutation anchor missing`. This was not accepted as GREEN.
3. **Final correction:** commit [`8eab8260`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/8eab82606ab8bf7ae5c598edde739d7b47e7c7a2) keeps lexical token streams for parity and replaces the string-based mutation anchors with `replace_cpp_tokens()`, which requires exactly one matching token subsequence. The parity check now ignores formatting/comments while preserving exact literal contents and token boundaries.

## Exact-source CI evidence — source/test SHA `8eab82606ab8bf7ae5c598edde739d7b47e7c7a2`

- Quarantine [run #45672193685](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45672193685), job `139410148857`: **PASS**. Logs include `POLL_SAFETY_LITERAL_WHITESPACE_MUTATION_REJECTED`, `POLL_SAFETY_BOARD_PARITY_PASS 19/19 normalized helpers`, and rejection of the ESP32 journal-fault guard mutation.
- Relay [run #45672194428](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45672194428), jobs `139410151542` and `139410152270`: **PASS / PASS**. Logs include the literal-whitespace mutation rejection, 19/19 parity, C++ token normalizer contract 14/14, poll-response fixture boundary 4/4, and bounded HTTP response tests on both boards.
- ESP8266 core 3.1.2 [run #45672193510](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45672193510), job `139410149072`: **PASS**. Sketch image 363,728 bytes; SHA-256 `cad045f77cbc9b1384d6bf10b40b10236080037c1ab015bb6a07188e59e475d5`.
- ESP32 core 3.3.13 [run #45672193620](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45672193620), job `139410149591`: **PASS**. Sketch image 1,045,808 bytes; SHA-256 `2c751b06ab69015c94a0bee85bd5f627c0a23c2ebfd0e50a422cd4cf36eaf87b`.
- ESP32 core 4.0.0, same run, job `139410148938`: **IN PROGRESS at checkpoint**; not counted as PASS.
- Full BlazePwifi workflow [run #45672193755](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45672193755): **PENDING at checkpoint**; no result claimed for this exact SHA.

All successful workflows are host/CI evidence. Logs explicitly retain `SIMULATED_ONLY=1`, `PHYSICAL_RELAY_POLARITY_VERIFIED=0`, `PHYSICAL_POWER_CUT_VERIFIED=0`, and `FINANCIAL_PRODUCTION_AUTHORIZED=0`.

## Scope and non-claims

Only `poll_loop_blocking_inhibit_lab_source_contracts.py` changed in the final source/test commit. No `.ino` sketch, CGI producer, controller API, relay actuation, coin accounting, replay, signer, witness, downgrade, migration, or COE destination file changed.

- Host/CI: **CI VERIFIED** for the scoped parity regression and the completed focused jobs above.
- Hardware: **NOT TESTED**; no board was flashed, reset, or electrically exercised.
- Production: **NO-GO**; no release, merge, signing, migration, or deployment authorized.

## Live coordination readback

- Experiments `main`: `6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5`.
- COE `main`: `a6513ab4412b4c014eee2863e45cbe32d06cb243`; COE integration PR #26 remains OPEN / DRAFT / FROZEN at `b382d233ff06c8791b1028bed3c617cc7b670d12`.
- Master PR #288 remains OPEN / DRAFT / UNMERGED at `555f50d8dd3ecd8ee2e7adbf8ecafd092470288f`; latest Master table still records cleanup #266 as 0/7 and production NO-GO.
- Hardware #239 remains OPEN / DRAFT at `d83b715b116185107737fef721c2eece8feebf39`; #254 remains OPEN / DRAFT at `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`; parallel #283 remains OPEN / DRAFT at `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`. Their bases/stacking were not changed.
- On #283, the current quarantine helper returns before `clearPending()` when append fails, but it has no active callsite in the inspected sketches; this is not treated as an accepted end-to-end fix. Current main CGI `register|ping` and `poll` responses do not emit `response_sig`; member endpoints do. No API contract was invented or changed here.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not recovered from the available file library; no Google Drive connector was exposed in this run. Older registry snapshots were not substituted.

## Next exact action

PHX-CORE must publish the approved authenticated register/poll/coin response contract and canonical vectors; PHX-QA must independently reconcile the Full validation assertion; PHX-MASTER must refresh the role/CI table and preserve the stacked PR ancestry. PHX-HARDWARE must re-read live heads before selecting the next hardware-owned task.
