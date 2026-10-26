using System.Net;
namespace BlazeNetMonitor.Core;

/// <summary>Never make incidental icon fetches for local or link-local addresses.
/// Special resolver IPs may only use explicitly documented canonical sites.</summary>
public static class FaviconSafety
{
    public static string? OfficialHost(string? target)
    {
        if (string.IsNullOrWhiteSpace(target)) return null;
        target = target.Trim();
        if (Uri.TryCreate(target, UriKind.Absolute, out var uri))
        {
            if (uri.Scheme != Uri.UriSchemeHttps || uri.UserInfo.Length != 0) return null;
            target = uri.Host;
        }
        else if (target.Contains('/') || target.Contains('@') || target.Contains(':'))
            return null;
        target = target.TrimEnd('.').ToLowerInvariant();
        if (target == "1.1.1.1" || target == "1.0.0.1") return "one.one.one.one";
        if (target == "8.8.8.8" || target == "8.8.4.4") return "dns.google";
        if (IPAddress.TryParse(target, out _)) return null;
        if (!target.Contains('.') || target.Length > 253 || target.EndsWith(".local") ||
            target.EndsWith(".localhost") || target.EndsWith(".internal") ||
            target.EndsWith(".test") || target.EndsWith(".invalid")) return null;
        if (target.Split('.').Any(label => label.Length == 0 || label.Length > 63 ||
            label.StartsWith('-') || label.EndsWith('-') ||
            label.Any(c => !char.IsLetterOrDigit(c) && c != '-'))) return null;
        return target;
    }

    public static bool IsPublicAddress(IPAddress ip)
    {
        if (ip.IsIPv4MappedToIPv6) return IsPublicAddress(ip.MapToIPv4());
        if (ip.AddressFamily == System.Net.Sockets.AddressFamily.InterNetwork)
        {
            var b = ip.GetAddressBytes();
            if (b[0] == 0 || b[0] == 10 || b[0] == 127 || b[0] >= 224 ||
                b[0] == 169 && b[1] == 254 ||
                b[0] == 172 && b[1] >= 16 && b[1] <= 31 ||
                b[0] == 192 && b[1] == 168 ||
                b[0] == 100 && b[1] >= 64 && b[1] <= 127 ||
                b[0] == 198 && b[1] is 18 or 19 ||
                b[0] == 192 && b[1] == 0 ||
                b[0] == 192 && b[1] == 0 && b[2] == 2 ||
                b[0] == 198 && b[1] == 51 && b[2] == 100 ||
                b[0] == 203 && b[1] == 0 && b[2] == 113)
                return false;
            return true;
        }
        if (ip.AddressFamily == System.Net.Sockets.AddressFamily.InterNetworkV6)
        {
            var b = ip.GetAddressBytes();
            return !IPAddress.IsLoopback(ip) && !ip.IsIPv6LinkLocal &&
                !ip.IsIPv6SiteLocal && !ip.IsIPv6Multicast &&
                (b[0] & 0xFE) != 0xFC && // unique-local
                !(b[0] == 0x20 && b[1] == 0x01 && b[2] == 0x0d && b[3] == 0xb8) &&
                !(b.Take(12).All(x => x == 0)); // no unspecified / v4-compat
        }
        return false;
    }
}
