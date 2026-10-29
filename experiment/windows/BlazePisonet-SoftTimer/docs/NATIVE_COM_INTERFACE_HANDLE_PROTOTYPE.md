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
