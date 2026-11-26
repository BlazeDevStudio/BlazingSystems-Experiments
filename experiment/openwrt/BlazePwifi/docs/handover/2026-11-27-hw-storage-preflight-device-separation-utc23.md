# PHX-HARDWARE — STORCHK-0674 root/overlay device separation

**Status:** focused synthetic regression CI VERIFIED; Full integration IN PROGRESS. **Physical acceptance:** NOT TESTED. **Production:** NO-GO.
**Issue:** https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/34
**DRAFT PR:** https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/356
**Branch:** phoenix/hardware-storage-preflight-device-separation-20261126-utc23
**Source/test SHA:** cd767cdf06ce3984c7e134c7d980b22b73f58844
**Docs head at readback:** 3295381dc3a6f9051ccef40d938130b33ab7afd4

## Focused evidence

RED: push run 45912530609 job 140224038590 and PR run 45912560098 job 140224138127 failed as expected when scratch reused the root device.
GREEN: push run 45912851366 job 140225058949 and PR run 45912857510 job 140225078166 PASS at the exact source/test SHA. Docs-head focused PR run 45913088792 job 140225825590 PASS at docs head 3295381.

## Full integration readback

Full PR run 45913088776 is still IN_PROGRESS. Handover freshness, HND-0700, CI-0701 and the first 121 validation steps passed. Validation job 140225968163 is still at step 122. ESP8266 and Android PASS; 13/14 target/platform jobs PASS. ESP32 job 140225968098 FAILS with missing mbedtls/sha256.h. No terminal Full result is available.

The ESP32 failure is inherited from active v0.6 and is not caused by this PR, which changes no firmware sketch. The focused guard's CI evidence is synthetic only; distinct major:minor does not prove separate physical media or owner-confirmed disposability.

## NEXT EXACT ACTION

Inspect terminal run 45913088776; request Master to add #356 to role assignments/integration matrix and QA to review the protected-mount identity guard. Keep DRAFT and unmerged. No physical trial without owner approval, isolated noncustomer media, authenticated power telemetry and recovery signoff.
