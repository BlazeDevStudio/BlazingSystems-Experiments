# PHX-HARDWARE — poll-safety source-contract module extraction (2026-11-24 UTC15)

**Role:** PHX-HARDWARE  
**Task:** cleanup-first #266 / Hardware #177 / DRAFT #349  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hw-json-array-primitive-guard-20261124-utc00`  
**Parent:** #347 at `960184670379f01e20f0e7e8bc23b3e5eedacd3f`  
**Starting PR HEAD:** `a361adfa144eca54326a48403d336886689c9c37`  
**Source/test commit:** [`4d36d08b4da5be4e6eaedc558be6e9ef38971f5d`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/4d36d08b4da5be4e6eaedc558be6e9ef38971f5d)  
**Status:** cleanup committed; focused Relay/Quarantine CI verified; Full integration blocked by the inherited CORE/QA poll-signature assertion; physical hardware NOT TESTED; production NO-GO.

## Selected task and concrete source change

The 1,037-line `poll_loop_blocking_inhibit_lab.py` still combined loop orchestration with cross-board source-contract checks and fixture-builder mutation checks.

This increment moves that cohesive responsibility into the new `poll_loop_blocking_inhibit_lab_source_contracts.py`:

- ESP8266/ESP32 extraction and normalized parity checks for 19 poll-safety helpers.
- The persistent-fault output-gate mutation and eight controller/coin/pending/quarantine authority mutations.
- Active-low/active-high drain-abort fixture callsite checks, including comment, string and inactive-`#if 0` decoy rejection.
- Explicit dependencies (`boards`, `extract_function`, and `main_fixture`) replace hidden runner globals.

The runner shrank from **1,037 to 871 lines** (166 lines removed); the new module is 179 lines including documentation and imports. The fixture logic was moved without changing its assertions or expected failure exits. The stable scenario/facade imports remain unchanged.

Relay workflow push and pull-request filters now watch the new source-contract module. Both Relay and Quarantine workflow filters watch this narrow handover so a docs-head refresh re-executes the focused evidence.

No production `.ino`, CGI producer, shared protocol, coin/relay actuation, financial ledger, signer, witness, migration, or COE destination source changed.

## Exact source/test-head CI — `4d36d08b4da5be4e6eaedc558be6e9ef38971f5d`

- Relay Output Polarity push [run #45423416694](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45423416694): **SUCCESS**.
  - ESP32 boot-polarity job `138548769179`: PASS.
  - Source/output-polarity job `138548770008`: PASS.
  - Logs show `POLL_SAFETY_BOARD_PARITY_PASS 19/19`, output-gate mutation rejection, all eight `POLL_COIN_AUTHORITY_PARITY_MUTATION_REJECTED` cases, and active-low/active-high drain-abort builder decoy rejection 2/2.
- Quarantine Byte Readback push [run #45423416609](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45423416609): **SUCCESS**.
  - Quarantine job `138548768715`: PASS.
  - Logs include both-board coin-pulse capture 17/17, EEPROM/config read-failure preservation, pending-journal recovery and poll-drain regression checks.
- Full BlazePwifi push [run #45423416573](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45423416573): **FAILURE**.
  - Validation job `138548773362` fails in `tests/controllers.sh` with the existing `Missing poll signature check` assertion against the ESP8266 sketch.
  - All 13 firmware target jobs and Android completed SUCCESS.
  - Browser/device simulations, update bundle, candidate, signing and publication stages were SKIPPED.
  - This is the CORE-owned register/poll producer contract versus QA-owned assertion mismatch. Hardware did not fabricate `response_sig`, alter the shared wire contract, or weaken default-deny.

**Local tests:** NOT RUN; no authenticated local checkout. GitHub Actions above are exact-source CI evidence and host/source-extracted simulations, not physical acceptance.

## Coordination and preserved boundaries

- PR #349 remains OPEN / DRAFT / UNMERGED, stacked on #347. No rebase, retarget, merge or force-push.
- Protected #239 Phase-A deny, #254 ControllerAuthV1Lab and parallel #283 remain OPEN / DRAFT / UNMERGED and untouched.
- #177 remains P0: the poll-inhibit/quiet-drain mitigation exists only in the unmerged Hardware stack; this cleanup does not close the issue or establish physical pulse acceptance.
- CORE owns the authenticated register/poll producer contract and canonical vectors; QA owns independent assertion reconciliation; MASTER owns global assignment and integration pins.
- Cleanup #266 remains OPEN / 0-of-7; this is one Hardware-owned contribution, not completion of the seven-role gate.
- Physical relay/coin/electrical acceptance, 150 controlled power cuts, 30-device 24-hour soak, protected anti-rollback witness, durable accounting/replay, reversible v1-to-v2 financial migration and independent release signoff remain NOT TESTED / NOT ACCEPTED.

## Next exact action

PHX-CORE publishes the approved versioned register/poll envelope and golden vectors; PHX-QA reconciles its assertion independently without weakening default-deny. PHX-HARDWARE then reruns Full on that approved contract SHA. Keep #349 DRAFT and unmerged until Master/QA review and owner authorization.
