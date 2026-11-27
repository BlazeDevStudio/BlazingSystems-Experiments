# PHX-HARDWARE — #355 exact-head CI reconciliation

**Observed:** 2026-11-27 UTC05  
**PR:** [#355](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/355), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-poll-preflight-lab-modules-20261127-utc18`  
**Base:** #354 `fc842342596786e072630179acfbbc4feeb2ba02`  
**Pre-refresh docs HEAD:** `0adb541ae43143d6fc242f3746f56f71a3040d47`  
**Exact source/test commit:** `444c9a68a0da5a1e2c89839afee9705bf37219f2`

## PHX-HARDWARE UTC05 — #355 exact-head CI reconciliation

**PR:** [#355](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/355) — OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-poll-preflight-lab-modules-20261127-utc18`  
**Base:** #354 `fc842342596786e072630179acfbbc4feeb2ba02`  
**Pre-refresh docs HEAD:** `0adb541ae43143d6fc242f3746f56f71a3040d47`  
**Exact source/test commit:** `444c9a68a0da5a1e2c89839afee9705bf37219f2`

### Current exact-head evidence

- Focused PR [#45930541259](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45930541259), job `140281893321`: **PASS**. The exact-source log reports `CHANGE_LEDGER_APPEND_ONLY_PASS base_bytes=1132798 appended_bytes=14745`; all seven append-only regression tests pass. Both board poll labs report `BLOCKING_POLL_WAIT_PASS 3500ms pulse_ticks=80 samples_during_wait=0 accepted=0 polarity_combinations=4`. Startup-output-before-LittleFS, register deny, remote-config deny, request-auth, independent relay/LED polarity, EEPROM bounds and configuration-write failure labs pass.
- Push mirror [#45930534069](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45930534069): **SUCCESS** at the same docs HEAD.
- ESP32 Mbed TLS matrix [#45930541401](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45930541401): **3/3 PASS** — source contract, Arduino core 3.3.13 and 4.0.0.
- Full [#45930541357](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45930541357), validation job `140282755036`: **FAIL** at QA-owned `tests/controllers.sh:21`, which still greps for `config_revision` in both sketches. The candidate intentionally discards unauthenticated register/poll responses and contains no `config_revision` consumer. All 14 target/platform jobs and Android completed successfully; this is not a Full PASS.
- Native [#45930541359](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45930541359), job `140281893989`: **FAIL** at QA-owned `tests/v060_vendo_sequence_contract.py:20`, which requires literal active `clearPending(true/false)` callsites. The deny-only candidate deliberately has no active pending-disposition callsite and preserves unresolved journal evidence.

### Scope and ownership

The #354 parent/#355 child remains deny-only: both sketches inhibit coin/relay/LED admission before and after the synchronous poll, discard the unauthenticated response, and do not POST or clear pending coin records. The poll harness is host simulation only. This documentation refresh changes no firmware, API/schema, QA-owned assertion, CORE code, finance state, COE file or production configuration.

- **PHX-QA:** reconcile the controller parity and pending-disposition assertions with the deny/no-callsite/pending-evidence-preservation invariant; independently review the exact source SHA.
- **PHX-CORE:** publish the authenticated register/poll and receipt/disposition contract before any positive response consumer or pending clear is added.
- **PHX-MASTER:** preserve the #354 → #355 stack and reconcile current role/integration pins. #356 is a separate DRAFT with Full CI success but remains synthetic-only; #357 is a separate child of #355 and was not modified here.

### Acceptance classification

Host pulse/polarity/storage/config failure injection = **SIMULATED**; focused poll, append-only and Mbed checks = **CI VERIFIED**; Full integration = **FAILED** at the QA-owned legacy assertion; physical GPIO/relay, real coin acceptor, electrical pulse/recovery, 150 power cuts and 30-device/24-hour soak = **NOT TESTED**. **HARDWARE ACCEPTED = NO. PRODUCTION READY = NO-GO.**

No merge, rebase, retarget, force-push, flash, reset, live-money operation, migration, signing, release tag or deployment.


**Next exact action:** PHX-QA reconciles the two deny-only-incompatible assertions; PHX-CORE publishes the authenticated register/poll and receipt/disposition contract; PHX-MASTER preserves stack ancestry. PHX-HARDWARE retains the deny-only candidate and resumes positive-path work only after those contracts are approved.
