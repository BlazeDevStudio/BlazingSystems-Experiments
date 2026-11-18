# PHX-HARDWARE handover — preload OFF before relay/LED output enable

**Disposition:** source correction committed; focused exact-head CI pending; SIMULATED ONLY; physical GPIO/relay acceptance NOT TESTED; PRODUCTION NO-GO.

## Lineage

- Parent PR: [#320](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/320)
- Parent branch: `phoenix/hardware-poll-edge-latch-20261118`
- Parent HEAD at branch creation: `b2b41a3d6ce7887b9624137c966f58462895d3fa`
- Child branch: `phoenix/hardware-output-preload-child-20261118`
- New child PR: [#322](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/322) (OPEN/DRAFT/UNMERGED)
- Separate test-first RED candidate #321 remains OPEN/DRAFT and is not rebased, retargeted, merged or force-pushed.

## Defect and correction

Both ESP32 and ESP8266 `configureRuntimePins()` previously enabled relay and LED pins with `pinMode(..., OUTPUT)` before setting their logical OFF level. For active-low wiring, the default LOW output latch could briefly energize the relay during pin-mode transition.

Both sketches now:
1. Preserve old relay/LED shutdown before runtime pin reassignment.
2. Assign the new configured pin numbers.
3. Preload the new relay and LED logical OFF levels with `writeLogical()`.
4. Only then switch the relay and LED pins to OUTPUT.
5. Attach the coin interrupt after pin configuration.
6. Reassert logical OFF after output enable as a confirmation.

No coin admission, poll, POST, receipt, ledger, API, migration, signing, or release behavior changed.

## Test-first evidence

- RED source was the unchanged #320 firmware at #321's test-only head `8efc4308d5c205976838092bbb746ce6f2c56113`.
- Relay-output workflow [#44226524555](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44226524555), job `134540917601`, failed exactly at `OUTPUT_SEQUENCE_FAIL relay OFF must precede OUTPUT mode` after the existing polarity lab passed 48/48 for each board.
- The new lab compiles the exact extracted `writeLogical()` and `configureRuntimePins()` functions for both boards. It checks active-high and active-low ordering and injects a mutation that removes only the new-pin preloads while retaining old-pin shutdown and post-enable OFF confirmation.
- The mutation injector was tightened to target the exact assignment/preload sequence; this avoids the earlier test-only implementation's overly narrow text window.
- First #322 focused attempt [#44232408796](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232408796), job `134560390600`, failed because the extracted C++ harness lacked Arduino interrupt stubs (`digitalPinToInterrupt`, `detachInterrupt`, `attachInterrupt`, edge constants and ISR symbol). This was a test-harness compile failure, not a firmware compile failure. Added deterministic no-op host stubs and a `runCoinActiveLow` fixture binding at `bdddb96aeea4f0ace088233563f780822d1377c8`; exact-head rerun is pending.

## Commits

- Test-harness compile correction: `bdddb96aeea4f0ace088233563f780822d1377c8`

- ESP8266 source: `e55570b52d66b3a85526d89827f3bddd9c277432`
- ESP32 source: `279e8ccb8259d066e50f37322a984b822c2ac0cb`
- Workflow wiring: `c918253fe757b412d367510dba58c9f6181f2f0c`
- Regression lab: `1f882c979550ebe723d3fbb6a26e3986fd041fc9`

## Acceptance limits

The host lab models Arduino call ordering only. It does not measure GPIO voltage, active-low relay energization, contact bounce, coil suppression, boot strap interactions, board-specific pin behavior, or physical output transients. A scope/logic-analyzer and isolated noncustomer relay fixture are required before HARDWARE ACCEPTED. No flashing, reset, relay actuation, coin or customer hardware was performed.

## Exact-head CI update — 2026-11-18

Current source/test head `7ba56c1ba92dcffa2555e4cce10d3010c3afaf5b` (subsequent changes, if any, are documentation-only).

- Focused output-order workflow [#44232546775](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232546775), job `134560838939`: **SUCCESS**. The exact-source lab compiled both board functions, passed active-high and active-low ordering on ESP8266 and ESP32, and rejected the missing-preload mutation on both boards. Log summary: `PHX-HARDWARE: 4/4 output-enable sequence checks PASS`.
- Companion quarantine/readback workflow [#44232546822](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232546822), job `134560839035`: **SUCCESS**. Existing poll-window and pulse-capture suites also passed (8/8 per board; targeted edge/save/output-inhibit mutations rejected). SIMULATED ONLY.
- Full build [#44232546807](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232546807): **INCOMPLETE at last poll**. Validation job `134560890322` FAILED at the inherited QA-owned `Missing poll signature check`. ESP8266 and several platform builds passed; ESP32, Android, x86_64 and remaining targets were still running. Production import/signing and update-bundle jobs were skipped. This is not a Full CI pass.
- The first #322 focused attempt [#44232408796](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44232408796), job `134560390600`, failed because the C++ test harness omitted Arduino interrupt stubs. The corrected harness at `bdddb96aeea4f0ace088233563f780822d1377c8` is included in the successful exact-head run above.

All passing hardware labs remain host-simulated. GPIO voltage, active-low relay transient, contact behavior, electrical pulse/recovery, power cuts and device soak remain NOT TESTED.
