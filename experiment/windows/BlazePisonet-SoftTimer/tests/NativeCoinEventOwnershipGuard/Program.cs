// PHX-PISONET test-only: actual SerialHardware.cs on Windows/.NET8 fake OS.
// Never treat green as proof of opened Windows kernel HANDLE/paid coin admission.
using BlazePisonet.SoftTimer;
using System.IO.Ports;

if (args.Contains("--invalid-setup", StringComparer.Ordinal))
{
    Console.Error.WriteLine("INCONCLUSIVE_EXIT_3: deliberate invalid-setup sentinel");
    return 3;
}

try
{
    TypedPositiveAndCrossThreadDisconnect();
    ReentrantReconnectRejectsOldAcceptance();
    CrossThreadReconnectRejectsOldAcceptance();
    Console.WriteLine("NATIVE_COIN_EVENT_OWNERSHIP_GREEN: typed positive and cross-thread/reentrant/duplicate checks passed");
    return 0;
}
catch (TimeoutException ex)
{
    Console.Error.WriteLine("SOURCE_UNSAFE_EXIT_2: callback blocked reconnect under lock: " + ex.Message);
    return 2;
}
catch (InvalidOperationException ex)
{
    Console.Error.WriteLine("SOURCE_UNSAFE_EXIT_2: " + ex.Message);
    return 2;
}
catch (Exception ex)
{
    Console.Error.WriteLine("INCONCLUSIVE_EXIT_3: " + ex);
    return 3;
}

static AppConfig Config() => new()
{
    SerialSelection = SerialSelectionMode.ExactDevice,
    PreferredPnpDeviceId = @"USB\VID_1234&PID_5678\COIN-A",
    PreferredUsbSerial = "COIN-A",
    PreferredVid = "1234",
    PreferredPid = "5678",
    ManualComPort = "COM9",
    CoinInputSignal = ModemSignal.Cts,
    CoinInputActiveHigh = true,
    MinimumPulseMs = 10,
    DebounceMs = 10
};

static SerialPort Connect(SerialHardware sut, AppConfig config)
{
    SerialPort.InitialCtsLevel = false;
    // FAKE OS only: pin the original opened PnP identity to the synthetic
    // SerialPort instance; the REAL verifier remains fail-closed.
    SerialPort.PhysicalPnpAtOpen = @"USB\VID_1234&PID_5678\COIN-A";
    System.Management.ManagementObjectSearcher.FakeDevices = new[]
    {
        new System.Management.ManagementObject(
            "Coin Adapter (COM9)", "Lab", @"USB\VID_1234&PID_5678\COIN-A", "COM9")
    };
    if (!sut.Connect(config))
        throw new InvalidOperationException("positive source Connect failed");
    return SerialPort.LastCreated ??
        throw new InvalidOperationException("fake opened serial instance absent");
}

static void RaiseValidPulse(SerialPort p)
{
    p.CtsLevel = true;
    p.Raise(SerialPinChange.CtsChanged);
    Thread.Sleep(70);
    p.CtsLevel = false;
    p.Raise(SerialPinChange.CtsChanged);
}

static void Require(bool condition, string message)
{
    if (!condition) throw new InvalidOperationException(message);
}

static void TypedPositiveAndCrossThreadDisconnect()
{
    using var sut = new SerialHardware();
    var p = Connect(sut, Config());
    var accepted = 0;
    var claimed = 0;
    var secondClaim = 0;
    var legacy = 0;
    sut.CoinPulseAccepted += () => Interlocked.Increment(ref legacy);
    sut.CoinPulseAcceptedWithContext += coin =>
    {
        Interlocked.Increment(ref accepted);
        Require(coin.Device.PortName == "COM9" && coin.SessionEpoch > 0 &&
                coin.EventSequence > 0 && coin.PulseWidthMs >= 10,
                "acceptance missing original immutable event provenance");
        if (sut.TryClaimCoin(coin)) Interlocked.Increment(ref claimed);
        if (sut.TryClaimCoin(coin)) Interlocked.Increment(ref secondClaim);
        // Must succeed while subscriber is still on stack: if _gate is held,
        // a separate thread cannot enter Disconnect and this test times out.
        var disconnected = Task.Run(sut.Disconnect);
        if (!disconnected.Wait(TimeSpan.FromSeconds(3)))
            throw new TimeoutException("cross-thread Disconnect blocked in coin event subscriber");
    };
    RaiseValidPulse(p);
    Require(accepted == 1 && claimed == 1 && secondClaim == 0 && legacy == 1,
        $"positive/once: typed={accepted}, first={claimed}, duplicate={secondClaim}, legacy={legacy}");
    Console.WriteLine("COIN_EVENT_TYPED_POSITIVE_PASS: count=1 claimed=1 duplicate=0 immutable provenance");
    Console.WriteLine("COIN_EVENT_OUTSIDE_LOCK_CROSS_THREAD_DISCONNECT_PASS");
}

static void ReentrantReconnectRejectsOldAcceptance()
{
    using var sut = new SerialHardware();
    var p = Connect(sut, Config());
    var reconnects = 0;
    var oldClaimed = 0;
    var legacy = 0;
    // Deliberately ordered multicast listeners: the first mutates session,
    // the next attempts to claim the original immutable acceptance.
    sut.CoinPulseAcceptedWithContext += _ =>
    {
        if (!sut.Connect(Config()))
            throw new InvalidOperationException("reentrant Connect failed");
        reconnects++;
    };
    sut.CoinPulseAcceptedWithContext += coin =>
    {
        if (sut.TryClaimCoin(coin)) oldClaimed++;
    };
    sut.CoinPulseAccepted += () => legacy++;
    RaiseValidPulse(p);
    Require(reconnects == 1 && oldClaimed == 0 && legacy == 1,
        $"reentrant old event claimed: reconnect={reconnects}, stale={oldClaimed}, legacy={legacy}");
    Console.WriteLine("COIN_EVENT_REENTRANT_RECONNECT_STALE_CLAIM_DENIED_PASS");
}

static void CrossThreadReconnectRejectsOldAcceptance()
{
    using var sut = new SerialHardware();
    var p = Connect(sut, Config());
    var reconnects = 0;
    var oldClaimed = 0;
    sut.CoinPulseAcceptedWithContext += _ =>
    {
        var reconnected = Task.Run(() => sut.Connect(Config()));
        if (!reconnected.Wait(TimeSpan.FromSeconds(3)))
            throw new TimeoutException("cross-thread Connect blocked under event callback");
        Require(reconnected.Result, "cross-thread replacement Connect failed");
        reconnects++;
    };
    sut.CoinPulseAcceptedWithContext += coin =>
    {
        if (sut.TryClaimCoin(coin)) oldClaimed++;
    };
    RaiseValidPulse(p);
    Require(reconnects == 1 && oldClaimed == 0,
        $"cross-thread old event claimed: reconnect={reconnects}, stale={oldClaimed}");
    Console.WriteLine("COIN_EVENT_CROSS_THREAD_RECONNECT_STALE_CLAIM_DENIED_PASS");
}
