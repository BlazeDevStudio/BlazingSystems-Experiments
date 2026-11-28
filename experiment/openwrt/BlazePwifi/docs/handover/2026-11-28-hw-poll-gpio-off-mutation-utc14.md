# PHX-HARDWARE UTC14 — immediate GPIO-off mutation regression

**Issue:** [#177](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/177)  
**Cleanup gate:** [#266](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/266)  
**Draft PR:** [#375](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/375) — OPEN / DRAFT / UNMERGED, child of #366  
**Branch:** `phoenix/hw-poll-deny-wrapper-20261128-utc13`  
**Source/test commit:** `227658bc09fa1ab5ff9140c0b920ecc95cc7422d`  
**Exact tested code + docs head:** `d6bd3737e60b49a7f4cec12226396ff60e83b9f6`

## Scope and implementation

The Hardware-owned host test now mutates the source-extracted `denyRemoteControl()` by removing its `applyOutputs();` call. It then compiles/runs the actual deny function and the extracted blocking-poll sequence against the GPIO model.

The mutation must fail because logical flags becoming false do not physically de-energize the relay unless the GPIO write occurs before the synchronous 3,500 ms poll. Both ESP8266 and ESP32 reject this mutation with exit 23 and emit `PREPOLL_GPIO_OFF_WRITE_MUTATION_REJECTED`.

No production sketch, CORE API, QA-owned test, finance, migration, signer/witness, COE destination or release workflow was changed in this incremental task.

## Exact-head evidence

| Workflow | Exact run/job | Result |
|---|---|---|
| Poll push | [#46153921703](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46153921703), `141006279696` | PASS |
| Poll PR | [#46153917558](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46153917558), `141006267901` | PASS |
| Mbed push | [#46153921753](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46153921753) | 3/3 PASS |
| Mbed PR | [#46153917594](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46153917594) | 3/3 PASS |
| Native | [#46153921746](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46153921746), `141006279859` | FAIL — QA PAY-0745 corrupt-state assertion |
| Full push | [#46153917616](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46153917616), `141006320757` | FAIL — QA controller parity; handover gate PASS; 14/14 target builds PASS |
| Full PR | [#46153921719](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46153921719), `141006484294` | FAIL — same controller parity; 14/14 target builds PASS |

Native failure: `BlazePwifiVendo.ino: corrupt persisted state must halt startup` in QA-owned `tests/v060_vendo_sequence_contract.py`.

Full failure: QA-owned `tests/controllers.sh:21` requires `config_revision` in both sketches. Hardware did not insert a decoy token or weaken the deny boundary. Update bundle, simulations, production signing and publishing were skipped.

## Parent/ownership collision

Master head `42dc13a7b732ff56152ec2170f2c61904b3dc67f` identifies #375 (child #366) and #374 (child #373) as separate stacks with seven overlapping paths. Master requires canonical-parent selection and append-only handover reconciliation before integration. Current Master role/integration pins still reference #375 head `224bea1`, while actual #375 head is `d6bd3737`.

Further overlapping sketch/workflow edits are paused pending Master sequencing. QA owns the PAY-0745 and controller-parity assertions; CORE owns the authenticated register/poll/receipt/disposition contract.

## Safety and acceptance

The active v0.6 branch remains `2fbd2475e9f54878c316fa7cea2f228386b0e859` and still consumes poll response fields before coin sampling. This PR is an unmerged deny-only candidate stack, not an active-branch fix.

Host simulation / CI verified only. Physical acceptor reject/inhibit, relay terminal polarity, pulse retention, electrical recovery, EEPROM/NVS brown-out, 150 power cuts and 30-device/24-hour soak remain NOT TESTED. Protected signer/witness, v1→v2 migration, durable accounting/replay and independent QA/release signoff remain NOT ACCEPTED.

**HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO.**

## NEXT EXACT ACTION

PHX-MASTER: select canonical #374/#375 parent/sequence and refresh pins. PHX-QA + PHX-CORE: resolve PAY-0745 and controller parity against approved semantic contracts. PHX-HARDWARE: no further overlapping sketch/workflow changes until the sequencing decision is recorded; preserve deny-only and do not merge, flash or enable coin admission.
