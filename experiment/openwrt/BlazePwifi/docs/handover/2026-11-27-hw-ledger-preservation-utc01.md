# PHX-HARDWARE — STORCHK-0674 append-only ledger preservation

**Role:** PHX-HARDWARE  
**Task:** STORCHK-0674 / issue #34  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-storage-preflight-device-separation-20261126-utc23`  
**Base:** `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`  
**DRAFT PR:** [#356](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/356)

## Proven preservation defect

The PR branch's `docs/handover/CHANGE_LEDGER.md` had been replaced by a 33-line excerpt while the base contained 3,388 historical lines. This was not an acceptable append-only handover update.

## Test-first evidence

- Guard-only commit: `e9e1b751b98e4e6ed5228abea64c705d02e98b9c`.
- Expected RED: [PR run #45924871309](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45924871309), job `140263739909`.
- Exact checkout verified the commit SHA. The new guard reported `CHANGE_LEDGER_DELETED_LINES=3388` and `CHANGE_LEDGER_APPEND_ONLY_FAIL`, then stopped before the storage test.

## Correction

- Restore the complete base ledger from blob `f16d5774366cf3a4c358dd2a0c2e7ee5e945f668` without rewriting historical bytes.
- Append all three existing STORCHK-0674 sections and this preservation checkpoint.
- Add an append-only CI guard to `.github/workflows/phx-hw-storage-preflight-device-separation.yml`, comparing the exact PR base SHA with the checked-out head.
- Keep the check fail-closed if the base ledger cannot be read or any line is deleted.

## Scope and limitations

No ESP firmware, coin admission, storage mount, block write, power cut, finance, migration, signer, witness, COE, shared API or customer system was changed. The ledger gate verifies repository history preservation; it does not establish physical hardware acceptance.

**Status:** CI regression expected RED; restored-head focused/Full validation pending. Physical acceptance NOT TESTED. HARDWARE ACCEPTED NO. PRODUCTION NO-GO.


## Exact-head results and handover freshness follow-up

- Source/workflow/ledger commit: `76026ef72abe31d66ec5c81ebfe4851da63547ca`.
- Focused push run [#45925047254](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45925047254), job `140264299951`: PASS.
- Focused PR run [#45925051984](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45925051984), job `140264314588`: PASS; `CHANGE_LEDGER_DELETED_LINES=0`, append-only guard PASS, mountinfo and physical-parent synthetic matrices PASS.
- Full [#45925051986](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45925051986) validation job `140264448626` failed only at handover freshness because the canonical handover/current-state documents had not yet been updated after the workflow change. This docs-only synchronization updates those canonical checkpoints; a new Full run is required.
- The append-only gate now prevents recurrence of the 3,388-line truncation. Physical power-cut, storage independence and hardware acceptance remain NOT TESTED.


## PHX-HARDWARE UTC01 — dangling sysfs holder regression

- Role/task: PHX-HARDWARE / STORCHK-0674 / issue #34 / DRAFT PR #356.
- Added a negative fixture with a dangling symlink under the scratch parent disk's sysfs `holders` directory. The resolver must treat the symlink itself as an active/ambiguous relationship and block, even when its target no longer exists.
- This exercises the existing `[ -e ] || [ -L ]` fail-closed rule; no production firmware or storage behavior changes.
- The test and canonical handovers are committed together so the mandatory handover freshness gate remains valid. Exact-head focused and Full CI are pending.
- Physical storage, power-cut, customer, coin, finance and migration tests remain NOT TESTED; production NO-GO.
