// PHX-L-APPS TEST ONLY: actual C# source compiled against exact guarded fake-OS API.
// The only source instrumentation is a disposable copy at the completed CTS
// sample / following pulse-state mutation boundary. Never call this hardware.
using BlazePisonet.SoftTimer;
using System.IO.Ports;

if (args.Contains("--invalid-setup", StringComparer.Ordinal))
{
    Console.Error.WriteLine("INCONCLUSIVE_EXIT_3: explicit invalid-test-setup positive verifier.");
    return 3;
}

try
{
    var (normalCount, validSamples) = ValidPulseControl();
    if (normalCount != 1 || validSamples < 2)
        return Inconclusive($"positive CTS control invalid: accepted={normalCount}, validSamples={validSamples}");
    Console.WriteLine($"VALID_PULSE_POSITIVE_CONTROL_PASS accepted={normalCount} validCtsSamples={validSamples}");

    var (v4Accepted, v4Observed) = ForcedRace(injectFault: false);
    var (v5Accepted, v5Observed) = ForcedRace(injectFault: true);
    if (!v4Observed || !v5Observed)
        return Inconclusive($"CTS_SAMPLE_SENTINEL_MISSING V4={v4Observed} V5={v5Observed}");

    Console.WriteLine($"V4_NATIVE_SOURCE_CTS_AFTER_SUCCESSFUL_SAMPLE: accepted={v4Accepted}, safe_expected=0");
    Console.WriteLine($"V5_NATIVE_SOURCE_FAILED_CTS_SAMPLE_RECONNECT: accepted={v5Accepted}, valid_pulse_expected=1");

    if (v4Accepted == 1 && v5Accepted == 0)
    {
        Console.Error.WriteLine("EXPECTED_NATIVE_SOURCE_SAFETY_RED_EXIT_2: V4 fabricated coin on idle new session; V5 discarded valid new-session pulse.");
        return 2;
    }
    if (v4Accepted == 0 && v5Accepted == 1)
    {
        Console.WriteLine("INSTRUMENTED_SOURCE_RACE_GREEN_ONLY: both controlled C# interleavings avoided false credit and preserved legitimate pulse.");
        return 0;
    }
    Console.Error.WriteLine($"UNEXPECTED_NATIVE_RACE_OUTCOME: v4={v4Accepted}, v5={v5Accepted}; cannot classify source behavior");
    return 1;
}
catch (Exception ex)
{
    return Inconclusive(ex.GetType().Name + ": " + ex.Message);
}
finally
{
    TestOnlyHooks.AfterRead = null;
}

static int Inconclusive(string why)
{
    Console.Error.WriteLine("INCONCLUSIVE_EXIT_3: " + why);
    return 3;
}

static (int accepted, int validSamples) ValidPulseControl()
{
    TestOnlyHooks.AfterRead = null;
    SerialPort.InitialCtsLevel = false;
    SerialPort.PhysicalPnpAtOpen = null;
    var cfg = new AppConfig { CoinInputSignal = ModemSignal.Cts,
        CoinInputActiveHigh = true, MinimumPulseMs = 10, DebounceMs = 10 };
    using var sut = new SerialHardware();
    int count = 0, good = 0;
    sut.CoinPulseAccepted += () => Interlocked.Increment(ref count);
    if (!sut.Connect(cfg)) throw new InvalidOperationException("positive control Connect failed");
    var p = SerialPort.LastCreated ?? throw new InvalidOperationException("positive control has no COM");
    TestOnlyHooks.AfterRead = (ok, _) => { if (ok) Interlocked.Increment(ref good); };
    p.CtsLevel = true;
    p.Raise(SerialPinChange.CtsChanged);
    Thread.Sleep(70);
    p.CtsLevel = false;
    p.Raise(SerialPinChange.CtsChanged);
    TestOnlyHooks.AfterRead = null;
    return (count, good);
}

static (int accepted, bool sampleObserved) ForcedRace(bool injectFault)
{
    TestOnlyHooks.AfterRead = null;
    SerialPort.InitialCtsLevel = false;
    SerialPort.PhysicalPnpAtOpen = null;
    var oldCfg = new AppConfig { CoinInputSignal = ModemSignal.Cts,
        CoinInputActiveHigh = true, MinimumPulseMs = 10, DebounceMs = 10 };
    var newCfg = new AppConfig { CoinInputSignal = ModemSignal.Cts,
        CoinInputActiveHigh = !injectFault, MinimumPulseMs = 10, DebounceMs = 10 };
    // V4 new B active-low (physical idle CTS high); V5 new B active-high
    // (physical idle CTS low), with a legitimate B pulse during old fault.
    if (!injectFault) newCfg.CoinInputActiveHigh = false;
    using var sut = new SerialHardware();
    int count = 0;
    sut.CoinPulseAccepted += () => Interlocked.Increment(ref count);
    if (!sut.Connect(oldCfg)) throw new InvalidOperationException("old session Connect failed");
    var a = SerialPort.LastCreated ?? throw new InvalidOperationException("missing old port");

    using var sampleReached = new ManualResetEventSlim(false);
    using var releaseOld = new ManualResetEventSlim(false);
    bool sentinel = false;
    var hookCalls = 0;
    var expectedGood = !injectFault;
    TestOnlyHooks.AfterRead = (ok, active) =>
    {
        Interlocked.Increment(ref hookCalls);
        sentinel = ok == expectedGood && (injectFault || active);
        sampleReached.Set();
        if (!releaseOld.Wait(TimeSpan.FromSeconds(10)))
            throw new TimeoutException("instrumented old callback never released");
    };
    if (injectFault) a.ThrowOnCtsRead = true;
    else a.CtsLevel = true;

    var aCallback = Task.Run(() => a.Raise(SerialPinChange.CtsChanged));
    try
    {
        if (!sampleReached.Wait(TimeSpan.FromSeconds(10)))
            throw new TimeoutException("actual C# CTS callback did not reach hooked sample");
        if (!sentinel || hookCalls != 1)
            throw new InvalidOperationException($"wrong sample sentinel, ok expected={expectedGood}, called={hookCalls}");

        // A's TryReadCoinActive has RELEASED its lock. Reconnect now with
        // a distinct fake opened COM9 object and no physical coin yet.
        SerialPort.InitialCtsLevel = !injectFault; // V4 B idle-high; V5 B idle-low
        if (!sut.Connect(newCfg)) throw new InvalidOperationException("replacement session Connect failed");
        var b = SerialPort.LastCreated ?? throw new InvalidOperationException("missing replacement port");
        if (ReferenceEquals(a, b)) throw new InvalidOperationException("replacement did not allocate a distinct port");

        // Stop instrumenting before any new B signal. V5: a valid B coin
        // starts BEFORE the failing old A callback resumes.
        TestOnlyHooks.AfterRead = null;
        if (injectFault)
        {
            b.CtsLevel = true;
            b.Raise(SerialPinChange.CtsChanged);
            Thread.Sleep(70);
        }
        releaseOld.Set();
        if (!aCallback.Wait(TimeSpan.FromSeconds(10)))
            throw new TimeoutException("old callback did not finish");

        if (!injectFault)
        {
            // Old A's captured asserted status must NOT manufacture a
            // completed pulse when new B remains idle-high.
            Thread.Sleep(70);
            b.Raise(SerialPinChange.CtsChanged);
        }
        else
        {
            // Old A's *failed* status sample must not clear new B's valid
            // in-progress pulse or its session's verified-idle status.
            b.CtsLevel = false;
            b.Raise(SerialPinChange.CtsChanged);
        }
        return (count, sentinel);
    }
    finally
    {
        TestOnlyHooks.AfterRead = null;
        releaseOld.Set();
        if (!aCallback.Wait(TimeSpan.FromSeconds(10)))
            throw new TimeoutException("fault-injection callback teardown timeout");
    }
}
