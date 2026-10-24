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
int lifecycleAccepted = 0;
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
    if (lifecycleAccepted != 0) throw new Exception("Old-session unfinished pulse was credited");
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

var cases = new (string Name, int Actual, int Expected)[] {
    ("normal_50ms_cts", normal.Accepted, 1),
    ("active_low_read_error_no_coin", falseCoin.Accepted, 0),
    ("active_low_selected_pin_read_error_no_coin", selectedPinFault.Accepted, 0),
    ("active_low_detach_reconnect_idle_no_coin", detachedWhileIdle.Accepted, 0),
    ("active_high_fault_mid_pulse_disarms", interruptedDuringPulse.Accepted, 0),
    ("delayed_callback_misses_pulse", delayed.Accepted, 0),
    ("ring_without_measured_duration", ring.Accepted, 1),
    ("ring_after_unrelated_dsr_preserves_legacy_event", ringAfterOtherPin.Accepted, 1),
    ("old_session_incomplete_cts_not_credited", 0, 0),
    ("fresh_cts_after_reconnect", freshAfterReconnect, 1),
    ("stale_ring_after_disconnect", staleRingAfterDisconnect, 0),
    ("stale_ring_after_replacement", staleRingAfterReplacement, 0),
    ("fresh_ring_after_stale_sender", freshRingAfterStale, 1),
    ("stale_cts_callback_does_not_cancel_fresh_pulse", staleCtsDuringFreshPulse, 1)
};
bool diagnosticFailed = false;
foreach (var c in cases) {
    var pass = c.Actual == c.Expected;
    Console.WriteLine($"{(pass ? "REPRODUCED" : "UNEXPECTED")} {c.Name}: accepted={c.Actual}, expected_source_behavior={c.Expected}");
    diagnosticFailed |= !pass;
}
if (diagnosticFailed) {
    Console.Error.WriteLine("NATIVE_DIAGNOSTIC_MISMATCH: source behavior changed or harness failed.");
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
Console.WriteLine("NATIVE_SOURCE_DIAGNOSTIC_PASS: 14/14 controlled in-process C# API traces met proposed read-error guard contract; delayed callback and RI capture risks remain. NOT hardware or real Windows serial driver.");
return 0;
