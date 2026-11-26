# PHX-HARDWARE — ESP32 Preferences per-key write-failure matrix

**Observed UTC:** 2026-11-26T21:47Z  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** phoenix/hw-poll-preflight-lab-modules-20261127-utc18  
**PR:** [#355](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/355), OPEN / DRAFT / UNMERGED  
**Base:** #354 at fc842342596786e072630179acfbbc4feeb2ba02  
**Exact source/test SHA:** 68416f69bc10dde8b2afa2948b312d4010507ad5

## Scope

One bounded test-hardening change. No production firmware, shared API, finance, QA source, signer, witness, COE destination or hardware configuration was modified.

The existing ESP32 Preferences host harness previously injected one failure at the server key. It now loops over all 13 keys independently:

ssid, pass, server, key, id, coinpin, ledpin, relaypin, coinlow, relayhi, ledhi, debounce, groupms.

For each key, the fake Preferences implementation returns zero for that write; the extracted real saveConfig() must return false while still attempting all 13 writes. A final all-success control must return true with 13/13 writes. ESP8266 continues to test failed/successful EEPROM.commit() propagation.

## Exact evidence

- Focused workflow [#45900402218](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45900402218), job 140184489587, exact checkout 68416f69bc10dde8b2afa2948b312d4010507ad5: **PASS**.
- Logs: ESP8266_EEPROM_COMMIT_FAILURE_PROPAGATED_PASS; ESP32_PREFERENCES_WRITE_FAILURE_MATRIX_PASS cases=13 writes=13/13; CONFIG_PERSISTENCE_WRITE_RESULT_PASS ESP8266+ESP32.
- Existing source-extracted poll wait/pulse-loss, deny-only remote-config, request-auth, output-latch and bounded EEPROM checks also passed in the same job.
- Native docs-head [#45900652601](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45900652601), job 140185311226, fails QA-owned tests/v060_vendo_sequence_contract.py:20 requiring active clearPending(true/false) callsites. No Hardware-side callsite was added.
- Full docs-head [#45900652616](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45900652616): CI-0701 job 140186298232 PASS; validation job 140186375629 fails QA-owned tests/controllers.sh:21 because the deny-only sketches intentionally lack config_revision. Target builds were still in progress; no final count is claimed.
- Mbed docs-head [#45900652645](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45900652645): source-contract job 140185906703 PASS; 3.3.13 job 140185906936 and 4.0.0 job 140185906993 still running at last check.

## Limits / risk

This is SIMULATED host validation with fake Preferences, not a physical ESP32 NVS failure or power-cut test. ESP32's 13 independent NVS writes remain non-atomic and may leave a partially updated configuration after a failure. The change proves failure propagation, not rollback or transactional persistence. It does not resolve active v0.6 #177's synchronous poll-before-sample race.

Physical GPIO/relay, real coin slot, electrical pulse/recovery, 150 power cuts and 30-device/24-hour soak remain NOT TESTED. HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO.

## Next exact action

Rerun Full after the handover refresh; ask PHX-QA and PHX-CORE to reconcile pending disposition and authenticated poll/receipt semantics before adding any clearPending callsite or enabling positive coin admission.
