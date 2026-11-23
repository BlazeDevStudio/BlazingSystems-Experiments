# PHX-HARDWARE UTC13 — configured coin-ingress predicate stack reconciliation

**Observed:** 2026-11-23T13:42:31Z
**Role:** PHX-HARDWARE
**Task:** #177 — preserve coin-line edges and fail-closed admission
**Parent:** PR #345, exact parent HEAD `ca72497ed386c9ac4e50d3f811827bef51e296ad`
**Child branch:** `phoenix/hw-coin-ingress-config-helper-reconciled-20261123-utc13`
**Source/test HEAD after first reconciliation:** `59de2e122f57559804ecb2929b56903b6486c694`  
**Latest source/test HEAD:** `275057aa28375223a32da099420f52696d9b667c` (includes the prior source/test correction at `724d892e980f878903425837226c45b321638793`)
**PR:** [#347](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/347), OPEN / DRAFT / UNMERGED; child of #345

## Why this reconciliation exists

Master's UTC11 audit found that PR #346 was based on the older #345 snapshot `797dece76c18d464a7c0580658b5db9351cb8e15`, while #345 had advanced to `ca72497ed386c9ac4e50d3f811827bef51e296ad`. The child also changed the same poll-loop lab as the parent and did not contain the parent's newly added `pending_clear_failure_lab.py` file.

Rather than rebase or force-push the existing #346 branch, Hardware created this new child from the current #345 head and reapplied the narrow configured-ingress predicate changes. PR #346 remains untouched and OPEN/DRAFT pending Master disposition.

## Changes on the reconciled child

- Both ESP8266 and ESP32 sketches now define one file-local `coinIngressConfigurationAllows()` predicate and reuse it from `sampleCoinPulseEdge()` and `applyOutputs()`.
- The predicate remains exactly `controllerEnabled && coinEnabled && relayEnabled`; poll-time intake suspension remains a separate runtime state.
- All source-extraction labs that compile or compare `applyOutputs()` now include the helper explicitly.
- The poll-loop lab has a dedicated one-edge disabled-ingress main for controller, coin and relay. It runs an unmutated deny baseline first, then independently mutates each predicate term and expects the specific fail-open exit (64/62/60).
- The output-path mutation remains independent. The sample-path test forces only the output admission helper false, retaining the real output function and its side effects, so the scenario isolates credit admission rather than reusing unrelated positive-output tests.

## Parent changes preserved

This branch starts from the live #345 head, so it retains the parent-only:
- `pending_clear_failure_lab.py` and its failure-injection coverage;
- poll-loop invocation of `run_pending_clear_failure_lab()`;
- `quarantinePending()` parity and mutation coverage added by #345;
- all three parent handovers and the parent's source/test state.

The shared `poll_loop_blocking_inhibit_lab.py` was updated in-place on this new child by adding the ingress helper while preserving the parent-only quarantine and pending-clear logic. No files under Master, CORE, QA, RELEASE, rental, or Pisonet ownership were edited.

## Paths changed

- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/coin_pulse_capture_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/esp8266_boot_polarity_lab.py`
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/esp32_boot_polarity_lab.py`
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/journal_mount_failclosed_lab.py`
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/pending_journal_recovery_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_fault_latch_edge_count_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_response_failclosed_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_response_keyless_authority_red.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_window_drain_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/relay_output_polarity_lab.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/remote_config_pin_recovery_lab.py`

## Validation

- Local shell/compiler execution: NOT AVAILABLE in this activation.
- Exact-head Quarantine run [#45182191780](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45182191780) was in progress at the first PR head.
- Exact-head Relay/Output run [#45182191910](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45182191910) **FAILED** in `coin_pulse_capture_lab.py`: the child had inserted `coinIngressConfigurationAllows` into `FUNCTION_NAMES` but not the parallel `SIGNATURES` tuple, so mutation indexes shifted and the `missing-edge-latch` anchor was not found. The 17/17 positive coin-pulse markers still printed, but the job exited 1. This was a proven test-harness defect, not a firmware failure.
- Correction commit `724d892e980f878903425837226c45b321638793` adds the helper signature in the matching position, restoring positional parity. The failed run is retained as evidence; it is not relabeled PASS.
- Full run [#45182191977](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45182191977) validation job `137718519049` **FAILED** at the inherited QA-owned `Missing poll signature check`; ESP8266 target build job `137718518772` passed. Other target jobs were still running when checked.
- Corrected-head Quarantine [#45182801987](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45182801987), job `137720646293`: **SUCCESS** at docs head `716b340`. It confirms controller/coin/relay disabled-ingress baselines and fail-open mutations on both ESP8266 and ESP32 (expected exits 64/62/60), quarantine append failure preserves pending and attempt state on both boards, and the broader source-extracted fault/persistence checks pass. Logs explicitly retain `SIMULATED_ONLY=1`, `PHYSICAL_COIN_PULSE_ACCEPTANCE=0`, `PHYSICAL_RELAY_ACCEPTANCE=0`, and `PHYSICAL_POWER_CUT_ACCEPTANCE=0`.
- Corrected-head Relay/Output [#45182801977](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45182801977): **SUCCESS**; jobs `137720646610` (source/output polarity) and `137720647410` (ESP32 boot polarity) passed. Logs show coin pulse capture 17/17 and all 16 mutation cases rejected on both boards, relay output polarity 48/48 scenarios per board, poll-response fail-closed 11/11 plus strict JSON 13/13 and coin disposition deny 4/4 per board, and boot OFF-before-LittleFS PASS.
- Corrected-head Full build [#45182802143](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45182802143): **FAILED** at validation job `137720657858` with the inherited QA-owned `Missing poll signature check` / Controller protocol parity assertion. The log checked the PR synthetic merge ref `refs/remotes/pull/347/merge` for source/test head `716b340`; the test source is unchanged at `724d892`. Four target jobs passed (Orange Pi One `137720658004`, Ruijie `137720658292`, Orange Pi Zero2w `137720658161`, Orange Pi PC2 optional `137720658428`); the other target jobs were cancelled after the validation failure. Simulations, signing and publication were cancelled/skipped. No Full acceptance is claimed.
- After the exact-head runs, handover-only commit `8b4c55cd0814f426bee90c6afe623a5e791cca07` updated this record; no firmware or test source changed after the verified source/test SHA `724d892`.
- Parent #345 exact-head Quarantine run #45165015610 and Relay run #45165015665: PASS.
- Parent #345 Full run #45165015859: FAIL at inherited QA-owned poll-signature/controller protocol assertion; 14 target/platform jobs passed and validation-dependent stages did not pass.
- #346 had no PR-triggered runs at its then-current head `bd3fd6e85717395f768aae26a310b647cdd72a7e`; it remains a stale, unreconciled sibling candidate.

## Safety / release status

The change centralizes a configuration predicate and its tests; it does not add remote authority or permit unsigned poll responses. The firmware remains fail-closed. The CORE producer/consumer `response_sig` contract and QA golden vectors remain unresolved. Host tests are SIMULATED; physical coin acceptor, relay contacts, LittleFS durability and electrical pulse behavior are NOT TESTED. The 150 power-cut trials, 30-device 24-hour soak and electrical pulse/recovery remain NOT TESTED. HARDWARE ACCEPTED: NO. PRODUCTION READY: NO.

## Next exact action

PHX-QA/PHX-CORE must resolve the existing poll-signature producer/assertion contract without inventing a signature; PHX-MASTER must refresh the Hardware assignment/matrix for #347. Hardware's next action is exact-head revalidation after those owned changes, while keeping default-deny and the draft stack intact.


## UTC13:42 live revalidation — exact current source/test head

**Observed:** 2026-11-23T13:42:31Z  
**PR #347 API head before this handover-only update:** `275057aa28375223a32da099420f52696d9b667c`  
**Source/test SHA:** `275057aa28375223a32da099420f52696d9b667c`  
**Parent:** #345 at `ca72497ed386c9ac4e50d3f811827bef51e296ad`

The latest test-only commit changes `pending_clear_failure_lab.py` so the ignored-clear-result mutation remains syntactically valid (`clearPending(); return true;`). It does not change either production sketch.

### Exact-head CI

- Quarantine [#45186057750](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45186057750), job `137731843201`: **SUCCESS**.
- Relay/output [#45186057806](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45186057806): jobs `137731843214` (source/output polarity) and `137731845818` (ESP32 boot polarity): **SUCCESS**. Logs include poll-inhibit/edge/pending-deny mutation rejection, request-digest fail-closed controls, Mbed TLS 3/4 selector controls, and NVS readback failure controls.
- Full [#45186057891](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45186057891), validation job `137731998988`: **FAILED** at `Missing poll signature check` in the inherited controller test. ESP32, ESP8266, Android and all 14 target/platform jobs completed successfully. Validation-dependent simulations, signing, candidate and publication jobs were skipped.
- Logs retain `SIMULATED_ONLY=1`, `PHYSICAL_COIN_PULSE_ACCEPTANCE=0`, `PHYSICAL_RELAY_ACCEPTANCE=0`, and `PHYSICAL_POWER_CUT_ACCEPTANCE=0`.

The current ESP32 sketch on this #347 stack selects PSA Crypto for Mbed TLS 4 and the legacy SHA-256 API for Mbed TLS 3. The exact-head Full ESP32 build passed. This does not transfer to the separate #254 stack.

### Parallel-stack compatibility audit

- #254 remains OPEN / DRAFT at `84c442a46ee2ee48dcbe68b71ff0f54edbc09ba9`, based on #239. Its latest Full run [#44683629491](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44683629491) fails ESP32 because the sketch includes missing `mbedtls/sha256.h` under Arduino ESP32 core 4.0.0; its validation job also fails the handover gate (`CHANGE_LEDGER has no dated entries`). The earlier user-referenced #43632185933 is now terminal, not in progress: focused header job `132561036351` passed; Full ESP32 and target jobs passed, but validation failed.
- Separate Hardware PR #340 has an Mbed TLS 4 PSA Crypto adapter and a successful prior Full run [#44978514967](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44978514967) at source/test SHA `4eefce64719f40fd30621296db7c3fa764a44f1a`. It is based on #283 parent snapshot `88581eef6bce0dbaa4ac0de43e1239ee1afc2e9d`, while #283 has since advanced to `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`. Do not cherry-pick or transfer that Full result across the stale parent.
- #347 already contains the Mbed TLS 3/4 provider split and has exact-head ESP32 build success; Master should select/reconcile the canonical stack rather than create another parallel compatibility implementation.

### Revalidated #283 audit leads

At live #283 head `4dd0b01bf04cf80aec6d4dd6fc93b2fdc633da30`, both sketches return false on failed `appendQuarantineRecord()` before `clearPending()`, but `quarantinePending()` is definition-only with no active callsite. **Do not mark #283's lifecycle as fixed.**

The reconciled #347 stack is distinct: ESP8266 sketch blob `fa8ed828026396db89aab2889bf6a61d6cf6bbac` calls `quarantinePending(response)` at line 1374; ESP32 sketch blob `717336b84d434d51eb24beac1ed8efce8e719f69` calls it at line 1616. In both #347 sketches, failed `appendQuarantineRecord(reason)` returns false before `clearPending()`, and the clear helper is reached only after append/readback success. Exact-head Quarantine [#45186057750](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45186057750), job `137731843201`, logs both boards passing `QUARANTINE_APPEND_FAILURE_PRESERVES_PENDING_AND_ATTEMPT` and `QUARANTINE_CLEAR_FAILURE_PRESERVES_ATTEMPT_AND_RAM`; mutations that clear pending on append failure (expected exit 110) or ignore clear failure (expected exit 114) are rejected on both boards. This is source-extracted host simulation, not physical LittleFS/power-cut acceptance, and no #283 branch change or cherry-pick occurred.

Current main CGI producer blob `2e3a1430d08cc6606429a042df3b5848f53c7267` emits no approved `response_sig` for register/ping or poll; member-endpoint signatures are not interchangeable. The authenticated producer/consumer contract remains CORE/QA-owned; coin/config/relay admission remains deny-only.

### Coordination and release state

Master PR #288 is OPEN / DRAFT at `9f04ece155d2a7f58753521645d16042ae52dbaa`. Its current `ROLE_ASSIGNMENTS.md` still identifies #327 as active Hardware child and its `INTEGRATION_MATRIX.md` lists #283/#254, not #347. This is Master-owned and remains a reconciliation request. Cleanup-first #266 remains OPEN with 0/7 tracks complete. Issues #31/#32/#34/#43 remain open. The exact private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not found in the connected Library; no Google Drive connector is exposed and no older registry was substituted.

**Disposition:** focused Quarantine/Relay **CI VERIFIED** on exact source/test SHA `275057aa`; Full integration **FAILED/BLOCKED** at the QA-owned poll-signature assertion; physical acceptance **NOT TESTED**; HARDWARE ACCEPTED **NO**; PRODUCTION READY **NO-GO**.


## Master UTC13 matrix reconciliation — supersedes earlier stale assignment read

**Master PR #288 current head:** `2fd03816e3ab44c48fdcc81ec3c20ae13c0a2e0c`  
**Master reconciliation commit:** [`2fd03816`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/2fd03816e3ab44c48fdcc81ec3c20ae13c0a2e0c)  
**Master report:** [Hardware #347 final-head CI and role matrix reconciliation](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/blob/2fd03816e3ab44c48fdcc81ec3c20ae13c0a2e0c/coordination/phoenix/PHX_MASTER_UTC13_20261123_HARDWARE347_FINAL_HEAD_CI_AND_ROLE_MATRIX_RECONCILIATION.md)

Master updated six coordination files: `ROLE_ASSIGNMENTS.md`, `INTEGRATION_MATRIX.md`, `AUDIT_SUMMARY.md`, `ARCHITECTURE_CONTRACTS.md`, `INDEX.md`, and the new report. The current role/matrix now records #345 as parent, #347 as the reconciled child candidate, and #346 as a stale sibling. This resolves the earlier assignment/matrix omission; it does not authorize merge, production integration, or release. The canonical integration candidate decision remains pending.

Hardware has already refreshed this PR's own body and handover at docs head `546c63e490b4ef989721cb719450271059021eb1`; source/test SHA remains `275057aa28375223a32da099420f52696d9b667c`. Master report's statement that the PR body/handover is stale refers to the pre-refresh snapshot at `c7ab3601` and is superseded by the Hardware update. Master may refresh its report if it needs the latest docs-only head; no Master-owned file was edited by Hardware.

### Additional documentation/provenance inconsistencies routed to Master

- Experiments root README blob `feb909e3f74ffb7b5b22df50399ccd127ada3b95` still labels the repository “BlazingSystems — Experiments” and links the historical `BlazingSystems` owner, while live GitHub repository metadata confirms canonical owner `BlazeDevStudio`.
- BlazePwifi README blob `7990e2ecbab06cafa5f8227050929e16fff1f4a1` says current production release `0.3.0`; the live `PROJECT_HANDOVER.md` blob `f86c0ae9b14853963b8a9b835e1100eb5178d1a6` says production is frozen at `v0.5.2`. These documentation claims need owner reconciliation; Hardware did not edit them.
- COE #26 remains OPEN/DRAFT/FROZEN at `b382d233`; no destination files were copied or migrated. COE #35 and #49 remain separate drafts.
- Private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` remains unavailable in the connected Library; no Google Drive connector is exposed and no older registry was substituted.

**Current disposition remains:** #347 OPEN / DRAFT / UNMERGED; focused Quarantine/Relay CI VERIFIED at source/test SHA `275057aa`; Full integration FAILS at the QA-owned poll-signature assertion; physical acceptance NOT TESTED; PRODUCTION NO-GO.


## UTC15 — single-source coin-pulse helper extraction map

**Updated:** 2026-11-23T15:13:21.003Z  
**Scope:** Hardware-owned host regression only; no production sketch, shared CORE contract, QA-owned test, finance, signer, migration, workflow permission, or device changed.

The coin-pulse lab previously maintained separate manual `FUNCTION_NAMES` and `SIGNATURES` tuples. The earlier exact-head Relay failure (run #45182191910) demonstrated that adding a helper to one list but not the other shifted mutation indexes and caused a harness failure before the intended assertion.

This increment replaces both lists with one ordered `FUNCTION_SPECS` table containing each helper name and expected declaration. The lab derives the mutation index map from helper names, rejects duplicate helper names/signatures, verifies every extracted declaration against its expected signature, and reports unknown mutation targets explicitly. Mutation scenarios and firmware behavior are unchanged.

The exact-head Relay Output Polarity and Quarantine Byte Readback workflows both execute this coin-pulse lab; the Full BlazePwifi workflow independently checks the controller-protocol gate. Terminal run/job results are recorded in the PR #347 UTC15 checkpoint. All host and CI results remain SIMULATED / CI VERIFIED only; physical coin, relay, LittleFS power-cut, 150-cut and 30-device soak acceptance remain NOT TESTED.


## UTC16 — poll-drain active-line abort mutation proof

**Updated:** 2026-11-23T16:48:00Z  
**Role:** PHX-HARDWARE · **Task:** #177 · **PR:** #347 OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-coin-ingress-config-helper-reconciled-20261123-utc13`  
**Parent:** #345 `ca72497ed386c9ac4e50d3f811827bef51e296ad`  
**Source/test head:** `506ec8df42542f58c4d9a04269fbce488492b765`

### One bounded change

Only `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_window_drain_lab.py` changed. The source-extracted drain lab now removes the in-loop `if(!coinLineIdle())` abort guard in a negative mutation while deliberately retaining the final idle sample. A 30 ms pulse beginning at 100 ms then ends before the 250 ms drain closes; without the in-loop guard, the mutated helper would return idle and incorrectly permit the poll. The mutation must fail at `pulse-100ms-width30`.

No ESP8266/ESP32 production sketch, CORE/QA shared contract, finance path, workflow permission, or device was changed.

### Exact-head evidence

- Quarantine Byte Readback [run #45220006814](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45220006814), job `137851401846`: **PASS**. Logs show baseline `POLL_WINDOW_DRAIN_PASS 11/11` and `missing-active-line-abort` mutation rejected on ESP8266 and ESP32.
- Relay Output Polarity [run #45220006839](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45220006839), job `137851402806`: **PASS** with the same baseline and mutation rejection on both boards. ESP32 boot-polarity job `137851401866`: **PASS**.
- Full BlazePwifi [run #45220006841](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45220006841), validation job `137851586096`: **FAIL** at inherited QA-owned `Missing poll signature check` in the ESP8266 sketch. At this checkpoint 10/14 target/platform jobs had completed successfully and 4 remained in progress; downstream validation-dependent stages were skipped. No Full success is claimed.

### Live coordination revalidation

- Master PR #288 is OPEN / DRAFT at `3d4226bbff276a26066b3cb04e520b6eba252110`; its current role matrix records #345 → #347 and #346 as stale sibling. Master-owned report/matrix may need the new #347 head `506ec8df`.
- #239 `d83b715b`, #254 `84c442a4`, and #283 `4dd0b01b` remain OPEN / DRAFT / UNMERGED. No rebase, cherry-pick, merge or retarget occurred.
- Experiments main remains `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`; active v0.6.0 audit branch is `2fbd2475e9f54878c316fa7cea2f228386b0e859`. Canonical GitHub owner is `BlazeDevStudio`; historical README links still need Master-owned reconciliation.
- Cleanup-first #266 remains OPEN, 0/7 tracks complete. Financial #31/#32, safety #34 and witness #43 remain OPEN.
- COE main remains `a6513ab4412b4c014eee2863e45cbe32d06cb243`; PR #26 remains FROZEN / OPEN / DRAFT at `b382d233ff06c8791b1028bed3c617cc7b670d12`. No COE destination was edited.
- The exact private `BLAZE_PROJECT_REGISTRY_v11_20261027.json` was not surfaced. Library search found older v7/v6 snapshots only; no Google Drive connector is exposed, and no older registry was substituted.

**Disposition:** focused Quarantine/Relay **CI VERIFIED**; Full integration **FAILED / BLOCKED** by CORE/QA response-contract mismatch; physical pulse/relay/LittleFS acceptance **NOT TESTED**; 150 power cuts and 30-device soak **NOT TESTED**; HARDWARE ACCEPTED **NO**; PRODUCTION READY **NO-GO**.

**Next exact action:** CORE must publish the authenticated register/poll response contract and golden vectors; QA must reconcile the inherited poll-signature assertion independently; Master must refresh its #347 head pin. Then PHX-HARDWARE reruns Full against the approved exact head. No positive response signature or admission path will be fabricated.


## UTC16 — Full workflow terminal inventory

**Final docs head audited:** `0c6b7d98b12840a9058b072f9a53eec2ed047dd7`

The Full BlazePwifi workflow [#45220718744](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45220718744) has now reached a terminal result:
- Validation job `137853894840`: **FAIL** at the inherited QA-owned `Missing poll signature check` in the ESP8266 sketch.
- Target/platform builds: **14/14 SUCCESS**, including ESP32, ESP8266, Android, Ruijie, Orange Pi and x86_64.
- Validation-dependent browser/Orange Pi/Ruijie/x86/ESP simulations, update bundle, signing handoff, candidate gate and publication stages: **SKIPPED**.
- The earlier source/test-head Full [#45220006841](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45220006841) also ended with the same validation failure and 14/14 target builds successful.

The Full workflow is therefore **FAILED / BLOCKED**, not a Full integration pass. The test-only drain mutation is independently green in both focused workflows on the source/test and docs heads. No positive poll signature was introduced and no QA-owned assertion or CORE producer was changed.


## UTC17 — generated C++ diagnostic brace escaping and exact-head revalidation

**Updated:** 2026-11-23T17:32:19Z  
**Role:** PHX-HARDWARE · **Task:** #177 · **PR:** #347 OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-coin-ingress-config-helper-reconciled-20261123-utc13`  
**Parent:** #345 `ca72497ed386c9ac4e50d3f811827bef51e296ad`  
**Pre-handover source/test head:** `865d56f58e22e8a44dc45f15ea350ecb6ca035af`

### Bounded test-harness correction

Commit `865d56f` changes only `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_loop_blocking_inhibit_lab.py`. Literal C++ braces inside the Python f-string that generates the pre-poll diagnostic fixture are now escaped as doubled braces. This prevents Python from interpreting the generated C++ block delimiters as f-string replacement fields. No ESP8266/ESP32 production sketch, shared API, financial code, signer, witness, migration, or workflow permission changed.

### Exact-head GitHub Actions

Each focused workflow checked out the literal PR head and passed its explicit SHA verification:

- Quarantine Byte Readback [run #45227564058](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45227564058), job `137878041172`: **PASS**. The run includes the exact-source pending/quarantine failure labs, poll-drain and pulse-capture labs, and `coin_post_gate_lab.py`.
- Relay Output Polarity [run #45227564121](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45227564121), jobs `137878040962` and `137878041469`: **PASS**. ESP32 boot-polarity and both-board output, poll-drain and source-extracted regressions pass.
- Full BlazePwifi [run #45227564043](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45227564043), validation job `137878217287`: **FAIL** at Controller protocol parity / inherited QA-owned `Missing poll signature check`. All 14 target/platform jobs succeeded, including ESP8266, ESP32, Ruijie, Orange Pi Zero 3 and x86_64. Validation-dependent simulations, update bundle, signing, candidate and publication stages were skipped.

The Full failure is not repaired by adding a legacy signature to firmware. Current main register/poll responses still lack the approved event-bound authenticated response contract. CORE owns the producer/golden vectors; QA owns the independent assertion; Master owns the cross-role contract and integration decision. Hardware remains default-deny.

### Evidence classification and next action

Focused results are **SIMULATED / CI VERIFIED** only. Physical coin acceptor, relay/electrical pulse, LittleFS power-loss durability, 150 controlled power cuts, 30-device 24-hour soak and electrical recovery remain **NOT TESTED**. HARDWARE ACCEPTED: **NO**. PRODUCTION READY: **NO-GO**.

**Next exact action:** PHX-CORE publishes the approved authenticated register/poll response contract and golden vectors; PHX-QA reconciles the inherited assertion independently; PHX-MASTER refreshes its #347 exact-head pin. PHX-HARDWARE then reruns Full on the approved exact head. No flashing, live coin, migration, signer provisioning, merge, release or deployment.


## UTC17 — final docs-head terminal CI inventory

The handover-only docs commit `6b551031141b598ba0d484bf9127b3de60be6b47` has now reached terminal exact-head CI:

- Quarantine [#45230343610](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45230343610), job `137887857788`: **SUCCESS**.
- Relay [#45230343279](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45230343279), jobs `137887856081` and `137887856674`: **SUCCESS**.
- Full [#45230343272](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45230343272): **27/27 jobs terminal**. Target/platform jobs **14/14 SUCCESS**; validation job `137887857871` **FAILURE** at Controller protocol parity; 12 dependent simulation, update-bundle, signing, candidate and publication jobs **SKIPPED**.

This is a terminal Full failure, not a target-build failure. It does not promote the candidate to Full CI VERIFIED. Focused host labs remain SIMULATED / CI VERIFIED only. Physical acceptance remains NOT TESTED; PRODUCTION NO-GO.


## UTC18 — coin POST ISR fixture fidelity and multi-edge rollover

**Updated:** 2026-11-23T18:52:51.719Z  
**Role:** PHX-HARDWARE · **Task:** #177 · **PR:** #347 OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-coin-ingress-config-helper-reconciled-20261123-utc13`  
**Parent:** #345 `ca72497ed386c9ac4e50d3f811827bef51e296ad`  
**Source/test head:** `1011ee292197201193f7543cdb995d0e80933d8b`

### One bounded Hardware-owned test correction

The synchronous coin-POST failure-injection adapter previously incremented `coinEdgeSequence` directly. That bypassed the actual attached ISR and could let the test pass even if the production interrupt attachment were missing.

The runtime fixture now invokes the registered ISR only when the interrupt is attached to the configured coin pin and polarity edge. A configurable edge count supports multiple edges during the same blocked coin POST.

A new isolated `COIN_POST_ISR_MAIN` case seeds the 32-bit edge counter at `0xFFFFFFFE`, injects two attached ISR edges during the simulated 3500 ms coin POST, and verifies:
- modulo delta is exactly two after wrap to zero;
- the existing four-pulse pending record and target/nonce identity remain intact;
- the pending-attempt marker remains set and `clearPending()` is not called;
- the durable poll-fault marker records `pulses=6` (four pending plus two unresolved ISR edges);
- outputs remain OFF and journal recovery is required.

A negative mutation removes the coin `attachInterrupt()` registration. The isolated case must fail with expected exit 45; it is rejected on both ESP8266 and ESP32.

### Changed test-only paths

- `poll_loop_blocking_inhibit_lab_runtime_fixtures.py`
- `poll_loop_blocking_inhibit_lab_scenario_fixtures.py`
- `poll_loop_blocking_inhibit_lab_fixtures.py`
- `poll_loop_blocking_inhibit_lab.py`

No production `.ino`, CORE API, QA assertion, finance code, signer, witness, migration, workflow permission, or device was changed.

### Exact-head GitHub Actions

- Quarantine Byte Readback [run #45242372193](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45242372193), job `137930113158`: **PASS** at exact source/test SHA `1011ee2`. Logs include the multi-edge rollover marker and missing-ISR mutation rejection for both boards.
- Relay Output Polarity [run #45242372365](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45242372365), jobs `137930112471` and `137930113226`: **PASS** at the same SHA. ESP32 boot polarity and source/output-polarity labs pass; logs include both board markers and expected-exit-45 mutation rejection.
- Full BlazePwifi PR run [#45242372166](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45242372166), validation job `137930281470`: **FAIL** at inherited `Missing poll signature check` in the ESP8266 sketch. Target jobs were still finishing at this checkpoint; this is not a Full integration pass.
- Push Full run [#45242359443](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45242359443), validation job `137930242874`: **FAIL** at the same controller-protocol assertion. Target jobs were still finishing at this checkpoint.
- The first test-only commit `ea6b69f2949fec9a306d3e07e867865e58817df7` produced focused failures [#45242055161](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45242055161) and [#45242055143](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45242055143): the isolated test main omitted shared `resetState()` helpers. This was a harness compile failure, not a firmware failure. Commit `1011ee2` corrected the fixture builder; the two focused workflows above pass on the corrected exact SHA.

### Classification and next action

The new multi-edge test is **SIMULATED / CI VERIFIED** only. Physical coin acceptor, relay/electrical pulse, LittleFS power-loss durability, 150 controlled power cuts, 30-device 24-hour soak, and electrical recovery remain **NOT TESTED**. HARDWARE ACCEPTED: **NO**. PRODUCTION READY: **NO-GO**.

**Next exact action:** PHX-CORE must publish the approved authenticated register/poll response contract and golden vectors; PHX-QA must independently reconcile the inherited poll-signature assertion; PHX-MASTER must refresh the #347 exact-head pin. PHX-HARDWARE then reruns Full integration against the approved exact head.


## UTC19 — shared C++ fixture runner extraction and exact-head reconciliation

**Observed:** 2026-11-23T19:48:44Z  
**Role:** PHX-HARDWARE · **Tasks:** #177 / #266 · **PR:** #347 OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-coin-ingress-config-helper-reconciled-20261123-utc13`  
**Parent/base:** #345 `ca72497ed386c9ac4e50d3f811827bef51e296ad`  
**Firmware-source SHA:** `275057aa28375223a32da099420f52696d9b667c`  
**ESP8266 sketch blob:** `fa8ed828026396db89aab2889bf6a61d6cf6bbac`  
**ESP32 sketch blob:** `717336b84d434d51eb24beac1ed8efce8e719f69`  
**Test/lab-source SHA:** `fc1bfe86e51e1446712915c69087dca5be8e0763`  
**PR/docs head before this handover:** `fc1bfe86e51e1446712915c69087dca5be8e0763`

### One bounded Hardware-owned cleanup

Added `cpp_fixture_runner.py` as the single owner of temporary C++ fixture file creation, compiler invocation, timeout handling, and execution result capture. The three source-extracted labs now delegate only those mechanics to it:

- `poll_loop_blocking_inhibit_lab.py` preserves its `-Wno-unused-parameter` flag, 30-second compile timeout, 10-second run timeout, expected-exit checks, and stdout return contract.
- `poll_window_drain_lab.py` preserves `-pedantic -O2` and its `CompletedProcess` result contract.
- `coin_pulse_capture_lab.py` preserves `-pedantic -O2` and its `CompletedProcess` result contract.

Fixture assembly, board-specific extraction, expected exit codes, and safety assertions remain in their existing labs. This is a test-harness structure cleanup only; no production `.ino`, CORE API, QA assertion, finance path, signer, witness, migration, workflow permission, or device was changed.

### Failed first attempt and correction — preserved honestly

The first runner extraction used an overbroad function replacement and inadvertently removed the adjacent `POLL_SAFETY_PARITY` / required-authority constants from `poll_loop_blocking_inhibit_lab.py`.

- Quarantine [#45252246599](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45252246599), job `137964669419`: **FAIL**, `NameError: POLL_SAFETY_PARITY is not defined`.
- Relay [#45252246721](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45252246721), job `137964666252`: **FAIL**, same missing parity constant.

The constants were restored from the exact pre-refactor source anchor in commit `fc1bfe86e51e1446712915c69087dca5be8e0763`. No failure was waived or relabeled as a pass.

### Corrected exact-source/test-head CI at `fc1bfe86e51e1446712915c69087dca5be8e0763`

- Quarantine [#45252412144](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45252412144), job `137965275116`: **SUCCESS**. Exact-source labs ran; ESP8266 and ESP32 coin-pulse capture each report `17/17` PASS, with negative mutations for missing edge latch, debounce, overflow guard, target-drift guard, persistence, output inhibit, and ISR reconciliation rejected. The run explicitly reports `SIMULATED_ONLY=1` and physical acceptance flags `0`.
- Relay [#45252412350](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45252412350), jobs `137965250628` and `137965250680`: **SUCCESS**. ESP32 boot polarity and source/output-polarity jobs pass; both-board poll-window and coin-pulse host labs run through the shared runner. Negative mutations remain rejected.
- Full [#45252412053](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45252412053): **TERMINAL FAILURE**, 27/27 jobs terminal; 14/14 target/platform jobs **SUCCESS**, validation job `137965441351` **FAILURE** at the inherited `Missing poll signature check` in the ESP8266 sketch, and 12 dependent simulation/update/signing/candidate/publication jobs **SKIPPED**. This is not Full CI VERIFIED.

### Evidence classification and next action

The runner refactor is **CI VERIFIED** as test infrastructure; the source-extracted hardware behaviors remain **SIMULATED**. Physical coin acceptor, relay/electrical pulse, LittleFS power-loss durability, 150 controlled power cuts, 30-device 24-hour soak, and electrical recovery remain **NOT TESTED**. HARDWARE ACCEPTED: **NO**. PRODUCTION READY: **NO-GO**.

**Next exact action:** PHX-CORE publishes the approved authenticated register/poll response envelope and golden vectors; PHX-QA independently reconciles its poll-signature assertion against that producer contract; PHX-MASTER refreshes the #347 exact source/lab/docs pins. PHX-HARDWARE then reruns Full on the approved exact head. Keep all candidate PRs DRAFT and deny-only.


## PHX-HARDWARE UTC20 — bound shared C++ fixture execution

**Observed:** 2026-11-23T20:48:19Z  
**Role:** PHX-HARDWARE  
**Task:** #177 / cleanup-first #266  
**PR:** [#347](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/347), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-coin-ingress-config-helper-reconciled-20261123-utc13`  
**Parent/base:** #345 at `ca72497ed386c9ac4e50d3f811827bef51e296ad`  
**Source/test commit:** `d246390e4468235defdd9a6837bd16e7cb4d45c6`

### Defect and bounded change

The shared `run_cpp_fixture()` helper defaulted both `compile_timeout` and `run_timeout` to `None`. The poll-window and coin-pulse labs use the defaults, so a stalled compiler or generated fixture had no per-process deadline and could occupy a GitHub job until the outer workflow timeout. The poll-loop lab already passed explicit 30/10-second bounds, but that protection was not shared by all callers.

The Hardware-owned test infrastructure now defines:
- `DEFAULT_COMPILE_TIMEOUT_SECONDS = 30`
- `DEFAULT_RUN_TIMEOUT_SECONDS = 10`

Those are the default parameters for every caller; explicit per-lab overrides remain supported. Added `cpp_fixture_runner_contract_lab.py` with five mocked-process contract tests for default bounds, explicit overrides, compile timeout, execution timeout, compile diagnostic-tail bounding, and preserving a nonzero fixture exit for the caller. `poll_window_drain_lab.py` runs the contract suite before compiling either board's extracted source.

Changed paths:
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/cpp_fixture_runner.py`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/cpp_fixture_runner_contract_lab.py` (new)
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/poll_window_drain_lab.py`

No production `.ino` sketch, shared CORE API, financial path, signer, witness, or release workflow changed.

### Exact-head CI

At source/test head `d246390e4468235defdd9a6837bd16e7cb4d45c6`:

- Quarantine [#45262310201](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45262310201), job `138000014771`: **SUCCESS**. Logs show `Ran 5 tests`, `CPP_FIXTURE_RUNNER_CONTRACT_PASS 5/5`, poll-window `11/11` on ESP8266 and ESP32, and all three timing/active-line mutations rejected on both boards.
- Relay [#45262310174](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45262310174), jobs `138000015101` and `138000015712`: **SUCCESS**. The same 5/5 runner contract suite and both-board poll-window cases passed; relay and boot-polarity labs also completed successfully.
- Full [#45262310273](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45262310273): **TERMINAL FAILURE**. Validation job `138000016294`, step `Controller protocol parity`, reports `Missing poll signature check` in the ESP8266 sketch. All 14 target/platform jobs (ESP32, ESP8266, Android, Orange Pi variants, Ruijie, x86-64) completed **SUCCESS**; 12 downstream simulation/update/signing/candidate/publication stages were **SKIPPED**. This is not a Full integration pass.

### Evidence classification and remaining gates

The runner contract is **CI VERIFIED**. Board-specific behavior in the host/source-extracted labs is **SIMULATED**. Physical coin acceptor, relay contacts, electrical pulse/recovery, LittleFS power-loss durability, 150 controlled power cuts, and 30-device/24-hour soak remain **NOT TESTED**. HARDWARE ACCEPTED: **NO**. PRODUCTION READY: **NO-GO**.

This is a narrow test-harness safety improvement; it does not complete #266's Hardware requirement to keep the canonical bounded parser, signature binding and verification routines separate from actuation. The #266 Hardware track remains unchecked.

**Next exact action:** PHX-CORE publishes the approved authenticated register/poll response envelope and canonical golden vectors; PHX-QA reconciles the poll-signature assertion against that contract; PHX-MASTER refreshes the #347 source/test/docs pins. Hardware then reruns Full on the approved exact source head. Keep all candidate PRs DRAFT and deny-only.
