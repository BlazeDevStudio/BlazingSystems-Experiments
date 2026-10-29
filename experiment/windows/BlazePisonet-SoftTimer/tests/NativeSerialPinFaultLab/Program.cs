// PHX-L-APPS #164: actual production C# SerialHardware.cs linked into .NET 8.
// The fake OS API gives deterministic control of modem pin levels and read faults.
// --diagnostic verifies the vulnerable source behavior is reproducible.
// --safety-gate deliberately exits 2 while the active-low false credit exists.
// NEVER treat a green diagnostic test as proof that a real coin acceptor is safe.
using BlazePisonet.SoftTimer;
using System.IO.Ports;

static (int Accepted, bool Connected) Run(bool initialCts, bool activeHigh,
    ModemSignal selectedSignal, Action<SerialPort> inject, int minimumPulseMs = 10)
{
    SerialPort.InitialCtsLevel = initialCts;
    var cfg = new AppConfig {
        CoinInputSignal = selectedSignal,
        CoinInputActiveHigh = activeHigh,
        MinimumPulseMs = minimumPulseMs
    };
    using var sut = new SerialHardware();
    int accepted = 0;
    sut.CoinPulseAccepted += () => accepted++;
    if (!sut.Connect(cfg)) throw new Exception("Fake COM9 failed to connect");
    var port = SerialPort.LastCreated ?? throw new Exception("Fake serial instance absent");
    inject(port);
    return (accepted, sut.IsConnected);
}

// PHX-L-APPS #164: isolated source-linked failed-open ownership regression.
// A thrown SerialPort.Open is not a connection; candidate, subscriptions and
// OS resources must be cleaned even though _port was never assigned.
// Exit 2 = SOURCE SAFETY RED; 3 = INVALID harness/positive; 0 = narrow GREEN.
if (args.Contains("--open-failure-safety-gate", StringComparer.Ordinal))
{
    System.Management.ManagementObjectSearcher.FakeDevices =
        Array.Empty<System.Management.ManagementObject>();
    SerialPort.InitialCtsLevel = false;
    SerialPort.PhysicalPnpAtOpen = null;
    SerialPort.ThrowOnNextOpen = true;
    var cfg = new AppConfig { SerialSelection = SerialSelectionMode.ManualPort,
        ManualComPort = "COM9", CoinInputSignal = ModemSignal.Cts, MinimumPulseMs = 10 };
    using var subject = new SerialHardware();
    int accepted = 0;
    subject.CoinPulseAccepted += () => accepted++;
    bool firstConnected = subject.Connect(cfg);
    var failedPort = SerialPort.LastCreated;
    if (firstConnected || failedPort is null || failedPort.OpenAttemptCount != 1 ||
        failedPort.IsOpen || SerialPort.ThrowOnNextOpen || subject.IsConnected)
    {
        Console.Error.WriteLine("OPEN_FAILURE_INCONCLUSIVE: failure injection or initial status invalid");
        return 3;
    }
    bool disposedAfterFault = failedPort.WasDisposed;
    bool unsubscribedAfterFault = failedPort.PinSubscriberCount == 0;
    if (!subject.Connect(cfg))
    {
        Console.Error.WriteLine("OPEN_FAILURE_INCONCLUSIVE: valid retry failed");
        return 3;
    }
    var goodPort = SerialPort.LastCreated;
    if (goodPort is null || ReferenceEquals(goodPort, failedPort) || !goodPort.IsOpen)
    {
        Console.Error.WriteLine("OPEN_FAILURE_INCONCLUSIVE: replacement port not distinct/open");
        return 3;
    }
    goodPort.CtsLevel = true;
    goodPort.Raise(SerialPinChange.CtsChanged);
    Thread.Sleep(70);
    goodPort.CtsLevel = false;
    goodPort.Raise(SerialPinChange.CtsChanged);
    if (accepted != 1)
    {
        Console.Error.WriteLine($"OPEN_FAILURE_INCONCLUSIVE: real C# positive pulse={accepted}, expected=1");
        return 3;
    }
    Console.WriteLine($"OPEN_FAILURE_CONTROL_PASS: injectedOpenAttempts=1 retryOpen=1 positivePulses={accepted}");
    if (!disposedAfterFault || !unsubscribedAfterFault)
    {
        Console.Error.WriteLine($"OPEN_FAILURE_RESOURCE_RED: disposed={disposedAfterFault}, pinUnsubscribed={unsubscribedAfterFault}; unowned failed COM candidate leaked");
        return 2;
    }
    Console.WriteLine("OPEN_FAILURE_RESOURCE_GREEN: failed candidate disposed and detached; positive reconnect pulse accepted");
    return 0;
}

var normal = Run(false, true, ModemSignal.Cts, port => {
    port.CtsLevel = true;
    port.Raise(SerialPinChange.CtsChanged);
    Thread.Sleep(50);
    port.CtsLevel = false;
    port.Raise(SerialPinChange.CtsChanged);
});
var falseCoin = Run(true, false, ModemSignal.Cts, port => {
    // The physical CTS remains high (idle) throughout this entire test.
    // An unrelated DSR event triggers a CTS read that throws; the source's
    // catch returns false and active-low inversion interprets it as asserted.
    port.ThrowOnCtsRead = true;
    port.Raise(SerialPinChange.DsrChanged);
    Thread.Sleep(50);
    port.ThrowOnCtsRead = false;
    port.Raise(SerialPinChange.DsrChanged);
});
var selectedPinFault = Run(true, false, ModemSignal.Cts, port => {
    // Also ensure the selected CTS notification cannot manufacture a coin.
    port.ThrowOnCtsRead = true;
    port.Raise(SerialPinChange.CtsChanged);
    Thread.Sleep(50);
    port.ThrowOnCtsRead = false;
    port.Raise(SerialPinChange.CtsChanged);
});
var detachedWhileIdle = Run(true, false, ModemSignal.Cts, port => {
    // SerialPort loss must never be mistaken for a low-active coin pulse.
    port.Close();
    port.Raise(SerialPinChange.CtsChanged);
    Thread.Sleep(50);
    port.Open();
    port.Raise(SerialPinChange.CtsChanged);
});
var interruptedDuringPulse = Run(false, true, ModemSignal.Cts, port => {
    // Previously, a read exception after a true assertion fabricated a
    // valid falling edge and accepted a coin with no verified pulse ending.
    port.CtsLevel = true;
    port.Raise(SerialPinChange.CtsChanged);
    Thread.Sleep(50);
    port.ThrowOnCtsRead = true;
    port.Raise(SerialPinChange.CtsChanged);
    port.ThrowOnCtsRead = false;
    port.CtsLevel = false;
    port.Raise(SerialPinChange.CtsChanged);
});
var delayed = Run(false, true, ModemSignal.Cts, port => {
    // Physical CTS was high for a pulse but returned low before callbacks ran.
    port.CtsLevel = true;
    Thread.Sleep(50);
    port.CtsLevel = false;
    port.Raise(SerialPinChange.CtsChanged);
    port.Raise(SerialPinChange.CtsChanged);
});
var ring = Run(false, true, ModemSignal.RingIndicator, port => {
    // No physical pulse duration is measured, yet the source supplies the
    // configured minimum width to its own debounce/acceptance function.
    port.Raise(SerialPinChange.Ring);
}, minimumPulseMs: 500);

var ringAfterOtherPin = Run(false, true, ModemSignal.RingIndicator, port => {
    // Preserve the existing RI event-only path: unrelated DSR notifications
    // should not disarm or fabricate a Ring event. Ring itself remains unsafe
    // for unattended paid coin input until measured duration is available.
    port.Raise(SerialPinChange.DsrChanged);
    port.Raise(SerialPinChange.Ring);
}, minimumPulseMs: 500);

// PHX-L-APPS #164: lifecycle cases are source-linked, in-process only.
// Deferred callbacks are manually injected after unsubscribe; this models a
// possible race and is NOT evidence that any Windows driver delivers it.
SerialPort.InitialCtsLevel = false;
var lifecycleCfg = new AppConfig { CoinInputSignal = ModemSignal.Cts, MinimumPulseMs = 10 };
int lifecycleAccepted = 0, oldSessionIncompletePulse = 0;
using (var sut = new SerialHardware()) {
    sut.CoinPulseAccepted += () => lifecycleAccepted++;
    if (!sut.Connect(lifecycleCfg)) throw new Exception("First lifecycle COM failed");
    var oldPort = SerialPort.LastCreated ?? throw new Exception("Missing first lifecycle port");
    oldPort.CtsLevel = true;
    oldPort.Raise(SerialPinChange.CtsChanged);
    Thread.Sleep(50);
    sut.Disconnect();
    if (!sut.Connect(lifecycleCfg)) throw new Exception("Second lifecycle COM failed");
    var newPort = SerialPort.LastCreated ?? throw new Exception("Missing second lifecycle port");
    newPort.CtsLevel = false;
    newPort.Raise(SerialPinChange.CtsChanged);
    // Incomplete pulse from old session MUST NOT become a new coin.
    oldSessionIncompletePulse = lifecycleAccepted;
    // A genuine complete pulse on the replacement port must still work.
    newPort.CtsLevel = true;
    newPort.Raise(SerialPinChange.CtsChanged);
    Thread.Sleep(50);
    newPort.CtsLevel = false;
    newPort.Raise(SerialPinChange.CtsChanged);
}
var freshAfterReconnect = lifecycleAccepted;

int staleRingAfterDisconnect = 0, staleRingAfterReplacement = 0, freshRingAfterStale = 0;
SerialPort.InitialCtsLevel = false;
var ringCfg = new AppConfig { CoinInputSignal = ModemSignal.RingIndicator, MinimumPulseMs = 10 };
using (var sut = new SerialHardware()) {
    int count = 0;
    sut.CoinPulseAccepted += () => count++;
    if (!sut.Connect(ringCfg)) throw new Exception("First RI COM failed");
    var oldPort = SerialPort.LastCreated ?? throw new Exception("Missing first RI port");
    var deferred = oldPort.CaptureDeferredPinCallback();
    sut.Disconnect();
    deferred(SerialPinChange.Ring);
    staleRingAfterDisconnect = count;
    if (!sut.Connect(ringCfg)) throw new Exception("Second RI COM failed");
    var newPort = SerialPort.LastCreated ?? throw new Exception("Missing second RI port");
    deferred(SerialPinChange.Ring);
    staleRingAfterReplacement = count;
    newPort.Raise(SerialPinChange.Ring);
    freshRingAfterStale = count;
}

int staleCtsDuringFreshPulse = 0;
SerialPort.InitialCtsLevel = false;
using (var sut = new SerialHardware()) {
    sut.CoinPulseAccepted += () => staleCtsDuringFreshPulse++;
    if (!sut.Connect(lifecycleCfg)) throw new Exception("First CTS COM failed");
    var oldPort = SerialPort.LastCreated ?? throw new Exception("Missing first CTS port");
    var deferred = oldPort.CaptureDeferredPinCallback();
    if (!sut.Connect(lifecycleCfg)) throw new Exception("Second CTS COM failed");
    var newPort = SerialPort.LastCreated ?? throw new Exception("Missing second CTS port");
    newPort.CtsLevel = true;
    newPort.Raise(SerialPinChange.CtsChanged);
    Thread.Sleep(50);
    deferred(SerialPinChange.DsrChanged);
    newPort.CtsLevel = false;
    newPort.Raise(SerialPinChange.CtsChanged);
}

// PHX-L-APPS #164: deterministic reentrant session-crossing negative test.
// SignalChanged is a public callback invoked BEFORE OnPinChanged reads CTS.
// A listener may reconnect synchronously, replacing _port/_config. The old
// callback must not then use its old cfg to sample the NEW port and invent
// an edge. New COM9 stays electrically idle (CTS high, active-low mode).
// This tests the actual linked SerialHardware.cs; no production source edit.
int reentrantReconnectIdleFalseCoin = 0;
SerialPort.InitialCtsLevel = false;
var beforeReconnectCfg = new AppConfig {
    CoinInputSignal = ModemSignal.Cts, CoinInputActiveHigh = true, MinimumPulseMs = 10
};
var afterReconnectCfg = new AppConfig {
    CoinInputSignal = ModemSignal.Cts, CoinInputActiveHigh = false, MinimumPulseMs = 10
};
using (var sut = new SerialHardware()) {
    sut.CoinPulseAccepted += () => reentrantReconnectIdleFalseCoin++;
    if (!sut.Connect(beforeReconnectCfg)) throw new Exception("Initial reentrant COM failed");
    var previous = SerialPort.LastCreated ?? throw new Exception("Missing previous COM");
    bool didReconnect = false;
    sut.SignalChanged += () => {
        if (didReconnect) return;
        didReconnect = true;
        SerialPort.InitialCtsLevel = true; // new port's idle CTS, never changes
        if (!sut.Connect(afterReconnectCfg)) throw new Exception("Reentrant reconnect failed");
    };
    // Unrelated old-session notification triggers the reconnect callback.
    previous.Raise(SerialPinChange.DsrChanged);
    if (!didReconnect) throw new Exception("Reentrant callback did not reconnect");
    var replacement = SerialPort.LastCreated ?? throw new Exception("Missing replacement COM");
    if (ReferenceEquals(previous, replacement)) throw new Exception("COM not replaced");
    if (!replacement.CtsLevel) throw new Exception("Replacement CTS was not idle-high");
    Thread.Sleep(50);
    // Still idle, but an old callback may have fabricated a pulse start.
    replacement.Raise(SerialPinChange.CtsChanged);
}

// PHX-L-APPS #164 UTC19: TEST-ONLY exact identity negative fixture.
// Actual production SerialDiscovery.ResolveExact is compiled into this .NET
// project; these device records are synthetic, not real WMI or USB hardware.
// An explicit ManualPort selection remains valid, but an ExactDevice binding
// MUST NOT silently move to a different adapter just because COM9 was reused.
var pinned = new AppConfig {
    SerialSelection = SerialSelectionMode.ExactDevice,
    PreferredPnpDeviceId = @"USB\VID_1234&PID_5678\COIN-A",
    PreferredUsbSerial = "COIN-A", PreferredVid = "1234", PreferredPid = "5678",
    LastKnownComPort = "COM9"
};
var originalDevice = new SerialDeviceInfo("COM9", "Original adapter", "Lab",
    @"USB\VID_1234&PID_5678\COIN-A", "1234", "5678", "COIN-A");
var replacementDevice = new SerialDeviceInfo("COM9", "Different adapter", "Lab",
    @"USB\VID_1234&PID_5678\COIN-B", "1234", "5678", "COIN-B");
var duplicateDevice = new SerialDeviceInfo("COM10", "Duplicate claimed identity", "Lab",
    @"USB\VID_1234&PID_5678\COIN-A", "1234", "5678", "COIN-A");
var exactComReused = SerialDiscovery.Resolve(pinned, new[] { replacementDevice });
var exactDuplicate = SerialDiscovery.Resolve(pinned, new[] { originalDevice, duplicateDevice });
var exactUnique = SerialDiscovery.Resolve(pinned, new[] { originalDevice });
var manual = new AppConfig { SerialSelection = SerialSelectionMode.ManualPort, ManualComPort = "COM9" };
var manualExplicit = SerialDiscovery.Resolve(manual, new[] { replacementDevice });
// PR #194 proposed exact-device admission hardening: all below execute
// SerialDiscovery.Resolve from the linked real C# application source. Synthetic
// USB descriptors only, no live WMI/USB or paid acceptance.
var movedPort = new SerialDeviceInfo("COM14", "Same physical adapter", "Lab",
    @"USB\VID_1234&PID_5678\COIN-A", "1234", "5678", "COIN-A");
var bogusVendor = new SerialDeviceInfo("COM14", "Counterfeit descriptor", "Lab",
    @"USB\VID_AAAA&PID_5678\COIN-A", "AAAA", "5678", "COIN-A");
var duplicateSerial1 = new SerialDeviceInfo("COM14", "Adapter 1", "Lab",
    @"USB\VID_1234&PID_5678\COIN-A", "1234", "5678", "COIN-A");
var duplicateSerial2 = new SerialDeviceInfo("COM15", "Adapter 2", "Lab",
    @"USB\VID_1234&PID_5678\COIN-A-OTHERPNP", "1234", "5678", "COIN-A");
var usbOnlyPinned = new AppConfig {
    SerialSelection = SerialSelectionMode.ExactDevice,
    PreferredUsbSerial = "COIN-A", PreferredVid = "1234", PreferredPid = "5678",
    LastKnownComPort = "COM9"
};
var unqualifiedSerial = new AppConfig {
    SerialSelection = SerialSelectionMode.ExactDevice,
    PreferredUsbSerial = "COIN-A", LastKnownComPort = "COM9"
};
var comOnlyPinned = new AppConfig {
    SerialSelection = SerialSelectionMode.ExactDevice,
    LastKnownComPort = "COM9"
};
var reflectedExtractor = typeof(SerialDiscovery).GetMethod("ExtractUsbSerial",
    System.Reflection.BindingFlags.NonPublic | System.Reflection.BindingFlags.Static)
    ?? throw new Exception("Actual USB serial parser not found");
var locationGeneratedSerial = (string?)reflectedExtractor.Invoke(null,
    new object[] { @"USB\VID_1234&PID_5678\5&ABCDEF&0&2" });
var realUsbSerial = (string?)reflectedExtractor.Invoke(null,
    new object[] { @"USB\VID_1234&PID_5678\COIN-A" });

var identityCases = new (string Name, bool Resolved, bool ExpectedResolved)[] {
    ("exact_pnp_missing_com_recycled_must_refuse", exactComReused is not null, false),
    ("exact_duplicate_pnp_must_refuse_ambiguity", exactDuplicate is not null, false),
    ("exact_unique_pnp_control", exactUnique?.PortName == "COM9", true),
    ("manual_com9_explicit_control", manualExplicit?.PortName == "COM9", true),
    ("exact_same_pnp_renumbered_com14_control", SerialDiscovery.Resolve(pinned, new[] { movedPort })?.PortName == "COM14", true),
    ("exact_usb_serial_reenumerated_unique_control", SerialDiscovery.Resolve(usbOnlyPinned, new[] { movedPort })?.PortName == "COM14", true),
    ("exact_usb_serial_duplicate_must_refuse", SerialDiscovery.Resolve(usbOnlyPinned, new[] { duplicateSerial1, duplicateSerial2 }) is not null, false),
    ("exact_usb_serial_wrong_vid_must_refuse", SerialDiscovery.Resolve(usbOnlyPinned, new[] { bogusVendor }) is not null, false),
    ("exact_usb_serial_without_vidpid_must_refuse", SerialDiscovery.Resolve(unqualifiedSerial, new[] { movedPort }) is not null, false),
    ("exact_com_only_legacy_must_refuse", SerialDiscovery.Resolve(comOnlyPinned, new[] { replacementDevice }) is not null, false),
    ("usb_location_instance_must_not_be_stable_serial", !string.IsNullOrEmpty(locationGeneratedSerial) || realUsbSerial != "COIN-A", false)
};

// PHX-L-APPS #164 UTC22: TEST-ONLY Open-time COM adapter substitution.
// The real SerialHardware.Connect() is linked; only WMI/SerialPort are fake.
// WMI reports the pinned adapter on COM9, then the fake COM9 physical
// mapping is changed before SerialPort.Open(). The selected descriptor
// remains stale even though the newly opened adapter is different.
// This is NOT evidence of actual Windows driver behavior or real coin money.
var openPinnedPnp = @"USB\VID_1234&PID_5678\COIN-A";
var openReplacementPnp = @"USB\VID_1234&PID_5678\COIN-B";
System.Management.ManagementObjectSearcher.FakeDevices = new[] {
    new System.Management.ManagementObject("Coin Adapter (COM9)", "Lab", openPinnedPnp, "COM9")
};
var openConfig = new AppConfig {
    SerialSelection = SerialSelectionMode.ExactDevice,
    PreferredPnpDeviceId = openPinnedPnp,
    PreferredUsbSerial = "COIN-A", PreferredVid = "1234", PreferredPid = "5678",
    CoinInputSignal = ModemSignal.Cts
};
SerialPort.InitialCtsLevel = false;
SerialPort.PhysicalPnpAtOpen = openReplacementPnp;
int substitutedAdapterPulseAccepted = 0;
bool connectedToSubstitutedAdapter;
using (var sut = new SerialHardware()) {
    sut.CoinPulseAccepted += () => substitutedAdapterPulseAccepted++;
    connectedToSubstitutedAdapter = sut.Connect(openConfig);
    var opened = SerialPort.LastCreated ?? throw new Exception("Missing swapped COM9");
    if (opened.OpenedPhysicalPnp != openReplacementPnp)
        throw new Exception("Fake COM mapping did not change at Open");
    if (connectedToSubstitutedAdapter && sut.ConnectedDevice?.PnpDeviceId != openPinnedPnp)
        throw new Exception("Unexpected descriptor: stale WMI selection was not retained");
    if (!connectedToSubstitutedAdapter &&
        (!opened.WasDisposed || opened.PinSubscriberCount != 0))
        throw new Exception("Swapped HANDLE candidate leaked resources or PinChanged subscriber");
    // TEST ONLY: a substituted physical adapter must never be allowed to
    // manufacture a coin callback merely because COM9 opened successfully.
    // This is synthetic CTS, not a real coin or paid ledger operation.
    if (connectedToSubstitutedAdapter) {
        opened.CtsLevel = true;
        opened.Raise(SerialPinChange.CtsChanged);
        Thread.Sleep(50);
        opened.CtsLevel = false;
        opened.Raise(SerialPinChange.CtsChanged);
    }
}
var rejectedSwapped = SerialPort.LastCreated ??
    throw new Exception("Swapped Open candidate not created");
if (rejectedSwapped.WasDisposed != true || rejectedSwapped.PinSubscriberCount != 0)
    throw new Exception("Swapped device failed-open cleanup broken");
SerialPort.PhysicalPnpAtOpen = openPinnedPnp;
bool connectedToStableAdapter;
int stableExactOpenedHandleCoins = 0;
using (var sut = new SerialHardware()) {
    sut.CoinPulseAccepted += () => stableExactOpenedHandleCoins++;
    connectedToStableAdapter = sut.Connect(openConfig);
    var opened = SerialPort.LastCreated ?? throw new Exception("Missing stable COM9");
    if (opened.OpenedPhysicalPnp != openPinnedPnp)
        throw new Exception("Fake stable COM mapping invalid");
    if (connectedToStableAdapter) {
        opened.CtsLevel = true;
        opened.Raise(SerialPinChange.CtsChanged);
        Thread.Sleep(55);
        opened.CtsLevel = false;
        opened.Raise(SerialPinChange.CtsChanged);
    }
}
SerialPort.PhysicalPnpAtOpen = null;
System.Management.ManagementObjectSearcher.FakeDevices =
    Array.Empty<System.Management.ManagementObject>();
var openTimeCases = new (string Name, bool Resolved, bool ExpectedResolved)[] {
    ("exact_open_time_adapter_swap_must_refuse", connectedToSubstitutedAdapter, false),
    ("exact_open_time_stable_adapter_control", connectedToStableAdapter, true)
};

// PHX-L-APPS #164 UTC04: an opened COM handle with UNVERIFIABLE physical
// identity must never be a coin admission authority. WMI still reports the
// selected pinned adapter; the fake opened handle provides NO identity proof.
// Rejecting Connect or allowing read-only connection with coin inhibit are
// both acceptable. This is a deterministic API model, NOT a real OS handle.
System.Management.ManagementObjectSearcher.FakeDevices = new[] {
    new System.Management.ManagementObject("Coin Adapter (COM9)", "Lab", openPinnedPnp, "COM9")
};
SerialPort.PhysicalPnpAtOpen = null;
SerialPort.InitialCtsLevel = false;
int unverifiableHandlePulseAccepted = 0;
bool unverifiableHandleConnected;
using (var sut = new SerialHardware()) {
    sut.CoinPulseAccepted += () => unverifiableHandlePulseAccepted++;
    unverifiableHandleConnected = sut.Connect(openConfig);
    if (unverifiableHandleConnected) {
        var opened = SerialPort.LastCreated ?? throw new Exception("Missing unverified COM9");
        if (opened.OpenedPhysicalPnp is not null)
            throw new Exception("Fake opened handle unexpectedly had physical identity proof");
        opened.CtsLevel = true;
        opened.Raise(SerialPinChange.CtsChanged);
        Thread.Sleep(50);
        opened.CtsLevel = false;
        opened.Raise(SerialPinChange.CtsChanged);
    }
}
var rejectedUnknownCts = SerialPort.LastCreated ??
    throw new Exception("Unknown CTS candidate not created");
if (rejectedUnknownCts.WasDisposed != true ||
    rejectedUnknownCts.PinSubscriberCount != 0)
    throw new Exception("Unverified CTS candidate leaked resources");
// PHX-L-APPS UTC05 TEST ONLY: the event-only RI path must also be coin-
// inhibited when a successful COM Open has NO opened-handle identity proof.
// The existing CTS negative does not exercise the Ring-specific path.
// Fake OS mapping only; no real Windows driver or paid credit is modeled.
System.Management.ManagementObjectSearcher.FakeDevices = new[] {
    new System.Management.ManagementObject("Coin Adapter (COM9)", "Lab", openPinnedPnp, "COM9")
};
SerialPort.PhysicalPnpAtOpen = null;
int unknownHandleRingPulseAccepted = 0;
bool unknownHandleRingConnected;
using (var sut = new SerialHardware()) {
    var ringUnknownConfig = new AppConfig {
        SerialSelection = SerialSelectionMode.ExactDevice,
        PreferredPnpDeviceId = openPinnedPnp,
        PreferredUsbSerial = "COIN-A", PreferredVid = "1234", PreferredPid = "5678",
        CoinInputSignal = ModemSignal.RingIndicator, MinimumPulseMs = 500
    };
    sut.CoinPulseAccepted += () => unknownHandleRingPulseAccepted++;
    unknownHandleRingConnected = sut.Connect(ringUnknownConfig);
    if (unknownHandleRingConnected) {
        var opened = SerialPort.LastCreated ?? throw new Exception("Missing unverified RI COM9");
        if (opened.OpenedPhysicalPnp is not null)
            throw new Exception("Fake RI opened handle unexpectedly has identity proof");
        opened.Raise(SerialPinChange.Ring);
    }
}
System.Management.ManagementObjectSearcher.FakeDevices =
    Array.Empty<System.Management.ManagementObject>();
SerialPort.PhysicalPnpAtOpen = null;

System.Management.ManagementObjectSearcher.FakeDevices =
    Array.Empty<System.Management.ManagementObject>();
SerialPort.PhysicalPnpAtOpen = null;

// PHX-L-APPS UTC06 TEST ONLY: a verified first ExactDevice session cannot
// authorize a second opened COM handle with UNKNOWN physical adapter identity.
// A deferred callback from the old session must not promote the new session.
// The fake OpenedPhysicalPnp field is NOT a real Windows handle identity API.
System.Management.ManagementObjectSearcher.FakeDevices = new[] {
    new System.Management.ManagementObject("Coin Adapter (COM9)", "Lab", openPinnedPnp, "COM9")
};
SerialPort.PhysicalPnpAtOpen = openPinnedPnp;
SerialPort.InitialCtsLevel = false;
int unknownReconnectPulseAccepted = 0;
using (var sut = new SerialHardware()) {
    sut.CoinPulseAccepted += () => unknownReconnectPulseAccepted++;
    if (!sut.Connect(openConfig))
        throw new Exception("Fake verified initial COM9 session failed");
    var first = SerialPort.LastCreated ?? throw new Exception("Missing first COM9");
    if (first.OpenedPhysicalPnp != openPinnedPnp)
        throw new Exception("Initial fake adapter identity was not pinned");
    var staleCallback = first.CaptureDeferredPinCallback();
    sut.Disconnect();
    SerialPort.PhysicalPnpAtOpen = null;
    if (sut.TryReconnect(openConfig)) {
        var second = SerialPort.LastCreated ?? throw new Exception("Missing reopened COM9");
        if (ReferenceEquals(first, second) || second.OpenedPhysicalPnp is not null)
            throw new Exception("Reopened fake COM9 unexpectedly proved adapter identity");
        staleCallback(SerialPinChange.CtsChanged);
        second.CtsLevel = true;
        second.Raise(SerialPinChange.CtsChanged);
        Thread.Sleep(50);
        second.CtsLevel = false;
        second.Raise(SerialPinChange.CtsChanged);
    }
}
System.Management.ManagementObjectSearcher.FakeDevices =
    Array.Empty<System.Management.ManagementObject>();
SerialPort.PhysicalPnpAtOpen = null;

var cases = new (string Name, int Actual, int Expected)[] {
    ("exact_stable_opened_handle_positive_coin", stableExactOpenedHandleCoins, 1),
    ("exact_open_time_swapped_adapter_must_not_emit_coin_pulse", substitutedAdapterPulseAccepted, 0),
    ("exact_open_time_unverifiable_handle_must_not_emit_coin_pulse", unverifiableHandlePulseAccepted, 0),
    ("exact_open_time_unverifiable_handle_ring_must_not_emit_coin_pulse", unknownHandleRingPulseAccepted, 0),
    ("exact_reconnect_unknown_handle_after_stale_callback_must_not_emit_coin_pulse", unknownReconnectPulseAccepted, 0),
    ("normal_50ms_cts", normal.Accepted, 1),
    ("active_low_read_error_no_coin", falseCoin.Accepted, 0),
    ("active_low_selected_pin_read_error_no_coin", selectedPinFault.Accepted, 0),
    ("active_low_detach_reconnect_idle_no_coin", detachedWhileIdle.Accepted, 0),
    ("active_high_fault_mid_pulse_disarms", interruptedDuringPulse.Accepted, 0),
    ("delayed_callback_misses_pulse", delayed.Accepted, 0),
    ("ring_without_measured_duration", ring.Accepted, 1),
    ("ring_after_unrelated_dsr_preserves_legacy_event", ringAfterOtherPin.Accepted, 1),
    ("old_session_incomplete_cts_not_credited", oldSessionIncompletePulse, 0),
    ("fresh_cts_after_reconnect", freshAfterReconnect, 1),
    ("stale_ring_after_disconnect", staleRingAfterDisconnect, 0),
    ("stale_ring_after_replacement", staleRingAfterReplacement, 0),
    ("fresh_ring_after_stale_sender", freshRingAfterStale, 1),
    ("stale_cts_callback_does_not_cancel_fresh_pulse", staleCtsDuringFreshPulse, 1),
    ("reentrant_reconnect_idle_cts_must_not_credit", reentrantReconnectIdleFalseCoin, 0)
};
bool diagnosticFailed = false;
foreach (var c in identityCases) {
    var pass = c.Resolved == c.ExpectedResolved;
    Console.WriteLine($"{(pass ? "REPRODUCED" : "UNEXPECTED")} {c.Name}: resolved={c.Resolved}, expected_resolved={c.ExpectedResolved}");
    diagnosticFailed |= !pass;
}
foreach (var c in openTimeCases) {
    var pass = c.Resolved == c.ExpectedResolved;
    Console.WriteLine($"{(pass ? "REPRODUCED" : "UNEXPECTED")} {c.Name}: connected={c.Resolved}, expected_connected={c.ExpectedResolved}");
    diagnosticFailed |= !pass;
}
foreach (var c in cases) {
    var pass = c.Actual == c.Expected;
    Console.WriteLine($"{(pass ? "REPRODUCED" : "UNEXPECTED")} {c.Name}: accepted={c.Actual}, expected_source_behavior={c.Expected}");
    diagnosticFailed |= !pass;
}
if (diagnosticFailed) {
    Console.Error.WriteLine("NATIVE_DIAGNOSTIC_MISMATCH: source behavior changed or harness failed; identity negatives may be intentionally RED.");
    return 1;
}
if (args.Contains("--safety-gate", StringComparer.Ordinal)) {
    if (falseCoin.Accepted != 0 || selectedPinFault.Accepted != 0 || detachedWhileIdle.Accepted != 0 || interruptedDuringPulse.Accepted != 0) {
        Console.Error.WriteLine("READ_ERROR_SAFETY_RED: idle CTS fault/detach emitted CoinPulseAccepted.");
        return 2;
    }
    Console.WriteLine("READ_ERROR_SAFETY_GREEN: 4/4 status-error/detach scenarios emitted zero coin pulses; other capture risks remain.");
    return 0;
}
Console.WriteLine("NATIVE_SOURCE_DIAGNOSTIC_PASS: 32/32 controlled in-process C# API traces met proposed read-error guard contract; delayed callback and RI capture risks remain. NOT hardware or real Windows serial driver.");
return 0;
