# PHX-PISONET #197 — opened serial HANDLE identity (draft NO-GO)

## Provenance and scope

- Actual source: `src/BlazePisonet.SoftTimer/SerialHardware.cs`, Git blob `af15d41c22ab8ed6a507e38fed3ccdfc40f4054f`; added real `OpenedSerialHandleIdentity.cs` fail-closed boundary.
- Test fake: `tests/NativeSerialPinFaultLab/FakeOsAndAppTypes.cs`, Git blob `3f3b3603f259ac52fde6765b70c2820b68bdb120`; **only fake** opened serial instances expose `OpenedPhysicalPnp`. No OS driver exposes that property in production.
- Test code and native Windows workflow are first-party new work, not third-party copied code. Windows interoperability design references are Microsoft documentation only:
  - https://learn.microsoft.com/en-us/windows-hardware/drivers/install/guid-devinterface-comport
  - https://learn.microsoft.com/en-us/windows-hardware/drivers/serports/device-interface-publication-sercx
  - https://learn.microsoft.com/en-us/dotnet/api/system.io.ports.serialport.basestream
- No third-party library, source, license or package was imported. Microsoft's recommendation is `GUID_DEVINTERFACE_COMPORT` to discover/access a COM interface rather than trusting a mutable legacy COM number.

## Changes actually implemented

`SerialHardware.Connect` validates **after** `SerialPort.Open()` but **before** committing `_port`. For `ExactDevice` an unavailable, unverifiable or mismatched same-opened-handle identity causes an exception followed by detaching/closing/disposing the provisional candidate. The production `OpenedSerialHandleIdentity.TryVerify` currently returns **false for all real ports**, because no supported same-opened-handle/PnP-instance proof exists through the existing `SerialPort` public APIs. It does not treat WMI, COM naming, QueryDosDevice, VID/PID, second-handle lookup or a cached PnP claim as sufficient.

All monetary `TryClaimCoin` and post-await `IsCoinSessionCurrent` operations additionally require `_openedHandleVerified`, cleared on disconnect. ManualPort/AutoCompatible/LegacyCom1 diagnostic pulse callbacks can remain for compatibility but **cannot authorize a paid coin claim**.

## Evidence (synthetic native Windows tests, not physical)

Native run [#40882169119](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40882169119), exact test HEAD `6197cd1bdaeb4b35049015ea4cfa6e8c1fdba8f8`, completed SUCCESS: 34/34 deterministic serial/PnP cases (formerly five #197 identity REDs) now pass. Fake opened adapter A passes a positive CTS pulse; swapped B and unknown CTS/RI/reconnect are rejected; ManualPort diagnostic pulse remains visible but one-time monetary claim is denied. Cleanup, CTS V4/V5, immutable reentrant event ownership, #216 original async attribution/ACK checks and Windows product build also passed; build 0 errors.

**This proves first-party C# fail-closed control flow under fake OS APIs only, NOT real Windows opened kernel HANDLE identity or device acceptance.**

## Actual remaining implementation blocker

To enable legitimate production coin input, implement and independently review a **handle-owning native Windows transport** that enumerates `GUID_DEVINTERFACE_COMPORT` interfaces and independently validates unique PnP instance ID, opens the exact selected device-interface symbolic path using `CreateFileW`, and performs all CTS/DSR/RING reads/events **through the same owned native HANDLE**, with removal/close and stale-session invalidation. Do not open a separately named COM path after interface selection and assume the handles refer to the same device. Add Windows device-interface API, negative swap/removal/power-loss, and legitimate same-device positive controls; then real adapters/USB-RS232, physical coin pulses and finance/witness/signed ACK review. No unreviewed private .NET SerialStream reflection, driver assumptions, false provenance, or broad enable toggle.

## Release status

P0 production NO-GO. The #197 **simulation** REDs are corrected, but actual physical identity proof is still absent and ExactDevice remains intentionally disabled for financial use. V1 `target_nonce` echoed ACK is not an original-event-signed paid receipt. No merge, release, device flash, publication, money or credentials.
