using System.Net.NetworkInformation;

namespace BlazeNetMonitor.Core;

/// <summary>Pure policies shared by Settings, validation, and GUI-independent checks.</summary>
public static class SettingsUiPolicy
{
    public static string Placeholder(TargetProtocol protocol) => protocol switch
    {
        TargetProtocol.Icmp => "1.1.1.1 or example.com",
        TargetProtocol.Https => "https://www.example.com",
        TargetProtocol.Tcp => "example.com",
        TargetProtocol.Dns => "example.com",
        _ => "example.com"
    };

    public static string InputLabel(TargetProtocol protocol) => protocol switch
    {
        TargetProtocol.Icmp => "Ping hostname or IP address",
        TargetProtocol.Https => "Complete HTTPS URL",
        TargetProtocol.Tcp => "Host or IP address",
        TargetProtocol.Dns => "Domain to resolve",
        _ => "Target address"
    };
    public static bool ShowPort(TargetProtocol protocol) => protocol == TargetProtocol.Tcp;
    public static string DefaultName(string? saved, int index)
    {
        if (string.IsNullOrWhiteSpace(saved) ||
            saved is "Primary DNS" or "Secondary DNS" or "Target")
            return $"Target {index + 1}";
        return saved.Trim();
    }

    public static bool IsValidAddress(TargetProtocol protocol, string address, int port)
    {
        address = address.Trim();
        if (address.Length == 0 || address.Length > 2048) return false;
        if (protocol == TargetProtocol.Https)
            return Uri.TryCreate(address, UriKind.Absolute, out var url) &&
                url.Scheme.Equals(Uri.UriSchemeHttps, StringComparison.OrdinalIgnoreCase) &&
                !string.IsNullOrWhiteSpace(url.Host) && url.UserInfo.Length == 0;
        if (protocol == TargetProtocol.Tcp && (port < 1 || port > 65535)) return false;
        // DNS, Ping and TCP use hostname/IP: never accidentally allow URL/path.
        return !address.Any(char.IsWhiteSpace) &&
               !address.Contains('/') && !address.Contains('@') && address.Length <= 253;
    }
}

public static class AdapterUiPolicy
{
    public static bool IsVisible(string? name, string? description,
        NetworkInterfaceType type, bool showAll)
    {
        if (showAll) return type != NetworkInterfaceType.Loopback;
        if (type is not (NetworkInterfaceType.Ethernet or
            NetworkInterfaceType.Wireless80211 or
            NetworkInterfaceType.GigabitEthernet or
            NetworkInterfaceType.FastEthernetFx or
            NetworkInterfaceType.FastEthernetT))
            return false;
        string label = ((name ?? "") + " " + (description ?? "")).ToLowerInvariant();
        string[] markers = ["virtual", "veth", "hyper-v", "vmware", "virtualbox",
            "wintun", "wireguard", "tap-", "tun-", "npcap", "loopback", "miniport",
            "docker", "bluetooth", "zerotier", "tailscale", "pseudo-interface"];
        return !markers.Any(label.Contains);
    }
}
