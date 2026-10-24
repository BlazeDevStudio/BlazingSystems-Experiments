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

var cases = new (string Name, int Actual, int Expected)[] {
    ("normal_50ms_cts", normal.Accepted, 1),
    ("active_low_read_error_no_coin", falseCoin.Accepted, 0),
    ("active_low_selected_pin_read_error_no_coin", selectedPinFault.Accepted, 0),
    ("active_low_detach_reconnect_idle_no_coin", detachedWhileIdle.Accepted, 0),
    ("delayed_callback_misses_pulse", delayed.Accepted, 0),
    ("ring_without_measured_duration", ring.Accepted, 1)
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
    if (falseCoin.Accepted != 0 || selectedPinFault.Accepted != 0 || detachedWhileIdle.Accepted != 0) {
        Console.Error.WriteLine("READ_ERROR_SAFETY_RED: idle CTS fault/detach emitted CoinPulseAccepted.");
        return 2;
    }
    Console.WriteLine("READ_ERROR_SAFETY_GREEN: 3/3 active-low read-error/detach scenarios emitted zero coin pulses; other capture risks remain.");
    return 0;
}
Console.WriteLine("NATIVE_SOURCE_DIAGNOSTIC_PASS: 6/6 controlled in-process C# API traces met proposed read-error guard contract; delayed callback and RI capture risks remain. NOT hardware or real Windows serial driver.");
return 0;
