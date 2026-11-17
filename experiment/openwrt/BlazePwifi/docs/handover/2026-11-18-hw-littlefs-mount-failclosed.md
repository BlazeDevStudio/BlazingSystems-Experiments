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
