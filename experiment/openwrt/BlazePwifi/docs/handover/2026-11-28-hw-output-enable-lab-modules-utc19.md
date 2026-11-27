# PHX-HARDWARE handover — startup GPIO output-sequence lab modularization (UTC19)

- Repository: BlazeDevStudio/BlazingSystems-Experiments
- Role: PHX-HARDWARE
- PR: #366 OPEN / DRAFT / UNMERGED, stacked on #365
- Branch: phoenix/hw-output-enable-lab-modules-20261128-utc19
- Parent #365 exact head: e65b0b895af9c3fc5e5632f704cb67b347e69725
- Source/test SHA: ff73702adf6fb958c9f21ebe9a68c908ee829ea4
- Evidence docs head: 9012440c1b80bf0b85d4399e7d37563e75014c62

## Change

Split output_enable_sequence_lab.py into a source-contract/mutation module, a C++ event/compile harness module, and a thin orchestration runner. The original command remains unchanged. No production firmware sketches or shared APIs changed.

## Terminal exact-head CI

- Focused run #46058803158, job 140707756468: PASS. 8/8 board/polarity scenarios PASS; 14/14 unsafe mutations rejected. Append-only ledger guard PASS (base 1,132,798 bytes; appended 43,445 bytes); its failure-injection suite passes. Existing config and pending-journal labs also pass.
- Mbed run #46058803171: source-contract 140708321000 PASS; Arduino ESP32 3.3.13 140708321364 PASS; 4.0.0 140708321346 PASS. Clean A/B build SHA256s match within each core: 044d78aa3540f2baa2de24430974c2c6db51cdff95d6a24dcfca878cfd41f9a5 (3.3.13), 160da9c7368abc85559c6bc2a941106f1d6dd7e6bd7d68ca545c42f1d6b51bac (4.0.0).
- Full run #46058803255: CI-0701 140707777619 PASS; controller protocol parity 140707834236 FAIL. ESP8266 140707834283, ESP32 140707834337, Android 140707834353, and 11 OpenWrt target jobs PASS. Downstream update/simulation/signing/publication jobs skipped. This known controller-parity failure is outside this test-only PR.

## Ledger and evidence integrity

The final CHANGE_LEDGER preserves the exact parent blob prefix and appends one UTC19 work record. The append-only CI guard independently passes. A transient incomplete ledger candidate from an oversized contents-API read was corrected through the Git Data API before review; it is not present in the final tree.

## Acceptance boundary

Physical GPIO voltage, relay contacts, pulse retention, electrical recovery, 150 power cuts, and 30-device/24-hour soak remain NOT TESTED. Host simulation/CI is not hardware acceptance. HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

## Next exact action

Master registers #366 in the role/integration matrices; QA reviews the exact source/test SHA and logs; Hardware keeps coin/relay admission denied until CORE publishes the authenticated register/poll/receipt/disposition contract and physical electrical review is completed.