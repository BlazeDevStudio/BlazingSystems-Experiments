# PHX-HARDWARE — #355 historical ledger restoration and append-only guard

**Observed:** 2026-11-27 UTC02  
**PR:** [#355](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/355), OPEN / DRAFT / UNMERGED  
**Branch:** `phoenix/hw-poll-preflight-lab-modules-20261127-utc18`  
**Base:** #354 `fc842342596786e072630179acfbbc4feeb2ba02`  
**Source/test commit:** `444c9a68a0da5a1e2c89839afee9705bf37219f2`

## Defect and preservation

The #355 branch's `CHANGE_LEDGER.md` had been reduced to 12,301 bytes / 94 lines while the exact #354 base ledger contained 3,621 newline-delimited records. The original base blob `b950f7be47f79d71e6cb8b721801c1bae128df45` was restored as an exact byte prefix. The complete former #355 ledger (94 lines, 59 nonblank) was retained after it; no exact nonblank line duplicated the base.

## Test-first evidence

- RED commit: `47eeb04cde42ac72b5e68ab1dc4c23cc91aadc6d`.
- Expected RED [run #45930205543](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45930205543), job `140280823970`: five negative tests failed against the intentionally unsafe stub (empty base, middle edit, prepend, truncation, missing newline separator).
- Fix commit: `444c9a68a0da5a1e2c89839afee9705bf37219f2`.
- Focused GREEN [run #45930312768](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45930312768), job `140281160286`: PASS. Exact checkout verified; byte-prefix guard PASS (`base_bytes=1132798 appended_bytes=13736`); all 7 guard tests PASS; existing poll, remote-config deny, request-auth, output-latch, EEPROM integrity and config-persistence labs PASS.

## Full integration and next action

Full [run #45930312762](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45930312762) had CI-0701 PASS but validation failed at the mandatory handover freshness gate because this new helper/test had not yet been recorded in the canonical project handover. This document sync addresses that stale record; rerun Full on the resulting docs head and inspect all target jobs plus validation. No aggregate Full PASS is claimed.

## Safety boundary

No firmware/payment authority/shared API/QA or CORE source/COE destination changed in this task. No flashing, reset, physical storage write, live money or customer data. SIMULATED / CI VERIFIED only. Physical acceptance NOT TESTED; HARDWARE ACCEPTED NO; PRODUCTION NO-GO.
