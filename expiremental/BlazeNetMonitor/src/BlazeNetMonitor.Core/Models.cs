using System.Text.Json;
using System.Text.Json.Serialization;

namespace BlazeNetMonitor.Core;

public enum TargetProtocol { Icmp, Https, Dns, Tcp }
public enum ConnectionState { Unknown, Down, Unstable, Degraded, Stable, LongStable }

public sealed class ProbeTarget
{
    public string Name { get; set; } = "Target";
    public TargetProtocol Protocol { get; set; } = TargetProtocol.Icmp;
    public string Address { get; set; } = "1.1.1.1";
    public int Port { get; set; } = 443;
}

public sealed class AppSettings
{
    public string AdapterId { get; set; } = "auto";
    public bool UseBits { get; set; } = true;
    public bool StartWithWindows { get; set; } = true;
    // Owner's fixed donation QR is embedded in the application; no visitor substitution.
    public string DonationSplashMode { get; set; } = "EveryLaunch";
    public bool DockInsideTaskbar { get; set; }
    // Auto migrates older installations: freeform or legacy taskbar placement.
    public string PlacementMode { get; set; } = "Auto";
    public int HorizontalOffset { get; set; } = 170;
    public int SamplingSeconds { get; set; } = 1;
    public int ProbeIntervalSeconds { get; set; } = 5;
    // v0.2: freeform canvas geometry is persisted separately from legacy taskbar placement.
    public bool FreeformPositioned { get; set; }
    public int WidgetX { get; set; } = -1;
    public int WidgetY { get; set; } = -1;
    public int WidgetWidth { get; set; } = 312;
    public int WidgetHeight { get; set; } = 64;
    public int WidgetOpacityPercent { get; set; } = 100;
    // Color-key transparency for the main widget, independent of form opacity.
    public bool TransparentBackground { get; set; }
    public int HoverOpacityPercent { get; set; } = 92;
    public bool AutoHideForFullscreen { get; set; } = true;
    public string ThemeMode { get; set; } = "System";
    public bool ShowGraphs { get; set; } = true;
    public string GraphStyle { get; set; } = "Line";  // Line, Filled, Bars, Steps
    public string GraphUploadColor { get; set; } = "#40C9F4";
    public string GraphDownloadColor { get; set; } = "#FFB360";
    public int GraphHistorySeconds { get; set; } = 0; // zero = Auto adaptive
    public int GraphRefreshSeconds { get; set; } = 1; // 1, 2 or 5 seconds
    public string MetricMode { get; set; } = "Auto"; // Auto, Speed, Latency, Loss, Jitter, Totals
    public string UnitMode { get; set; } = "Auto";  // Auto, Bits, Bytes
    public bool ShowFavicons { get; set; } = false; // opt-in outbound HTTPS favicon fetch
    public bool UseSystemAccent { get; set; } = true;
    public ProbeTarget[] Targets { get; set; } =
    [
        new() { Name = "Target 1", Protocol = TargetProtocol.Icmp, Address = "1.1.1.1" },
        new() { Name = "Target 2", Protocol = TargetProtocol.Icmp, Address = "8.8.8.8" }
    ];

    public AppSettings Copy()
    {
        var copy = (AppSettings)MemberwiseClone();
        copy.Targets = Targets.Select(t => new ProbeTarget {
            Name = t.Name, Protocol = t.Protocol, Address = t.Address, Port = t.Port
        }).ToArray();
        return copy;
    }
}

public sealed class TargetHistory
{
    public ConnectionState State { get; set; } = ConnectionState.Unknown;
    public DateTimeOffset? StableSinceUtc { get; set; }
    public DateTimeOffset? LastSampleUtc { get; set; }
    public int ConsecutiveFailures { get; set; }
    public int ConsecutiveGood { get; set; }
    public int ConsecutiveBad { get; set; }
    public double LatencyBaselineMs { get; set; } = 0;
    public List<ProbeResult> Samples { get; set; } = [];
}

public readonly record struct ProbeResult(DateTimeOffset TimeUtc, bool Success, double LatencyMs, string Message);
public readonly record struct TargetSnapshot(ConnectionState State, double LatencyMs, double LossPercent, double JitterMs, string Message, DateTimeOffset? StableSinceUtc);
public readonly record struct SpeedSample(double UploadBytesPerSecond, double DownloadBytesPerSecond);

public static class MonitorMath
{
    public static SpeedSample Compute(long previousSent, long previousReceived, long currentSent, long currentReceived, TimeSpan elapsed)
    {
        if (elapsed.TotalSeconds <= 0 || currentSent < previousSent || currentReceived < previousReceived)
            return new SpeedSample(0, 0);
        return new SpeedSample((currentSent - previousSent) / elapsed.TotalSeconds, (currentReceived - previousReceived) / elapsed.TotalSeconds);
    }

    public static string Rate(double bytesPerSecond, bool bits)
    {
        var value = Math.Max(0, bytesPerSecond) * (bits ? 8d : 1d);
        var units = bits ? new[] { "bps", "Kbps", "Mbps", "Gbps" } : new[] { "B/s", "KB/s", "MB/s", "GB/s" };
        var index = 0;
        while (value >= 1000 && index < units.Length - 1) { value /= 1000; index++; }
        return $"{value:0.##} {units[index]}";
    }

    public static string Bytes(long bytes)
    {
        double size = Math.Max(0, bytes);
        var units = new[] { "B", "KiB", "MiB", "GiB", "TiB" };
        int i = 0;
        while (size >= 1024 && i < units.Length - 1) { size /= 1024; i++; }
        return $"{size:0.##} {units[i]}";
    }
}

public sealed class QualityTracker
{
    private const int MaxHistory = 24; // 2 minutes at 5 second intervals
    public TargetHistory History { get; }
    public QualityTracker(TargetHistory? history = null) => History = history ?? new();

    public TargetSnapshot Add(ProbeResult result, int intervalSeconds)
    {
        var elapsed = History.LastSampleUtc.HasValue
            ? result.TimeUtc - History.LastSampleUtc.Value : TimeSpan.Zero;
        bool gap = History.LastSampleUtc.HasValue &&
            (elapsed.TotalSeconds > Math.Max(15, intervalSeconds * 3) ||
             elapsed.TotalSeconds <= 0);
        if (gap)
        {
            // Sleep/network suspension breaks continuity; no invented blue streaks.
            History.Samples.Clear();
            History.StableSinceUtc = null;
            History.ConsecutiveFailures = 0;
            History.ConsecutiveGood = 0;
            History.ConsecutiveBad = 0;
            History.LatencyBaselineMs = 0;
        }

        History.LastSampleUtc = result.TimeUtc;
        History.Samples.Add(result);
        if (History.Samples.Count > MaxHistory) History.Samples.RemoveAt(0);
        History.ConsecutiveFailures = result.Success ? 0 : History.ConsecutiveFailures + 1;

        // Two observations are used together:
        // Last 12 for trend, last 6 for recent loss and jitter. Neither is a speed test.
        var window = History.Samples.TakeLast(12).ToArray();
        var recent = History.Samples.TakeLast(6).ToArray();
        var latencies = window.Where(s => s.Success).Select(s => s.LatencyMs).ToArray();
        var recentLatencies = recent.Where(s => s.Success).Select(s => s.LatencyMs).ToArray();
        double loss = recent.Count(s => !s.Success) * 100d / recent.Length;
        double average = latencies.Length > 0 ? latencies.Average() : 0;
        double jitter = recentLatencies.Length > 1 ?
            recentLatencies.Zip(recentLatencies.Skip(1), (a, b) => Math.Abs(a - b)).Average() : 0;

        // Learn normal RTT slowly only during healthy probes. High RTT relative to
        // established baseline is detected even when absolute thresholds are low.
        if (result.Success && result.LatencyMs > 0 && result.LatencyMs < 180 &&
            loss == 0 && jitter < 45)
        {
            History.LatencyBaselineMs = History.LatencyBaselineMs <= 0
                ? result.LatencyMs
                : History.LatencyBaselineMs * 0.97 + result.LatencyMs * 0.03;
        }
        var baseline = History.LatencyBaselineMs;
        bool strongSpike = baseline > 12 && result.Success &&
            result.LatencyMs > Math.Max(250, baseline * 5);
        bool moderateSpike = baseline > 12 && result.Success &&
            result.LatencyMs > Math.Max(140, baseline * 3);

        // Red requires repeat failure. A single failure goes orange immediately.
        // Orange/yellow severity is based on rolling records, not a single rate reading.
        bool severe = !result.Success ||
            (recent.Length >= 4 && loss >= 25) ||
            average >= 350 || result.LatencyMs >= 350 ||
            (recentLatencies.Length >= 4 && jitter >= 110) || strongSpike;
        bool degraded = (recent.Length >= 4 && loss >= 8) ||
            average >= 180 || result.LatencyMs >= 180 ||
            (recentLatencies.Length >= 4 && jitter >= 60) || moderateSpike;

        var proposed = History.ConsecutiveFailures >= 2 ? ConnectionState.Down :
            severe ? ConnectionState.Unstable :
            degraded ? ConnectionState.Degraded : ConnectionState.Stable;

        bool cleanSample = result.Success && !severe && !degraded;
        History.ConsecutiveGood = cleanSample ? History.ConsecutiveGood + 1 : 0;
        History.ConsecutiveBad = cleanSample ? 0 : History.ConsecutiveBad + 1;

        // Recovery hysteresis: don't flip to green on one lucky probe after a
        // prolonged outage. The latest bad state is retained as degraded.
        if (proposed == ConnectionState.Stable &&
            History.State is ConnectionState.Down or ConnectionState.Unstable or ConnectionState.Degraded &&
            History.ConsecutiveGood < 3)
            proposed = ConnectionState.Degraded;

        if (proposed == ConnectionState.Stable)
        {
            History.StableSinceUtc ??= result.TimeUtc;
            var localStart = History.StableSinceUtc.Value.ToLocalTime();
            var localNow = result.TimeUtc.ToLocalTime();
            if (localStart.Date < localNow.Date &&
                result.TimeUtc - History.StableSinceUtc.Value >= TimeSpan.FromHours(24))
                proposed = ConnectionState.LongStable;
        }
        else History.StableSinceUtc = null;

        History.State = proposed;
        return new TargetSnapshot(proposed, result.LatencyMs, loss, jitter, result.Message,
            History.StableSinceUtc);
    }
}

public sealed class TrafficTotals
{
    public long SessionUpload { get; set; }
    public long SessionDownload { get; set; }
    public long TodayUpload { get; set; }
    public long TodayDownload { get; set; }
    public long MonthUpload { get; set; }
    public long MonthDownload { get; set; }
    public DateOnly Day { get; set; } = DateOnly.FromDateTime(DateTime.Now);
    public string Month { get; set; } = DateTime.Now.ToString("yyyy-MM");
    public void Add(long up, long down, DateTime localNow)
    {
        var day = DateOnly.FromDateTime(localNow);
        var month = localNow.ToString("yyyy-MM");
        if (Day != day) { Day = day; TodayUpload = 0; TodayDownload = 0; }
        if (Month != month) { Month = month; MonthUpload = 0; MonthDownload = 0; }
        up = Math.Max(0, up); down = Math.Max(0, down);
        SessionUpload += up; SessionDownload += down;
        TodayUpload += up; TodayDownload += down;
        MonthUpload += up; MonthDownload += down;
    }
    public void ResetSession() { SessionUpload = 0; SessionDownload = 0; }
}

public sealed class PersistedData
{
    public AppSettings Settings { get; set; } = new();
    public TrafficTotals Totals { get; set; } = new();
    public bool WelcomeAcknowledged { get; set; }
    public bool DonationSplashViewed { get; set; }
    public TargetHistory[] Histories { get; set; } = [new(), new()];
}

public sealed class Storage
{
    private static readonly JsonSerializerOptions Options = new() { WriteIndented = true, Converters = { new JsonStringEnumConverter() } };
    public string FilePath { get; }
    public Storage(string filePath) => FilePath = filePath;
    public PersistedData Load()
    {
        try
        {
            if (File.Exists(FilePath))
            {
                var data = JsonSerializer.Deserialize<PersistedData>(File.ReadAllText(FilePath), Options);
                if (data != null && data.Settings.Targets?.Length == 2 && data.Histories?.Length == 2)
                {
                    // Pre-v0.2.6 state means an existing installation: never
                    // unexpectedly show first-run onboarding during an upgrade.
                    using var parsed = JsonDocument.Parse(File.ReadAllText(FilePath));
                    if (!parsed.RootElement.TryGetProperty("WelcomeAcknowledged", out _))
                        data.WelcomeAcknowledged = true;
                    return data;
                }
            }
        }
        catch (Exception) { /* corrupt settings are archived on next save, never crash at startup */ }
        return new PersistedData();
    }
    public void Save(PersistedData data)
    {
        Directory.CreateDirectory(Path.GetDirectoryName(FilePath)!);
        var temp = FilePath + ".tmp";
        File.WriteAllText(temp, JsonSerializer.Serialize(data, Options));
        File.Move(temp, FilePath, true);
    }
}
