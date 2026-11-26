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
