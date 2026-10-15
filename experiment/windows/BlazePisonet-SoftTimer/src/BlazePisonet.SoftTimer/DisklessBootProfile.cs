using System.Net;
using System.Net.Sockets;
using System.Text.RegularExpressions;

namespace BlazePisonet.SoftTimer;

// Operator output only. This does not configure DHCP, iPXE, target ACLs or a Windows client.
public sealed record DisklessBootProfile(string ClientLabel, string DhcpRootPath, string IpxeScript)
{
    private const string IqnPattern = @"\Aiqn\.[0-9]{4}-(0[1-9]|1[0-2])\.[a-z0-9]+(?:[.-][a-z0-9]+)*:[a-z0-9][a-z0-9._:-]{0,127}\z";

    public static DisklessBootProfile Create(string clientLabel, string targetIp,
        string targetIqn, string initiatorIqn)
    {
        if (string.IsNullOrEmpty(clientLabel) || clientLabel.Length > 32 ||
            !Regex.IsMatch(clientLabel, @"\A[A-Za-z0-9][A-Za-z0-9._-]*\z", RegexOptions.CultureInvariant))
            throw new InvalidOperationException("Enter a short client label using letters, digits, dot, underscore or hyphen.");
        if (!IPAddress.TryParse(targetIp, out var ip) ||
            ip.AddressFamily != AddressFamily.InterNetwork || ip.ToString() != targetIp)
            throw new InvalidOperationException("Enter a canonical IPv4 address for the iSCSI target.");
        var octets = ip.GetAddressBytes();
        if (octets[0] is 0 or 127 or >= 224 ||
            (octets[0] == 169 && octets[1] == 254) ||
            (octets[0] == 255 && octets[1] == 255 && octets[2] == 255 && octets[3] == 255))
            throw new InvalidOperationException("The iSCSI target must use a routable unicast IPv4 address.");
        if (!ValidIqn(targetIqn) || !ValidIqn(initiatorIqn) ||
            targetIqn.Equals(initiatorIqn, StringComparison.OrdinalIgnoreCase))
            throw new InvalidOperationException("Enter distinct valid target and client initiator IQNs.");

        var rootPath = $"iscsi:{targetIp}::::{targetIqn}";
        var script = $"#!ipxe\nset initiator-iqn {initiatorIqn}\nsanboot {rootPath}\n";
        return new DisklessBootProfile(clientLabel, rootPath, script);
    }

    private static bool ValidIqn(string value) =>
        value.Length <= 223 && Regex.IsMatch(value, IqnPattern, RegexOptions.CultureInvariant);
}
