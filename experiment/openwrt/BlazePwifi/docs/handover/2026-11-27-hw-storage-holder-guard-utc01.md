# PHX-HARDWARE — STORCHK-0674 active block-holder rejection

**Role:** PHX-HARDWARE  
**Task:** STORCHK-0674 / issue #34  
**Repository:** `BlazeDevStudio/BlazingSystems-Experiments`  
**Branch:** `phoenix/hardware-storage-preflight-device-separation-20261126-utc23`  
**Base:** `blazepwifi-v0.6.0-audit-foundation@2fbd2475e9f54878c316fa7cea2f228386b0e859`  
**DRAFT PR:** [#356](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/356)  
**Status:** CI VERIFIED (synthetic only) / HARDWARE NOT TESTED / PRODUCTION NO-GO

## Defect and test-first evidence

The sysfs resolver rejected non-empty `slaves` relationships but did not inspect `holders`. A scratch partition already backing a stacked mapping could therefore be accepted as an independent disposable partition.

- Test-only commit: `2ed04f5934954f9445616dd7c5f0f43923170aa6`.
- Expected RED: [focused run #45923702833](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45923702833), job `140260078848`; the log reported `unsafe physical-parent layout accepted: scratch partition with an active holder`.

## Correction

- Source fix commit: `9fad1abd1eab8bcb2caadff6901999df4be30944`.
- Replaced the slaves-only check with `has_block_relations()`, which rejects any existing symlink/entry under either `slaves` or `holders`.
- Apply the same conservative rejection to the candidate block node and its whole-device parent.
- Added synthetic failure injection for a holder on the scratch partition and a holder on the parent disk.

## Exact-source result

- [Focused push run #45923785751](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45923785751), job `140260350436`: PASS.
- Expected and actual checkout SHA both equal `9fad1abd1eab8bcb2caadff6901999df4be30944`.
- The test harness reports the physical-parent matrix PASS and explicitly emits `SIMULATED_ONLY=1`, `PHYSICAL_POWER_CUT_VERIFIED=0`, `CUSTOMER_INSTALL_AUTHORIZED=0`.

## Full integration and limitations

- Full run [#45923785875](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45923785875) was IN PROGRESS at the time of this handover; no aggregate Full PASS is claimed.
- Synthetic sysfs does not establish actual enclosure/controller separation, independent media, disposability or power-loss durability.
- No live mounts, block writes, power cuts, coin pulses, financial state, migration, device flashing or customer systems were touched.

## Next exact action

PHX-QA independently reviews the holder/slave rejection and supported sysfs topology; PHX-MASTER refreshes the #356 assignment/integration matrix. Keep #356 DRAFT and unmerged. Physical issue #34 remains NOT TESTED; production remains NO-GO.
