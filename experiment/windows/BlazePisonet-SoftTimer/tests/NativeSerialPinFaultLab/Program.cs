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
    ("active_low_read_error_false_coin", falseCoin.Accepted, 1),
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
    if (falseCoin.Accepted != 0) {
        Console.Error.WriteLine("EXPECTED_SAFETY_RED: no physical coin, but source emitted CoinPulseAccepted after active-low CTS read failure.");
        return 2;
    }
    Console.WriteLine("SAFETY_GATE_GREEN: no false credit in injected scenario.");
    return 0;
}
Console.WriteLine("NATIVE_SOURCE_DIAGNOSTIC_PASS: 4/4 controlled in-process API traces reproduced. NOT hardware or real Windows serial driver.");
return 0;
