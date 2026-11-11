using System.Diagnostics;
using System.Net;
using System.Net.Http;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using BlazeNetMonitor.Core;

namespace BlazeNetMonitor;

internal sealed class NetworkMonitor : IDisposable
{
    private readonly HttpClient _http = new(new HttpClientHandler { AllowAutoRedirect = true }) { Timeout = TimeSpan.FromSeconds(3) };
    private string? _lastAdapterId;
    private long _lastSent, _lastReceived;
    private long _lastTimestamp;
    public string AdapterName { get; private set; } = "Disconnected";
    public string AdapterDescription { get; private set; } = "";
    public string Address { get; private set; } = "—";
    public string Error { get; private set; } = "";

    public (SpeedSample speed, long uploadBytes, long downloadBytes) Sample(string preferredId)
    {
        try
        {
            var interfaces = NetworkInterface.GetAllNetworkInterfaces();
            var selected = preferredId == "auto" ? interfaces.FirstOrDefault(n => n.OperationalStatus == OperationalStatus.Up && n.NetworkInterfaceType != NetworkInterfaceType.Loopback && n.GetIPProperties().GatewayAddresses.Any(g => !IPAddress.Any.Equals(g.Address) && !IPAddress.IPv6Any.Equals(g.Address))) : interfaces.FirstOrDefault(n => n.Id == preferredId);
            if (preferredId == "auto") selected ??= interfaces.FirstOrDefault(n => n.OperationalStatus == OperationalStatus.Up && n.NetworkInterfaceType != NetworkInterfaceType.Loopback);
            if (selected == null || selected.OperationalStatus != OperationalStatus.Up)
            {
                Reset(); AdapterName = "Disconnected"; Error = "No active network adapter";
                return (new SpeedSample(0, 0), 0, 0);
            }
            var stats = selected.GetIPv4Statistics();
            var now = Stopwatch.GetTimestamp();
            var sent = stats.BytesSent;
            var received = stats.BytesReceived;
            AdapterName = selected.Name;
            AdapterDescription = selected.Description;
            Address = selected.GetIPProperties().UnicastAddresses.FirstOrDefault(a => a.Address.AddressFamily == AddressFamily.InterNetwork)?.Address.ToString() ?? "—";
            var previous = selected.Id == _lastAdapterId && _lastTimestamp != 0;
            var deltaSent = previous && sent >= _lastSent ? sent - _lastSent : 0;
            var deltaReceived = previous && received >= _lastReceived ? received - _lastReceived : 0;
            var elapsed = previous ? Stopwatch.GetElapsedTime(_lastTimestamp, now) : TimeSpan.Zero;
            _lastAdapterId = selected.Id; _lastSent = sent; _lastReceived = received; _lastTimestamp = now; Error = "";
            return (MonitorMath.Compute(0, 0, deltaSent, deltaReceived, elapsed), deltaSent, deltaReceived);
        }
        catch (Exception e)
        {
            Reset(); Error = e.Message; return (new SpeedSample(0, 0), 0, 0);
        }
    }

    private void Reset() { _lastAdapterId = null; _lastTimestamp = 0; _lastSent = 0; _lastReceived = 0; }
    public void Invalidate() => Reset();

    public async Task<ProbeResult> Probe(ProbeTarget target, CancellationToken cancel)
    {
        var now = DateTimeOffset.UtcNow;
        var clock = Stopwatch.StartNew();
        using var limit = CancellationTokenSource.CreateLinkedTokenSource(cancel);
        limit.CancelAfter(TimeSpan.FromSeconds(3));
        try
        {
            var host = target.Address.Trim();
            if (string.IsNullOrWhiteSpace(host)) return new ProbeResult(now, false, 0, "Empty target");
            switch (target.Protocol)
            {
                case TargetProtocol.Icmp:
                {
                    if (Uri.TryCreate(host, UriKind.Absolute, out var uri)) host = uri.Host;
                    using var ping = new Ping();
                    var reply = await ping.SendPingAsync(host, TimeSpan.FromSeconds(3), cancellationToken: limit.Token);
                    clock.Stop();
                    return new ProbeResult(now, reply.Status == IPStatus.Success, clock.Elapsed.TotalMilliseconds, reply.Status.ToString());
                }
                case TargetProtocol.Https:
                {
                    if (!Uri.TryCreate(host, UriKind.Absolute, out var uri) || uri.Scheme != Uri.UriSchemeHttps)
                        return new ProbeResult(now, false, 0, "Use a complete https:// URL");
                    using var request = new HttpRequestMessage(HttpMethod.Head, uri);
                    using var reply = await _http.SendAsync(request, HttpCompletionOption.ResponseHeadersRead, limit.Token);
                    clock.Stop();
                    // Even a 4xx response confirms that this host is reachable.
                    return new ProbeResult(now, (int)reply.StatusCode < 500, clock.Elapsed.TotalMilliseconds, $"HTTP {(int)reply.StatusCode}");
                }
                case TargetProtocol.Dns:
                {
                    if (Uri.TryCreate(host, UriKind.Absolute, out var uri)) host = uri.Host;
                    var addrs = await Dns.GetHostAddressesAsync(host, limit.Token);
                    clock.Stop();
                    return new ProbeResult(now, addrs.Length > 0, clock.Elapsed.TotalMilliseconds, addrs.Length > 0 ? "DNS resolved" : "No records");
                }
                case TargetProtocol.Tcp:
                {
                    if (Uri.TryCreate(host, UriKind.Absolute, out var uri)) host = uri.Host;
                    if (target.Port is < 1 or > 65535) return new ProbeResult(now, false, 0, "Invalid port");
                    using var tcp = new TcpClient();
                    await tcp.ConnectAsync(host, target.Port, limit.Token);
                    clock.Stop();
                    return new ProbeResult(now, tcp.Connected, clock.Elapsed.TotalMilliseconds, "TCP connected");
                }
                default: throw new ArgumentOutOfRangeException();
            }
        }
        catch (OperationCanceledException) when (!cancel.IsCancellationRequested) { return new ProbeResult(now, false, 0, "Timed out"); }
        catch (Exception e) when (e is HttpRequestException or PingException or SocketException or ArgumentException or InvalidOperationException)
        { return new ProbeResult(now, false, 0, e.Message); }
    }
    public void Dispose() => _http.Dispose();
}
