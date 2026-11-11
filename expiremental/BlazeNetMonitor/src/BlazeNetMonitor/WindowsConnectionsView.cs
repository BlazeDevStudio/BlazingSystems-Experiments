using System.Net.NetworkInformation;
using System.Runtime.InteropServices;
using Microsoft.Win32;
using BlazeNetMonitor.Core;

namespace BlazeNetMonitor;

/// <summary>
/// The default dropdown comes from Windows' Network Connections shell folder,
/// the same virtual folder that ncpa.cpl presents. No adapter names are hardcoded.
/// Advanced mode exposes other NetworkInterface entries (VPN, virtual, tunnels).
/// </summary>
internal static class WindowsConnectionsView
{
    internal sealed record Choice(string Name, NetworkInterface? NetworkInterface)
    {
        public bool Available => NetworkInterface is not null;
        public string Id => NetworkInterface?.Id ?? "";
        public string Label => Available
            ? $"{Name}  ·  {(NetworkInterface!.OperationalStatus == OperationalStatus.Up ? "Connected" : "Disconnected")}"
            : $"{Name}  ·  Disabled / unavailable";
    }

    private static void Release(object? obj)
    {
        if (obj is not null && Marshal.IsComObject(obj))
            Marshal.ReleaseComObject(obj);
    }

    public static bool TryReadNetworkConnections(out IReadOnlyList<string> displayNames)
    {
        displayNames = [];
        if (!OperatingSystem.IsWindows()) return false;
        object? shell = null, folder = null, items = null;
        var names = new List<string>();
        try
        {
            var type = Type.GetTypeFromProgID("Shell.Application");
            if (type is null) return false;
            shell = Activator.CreateInstance(type);
            if (shell is null) return false;
            // CSIDL_CONNECTIONS 0x31 maps to the Network Connections folder.
            // Some Explorer builds accept shell:ConnectionsFolder instead.
            folder = ((dynamic)shell).NameSpace(0x31);
            folder ??= ((dynamic)shell).NameSpace("shell:ConnectionsFolder");
            if (folder is null) return false;
            items = ((dynamic)folder).Items();
            if (items is null) return false;
            int count = (int)((dynamic)items).Count;
            if (count < 0 || count > 512) return false;
            for (int i = 0; i < count; ++i)
            {
                object? item = null;
                try
                {
                    item = ((dynamic)items).Item(i);
                    string? name = (string?)((dynamic)item!).Name;
                    if (!string.IsNullOrWhiteSpace(name))
                        names.Add(name.Trim());
                }
                finally { Release(item); }
            }
            displayNames = names.Distinct(StringComparer.OrdinalIgnoreCase).ToArray();
            return true;
        }
        catch (Exception)
        {
            // In restricted shells the native folder may be unavailable.
            // Caller explicitly labels fallback; never silently treat every
            // device-manager interface as visible in ncpa.cpl.
            return false;
        }
        finally
        {
            Release(items);
            Release(folder);
            Release(shell);
        }
    }

    private static string ConnectionName(NetworkInterface nic)
    {
        // Shell returns a friendly name; Windows keeps this under the
        // network-class Connection key, indexed by the interface GUID.
        try
        {
            if (!Guid.TryParse(nic.Id, out var guid)) return nic.Name;
            const string networkKey = @"SYSTEM\CurrentControlSet\Control\Network\{4D36E972-E325-11CE-BFC1-08002BE10318}";
            using var key = Registry.LocalMachine.OpenSubKey(
                networkKey + @"\{" + guid.ToString("D").ToUpperInvariant() + @"}\Connection");
            var label = key?.GetValue("Name") as string;
            return !string.IsNullOrWhiteSpace(label) ? label : nic.Name;
        }
        catch (Exception) { return nic.Name; }
    }

    public static IReadOnlyList<Choice> Enumerate(bool advanced, out bool matchedShell)
    {
        var all = NetworkInterface.GetAllNetworkInterfaces()
            .Where(n => n.NetworkInterfaceType != NetworkInterfaceType.Loopback)
            .ToArray();
        matchedShell = TryReadNetworkConnections(out var names);
        if (!matchedShell)
        {
            // If the Windows Shell cannot report ncpa.cpl items, don't flood
            // the default selector with guessed devices. The user can explicitly
            // choose Advanced to access all .NET-visible interfaces.
            if (!advanced) return [];
            return all.OrderBy(n => n.Name, StringComparer.OrdinalIgnoreCase)
                .Select(n => new Choice(n.Name, n)).ToArray();
        }

        var mapped = new List<Choice>();
        var used = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
        foreach (var name in names)
        {
            var nic = all.FirstOrDefault(n =>
                string.Equals(ConnectionName(n), name, StringComparison.OrdinalIgnoreCase) ||
                string.Equals(n.Name, name, StringComparison.OrdinalIgnoreCase));
            mapped.Add(new Choice(name, nic));
            if (nic is not null) used.Add(nic.Id);
        }

        if (advanced)
        {
            foreach (var nic in all.Where(n => !used.Contains(n.Id)))
                mapped.Add(new Choice(nic.Name, nic));
        }

        return mapped.OrderBy(n => n.Name, StringComparer.OrdinalIgnoreCase).ToArray();
    }
}
