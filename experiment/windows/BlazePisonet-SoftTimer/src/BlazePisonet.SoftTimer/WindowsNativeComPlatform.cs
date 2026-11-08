using System.ComponentModel;
using System.Runtime.InteropServices;
using System.Text;
using Microsoft.Win32.SafeHandles;

namespace BlazePisonet.SoftTimer;

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
                    devices.Add(new NativeComDeviceInterface(id.ToString(), path));
                }
                finally { Marshal.FreeHGlobal(buffer); }
            }
            throw new Win32Exception("Exceeded device-interface enumeration limit");
        }
        finally { SetupDiDestroyDeviceInfoList(set); }
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
