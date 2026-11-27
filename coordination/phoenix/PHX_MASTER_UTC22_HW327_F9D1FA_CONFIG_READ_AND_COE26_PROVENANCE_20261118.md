# PHX-MASTER UTC22 — poll-drain subtest PASS; full-image EEPROM read recovery remains failing

**Timestamp:** 2026-11-18T22:51:38.802Z  
**Role:** PHX-MASTER — Master Auditor / Integration Coordinator  
**Task:** #172 / #266 / #288 / #327 / COE #26  
**Scope:** coordination/phoenix, architecture/interface contracts, exact-head integration matrix and migration provenance only  
**Codex:** NOT USED  
**Disposition:** PR #288 OPEN/DRAFT; production NO-GO; no migration proposed.

## Live refs

- Experiments main f4e8a891aed8af86d5fd315d28750a0ac3a7372b; development blazepwifi-v0.5.3-development @ aad3aade72c1156eecba1fed30907c6d0283b2c5; comparison-only branch blazepwifi-v0.6.0-audit-foundation @ 2fbd2475e9f54878c316fa7cea2f228386b0e859.
- Master pre-update 0f64a25a9948322d3dfd9e7e190fce1c8c8bcf14; COE main a6513ab4412b4c014eee2863e45cbe32d06cb243; COE #26 b382d233ff06c8791b1028bed3c617cc7b670d12 OPEN/DRAFT.
- Master #288 OPEN/DRAFT, base main@f4e8a891..., head 0f64a25... before this update. OWNERSHIP_ROUTES e4db324315a1b3543fec17a148fbf960170fcb29, DRAFT_REVIEW_ONLY, Master target null.

## Hardware #327 exact-head status

Live PR head f9d1fa165ccc94b18aeac7e85ffd83c29899463f, child of #326 at 58c558fb6a237935214621adc3dee65a10fe1a51. Source/test SHA ed667e88f6844284834ebd3a337dfce07a817e8c; firmware correction ddb386847e152e8ca4992e9f6b3370bfa3f20462. PR description still says c51271938c15e13998d1c99f1d311ca777bb1cc2 is current head and is stale.

Current blobs: ESP8266 sketch cd1acb1da298d4f9598e943dae05918b088e5363; ESP32 sketch ef498761e46d37134730dd41de1cc322d5d443e8; poll-loop lab 02dc80e547424817d00bfa23c70540a51a262273; full-image read lab 07e44b5076db69c1d55e913790c44a5feac29ca3.

| Exact-head run | Result |
|---|---|
| [44414150601 — quarantine/readback](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44414150601), job 135189867065 | FAIL: config read lab expected exit 0, got 31 |
| [44414150956 — relay/output](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44414150956), job 135189869232 | FAIL: same config read lab exit 31 |
| [44414150578 — Full build](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44414150578), validate 135190015439 | FAIL: Missing poll signature check |

Both focused logs show POLL_ABORT_DRAIN_INHIBIT_CONTINUITY_PASS, POLL_ABORTED_DRAIN_ISR_EDGE_PERSISTED_PASS, POLL_ABORTED_DRAIN_ISR_EDGE_ACTIVE_HIGH_PASS and POLL_LOOP_BLOCKING_INHIBIT_LAB=PASS on ESP8266 and ESP32. They then fail in the separate ESP8266 config_load_read_failure_lab.py first recovery scenario. The log exposes the combined predicate only. Source inspection shows loadCfg() still uses EEPROM.begin(544) then EEPROM.get(0,current); status-bearing ESP.flashRead is limited to the poll-fault marker record, not the complete Config image. The full-image read-failure/recovery invariant remains OPEN; this is not confirmed physical data loss.

The Full validation fails at the inherited QA-owned positive poll-signature assertion. All 13 firmware/platform targets and Android completed SUCCESS; simulations, update bundle, candidate, signing and publishing were skipped. No fake signature should be added.

## Other role and integration evidence

- CORE #252 c82705f2...: 42698139210 SUCCESS, scoped; separate owner retained.
- RENTAL #289 68928774...: 43653329235 and 43653329229 SUCCESS; Android instrumentation class not proven by those runs.
- PISONET #255 d01fd164...: 42462978704 SUCCESS; physical COM acceptance NOT TESTED.
- QA #292 75a3f66d..., base b1ca02e... stale Master base; no runs.
- RELEASE #291 5020f710...: Windows 44411293227 FAIL because $buildWorkflow is uninitialized under StrictMode; shared 44411293180 SUCCESS; publisher skipped.
- COE Release #44 code/test 81cb174..., docs 582fd5d5...: shared 44390136309 and case 44390136296 SUCCESS; sandbox 44390136327 FAIL because bubblewrap is unavailable.
- COE CORE #45 9d76a134...: 44295049903 and 44295049727 SUCCESS, scoped.

## COE #26 provenance — no migration

Source ESP8266/ESP32 blobs cd1acb1d... / ef498761... differ from COE #26 blobs c8be98f7... / 3cc7ec54.... Exact trees contain 19 source ESP32/ESP8266 Python board labs and zero COE Hardware Python labs. COE has one generic Hardware shell test (f921c56c...) invoked by hardware-ci.yml (fe79adbd...); it still positively greps response_sig and |poll| and does not invoke source labs. #26 has five queued workflows and zero jobs.

Source experiment/openwrt/BlazePwifi/LICENSE and COE Pisowifi/LICENSE are identical blob 1ee55b94.... Source root NOTICE.md exists at f6d92cd2...; COE root NOTICE.md and Hardware/LICENSE/NOTICE.md are absent. Pisowifi license is in a sibling directory; intended scope over Hardware is unresolved. QR-code and TailAdmin vendor LICENSE/NOTICE blobs match but do not resolve root/Hardware scope. No files were moved or copied.

## Governance, test limits and next action

Both rulesets endpoints returned empty arrays. Main branch-protection reads returned 403 Resource not accessible by integration; protections are NOT independently verified. AGENTS.md was read; its linked cloud policy/recovery handover were not readable at referenced paths. No Google Drive connector is exposed; private registry and newer corrections are unavailable in Library. Older v3-v7 snapshots were not substituted. No private IDs or registry contents were published. Issue #266 remains OPEN with historical PR pins.

GitHub source/tree inspection and exact CI logs were performed. Master Python suite NOT RUN; PR #288 returned no workflow runs. Exact-SHA git clone failed because this runtime could not resolve github.com. No physical tests, flashing, power cuts, soak, signing, financial migration, merge or release occurred.

Next: PHX-HARDWARE fixes full-image EEPROM read/recovery while preserving marker bytes; PHX-QA independently reviews the exact SHA and negative poll contract; PHX-RELEASE fixes its own #291 harness and obtains a bubblewrap-capable runner; COE owner completes provenance/CI; repository admin and registry custodian restore access and protection.

**PRODUCTION NO-GO** remains until independent protected signing/anti-rollback witness, crash-atomic durable financial state, reversible migration tests, independent QA, native acceptance, 150 real power cuts, 30-device/24-hour soak and owner-authorized release gates are independently evidenced.
