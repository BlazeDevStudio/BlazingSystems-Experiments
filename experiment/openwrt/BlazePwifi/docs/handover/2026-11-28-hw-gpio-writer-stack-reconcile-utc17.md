# PHX-HARDWARE UTC17 — GPIO writer guard stack reconciliation

**Task:** `PHX-HW-177-GPIO-WRITER-STACK-RECONCILE-20261128T17Z`  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Role:** PHX-HARDWARE  
**Base PR:** [#377](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/377)  
**Base branch:** `phoenix/hw-poll-deny-wrapper-child-20261128-utc15`  
**Base SHA:** `95ace1236c2b3e4816515c372edd4853ceeed064`  
**Working branch:** `phoenix/hw-gpio-writer-reconcile-20261128-utc17`  
**Source/test commit:** `83fc27e474064f2ed429332b8a14fa8ffb66784c`  
**Status at this handover:** source/test port committed; fresh exact-head CI pending.

## Why this reconciliation exists

PHX-MASTER's UTC16 decision in [#172 comment 7242694574](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/172#issuecomment-7242694574) identified that #378 was based on the stale #377 snapshot `95e54790...`, while the live #377 head is `95ace123...`; #379 inherits #378's stale ancestry. This branch is a new child of the live #377 head. Original #378 and #379 branches are preserved; neither is force-pushed, retargeted or closed.

## Actual source/test changes

Only two Hardware-owned host/source-contract files were ported from the #379 child tree onto the current #377 base:

- `poll_preflight_inhibit_lab_cases.py` retains the #378 post-deny direct-GPIO-ON failure injection and adds the #379 four writer-authority mutations per board.
- `poll_preflight_inhibit_lab_contract.py` adds `gpio_write_authority_locations()`.

The combined contract requires exactly one executable `digitalWrite()` inside `writeLogical()`; all logical writer callsites remain inside `configureRuntimePins()` and `applyOutputs()`; startup configuration writes logical OFF only; and `applyOutputs()` retains the existing polarity-aware `accepting` gate. The #379 matrix expects four unsafe mutations per board (8 total) to be rejected. The #378 direct post-deny bypass marker remains in the case module.

No production `.ino`, CORE API, QA-owned assertion, finance, receipt, signer, witness, migration or COE destination file changed.

## Prior exact-head evidence — historical only, not transferred

- #378 Poll [#46162211315](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46162211315) PASS; Mbed [#46162211276](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46162211276) 3/3 PASS; Full [#46162211282](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46162211282) FAIL at QA-owned `tests/controllers.sh:21` `config_revision`; Native NOT RUN.
- #379 Poll [#46166976076](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46166976076) PASS (8/8 GPIO writer mutations); Mbed [#46166976049](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46166976049) 3/3 PASS; Full [#46166976129](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46166976129) FAIL at the same QA-owned parity assertion; Native NOT RUN.

Those runs tested different PR heads. They are retained as history only. **Fresh Poll, Mbed, Native and Full runs for this reconciliation PR are required.**

## Known blockers retained

- QA owns controller parity and Native PAY-0745 semantic assertions; no decoy `config_revision` or altered QA-owned test is permitted.
- CORE owns the authenticated register/poll/receipt/disposition contract; no `response_sig` or positive admission is invented.
- Active v0.6 still polls before the first coin sample on both boards; this test-contract reconciliation does not fix P0 pulse loss in issue #177.
- Physical GPIO/relay polarity, acceptor pulse retention, EEPROM/NVS brown-out, LittleFS recovery, 150 power cuts, 30-device/24-hour soak and electrical pulse/recovery remain NOT TESTED.
- Protected signer/witness, v1-to-v2 migration, durable accounting/replay and independent QA/release signoff remain NOT ACCEPTED.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not recovered through Library search/list; no Google Drive connector is exposed in this runtime. No older registry was substituted.

## Required next action

Run Poll, Mbed, Native and Full against the exact final PR head. Keep the PR DRAFT. PHX-QA/PHX-CORE must resolve the controller contract and PAY-0745 blockers; PHX-MASTER must refresh integration pins after reviewing this new child. Coin/relay admission stays denied.

**Classification:** source changes are committed; fresh SIMULATED / CI VERIFIED status is pending exact-head runs. HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO.


## PHX-HARDWARE UTC17 — current-stack reconciliation and first exact-head CI

**Updated:** 2026-11-28T17:50Z (first CI read; canonical handover sync follows)  
**Task:** `PHX-HW-177-GPIO-WRITER-STACK-RECONCILE-20261128T17Z`  
**PR:** [#380](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/380), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-gpio-writer-reconcile-20261128-utc17`  
**Base:** #377 at `95ace1236c2b3e4816515c372edd4853ceeed064`  
**Source/test SHA:** `83fc27e474064f2ed429332b8a14fa8ffb66784c`  
**First tested PR head:** `dffa9a8e43b750372f8cd002b4106aa767a3abba`

### Exact CI on first tested head

- Poll Intake Deny [#46172575486](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46172575486), job `141064062306`: **PASS**. Logs contain `GPIO_WRITE_AUTHORITY_MUTATIONS_REJECTED=8`, both ESP8266 and ESP32 `POST_POLL_DENY_DIRECT_GPIO_REENABLE_MUTATION_REJECTED` markers, and the 5-outcome × 4-polarity poll transport matrix. The run explicitly reports `POLL_INTAKE_GUARD_SIMULATED_ONLY=1`.
- Full [#46172575460](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46172575460), validation job `141064117452`: **FAIL** at the mandatory handover-freshness gate. Its log identifies prior canonical checkpoint `f52524d20a589c7c300f0a97a13bfdb5ac3e8a6c` and requires the live canonical handover/state/ledger to be updated after the code change. It did **not** reach the controller-parity assertion. Target/platform jobs were still running at first read; no final target count is claimed here. This record is the corrective append-only canonical sync; a fresh Full run is required on the resulting head.
- Mbed TLS: **NOT RUN** on this PR head (no matching run returned).
- Native Synthetic Journal: **NOT RUN** on this PR head (no matching run returned).

### Classification

The source mutation guard is **CI VERIFIED / SIMULATED** by the exact Poll run. Full integration is **FAILED at handover freshness** on the first tested head; this is not a Full pass and not a controller-contract result. Mbed and Native remain NOT TESTED. No physical acceptance is inferred. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
