# PHX-L-APPS #164 — proposed read-error guard (stacked test + app-only draft)

**THIS BRANCH IS NOT MERGED OR RELEASED.** Builds the previously source-linked native C# fake-OS harness from test-only PR #176 into a narrowly scoped source correction. Previous owner-closed PR #175 stays unmerged and is not revived.

## Source RED → proposed GREEN contract

- Historical **real C# source-linked expected RED** (unmodified `SerialHardware.cs`): PR #176 at SHA `9f29470f7ba6287b140b19a7b1db856f6e9638b5`, [Windows #40100726703](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40100726703). Native controlled API status read failure with physically idle active-low CTS emitted one spurious `CoinPulseAccepted`; the test explicitly expected safety RED.
- This proposed guarded branch tests **eight actual C# source-linked fake-OS traces**: normal 50 ms CTS accepted (1), unrelated pin event during active-low CTS read exception (0), selected-pin CTS read exception (0), port Close/reopen with no coin (0), active-high mid-pulse read failure (0), delayed callback missing actual pulse (0; **still a known lost-pulse risk**), and Ring callback without pulse width (1; **still a known false-credit risk**), plus an unrelated DSR pin notification followed by Ring must retain one legacy Ring event (1; **compatibility only**, not qualified paid acceptance).
- `--diagnostic` must reproduce the exact eight expected results; `--safety-gate` must return 0 with `READ_ERROR_SAFETY_GREEN` for the four status-fault/detach scenarios. Both commands are mandatory in Windows CI. This is **only the no-false-credit-on-status-failure gate**, not general coin or safety acceptance.

```powershell
dotnet run --project experiment/windows/BlazePisonet-SoftTimer/tests/NativeSerialPinFaultLab/NativeSerialPinFaultLab.csproj -c Release -- --diagnostic
dotnet run --project experiment/windows/BlazePisonet-SoftTimer/tests/NativeSerialPinFaultLab/NativeSerialPinFaultLab.csproj -c Release --no-restore -- --safety-gate
```

### Proposed implementation boundary

In `SerialHardware.cs`, paid coin capture uses a new trusted/unknown modem-level read rather than inverting a UI-oriented `false` on read failure. A failure/closed/stale session **disarms current pulse**, then requires a verified idle input before rearming. No change to billing/ledger writer, admin configuration, COM-binding modes, packet wire protocol, Android apps, firmware or production credentials. Existing read-only UI method `GetSignal()` retains its published Boolean contract.

**Further blockers:** serial callback scheduling is not a hardware edge timestamp; control-line notifications are not guaranteed queued; Ring event acceptance without measured level remains unqualified. No real serial adapter/coin acceptor, driver timing, electrical level/coin inhibit, monotonic sequence or durability, real 150 power cuts, 24h/30-device soak has been tested. No paid acceptance/release/merge.

## Native test limits

The test compiles **actual C# application `SerialHardware.cs` source** against in-process stand-ins for `System.IO.Ports`, `System.Management` and minimal config. It runs .NET methods and synthetic callbacks, not real Windows serial chip timing. No external proprietary code or kernel driver was imported. MASTER/VERIFY must review exact source and CI before any integration decision.


## 2026-10-24 compatibility-test correction after first GREEN
First proposed guard exact Windows source `bc6baee3` succeeded in [#40102803254](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40102803254), proving 7/7 C# source-linked fake-OS traces and 4/4 no-false-credit fault checks. Independent source review found a **potential new regression**: when RI is configured, a non-Ring pin change fell through the tri-state status path, disarming subsequent legacy RI events. The new eighth C# test first pins expected preexisting RI behavior; source commit `cdd9f9cef1d94df67c25319a0fb19c80bbdb1a11` avoids invoking level-read/disarm for a non-Ring RI notification. This maintains compatibility while leaving event-only RI counting **explicitly commercially unsafe**. The 8/8 test and successor CI must be checked at the exact new commit before passing this regression. No real adapter, coin slot or money tested.

## 2026-10-25 UTC21 — strict ExactDevice identity proposal (stacked review-only)

This child branch preserves the parent PR #191 **17/19 source-linked C# RED** as historical evidence. The original source-selected recycled COM9 when a pinned PnP device vanished and the first of two duplicate PnP identifiers. Actual parent [Windows #40132072186](https://github.com/BlazingSystems/BlazingSystems-Experiments/actions/runs/40132072186) **FAILED at 17/19**, downstream installer skipped, not a general build failure.

Seven added deterministic source-linked identity cases (total target **26/26**) cover: exact PnP across COM9 → COM14 positive; stable USB serial+matching VID/PID across renumbering positive; duplicate USB serial negative; wrong VID negative; unqualified bare USB serial negative; legacy ExactDevice with COM number only negative; false Windows location-derived USB instance ID negative. All tests use synthetic device records and the actual linked C# `SerialDiscovery`, not WMI hardware.

Source change is narrowly restricted to `SerialDiscovery.ResolveExact` and `ExtractUsbSerial` in `SerialHardware.cs`. `ResolveExact` accepts only a unique pinned PnP candidate with matching recorded vendor/product (when present), or one USB serial qualified by both VID and PID; no implicit `LastKnownComPort` fallback. `ExtractUsbSerial` rejects instance strings containing `&`, rather than truncating a location path. Existing intentionally selected `ManualPort` continues to work; an old COM-only ExactDevice profile must be deliberately rebound or switched to manual, not auto-credited. Coin/ACK authority, firmware, Android and paid-event schema are untouched. This change is a DRAFT, not integrated into Phoenix development.

**Pending evidence at time of writing:** 26/26 native diagnostic, win-x64 warnings-as-errors build, and NSIS install/uninstall must be verified from the **new exact branch-head Windows Actions**; no hardware coin acceptance claimed. Parent #176/#184/#190/#191 remain DRAFT UNMERGED; owner-closed #175 remains closed; alternative identity/session PR #147/#149 exists only in CLOSED UNMERGED #90. Further session-atomic callback/paid event binding and RI pulse/driver timing remain unresolved. P0 #31/#32/#43/#34 NO-GO.

## 2026-10-25 UTC22 — Open-time COM adapter swap negative (TEST-ONLY)

The new isolated child branch from draft #195 adds a deterministic fake WMI/SerialPort mapping change between `SerialDiscovery.Enumerate()` and `SerialPort.Open()`. The actual `SerialHardware.Connect()` is still compiled unmodified into the .NET 8 native C# fixture. It now checks 28 synthetic cases: 26 unchanged parent cases, one stable Open-time adapter positive, and one swapped adapter negative. The negative **must refuse connection**; until actual Windows CI logs are inspected, it is a proposed RED, not an observed failure. This does not authenticate USB hardware and does not prove a real Windows race, physical coin acceptance or financial safety. No application production source or financial core change; MASTER/VERIFY integration review remains mandatory.
