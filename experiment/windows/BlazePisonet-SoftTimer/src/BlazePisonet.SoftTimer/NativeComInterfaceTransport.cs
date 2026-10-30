using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;

namespace BlazePisonet.SoftTimer;

// Native Windows device-interface transport. A SerialPort opened by COM number
// is NEVER promoted using a separate lookup or a second, different handle.
// This scoped handle is not yet wired into CoinPulseAccepted / paid capture.
// Win32 API contracts: GUID_DEVINTERFACE_COMPORT, SetupDiGetClassDevsW,
// SetupDiEnumDeviceInterfaces, SetupDiGetDeviceInterfaceDetailW,
// SetupDiGetDeviceInstanceIdW, CreateFileW and GetCommModemStatus.
// No copied third-party code, no private reflection.
internal sealed record NativeComDeviceInterface(string InstanceId, string Path);

internal interface INativeComPlatform
{
    IReadOnlyList<NativeComDeviceInterface> EnumeratePresent();
    SafeFileHandle OpenInterface(string path);
    bool TryReadModemStatus(SafeFileHandle openedHandle, out uint modemStatus);
}

/// <summary>
/// Owns the SAME handle opened using the unique Windows device-interface path
/// that was resolved to an ExactDevice PnP instance ID. All diagnostic modem
/// status reads use this owned handle, never an independently opened COM name.
/// An interface-path open still needs real removal/swap/driver/physical proof.
/// </summary>
internal sealed class NativeComInterfaceSession : IDisposable
{
    private const uint CtsOn = 0x10, DsrOn = 0x20, RingOn = 0x40, CarrierOn = 0x80;
    private readonly INativeComPlatform _platform;
    private readonly SafeFileHandle _handle;
    private readonly object _gate = new();
    private bool _disposed;

    private NativeComInterfaceSession(
        INativeComPlatform platform, SafeFileHandle opened, NativeComDeviceInterface selected)
    {
        _platform = platform;
        _handle = opened;
        DeviceInstanceId = selected.InstanceId;
        InterfacePath = selected.Path;
    }

    internal string DeviceInstanceId { get; }
    internal string InterfacePath { get; }
    internal bool IsClosed { get { lock (_gate) return _disposed || _handle.IsClosed || _handle.IsInvalid; } }

    internal static bool TryOpenExact(string expectedInstanceId,
        out NativeComInterfaceSession? session, out string failure)
    {
        session = null;
        if (!OperatingSystem.IsWindows())
        {
            failure = "Native serial device interfaces require Windows";
            return false;
        }
        return TryOpenExact(expectedInstanceId, new WindowsNativeComPlatform(), out session, out failure);
    }

    // Injection is internal/test-only. Production uses actual Windows SetupAPI.
    internal static bool TryOpenExact(string expectedInstanceId, INativeComPlatform platform,
        out NativeComInterfaceSession? session, out string failure)
    {
        session = null;
        if (platform is null || string.IsNullOrWhiteSpace(expectedInstanceId))
        {
            failure = "Exact device instance ID is required";
            return false;
        }

        SafeFileHandle? candidate = null;
        try
        {
            if (!TrySelectUniqueInterface(platform.EnumeratePresent(),
                    expectedInstanceId, out var selected) || selected is null)
            {
                failure = "Missing, conflicting or ambiguous serial device interface";
                return false;
            }

            // Exactly ONE opening: the selected Windows device-interface path.
            // Not \\.\COM9, SerialPort.Open, WMI lookup or reflection.
            candidate = platform.OpenInterface(selected.Path);
            if (candidate is null || candidate.IsInvalid || candidate.IsClosed)
            {
                failure = "Opening exact serial interface failed";
                return false;
            }

            // A removal/retarget during CreateFile must never be silently
            // accepted. A second enumeration is a freshness check ONLY, not
            // purported independent proof of the open kernel handle.
            if (!HasExactUniqueInterface(platform.EnumeratePresent(),
                    expectedInstanceId, selected.Path))
            {
                failure = "Device interface changed during exact-handle open";
                return false;
            }

            // Probe the modem status on THAT SAME handle before exposing it;
            // unsupported/error/removed driver state is UNKNOWN, never idle.
            if (!platform.TryReadModemStatus(candidate, out _))
            {
                failure = "Opened serial handle status unverifiable";
                return false;
            }

            session = new NativeComInterfaceSession(platform, candidate, selected);
            candidate = null;  // ownership transferred exactly once
            failure = "";
            return true;
        }
        catch (Exception ex) when (
            ex is Win32Exception or ExternalException or InvalidOperationException or
            System.IO.IOException or ArgumentException)
        {
            failure = "Native serial interface unavailable: " + ex.GetType().Name;
            return false;
        }
        finally { candidate?.Dispose(); }
    }

    // The opened kernel handle can outlive its published device interface,
    // and a driver may still return cached modem bits after unplug/rebind.
    // Check the exact instance AND interface path for EACH observation and
    // again when a deferred observation is claimed. Enumeration is a bounded
    // presence check, NOT physical kernel HANDLE identity attestation.
    internal bool TryVerifyPresent()
    {
        lock (_gate) return VerifyPresentLocked();
    }

    private bool VerifyPresentLocked()
    {
        if (_disposed || _handle.IsInvalid || _handle.IsClosed) return false;
        try
        {
            if (HasExactUniqueInterface(_platform.EnumeratePresent(),
                    DeviceInstanceId, InterfacePath))
                return true;
        }
        catch (Exception)
        {
            // Enumeration failure = unknown, never "still present".
        }

        RevokeLocked(); // missing/replaced/duplicate interface revokes original
        return false;
    }

    internal bool TryReadSignal(ModemSignal signal, out bool active)
    {
        active = false;
        lock (_gate)
        {
            if (_disposed || _handle.IsInvalid || _handle.IsClosed)
                return false;

            uint flags;
            try
            {
                if (!_platform.TryReadModemStatus(_handle, out flags))
                {
                    RevokeLocked();
                    return false;
                }
            }
            catch (Exception)
            {
                RevokeLocked();
                return false;
            }

            // IMPORTANT: a cached-success CTS=1 from a still-open, removed
            // handle is not an admissible edge. Recheck after each read, NOT
            // only during TryOpenExact. Do not emit even a diagnostic pulse.
            if (!VerifyPresentLocked()) return false;

            var bit = signal switch
            {
                ModemSignal.Cts => CtsOn,
                ModemSignal.Dsr => DsrOn,
                ModemSignal.CarrierDetect => CarrierOn,
                ModemSignal.RingIndicator => RingOn,
                _ => 0u
            };
            if (bit == 0) return false;
            active = (flags & bit) != 0;
            return true;
        }
    }

    public void Dispose()
    {
        lock (_gate) RevokeLocked();
    }

    // Invoked only under _gate; every invalidation owns the same SafeFileHandle.
    private void RevokeLocked()
    {
        if (_disposed) return;
        _disposed = true;
        _handle.Dispose();
    }

    // One rule for initial selection, post-open refresh and every later read
    // or claim: exactly one matching instance and one claimant for its path.
    private static bool TrySelectUniqueInterface(
        IReadOnlyList<NativeComDeviceInterface>? devices, string instanceId,
        out NativeComDeviceInterface? selected)
    {
        selected = null;
        if (devices is null) return false;

        foreach (var device in devices)
        {
            if (!SameId(device.InstanceId, instanceId)) continue;
            if (selected is not null || string.IsNullOrWhiteSpace(device.Path))
                return false;
            selected = device;
        }

        if (selected is null) return false;
        var path = selected.Path;
        return devices.Count(device => SamePath(device.Path, path)) == 1;
    }

    private static bool HasExactUniqueInterface(
        IReadOnlyList<NativeComDeviceInterface>? devices,
        string instanceId, string originalPath) =>
        TrySelectUniqueInterface(devices, instanceId, out var selected) &&
        selected is not null && SamePath(selected.Path, originalPath);

    private static bool SameId(string? a, string? b) =>
        !string.IsNullOrWhiteSpace(a) && !string.IsNullOrWhiteSpace(b) &&
        string.Equals(a, b, StringComparison.OrdinalIgnoreCase);
    private static bool SamePath(string? a, string? b) =>
        !string.IsNullOrWhiteSpace(a) && !string.IsNullOrWhiteSpace(b) &&
        string.Equals(a, b, StringComparison.OrdinalIgnoreCase);
}

// Windows-native implementation, not loaded on other operating systems.
internal sealed class WindowsNativeComPlatform : INativeComPlatform
{
    private static readonly Guid ComPortGuid =
        new("86E0D1E0-8089-11D0-9CE4-08003E301F73");
    private const uint DigcfPresent = 0x2, DigcfDeviceInterface = 0x10;
    private const int ErrorNoMoreItems = 259, ErrorInsufficientBuffer = 122;
    private const uint GenericRead = 0x80000000, GenericWrite = 0x40000000;
    private const uint OpenExisting = 3;

    [StructLayout(LayoutKind.Sequential)]
    private struct SpDeviceInterfaceData
    {
        public int cbSize;
        public Guid InterfaceClassGuid;
        public int Flags;
        public IntPtr Reserved;
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct SpDevInfoData
    {
        public int cbSize;
        public Guid ClassGuid;
        public uint DevInst;
        public IntPtr Reserved;
    }

    [DllImport("setupapi.dll", EntryPoint = "SetupDiGetClassDevsW", SetLastError = true)]
    private static extern IntPtr SetupDiGetClassDevs(
        ref Guid classGuid, IntPtr enumerator, IntPtr hwndParent, uint flags);

    [DllImport("setupapi.dll", EntryPoint = "SetupDiEnumDeviceInterfaces", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetupDiEnumDeviceInterfaces(
        IntPtr set, IntPtr deviceInfoData, ref Guid interfaceGuid, uint memberIndex,
        ref SpDeviceInterfaceData interfaceData);

    [DllImport("setupapi.dll", EntryPoint = "SetupDiGetDeviceInterfaceDetailW", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetupDiGetDeviceInterfaceDetail(
        IntPtr set, ref SpDeviceInterfaceData interfaceData, IntPtr detail,
        int detailBytes, out int requiredBytes, ref SpDevInfoData deviceInfo);

    [DllImport("setupapi.dll", EntryPoint = "SetupDiGetDeviceInstanceIdW",
        CharSet = CharSet.Unicode, SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetupDiGetDeviceInstanceId(
        IntPtr set, ref SpDevInfoData info, StringBuilder result,
        int capacityChars, out int requiredChars);

    [DllImport("setupapi.dll", EntryPoint = "SetupDiDestroyDeviceInfoList", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetupDiDestroyDeviceInfoList(IntPtr set);

    [DllImport("kernel32.dll", EntryPoint = "CreateFileW", CharSet = CharSet.Unicode,
        SetLastError = true)]
    private static extern SafeFileHandle CreateFile(
        string path, uint access, uint share, IntPtr security, uint disposition,
        uint flags, IntPtr template);

    [DllImport("kernel32.dll", EntryPoint = "GetCommModemStatus", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetCommModemStatus(SafeFileHandle handle, out uint status);

    public IReadOnlyList<NativeComDeviceInterface> EnumeratePresent()
    {
        if (!OperatingSystem.IsWindows()) return Array.Empty<NativeComDeviceInterface>();
        var guid = ComPortGuid;
        var set = SetupDiGetClassDevs(ref guid, IntPtr.Zero, IntPtr.Zero,
                                     DigcfPresent | DigcfDeviceInterface);
        if (set == IntPtr.Zero || set == new IntPtr(-1))
            throw new Win32Exception(Marshal.GetLastWin32Error());

        var devices = new List<NativeComDeviceInterface>();
        try
        {
            for (uint index = 0; index < 4096; index++)
            {
                var iface = new SpDeviceInterfaceData
                    { cbSize = Marshal.SizeOf<SpDeviceInterfaceData>() };
                if (!SetupDiEnumDeviceInterfaces(set, IntPtr.Zero, ref guid, index, ref iface))
                {
                    var error = Marshal.GetLastWin32Error();
                    if (error == ErrorNoMoreItems) return devices;
                    throw new Win32Exception(error);
                }

                devices.Add(ReadDeviceInterface(set, ref iface));
            }
            throw new Win32Exception("Exceeded device-interface enumeration limit");
        }
        finally { SetupDiDestroyDeviceInfoList(set); }
    }

    // Keep SetupAPI allocation, Unicode detail decoding and the device ID
    // in one bounded scope. Enumeration only owns the present-interface loop.
    private static NativeComDeviceInterface ReadDeviceInterface(
        IntPtr set, ref SpDeviceInterfaceData iface)
    {
        var info = new SpDevInfoData { cbSize = Marshal.SizeOf<SpDevInfoData>() };
        _ = SetupDiGetDeviceInterfaceDetail(
            set, ref iface, IntPtr.Zero, 0, out var required, ref info);
        if (Marshal.GetLastWin32Error() != ErrorInsufficientBuffer ||
            required < 8 || required > 65536)
            throw new Win32Exception("Invalid device-interface detail size");

        var buffer = Marshal.AllocHGlobal(required);
        try
        {
            // SP_DEVICE_INTERFACE_DETAIL_DATA_W cbSize: 8 on x64,
            // 6 on x86; actual Unicode DevicePath begins at byte 4.
            Marshal.WriteInt32(buffer, IntPtr.Size == 8 ? 8 : 6);
            if (!SetupDiGetDeviceInterfaceDetail(
                set, ref iface, buffer, required, out _, ref info))
                throw new Win32Exception(Marshal.GetLastWin32Error());
            var path = Marshal.PtrToStringUni(IntPtr.Add(buffer, 4));
            var id = new StringBuilder(1024);
            if (!SetupDiGetDeviceInstanceId(
                set, ref info, id, id.Capacity, out _))
                throw new Win32Exception(Marshal.GetLastWin32Error());
            if (string.IsNullOrWhiteSpace(path) || id.Length == 0)
                throw new Win32Exception("Device-interface identity missing");
            return new NativeComDeviceInterface(id.ToString(), path);
        }
        finally { Marshal.FreeHGlobal(buffer); }
    }

    public SafeFileHandle OpenInterface(string path)
    {
        if (!OperatingSystem.IsWindows() || string.IsNullOrWhiteSpace(path))
            throw new InvalidOperationException("Windows device-interface path required");
        // Exclusively open the symbolic device interface, NOT a COM alias.
        return CreateFile(path, GenericRead | GenericWrite, 0, IntPtr.Zero,
                          OpenExisting, 0, IntPtr.Zero);
    }

    public bool TryReadModemStatus(SafeFileHandle openedHandle, out uint modemStatus)
    {
        modemStatus = 0;
        return OperatingSystem.IsWindows() && !openedHandle.IsClosed &&
            !openedHandle.IsInvalid && GetCommModemStatus(openedHandle, out modemStatus);
    }
}
