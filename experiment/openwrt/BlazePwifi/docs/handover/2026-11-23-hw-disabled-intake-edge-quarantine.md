# PHX-HARDWARE — disabled-intake coin edge quarantine

**Checkpoint:** 2026-11-23 UTC23  
**Disposition:** focused Quarantine + Relay CI VERIFIED at exact source/test head; Full integration FAILED at inherited QA-owned poll-signature assertion; SIMULATED ONLY; HARDWARE ACCEPTED NO; PRODUCTION NO-GO.

## Exact refs

- Repository: `BlazeDevStudio/BlazingSystems-Experiments` (repository ID `1389289885`).
- Child PR: [#345](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/345), OPEN / DRAFT / UNMERGED.
- Branch: `phoenix/hw-coin-intake-armed-gate-20261122-utc23`.
- Base/parent: PR #343, branch `phoenix/hw-esp8266-pin-recovery-20261122-utc16`, exact parent HEAD `dfeff7d5f63e699de7bc296c7641f2493f1e0e13`.
- Test-only RED commit: `834738d2e82b6857779935b988c4046cbcb6c89f`.
- ESP8266 source correction: `911543b8c09044944803d3cee09ddc062b1c191a`.
- ESP32 source correction: `ccf2ed3b45d8b1b3b7d634ba4f1c32a054b23863`.
- Six-scenario test expansion: `af8709b96b92f9532ebc4f19e5a7d4f32cced9ed`.
- Test-order correction: `587f82b80d546a5b6c027e33ede9caa7fef24ba7` (exact source/test SHA).

## Proven defect and correction

Both sketches previously allowed `sampleCoinPulseEdge()` to append a pending pulse when the controller, coin feature or acceptor relay was configured OFF. `applyOutputs()` correctly kept the relay output OFF, but the sample path did not include the same configuration gate.

Both ESP8266 and ESP32 now compute:

```cpp
const bool coinIngressConfigured =
    controllerEnabled && coinEnabled && relayEnabled;
```

The predicate is included in the single-edge eligibility check. A sampled active edge while any of those configuration gates is OFF now latches the existing sticky poll-fault path, deasserts outputs before persistence, preserves any pre-existing pending identity, and requires operator reconciliation. No new coin credit is created.

The comment explicitly distinguishes configured relay disable from temporary poll-time relay suspension: `relayEnabled` remains true while `pollIntakeSuspended` temporarily turns the physical output off, so the existing synchronous-poll pulse-reconciliation behavior is retained.

## Test-first and failure-injection evidence

### Expected RED

- Test-only commit `834738d2e82b6857779935b988c4046cbcb6c89f`.
- Quarantine run [#45083252631](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45083252631), job `137395949187`: expected failure, ESP8266 exact-source exit 60 because the relay-disabled edge was accepted by the old source path.

### Intermediate harness-order failure and correction

- First source/test attempt at `af8709b96b92f9532ebc4f19e5a7d4f32cced9ed`: Quarantine [#45084726332](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45084726332), job `137400631162`. All six new disabled-ingress scenarios passed for both boards, but the early placement caused the existing `remove-fault-marker-write` mutation to fail at the new earlier assertion (exit 60 instead of its expected exit 12).
- The fixture-only follow-up moved the six new assertions after the existing mutation checks. No production logic was changed by that test-order correction.

### Final exact-source GREEN

- Exact source/test SHA: `587f82b80d546a5b6c027e33ede9caa7fef24ba7`.
- Quarantine [#45084968734](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45084968734), job `137401392690`: **SUCCESS**.
- Six disabled-ingress cases passed on each extracted sketch: controller OFF, coin OFF and relay OFF, each tested with and without an ISR sequence. Every case verifies sticky `/pollpulse.fault`, no new pending pulse, no save, outputs OFF, insert mode OFF and target cleared.
- Logs: `POLL_EDGE_WHILE_RELAY_DISABLED_DENY_PASS`, `POLL_ISR_EDGE_WHILE_RELAY_DISABLED_DENY_PASS`, `POLL_EDGE_WHILE_COIN_DISABLED_DENY_PASS`, `POLL_ISR_EDGE_WHILE_COIN_DISABLED_DENY_PASS`, `POLL_EDGE_WHILE_CONTROLLER_DISABLED_DENY_PASS`, `POLL_ISR_EDGE_WHILE_CONTROLLER_DISABLED_DENY_PASS`.
- Board parity: `POLL_SAFETY_BOARD_PARITY_PASS 17/17 normalized helpers`; existing poll-loop, journal, NVS/EEPROM, pending-clear, POST-gate and pulse-capture regressions also passed.

### Relay/output verification

- Relay [#45084968714](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45084968714):
  - job `137401392090` source-output-polarity: SUCCESS;
  - job `137401392489` ESP32 boot-polarity: SUCCESS.
- Existing pulse-capture suite passed 17/17 per board with fail-open mutations rejected. Explicit logs remain `SIMULATED_ONLY=1`, `PHYSICAL_COIN_PULSE_ACCEPTANCE=0`, `PHYSICAL_RELAY_ACCEPTANCE=0`, and `PHYSICAL_POWER_CUT_ACCEPTANCE=0`.

### Full integration

- Full [#45084968764](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45084968764), exact source/test SHA `587f82b80d546a5b6c027e33ede9caa7fef24ba7`.
- Validation job `137401435383`: **FAILURE** at the inherited QA-owned `Missing poll signature check` in the ESP8266 sketch. No signature was fabricated and no controller/coin admission gate was weakened.
- All 13 configured firmware target jobs completed SUCCESS (ESP8266, ESP32, x86_64, Ruijie and configured Orange Pi targets). Android was still in progress at this handover checkpoint.
- Downstream simulations, update bundle, candidate gate, signing handoff and publication were skipped after validation failure.

## Ownership and safety

Changed paths are limited to the two PHX-HARDWARE-owned ESP sketches, the Hardware-owned host scenario fixture, and this narrow Hardware handover. No QA-owned tests, shared API, register/poll producer, finance backend, ledger, migration, signer, witness, Release workflow or COE destination was changed.

No flashing, physical device, live coin, live money, production migration, signing, merge, release tag, deployment or cutover occurred.

## Remaining blockers / next exact actions

1. PHX-QA owns the stale positive poll-signature assertion. Reconcile it against the current deny-only register/poll producer and independent negative tests; do not ask Hardware to invent `response_sig`.
2. PHX-CORE owns the authenticated register/poll/configuration and event-bound receipt contract. Keep coin POST/admission default-deny until that contract and independent QA vectors exist.
3. PHX-MASTER should refresh `ROLE_ASSIGNMENTS.md` and `INTEGRATION_MATRIX.md` to record #343 → #345 as a separate Hardware child lineage, without collapsing it into #338 → #344 or other open stacks.
4. Preserve #239 (Phase A deny), #254 (ControllerAuthV1Lab) and #283 (both sketches) as independent OPEN / DRAFT / UNMERGED branches; revalidate their heads before any future integration.
5. Physical acceptance remains NOT TESTED: 150 noncustomer power cuts, 30-device/24-hour soak, electrical pulse/recovery, protected anti-rollback witness, durable accounting/replay, v1→v2 migration and independent release signoff remain outstanding.

## 2026-11-23 UTC00 follow-up — preserve an already-pending event identity

This follow-up changes only the Hardware-owned source-extraction lab. The ESP8266/ESP32 production sketch blobs are unchanged from the configured-intake correction above.

### Added source-exact cases

The new runDisabledIngressPendingCase() seeds an existing pending batch (pendingPulses=2, target and nonce populated, pendingReady=false) before a later sampled edge is observed with one configured gate OFF. It exercises all three gates (controller, coin feature, acceptor relay), with and without an ISR sequence: **6 cases per board**.

Each case requires:
- the existing pending pulse count remains 2 and the target/nonce identity remains unchanged;
- pendingReady is raised for operator reconciliation;
- no POST attempt or pending save is created;
- the sticky /pollpulse.fault marker records the unresolved total (pulses=3);
- relay/LED stay OFF, insertion mode is OFF, and active target is cleared.

Two negative controls prove the new checks are sensitive:
- removing the pendingReady preservation assignment is rejected with expected exit 66;
- clearing pendingTarget and pendingNonce in the fault helper is rejected with expected exit 66.

### Intermediate harness failure and correction

- Intermediate test commit 8cf3f8317230138e33c34c781846faeb1aa185fd had a Python triple-quote delimiter error in the new fixture constant. Quarantine [#45090746935](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45090746935), job 137419485846, and Relay [#45090746965](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45090746965), job 137419960068, failed at fixture import. This was a test-harness defect, not a firmware result.
- Correction commit 6eb3e9ba82fdbdcfe4fb6dc8ab1c38c9ffdc3043 removed the duplicate delimiter. The exact-head jobs below compile and execute the expanded fixture.

### Final exact-source/test evidence

- Exact source/test SHA: 6eb3e9ba82fdbdcfe4fb6dc8ab1c38c9ffdc3043.
- Quarantine [#45090899038](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45090899038), job 137419959248: **SUCCESS**. Both boards report all six pending-identity cases PASS, POLL_DISABLED_INGRESS_PENDING_IDENTITY_PRESERVATION_PASS 6/6, and both mutations rejected.
- Relay [#45090899225](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45090899225): job 137419960068 source-output-polarity **SUCCESS**; job 137419960333 ESP32 boot-polarity **SUCCESS**.
- Full [#45090899167](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45090899167), PR merge commit 98e86dfadbba7f5478aba7b6f66a5fd0f8c51847: validation job 137420042013 **FAILURE** at the inherited QA-owned Missing poll signature check. All 14 target/platform jobs (ESP8266, ESP32, Android, x86_64, Ruijie and configured Orange Pi targets) completed **SUCCESS**. Downstream simulations, update bundle, candidate, signing and publication were skipped after validation failed.

All logs continue to declare SIMULATED_ONLY=1, physical coin/relay/power-cut acceptance = 0. These tests establish host-lab behavior only; they do not establish durable storage across real power loss or physical hardware acceptance.

## Follow-up ownership boundary

The follow-up adds only the Hardware-owned runner, fixture-export module, scenario fixture, and this handover. It does not edit QA-owned tests/controllers.sh, the register/poll producer, shared API, finance backend, ledger, migration, signer, witness, Release workflow or COE destination. Keep the stale poll-signature assertion with PHX-QA and do not synthesize a response_sig.


## PHX-HARDWARE UTC01 — multi-edge disabled-intake pending identity coverage

**Scope:** one bounded Hardware-owned cleanup/test increment on the existing #345 draft. No shared API, CORE ledger, QA-owned test, Release workflow, or production admission behavior was changed.

### Exact source/test head before this handover update

- Branch: \`phoenix/hw-coin-intake-armed-gate-20261122-utc23\`
- Source/test HEAD: \`40d8a705d2519e9bcbb2576b00facb2bd456cd01\`
- PR #345: OPEN / DRAFT / UNMERGED; parent #343 remains separate.
- ESP8266 source commit: \`66c88d1f3d107b01a1f6939b7160854a4f839dbd\`
- ESP32 source commit: \`97be7d5bec7328ea9e6d3b257d9b559a964d5825\`
- Scenario fixture commit: \`966107c1b4062d3b58b5d28d6e8e3833c1473f02\`
- Runner mutation commit: \`3489a17d090a420e8a0ccedabda13b79da0cf11c\`
- Baseline-runner correction: \`40d8a705d2519e9bcbb2576b00facb2bd456cd01\`

### Change

Both sketches now name the existing single-edge condition as \`exactlyOneUnseenEdge\`. This is a behavior-preserving readability change: an ISR delta other than exactly one is never collapsed into one credit-eligible sampled edge.

The source-extracted pending-identity matrix now runs as a green baseline on the unmutated source, in addition to its mutation runs. Three additional scenarios cover:

- relay disabled, three unseen ISR edges across \`uint32_t\` rollover (\`0xFFFFFFFE + 3 -> 1\`);
- coin disabled, two unseen ISR edges;
- controller disabled, four unseen ISR edges.

Each scenario starts with an existing two-pulse pending batch and asserts that pulse count, target, nonce and pending identity are preserved; \`pendingReady\` is raised for reconciliation; no save or POST is attempted; the sticky fault marker records the exact aggregate edge count; and relay/LED/coin admission remain OFF.

A failure-injection mutation that collapses \`pendingPulses + unseenEdges\` to \`pendingPulses + 1\` is rejected on both boards.

### Exact-source CI evidence

- Quarantine [run #45097138177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45097138177), job \`137439344434\`: SUCCESS. The unmutated matrix reports 9/9 per board; the pending-ready, identity-clear and multi-edge-count mutations are rejected. The existing dual-store fault lab also passes while explicitly reproducing the known BOTH-STORES-FAILED reboot-durability limitation.
- Relay [run #45097138288](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45097138288), jobs \`137439345032\` and \`137439345194\`: SUCCESS. Output polarity suite 48/48 per board; normalized poll safety parity 17/17; pending identity matrix 9/9 per board and the three mutations are rejected.
- Full [run #45097138225](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45097138225), validation job \`137439345378\`: FAILURE at the inherited QA-owned \`Missing poll signature check\`. All 14 configured firmware target jobs completed SUCCESS; Android was still running when this handover was written. Downstream simulations, bundle, candidate, signing and publication were skipped.

The earlier run on the intermediate \`3489a17\` head is not used as 9/9 baseline evidence: inspection showed the focused matrix was only exercised under mutation. The runner correction at \`40d8a705\` now executes the unmutated 9/9 matrix first; the successful Quarantine and Relay runs above verify that correction.

### Remaining boundaries

- CI classification: **CI VERIFIED / SIMULATED ONLY**.
- Physical relay, coin pulse, electrical recovery and power-cut acceptance: **NOT TESTED**.
- The dual-store lab still reproduces that if both LittleFS and the secondary EEPROM/NVS fault stores fail before persistence, only the current-boot RAM latch remains. No protected independent witness is established.
- Full integration remains blocked by the stale positive poll-signature assertion. The current main register/poll producer still does not provide the required \`response_sig\`; Hardware will not invent a producer or weaken QA validation.
- PR #254 remains stacked on #239 and separately fails the ESP32 Mbed TLS 4 application build; do not transplant the #327/#340 PSA candidate until Master selects canonical ancestry and Release confirms the supported toolchain.
- PR #283 remains a separate parallel branch. Its quarantine helper is definition-only on the checked head; no production callsite or authenticated poll response contract is claimed.

**Next exact action:** PHX-QA / PHX-CORE to reconcile the positive poll-signature assertion against the live producer/consumer contract, and PHX-MASTER to refresh role/stack pins before any cross-branch integration. No merge, flash, device reset, money, migration, signer provisioning or release action.


## PHX-HARDWARE UTC02 — restore configured-output mutation sensitivity

**Task:** one bounded Hardware-owned test-integrity correction on the existing #345 child. No production firmware sketch, shared API, CORE ledger, QA-owned controller assertion, Release workflow, or COE destination was changed.

### Defect reproduced

The pending-identity scenario checked relay/LED outputs only *after* `sampleCoinPulseEdge()`. That call enters the fault path and calls `applyOutputs()` again, so it could hide a transient ready-LED assertion caused by removing `relayEnabled` from the initial `accepting` predicate. The physical relay still had a separate `if(relayEnabled)` write guard, but the test did not prove the ready indicator was denied before fault handling.

- At head `6a00cf5e2f5967fc3b38c594b64cb6f36c2cfd58`, the relay-output mutation survived: Quarantine [#45100297925](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45100297925), job `137449361363`, and Relay [#45100297964](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45100297964), job `137449361476`, both failed because the mutation returned 0 instead of expected exit 80.
- First correction at `90231e157a8b0f2d3dd3d0548ea01abef78aa5c8` added the pre-sample output assertion, correctly detected the mutation, but reused pending-case exit 66. Relay [#45101370466](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45101370466), job `137452740438`, failed expected 80 / got 66. This was a harness exit-code collision, not a firmware failure.

### Final correction and exact-source evidence

Source/test SHA: `6f1dc79b6d8f263655a0a385eb162d31972d3700`.

The scenario fixture now checks relay and LED are OFF immediately after applying each disabled configuration and before any sampled edge or fault handler can mask the initial output state. The same assertion is present in single-edge pending-identity and multi-edge/rollover scenarios. Output-interlock mutation failures use a distinct `failureCode + 14` exit range; the relay-disabled first case therefore rejects with exit 80 without colliding with the 66–74 pending-identity checks.

- Quarantine [#45101510839](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45101510839), job `137453194883`: **SUCCESS**. Both boards pass the 6/6 and 9/9 pending-identity matrices; pending-ready, identity-clear, edge-delta and relay-output-gate mutations are rejected. The new relay-output-gate mutation reports expected exit 80 on ESP8266 and ESP32.
- Relay [#45101510916](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45101510916): source-output-polarity job `137453195996` **SUCCESS**; ESP32 boot-polarity job `137453195381` **SUCCESS**. Output polarity passes 48/48 scenarios per board; pending-identity matrices pass 6/6 and 9/9 per board; the relay-output-gate mutation is rejected with exit 80 on both boards.
- Quarantine also reports pending write/readback 22/22, normalized poll-safety parity 17/17, and the existing dual-store fault lab. That lab still explicitly reproduces the current-boot-only limitation when both persistence stores fail; it does not establish an independent durable witness.

### Full integration and boundaries

Full build run [#45101505306](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45101505306), validation job `137453264998`, **FAILS** at inherited QA-owned Controller protocol parity: `Missing poll signature check` in the ESP8266 sketch. All 14/14 configured target/platform jobs, including Android, completed SUCCESS on this exact source/test SHA. The validation failure skips downstream simulations, bundle, candidate, signing and publication. The same source/test SHA is `6f1dc79b6d8f263655a0a385eb162d31972d3700`.

All focused logs remain `SIMULATED_ONLY=1`; physical coin acceptor, relay voltage, power-cut and electrical recovery acceptance remain **NOT TESTED**. No physical flash, device reset, live money, migration, signer provisioning, merge or release occurred.

**Next exact action:** PHX-QA / PHX-CORE resolve the authenticated register/poll contract and replace the stale positive signature assertion with source-linked negative/default-deny checks; PHX-MASTER refreshes #345's role/integration pin. Hardware keeps coin admission fail-closed.


### Documentation-head revalidation (before this handover-only commit)

The source/test SHA remains `6f1dc79b6d8f263655a0a385eb162d31972d3700`; the previous documentation head was `44685c183914cec840a0b7df09c74918126888bb`.

- Quarantine [#45101895552](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45101895552), job `137454414127`: **SUCCESS**.
- Relay [#45101895612](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45101895612): source-output-polarity job `137454414907` and ESP32 boot-polarity job `137454414681`: **SUCCESS**.
- Full build [#45101889654](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45101889654), validation job `137454395798`: **FAILURE** at the inherited QA-owned `Missing poll signature check`. All 14/14 configured target/platform jobs (including Android, ESP32 and ESP8266) completed **SUCCESS**; 12 downstream simulation/bundle/candidate/signing/publication jobs were skipped.
- This update changes only this handover. Firmware/test source remains at `6f1dc79b6d8f263655a0a385eb162d31972d3700`; the PR documentation head advances with this commit.



### UTC03 pending-journal byte-preservation regression

Exact source/test SHA: `e95b1109141f8c3377aff055946c3fdd78965c73`. This increment is a host-lab test-integrity correction only; no production sketch or shared API changed.

The disabled-intake pending-identity scenarios now seed an **opaque** fake LittleFS `/pending.dat` byte fixture and compare it byte-for-byte after `sampleCoinPulseEdge()` latches the fault. The handover and fixture explicitly state that this lab does not parse or validate the production `PendingRecord` serialization. Both the single-edge and multi-edge/uint32-rollover cases assert that the sentinel remains present and unchanged.

The runner adds a negative mutation that deletes `/pending.dat` inside the extracted `latchPollPulseFault()`; the pending-identity suite must reject it on both board builds.

- Quarantine [#45107477749](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45107477749), job `137471956271`: **SUCCESS**. ESP8266 and ESP32 each pass pending identity 6/6 and 9/9; the new pending-journal deletion mutation is rejected with expected exit 66 on both boards. Existing pending-edge-delta and configured relay-output mutations are also rejected (72 and 80).
- Relay [#45107477959](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45107477959): source-output-polarity job `137471957188` and ESP32 boot-polarity job `137471957356`: **SUCCESS**; active-high/active-low source scenarios 48/48 per board.
- Full build [#45107477751](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45107477751): validation job `137471957500` **FAILURE** at inherited QA-owned `Missing poll signature check` in `tests/controllers.sh`. All 14/14 target/platform jobs completed **SUCCESS**; downstream simulation, bundle, candidate, signing and publication jobs were skipped.

This proves only byte-preservation behavior in the fake LittleFS host fixture. It does **not** prove actual filesystem durability, reboot recovery, physical coin/relay behavior, power-cut recovery or an independent witness. `SIMULATED_ONLY=1`; physical acceptance remains **NOT TESTED**.

**Next exact action:** PHX-QA and PHX-CORE reconcile the stale positive poll-signature assertion against the current main `register|ping` and `poll` producers; Hardware keeps coin admission default-deny until an approved authenticated response/event contract exists.


## 2026-11-23 UTC04 follow-up — preserve all pending recovery evidence

**Task:** one bounded PHX-HARDWARE test-integrity improvement on the existing #345 child. The production ESP8266/ESP32 sketches and shared APIs were not changed.

### Exact source/test change

**Source/test commit:** b1a5a36627075581973b451934eed000e43b4038.

The previous opaque fake LittleFS fixture preserved only /pending.dat. That did not independently guard the other recovery artifacts or the durable POST-attempt marker. The host lab now adds a separate already-attempted pending-event scenario that seeds opaque bytes at:

- /pending.dat
- /pending.new
- /pending.bak
- /pending.attempt

For each configured gate (controller OFF, coin feature OFF, acceptor relay OFF), with and without a simulated ISR edge, the new 6/6-per-board matrix verifies that pending RAM identity, pendingPostAttempted, and every seeded file's exact bytes survive the disabled-intake fault. It also checks no save/POST path is entered, the sticky fault marker records three unresolved pulses, and outputs remain OFF.

The runner builds a separate ATTEMPTED_EVIDENCE_MAIN so each injected deletion is caught by the intended new scenario rather than an earlier legacy pending-identity assertion. It injects deletion of each of the four paths and clearing of pendingPostAttempted; every mutation must exit 82 on both boards.

**Fixture boundary:** all four files are deliberately opaque sentinels, seeded together to model ambiguous recovery evidence. This test does not parse PendingRecord, validate a production journal layout, choose a recovery candidate, or prove actual LittleFS durability. It proves only that this extracted fault path does not erase or rewrite the supplied evidence in the host fixture.

### Test-first correction history

- Initial implementation commit cc3db78dc9182c7b5f3d83b89c4ac1ad5d679aa6 ran the deletion mutations through the combined legacy/new main. The /pending.dat deletion was detected earlier by the legacy test (exit 66) before the new scenario's expected exit 82. Quarantine [#45113942257](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45113942257) and Relay [#45113942311](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45113942311) therefore failed at the harness sequencing/exit expectation; this was not a production firmware failure.
- Correction commit b1a5a36627075581973b451934eed000e43b4038 isolates the attempted-evidence main and runs it as an independent unmutated baseline before the deletion mutations.

### Exact-head CI evidence — source/test SHA b1a5a36627075581973b451934eed000e43b4038

- Quarantine [run #45114100708](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45114100708), job 137492844603: **SUCCESS**. ESP8266 and ESP32 each pass the existing pending-identity matrices (6/6 and 9/9) and new attempted-evidence matrix (6/6). All four file-deletion mutations and the attempt-state mutation are rejected on both boards with expected exit 82. Normalized poll-safety helper parity remains 17/17.
- Relay [run #45114100704](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45114100704): source-output-polarity job 137492844339 **SUCCESS**; ESP32 boot-polarity job 137492844764 **SUCCESS**. Existing active-high/active-low output scenarios remain 48/48 per board; poll-window, edge-capture and output-interlock mutations are rejected.
- Full [run #45114100788](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45114100788): validation job 137492926791 **FAILURE** at the inherited QA-owned Missing poll signature check in the ESP8266 sketch. All 14/14 configured target/platform jobs completed **SUCCESS** (ESP8266, ESP32, Android, Ruijie and configured Orange Pi/x86 targets). Downstream simulations, update bundle, candidate gate, signing handoff and publication were skipped.

All focused output remains SIMULATED_ONLY=1; physical coin acceptor, relay polarity, electrical recovery and power-cut acceptance remain **NOT TESTED**. No hardware flashing, device reset, live coin/money, migration, signer provisioning, merge, release tag, deployment or cutover occurred.

### Coordination and next exact action

- PHX-CORE / PHX-QA: publish and independently validate the authenticated register/poll and event-bound receipt contract; do not invent response_sig or relax default-deny.
- PHX-MASTER: current control-plane body identifies #345 as the Hardware child, while the current ROLE_ASSIGNMENTS.md snapshot in #288 still names #327. Reconcile those pointers in Master-owned files; Hardware did not edit them.
- Registry: private BLAZE_PROJECT_REGISTRY_v11_20261027.json was not available in the connected file surface, and no Google Drive connector action was exposed. No older registry snapshot was substituted.
- PHX-HARDWARE: retain #345 OPEN / DRAFT / UNMERGED and continue only after revalidating all stacked branch heads.

**Classification:** host fixture SIMULATED; exact-head Quarantine and Relay CI VERIFIED; Full integration FAILED at the shared contract assertion; HARDWARE ACCEPTED NO; PRODUCTION NO-GO.


## PHX-HARDWARE UTC05 — source-exact pending-journal reclamation failure injection

**Task:** one bounded Hardware-owned test modularization / preservation increment on the existing #345 draft. No production sketch, shared API, CORE ledger, QA-owned test, Release workflow, or COE destination changed.

### Exact source/test commit

- Commit: `0cde88296855515c06b7650a71b190167834fcc5`.
- Branch: `phoenix/hw-coin-intake-armed-gate-20261122-utc23`.
- Parent: previous PR #345 HEAD `4c4653e5fab28170fcf05c490a873a2ae73e4a1d`.
- PR #345 remains OPEN / DRAFT / UNMERGED, based on #343 at `dfeff7d5f63e699de7bc296c7641f2493f1e0e13`.

### Change

The existing poll-loop host lab already checked board parity for `clearPending()`, but did not execute that exact helper through deletion-failure paths. The runner now extracts `clearPending()` unchanged from each ESP8266/ESP32 sketch and invokes a dedicated module:

`experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/pending_clear_failure_lab.py`

The isolated fake filesystem exercises three fail-closed cases plus a successful control:

1. Pending-journal removal fails: both journal and attempt marker remain; RAM identity is retained and recovery is latched.
2. Attempt-marker removal fails after the pending journal is removed: the attempt marker remains as an orphan boot-deny witness; RAM identity is retained and recovery is latched.
3. Remove reports success but readback still finds the pending file: reclamation is rejected and recovery is latched.
4. Successful control: both files are removed and the pending RAM identity is cleared.

A failure-injection mutation that ignores the attempt-marker removal result must be rejected with expected exit 91 on both board builds.

**Fixture boundary:** this compiles the exact `clearPending()` body, but stubs `readPendingFile()`, `pendingAttemptMarkerMatches()`, and the filesystem. It tests the deletion sequence and fail-closed state transitions only. It does not parse the production record, emulate LittleFS wear/metadata semantics, prove reboot recovery, or establish power-cut durability.

### Exact-head CI evidence — source/test SHA `0cde88296855515c06b7650a71b190167834fcc5`

- Quarantine [#45117528160](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45117528160), job `137503661431`: **SUCCESS**. ESP8266 and ESP32 baseline cases passed; the attempt-marker deletion-failure mutation was rejected on both boards with expected exit 91. Existing poll-edge/rollover, pending identity 6/6 and 9/9, attempted-evidence 6/6, relay output gate, NVS/EEPROM and request-digest failure-injection labs passed. Logs explicitly retain `SIMULATED_ONLY=1` and physical acceptance flags at 0.
- Relay [#45117528212](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45117528212): source-output-polarity job `137503661391` and ESP32 boot-polarity job `137503661937`: **SUCCESS**. Existing active-high/active-low output and poll-release interlock regressions passed.
- Full build [#45117528096](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45117528096), validation job `137503662135`: **FAILURE** at the inherited QA-owned `Controller protocol parity` / `Missing poll signature check` in the ESP8266 sketch. All 14 configured target/platform jobs completed **SUCCESS** (ESP8266, ESP32, Android, x86_64, Ruijie and configured Orange Pi targets). Downstream simulation, bundle, candidate, signing and publication jobs were skipped.

### Ownership / remaining blockers

- PHX-HARDWARE owns the ESP sketches and the host labs under the Hardware directories. No QA or CORE-owned source was changed.
- The Master `ROLE_ASSIGNMENTS.md` still lists #327 as the active Hardware child while the Control Plane references #345; Master must reconcile its own assignment/integration pointers. Hardware does not edit Master-owned coordination files.
- CORE/QA must publish and independently validate the authenticated register/poll and event-bound receipt contract. Do not synthesize `response_sig` or relax the default-deny consumer.
- Physical coin/relay/electrical acceptance, 150 power cuts, 30-device/24-hour soak, independent witness, protected signer, financial migration, durable accounting/replay and independent QA/release signoff remain outstanding.

**Classification:** source-exact host regression **SIMULATED**; Quarantine and Relay **CI VERIFIED**; Full integration **FAILED/BLOCKED**; **HARDWARE ACCEPTED NO; PRODUCTION NO-GO.**


## PHX-HARDWARE UTC05 follow-up — exact pending-clear identity and candidate guards

**Task:** extend the existing #345 pending-journal reclamation lab so it executes the production identity helpers unchanged and proves fail-closed behavior for unreadable, mismatched, changed, missing, and ambiguous evidence. This is a test-fidelity improvement, not a newly discovered production deletion defect.

### Source/test changes

- Final source/test SHA: `96aee3acbbbf9a55ad959ae022dd6a1baf642a5d`.
- Test expansion commit: `f7ca585b6d5292e702a0711c93420e58a0168ca7`.
- Follow-up harness escaping correction: `96aee3acbbbf9a55ad959ae022dd6a1baf642a5d`.
- Parent PR #345 HEAD before this increment: `7a4de0b8bfe207d199779a93204ff10f9e2e923a`.
- PR #345 remains OPEN / DRAFT / UNMERGED, based on #343 at `dfeff7d5f63e699de7bc296c7641f2493f1e0e13`.

The runner now extracts these exact production helpers from each board sketch and passes them to the dedicated lab:

- `clearPending()`
- `samePendingRecord()`
- `pendingAttemptMarkerMatches()`

The fake `readPendingFile()` adapter remains intentionally stubbed. It injects path-specific read failures, attempt-marker mismatch, a persisted-identity change between the initial match and the second read, and durable-record mismatch. The matrix also tests zero and multiple journal candidates. Opaque fake-file bytes and RAM identity must remain unchanged on every denied path.

**Negative controls:** four fail-open mutations are rejected on both ESP8266 and ESP32:
1. Ignore attempt-marker deletion failure — expected exit 91.
2. Skip the second attempt identity check — expected exit 96.
3. Ignore durable journal/attempt record equality — expected exit 97.
4. Ignore the exactly-one-candidate guard — expected exit 99.

The lab reports `PENDING_CLEAR_LAB_PASS 17/17` for each board. There was no separate expected-RED commit because the production guards already existed; the four source mutations prove the expanded tests detect their removal.

### Exact-source CI

- Quarantine [#45121211341](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45121211341), job `137515178556`: **SUCCESS**. Both ESP8266 and ESP32 source-extracted suites passed; the four new fail-open mutations were rejected on each board.
- Relay [#45121211439](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45121211439): jobs `137515179302` and `137515179545`: **SUCCESS**.
- Full [#45121211344](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45121211344), validation job `137515262590`: **FAILURE** at the inherited QA-owned `Controller protocol parity` assertion: `Missing poll signature check` in the ESP8266 sketch. All 14 configured target/platform jobs completed **SUCCESS**. Downstream simulation, update bundle, candidate, signing and publication stages were skipped.

### Scope and limitations

- Changed only the Hardware-owned host lab and its Hardware-owned runner.
- No production `.ino`, shared API, CORE financial code, QA-owned assertion, Release workflow, COE destination, signer, witness, migration, or accounting source changed.
- The fake reader does not parse serialized `PendingRecord` bytes or model LittleFS metadata/wear. No real flash, physical coin/relay, electrical pulse, power cut, or device was used.
- `SIMULATED_ONLY=1`; physical power-cut, coin-acceptor, and relay acceptance remain 0.

### Coordination and remaining blockers

- Live Master PR #288 head is `dab1f42b93c258d00054a754bd85698e3ae38b82`; its `ROLE_ASSIGNMENTS.md` still lists #327 as the active Hardware child. Master must refresh its own assignment and integration pointers to the live #345 branch; Hardware did not edit Master-owned files.
- Parallel drafts remain separate: #239 `d83b715b116185107737fef721c2eece8feebf39`, #254 `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`, and #283 `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`.
- CORE/QA must reconcile the actual register/poll producer with the authenticated response contract. Do not invent `response_sig` or relax the firmware default-deny consumer.
- The private Drive registry v11 remains unavailable through the connected file surface; no older registry snapshot was substituted.
- Physical acceptance, 150 power cuts, 30-device/24-hour soak, independent witness, protected signer, v1-to-v2 financial migration, durable accounting/replay, and independent QA/release signoff remain outstanding.

**Classification:** source-exact host lab SIMULATED; focused Quarantine/Relay CI VERIFIED; Full integration FAILED/BLOCKED; HARDWARE ACCEPTED NO; PRODUCTION NO-GO.


## PHX-HARDWARE UTC06 — post-clear ISR edge race regression

**Role:** PHX-HARDWARE  
**Repository:** \`BlazeDevStudio/BlazingSystems-Experiments\`  
**Branch:** \`phoenix/hw-coin-intake-armed-gate-20261122-utc23\`  
**Parent/base:** #343 at \`dfeff7d5f63e699de7bc296c7641f2493f1e0e13\`  
**Source/test commit:** \`edff098446247d3b2851af643d31673921cae03f\`  
**PR:** #345, OPEN / DRAFT / UNMERGED

### Change

Added a host regression for the narrow race where a coin ISR edge arrives while the pending event is being cleared after a simulated authenticated success response.

- \`poll_loop_blocking_inhibit_lab_runtime_fixtures.py\`: test-only \`clearPending()\` injects the extracted \`coinEdgeISR()\` during the clear window.
- \`poll_loop_blocking_inhibit_lab_scenario_fixtures.py\`: adds \`CLEAR_WINDOW_ISR_MAIN\`; verifies the new edge is reconciled after clear, \`journalRecoveryRequired\` is latched, the fake \`/pollpulse.fault\` record contains \`pulses=1\`, and relay/ready outputs remain OFF.
- \`poll_loop_blocking_inhibit_lab_fixtures.py\`: exports the new scenario.
- \`poll_loop_blocking_inhibit_lab.py\`: runs the scenario and a failure-injection mutation that removes the second post-clear \`reconcileUnobservedCoinEdges()\` check.

The test compiles the exact extracted production ISR, reconciliation, fault-latch, output, and response-handler functions for both boards. The positive disposition is a **test-only stub override**; production \`coinPostDispositionVerified()\` remains default-deny. No production \`.ino\`, shared API, financial ledger, QA-owned file, COE destination, or release workflow was changed.

### Exact CI evidence at source/test SHA

- Quarantine [#45124661252](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45124661252), job \`137526132962\`: SUCCESS.
  - ESP8266 and ESP32 both emitted \`COIN_POST_CLEAR_WINDOW_ISR_EDGE_LATCHED_PASS\`.
  - Both rejected \`coin-post-clear-window-isr-recheck\` mutation with expected exit 54.
  - Existing pending-clear lab: 17/17 source-extracted cases per board.
  - Existing poll blocked-edge fault suite: 8/8 scenarios.
- Relay [#45124661167](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45124661167): SUCCESS; jobs \`137526132969\` and \`137526133163\` both PASS.
- Full build/integration [#45124661259](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45124661259): FAILURE at validation job \`137526133628\`, exact message \`Missing poll signature check\` in the ESP8266 sketch. All 14/14 configured target/platform jobs (13 firmware targets plus Android) PASS. Downstream simulation, candidate, signing and publication stages were skipped.

### Limits and blockers

This is host SIMULATED / CI VERIFIED evidence only. It does not prove physical coin timing, LittleFS persistence, electrical pulse recovery, power-cut durability, or hardware acceptance. The response-signature contract remains a CORE/QA dependency; no positive coin disposition is enabled. Master #288 must refresh the active Hardware role pointer: the current \`ROLE_ASSIGNMENTS.md\` still points to #327 while the current integration matrix records #345.

**Next action:** PHX-QA independently review the clear-window race fixture; PHX-CORE publish the canonical authenticated poll/receipt contract; PHX-MASTER reconcile the #327/#345 assignment pointer. Hardware will continue only on a separate unblocked firmware-preservation task.
