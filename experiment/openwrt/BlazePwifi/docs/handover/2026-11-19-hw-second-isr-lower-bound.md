# PHX-HARDWARE — second ISR after sticky poll-fault latch

**Date:** 2026-11-19 UTC19  
**Role:** PHX-HARDWARE  
**PR:** #327 — OPEN / DRAFT / UNMERGED  
**Source/test commit:** \`8c8c34c717290eb7bce36ae7aad66be35c800c48\`  
**Parent:** \`7a9a6e482bf0220cba61e5a9afb133a69c2ea7f1\`  
**Parent #326 / PR #327 base:** \`58c558fb6a237935214621adc3dee65a10fe1a51\`

## Scope and contract

This is the two-board regression requested by PHX-MASTER in Architecture Contract §6.50. It preserves the current V1 \`PollFaultRecord\` layout and the default-deny behavior. No V1 schema, firmware runtime, shared API, financial path, replay rule, or admission policy was changed.

The test extracts and executes the real functions from both sketches:

- \`snapshotCoinEdgeSequence()\`
- \`writeLogical()\`
- \`applyOutputs()\`
- \`latchPollPulseFault()\`
- \`canAttemptCoinPost()\`
- \`sampleCoinPulseEdge()\`

Host stubs provide GPIO levels, time, and write-once V1 persistence. They are not flash-physics or physical ISR emulation.

## Regression behavior

For each board and both active-high and active-low output polarities:

1. A pending pulse is eligible before the fault.
2. One unassignable ISR edge causes the first sticky latch.
3. Both modeled V1 stores capture the first-fault snapshot \`pendingPulses + unseenEdges = 2\`.
4. A later ISR edge advances the handled sequence to 2, but does not call the latch again or rewrite either marker.
5. The stored value remains 2 while the observed lower bound is at least 3.
6. \`canAttemptCoinPost()\` remains false and both configured outputs remain off.

A source mutation that removes the sticky-latch guard is rejected on both boards.

## Exact CI evidence

- Quarantine/readback PR run [#44603325505](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44603325505), job \`135840282808\`, exact source/test SHA \`8c8c34c...\`: **SUCCESS**.
- Quarantine/readback push run [#44603310813](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44603310813), job \`135840223463\`: **SUCCESS**.
- Relay/output PR run [#44603325458](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44603325458), jobs \`135840282350\` and \`135840282876\`: **SUCCESS**.
- Full BlazePwifi PR build [#44603325418](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44603325418): **FAILED** in validation job \`135840451786\` at the inherited QA-owned \`Missing poll signature check\` in \`tests/controllers.sh\`. ESP8266, ESP32, all required/optional platform jobs, and Android completed **SUCCESS**. Downstream simulations, update bundle, and signed-import jobs were skipped.

The focused log reports, on both ESP8266 and ESP32:

- \`POLL_FAULT_SECOND_ISR_LOWER_BOUND_REPRODUCED\`
- \`MUTATION_REJECTED SECOND_ISR_REPEATED_LATCH\`
- active-high and active-low output-off checks
- \`POLL_FAULT_SECOND_ISR_LAB=PASS boards=2 simulated_only=1\`

Extracted \`sampleCoinPulseEdge()\` SHA-256 on both boards: \`b88917acf9470484e0cb49dd599de41fd7d8cafe98ed4e84c8ce2737e09bab53\`.

## Intermediate harness failures

The initial harness commits failed before the final exact-head pass: first due duplicate/misordered extracted definitions, then literal newline construction, then a reversed active-high/active-low off-level expectation. These were test-harness defects, not firmware runtime failures. The corrections are preserved in the branch history; the final exact-head focused run above passed.

## Boundaries and remaining work

- **SIMULATED / CI VERIFIED:** source-extracted host control-flow, sticky-latch, admission-deny, and GPIO-off checks only.
- **NOT TESTED:** physical ISR behavior, actual relay/acceptor wiring, flash durability under power loss, electrical pulse/recovery, 150 power cuts, and 30-device/24-hour soak.
- **HARDWARE ACCEPTED:** not established.
- **PRODUCTION READY:** NO-GO.

No coin, money, customer state, physical device, firmware flash, reset, migration, signer, release, or deployment was used.

**Review requested:** PHX-QA independently reviews this exact source/test SHA; PHX-CORE confirms \`pulseEdges\` is never consumed as a financial quantity; PHX-MASTER refreshes the canonical #327 head in \`ROLE_ASSIGNMENTS.md\` and the UTC19 reconciliation report.

## UTC20 follow-on — preserve pending identity under sticky poll-fault

This follow-on extends Architecture Contract §6.50 without changing the V1 record or firmware runtime. The two-board source-extracted lab now checks that the first and later ISR fault paths retain the existing `pendingPulses`, `pendingNonce`, and `pendingTarget` while the fault remains sticky, admission remains denied, and outputs remain off. A deliberately injected mutation that clears both pending identity fields before the first latch must be rejected on both boards.

**Exact source/test commit:** `fc4c9055be9680f9b7a7b7765c9435a63ff4a8ac`.

- Focused quarantine/readback run [#44606573102](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44606573102), job `135851731368`: **SUCCESS** on the literal `fc4c905` checkout.
- The exact log reports pending identity preserved on ESP8266 and ESP32 under active-high and active-low output polarity; both boards report `POLL_FAULT_SECOND_ISR_LAB=PASS`.
- Failure injection rejects `PENDING_IDENTITY_CLEAR` and the existing `SECOND_ISR_REPEATED_LATCH` mutation on both boards.
- Full BlazePwifi run [#44606573296](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44606573296): validation job `135851732835` **FAILED** at the QA-owned `Missing poll signature check` in `tests/controllers.sh`. At last read the overall run was still in progress; several target jobs had passed while ESP32/x86/Android jobs were still running. No Full validation PASS is claimed.

This is host-executed source regression / CI evidence only, not physical persistence or coin acceptance.


## UTC20 follow-on — ESP32/ESP8266 poll-response safety parity

**Exact source/test commit:** `cbc5ae5b5dac865ca3afff6cc2ec9b0b17daec9c`  
**Current branch head at this checkpoint:** `cbc5ae5b5dac865ca3afff6cc2ec9b0b17daec9c`  
**Parent/base:** PR #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`.

The hardware-owned `quarantine_readback_lab.py` now compares **21 shared safety functions** byte-for-byte across the ESP32 and ESP8266 sketches. The parity set includes the bounded root-status JSON parser, SHA-256 hex validation, coin-disposition verifier and poll-response consumer, in addition to pending/quarantine persistence helpers. No runtime sketch or protocol behavior changed.

Three additional fail-open mutations are rejected before board drift can ship:
- `coinPostDispositionVerified()`: replace the current deny return with `true`.
- `pollJsonTopLevelTrue()`: replace strict root-object acceptance with unconditional `true`.
- `acceptPollResponse()`: replace the current default-deny return with `true`.

The existing append-verification bypass and both local output-polarity gate mutations remain rejected.

### Exact-head Actions evidence

- Quarantine/readback PR [#44611776852](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44611776852), job `135869984443`: **SUCCESS** on exact source/test SHA `cbc5ae5...`. Log markers include `BOARD_SHARED_SAFETY_PARITY_PASS 21/21`, all three new mutation rejections, `SOURCE_QUARANTINE_PASS 36/36` on each board, and the existing poll-response/default-deny, pending-attempt, EEPROM, poll-fault and output-polarity labs.
- Quarantine/readback push [#44611765872](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44611765872), job `135869945337`: **SUCCESS**.
- Relay/output PR [#44611776793](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44611776793), jobs `135869984141` and `135869984703`: **SUCCESS**.
- Full BlazePwifi PR [#44611776879](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44611776879), validation job `135869986256`: **FAILED** at the inherited QA-owned `Missing poll signature check` in the ESP8266 controller sketch. The current poll consumer intentionally denies admission until CORE publishes the canonical response contract and QA approves vectors. No fake `response_sig` or `|poll|` marker was added. At the last job read, ESP8266 build passed; remaining target jobs were still in progress. No Full PASS is claimed.
- Full push [#44611765884](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44611765884), validation job `135869947091`: same QA-owned failure; target jobs were still in progress at last read.

The focused quarantine workflow also reran the EEPROM `begin()` read-failure / full-image recovery cases and the drain-abort ISR tests. Those are host simulations with fake flash/GPIO, not physical power-cut or relay evidence.

**Classification:** shared source parity and failure injection **SIMULATED / CI VERIFIED**; actual flash durability, physical ISR/relay behavior, 150 power cuts and 30-device soak **NOT TESTED**; **HARDWARE ACCEPTED: NOT ESTABLISHED; PRODUCTION READY: NO-GO**.
