# PHX-HARDWARE — poll-fault output-inhibit stack reconciliation

**Checkpoint:** 2026-11-18 UTC11  
**Role:** PHX-HARDWARE  
**Canonical review candidate:** PR #322 → PR #323  
**Branch:** \`phoenix/hardware-poll-fault-dual-store-20261118\`  
**Source/test SHA:** \`176ad50da2180ee085e2fb63ddb23d17b53dd63d\`  
**Parent:** PR #322 at \`50d93e0de3d682550b6f02fb43484e76ad9c7e08\`

## Stack decision

Master's live review chain is #314 → #315 → #317 → #320 → #322. I select #322 as the output-preload parent and #323 as the poll-fault dual-store child for the canonical **review candidate**, because #323 is already based on #322 and adds the secondary-store/reboot-hold implementation.

- #321 is an alternate child of #317 with overlapping output-enable files and a different ancestry. Do not compose it automatically.
- #324 is a parallel child of #322 that adds a direct marker-open output-inhibit regression. Do not compose the branch or source commits automatically.
- Port only the missing regression into #323. Leave #321 and #324 OPEN/DRAFT/UNMERGED for Master to reconcile. This is a review-stack recommendation, not merge or integration authority.

## Concrete change

The #323 ESP8266 and ESP32 sketches already call \`applyOutputs()\` immediately after latching the deny state and before the secondary NVS/EEPROM writer and LittleFS marker write. This checkpoint does not change production firmware.

Ported and strengthened the direct regression in:

- \`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py\`
- \`.github/workflows/phx-hardware-relay-output-polarity.yml\`

The source-extracted harness now observes the exact entry boundary for both persistence operations:
1. the secondary \`writePollFaultBackup()\` call (NVS on ESP32 / EEPROM emulation on ESP8266);
2. the LittleFS \`/pollpulse.fault\` open-for-write call.

The test deliberately starts with relay and LED logical outputs active, calls the production-extracted \`latchPollPulseFault()\`, and requires both observations and final output state to be OFF while the journal recovery latch is set, insertion is disabled and the target is cleared.

A failure-injection mutation removes the early \`applyOutputs()\` call before the first persistence operation. The harness requires this mutation to exit with the expected failure code 23 on **both** board source extractions. The workflow path filter and step now execute this lab on the exact PR head.

## Exact-head evidence

### Initial implementation error — not counted as RED

- Commit: \`938da1a0f518b4d245a8c863e65e9f01465212ad\`
- Relay workflow [44300603872](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44300603872), job \`134789019979\`: **FAILURE** because the mutation string contained an incorrectly escaped newline and the intended mutation did not apply. The direct test had passed before that guard. This was a test implementation error, not an expected defect RED.
- Corrected the mutation source and added an explicit PASS log in \`176ad50d\`.

### Focused relay/output/poll-fault

- Exact source/test SHA: \`176ad50da2180ee085e2fb63ddb23d17b53dd63d\`
- Run [44300908495](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44300908495), job \`134790069730\`: **SUCCESS**.
- Both ESP8266 and ESP32 emitted \`POLL_FAULT_PRE_PERSISTENCE_OUTPUT_OFF_PASS\`.
- Both boards rejected \`defer-fault-output-inhibit\` with expected exit 23.
- Existing relay polarity, output-enable sequence, poll-window drain, pulse-capture, timeline and response-deny labs passed on this exact head.
- Logs retain \`SIMULATED_ONLY=1\`, \`PHYSICAL_RELAY_POLARITY_VERIFIED=0\`, \`PHYSICAL_COIN_ACCEPTOR_VERIFIED=0\`, and \`PHYSICAL_POWER_CUT_VERIFIED=0\`.

### Quarantine / dual-store / pending recovery

- Exact source/test SHA: \`176ad50da2180ee085e2fb63ddb23d17b53dd63d\`
- Run [44300908665](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44300908665), job \`134790070092\`: **SUCCESS**.
- ESP32 NVS read-error, type-mismatch and namespace-open failure remain deny.
- Ambiguous commit/reboot deny scenarios passed on both boards.
- ESP8266 and ESP32 quarantine helpers passed 36/36 per board; pending marker 28/28 per board; mount 8/8 per board; pending journal 16/16; pending clear 17/17; pending write/readback 22/22; coin POST gate 10/10; poll-window drain 11/11; pulse capture 8/8; the new pre-persistence output-inhibit lab passed on both boards.
- These are source-extracted host simulations, not flash-physics or power-cut evidence.

### Full BlazePwifi workflow

- Exact PR head: \`176ad50da2180ee085e2fb63ddb23d17b53dd63d\`
- Run [44300908564](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44300908564): **FAILURE** at validation job \`134790228692\`, step \`Controller protocol parity\`.
- Exact validation error: \`Missing poll signature check\` in the ESP8266 sketch.
- All 13 firmware target jobs and Android completed SUCCESS. Downstream simulations, update bundle, candidate gate, signing and publishing were skipped after validation failed.
- This is not a full candidate acceptance. Do not restore unsigned positive poll admission to satisfy the stale assertion.

## Ownership / blockers

- PHX-HARDWARE owns the two firmware sketches and this hardware-local lab/workflow.
- PHX-QA owns the stale controller-protocol parity assertion and independent review.
- PHX-CORE owns the canonical authenticated poll/receipt envelope and golden vectors.
- PHX-MASTER owns stack selection, global assignment and integration order.
- No shared API, financial schema, QA-owned file, CORE ledger, Release signing path or COE destination was changed.

**Release status:** focused hardware-source labs **CI VERIFIED / SIMULATED**; full validation **FAILED**; physical relay, pulse, electrical recovery, 150 power cuts, 30-device/24-hour soak, protected independent witness, durable accounting/replay and reversible v1→v2 migration **NOT TESTED / BLOCKED**. Production remains **NO-GO**.

## Next exact action

PHX-QA must replace the stale positive \`response_sig\` / poll-string assertion with source-linked negative deny-behavior tests, without changing the firmware's hard-deny contract. PHX-MASTER then confirms the #322 → #323 review candidate stack. Keep #323 DRAFT/UNMERGED and leave #321/#324 separate until that decision is recorded.
