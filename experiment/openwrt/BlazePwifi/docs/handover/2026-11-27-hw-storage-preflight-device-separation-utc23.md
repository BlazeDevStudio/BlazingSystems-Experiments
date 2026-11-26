# PHX-HARDWARE — STORCHK-0674 root/overlay device separation

**Status:** SIMULATED / FOCUSED CI VERIFIED. **Physical acceptance:** NOT TESTED. **Production:** NO-GO.
**Issue:** https://github.com/BlazeDevStudio/BlazingSystems-Experiments/issues/34
**DRAFT PR:** https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/356
**Branch:** phoenix/hardware-storage-preflight-device-separation-20261126-utc23
**Base:** active v0.6 audit foundation at 2fbd2475e9f54878c316fa7cea2f228386b0e859
**Test-only RED SHA:** 68907bfa993c1b6b635e41e0935193c80126b7ac
**Source/test GREEN SHA:** cd767cdf06ce3984c7e134c7d980b22b73f58844

## Change

The read-only mountinfo guard now requires exactly one root mount, rejects duplicate overlay/rom/boot records, rejects scratch major:minor reuse with root/overlay/rom/boot, and requires a separate overlay mount when root is overlayfs. Existing fixture/source/path/filesystem/private-marker checks remain.

## Exact tests

- RED push run 45912530609 job 140224038590: expected failure because scratch reused the root filesystem device.
- RED PR run 45912560098 job 140224138127: same expected failure.
- GREEN push run 45912851366 job 140225058949: PASS at exact source/test SHA cd767cdf06ce3984c7e134c7d980b22b73f58844.
- GREEN PR run 45912857510 job 140225078166: PASS at the same SHA.
- GREEN logs state SIMULATED_ONLY=1, PHYSICAL_POWER_CUT_VERIFIED=0 and CUSTOMER_INSTALL_AUTHORIZED=0.
- Full run 45912851358 validation job 140225122247 failed handover freshness because the source commit preceded this synchronization; remaining target jobs were in progress. PR Full run 45912857560 queued.

## Evidence limits

Only synthetic mountinfo text and private temporary directories were used. No mount/unmount, block write, physical power cut, coin, payment, migration or customer operation occurred. Distinct major:minor proves distinct mounted block-device identity only, not separate physical media or owner-confirmed disposability.

## NEXT EXACT ACTION

Request PHX-MASTER/PHX-QA review of PR #356, then inspect Full validation at the post-documentation head. Keep PR DRAFT and unmerged. Physical trials require owner-approved isolated equipment, independent media verification, authenticated power telemetry and recovery signoff.
