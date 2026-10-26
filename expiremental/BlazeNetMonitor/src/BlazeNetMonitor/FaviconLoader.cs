using System.Net;
using System.Net.Http;
using System.Net.Sockets;
using BlazeNetMonitor.Core;

namespace BlazeNetMonitor;

/// <summary>Opt-in, small, bounded icon fetcher; no redirects, internal hosts, or persistent cache.</summary>
internal static class FaviconLoader
{
    private static readonly HttpClient Client = new(new SocketsHttpHandler
    {
        AllowAutoRedirect = false,
        UseProxy = false,
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
            throw new HttpRequestException("No reachable public address for favicon origin");
        }
    }) { Timeout = TimeSpan.FromSeconds(7) };

    public static async Task<Bitmap?> TryLoadAsync(ProbeTarget target, CancellationToken ct)
    {
        string? host = FaviconSafety.OfficialHost(target.Address);
        if (host is null) return null;
        try
        {
            var uri = new UriBuilder(Uri.UriSchemeHttps, host) { Path = "/favicon.ico" }.Uri;
            using var req = new HttpRequestMessage(HttpMethod.Get, uri);
            using var response = await Client.SendAsync(req,
                HttpCompletionOption.ResponseHeadersRead, ct);
            if (!response.IsSuccessStatusCode ||
                (int)response.StatusCode is >= 300 and < 400 ||
                response.Content.Headers.ContentLength > 96 * 1024) return null;
            var type = response.Content.Headers.ContentType?.MediaType;
            if (type is not null && type != "image/x-icon" && type != "image/vnd.microsoft.icon" &&
                type != "image/png" && type != "image/ico" && type != "application/octet-stream")
                return null;
            await using var stream = await response.Content.ReadAsStreamAsync(ct);
            using var ms = new MemoryStream();
            byte[] buffer = new byte[8192];
            int n;
            while ((n = await stream.ReadAsync(buffer, ct)) > 0)
            {
                if (ms.Length + n > 96 * 1024) return null;
                ms.Write(buffer, 0, n);
            }
            if (ms.Length == 0) return null;
            ms.Position = 0;
            try { using var ico = new Icon(ms); return ico.ToBitmap(); }
            catch (Exception)
            {
                ms.Position = 0;
                using var img = Image.FromStream(ms);
                return new Bitmap(img);
            }
        }
        catch (OperationCanceledException) { return null; }
        catch (Exception) { return null; }
    }
}
