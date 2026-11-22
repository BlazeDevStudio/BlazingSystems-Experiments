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
