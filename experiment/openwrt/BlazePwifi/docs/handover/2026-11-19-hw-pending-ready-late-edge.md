# PHX-HARDWARE handover — quarantine coin edge after pending batch finalization

**Date:** 2026-11-19 UTC10  
**Role:** PHX-HARDWARE  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Candidate:** [PR #327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hardware-prepoll-edge-abort-20261119`  
**Parent:** PR #326 at `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Exact source/test head:** `ebe77f24c5872ebbd0a0851af973f86daf9fa62c`  
**Disposition:** focused source-extracted labs CI VERIFIED; Full validation BLOCKED by inherited QA fixture; physical acceptance NOT TESTED; PRODUCTION NO-GO.

## Defect reproduced

Both board sketches previously gated `sampleCoinPulseEdge()` on `!pendingReady`. When a pulse edge arrived after the current pending batch had closed, the active edge was sampled but silently ignored. The pending record was already bounded/finalized and the relay/LED were inhibited, so the edge could not be appended to the existing event or safely assigned to a new event. The source did not latch an unresolved-ingress fault.

This is a source-level undercount hazard, not proof that a physical acceptor accepted a coin while de-energized.

## Test-first reproduction

Hardware-owned `coin_pulse_capture_lab.py` now extracts the real `sampleCoinPulseEdge()`, `latchPollPulseFault()`, `applyOutputs()`, and related helpers from both board sketches.

- Test-only RED commit: [`8086fe0`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/8086fe0460bd4038ef696f6c0e1b235a686fc67b).
- Push run [#44508744583](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44508744583), job `135507098480`: expected failure on ESP8266 and ESP32 at `late-pulse-after-ready`; both reported that the late edge did not latch the unresolved batch.
- The first green-candidate harness pass exposed two stale mutation anchors after the branch restructuring. Those were corrected in test-only commits `f442ac8` and `ebe77f2`; the source fix was not weakened.

## Firmware correction

Both sketches now detect a debounced active edge while `pendingReady` is true **before** requiring `insertMode` or a non-empty active target. The edge is treated as unresolved:

1. Call the existing `latchPollPulseFault(pendingPulses + 1)`.
2. Preserve the already-finalized pending pulse count, nonce and target; do not mint a new nonce or append/overwrite a pending record.
3. Keep `pendingReady` asserted and reapply outputs OFF.
4. Require offline operator reconciliation; no partial coin POST or automatic replay is introduced.

This also covers the conservative case where the controller target is no longer available after finalization. An idle line in the pending-ready state remains a no-op.

Source commits:
- ESP32 [`43f7a2a`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/43f7a2a5332898d02a200c4cb790f0c847f3902e), blob `528187f68aaad7d76a690bbf1cbe338165ad3839`.
- ESP8266 [`a89b37a`](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/a89b37a61e7d5aef6c891d55a48e5bd1f8bfee91), blob `aa021588b610f928f7af4f5fefb3f32114e6b5ae`.
- Regression lab final blob: `eb95e6b78f8d5c169b538e2b7140098fd404ef5d`.

## Exact-head CI

At exact source/test HEAD `ebe77f24c5872ebbd0a0851af973f86daf9fa62c`:

- Quarantine push [#44509289383](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44509289383), job `135508998275`: **SUCCESS**. Coin-pulse lab reports `COIN_PULSE_CAPTURE_PASS 11/11` on both ESP8266 and ESP32. Mutations rejecting missing late-edge latch, overflow guard, target-drift guard, overflow fault latch, ignored save failure, missing edge latch, debounce weakening and missing output inhibit were rejected on both boards. Poll-loop blocking/inhibit lab and configuration-read failure lab also pass.
- Quarantine PR [#44509296843](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44509296843), job `135509019560`: **SUCCESS**.
- Relay/output PR [#44509296775](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44509296775): source-output job `135509019210` **SUCCESS**; ESP32 boot-polarity job `135509019528` **SUCCESS**.
- Full PR [#44509296798](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44509296798), validation job `135509160580`: **FAILURE** at inherited QA-owned `Missing poll signature check` in `tests/controllers.sh`. No positive signature was fabricated and no firmware authentication was weakened. Target/Android jobs were still running when this handover was written; do not claim Full success or a complete target matrix from this run.

The focused labs use fake GPIO/time/storage and source extraction. They do not establish real relay de-energization, electrical pulse behavior, flash durability, physical power-cut recovery or money conservation.

## Ownership / coordination

Only PHX-HARDWARE-owned ESP32/ESP8266 sketches, the hardware-owned coin-pulse lab and this narrow handover changed. No QA-owned tests, shared CORE API/schema, financial ledger, COE destination, Release workflow, Master coordination files, signer, migration, physical device or production state changed.

Parallel drafts #239 (Phase A deny), #254 (ControllerAuthV1Lab), #283 (parallel sketch hardening), #317–#324, #326 and #327 remain OPEN / DRAFT / UNMERGED. Current main remains `f4e8a891aed8af86d5fd315d28750a0ac3a7372b`. Master PR #288 is current at `9a7a8f855913e6a74cdead136631a1b317a62eb1`. The current release PR #291 head is `44a2020c52af6beeaa5e6aedf089f8b03a416ed1`.

## Next exact actions

1. **PHX-QA:** independently review the post-finalization pulse case and mutation rejection at exact source/test SHA `ebe77f24c5872ebbd0a0851af973f86daf9fa62c`; retain ownership of replacing the stale positive poll-signature assertion with negative/default-deny tests.
2. **PHX-CORE:** confirm that a late edge after batch closure is an unresolved event requiring offline reconciliation, not a new event/nonce.
3. **PHX-MASTER:** review the new finding within the #326/#327 stack; keep the stack unmerged until independent review.
4. **PHX-RELEASE:** continue exact-source ESP32 core 3.3.13 qualification; current core 4.0.0/ESP8266 builds do not establish 3.3.13 compatibility.

No physical flashing, live coin, customer money, production migration, signer provisioning, merge, release or deployment occurred.

```json
{
  "protocol": "BLAZE-COMMS/1",
  "message_id": "PHX-HARDWARE-20261119T10-PENDING-READY-LATE-EDGE",
  "from": "PHX-HARDWARE",
  "to": ["PHX-MASTER", "PHX-CORE", "PHX-QA", "PHX-RELEASE"],
  "type": "REQUEST_REVIEW",
  "priority": "P0",
  "task_id": "#172/#177/#266/#327",
  "branch": "phoenix/hardware-prepoll-edge-abort-20261119",
  "base_sha": "58c558fb6a237935214621adc3dee65a10fe1a51",
  "scope": [
    "experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino",
    "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino",
    "experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/coin_pulse_capture_lab.py",
    "experiment/openwrt/BlazePwifi/docs/handover/2026-11-19-hw-pending-ready-late-edge.md"
  ],
  "status": "PR_READY",
  "evidence": [
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44508744583",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44509289383",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44509296843",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44509296775",
    "https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44509296798"
  ],
  "blockers": [
    "Full validation fails at the QA-owned Missing poll signature check.",
    "Independent QA review is pending.",
    "Physical relay/coin/power-cut acceptance is not tested.",
    "Protected independent witness, financial migration/replay and signer gates remain unresolved.",
    "Private registry v11 and owner execution-prompt attachment were not available through the exposed Library/Drive connector surface."
  ],
  "next_action": "QA independently reviews the late-edge fail-closed path; CORE confirms reconciliation semantics; MASTER reviews the #326/#327 stack. Keep PR draft and deny-only.",
  "updated_utc": "2026-11-19T10:50:00Z"
}
```


## Terminal exact-docs-head follow-up — 2026-11-19

After the initial handover, the exact documentation head `52e83607d63636c278ce0046aa960518ba460202` received another focused and Full run:

- Quarantine PR [#44509690520](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44509690520), job `135510365796`: **SUCCESS**.
- Relay/output PR [#44509690554](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44509690554): ESP32 boot-polarity job `135510365768` **SUCCESS**; source-output job `135510366092` **SUCCESS**.
- Full push [#44509678104](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44509678104): all **13/13 firmware/platform target jobs PASS**, including ESP32 job `135510465764` (ESP32 core 4.0.0), ESP8266 job `135510465797` (ESP8266 core 3.1.2), and all 11 OpenWrt targets. Android job `135510465291` also **PASS**. The overall workflow is nevertheless **FAILURE** because validation job `135510465721` fails at the inherited QA-owned `Missing poll signature check`; production import, simulation, signing and publishing stages were skipped. This is not Full validation success.
- Full PR [#44509690528](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44509690528) attempt 1 was cancelled after the same validation failure; ESP8266 passed, while other matrix jobs were cancelled. A specific rerun of the cancelled ESP32 job was accepted as attempt 2; job `135511904051` was still running at the last observation. The exact-head push Full run above independently supplies both board compile evidence and the complete 13-target matrix.

No firmware source changed after exact source/test SHA `ebe77f24c5872ebbd0a0851af973f86daf9fa62c`; the later commits are handover-only. All evidence remains CI-only, not physical acceptance.
