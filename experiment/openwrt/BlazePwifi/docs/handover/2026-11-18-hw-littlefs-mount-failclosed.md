# PHX-HARDWARE handover — preserve pending evidence on LittleFS mount failure

**Date:** 2026-11-18 UTC21  
**Role:** PHX-HARDWARE  
**Task:** #177 / #266 — fail-closed LittleFS mount recovery  
**PR:** [#283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283) — OPEN / DRAFT / UNMERGED  
**Branch:** `cleanup/esp-firmware-hardening-and-quarantine-20261111`  
**Base:** `main@f4e8a891aed8af86d5fd315d28750a0ac3a7372b`  
**Source/test commit:** [90a9cf8623b54139dabe6ef5360f0a7da91a9519](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/90a9cf8623b54139dabe6ef5360f0a7da91a9519)

## Source-confirmed defect

The previous ESP32 setup called `LittleFS.begin(true)`; ESP32 LittleFS interprets the argument as format-on-mount-failure. The previous ESP8266 `initPendingStore()` explicitly called `LittleFS.format()` after a failed mount and retried the mount.

A failed mount can indicate transient I/O trouble or filesystem corruption while pending coin evidence still exists. Formatting at that point can erase `/pending.dat`, `/pending.new`, `/pending.bak`, or quarantine evidence. The controller's default-deny outputs reduce actuation risk but do not make destructive evidence loss acceptable.

## Firmware change

Both board sketches now use the same explicit initialization boundary:

- ESP32 has a dedicated `initPendingStore()` helper instead of inline setup initialization.
- Both boards call `LittleFS.begin()` without format-on-failure.
- Neither board calls `LittleFS.format()` automatically.
- `loadPending()` runs only after a successful mount.
- On mount failure, `fsReady` remains false, the critical diagnostic is emitted, and setup continues through the existing default-deny output path. No journal or quarantine file is intentionally deleted.

Changed firmware paths:
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/BlazePwifiVendo32.ino`
- `experiment/openwrt/BlazePwifi/esp8266/BlazePwifiVendo/BlazePwifiVendo.ino`

New hardware-owned host lab:
- `experiment/openwrt/BlazePwifi/esp32/BlazePwifiVendo32/littlefs_mount_failclosed_lab.py`

The lab extracts the exact `initPendingStore()` body from both sketches, compiles it against a fake LittleFS boundary, tests mount-failure and mount-success paths, and rejects both `begin(true)` and explicit-`format()` mutations. It never accesses physical flash.

## Test-first and verification status

**Pre-fix RED — local host C++ harness, exact source bodies:**
- ESP32: expected failure; mount failure became `fsReady=true` after format-on-failure.
- ESP8266: expected failure; explicit format/retry converted mount failure into a successful mount.
- Both failed the assertion that mount failure must remain unavailable and must not load pending state.

**Post-fix GREEN — local host C++ harness:**
- ESP32: mount failure preserved; mount success loads pending once.
- ESP8266: mount failure preserved; mount success loads pending once.
- Both boards rejected `LittleFS.begin(true)` and explicit-`LittleFS.format()` injected mutations.

These are **SIMULATED host results**, not physical LittleFS durability evidence.

Exact source/test commit `90a9cf8623b54139dabe6ef5360f0a7da91a9519` triggered [BlazePwifi build run #44182009870](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44182009870). At handover creation it was QUEUED; no Actions PASS is claimed yet. The existing workflow compiles both sketches, but does not invoke the new mount lab. PHX-QA is asked to wire this hardware-owned lab into its owned test entrypoint and independently run it at the exact PR head. No QA-owned test or release workflow was modified here.

## Coordination and remaining gates

- No shared API, financial schema, CGI producer, controller authorization contract, or QA-owned test file changed.
- Existing poll/register and coin dispatch remain default-deny. This fix does not authorize coin intake or replay.
- PR #317 / #318 remain a separate divergent pulse-drain stack; no rebase or composition occurred.
- Physical flash/boot recovery, electrical pulse/relay acceptance, 150 controlled power cuts, 30-device 24-hour soak, protected signer/witness, durable accounting/replay, v1-to-v2 migration and independent release signoff remain NOT TESTED or BLOCKED.

**Next exact action:** PHX-QA adds the new lab invocation to the QA-owned controller test entrypoint, runs it against the exact PR #283 head, and returns the independent job link. PHX-HARDWARE then reviews the exact result and preserves this no-auto-format behavior. Keep PR #283 DRAFT / UNMERGED / NO-GO.


## Latest exact-head CI update — 2026-11-17T21:42Z

The initial source commit `90a9cf8623b54139dabe6ef5360f0a7da91a9519` was followed by documentation-only head `a43ca007b1a7ef38cc278395ca12c5bb2ec656da`; the two firmware blobs and new lab are unchanged. Exact-head [Actions #44182117122](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44182117122) at `a43ca007...` reports:
- ESP8266 job `134389072926`: SUCCESS.
- ESP32 job `134389073268`: SUCCESS.
- Full validation job `134389072950`: SUCCESS.
- Target/platform matrix: 14/14 SUCCESS.
- Update bundle and completed browser/ESP/Ruijie/Orange Pi simulations: SUCCESS; x86 and Android emulator simulations were still running at checkpoint time.
- Production APK import/signing and production/release handoff stages: SKIPPED.

The new source-extracted mount lab is still not part of the workflow. Local C++ host failure injection passed on both board function bodies and rejected `begin(true)` plus explicit-format mutations, but this remains SIMULATED, not independent QA or physical durability evidence. PHX-QA must wire and run the lab at the exact current PR head.


## 2026-11-18 UTC01 — pending journal boot recovery

**Role:** PHX-HARDWARE  
**Task:** #177 / #266 — preserve pending-event evidence during boot recovery  
**PR:** [#283](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/pull/283), OPEN / DRAFT / UNMERGED  
**Source/test head:** [176d518dcfb17d40a77f37f299ff8247ade29a36](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/176d518dcfb17d40a77f37f299ff8247ade29a36)  
**Master coordination head observed:** [650c6e5991ed8ba30d82dd98216316b3ae3a3780](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/650c6e5991ed8ba30d82dd98216316b3ae3a3780)

#### Defects reproduced

The prior #283 boot loader selected the first valid file among /pending.dat, /pending.new and /pending.bak. It did not reject multiple candidates as ambiguous and could remove/rename candidates during recovery. The record reader used unbounded strlen() on fixed-size nonce/target arrays and accepted trailing bytes beyond sizeof(PendingRecord).

The local exact-source host harness reproduced these failures on both boards: 2/13 scenarios passed and 11/13 failed. Cases included multiple valid candidates, valid+corrupt candidates, invalid records without a recovery hold, .new/.bak rename, oversized files and an unterminated nonce read crossing into the target field.

#### Firmware correction

Both ESP32 and ESP8266 sketches now:

- require exact file size and exact record read;
- use bounded memchr() for nonce and target terminators;
- reject missing/short terminators and non-zero bytes after the first NUL;
- count all three pending candidate paths before selecting anything;
- latch fsReady=false and pendingReady=true when multiple candidates or an invalid candidate exist;
- preserve all candidate files on ambiguity/corruption;
- load exactly one valid candidate without renaming or deleting it.

Source commits:
- ESP32: [12252c1d1deaf7b30a056e88e0764081cae8bca6](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/12252c1d1deaf7b30a056e88e0764081cae8bca6)
- ESP8266: [8109cd12d0c46f61c4934cbab1dd7943d754e217](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/8109cd12d0c46f61c4934cbab1dd7943d754e217)
- New source-extracted lab: [449aefbd0986073c0bb63aaa7cb25c51d26caf63](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/449aefbd0986073c0bb63aaa7cb25c51d26caf63)
- Lab invocation: [760809dd7cab9a10b47a70e5b13a4997d2436343](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/760809dd7cab9a10b47a70e5b13a4997d2436343)
- Fixture correction: [741a84db0c298d497320fe9e4d884ceb3bec7e29](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/741a84db0c298d497320fe9e4d884ceb3bec7e29)
- Wrapper import correction: [176d518dcfb17d40a77f37f299ff8247ade29a36](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/commit/176d518dcfb17d40a77f37f299ff8247ade29a36)

#### Verification

**Local exact-source host harness — SIMULATED**
- Pre-fix: 2/13 pass, 11/13 fail per board.
- Post-fix: 13/13 pass ESP32; 13/13 pass ESP8266.

**Focused GitHub Actions — CI VERIFIED**
- [Run #44218225761](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44218225761)
- Exact checkout SHA: 176d518dcfb17d40a77f37f299ff8247ade29a36
- Job 134513313681: SUCCESS
- Quarantine append/readback: 13/13 per board.
- Pending-journal boot fail-closed: 13/13 per board.
- Both suites explicitly report SIMULATED ONLY.

The first focused run [#44218120535](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44218120535) failed because the wrapper omitted import sys. The import was added and the exact-head rerun above passed.

**Full BlazePwifi build — IN PROGRESS at handover update**
- [Run #44218225798](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/44218225798)
- ESP8266 job 134513431137: PASS.
- ESP32 job 134513431783: PASS.
- Validation job 134513431834: PASS.
- 13 of 14 platform/build jobs had completed successfully; Android job 134513431810 remained in progress.
- Update bundle 134514427909: PASS.
- Browser, ESP32, ESP8266 and Ruijie simulations: PASS; Orange Pi/x86 simulations still running.
- Production import/signing: SKIPPED.
- No overall Full workflow conclusion is claimed.

The validation PASS is not independent QA acceptance: Master notes that #283 already changes QA-owned tests/controllers.sh and v05_firmware_hardening_test.sh, and their static response_sig/|poll| checks do not prove positive authentication. This activation did not modify either QA-owned file. QA must review the PR's existing test changes and independently own any replacement tests.

#### Audit-lead status

The old unconditional-clear finding from comment 6883020442 is superseded in current source: quarantinePending() returns before clearPending() when appendQuarantineRecord() fails. The later no-retry-latch concern remains a future-enable blocker; current #283 has no active quarantinePending() callsite and automatic coin POST/retry/clear remain removed. Do not enable those paths without the CORE-approved authenticated producer/consumer and event-bound receipt/disposition contract.

The response_sig/poll references remain comments/static test tokens, not a working authentication contract. Positive register/poll admission remains disabled.

#### Coordination and release boundary

- PHX-MASTER latest coordination head 650c6e5991ed8ba30d82dd98216316b3ae3a3780 keeps #283/#317/#318 as separate candidates; no canonical stack selection is recorded.
- COE main remains a6513ab4412b4c014eee2863e45cbe32d06cb243; integration PR #26 remains DRAFT at b382d233ff06c8791b1028bed3c617cc7b670d12. No source migration or destination write occurred.
- Private Drive BLAZE_PROJECT_REGISTRY_v11_20261027.json remains unavailable through the exposed file-library search. No v5-v7 historical registry was substituted.
- No physical flash, device reset, coin pulse, relay test, live payment, production migration, signing, merge, release or deployment occurred.

**Next exact action:** PHX-QA reviews and independently runs the new boot-recovery lab and replaces static controller-token tests; PHX-MASTER records the canonical hardware stack selection; PHX-HARDWARE continues only after revalidating all selected heads. Keep #283 OPEN/DRAFT/UNMERGED and PRODUCTION NO-GO.
