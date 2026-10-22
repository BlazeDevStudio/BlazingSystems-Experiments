using System.IO.Ports;
using System.Management;
using System.Text.RegularExpressions;

namespace BlazePisonet.SoftTimer;

public sealed record SerialDeviceInfo(
    string PortName,
    string FriendlyName,
    string Manufacturer,
    string PnpDeviceId,
    string Vid,
    string Pid,
    string UsbSerial)
{
    public string Display => string.IsNullOrWhiteSpace(FriendlyName) ? PortName : $"{FriendlyName} · {PortName}";
    public bool IsUsb => PnpDeviceId.StartsWith("USB\\", StringComparison.OrdinalIgnoreCase);
}

public static class SerialDiscovery
{
    private static readonly Regex PortRegex = new(@"\((COM\d+)\)", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex VidRegex = new(@"VID_([0-9A-F]{4})", RegexOptions.IgnoreCase | RegexOptions.Compiled);
    private static readonly Regex PidRegex = new(@"PID_([0-9A-F]{4})", RegexOptions.IgnoreCase | RegexOptions.Compiled);

    public static IReadOnlyList<SerialDeviceInfo> Enumerate()
    {
        var result = new Dictionary<string, SerialDeviceInfo>(StringComparer.OrdinalIgnoreCase);
        if (OperatingSystem.IsWindows())
        {
            try
            {
                using var searcher = new ManagementObjectSearcher("SELECT Name,Manufacturer,PNPDeviceID,DeviceID FROM Win32_PnPEntity WHERE Name LIKE '%(COM%' ");
                foreach (ManagementObject obj in searcher.Get())
                {
                    var name = Convert.ToString(obj["Name"]) ?? string.Empty;
                    var match = PortRegex.Match(name);
                    if (!match.Success) continue;
                    var port = match.Groups[1].Value.ToUpperInvariant();
                    var pnp = Convert.ToString(obj["PNPDeviceID"]) ?? Convert.ToString(obj["DeviceID"]) ?? string.Empty;
                    var manufacturer = Convert.ToString(obj["Manufacturer"]) ?? string.Empty;
                    var vid = VidRegex.Match(pnp).Groups[1].Value.ToUpperInvariant();
                    var pid = PidRegex.Match(pnp).Groups[1].Value.ToUpperInvariant();
                    var usbSerial = ExtractUsbSerial(pnp);
                    result[port] = new SerialDeviceInfo(port, name.Replace($"({port})", "", StringComparison.OrdinalIgnoreCase).Trim(), manufacturer, pnp, vid, pid, usbSerial);
                }
            }
            catch (Exception ex)
            {
                Storage.Log("Serial WMI enumeration failed: " + ex.Message);
            }
        }

        foreach (var port in SerialPort.GetPortNames())
        {
            if (!result.ContainsKey(port))
                result[port] = new SerialDeviceInfo(port, "Serial Port", string.Empty, string.Empty, string.Empty, string.Empty, string.Empty);
        }

        return result.Values.OrderBy(d => PortNumber(d.PortName)).ThenBy(d => d.PortName).ToList();
    }

    public static SerialDeviceInfo? Resolve(AppConfig config, IReadOnlyList<SerialDeviceInfo>? devices = null)
    {
        devices ??= Enumerate();
        if (devices.Count == 0) return null;

        return config.SerialSelection switch
        {
            SerialSelectionMode.ExactDevice => ResolveExact(config, devices),
            SerialSelectionMode.DeviceFamily => devices.FirstOrDefault(d =>
                !string.IsNullOrWhiteSpace(config.PreferredVid) &&
                d.Vid.Equals(config.PreferredVid, StringComparison.OrdinalIgnoreCase) &&
                d.Pid.Equals(config.PreferredPid, StringComparison.OrdinalIgnoreCase)),
            SerialSelectionMode.ManualPort => devices.FirstOrDefault(d => d.PortName.Equals(config.ManualComPort, StringComparison.OrdinalIgnoreCase)),
            SerialSelectionMode.LegacyCom1 => devices.FirstOrDefault(d => d.PortName.Equals("COM1", StringComparison.OrdinalIgnoreCase)),
            SerialSelectionMode.AnyAvailable => devices.FirstOrDefault(),
            SerialSelectionMode.AutoCompatible => devices.FirstOrDefault(d => d.IsUsb) ?? devices.FirstOrDefault(),
            _ => devices.FirstOrDefault()
        };
    }

    private static SerialDeviceInfo? ResolveExact(AppConfig config, IReadOnlyList<SerialDeviceInfo> devices)
    {
        // Exact mode must NEVER become manual COM mode when an adapter is removed.
        // Windows can reassign the last-known COM number to unrelated hardware.
        if (!string.IsNullOrWhiteSpace(config.PreferredPnpDeviceId))
        {
            var matches = devices.Where(d =>
                !string.IsNullOrWhiteSpace(d.PnpDeviceId) &&
                d.PnpDeviceId.Equals(config.PreferredPnpDeviceId, StringComparison.OrdinalIgnoreCase) &&
                MatchesPinnedVidPid(config, d)).Take(2).ToArray();
            if (matches.Length == 1) return matches[0];
            if (matches.Length > 1) return null; // Conflicting PnP enumeration.
        }

        // USB adapters with a genuine stable serial can move between ports.
        // Require VID + PID to avoid mistaking an identically numbered adapter
        // of a different family for the operator's selected coin interface.
        if (!string.IsNullOrWhiteSpace(config.PreferredUsbSerial) &&
            !string.IsNullOrWhiteSpace(config.PreferredVid) &&
            !string.IsNullOrWhiteSpace(config.PreferredPid))
        {
            var matches = devices.Where(d =>
                d.IsUsb &&
                !string.IsNullOrWhiteSpace(d.UsbSerial) &&
                d.UsbSerial.Equals(config.PreferredUsbSerial, StringComparison.OrdinalIgnoreCase) &&
                MatchesPinnedVidPid(config, d)).Take(2).ToArray();
            if (matches.Length == 1) return matches[0];
        }

        // Missing or ambiguous hardware identity: disconnect until explicitly rebound.
        // ManualPort, AnyAvailable and LegacyCom1 still offer deliberate port-only modes.
        return null;
    }

    private static bool MatchesPinnedVidPid(AppConfig config, SerialDeviceInfo device) =>
        (string.IsNullOrWhiteSpace(config.PreferredVid) ||
         device.Vid.Equals(config.PreferredVid, StringComparison.OrdinalIgnoreCase)) &&
        (string.IsNullOrWhiteSpace(config.PreferredPid) ||
         device.Pid.Equals(config.PreferredPid, StringComparison.OrdinalIgnoreCase));

    public static void BindExactDevice(AppConfig config, SerialDeviceInfo device)
    {
        if (string.IsNullOrWhiteSpace(device.PnpDeviceId))
            throw new InvalidOperationException(
                "Windows did not provide a PnP hardware identity for this serial port. " +
                "Choose Manual COM instead, or reinstall the adapter driver and rescan.");

        config.SerialSelection = SerialSelectionMode.ExactDevice;
        config.PreferredPnpDeviceId = device.PnpDeviceId;
        config.PreferredVid = device.Vid;
        config.PreferredPid = device.Pid;
        config.PreferredUsbSerial = device.UsbSerial;
        config.PreferredFriendlyName = device.FriendlyName;
        config.LastKnownComPort = device.PortName;
        config.ManualComPort = device.PortName;
    }

    private static string ExtractUsbSerial(string pnp)
    {
        if (!pnp.StartsWith("USB\\", StringComparison.OrdinalIgnoreCase)) return string.Empty;
        var parts = pnp.Split('\\', StringSplitOptions.RemoveEmptyEntries);
        if (parts.Length < 3) return string.Empty;
        // A location-generated instance (e.g. 5&26ABCDEF&0&2) is NOT a
        // stable USB serial and must never be used to match a different port.
        return parts[^1].Contains('&') ? string.Empty : parts[^1];
    }

    // Runs inside the actual compiled Windows EXE before UI/mutex/device access.
    // Synthetic enumeration only: never opens a COM port or credits time.
    internal static int VerifyExactBinding()
    {
        const string pinnedPnp = @"USB\VID_1A86&PID_7523\REAL123";
        var bound = new SerialDeviceInfo("COM7", "Bound RS232 adapter", "Vendor", pinnedPnp,
            "1A86", "7523", "REAL123");
        var other = new SerialDeviceInfo("COM7", "Unrelated adapter", "Vendor",
            @"USB\VID_0403&PID_6001\OTHER456", "0403", "6001", "OTHER456");
        var moved = bound with { PortName = "COM9" };
        var config = new AppConfig
        {
            SerialSelection = SerialSelectionMode.ExactDevice,
            PreferredPnpDeviceId = pinnedPnp,
            PreferredVid = "1A86",
            PreferredPid = "7523",
            PreferredUsbSerial = "REAL123",
            LastKnownComPort = "COM7"
        };

        if (Resolve(config, [other]) is not null) return 101; // Previously accepted COM7.
        if (Resolve(config, [other, moved]) != moved) return 102;
        if (Resolve(config, [moved, moved with { PortName = "COM10" }]) is not null) return 103;

        // PnP instance can change after a genuine adapter moves; stable serial,
        // full matching VID/PID, and uniqueness are required for recovery.
        var reborn = moved with
        {
            PnpDeviceId = @"USB\VID_1A86&PID_7523\REAL123NEW",
            PortName = "COM11"
        };
        if (Resolve(config, [reborn]) != reborn) return 104;
        if (Resolve(config, [reborn, reborn with { PortName = "COM12" }]) is not null) return 105;

        var wrongFamily = reborn with { Vid = "0403", Pid = "6001" };
        if (Resolve(config, [wrongFamily]) is not null) return 106;

        config.PreferredPnpDeviceId = string.Empty;
        config.PreferredUsbSerial = string.Empty;
        if (Resolve(config, [other]) is not null) return 107; // No identity, no COM fallback.
        try
        {
            BindExactDevice(config, other with { PnpDeviceId = string.Empty });
            return 108; // Binding an identity-less port must be refused.
        }
        catch (InvalidOperationException) { }

        config.SerialSelection = SerialSelectionMode.ManualPort;
        config.ManualComPort = "COM7";
        if (Resolve(config, [other]) != other) return 109; // Explicit legacy modes retained.
        config.SerialSelection = SerialSelectionMode.AnyAvailable;
        if (Resolve(config, [other]) != other) return 110;
        config.SerialSelection = SerialSelectionMode.LegacyCom1;
        if (Resolve(config, [other with { PortName = "COM1" }])?.PortName != "COM1") return 111;

        if (ExtractUsbSerial(@"USB\VID_1A86&PID_7523\5&26ABCDEF&0&2") != string.Empty)
            return 112; // USB location IDs cannot impersonate stable serials.
        if (ExtractUsbSerial(pinnedPnp) != "REAL123") return 113;
        return 0;
    }

    private static int PortNumber(string port)
    {
        var digits = new string(port.Where(char.IsDigit).ToArray());
        return int.TryParse(digits, out var n) ? n : int.MaxValue;
    }
}

public sealed class SerialHardware : IDisposable
{
    private readonly object _gate = new();
    private SerialPort? _port;
    private AppConfig? _config;
    private bool _lastCoinActive;
    private DateTimeOffset? _pulseStarted;
    private DateTimeOffset _lastAccepted = DateTimeOffset.MinValue;

    public SerialDeviceInfo? ConnectedDevice { get; private set; }
    public bool IsConnected => _port?.IsOpen == true;
    public event Action<string>? ConnectionChanged;
    public event Action? CoinPulseAccepted;
    public event Action? SignalChanged;

    public bool Connect(AppConfig config)
    {
        lock (_gate)
        {
            DisconnectInternal();
            _config = config;
            var devices = SerialDiscovery.Enumerate();
            var selected = SerialDiscovery.Resolve(config, devices);
            if (selected is null)
            {
                ConnectionChanged?.Invoke("No matching serial device found");
                return false;
            }

            try
            {
                var port = new SerialPort(selected.PortName, Math.Clamp(config.SerialBaudRate, 300, 115200), Parity.None, 8, StopBits.One)
                {
                    Handshake = Handshake.None,
                    DtrEnable = config.DtrEnabled,
                    RtsEnable = config.RtsEnabled,
                    ReadTimeout = 250,
                    WriteTimeout = 250
                };
                port.PinChanged += OnPinChanged;
                port.ErrorReceived += (_, e) => Storage.Log($"Serial error {selected.PortName}: {e.EventType}");
                port.Open();
                _port = port;
                ConnectedDevice = selected;
                config.LastKnownComPort = selected.PortName;
                _lastCoinActive = IsSignalActive(config.CoinInputSignal, config.CoinInputActiveHigh);
                ConnectionChanged?.Invoke($"Connected to {selected.Display}");
                return true;
            }
            catch (Exception ex)
            {
                Storage.Log($"Serial open failed for {selected.PortName}: {ex.Message}");
                ConnectedDevice = null;
                ConnectionChanged?.Invoke($"Could not open {selected.PortName}: {ex.Message}");
                return false;
            }
        }
    }

    public bool TryReconnect(AppConfig config)
    {
        if (IsConnected) return true;
        return Connect(config);
    }

    public bool GetSignal(ModemSignal signal)
    {
        lock (_gate)
        {
            if (_port?.IsOpen != true) return false;
            try
            {
                return signal switch
                {
                    ModemSignal.Dsr => _port.DsrHolding,
                    ModemSignal.Cts => _port.CtsHolding,
                    ModemSignal.CarrierDetect => _port.CDHolding,
                    ModemSignal.RingIndicator => false,
                    _ => false
                };
            }
            catch { return false; }
        }
    }

    public void SetDtr(bool enabled)
    {
        lock (_gate) if (_port?.IsOpen == true) _port.DtrEnable = enabled;
    }

    public void SetRts(bool enabled)
    {
        lock (_gate) if (_port?.IsOpen == true) _port.RtsEnable = enabled;
    }

    private void OnPinChanged(object? sender, SerialPinChangedEventArgs e)
    {
        var cfg = _config;
        if (cfg is null) return;
        SignalChanged?.Invoke();

        if (cfg.CoinInputSignal == ModemSignal.RingIndicator && e.EventType == SerialPinChange.Ring)
        {
            AcceptCoinIfDebounced(cfg, Math.Max(cfg.MinimumPulseMs, 1));
            return;
        }

        var active = IsSignalActive(cfg.CoinInputSignal, cfg.CoinInputActiveHigh);
        if (active == _lastCoinActive) return;
        _lastCoinActive = active;

        if (active)
        {
            _pulseStarted = DateTimeOffset.UtcNow;
        }
        else if (_pulseStarted is { } started)
        {
            var width = (int)Math.Max(0, (DateTimeOffset.UtcNow - started).TotalMilliseconds);
            _pulseStarted = null;
            AcceptCoinIfDebounced(cfg, width);
        }
    }

    private void AcceptCoinIfDebounced(AppConfig cfg, int widthMs)
    {
        var now = DateTimeOffset.UtcNow;
        if ((now - _lastAccepted).TotalMilliseconds < Math.Max(10, cfg.DebounceMs)) return;
        if (widthMs < Math.Max(1, cfg.MinimumPulseMs)) return;
        if (cfg.MaximumPulseMs > 0 && widthMs > cfg.MaximumPulseMs) return;
        _lastAccepted = now;
        Storage.Log($"Coin pulse accepted on {ConnectedDevice?.PortName ?? "serial"} ({widthMs} ms)");
        CoinPulseAccepted?.Invoke();
    }

    private bool IsSignalActive(ModemSignal signal, bool activeHigh)
    {
        var raw = GetSignal(signal);
        return activeHigh ? raw : !raw;
    }

    public void Disconnect()
    {
        lock (_gate) DisconnectInternal();
    }

    private void DisconnectInternal()
    {
        if (_port is not null)
        {
            try { _port.PinChanged -= OnPinChanged; } catch { }
            try { if (_port.IsOpen) _port.Close(); } catch { }
            try { _port.Dispose(); } catch { }
        }
        _port = null;
        ConnectedDevice = null;
    }

    public void Dispose() => Disconnect();
}
