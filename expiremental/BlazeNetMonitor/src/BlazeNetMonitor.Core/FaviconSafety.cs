using System.Net;
using System.Text.RegularExpressions;
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

    /// <summary>Validate icon URLs before any network request, including redirects and HTML links.</summary>
    public static bool IsPermittedIconUri(Uri? uri) =>
        uri is { IsAbsoluteUri: true } &&
        uri.Scheme == Uri.UriSchemeHttps &&
        uri.UserInfo.Length == 0 &&
        uri.Port == 443 &&
        OfficialHost(uri.Host) is not null;

    /// <summary>Resolve redirects only to publicly routable HTTPS sites, including provider CDNs.</summary>
    public static Uri? SafeRedirect(Uri current, string? location)
    {
        if (string.IsNullOrWhiteSpace(location)) return null;
        if (!Uri.TryCreate(current, location.Trim(), out var next)) return null;
        return IsPermittedIconUri(next) ? next : null;
    }

    /// <summary>
    /// Extract site-declared official icons, whatever their CDN, without a third-party lookup.
    /// Common link variants, attribute ordering, and relative URLs are supported.
    /// </summary>
    public static IReadOnlyList<Uri> FindIconLinks(string html, Uri page, int max = 8)
    {
        var urls = new List<Uri>();
        if (!IsPermittedIconUri(page) || string.IsNullOrEmpty(html) || max <= 0) return urls;
        // Only inspect head markup; avoid treating article/user-content links as official favicons.
        int headEnd = html.IndexOf("</head", StringComparison.OrdinalIgnoreCase);
        if (headEnd >= 0) html = html[..headEnd];
        foreach (Match link in Regex.Matches(html, @"<link\b[^>]*>", RegexOptions.IgnoreCase | RegexOptions.Singleline,
                     TimeSpan.FromMilliseconds(150)))
        {
            if (urls.Count >= Math.Min(12, max)) break;
            var attributes = new Dictionary<string, string>(StringComparer.OrdinalIgnoreCase);
            foreach (Match attr in Regex.Matches(link.Value,
                         @"(?<key>[a-z][\w:-]*)\s*=\s*(?:""(?<quoted>[^""]*)""|'(?<single>[^']*)'|(?<bare>[^\s>]+))",
                         RegexOptions.IgnoreCase, TimeSpan.FromMilliseconds(150)))
            {
                var val = attr.Groups["quoted"].Success ? attr.Groups["quoted"].Value :
                          attr.Groups["single"].Success ? attr.Groups["single"].Value :
                          attr.Groups["bare"].Value;
                attributes[attr.Groups["key"].Value] = WebUtility.HtmlDecode(val);
            }
            if (!attributes.TryGetValue("rel", out var rel) ||
                !rel.Split(' ', '\t', '\n', '\r').Any(token =>
                    token.Equals("icon", StringComparison.OrdinalIgnoreCase) ||
                    token.Equals("apple-touch-icon", StringComparison.OrdinalIgnoreCase) ||
                    token.Equals("apple-touch-icon-precomposed", StringComparison.OrdinalIgnoreCase)))
                continue;
            if (!attributes.TryGetValue("href", out var href) ||
                href.StartsWith("data:", StringComparison.OrdinalIgnoreCase) ||
                !Uri.TryCreate(page, href, out var url) || !IsPermittedIconUri(url) ||
                url.AbsolutePath.EndsWith(".svg", StringComparison.OrdinalIgnoreCase))
                continue;
            if (!urls.Contains(url)) urls.Add(url);
        }
        return urls;
    }
}
