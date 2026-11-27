using System.Collections.Concurrent;
using System.Diagnostics;
using System.Net;
using System.Net.NetworkInformation;
using System.Net.Sockets;
using System.Text.RegularExpressions;

namespace BlazePisonet.SoftTimer;

public sealed record BlazeTimerDevice(string Address, string Name, string MacAddress, long RemainingSeconds);

public sealed class BlazeTimerBridge : IDisposable
{
    private static readonly Regex TimeRegex = new(@"(?<!\d)(\d{1,5}):(\d{2})(?!\d)", RegexOptions.Compiled);
    private readonly HttpClient _http = new() { Timeout = TimeSpan.FromMilliseconds(1200) };
    private readonly System.Threading.Timer _timer;
    private AppConfig _config;
    private int _busy;

    public event Action<long>? RemainingReceived;
    public event Action<string>? StatusChanged;

    public BlazeTimerBridge(AppConfig config)
    {
        _config = config;
        _timer = new System.Threading.Timer(async _ => await PollTimer(), null, Timeout.Infinite, Timeout.Infinite);
    }

    public void UpdateConfig(AppConfig config) => _config = config;

    public void Start()
    {
        var period = Math.Clamp(_config.BlazeTimerPollMs, 500, 10000);
        _timer.Change(0, period);
    }

    public void Stop() => _timer.Change(Timeout.Infinite, Timeout.Infinite);

    private async Task PollTimer()
    {
        if (Interlocked.Exchange(ref _busy, 1) != 0) return;
        try
        {
            var address = NormalizeAddress(_config.BlazeTimerAddress);
            var device = await ProbeAsync(address);
            if (device is null && !string.IsNullOrWhiteSpace(_config.BlazeTimerMac))
            {
                var matches = await DiscoverAsync(24, _config.BlazeTimerMac);
                device = matches.FirstOrDefault();
                if (device is not null) _config.BlazeTimerAddress = device.Address;
            }
            if (device is null)
            {
                StatusChanged?.Invoke("Blaze timer offline or not found");
                return;
            }
            if (!string.IsNullOrWhiteSpace(device.MacAddress) && string.IsNullOrWhiteSpace(_config.BlazeTimerMac))
                _config.BlazeTimerMac = device.MacAddress;
            if (string.IsNullOrWhiteSpace(_config.BlazeTimerName)) _config.BlazeTimerName = device.Name;
            StatusChanged?.Invoke($"Connected to {device.Name} · {new Uri(device.Address).Host}");
            RemainingReceived?.Invoke(device.RemainingSeconds);
        }
        catch (Exception ex) { StatusChanged?.Invoke("Blaze timer error: " + ex.Message); }
        finally { Interlocked.Exchange(ref _busy, 0); }
    }

    public async Task<BlazeTimerDevice?> ProbeAsync(string address)
    {
        try
        {
            address = NormalizeAddress(address);
            using var cts = new CancellationTokenSource(TimeSpan.FromMilliseconds(1200));
            var html = await _http.GetStringAsync(address, cts.Token);
            if (!IsBlazeTimerPage(html)) return null;
            var seconds = ParseRemainingSeconds(html);
            var host = new Uri(address).Host;
            var mac = await TryResolveMacAsync(host);
            var name = ExtractTitle(html) ?? "Blaze Pisonet Timer";
            return new BlazeTimerDevice(address, name, mac, seconds);
        }
        catch { return null; }
    }

    public async Task<IReadOnlyList<BlazeTimerDevice>> DiscoverAsync(int prefixLength = 24, string? requiredMac = null)
    {
        var found = new ConcurrentBag<BlazeTimerDevice>();
        var candidates = LocalSubnetCandidates(prefixLength).Distinct().Take(1024).ToArray();
        using var gate = new SemaphoreSlim(32);
        var tasks = candidates.Select(async ip =>
        {
            await gate.WaitAsync();
            try
            {
                var device = await ProbeAsync($"http://{ip}/");
                if (device is null) return;
                if (!string.IsNullOrWhiteSpace(requiredMac) && !NormalizeMac(device.MacAddress).Equals(NormalizeMac(requiredMac), StringComparison.OrdinalIgnoreCase)) return;
                found.Add(device);
            }
            finally { gate.Release(); }
        });
        await Task.WhenAll(tasks);
        return found.OrderBy(d => IPAddress.Parse(new Uri(d.Address).Host).GetAddressBytes().Last()).ToList();
    }

    private static IEnumerable<string> LocalSubnetCandidates(int prefixLength)
    {
        foreach (var nic in NetworkInterface.GetAllNetworkInterfaces())
        {
            if (nic.OperationalStatus != OperationalStatus.Up) continue;
            foreach (var ua in nic.GetIPProperties().UnicastAddresses)
            {
                if (ua.Address.AddressFamily != AddressFamily.InterNetwork) continue;
                var b = ua.Address.GetAddressBytes();
                if (IPAddress.IsLoopback(ua.Address) || b[0] == 169 && b[1] == 254) continue;
                if (prefixLength >= 24)
                {
                    for (var i = 1; i <= 254; i++)
                    {
                        if (i == b[3]) continue;
                        yield return $"{b[0]}.{b[1]}.{b[2]}.{i}";
                    }
                }
            }
        }
        // Common standalone ESP8266 AP address is always worth trying.
        yield return "192.168.4.1";
    }

    public static long ParseRemainingSeconds(string html)
    {
        var marker = html.IndexOf("Current remaining time", StringComparison.OrdinalIgnoreCase);
        var sample = marker >= 0 ? html[marker..Math.Min(html.Length, marker + 1200)] : html;
        var match = TimeRegex.Match(sample);
        if (!match.Success) return 0;
        var minutes = long.Parse(match.Groups[1].Value);
        var seconds = int.Parse(match.Groups[2].Value);
        return Math.Max(0, minutes * 60 + Math.Clamp(seconds, 0, 59));
    }

    private static bool IsBlazeTimerPage(string html) =>
        html.Contains("BLAZE Pisonet Timer", StringComparison.OrdinalIgnoreCase) ||
        html.Contains("Blaze Pisonet Timer", StringComparison.OrdinalIgnoreCase);

    private static string? ExtractTitle(string html)
    {
        var m = Regex.Match(html, @"<title>\s*(.*?)\s*</title>", RegexOptions.IgnoreCase | RegexOptions.Singleline);
        return m.Success ? WebUtility.HtmlDecode(m.Groups[1].Value.Trim()) : null;
    }

    private static string NormalizeAddress(string address)
    {
        address = address.Trim();
        if (!address.StartsWith("http://", StringComparison.OrdinalIgnoreCase) && !address.StartsWith("https://", StringComparison.OrdinalIgnoreCase))
            address = "http://" + address;
        if (!address.EndsWith('/')) address += "/";
        return address;
    }

    private static async Task<string> TryResolveMacAsync(string host)
    {
        if (!OperatingSystem.IsWindows()) return string.Empty;
        try
        {
            using var ping = new Ping();
            await ping.SendPingAsync(host, 500);
            var psi = new ProcessStartInfo("arp.exe", "-a " + host)
            {
                RedirectStandardOutput = true,
                RedirectStandardError = true,
                UseShellExecute = false,
                CreateNoWindow = true
            };
            using var p = Process.Start(psi);
            if (p is null) return string.Empty;
            var output = await p.StandardOutput.ReadToEndAsync();
            await p.WaitForExitAsync();
            var match = Regex.Match(output, @"\b([0-9a-f]{2}[-:]){5}[0-9a-f]{2}\b", RegexOptions.IgnoreCase);
            return match.Success ? NormalizeMac(match.Value) : string.Empty;
        }
        catch { return string.Empty; }
    }

    private static string NormalizeMac(string mac) => mac.Replace('-', ':').Trim().ToUpperInvariant();

    public void Dispose()
    {
        _timer.Dispose();
        _http.Dispose();
    }
}
