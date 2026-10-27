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
        // A Windows COM number is not a permanent device identity. It may be
        // reassigned to a different coin adapter after unplug or reboot.
        // Never silently promote LastKnownComPort into an ExactDevice match.
        if (!string.IsNullOrWhiteSpace(config.PreferredPnpDeviceId))
        {
            var matches = devices.Where(d =>
                    !string.IsNullOrWhiteSpace(d.PnpDeviceId) &&
                    d.PnpDeviceId.Equals(config.PreferredPnpDeviceId, StringComparison.OrdinalIgnoreCase))
                .Take(2).ToArray();
            if (matches.Length > 1) return null; // conflicting identities
            if (matches.Length == 1)
            {
                var candidate = matches[0];
                if (!string.IsNullOrWhiteSpace(config.PreferredVid) &&
                    !candidate.Vid.Equals(config.PreferredVid, StringComparison.OrdinalIgnoreCase)) return null;
                if (!string.IsNullOrWhiteSpace(config.PreferredPid) &&
                    !candidate.Pid.Equals(config.PreferredPid, StringComparison.OrdinalIgnoreCase)) return null;
                return candidate;
            }
        }

        // A USB serial can remain stable across COM renumbering, but only when
        // qualified by BOTH vendor and product IDs and observed exactly once.
        // Unscoped, ambiguous and Windows location-generated IDs are unsafe.
        if (!string.IsNullOrWhiteSpace(config.PreferredUsbSerial) &&
            !config.PreferredUsbSerial.Contains('&') &&
            !string.IsNullOrWhiteSpace(config.PreferredVid) &&
            !string.IsNullOrWhiteSpace(config.PreferredPid))
        {
            var matches = devices.Where(d =>
                    d.IsUsb && !string.IsNullOrWhiteSpace(d.UsbSerial) &&
                    !d.UsbSerial.Contains('&') &&
                    d.UsbSerial.Equals(config.PreferredUsbSerial, StringComparison.OrdinalIgnoreCase) &&
                    d.Vid.Equals(config.PreferredVid, StringComparison.OrdinalIgnoreCase) &&
                    d.Pid.Equals(config.PreferredPid, StringComparison.OrdinalIgnoreCase))
                .Take(2).ToArray();
            return matches.Length == 1 ? matches[0] : null;
        }

        // Identity-free legacy profiles must be explicitly rebound by the
        // operator or deliberately switched to the separate ManualPort mode.
        return null;
    }

    public static void BindExactDevice(AppConfig config, SerialDeviceInfo device)
    {
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
        // An instance such as 5&ABCDEF&0&2 encodes a Windows USB location,
        // not a transportable adapter serial. Never truncate it to "5".
        var instance = parts.Length >= 3 ? parts[^1] : string.Empty;
        return instance.Contains('&') ? string.Empty : instance;
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
    // After a failed/unknown status sample, wait for a verified idle level
    // before arming another pulse. A missing modem read is NEVER a low level.
    private bool _requireVerifiedIdle = true;
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

            SerialPort? candidate = null;
            try
            {
                candidate = new SerialPort(selected.PortName, Math.Clamp(config.SerialBaudRate, 300, 115200), Parity.None, 8, StopBits.One)
                {
                    Handshake = Handshake.None,
                    DtrEnable = config.DtrEnabled,
                    RtsEnable = config.RtsEnabled,
                    ReadTimeout = 250,
                    WriteTimeout = 250
                };
                candidate.PinChanged += OnPinChanged;
                candidate.ErrorReceived += (_, e) => Storage.Log($"Serial error {selected.PortName}: {e.EventType}");
                candidate.Open();
                _port = candidate;
                ConnectedDevice = selected;
                config.LastKnownComPort = selected.PortName;
                if (config.SerialSelection == SerialSelectionMode.ExactDevice && string.IsNullOrWhiteSpace(config.PreferredPnpDeviceId))
                    SerialDiscovery.BindExactDevice(config, selected);
                _pulseStarted = null;
                _lastAccepted = DateTimeOffset.MinValue;
                _lastCoinActive = false;
                _requireVerifiedIdle = false;
                if (config.CoinInputSignal != ModemSignal.RingIndicator)
                {
                    if (!TryReadCoinActive(config, out var initialActive))
                    {
                        Storage.Log($"Serial coin input {selected.PortName}: no trusted status at connection");
                        DisconnectInternal();
                        ConnectionChanged?.Invoke("Serial coin input unavailable; cannot arm pulse capture");
                        return false;
                    }
                    _lastCoinActive = initialActive;
                    // If connected while an asserted pulse is in progress,
                    // do not infer its beginning or credit an incomplete coin.
                    _requireVerifiedIdle = initialActive;
                }
                ConnectionChanged?.Invoke($"Connected to {selected.Display}");
                return true;
            }
            catch (Exception ex)
            {
                // Open() may throw before _port is assigned. That provisional
                // SerialPort and its PinChanged subscription are still ours.
                // Never leave a failed-open adapter object observing callbacks.
                if (candidate is not null && !ReferenceEquals(candidate, _port))
                {
                    try { candidate.PinChanged -= OnPinChanged; } catch { }
                    try { if (candidate.IsOpen) candidate.Close(); } catch { }
                    try { candidate.Dispose(); } catch { }
                }
                if (_port is null)
                {
                    _config = null;
                    _pulseStarted = null;
                    _lastCoinActive = false;
                    _requireVerifiedIdle = true;
                }
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

    // Unlike GetSignal (a read-only UI API returning false on failure), paid
    // pulse capture needs a tri-state result: valid high/low OR unknown.
    // Unknown, detached or throwing modem status must never become an edge.
    private bool TryReadCoinActive(AppConfig cfg, out bool active)
    {
        active = false;
        lock (_gate)
        {
            var port = _port;
            if (port?.IsOpen != true) return false;
            try
            {
                bool raw;
                switch (cfg.CoinInputSignal)
                {
                    case ModemSignal.Dsr:
                        raw = port.DsrHolding;
                        break;
                    case ModemSignal.Cts:
                        raw = port.CtsHolding;
                        break;
                    case ModemSignal.CarrierDetect:
                        raw = port.CDHolding;
                        break;
                    default:
                        return false; // Ring is an unmeasured event, not a level.
                }
                active = cfg.CoinInputActiveHigh ? raw : !raw;
                return true;
            }
            catch (Exception ex)
            {
                Storage.Log("Serial coin status read failed (capture disarmed): " + ex.Message);
                return false;
            }
        }
    }

    private void OnPinChanged(object? sender, SerialPinChangedEventArgs e)
    {
        var cfg = _config;
        if (cfg is null) return;
        // A callback can arrive after unplug/dispose or from an old COM session.
        // Fail closed; it must not be interpreted as an active-low assertion.
        // A deferred callback from an old COM session must not modify the
        // NEW session's in-progress pulse or verified-idle arm state.
        if (!ReferenceEquals(sender, _port)) return;
        // A callback from the current port that is now closed is different:
        // its own in-progress pulse must be abandoned until verified idle.
        if (_port?.IsOpen != true)
        {
            _pulseStarted = null;
            _requireVerifiedIdle = true;
            return;
        }
        SignalChanged?.Invoke();
        // A SignalChanged subscriber can synchronously reconnect and replace
        // the port/config while this old callback is on the stack. Never
        // sample a replacement session using the old callback's settings.
        // This protects reentrant listeners; parallel reconnects still need
        // independently reviewed session-atomic capture and paid identity.
        if (!ReferenceEquals(sender, _port) || !ReferenceEquals(cfg, _config) || _port?.IsOpen != true)
            return;

        if (cfg.CoinInputSignal == ModemSignal.RingIndicator)
        {
            // RI is event-only in System.IO.Ports; unrelated pin notifications
            // must not enter the level-read failure/disarm path. RI acceptance
            // remains UNQUALIFIED for unattended monetary input.
            if (e.EventType == SerialPinChange.Ring)
                AcceptCoinIfDebounced(cfg, Math.Max(cfg.MinimumPulseMs, 1));
            return;
        }

        if (!TryReadCoinActive(cfg, out var active))
        {
            // Do not treat false from an exception as a physical pin level.
            _pulseStarted = null;
            _lastCoinActive = false;
            _requireVerifiedIdle = true;
            return;
        }

        if (_requireVerifiedIdle)
        {
            // The fault could have happened mid-pulse. Never resume counting
            // an edge whose true start/end may have been lost.
            _pulseStarted = null;
            _lastCoinActive = active;
            if (!active) _requireVerifiedIdle = false;
            return;
        }

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
        if (_port?.IsOpen != true || _requireVerifiedIdle) return;
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
        _config = null;
        _pulseStarted = null;
        _lastCoinActive = false;
        _requireVerifiedIdle = true;
        ConnectedDevice = null;
    }

    public void Dispose() => Disconnect();
}
