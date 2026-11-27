## PHX-HARDWARE UTC00 — STORCHK-0674 physical-parent isolation exact-head checkpoint

**Source/test commit:** cb07904ccbedaeeb93e7eb763dc3c795e7e90c9f  
**Branch:** phoenix/hardware-storage-preflight-device-separation-20261126-utc23  
**DRAFT PR #356:** OPEN / UNMERGED.  
**Focused push:** [#45918491229](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45918491229), job 140243305697 — PASS.  
**Focused PR:** [#45918494920](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45918494920), job 140243318268 — PASS.

The test-only regression at 660660aebc164fdc1958547d0d5e8f82656fd47e produced expected RED in push run [#45918235002](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45918235002), job 140242498187: a scratch sibling partition on the root disk was accepted because major:minor values differed. This is the reproduced defect.

The correction resolves /sys/dev/block/<major:minor> to a direct block partition and its parent whole-device identity. The on-device wrapper now compares scratch parent identity against root, overlay upper storage, ROM and boot mounts; requires scratch to be a partition; and fails closed when sysfs identity is missing or topology is virtual, device-mapper, RAID/slave-backed or otherwise unsupported. The overlay-root case uses its separately identified /overlay upper storage. The wrapper hardcodes the live /sys and /proc/self/mountinfo sources; synthetic overrides are confined to the host test invoking the helper directly.

The synthetic matrix passes: separate scratch disk accepted; sibling partitions sharing root, overlay and boot parents rejected; whole-disk scratch rejected; device-mapper and missing-sysfs layouts rejected; overlay-root upper-storage comparison passes. Exact checkout SHA matched in both focused workflows. Logs state SIMULATED_ONLY=1, PHYSICAL_POWER_CUT_VERIFIED=0, CUSTOMER_INSTALL_AUTHORIZED=0.

Full run [#45918491238](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45918491238) push validation job 140243453805 failed the handover-freshness gate because this checkpoint had not yet been committed. PR Full run [#45918494903](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45918494903) was still running at this readback. No aggregate Full PASS is claimed.

**Limitations:** sysfs ancestry is a kernel block-topology check, not proof of separate enclosure, controller, physical disposability, or power-loss durability. Unsupported NVMe/virtual/device-mapper/RAID layouts may block until separately audited. The CI fixture uses synthetic mountinfo and fake sysfs only. No real mount, block write, power cut, coin, payment, migration or customer operation occurred.

**Next exact action:** obtain exact-docs-head focused/Full results, request PHX-QA review and PHX-MASTER role-matrix update, and keep PR #356 DRAFT. Issue #34 physical acceptance remains NOT TESTED; production remains NO-GO.

# PHX-HARDWARE — STORCHK-0674 root/overlay device separation

**Focused exact-head CI:** PASS. **Full integration:** IN PROGRESS. **Physical acceptance:** NOT TESTED. **Production:** NO-GO.
**Issue #34:** https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/34
**DRAFT PR #356:** https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/356
**Branch:** phoenix/hardware-storage-preflight-device-separation-20261126-utc23
**Source/test SHA:** cd767cdf06ce3984c7e134c7d980b22b73f58844
**Docs head at latest focused PASS:** b453272130e2839f404db4adb42eacd7a76f5fcb

Focused PR run 45913560571 job 140227322280 PASS at exact docs head b453. Log confirms expected/actual checkout SHA match, STORCHK-0674 PASS, SIMULATED_ONLY=1, PHYSICAL_POWER_CUT_VERIFIED=0 and CUSTOMER_INSTALL_AUTHORIZED=0.

Full run 45913088776 at docs head 3295381 remains in progress: handover and first 121 validation steps passed; Android and ESP8266 passed; 13/14 target/platform builds passed; ESP32 failed missing mbedtls/sha256.h; validation job 140225968163 not terminal. New Full run 45913560627 at docs head b453 is in progress, no terminal result yet.

NEXT EXACT ACTION: inspect terminal Full runs 45913088776 and 45913560627; obtain Master assignment update and independent QA review. Keep PR DRAFT and unmerged. Physical trial requires owner-approved noncustomer equipment, independent media verification, authenticated power telemetry and recovery signoff.
