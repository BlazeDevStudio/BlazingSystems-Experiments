# PHX-HARDWARE handover — ESP quarantine helper board parity

**Date:** 2026-11-21 UTC09  
**Role:** PHX-HARDWARE  
**Tasks:** #177 hardware safety / #266 cleanup-first  
**PR:** [#329 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/329), stacked on [#327](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/327)  
**Branch:** `phoenix/hardware-quarantine-parity-20261121`  
**Parent #327 HEAD at branch creation:** `827fa75fa4e56ff3033076cc2f9b7ebb0cddf1a8`  
**Parent #327 base #326:** `58c558fb6a237935214621adc3dee65a10fe1a51`  
**Source/test commit:** `aaf1a0e7c8012873a3b86c69e3329ed06f1f3beb`

## Selected cleanup / safety-coverage task

The active poll-loop board-parity guard compared 17 shared poll and coin-authority helpers, but omitted the six shared quarantine persistence/cleanup helpers. Exact-source review of both current sketches showed the following six functions were identical after whitespace normalization:

- `quarantineLogTokenValid`
- `quarantineLogField`
- `quarantineLogRecordValid`
- `inspectQuarantineLog`
- `appendQuarantineRecord`
- `quarantinePending`

The Hardware-owned `poll_loop_blocking_inhibit_lab.py` now requires these six helpers as part of the 23-helper ESP8266/ESP32 parity contract. It emits a dedicated 6/6 marker and rejects two fail-open ESP32 mutations:
1. bypassing the append write-length failure guard in `appendQuarantineRecord`;
2. bypassing the append-failure guard in `quarantinePending` before pending cleanup.

This is a test-harness parity/maintenance change only. No production `.ino`, persistence format, API, finance, signer/witness, QA-owned test, Release workflow, COE destination or shared contract changed. Coin admission remains default-deny.

## Exact-head CI evidence — source/test SHA above

- **Quarantine/readback:** [run #44891881754](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44891881754), job `136809273105`: **SUCCESS**. Logs include `POLL_SAFETY_BOARD_PARITY_PASS 23/23`, `POLL_QUARANTINE_HELPER_BOARD_PARITY_PASS 6/6`, both quarantine mutations rejected, `SOURCE_QUARANTINE_PASS 36/36`, and `PENDING_JOURNAL_LAB_PASS 16/16`. Physical power-cut testing was not run.
- **Relay/output:** [run #44891881780](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44891881780), job `136809273532`: **SUCCESS**. The same 23/23 and 6/6 parity markers and both quarantine mutation rejections are present. ESP32 boot-polarity job `136809273370`: **SUCCESS**.
- **Full BlazePwifi:** [run #44891881763](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44891881763): **FAILURE**, validation job `136809273964`. The failure is the inherited QA-owned `Missing poll signature check` in `experiment/openwrt/BlazePwifi/tests/controllers.sh`. All 14 target/platform build jobs, including ESP8266, ESP32 and Android, completed **SUCCESS**; downstream simulation, update, signing and publication jobs were skipped. No Full validation pass is claimed.

No pre-fix RED commit is claimed for this parity-coverage addition. The two explicit mutation injections are the negative evidence for the new guard.

## Classification and boundaries

- **SIMULATED:** normalized source-helper parity and mutation rejection; host LittleFS/quarantine fixtures.
- **CI VERIFIED:** exact source/test SHA focused Quarantine/readback and Relay/output workflows.
- **Full integration:** FAILED at the independent controller poll-signature contract gate.
- **HARDWARE ACCEPTED:** NO. Real coin selector, relay/electrical behavior, physical flash durability, 150 power cuts and 30-device/24-hour soak remain NOT TESTED.
- **PRODUCTION READY:** NO-GO.

The parity checks do not establish a working positive authenticated poll/receipt path. Current coin/poll admission remains deny-until-CORE-contract; this PR does not invent a signature or weaken the QA failure.

## Next exact actions

1. **PHX-CORE:** publish the canonical authenticated register/poll and event-bound receipt/disposition contract with exact bytes and golden vectors.
2. **PHX-QA:** align the stale positive poll-signature assertion only after CORE approval, retaining negative/default-deny checks.
3. **PHX-MASTER:** refresh canonical Hardware stack pins and active-head assignments; the existing #288 role/matrix rows still lag live #327.
4. **PHX-HARDWARE:** revalidate the entire live stack before the next owned change.

No merge, rebase, retarget, force-push, flash, production migration, signing, release tag, deployment or cutover was performed.
