// PHX-PISONET: executes literal production NativeComPulseCapture.cs linked
// by this test .csproj. All physical levels and handles here are synthetic.
// No customer coin, serial device open or financial acceptance is possible.
using System.Threading.Tasks;

namespace BlazePisonet.SoftTimer;

internal sealed class FakeMonotonicPulseClock : INativePulseClock
{
    public TimeSpan Elapsed { get; private set; }
    public void Advance(int milliseconds) =>
        Elapsed += TimeSpan.FromMilliseconds(milliseconds);
    public void Rewind(int milliseconds) =>
        Elapsed -= TimeSpan.FromMilliseconds(milliseconds);
}

internal static class NativePulseCaptureCases
{
    private static void Require(bool condition, string why)
    {
        if (!condition) throw new InvalidOperationException(why);
    }

    private static NativeComInterfaceSession Open(
        string id, FakeNativeComPlatform platform)
    {
        Require(NativeComInterfaceSession.TryOpenExact(
            id, platform, out var session, out var reason),
            "fixture opened-handle precondition: " + reason);
        return session ?? throw new InvalidOperationException("fixture session null");
    }

    private static void Low(FakeNativeComPlatform os) => os.ModemStatus = 0u;
    private static void High(FakeNativeComPlatform os) => os.ModemStatus = 0x10u;

    public static void Run(NativeComDeviceInterface adapterA, NativeComDeviceInterface adapterB)
    {
        var clock = new FakeMonotonicPulseClock();
        using (var os = new FakeNativeComPlatform(adapterA) { ModemStatus = 0 })
        using (var capture = new NativeComPulseCapture(clock,
            minimumMs: 20, maximumMs: 200, debounceMs: 40, maximumGapMs: 50))
        {
            capture.Rebind(Open(adapterA.InstanceId, os));
            int observations = 0, firstClaims = 0, secondClaims = 0;
            NativeObservedPulse? recorded = null;
            capture.Observed += pulse =>
            {
                observations++;
                recorded = pulse;
                if (capture.TryClaimObserved(pulse)) firstClaims++;
                if (capture.TryClaimObserved(pulse)) secondClaims++;
            };
            capture.SampleOnce();             // exact verified idle at 0
            clock.Advance(10);
            High(os); capture.SampleOnce();   // rising 10
            clock.Advance(15);
            capture.SampleOnce();             // sampled high still on original handle
            clock.Advance(15);
            Low(os); capture.SampleOnce();    // falling 40, width=30
            Require(observations == 1 && firstClaims == 1 && secondClaims == 0 &&
                recorded is not null && recorded.WidthMs == 30 &&
                recorded.DeviceInstanceId == adapterA.InstanceId &&
                recorded.InterfacePath == adapterA.Path &&
                recorded.Generation == capture.Generation &&
                os.ReadsOnOtherHandle == 0,
                "positive original-handle 30ms pulse ownership/debounce failed");
            clock.Advance(5);
            High(os); capture.SampleOnce();  // no verified-idle rearm yet
            clock.Advance(30);
            Low(os); capture.SampleOnce();   // does NOT fabricate second pulse
            Require(observations == 1,
                "missed verified-idle rearm created second pulse");
            Console.WriteLine("NATIVE_PULSE_SAME_OWNED_HANDLE_POSITIVE_PASS: duration=30ms claim=1 duplicate=0 idle-rearm=1");
        }

        // High on first sample cannot be treated as a known rising edge.
        clock = new FakeMonotonicPulseClock();
        using (var os = new FakeNativeComPlatform(adapterA))
        using (var capture = new NativeComPulseCapture(clock,
            minimumMs: 20, maximumMs: 200, debounceMs: 0, maximumGapMs: 50))
        {
            capture.Rebind(Open(adapterA.InstanceId, os));
            int observed = 0;
            capture.Observed += _ => observed++;
            capture.SampleOnce(); // initial high, unverified start
            clock.Advance(30);
            Low(os); capture.SampleOnce();
            Require(observed == 0, "high at bind fabricated an incomplete pulse");
            clock.Advance(10);
            High(os); capture.SampleOnce();
            clock.Advance(25);
            Low(os); capture.SampleOnce();
            Require(observed == 1, "idle-rearmed legitimate pulse not observed");
            Console.WriteLine("NATIVE_PULSE_INITIAL_HIGH_INHIBIT_THEN_IDLE_POSITIVE_PASS");
        }

        // Lost sampling interval during active pulse is unknown, NOT idle.
        clock = new FakeMonotonicPulseClock();
        using (var os = new FakeNativeComPlatform(adapterA) { ModemStatus = 0 })
        using (var capture = new NativeComPulseCapture(clock,
            minimumMs: 20, maximumMs: 200, debounceMs: 0, maximumGapMs: 40))
        {
            capture.Rebind(Open(adapterA.InstanceId, os));
            int observed = 0;
            capture.Observed += _ => observed++;
            capture.SampleOnce();
            clock.Advance(10);
            High(os); capture.SampleOnce();
            clock.Advance(100); // unobserved false-high may have occurred
            Low(os); capture.SampleOnce();
            Require(observed == 0, "stale sample gap credited an unseen pulse");
            clock.Advance(10);
            High(os); capture.SampleOnce();
            clock.Advance(22);
            Low(os); capture.SampleOnce();
            Require(observed == 1, "positive after gap/verified idle failed");
            Console.WriteLine("NATIVE_PULSE_SAMPLING_GAP_DENIED_RECOVERY_PASS");
        }

        // Same handle status failure is permanent revocation, not CTS low.
        clock = new FakeMonotonicPulseClock();
        using (var os = new FakeNativeComPlatform(adapterA) { ModemStatus = 0 })
        using (var capture = new NativeComPulseCapture(clock, minimumMs: 20))
        {
            capture.Rebind(Open(adapterA.InstanceId, os));
            int observed = 0;
            capture.Observed += _ => observed++;
            capture.SampleOnce();
            clock.Advance(10);
            High(os); capture.SampleOnce();
            clock.Advance(30);
            os.StatusSupported = false;
            capture.SampleOnce();
            Require(observed == 0 && os.OpenedHandle?.IsClosed == true,
                "status error granted pulse or leaked owned handle");
            os.StatusSupported = true;
            Low(os); capture.SampleOnce();
            Require(observed == 0, "unbound stale poll yielded callback");
            Console.WriteLine("NATIVE_PULSE_UNPLUG_STATUS_ERROR_CLOSE_NO_CREDIT_PASS");
        }

        // A callback on a known original event cannot hold the capture lock,
        // and cannot claim A after cross-thread rebind to B on the same COM path.
        clock = new FakeMonotonicPulseClock();
        using (var osA = new FakeNativeComPlatform(adapterA) { ModemStatus = 0 })
        using (var osB = new FakeNativeComPlatform(adapterB) { ModemStatus = 0 })
        using (var capture = new NativeComPulseCapture(clock,
            minimumMs: 20, maximumMs: 200, debounceMs: 0, maximumGapMs: 50))
        {
            capture.Rebind(Open(adapterA.InstanceId, osA));
            var aGeneration = capture.Generation;
            var b = Open(adapterB.InstanceId, osB);
            int receivedA = 0, staleClaim = 0, goodClaimB = 0;
            capture.Observed += pulse =>
            {
                if (pulse.DeviceInstanceId != adapterA.InstanceId) return;
                receivedA++;
                var rebind = Task.Run(() => capture.Rebind(b));
                if (!rebind.Wait(TimeSpan.FromSeconds(3)))
                    throw new InvalidOperationException(
                        "callback executed under _gate, blocking cross-thread rebind");
                Require(osA.OpenedHandle?.IsClosed == true,
                    "old A owned handle leaked across rebind");
            };
            capture.Observed += pulse =>
            {
                if (pulse.DeviceInstanceId == adapterA.InstanceId)
                {
                    if (capture.TryClaimObserved(pulse)) staleClaim++;
                }
                else if (capture.TryClaimObserved(pulse)) goodClaimB++;
            };
            capture.SampleOnce(); // A idle
            clock.Advance(10);
            High(osA); capture.SampleOnce();
            clock.Advance(30);
            Low(osA); capture.SampleOnce(); // A callback does cross-thread rebind
            Require(receivedA == 1 && staleClaim == 0 &&
                capture.Generation != aGeneration && osB.ReadsOnOtherHandle == 0,
                "rebound B could claim stale A observation");
            clock.Advance(5);
            capture.SampleOnce(); // B verified idle after rebind
            clock.Advance(10);
            High(osB); capture.SampleOnce();
            clock.Advance(28);
            Low(osB); capture.SampleOnce();
            Require(goodClaimB == 1 && osB.ReadsOnOtherHandle == 0,
                "legitimate original B handle pulse not claimable");
            Console.WriteLine("NATIVE_PULSE_CROSS_THREAD_REBIND_STALE_A_DENIED_B_POSITIVE_PASS");
        }

        // Too-short pulse, clock rollback and overlong pulse must not count.
        clock = new FakeMonotonicPulseClock();
        using (var os = new FakeNativeComPlatform(adapterA) { ModemStatus = 0 })
        using (var capture = new NativeComPulseCapture(clock,
            minimumMs: 20, maximumMs: 100, debounceMs: 0, maximumGapMs: 50))
        {
            capture.Rebind(Open(adapterA.InstanceId, os));
            int seen = 0;
            capture.Observed += _ => seen++;
            capture.SampleOnce();
            clock.Advance(10); High(os); capture.SampleOnce();
            clock.Advance(5); Low(os); capture.SampleOnce(); // width 5
            Require(seen == 0, "too-short pulse was observed");
            clock.Advance(5); capture.SampleOnce(); // verified idle
            clock.Advance(10); High(os); capture.SampleOnce();
            clock.Rewind(15); Low(os); capture.SampleOnce();
            Require(seen == 0, "clock rollback generated pulse");
            clock.Advance(10); capture.SampleOnce(); // verified idle
            clock.Advance(10); High(os); capture.SampleOnce();
            clock.Advance(45); High(os); capture.SampleOnce();
            clock.Advance(45); High(os); capture.SampleOnce();
            clock.Advance(45); Low(os); capture.SampleOnce(); // width 135
            Require(seen == 0, "overlong pulse generated observation");
            Console.WriteLine("NATIVE_PULSE_SHORT_LONG_CLOCK_ROLLBACK_DENIED_PASS");
        }

        Console.WriteLine("NATIVE_OWNED_HANDLE_PULSE_SOURCE_GREEN: 6 deterministic positive/fault/rebind suites; diagnostic only");
    }
}
