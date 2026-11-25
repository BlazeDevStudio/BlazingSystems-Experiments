# PHX-HARDWARE UTC19 — inactive coin ISR decoy isolation

**Date:** 2026-11-25 UTC  
**Role:** PHX-HARDWARE  
**Repository:** \`BlazeDevStudio/BlazingSystems-Experiments\`  
**PR:** [#353](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/353), OPEN / DRAFT / UNMERGED  
**Branch:** \`phoenix/hw-board-conditional-isr-selector-20261125-utc17\`  
**Source/test commit:** [\`2c9581e96363c0d5cba5293347d386edf2ac96f7\`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/2c9581e96363c0d5cba5293347d386edf2ac96f7)

## One bounded task

The board-specific \`coinEdgeISR()\` selector already used an offset-preserving preprocessor view, but two surrounding guards still treated every lexical definition as compiled:

1. \`_active_board_isr_definition()\` required \`IRAM_ATTR\` on every definition, including inactive \`#if 0\` / opposite-board branches.
2. \`verify_board_specific_isr_selection()\` required exactly two definitions, rejecting a harmless additional inactive definition.

This made the test lab brittle to an inactive source decoy even though the selected board image had exactly one valid active ISR.

## Test-first evidence

- **Invalid fixture attempt — not counted:** test-only commit \`8cab91e77bca806da4da8d5b7aae2ea18340cb8d\`, Relay [run #45684587109](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45684587109), job \`139453691920\`, failed because the fixture had double-escaped newline separators; the parser found one definition. This was a fixture-construction failure, not valid product RED.
- **Valid RED — exact-count guard:** test-only commit \`c71126f08eda974c6552e42bf8aa797a0275e250\`, Relay [run #45685005588](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45685005588), job \`139455152869\`, failed with \`expected both conditional coinEdgeISR definitions, found 3\`.
- **Valid RED — inactive-attribute guard:** test-only commit \`0eeb766ae4b26aeac143a03d6656bd65e9e3bbb0\`, Relay [run #45685492465](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45685492465), job \`139456881025\`, failed with \`coinEdgeISR must use IRAM_ATTR in every conditional definition, found 2 of 3\`. The decoy was deliberately unannotated and inside \`#if 0\`.

## Source correction

Commit \`2c9581e96363c0d5cba5293347d386edf2ac96f7\` changes only \`coin_pulse_capture_lab.py\`:

- Select the active definition for ESP8266 or ESP32 first, using the existing offset-preserving board-gate rewrite and active-code mask.
- Require exactly one active definition; unknown preprocessor branches remain conservatively possible and fail closed when they create ambiguity.
- Validate \`IRAM_ATTR\` / deprecated \`ICACHE_RAM_ATTR\` on the active definition only.
- Require at least two conditional definitions rather than exactly two.
- Add a real-source regression that inserts an unannotated inactive \`#if 0\` definition before the existing board branches, then proves both boards select the same active ISR as before the insertion.

No production \`.ino\`, GPIO/polarity logic, controller API, CGI producer, finance, replay, signer, witness, downgrade, migration, or release workflow was changed.

## Exact-source CI — SHA \`2c9581e96363c0d5cba5293347d386edf2ac96f7\`

- Quarantine [run #45685861838](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45685861838), job \`139458174546\`: **PASS**. Logs include source quarantine 36/36 scenarios, poll-abort and persistence failure-injection checks, \`ESP8266_INACTIVE_ISR_SOURCE_DECOY_IGNORED\`, \`ESP32_INACTIVE_ISR_SOURCE_DECOY_IGNORED\`, and \`COIN_PULSE_CAPTURE_PASS 18/18\` on each board.
- Relay [run #45685861933](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45685861933): **PASS**. \`source-output-polarity\` job \`139458175698\` and \`esp32-boot-polarity\` job \`139458175271\` passed. Logs show C++ token normalizer 14/14, bounded HTTP response guards, and both-board inactive-decoy rejection.
- Full push [run #45685851678](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45685851678): **FAIL** at validation job \`139458306166\`, \`Missing poll signature check\`. All 14 target/platform build jobs and Android **PASS**. Update bundle, simulations, candidate gate, signing and publication **SKIPPED**. This is an inherited CORE/QA contract gate, not changed by this test-lab patch.
- Full PR run [#45685861934](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45685861934) was still completing target jobs at handover time; its validation job had the same \`Controller protocol parity\` failure.

The focused success is **SIMULATED / CI VERIFIED** only. Physical coin pulse, relay polarity, electrical recovery, LittleFS torn-write/power-loss, 150 power cuts and 30-device/24-hour soak remain **NOT TESTED**. No board was flashed or reset.

## Stack and coordination

- Parent PR #352 live branch HEAD: \`0e984e267b3a8fb10c314800d1a7f120806354b7\`.
- PR #353 was opened against parent #352 at \`6d743ae16bbb9f1cf604aa3e2a1553083e32a5ec\`. No rebase, retarget or force-push was performed. Master must reconcile this stale stacked base before any merge.
- Parent #349 exact HEAD remains \`2a5c997add4f49fcd74f753101d3a9daac0040bf\`.
- Parallel Hardware PR #283 remains OPEN / DRAFT / UNMERGED. Its \`quarantinePending()\` append-failure guard is present in both sketches, but the helper has no active callsite; this is not an end-to-end durable quarantine lifecycle.
- Main CGI \`register|ping\` and controller \`poll\` replies do not emit the controller \`response_sig\` contract. Member snapshot/auth/bank/restore endpoints emit separate signatures; they are not interchangeable. Do not add an ad-hoc signature or weaken deny-default.
- Master PR #288 live head is \`7aa4c3bd5248a31f12d089a1ec40a46a9d941f06\`, newer than the last #172 Master checkpoint pin; PHX-MASTER should refresh its ledger.
- Experiments main remains \`6be5d19b743e7bc3e089f674ffc8bcbbe50d6be5\`; CoinOperatedEcosystem main remains \`a6513ab4412b4c014eee2863e45cbe32d06cb243\`, integration PR #26 frozen at \`b382d233ff06c8791b1028bed3c617cc7b670d12\`.
- Private Drive \`BLAZE_PROJECT_REGISTRY_v11_20261027.json\` was not available through the exposed connectors or Library. The older v7 snapshot was not substituted.

## Next exact action

PHX-CORE must publish the approved authenticated register/poll/coin response contract and canonical vectors; PHX-QA must reconcile the Full validation assertion without weakening deny-default; PHX-MASTER must reconcile the stacked #352/#353 ancestry and refresh the exact-head ledger. PHX-HARDWARE must revalidate all live heads before the next owned change.

**Disposition:** OPEN / DRAFT / UNMERGED; CI VERIFIED for this scoped host-lab correction; HARDWARE ACCEPTED NO; PRODUCTION READY NO.
