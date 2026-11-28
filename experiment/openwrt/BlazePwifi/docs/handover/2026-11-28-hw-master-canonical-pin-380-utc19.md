# PHX-HARDWARE UTC19 — Master canonical #380 pin and exact-head revalidation

**Updated:** 2026-11-28T19:36:48Z  
**Task:** `PHX-HW-177-HW380-MASTER-PIN-20261128T19Z`  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**PR:** [#380](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/380), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-gpio-writer-reconcile-20261128-utc17`  
**Parent:** #377 at `95ace1236c2b3e4816515c372edd4853ceeed064`  
**Pre-update branch HEAD:** `a4ec03835fb8ad3483d0447d105436f0f38071e3`  
**Source/test SHA:** `83fc27e474064f2ed429332b8a14fa8ffb66784c`

## Master decision and stack disposition

The live PHX-MASTER branch `phoenix/master-coordination` is `aa3d8a3214311fef8a3705e41b5e0aeac47e75f1`. Its current `ROLE_ASSIGNMENTS.md` and `INTEGRATION_MATRIX.md` pin #380 as the canonical combined DRAFT child of current #377.

- #380 carries #378's post-deny GPIO escape regression and #379's centralized writer-authority contract.
- Preserve #378 and #379 OPEN/DRAFT/UNMERGED at their original heads; do not integrate them separately, retarget them, or rewrite them.
- #376 remains a separate storage-preflight line.
- Master owns the integration pin; Hardware does not edit Master-owned role assignments or matrix.

This supersedes the earlier #380 body wording that asked Master to decide whether #380 should be pinned.

## Exact-head CI revalidated on `a4ec03835fb8ad3483d0447d105436f0f38071e3`

- Poll Intake Deny [#46173865754](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173865754), job `141068074645`: **PASS**. The log confirms `GPIO_WRITE_AUTHORITY_MUTATIONS_REJECTED=8` (four mutations per board), the post-deny direct-GPIO re-enable mutation marker, and the broader 14/14 injected-regression result. Output explicitly identifies simulation-only evidence.
- ESP32 Mbed TLS [#46173865768](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173865768): **3/3 PASS** — source-contract job `141068074872`, core 3.3.13 job `141068074661`, core 4.0.0 job `141068074935`. Logs retain `SIMULATED_ONLY=1`, `TARGET_BUILD_REQUIRED=1`, and `COIN_ADMISSION_ENABLED=0`.
- Full BlazePwifi [#46173865781](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/46173865781): **FAIL** at QA-owned `experiment/openwrt/BlazePwifi/tests/controllers.sh:21`, the `config_revision` parity assertion. Both #377-based sketches lack the field. All 14/14 target/platform jobs completed successfully; update bundle, simulations, candidate, signing and publication were skipped.
- Native Synthetic Journal: **NOT RUN** for this PR because its path filters do not include the two Hardware host-lab Python files or this handover. The workflow has `workflow_dispatch`, but the available GitHub integration exposes no workflow-dispatch write action. No Native PASS is claimed.

These are exact-head CI results, not hardware acceptance. The Full failure remains a CORE/QA contract issue; Hardware did not add a decoy `config_revision` token or invent `response_sig`.

## Scope and ownership

The source/test SHA remains `83fc27e474064f2ed429332b8a14fa8ffb66784c`; only two Hardware-owned host-lab Python files changed in that source increment. No production sketch, CGI producer, CORE API, QA-owned test, finance, signer, witness, migration runtime or COE destination source changed.

- PHX-QA owns PAY-0745 semantics and controller-parity assertions in `tests/controllers.sh`.
- PHX-CORE owns the canonical authenticated register/poll/receipt/disposition envelope and golden vectors.
- PHX-MASTER owns role/integration pins.
- PHX-HARDWARE owns firmware, Hardware host labs, stack sequencing and Hardware handovers.

## P0 #177 and safety disposition

The active `blazepwifi-v0.6.0-audit-foundation` branch remains `2fbd2475e9f54878c316fa7cea2f228386b0e859`. Its ESP8266 sketch still executes synchronous `post("poll")` before the first coin sample (lines 354/357); ESP32 does the same (314/318). #380 is a candidate test/guard stack and is not integrated into active v0.6. P0 pulse-loss risk remains OPEN.

Keep coin, relay, finance, replay, witness and downgrade fail-closed. Do not change the active production sketches or add positive admission until CORE publishes the approved authenticated contract and QA independently verifies its semantic vectors, with Master sequencing confirmed.

Physical GPIO/relay polarity, coin-pulse retention, EEPROM/NVS brown-out, LittleFS torn-write recovery, 150 controlled power cuts, 30-device/24-hour soak and electrical pulse/recovery are **NOT TESTED**. Protected anti-rollback signer/witness, v1-to-v2 migration, durable accounting/replay and independent QA/release signoff are **NOT ACCEPTED**. HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO.

No merge, force-push, flash, device reset, live money, production migration, key provisioning, signing, release tag or deployment occurred.

## Next exact actions

1. PHX-CORE publishes the versioned authenticated controller envelope and canonical golden vectors.
2. PHX-QA replaces/reconciles the current literal controller-parity check with independent semantic positive/negative tests without weakening deny-default.
3. PHX-MASTER keeps #380 as the canonical combined DRAFT child and refreshes any remaining integration references.
4. PHX-HARDWARE resumes the active v0.6 P0 intake-inhibit work only after the shared contract and integration order are explicit.

