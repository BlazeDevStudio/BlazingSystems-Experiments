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

Full build run [#45101505306](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45101505306), validation job `137453264998`, **FAILS** at inherited QA-owned Controller protocol parity: `Missing poll signature check` in the ESP8266 sketch. At this checkpoint 13/14 target/platform jobs had succeeded; Android was still running. The validation failure skips downstream simulations, bundle, candidate, signing and publication. The same source/test SHA is `6f1dc79b6d8f263655a0a385eb162d31972d3700`.

All focused logs remain `SIMULATED_ONLY=1`; physical coin acceptor, relay voltage, power-cut and electrical recovery acceptance remain **NOT TESTED**. No physical flash, device reset, live money, migration, signer provisioning, merge or release occurred.

**Next exact action:** PHX-QA / PHX-CORE resolve the authenticated register/poll contract and replace the stale positive signature assertion with source-linked negative/default-deny checks; PHX-MASTER refreshes #345's role/integration pin. Hardware keeps coin admission fail-closed.
