
## 2026-11-27 — STORCHK-0674 physical-parent isolation

- Role/task: PHX-HARDWARE / STORCHK-0674 / DRAFT PR #356.
- Test-only RED commit: 660660aebc164fdc1958547d0d5e8f82656fd47e; run 45918235002 job 140242498187 failed as expected because a sibling partition sharing the root disk was accepted.
- Source/test GREEN commit: cb07904ccbedaeeb93e7eb763dc3c795e7e90c9f.
- Focused push run 45918491229 job 140243305697 PASS; focused PR run 45918494920 job 140243318268 PASS; exact expected/actual checkout SHA matched.
- New guard resolves sysfs parent identity, requires a direct scratch partition, rejects same-parent root/overlay/ROM/boot layouts, whole-disk scratch, missing sysfs identity and virtual/stacked topology.
- Synthetic cases only; SIMULATED_ONLY=1; PHYSICAL_POWER_CUT_VERIFIED=0; CUSTOMER_INSTALL_AUTHORIZED=0.
- Full push run 45918491238 validation job 140243453805 failed handover freshness before this checkpoint was committed. PR Full run 45918494903 was still in progress at readback. No Full PASS claimed.
- Physical acceptance NOT TESTED; production NO-GO.
- NEXT ACTION: rerun exact-head Full after canonical handover update; request independent QA and Master matrix review; no physical trial or merge.


## 2026-11-27 UTC00 — exact-docs-head Full validation update

- Run 45918825520 at docs head 11f406a89ef4c5ae56c97b89678df6d737f1edbd; source/test SHA cb07904ccbedaeeb93e7eb763dc3c795e7e90c9f.
- CI-0701 and HND-0700 PASS; Full validation job 140244506231 PASS, including STORCHK-0674 physical-parent matrix.
- 13/14 target/platform jobs PASS; ESP32 job 140244506219 FAILS with mbedtls/sha256.h missing on the active v0.6 branch. No ESP32 source changed in this task.
- v0.4 Android emulator and x86 simulation still in progress; no aggregate Full PASS.
- Physical acceptance NOT TESTED; production NO-GO.

