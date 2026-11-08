using System.ComponentModel;
using System.Runtime.InteropServices;
using Microsoft.Win32.SafeHandles;

namespace BlazePisonet.SoftTimer;

// Native Windows device-interface transport. A SerialPort opened by COM number
// is NEVER promoted using a separate lookup or a second, different handle.
// This scoped handle is not yet wired into CoinPulseAccepted / paid capture.
// Win32 interop is isolated in WindowsNativeComPlatform.cs.
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

