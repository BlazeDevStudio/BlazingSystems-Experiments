# PHX-HARDWARE UTC03 — PSA initialization ordering and unsupported-major guard

**Date:** 2026-11-26 UTC03  
**Role:** PHX-HARDWARE  
**Repository:** BlazeDevStudio/BlazingSystems-Experiments  
**PR:** [#340 — OPEN / DRAFT / UNMERGED](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/340)  
**Branch:** `phoenix/hardware-prepoll-intake-deny-20261122-utc01`  
**Source/test SHA:** `d1380acf80c0b631c5814d746dca36b2fad7a986`  
**Handover update commit:** `b4d0b4ea67d12c399b596b55b2e2ec2d45a1355e`

## Change

Only `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/mbedtls_sha256_compat_lab.py` changed in the source/test commit. The lab now verifies PSA initialization occurs before SHA-256 computation and rejects three mutations: ignored PSA-init failure, hash-before-init, and removal of unsupported-major compile denial.

## Exact CI

| Workflow | Run / job | Result |
|---|---|---|
| Mbed TLS SHA256 compatibility guard | [45747199083](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747199083) / 139666018101 | PASS; seven fail-open mutations rejected |
| Poll preflight inhibit | [45747199112](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747199112) / 139666018314 | PASS; ESP8266 + ESP32, simulated |
| Quarantine append/readback | [45747199138](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747199138) / 139666018487 | PASS; 14/14 boot cases and 10/10 clear-commit cases per board, simulated |
| ESP8266 core 3.1.2 | [45747199174](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747199174) / 139666018959 | PASS |
| ESP32 core 3.3.13 | [45747199118](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747199118) / 139666018483 | PASS; 78% program storage |
| ESP32 core 4.0.0 | [45747192648](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747192648) / 139665996232 | PASS; 82% program storage; application binary SHA-256 `ea6bfb5fbf31f4fca3ed7942e92cede58b75c1d087cd74ac15414d9d568f0a2e` |

Full push [#45747192586](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747192586) and PR [#45747199081](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/45747199081) were still running at handover time. Validation and all 14 target/platform jobs had passed on the push run; x86 simulation artifact upload and Android emulator remained in progress. Do not claim Full PASS until terminal status is rechecked.

## Reproducibility issue

The ESP32 `.ino` blob is unchanged from the earlier core-4 build, and both logs report Arduino CLI 1.6.0 / ESP32 core 4.0.0, but binary SHA-256 changed from `f9489e1df0d075cbfce549120c37af2778c53cb055f165c14a1d790623293c31` to `ea6bfb5fbf31f4fca3ed7942e92cede58b75c1d087cd74ac15414d9d568f0a2e`. Cause not established; the workflow does not retain both binaries. RELEASE review is requested for complete toolchain pinning and artifact retention.

## Blockers

- Active v0.6 remains at `2fbd2475e9f54878c316fa7cea2f228386b0e859`; synchronous poll still precedes coin sampling and unsigned response fields are consumed.
- Main CGI poll/register lacks `response_sig`; CORE owns the authenticated response contract.
- #348's Mbed TLS 4 header failure remains separate; no provider port was made.
- #239/#254/#283 remain OPEN / DRAFT; #177 P0, #266 cleanup gate, #31/#32/#34/#43 and physical acceptance remain open.
- COE #26 remains frozen. Private Drive registry v11 remains NOT RECOVERED; no Google Drive connector was exposed.

**No production sketch, shared API, finance, relay policy, signer, witness, updater or COE destination source changed. No flash, reset, migration, merge, release or deployment.**

**Status:** focused CI VERIFIED; SIMULATED guards; physical acceptance NOT TESTED; HARDWARE ACCEPTED = NO; PRODUCTION READY = NO-GO.

**Next:** recheck Full runs to terminal state; request RELEASE/QA review; wait for CORE's authenticated response contract before changing response trust or actuation.
