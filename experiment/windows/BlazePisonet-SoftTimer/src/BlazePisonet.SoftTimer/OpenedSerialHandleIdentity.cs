using System.IO.Ports;

namespace BlazePisonet.SoftTimer;

/// <summary>
/// Safety boundary for ExactDevice serial coin admission.
///
/// Windows GUID_DEVINTERFACE_COMPORT/PnP enumeration identifies a device
/// interface before Open(), but SerialPort.Open() opens by a mutable COM name.
/// SerialPort.BaseStream does not publicly expose a supported original Windows
/// device-instance ID for the SAME opened serial HANDLE.
/// Never replace this proof with a WMI lookup, SerialPort.PortName, cached COM
/// number, QueryDosDevice at a different time, or a second newly opened handle.
///
/// This implementation deliberately DENIES monetary ExactDevice admission
/// until an audited, native handle-owning serial transport can provide a
/// trustworthy same-handle mapping. No driver assumptions or vendor shortcuts.
/// </summary>
internal static class OpenedSerialHandleIdentity
{
    internal static bool TryVerify(
        SerialPort opened, SerialDeviceInfo selected, out string reason)
    {
        if (!OperatingSystem.IsWindows())
        {
            reason = "Windows opened-handle identity is unavailable";
            return false;
        }

        if (!opened.IsOpen || string.IsNullOrWhiteSpace(selected.PnpDeviceId))
        {
            reason = "Selected/opened serial identity is absent";
            return false;
        }

        // There is no safely supported SerialPort -> exact opened PnP instance
        // mapping in this transport. Fail closed rather than miscredit a swapped
        // or unverifiable coin adapter, including when WMI claims a match.
        reason = "Actual opened serial HANDLE has no verified PnP-instance proof";
        return false;
    }
}
