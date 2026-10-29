// TEST ONLY: in-process stand-ins for external serial and WMI APIs.
// The production SerialHardware.cs file is compiled unmodified into this test.
// This does NOT exercise real kernel/USB/RS-232 timing or electrical hardware.
namespace System.IO.Ports
{
    public enum Parity { None }
    public enum StopBits { One }
    public enum Handshake { None }
    public enum SerialPinChange { CtsChanged, DsrChanged, CDChanged, Ring }
    public enum SerialError { Frame }
    public sealed class SerialPinChangedEventArgs : EventArgs
    {
        public SerialPinChange EventType { get; }
        public SerialPinChangedEventArgs(SerialPinChange eventType) => EventType = eventType;
    }
    public sealed class SerialErrorReceivedEventArgs : EventArgs
    {
        public SerialError EventType { get; }
        public SerialErrorReceivedEventArgs(SerialError eventType) => EventType = eventType;
    }
    public delegate void SerialPinChangedEventHandler(object sender, SerialPinChangedEventArgs e);
    public delegate void SerialErrorReceivedEventHandler(object sender, SerialErrorReceivedEventArgs e);

    public sealed class SerialPort : IDisposable
    {
        public static bool InitialCtsLevel { get; set; }
        // Fake OS fault injection for actual C# failed-Open lifecycle test.
        public static bool ThrowOnNextOpen { get; set; }
        public int OpenAttemptCount { get; private set; }
        public bool WasDisposed { get; private set; }
        public int PinSubscriberCount => PinChanged?.GetInvocationList().Length ?? 0;
        public static SerialPort? LastCreated { get; private set; }
        // TEST ONLY: the physical adapter currently mapped to a COM port may
        // differ from the PnP identity previously enumerated by WMI.
        public static string? PhysicalPnpAtOpen { get; set; }
        public string? OpenedPhysicalPnp { get; private set; }
        public static string[] GetPortNames() => new[] { "COM9" };
        public string PortName { get; }
        public bool IsOpen { get; private set; }
        public bool CtsLevel { get; set; }
        public bool DsrLevel { get; set; }
        public bool CarrierLevel { get; set; }
        public bool ThrowOnCtsRead { get; set; }
        public bool CtsHolding => ThrowOnCtsRead
            ? throw new IOException("Injected transient CTS status read failure")
            : CtsLevel;
        public bool DsrHolding => DsrLevel;
        public bool CDHolding => CarrierLevel;
        public Handshake Handshake { get; set; }
        public bool DtrEnable { get; set; }
        public bool RtsEnable { get; set; }
        public int ReadTimeout { get; set; }
        public int WriteTimeout { get; set; }
        public event SerialPinChangedEventHandler? PinChanged;
        public event SerialErrorReceivedEventHandler? ErrorReceived;

        public SerialPort(string portName, int baudRate, Parity parity, int dataBits, StopBits stopBits)
        {
            PortName = portName;
            CtsLevel = InitialCtsLevel;
            LastCreated = this;
        }
        public void Open()
        {
            OpenAttemptCount++;
            if (ThrowOnNextOpen)
            {
                ThrowOnNextOpen = false;
                throw new IOException("TEST_ONLY injected COM9 access-denied on Open");
            }
            OpenedPhysicalPnp = PhysicalPnpAtOpen;
            IsOpen = true;
        }
        public void Close() => IsOpen = false;
        public void Dispose() { WasDisposed = true; Close(); }
        public void Raise(SerialPinChange change) =>
            PinChanged?.Invoke(this, new SerialPinChangedEventArgs(change));
        // TEST-ONLY: snapshot a handler before Dispose()/unsubscribe and invoke
        // it later to model an already-dispatched OS callback. This explicitly
        // does NOT assert that Windows drivers really queue such callbacks.
        public Action<SerialPinChange> CaptureDeferredPinCallback()
        {
            var captured = PinChanged;
            return change => captured?.Invoke(this, new SerialPinChangedEventArgs(change));
        }
        public void RaiseError() =>
            ErrorReceived?.Invoke(this, new SerialErrorReceivedEventArgs(SerialError.Frame));
    }
}
namespace System.Management
{
    public sealed class ManagementObject
    {
        private readonly Dictionary<string, object?> _properties;
        public ManagementObject(string name, string manufacturer, string pnp, string deviceId)
        {
            _properties = new(StringComparer.OrdinalIgnoreCase)
            {
                ["Name"] = name, ["Manufacturer"] = manufacturer,
                ["PNPDeviceID"] = pnp, ["DeviceID"] = deviceId
            };
        }
        public object? this[string key] =>
            _properties.TryGetValue(key, out var value) ? value : null;
    }
    public sealed class ManagementObjectSearcher : IDisposable
    {
        public static IReadOnlyList<ManagementObject> FakeDevices { get; set; } =
            Array.Empty<ManagementObject>();
        public ManagementObjectSearcher(string query) { }
        public IEnumerable<ManagementObject> Get() => FakeDevices;
        public void Dispose() { }
    }
}
namespace BlazePisonet.SoftTimer
{
    public enum SerialSelectionMode { ExactDevice, DeviceFamily, ManualPort, AutoCompatible, AnyAvailable, LegacyCom1 }
    public enum ModemSignal { Dsr, Cts, CarrierDetect, RingIndicator }
    public sealed class AppConfig
    {
        public SerialSelectionMode SerialSelection { get; set; } = SerialSelectionMode.ManualPort;
        public string ManualComPort { get; set; } = "COM9";
        public string LastKnownComPort { get; set; } = "";
        public string PreferredPnpDeviceId { get; set; } = "";
        public string PreferredVid { get; set; } = "";
        public string PreferredPid { get; set; } = "";
        public string PreferredUsbSerial { get; set; } = "";
        public string PreferredFriendlyName { get; set; } = "";
        public ModemSignal CoinInputSignal { get; set; } = ModemSignal.Cts;
        public bool CoinInputActiveHigh { get; set; } = true;
        public int SerialBaudRate { get; set; } = 9600;
        public bool DtrEnabled { get; set; }
        public bool RtsEnabled { get; set; }
        public int MinimumPulseMs { get; set; } = 10;
        public int MaximumPulseMs { get; set; } = 1000;
        public int DebounceMs { get; set; } = 10;
    }
    // TEST ONLY — Fake opened-HANDLE identity verifier. It reads the PnP
    // value captured by the *fake SerialPort.Open()* instance, not the mutable
    // WMI pre-open descriptor. Real production verifier is deliberately
    // fail closed until a reviewed HANDLE-owning transport exists.
    internal static class OpenedSerialHandleIdentity
    {
        internal static bool TryVerify(
            System.IO.Ports.SerialPort opened,
            SerialDeviceInfo selected, out string reason)
        {
            if (!opened.IsOpen || string.IsNullOrWhiteSpace(opened.OpenedPhysicalPnp))
            {
                reason = "Fake opened HANDLE: physical PnP identity unavailable";
                return false;
            }
            if (!string.Equals(opened.OpenedPhysicalPnp, selected.PnpDeviceId,
                StringComparison.OrdinalIgnoreCase))
            {
                reason = "Fake opened HANDLE: selected PnP does not match opened adapter";
                return false;
            }
            reason = string.Empty;
            return true;
        }
    }
    public static class Storage
    {
        public static void Log(string message) => Console.WriteLine("SOURCE_LOG " + message);
    }
}
