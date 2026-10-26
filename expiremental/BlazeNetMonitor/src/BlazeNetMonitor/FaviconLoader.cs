using System.Drawing.Drawing2D;
using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using System.Text;
using BlazeNetMonitor.Core;

namespace BlazeNetMonitor;

/// <summary>
/// Site-origin favicon discovery. Public HTTPS only; limited redirects, bounded
/// downloads, validated DNS-to-public-IP sockets, no proxy or third-party icon API.
/// </summary>
internal static class FaviconLoader
{
    private const int MaxIconBytes = 128 * 1024;
    private const int MaxHtmlBytes = 256 * 1024;
    private const int MaxRedirects = 4;

    private static readonly HttpClient Client = new(new SocketsHttpHandler
    {
        AllowAutoRedirect = false,  // Every redirect is individually validated.
        AutomaticDecompression = DecompressionMethods.GZip | DecompressionMethods.Deflate,
        UseProxy = false,
        UseCookies = false,
        ConnectTimeout = TimeSpan.FromSeconds(4),
        ConnectCallback = async (ctx, ct) =>
        {
            var addresses = await Dns.GetHostAddressesAsync(ctx.DnsEndPoint.Host, ct);
            foreach (var ip in addresses.Where(FaviconSafety.IsPublicAddress))
            {
                var socket = new Socket(ip.AddressFamily, SocketType.Stream, ProtocolType.Tcp);
                try
                {
                    await socket.ConnectAsync(ip, ctx.DnsEndPoint.Port, ct);
                    return new NetworkStream(socket, ownsSocket: true);
                }
                catch (Exception) { socket.Dispose(); }
            }
            throw new HttpRequestException("No reachable public IP address for favicon host");
        }
    }) { Timeout = TimeSpan.FromSeconds(8) };

    private static async Task<byte[]?> GetBytesAsync(Uri initial, int maxBytes, CancellationToken ct)
    {
        var current = initial;
        for (int hop = 0; hop <= MaxRedirects; hop++)
        {
            if (!FaviconSafety.IsPermittedIconUri(current)) return null;
            using var request = new HttpRequestMessage(HttpMethod.Get, current);
            request.Headers.UserAgent.ParseAdd("Mozilla/5.0 (compatible; BlazeNetMonitor/0.2.5; +https://github.com/BlazingSystems)");
            using var response = await Client.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, ct);
            if ((int)response.StatusCode >= 300 && (int)response.StatusCode < 400)
            {
                current = FaviconSafety.SafeRedirect(current,
                    response.Headers.Location?.ToString()) ?? throw new HttpRequestException("Blocked favicon redirect");
                continue;
            }

            if (!response.IsSuccessStatusCode ||
                response.Content.Headers.ContentLength > maxBytes) return null;
            await using var stream = await response.Content.ReadAsStreamAsync(ct);
            await using var buffer = new MemoryStream();
            byte[] chunk = new byte[8192];
            int count;
            while ((count = await stream.ReadAsync(chunk.AsMemory(), ct)) > 0)
            {
                if (buffer.Length + count > maxBytes) return null;
                buffer.Write(chunk, 0, count);
            }
            return buffer.ToArray();
        }
        return null;
    }

    private static Bitmap? DecodeIcon(byte[]? bytes)
    {
        if (bytes is null || bytes.Length < 8) return null;
        using var stream = new MemoryStream(bytes, false);
        try
        {
            using var icon = new Icon(stream);
            using var source = icon.ToBitmap();
            return Normalize(source);
        }
        catch (Exception) { /* PNG/JPEG/GIF favicons use Image below. */ }
        stream.Position = 0;
        try
        {
            using var image = Image.FromStream(stream, false, true);
            return Normalize(image);
        }
        catch (Exception) { return null; }
    }

    private static Bitmap? Normalize(Image image)
    {
        if (image.Width <= 0 || image.Height <= 0 ||
            image.Width > 2048 || image.Height > 2048) return null;
        // Always store a uniform 32x32 memory-only image. Rendering later applies
        // a circular clip while keeping the independently colored network dot.
        var bitmap = new Bitmap(32, 32);
        using var g = Graphics.FromImage(bitmap);
        g.SmoothingMode = SmoothingMode.AntiAlias;
        g.InterpolationMode = InterpolationMode.HighQualityBicubic;
        g.Clear(Color.Transparent);
        float scale = Math.Min(32f / image.Width, 32f / image.Height);
        float w = image.Width * scale, h = image.Height * scale;
        g.DrawImage(image, (32f - w) / 2, (32f - h) / 2, w, h);
        return bitmap;
    }

    public static async Task<Bitmap?> TryLoadAsync(ProbeTarget target, CancellationToken ct)
    {
        string? host = FaviconSafety.OfficialHost(target.Address);
        if (host is null) return null;
        using var deadline = CancellationTokenSource.CreateLinkedTokenSource(ct);
        deadline.CancelAfter(TimeSpan.FromSeconds(16));
        var cancel = deadline.Token;
        try
        {
            var root = new UriBuilder(Uri.UriSchemeHttps, host) { Path = "/" }.Uri;
            // Common default first; some sites redirect to their official icon CDN.
            var ico = new Uri(root, "/favicon.ico");
            var decoded = DecodeIcon(await GetBytesAsync(ico, MaxIconBytes, cancel));
            if (decoded is not null) return decoded;

            // Websites may declare icons at a relative or CDN path, not /favicon.ico.
            var pageBytes = await GetBytesAsync(root, MaxHtmlBytes, cancel);
            if (pageBytes is null) return null;
            string html = Encoding.UTF8.GetString(pageBytes);
            foreach (var url in FaviconSafety.FindIconLinks(html, root))
            {
                decoded = DecodeIcon(await GetBytesAsync(url, MaxIconBytes, cancel));
                if (decoded is not null) return decoded;
            }
        }
        catch (OperationCanceledException) { /* Shutdown or bounded lookup time. */ }
        catch (Exception) { /* Site may deny automated favicon access. */ }
        return null;
    }
}
