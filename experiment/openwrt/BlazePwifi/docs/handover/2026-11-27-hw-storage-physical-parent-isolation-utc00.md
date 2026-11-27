## PHX-HARDWARE UTC00 — exact-docs-head Full validation update

- Exact docs/source workflow run: [#45918825520](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45918825520), checked out docs head 11f406a89ef4c5ae56c97b89678df6d737f1edbd and source/test SHA cb07904ccbedaeeb93e7eb763dc3c795e7e90c9f.
- CI-0701 docs synchronization: PASS.
- HND-0700 docs-only classifier: PASS.
- Full validation job 140244506231: PASS. The log includes STORCHK-0674 physical-parent matrix PASS and the existing synthetic safety/rental/financial contract tests.
- Target/platform jobs: 13/14 PASS; ESP32 FAIL job 140244506219 with fatal error mbedtls/sha256.h not found on the active v0.6 branch. This is an inherited target build blocker; this PR changes no ESP32 firmware source.
- The v0.4 Android emulator and x86 simulation jobs remain IN PROGRESS at this checkpoint. No aggregate Full workflow PASS is claimed.
- Signed production import remained SKIPPED. No deployment, device flash, reset, mount, block write, power cut or customer operation occurred.
- Status: CI VERIFIED for the synthetic preflight gate; physical issue #34 remains NOT TESTED; production NO-GO.

# PHX-HARDWARE — STORCHK-0674 physical-parent isolation

**Role:** PHX-HARDWARE  
**Task:** STORCHK-0674 / issue #34  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**Branch:** phoenix/hardware-storage-preflight-device-separation-20261126-utc23  
**Source/test SHA:** cb07904ccbedaeeb93e7eb763dc3c795e7e90c9f  
**PR:** #356 OPEN / DRAFT / UNMERGED

## Reproduced defect

The previous guard compared mountinfo major:minor values. Two sibling partitions on one physical disk have different major:minor identities, so the scratch partition could share the same underlying device as root/overlay/boot and still pass.

Test-only commit 660660aebc164fdc1958547d0d5e8f82656fd47e produced expected RED: run 45918235002, job 140242498187, failed with unsafe physical-parent layout accepted for a scratch sibling partition sharing the root disk.

## Correction

- Added tools/v060_lab_block_parent_guard.sh.
- Resolve direct block partitions through /sys/dev/block/<major:minor> and compare their parent whole-device major:minor identities.
- Require the scratch mount source to resolve to a direct partition.
- Compare scratch against root, overlay upper storage, ROM and boot mount parents.
- For overlayfs root, compare through the separately identified /overlay upper storage.
- Fail closed on missing sysfs identity, virtual block paths, device-mapper/RAID/slave-backed topology and unsupported ancestry.
- The on-device wrapper reads only the live /proc/self/mountinfo and /sys; no test override is exposed by the wrapper.

## Exact CI

- Expected RED: [#45918235002](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45918235002), job 140242498187.
- Fixed source/test SHA: cb07904ccbedaeeb93e7eb763dc3c795e7e90c9f.
- Focused push: [#45918491229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45918491229), job 140243305697 — PASS.
- Focused PR: [#45918494920](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45918494920), job 140243318268 — PASS.
- Both exact-source jobs verify expected and actual checkout SHA equality.
- Test matrix covers separate parent pass; sibling partitions sharing root, overlay and boot; whole-disk scratch; non-partition scratch; device-mapper; missing sysfs; overlayfs-root comparison.
- Logs explicitly retain SIMULATED_ONLY=1, PHYSICAL_POWER_CUT_VERIFIED=0 and CUSTOMER_INSTALL_AUTHORIZED=0.

## Full integration

- Push Full #45918491238 validation job 140243453805 failed handover freshness because this canonical handover had not yet been committed.
- PR Full #45918494903 was in progress when this handover was prepared. Its final result must be read at exact docs head; no aggregate Full PASS is claimed.

## Evidence boundary and limitations

The test uses synthetic mountinfo and fake sysfs. It does not mount a filesystem, write to a block device, power-cycle hardware, or touch customer data. Sysfs ancestry is not proof of separate enclosure/controller, physical disposability, or actual power-loss durability. Unsupported layouts fail closed. Issue #34 physical acceptance remains NOT TESTED; production remains NO-GO.

## Next exact action

Obtain exact-docs-head focused and Full CI; request PHX-QA review and PHX-MASTER assignment/integration-matrix update. Keep PR #356 DRAFT and unmerged. Do not authorize physical trial or release.

