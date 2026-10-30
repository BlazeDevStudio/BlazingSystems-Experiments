# PHX-PISONET — Windows COM device-interface owned-handle prototype

Status: **DRAFT / SOURCE-LINKED WINDOWS GREEN / NOT COIN ADMISSION / NO PHYSICAL PROOF**

## Source and provenance

- Current owner repository: `BlazeDevStudio/BlazingSystems-Experiments`; branch `phoenix/pisonet-native-com-interface-20261030`, based on existing DRAFT PR #238 HEAD `0496482a22c28eab30d2850b72d13db366ae969e`.
- New actual production-source file: `src/BlazePisonet.SoftTimer/NativeComInterfaceTransport.cs` at Git blob `5905082568cfb0a2638c5c61f097a837898f761f`. New native test: `tests/NativeComInterfaceHandleLab`. New *branch-only*, test-only workflow `.github/workflows/phoenix-pisonet-native-com-interface.yml`.
- No third-party code or library was copied. Own P/Invoke declarations implement Windows native APIs documented by Microsoft:
  - [GUID_DEVINTERFACE_COMPORT](https://learn.microsoft.com/en-us/windows-hardware/drivers/install/guid-devinterface-comport)
  - [SetupDiGetDeviceInterfaceDetailW](https://learn.microsoft.com/en-us/windows/win32/api/setupapi/nf-setupapi-setupdigetdeviceinterfacedetailw)
  - [SetupDiGetDeviceInstanceIdW](https://learn.microsoft.com/en-us/windows/win32/api/setupapi/nf-setupapi-setupdigetdeviceinstanceidw)
  - [GetCommModemStatus](https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getcommmodemstatus)
  - [Device interface enumeration](https://learn.microsoft.com/en-us/windows-hardware/drivers/install/enumerating-installed-device-interface-classes)

## Implementation

`WindowsNativeComPlatform` enumerates **present** `GUID_DEVINTERFACE_COMPORT` interfaces through SetupAPI and retrieves each interface's device-instance ID and opaque symbolic path. `NativeComInterfaceSession.TryOpenExact` demands exactly one interface matching the operator-pinned original PnP instance ID, rejects ambiguous/shared paths, then invokes `CreateFileW` on **that exact device-interface path**. It does **not** substitute a mutable `COM9` alias, reopen the port under `SerialPort`, inspect private .NET `SerialStream` handles, or equate a later WMI lookup with the opened handle.

The session takes single ownership of the `SafeFileHandle`. It verifies a fresh enumeration after open, probes `GetCommModemStatus` on that same opened handle and uses it for later CTS/DSR/carrier diagnostic reads. A removed/changed/duplicate/unknown interface, invalid handle, unsupported modem status or exception must be rejected and the candidate closed. Session disposal closes the same handle. The after-open SetupAPI refresh is **not** independent cryptographic or kernel attestation of an opened handle. Interface-path selection plus same-handle IO is the supported Windows ownership model, subject to actual driver testing.

The new class is a **diagnostic transport foundation only**. Existing `SerialHardware.Connect` and `OpenedSerialHandleIdentity.TryVerify(SerialPort,...)` are NOT changed or bypassed; actual `ExactDevice` paid admission stays **fail closed**. No actual CTS event capture or minted `SerialCoinAcceptance` is wired to the new native handle. A point-in-time `GetCommModemStatus` read does not prove an accurate measured coin pulse, RI duration or reliable driver notification.

## Exact native evidence

[Windows workflow run #40911340730](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40911340730) completed **SUCCESS** at source+test HEAD `41e15c445ea2fab4d7d893e7c2bdd007083d8912`, after a test-only nullable analysis error in an earlier run was fixed. Its .NET8 native CLR test compiled the **unmodified production-source transport** and passed:

- Synthetic exact interface A -> owned fake handle -> initial status and CTS=1/DSR=0 on the SAME fake SafeFileHandle, then closed on dispose.
- Synthetic missing identity, duplicate device instance ID, shared path, swap/removal at open (candidate closed), same-instance path retarget, unavailable modem status (candidate closed), invalid opened handle and empty operator pin all denied.
- Real Windows SetupAPI `GUID_DEVINTERFACE_COMPORT` read-only enumeration succeeded on runner, **count=1**. Deliberately nonexistent PnP instance was rejected. No physical interface was opened by the test.
- Original #219 CTS V4=0/V5=1, #221 failed-Open cleanup, reentrant/async ownership and #216 controller/target/nonce ACK regressions all GREEN. Production Windows app `dotnet build` success with 0 errors.

**Native test's matched-handle positive is in-process synthetic, not real USB/RS232 coin hardware.** Windows runner present-interface count is observational only; it was not opened or signaled.

## NEXT exact P0 integration and physical proof

1. Review native SetupAPI structure sizes, x86/x64, error paths, race and device-interface matching on supported Windows/adapter driver versions. Establish same-handle **event notification** with `SetCommMask` / `WaitCommEvent` or a bounded verified sampling loop, and status read with `GetCommModemStatus`. Do not create a second `SerialPort` for money.
2. Integrate **the same session handle** with an immutable accepted-event session/target/nonce claim; preserve callback outside lock, verified-idle rearm, pulse width/debounce, detach/reconnect epoch and source-hash regressions. Keep RI denied unless a measured/proven policy explicitly admits it.
3. On physical Windows PC using real USB-RS232 adapter: verify matched ExactDevice positive CTS pulses and wrong/swapped adapter with reused COM number, unknown driver identity, disconnect/replug during open and callbacks, and status read failures. Confirm no coin is credited after detach/replace, and successful original physical device resumes only after verified idle.
4. Financial CORE still requires authenticated controller config, signed event-specific ACK/replay provenance, protected witness, power-cut/soak evidence and independent production review.

**NO-GO:** No physical adapter acceptance, real paid coin, flash, release, merge, signing keys or production enablement. Existing LIGHT PRs and three canonical handovers must remain intact.


## 2026-10-30 — Bounded same-owned-HANDLE CTS observation continuation (PHX-PISONET-J)

New original production-source `src/BlazePisonet.SoftTimer/NativeComPulseCapture.cs` Git blob **`882b5cce4b75b342dd623707e24943e05843f6a7`**, and source-linked Windows fixture `tests/NativeComInterfaceHandleLab/NativePulseCaptureCases.cs` Git blob **`5107c034e6d70f421c56224f72372653bf34985c`** (literal source compiled via lab project, no copied source model). The code extends *only* PR #255; parent PR #238 / original `SerialHardware` / money admission are unchanged.

`NativeComPulseCapture` takes ownership of an already opened `NativeComInterfaceSession` and requires explicit `SampleOnce()` calls by a caller-provided scheduler. Each sample invokes `NativeComInterfaceSession.TryReadSignal(ModemSignal.Cts)`, which reads `GetCommModemStatus` via the SAME exact interface `SafeFileHandle` opened by `CreateFileW`, never WMI/COM alias or a separately reopened serial handle. Microsoft API contract: https://learn.microsoft.com/en-us/windows/win32/api/winbase/nf-winbase-getcommmodemstatus . This is bounded *level sampling*, **NOT SetCommMask/WaitCommEvent continuous event notification**, not an implemented scheduler and not physical proof that pulses cannot occur between samples.

Immutable `NativeObservedPulse` records the original native session reference, generation, event sequence, pinned instance ID, exact device-interface path, monotonic start/end and measured sampled pulse width. Every bind/rebind/disconnect/status error/dispose invalidates the old generation and all unclaimed observations. `TryClaimObserved` is a one-time in-process diagnostic ownership check (not a paid event); callbacks dispatch **outside** the capture lock. Verified idle is mandatory initially and after accepted pulse, clock rollback or missed sample gap; early/late/unknown pulses are denied, not treated as a low transition. An invalid modem-status read permanently retires and closes its owned handle, requiring an explicit newly verified bind. Timestamping uses monotonic `Stopwatch` via injectable test clock; sample gap, width, and debounce are bounded and configurable.

**Native CI proof:** [Windows run #40943179215/job #123691679093](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/40943179215), completed **SUCCESS** at exact pre-documentation head `7fe880b0168f972dc8f96d9c13c8c9e416040289`. Actual CLR test executed the unmodified new source, with synthetic legitimate CTS pulse 30ms, 1/0 one-time duplicate claims, initial-high inhibition followed by valid idle/positive pulse, missed sample gap denial+recovery, status-error/unplug cleanup, cross-thread callback A→B rebind stale A denial plus legitimate B positive, short/long pulse and clock rollback rejection. Read-only Windows SetupAPI enumeration remained green. The same job ran the existing V4=0/V5=1, failed-Open, reentrant/immutable and #216 original async controller/target/nonce tests, plus Windows production build with **0 errors**. These are fake modem levels and fake handles; a genuine serial device was not opened or signaled.

**Remaining exact real-adapter gate:** review the bounded sampling cadence and missed-edge problem under real Windows USB-RS232/serial drivers; implement and independently validate `SetCommMask(EV_CTS)` / `WaitCommEvent` on the owned handle (or prove a sampling schedule accurately observes the desired physical pulse durations), plus removal cancellation and safe reconnect under physical unplug/replug. Verify legitimate matched physical adapter CTS positive and same-COM swapped/unverifiable negative, power cuts, driver status errors, GPIO polarity, idle threshold, pulse width across actual hardware. Keep `NativeComPulseCapture` disconnected from `SerialHardware`/timer/central credit, and leave financial admission fail-closed until independent review, hardware evidence, signed original-event receipt and protected witness. No payment, release, merge, code-signing key or physical coin operation was performed.


## 2026-10-30 — PHX-PISONET-K: QA cached-success-after-removal correction

**Exact original QA gap:** Open the pinned A interface successfully. After session creation, remove/replace the published device interface with B while keeping the old fake A handle valid; make its `TryReadModemStatus` return a *successful cached CTS=1*. Previous unplug/status-fault tests did not execute this scenario. A cache-success must be rejected, and no diagnostic claim can occur until a new exact-device session rebind and verified-low idle.

**Minimal source changes** on the same isolated draft PR #255:

- Production native transport `NativeComInterfaceTransport.cs`, blob `e844a6408af89951ba4bcef13367b3212e4dac9f`: after **each** `GetCommModemStatus` call—even successful cached CTS—the same `NativeComInterfaceSession` performs a fresh SetupAPI `EnumeratePresent` check requiring exactly one original pinned device instance ID and exactly one original device-interface path. A missing, replaced, duplicate, invalid or unverifiable path retires and disposes the original opened `SafeFileHandle`; all reads fail closed, never treating unknown as CTS low.
- Production diagnostic capture `NativeComPulseCapture.cs`, blob `25f1b2f6a31d9745063efcd5d8f7e296f91b5369`: `TryClaimObserved` rechecks the original session's interface presence at **claim time**, closing invalid original handle, clearing all unclaimed observations, and advancing generation before denying a queued/stale event.
- Literal-source-linked test `NativePulseCaptureCases.cs`, blob `6f8519fb748590eda10fd7b18d7f1991007e7026`: tests both a cached-success old-A sample after A→B interface removal (assert old handle *actually* returned an extra successful fake status read, then was closed, no stale event) and an already-dispatched observation where duplicate interface identity appears before its callback claims it. Newly opened pinned B cannot claim the old A event and must first rearm using a verified-low level before a legitimate positive observation.

**Executed exact source evidence:** [Windows run #41010121683, job #123914052710](https://github.com/BlazeDevStudio/BlazingSystems-Experiments/actions/runs/41010121683), **SUCCESS** at source/test head `c7a99a8ad3f9713701771cb8c70d656f0871e07d`. Log anchors:

```text
NATIVE_PULSE_CACHED_CTS_SUCCESS_REMOVED_A_DENIED_FRESH_B_POSITIVE_PASS
NATIVE_PULSE_AFTER_SAMPLE_DUPLICATE_INTERFACE_STALE_CLAIM_DENIED_PASS
NATIVE_OWNED_HANDLE_PULSE_SOURCE_GREEN: 8 deterministic positive/fault/rebind/presence suites; diagnostic only
V4_NATIVE_SOURCE_CTS_AFTER_SUCCESSFUL_SAMPLE: accepted=0, safe_expected=0
V5_NATIVE_SOURCE_FAILED_CTS_SAMPLE_RECONNECT: accepted=1, valid_pulse_expected=1
OPEN_FAILURE_RESOURCE_GREEN
NATIVE_COIN_EVENT_OWNERSHIP_GREEN
NATIVE_ASYNC_DISPATCH_SOURCE_GREEN
Build succeeded. 0 Error(s)
```

**Limitations unchanged:** This is a **synthetic fake-OS status and interface-enumeration** regression compiled on a real Windows runner, not a real unplugged USB-RS232 adapter; its fake handle returns user-controlled cached CTS. SetupAPI presence sampling is non-atomic relative to physical device removal and **is not an OS cryptographic binding to a real opened handle**. A real driver with stale enumeration or removal between identity checks still requires physical tests, actual same-handle event/cancellation handling and timing proof. Original `SerialHardware` and its real ExactDevice-money fail-closed gate are unchanged; no coin admission, release, merge, keys, payment or hardware operation. Three canonical handovers must remain append-only.
