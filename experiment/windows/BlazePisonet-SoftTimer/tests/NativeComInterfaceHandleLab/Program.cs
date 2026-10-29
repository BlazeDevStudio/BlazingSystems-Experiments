// PHX-PISONET Windows/.NET8 source-linked native SetupAPI transport test.
// Real Windows PnP enumeration is a read-only API smoke test. No hardware
// opens, physical coin pulses, controller credentials or monetary writes.
using System.ComponentModel;
using Microsoft.Win32.SafeHandles;
using BlazePisonet.SoftTimer;

if (args.Contains("--invalid-setup", StringComparer.Ordinal))
{
    Console.Error.WriteLine("INCONCLUSIVE_EXIT_3: deliberate test-control sentinel");
    return 3;
}

try
{
    const string A = @"USB\VID_1234&PID_5678\COIN-A";
    const string B = @"USB\VID_1234&PID_5678\COIN-B";
    const string PathA = @"\\?\usb#vid_1234&pid_5678#coin-a#{86e0d1e0-8089-11d0-9ce4-08003e301f73}";
    const string PathB = @"\\?\usb#vid_1234&pid_5678#coin-b#{86e0d1e0-8089-11d0-9ce4-08003e301f73}";
    var ifaceA = new NativeComDeviceInterface(A, PathA);
    var ifaceB = new NativeComDeviceInterface(B, PathB);

    static void Require(bool yes, string details)
    {
        if (!yes) throw new InvalidOperationException(details);
    }

    {
        using var api = new FakeNativeComPlatform(ifaceA);
        Require(NativeComInterfaceSession.TryOpenExact(A, api, out var session, out var failure),
            "same-device positive rejected: " + failure);
        var openedSession = session ??
            throw new InvalidOperationException("positive opened session is null");
        using (openedSession)
        {
            Require(openedSession.DeviceInstanceId == A &&
                openedSession.InterfacePath == PathA, "original interface ownership changed");
            Require(api.Opens == 1 && api.OpenedPath == PathA,
                "opened COM alias or wrong path rather than exact interface");
            Require(openedSession.TryReadSignal(ModemSignal.Cts, out var cts) && cts,
                "CTS value not sampled from originally opened handle");
            Require(openedSession.TryReadSignal(ModemSignal.Dsr, out var dsr) && !dsr,
                "DSR negative positive-control failed");
            Require(api.ReadsOnOriginalHandle == 3, "expected initial+two status reads through same handle");
            Require(api.ReadsOnOtherHandle == 0, "read through a new or nonmatching handle");
        }
        Require(api.OpenedHandle?.IsClosed == true, "owned handle not closed on disposal");
        Console.WriteLine("NATIVE_INTERFACE_FAKE_SAME_HANDLE_POSITIVE_PASS: path=A CTS=1 DSR=0 reads=3 closed=1");
    }

    {
        using var api = new FakeNativeComPlatform(ifaceB);
        Require(!NativeComInterfaceSession.TryOpenExact(A, api, out var denied, out _) &&
                denied is null && api.Opens == 0, "missing A picked replacement B");
        Console.WriteLine("NATIVE_INTERFACE_MISSING_PIN_REJECTED_PASS");
    }

    {
        using var api = new FakeNativeComPlatform(ifaceA, ifaceA);
        Require(!NativeComInterfaceSession.TryOpenExact(A, api, out _, out _) && api.Opens == 0,
            "ambiguous duplicate A accepted");
        Console.WriteLine("NATIVE_INTERFACE_DUPLICATE_PIN_REJECTED_PASS");
    }

    {
        using var api = new FakeNativeComPlatform(ifaceA, new NativeComDeviceInterface(B, PathA));
        Require(!NativeComInterfaceSession.TryOpenExact(A, api, out _, out _) && api.Opens == 0,
            "same interface path claimed by A and B");
        Console.WriteLine("NATIVE_INTERFACE_PATH_COLLISION_REJECTED_PASS");
    }

    {
        using var api = new FakeNativeComPlatform(ifaceA) { AfterOpen = new[] { ifaceB } };
        Require(!NativeComInterfaceSession.TryOpenExact(A, api, out _, out _) &&
            api.Opens == 1 && api.OpenedHandle?.IsClosed == true,
            "opened candidate retained after swap to B on OS refresh");
        Console.WriteLine("NATIVE_INTERFACE_SWAP_ON_OPEN_REJECTED_CLOSED_PASS");
    }

    {
        using var api = new FakeNativeComPlatform(ifaceA)
        {
            AfterOpen = new[] { new NativeComDeviceInterface(A, PathB) }
        };
        Require(!NativeComInterfaceSession.TryOpenExact(A, api, out _, out _) &&
            api.OpenedHandle?.IsClosed == true,
            "retargeted A->another interface path allowed");
        Console.WriteLine("NATIVE_INTERFACE_RETARGET_SAME_INSTANCE_REJECTED_PASS");
    }

    {
        using var api = new FakeNativeComPlatform(ifaceA) { StatusSupported = false };
        Require(!NativeComInterfaceSession.TryOpenExact(A, api, out _, out _) &&
            api.OpenedHandle?.IsClosed == true,
            "unreadable modem status allowed or handle leaked");
        Console.WriteLine("NATIVE_INTERFACE_UNVERIFIABLE_STATUS_REJECTED_PASS");
    }

    {
        using var api = new FakeNativeComPlatform(ifaceA) { OpenReturnsInvalid = true };
        Require(!NativeComInterfaceSession.TryOpenExact(A, api, out _, out _) &&
            api.Opens == 1, "invalid opened handle treated as verified");
        Console.WriteLine("NATIVE_INTERFACE_INVALID_HANDLE_REJECTED_PASS");
    }

    {
        using var api = new FakeNativeComPlatform(ifaceA);
        Require(!NativeComInterfaceSession.TryOpenExact("", api, out _, out _) &&
            api.Opens == 0, "empty PnP identity allowed");
        Console.WriteLine("NATIVE_INTERFACE_EMPTY_PIN_REJECTED_PASS");
    }

    // Real SetupAPI code runs on GitHub Windows runner, but never opens an
    // arbitrary available COM interface or toggles/reads real coin hardware.
    if (!OperatingSystem.IsWindows())
        throw new InvalidOperationException("real Windows PnP smoke test requires Windows");
    var real = new WindowsNativeComPlatform();
    var present = real.EnumeratePresent();
    Require(present.All(x => !string.IsNullOrWhiteSpace(x.InstanceId) &&
                            !string.IsNullOrWhiteSpace(x.Path)),
        "native SetupAPI emitted unqualified interface");
    Require(!NativeComInterfaceSession.TryOpenExact(
        @"USB\VID_DEAD&PID_BEEF\PHX_TEST_DOES_NOT_EXIST_183EA5",
        out var physical, out _) && physical is null,
        "nonexistent real PnP instance unexpectedly opened");
    Console.WriteLine("NATIVE_WINDOWS_SETUPAPI_ENUMERATION_READONLY_PASS: count=" + present.Count);
    Console.WriteLine("NATIVE_COM_INTERFACE_SOURCE_LINKED_GREEN: fake handles only; production coin admission remains denied");
    return 0;
}
catch (InvalidOperationException ex)
{
    Console.Error.WriteLine("NATIVE_COM_INTERFACE_SAFETY_RED_EXIT_2: " + ex.Message);
    return 2;
}
catch (Win32Exception ex)
{
    Console.Error.WriteLine("NATIVE_COM_INTERFACE_WIN32_INCONCLUSIVE_EXIT_3: " + ex.Message);
    return 3;
}
catch (Exception ex)
{
    Console.Error.WriteLine("NATIVE_COM_INTERFACE_INCONCLUSIVE_EXIT_3: " + ex);
    return 3;
}

namespace BlazePisonet.SoftTimer
{
    // The only dependency outside the production transport source. This stub
    // mirrors the existing serial input enum without copying SerialHardware.
    public enum ModemSignal { Dsr, Cts, CarrierDetect, RingIndicator }

    internal sealed class FakeNativeComPlatform : INativeComPlatform, IDisposable
    {
        private readonly NativeComDeviceInterface[] _first;
        public NativeComDeviceInterface[]? AfterOpen { get; set; }
        public bool StatusSupported { get; set; } = true;
        public bool OpenReturnsInvalid { get; set; }
        public string? OpenedPath { get; private set; }
        public SafeFileHandle? OpenedHandle { get; private set; }
        public int Opens { get; private set; }
        public int ReadsOnOriginalHandle { get; private set; }
        public int ReadsOnOtherHandle { get; private set; }
        public FakeNativeComPlatform(params NativeComDeviceInterface[] first) => _first = first;
        public IReadOnlyList<NativeComDeviceInterface> EnumeratePresent() =>
            Opens > 0 && AfterOpen is not null ? AfterOpen : _first;

        public SafeFileHandle OpenInterface(string path)
        {
            Opens++;
            OpenedPath = path;
            // 4242 is a fake, NON-OWNING SafeFileHandle, never a real device.
            OpenedHandle = new SafeFileHandle(
                OpenReturnsInvalid ? IntPtr.Zero : new IntPtr(4242), ownsHandle: false);
            return OpenedHandle;
        }

        public bool TryReadModemStatus(SafeFileHandle openedHandle, out uint status)
        {
            if (ReferenceEquals(openedHandle, OpenedHandle))
                ReadsOnOriginalHandle++;
            else
                ReadsOnOtherHandle++;
            status = 0x10u; // fake CTS on, DSR off
            return StatusSupported && !openedHandle.IsClosed && !openedHandle.IsInvalid;
        }

        public void Dispose() => OpenedHandle?.Dispose();
    }
}
