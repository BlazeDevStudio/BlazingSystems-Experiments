using System.Reflection;
using BlazePisonet.SoftTimer;

var failures = 0;
void Check(string name, Func<bool> test)
{
    try
    {
        if (!test()) throw new Exception("expected fail-closed contract not met");
        Console.WriteLine("PASS " + name);
    }
    catch (Exception ex)
    {
        failures++;
        Console.Error.WriteLine("FAIL " + name + ": " + ex.Message);
    }
}

var original = new SerialDeviceInfo("COM7", "Adapter A", "Vendor", @"USB\VID_0403&PID_6001\A12345", "0403", "6001", "A12345");
var moved = original with { PortName = "COM12" };
var otherAtCom7 = new SerialDeviceInfo("COM7", "Adapter B", "Vendor", @"USB\VID_0403&PID_6001\B98765", "0403", "6001", "B98765");
var rebound = original with { PortName = "COM14", PnpDeviceId = @"USB\VID_0403&PID_6001\NEWPATH" };
var wrongVendor = rebound with { Vid = "1A86", Pid = "7523", PnpDeviceId = @"USB\VID_1A86&PID_7523\A12345" };

var config = new AppConfig();
Check("Bind exact device with real PnP identity", () => SerialDiscovery.BindExactDevice(config, original));
Check("Same physical identity survives COM renumbering", () => SerialDiscovery.Resolve(config, [moved, otherAtCom7])?.PortName == "COM12");
Check("Replacement adapter at remembered COM number is rejected", () => SerialDiscovery.Resolve(config, [otherAtCom7]) is null);
Check("Unique USB hardware serial survives PnP instance change", () => SerialDiscovery.Resolve(config, [rebound])?.PortName == "COM14");
Check("USB serial with mismatched VID/PID is rejected", () => SerialDiscovery.Resolve(config, [wrongVendor]) is null);
Check("Duplicated PnP identity is ambiguous and rejected", () => SerialDiscovery.Resolve(config, [original, moved]) is null);
Check("Duplicated USB serial identity is ambiguous and rejected", () =>
{
    var second = rebound with { PortName = "COM15", PnpDeviceId = @"USB\VID_0403&PID_6001\OTHERPATH" };
    return SerialDiscovery.Resolve(config, [rebound, second]) is null;
});
Check("Legacy exact mode with remembered COM only fails closed", () =>
{
    var legacy = new AppConfig { SerialSelection = SerialSelectionMode.ExactDevice, LastKnownComPort = "COM7" };
    return SerialDiscovery.Resolve(legacy, [otherAtCom7]) is null;
});
Check("Identity-free WMI fallback cannot silently bind ExactDevice", () =>
{
    var unknown = new SerialDeviceInfo("COM4", "Serial Port", "", "", "", "", "");
    var fresh = new AppConfig();
    return !SerialDiscovery.BindExactDevice(fresh, unknown)
        && fresh.SerialSelection != SerialSelectionMode.ExactDevice
        && SerialDiscovery.Resolve(new AppConfig { SerialSelection = SerialSelectionMode.ExactDevice, LastKnownComPort = "COM4" }, [unknown]) is null;
});
Check("Explicit ManualPort remains available for supervised devices", () =>
{
    var manual = new AppConfig { SerialSelection = SerialSelectionMode.ManualPort, ManualComPort = "COM7" };
    return SerialDiscovery.Resolve(manual, [otherAtCom7])?.PortName == "COM7";
});
Check("Location-derived USB instance number is not fabricated as a serial", () =>
{
    var method = typeof(SerialDiscovery).GetMethod("ExtractUsbSerial", BindingFlags.NonPublic | BindingFlags.Static)
        ?? throw new Exception("Extractor missing");
    return (string?)method.Invoke(null, [@"USB\VID_1A86&PID_7523\5&175DAA97&0&2"]) == string.Empty
        && (string?)method.Invoke(null, [@"USB\VID_0403&PID_6001\A12345"]) == "A12345";
});

Console.WriteLine(failures == 0 ? "Serial identity LAB PASS (no hardware was connected)" : $"Serial identity LAB FAIL ({failures} checks)");
return failures == 0 ? 0 : 1;
