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
    public bool StartWithWindows { get; set; }
    public bool DockInsideTaskbar { get; set; }
    public int HorizontalOffset { get; set; } = 170;
    public int SamplingSeconds { get; set; } = 1;
    public int ProbeIntervalSeconds { get; set; } = 5;
    public ProbeTarget[] Targets { get; set; } =
    [
        new() { Name = "Primary DNS", Protocol = TargetProtocol.Icmp, Address = "1.1.1.1" },
        new() { Name = "Secondary DNS", Protocol = TargetProtocol.Icmp, Address = "8.8.8.8" }
    ];
}

public sealed class TargetHistory
{
    public ConnectionState State { get; set; } = ConnectionState.Unknown;
    public DateTimeOffset? StableSinceUtc { get; set; }
    public DateTimeOffset? LastSampleUtc { get; set; }
    public int ConsecutiveFailures { get; set; }
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
        // No fabricated uninterrupted stability after sleep, app shutdown, or missed probes.
        var gap = History.LastSampleUtc.HasValue && (result.TimeUtc - History.LastSampleUtc.Value).TotalSeconds > Math.Max(15, intervalSeconds * 3);
        if (gap || (History.LastSampleUtc.HasValue && result.TimeUtc <= History.LastSampleUtc.Value))
        {
            History.Samples.Clear();
            History.StableSinceUtc = null;
            History.ConsecutiveFailures = 0;
        }
        History.LastSampleUtc = result.TimeUtc;
        History.Samples.Add(result);
        if (History.Samples.Count > MaxHistory) History.Samples.RemoveAt(0);
        History.ConsecutiveFailures = result.Success ? 0 : History.ConsecutiveFailures + 1;
        var recent = History.Samples;
        var successful = recent.Where(s => s.Success).Select(s => s.LatencyMs).ToArray();
        var loss = recent.Count == 0 ? 100d : recent.Count(s => !s.Success) * 100d / recent.Count;
        var avg = successful.Length > 0 ? successful.Average() : 0;
        var jitter = successful.Length > 1 ? successful.Zip(successful.Skip(1), (a, b) => Math.Abs(a - b)).Average() : 0;
        ConnectionState state;
        if (!result.Success && History.ConsecutiveFailures >= 2) state = ConnectionState.Down;
        else if (!result.Success || (recent.Count >= 4 && loss >= 20) || result.LatencyMs > 350 || avg > 350 || jitter > 100) state = ConnectionState.Unstable;
        else if ((recent.Count >= 4 && loss >= 5) || result.LatencyMs > 180 || avg > 180 || jitter > 60) state = ConnectionState.Degraded;
        else state = ConnectionState.Stable;

        if (state == ConnectionState.Stable)
        {
            History.StableSinceUtc ??= result.TimeUtc;
            var localStart = History.StableSinceUtc.Value.ToLocalTime();
            var localNow = result.TimeUtc.ToLocalTime();
            if (localStart.Date < localNow.Date && result.TimeUtc - History.StableSinceUtc.Value >= TimeSpan.FromHours(24))
                state = ConnectionState.LongStable;
        }
        else History.StableSinceUtc = null;
        History.State = state;
        return new TargetSnapshot(state, result.LatencyMs, loss, jitter, result.Message, History.StableSinceUtc);
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
                if (data != null && data.Settings.Targets?.Length == 2 && data.Histories?.Length == 2) return data;
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
