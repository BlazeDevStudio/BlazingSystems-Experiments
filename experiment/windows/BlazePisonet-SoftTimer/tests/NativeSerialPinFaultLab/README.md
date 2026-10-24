# PHX-L-APPS #164 — proposed read-error guard (stacked test + app-only draft)

**THIS BRANCH IS NOT MERGED OR RELEASED.** Builds the previously source-linked native C# fake-OS harness from test-only PR #176 into a narrowly scoped source correction. Previous owner-closed PR #175 stays unmerged and is not revived.

## Source RED → proposed GREEN contract

- Historical **real C# source-linked expected RED** (unmodified `SerialHardware.cs`): PR #176 at SHA `9f29470f7ba6287b140b19a7b1db856f6e9638b5`, [Windows #40100726703](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40100726703). Native controlled API status read failure with physically idle active-low CTS emitted one spurious `CoinPulseAccepted`; the test explicitly expected safety RED.
- This proposed guarded branch tests **six actual C# source-linked fake-OS traces**: normal 50 ms CTS accepted (1), unrelated pin event during active-low CTS read exception (0), selected-pin CTS read exception (0), port Close/reopen with no coin (0), delayed callback missing actual pulse (0; **still a known lost-pulse risk**), and Ring callback without pulse width (1; **still a known false-credit risk**).
- `--diagnostic` must reproduce the exact six expected results; `--safety-gate` must return 0 with `READ_ERROR_SAFETY_GREEN` for the three fault/detach scenarios. Both commands are mandatory in Windows CI. This is **only the no-false-credit-on-status-failure gate**, not general coin or safety acceptance.

```powershell
dotnet run --project experiment/windows/BlazePisonet-SoftTimer/tests/NativeSerialPinFaultLab/NativeSerialPinFaultLab.csproj -c Release -- --diagnostic
dotnet run --project experiment/windows/BlazePisonet-SoftTimer/tests/NativeSerialPinFaultLab/NativeSerialPinFaultLab.csproj -c Release --no-restore -- --safety-gate
```

### Proposed implementation boundary

In `SerialHardware.cs`, paid coin capture uses a new trusted/unknown modem-level read rather than inverting a UI-oriented `false` on read failure. A failure/closed/stale session **disarms current pulse**, then requires a verified idle input before rearming. No change to billing/ledger writer, admin configuration, COM-binding modes, packet wire protocol, Android apps, firmware or production credentials. Existing read-only UI method `GetSignal()` retains its published Boolean contract.

**Further blockers:** serial callback scheduling is not a hardware edge timestamp; control-line notifications are not guaranteed queued; Ring event acceptance without measured level remains unqualified. No real serial adapter/coin acceptor, driver timing, electrical level/coin inhibit, monotonic sequence or durability, real 150 power cuts, 24h/30-device soak has been tested. No paid acceptance/release/merge.

## Native test limits

The test compiles **actual C# application `SerialHardware.cs` source** against in-process stand-ins for `System.IO.Ports`, `System.Management` and minimal config. It runs .NET methods and synthetic callbacks, not real Windows serial chip timing. No external proprietary code or kernel driver was imported. MASTER/VERIFY must review exact source and CI before any integration decision.

