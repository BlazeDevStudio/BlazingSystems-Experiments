using System.Globalization;
using System.Text;

namespace BlazeNetMonitor.Core;

public readonly record struct AppUsageEntry(string AppName, string ExecutablePath,
    long BytesSent, long BytesReceived)
{
    public long TotalBytes => (long)Math.Min(long.MaxValue,
        (decimal)Math.Max(0, BytesSent) + Math.Max(0, BytesReceived));
}

/// <summary>
/// Ranks Windows SRUM Network Data Usage records, not live connections.
/// The caller supplies a verified, local CSV export from SRUM.
/// SRUM timestamps mark the end of approximately hourly accumulation periods.
/// Exclude the reboot-boundary partial hour to avoid crediting preboot usage.
/// </summary>
public static class AppUsageRanking
{
    public static DateTimeOffset BootTimeUtc(DateTimeOffset nowUtc, TimeSpan uptime) =>
        nowUtc.ToUniversalTime() - uptime;

    public static IReadOnlyList<AppUsageEntry> TopFive(
        string csv, DateTimeOffset bootUtc, DateTimeOffset nowUtc)
    {
        if (string.IsNullOrWhiteSpace(csv) || csv.Length > 12_000_000) return [];
        var lines = csv.Replace("\r\n", "\n").Split('\n');
        if (lines.Length < 2) return [];
        var cols = ParseCsvRow(lines[0].TrimStart('\uFEFF'));
        int time = IndexOf(cols, "Timestamp");
        int app = IndexOf(cols, "App Name", "AppName");
        int sent = IndexOf(cols, "Bytes Sent", "BytesSent");
        int received = IndexOf(cols, "Bytes Received", "BytesReceived");
        if (time < 0 || app < 0 || sent < 0 || received < 0) return [];

        // All partial activity in the hour containing the reboot is excluded.
        // SRUM emits delayed hourly aggregate records; do not claim live totals.
        var safeStart = bootUtc.ToLocalTime().AddHours(1);
        var safeEnd = nowUtc.ToLocalTime();
        var totals = new Dictionary<string, (string path, long up, long down)>(
            StringComparer.OrdinalIgnoreCase);
        int maxCol = new[] { time, app, sent, received }.Max();
        foreach (var line in lines.Skip(1).Take(100_000))
        {
            if (line.Length == 0 || line.Length > 4096) continue;
            var fields = ParseCsvRow(line);
            if (fields.Count <= maxCol) continue;
            if (!DateTimeOffset.TryParse(fields[time], CultureInfo.CurrentCulture,
                    DateTimeStyles.AssumeLocal, out var when) &&
                !DateTimeOffset.TryParse(fields[time], CultureInfo.InvariantCulture,
                    DateTimeStyles.AssumeLocal, out when)) continue;
            if (when < safeStart || when > safeEnd.AddMinutes(5)) continue;
            if (!ReadPositiveLong(fields[sent], out long up) ||
                !ReadPositiveLong(fields[received], out long down)) continue;
            var value = fields[app].Trim().Trim('"');
            if (string.IsNullOrWhiteSpace(value)) continue;
            var path = value.EndsWith(".exe", StringComparison.OrdinalIgnoreCase)
                ? value : "";
            var name = path.Length > 0
                ? Path.GetFileNameWithoutExtension(path)
                : value;
            if (string.IsNullOrWhiteSpace(name) || name.Length > 160) continue;
            var key = value.ToLowerInvariant();
            totals.TryGetValue(key, out var previous);
            totals[key] = (path,
                SafeAdd(previous.up, up), SafeAdd(previous.down, down));
        }
        return totals.Select(kvp =>
            new AppUsageEntry(
                kvp.Value.path.Length > 0 ? Path.GetFileNameWithoutExtension(kvp.Value.path) : kvp.Key,
                kvp.Value.path,
                kvp.Value.up, kvp.Value.down))
            .Where(x => x.TotalBytes > 0)
            .OrderByDescending(x => x.TotalBytes)
            .ThenBy(x => x.AppName, StringComparer.OrdinalIgnoreCase)
            .Take(5)
            .ToArray();
    }

    private static long SafeAdd(long x, long y) =>
        y > long.MaxValue - x ? long.MaxValue : x + y;

    private static bool ReadPositiveLong(string s, out long value)
    {
        var clean = s.Trim().Replace(",", "").Replace(" ", "");
        return long.TryParse(clean, NumberStyles.None, CultureInfo.InvariantCulture, out value) &&
            value >= 0;
    }

    private static int IndexOf(IReadOnlyList<string> columns, params string[] names)
    {
        for (int i = 0; i < columns.Count; i++)
            if (names.Any(n => string.Equals(columns[i].Trim(), n,
                    StringComparison.OrdinalIgnoreCase))) return i;
        return -1;
    }

    private static List<string> ParseCsvRow(string row)
    {
        var fields = new List<string>();
        var buffer = new StringBuilder();
        bool quote = false;
        for (int i = 0; i < row.Length; i++)
        {
            char c = row[i];
            if (c == '"')
            {
                if (quote && i + 1 < row.Length && row[i + 1] == '"')
                {
                    buffer.Append('"'); i++;
                }
                else quote = !quote;
            }
            else if (c == ',' && !quote)
            {
                fields.Add(buffer.ToString()); buffer.Clear();
            }
            else buffer.Append(c);
        }
        fields.Add(buffer.ToString());
        return fields;
    }
}
