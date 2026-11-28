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


## PHX-HARDWARE UTC17 — terminal exact-head reconciliation CI

**Updated:** 2026-11-28T17:58:01Z  
**Task:** `PHX-HW-177-GPIO-WRITER-STACK-RECONCILE-20261128T17Z`  
**PR:** [#380](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/380), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-gpio-writer-reconcile-20261128-utc17`  
**Source/test SHA:** `83fc27e474064f2ed429332b8a14fa8ffb66784c`  
**Exact tested docs head:** `923bb5fa773a9164b0587b21b1e0fd29cf8323ed`

### Exact-head results

- Poll Intake Deny [#46173004720](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173004720), job `141065398557`: **PASS**. Both ESP8266 and ESP32 reject the four GPIO-writer mutations (8/8), both reject the direct post-deny relay GPIO ON mutation, and each passes the five-outcome × four-polarity matrix (20 cases). Log explicitly says `POLL_INTAKE_GUARD_SIMULATED_ONLY=1`.
- ESP32 Mbed TLS [#46173004705](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173004705): **3/3 PASS** — source contract job `141065398993`, core 4.0.0 job `141065399222`, core 3.3.13 job `141065399304`. Both clean A/B builds were byte-identical. Staged source tree SHA-256: `ccea8c3ba80f417b5cd0789ad68928f78c12a467ce77a0a3957121a4ad494c81`; core 4.0.0 image SHA-256: `0dd322dbb123a503076c3751e41363a1930737ca14276cae149c815b418d3d0d`; core 3.3.13 image SHA-256: `c96d722323d68ac2df940946930074f7961707cfaf0544572f4292eb486ba9cc`. Artifacts: [4.0.0 #15274507915](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173004705/artifacts/15274507915), [3.3.13 #15274855972](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173004705/artifacts/15274855972).
- Full [#46173004825](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173004825): **FAIL overall**. Handover freshness/history and CI-0701 passed. Validation job `141065462212` failed at QA-owned `tests/controllers.sh:21`, `grep -q 'config_revision' "$f"`. Both #377-based sketches lack that field. All **14/14 target/platform jobs passed**, including Android. Update bundle, simulations, candidate, signing and publication stages were skipped. This is a real CORE/QA controller-contract parity blocker; no decoy token was added.
- Native Synthetic Journal: **NOT RUN**. The workflow `blazepwifi-v060-native-journal.yml` is path-filtered to native journal files, pending-sequence files, and the two production sketches; this PR changes only the Hardware host-lab Python contract/case and handovers. No manual workflow-dispatch action is exposed by the connected GitHub tools.
- The first Full attempt on `dffa9a8` failed the canonical handover-freshness gate before controller parity; it is superseded by this exact-head Full result after append-only canonical sync.

### Remaining safety / release status

The active v0.6 branch remains `2fbd2475e9f54878c316fa7cea2f228386b0e859`; ESP8266 still performs synchronous poll before its first coin sample (lines 354/357), and ESP32 does so at lines 314/318. This reconciliation does not fix P0 pulse loss. Physical relay/acceptor polarity, pulse retention, EEPROM/NVS brown-out, LittleFS recovery, 150 controlled power cuts, 30-device/24-hour soak and electrical pulse/recovery remain **NOT TESTED**. Protected signer/witness, v1-to-v2 migration, durable accounting/replay and independent QA/release signoff remain **NOT ACCEPTED**. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.


## PHX-HARDWARE UTC17 — final exact tested PR head and release disposition

**Updated:** 2026-11-28T18:03:30Z  
**Task:** `PHX-HW-177-GPIO-WRITER-STACK-RECONCILE-20261128T17Z`  
**PR:** [#380](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/380), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-gpio-writer-reconcile-20261128-utc17`  
**Source/test SHA:** `83fc27e474064f2ed429332b8a14fa8ffb66784c`  
**Exact tested docs head:** `8b9a9d127fed56d9f38052bef353c2a4d71a7bcb`

### Final exact-head CI

- Poll [#46173474280](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173474280), job `141066875248`: **PASS**. Eight writer-authority mutations rejected (four per board), direct post-deny GPIO ON rejected on both boards, five poll outcomes × four polarity combinations pass. Explicit `POLL_INTAKE_GUARD_SIMULATED_ONLY=1`.
- Mbed TLS [#46173474278](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173474278): **3/3 PASS** — source contract `141066875879`, core 4.0.0 `141066876027`, core 3.3.13 `141066876136`. Both clean A/B builds byte-identical. Staged source tree SHA-256 `ccea8c3ba80f417b5cd0789ad68928f78c12a467ce77a0a3957121a4ad494c81`; core 4.0.0 image SHA-256 `1a544126e2f6ee4244d5eb66de5cfd4ac6a274e77ea1f7714b61b64c5bcb651e`; core 3.3.13 image SHA-256 `631f31a969ca4d367121d0b32db83e25162caab2b5ee0db4b63e23d34f345ab0`. Artifacts: [4.0.0 #15274374112](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173474278/artifacts/15274374112), [3.3.13 #15274757818](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173474278/artifacts/15274757818).
- Full [#46173474301](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173474301): **FAIL overall**. CI-0701 and handover freshness/history pass. Validation job `141066938748` fails at QA-owned `tests/controllers.sh:21` (`grep -q 'config_revision' "$f"`); both #377-based sketches lack that field. All **14/14 target/platform jobs PASS**, including Android, ESP8266, ESP32 and 11 OpenWrt targets. Update bundle, simulations, signing and publication remain skipped.
- Native Synthetic Journal: **NOT RUN**. Its workflow path filter requires native journal / pending-sequence paths or the production `.ino` sketches; this PR changes host-lab Python contract/cases and handovers only. The available GitHub connector exposes no workflow-dispatch write action.

### Disposition and next owner action

The #380 combined child preserves #378's post-deny GPIO escape test and #379's centralized writer authority on the current #377 base. Original #378/#379 remain OPEN/DRAFT and unmodified at their exact heads; #380 is a non-force-push successor, not a rewrite of either branch. PHX-MASTER must decide whether to pin #380 as the reconciled child or request a separately stacked child for #379.

QA owns the `config_revision` semantic parity assertion; CORE owns the canonical authenticated controller envelope. Do not add a decoy field or invent `response_sig`. Active v0.6 still polls before first coin sample on ESP8266 (354/357) and ESP32 (314/318). Physical GPIO/relay polarity, pulse retention, EEPROM/NVS brown-out, LittleFS recovery, 150 power cuts, 30-device/24-hour soak and electrical pulse/recovery remain **NOT TESTED**. Protected signer/witness, v1-to-v2 migration, durable accounting/replay and independent QA/release signoff remain **NOT ACCEPTED**. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.
