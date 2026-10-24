# PHX-L-APPS #164 — source-linked native C# modem-pin fault lab

**Test-only, no production application change.** `NativeSerialPinFaultLab.csproj` compiles the repository's **actual unmodified** `src/BlazePisonet.SoftTimer/SerialHardware.cs` with .NET 8. `FakeOsAndAppTypes.cs` replaces only the external `System.IO.Ports` and `System.Management` dependencies plus minimal application configuration/logging with in-process test doubles. No COM kernel driver, USB adapter, coin acceptor, money writer, device, or protected key is accessed.

The fixture is intentionally different from the earlier Python **behavioral model**: this test executes the actual C# source methods and callback handlers in the .NET CLR, while the OS-facing modem-status implementation remains fake. It is still **not** an actual Windows driver timing test or electrical pulse measurement.

## Commands

```powershell
dotnet run --project experiment/windows/BlazePisonet-SoftTimer/tests/NativeSerialPinFaultLab/NativeSerialPinFaultLab.csproj -c Release -- --diagnostic
dotnet run --project experiment/windows/BlazePisonet-SoftTimer/tests/NativeSerialPinFaultLab/NativeSerialPinFaultLab.csproj -c Release --no-restore -- --safety-gate
```

Diagnostic mode expects four *currently unsafe/limited source behaviors*, not four safe outcomes: one normal 50ms CTS pulse accepted; one **false** active-low coin after a transient status-read exception with CTS physically idle; one lost 50ms pulse whose callbacks arrive after release; and one ring notification accepted despite no duration measurement. If the source differs, diagnostic fails instead of manufacturing a pass.

Safety-gate mode is deliberately **expected RED exit 2** on the false-coin scenario. The Windows CI wrapper asserts this explicit exit, logs `EXPECTED_SAFETY_RED_CONFIRMED`, and does **not** claim the product is safe. If the code changes and no longer reproduces, update the diagnostic contract and turn this into a proper no-false-credit GREEN gate after independent review. Do not hide the expected RED behind the overall workflow success.

## Safety and limits

- No installed application source is modified; PR #175 remains **closed unmerged**.
- The fake COM9 device uses a controllable `CtsHolding` exception and in-process `PinChanged` event. It cannot establish Windows kernel event ordering, USB chip behavior, voltage isolation, lossless pulse capture or power-fail durability.
- A production repair must distinguish `unavailable/failed status read` from `valid false`, disarm capture on read failure or detach, and prove that no `CoinPulseAccepted` event occurs on errors. Do not treat a callback as a durable paid event.
- The fixture deliberately sleeps 50ms to exercise the actual `DateTimeOffset.UtcNow` width measurement. It tests only controlled process scheduling, not physical edge timestamps.
- Next: classify exact-source Windows CI and request MASTER/VERIFY review; if approved, implement a narrowly scoped fail-closed source change on a separate role branch and verify native C# safety GREEN. Hardware/electrical and financial acceptance are separate gates.
