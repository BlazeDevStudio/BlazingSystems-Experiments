## PHX-HARDWARE UTC21 — deny-latch monotonicity contract

**Status:** OPEN / DRAFT / UNMERGED — PR #367.  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Role:** PHX-HARDWARE  
**Task:** #177 (supporting P0) / cleanup-first #266  
**Branch:** phoenix/hw-deny-latch-monotonicity-20261127-utc21  
**Base:** PR #366 at 07fef4e8e1055c06cf5e5c3a0d3829c52be31cc9  
**Exact tested head:** 183650be2174e94027b245654cf1eb5db5451dac  
**Terminal ledger commit:** 764a431a55549d7236a7d9ff398761185e139596

### Actual change

Extended the existing poll-preflight source-contract lab with a whole-sketch assignment audit for controllerEnabled, coinEnabled, relayEnabled, ledEnabled, insertMode and activeTarget. The contract allows only one global initializer per boolean and the unconditional denyRemoteControl() helper as the sole runtime write site. That helper must clear all five flags and the target exactly once.

Added seven failure mutations per board: re-enable each of the five flags outside the deny helper, restore a stale target outside the helper, and change the helper to set relay enabled.

No production ESP8266/ESP32 sketch, CORE API, financial source, QA-owned assertion, COE destination, signer or release configuration was modified.

### Tests

- Focused run #46069083820, job 140741404795: PASS. ESP8266 and ESP32 each report 7/7 deny-latch mutations rejected. Existing poll-intake, register, GPIO, config-persistence and pending-recovery labs passed.
- CHANGE_LEDGER append-only guard: PASS; base_bytes=1132798 appended_bytes=46976; exact #354 historical prefix preserved.
- ESP32 clean-build matrix #46069083861: 3/3 PASS. Source-contract 140741697634; core 3.3.13 140741697559; core 4.0.0 140741697175. Both core versions built twice from clean staging and produced byte-identical binaries. Binary SHA256: 3.3.13=a53c3c91a5a52274c3e94cff3f1836764c07c33087938d7152f20b44d699c4e4; 4.0.0=bd59c469b50ce6bb579083110e089df3082aa0dff79b55f010aaac7fec83bfac.
- Full run #46069084089: handover freshness/HND-0700/CI-0701 PASS; ESP8266, ESP32, Android and 11 OpenWrt targets PASS (14/14). Validation job 140741571137 FAILS at tests/controllers.sh:21 because config_revision is absent from the deny-only candidate. This is inherited QA/CORE contract parity; no decoy field was added. Downstream update/simulation/signing/publication skipped.
- Native PAY-0745: NOT RUN on this head; previous QA-owned assertion mismatch remains open.

### Limitations and safety

The scan covers direct assignments visible after comment/string masking; it is not proof against pointer aliasing, memory corruption or electrical faults. It does not resolve active-v0.6 P0 #177: active main still performs synchronous poll before first coin sample. The candidate remains deny-only. Coin and relay admission remain denied.

Physical polarity/retention, electrical recovery, 150 power cuts, 30-device/24-hour soak, protected anti-rollback signer/witness, durable accounting/replay, v1-to-v2 migration and independent QA/release signoff are NOT TESTED / NOT ACCEPTED. HARDWARE ACCEPTED=NO; PRODUCTION READY=NO-GO.

### Coordination

PHX-MASTER owns role and integration matrices; PHX-QA owns controller parity/PAY-0745; PHX-CORE owns authenticated register/poll/receipt/disposition. Master must register #367. No merge or deployment was performed.

The private BLAZE_PROJECT_REGISTRY_v11_20261027.json was not recovered. The accessible Library contains only an older 2026-11-09 checkpoint snapshot. The hourly signal YAML explicitly says it is a heartbeat only and does not wake AI workers.

**Sequencing deviation:** the pre-change IN_PROGRESS marker was not committed before the first source edit; disclosed rather than backdated.
