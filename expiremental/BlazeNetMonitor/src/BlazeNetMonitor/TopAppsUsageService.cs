using System.Diagnostics;
using BlazeNetMonitor.Core;

namespace BlazeNetMonitor;

/// <summary>
/// Optional historical Windows SRUM reader. Windows does not publish a simple,
/// unprivileged per-process "bytes since reboot" .NET API. We never substitute
/// TCP connection counts, disk I/O, or network-adapter totals as per-app bytes.
///
/// NetworkUsageView is NOT bundled or auto-downloaded (independent licensing).
/// When an operator places a copy beside the EXE, we can read its local CSV
/// export. A user-supplied SRUM CSV is an alternative. No elevation requested.
/// </summary>
internal sealed class TopAppsUsageService : IDisposable
{
    private readonly SemaphoreSlim _gate = new(1, 1);
    private DateTimeOffset _lastRefresh = DateTimeOffset.MinValue;
    private readonly CancellationTokenSource _stop = new();
    public IReadOnlyList<AppUsageEntry> Leaders { get; private set; } = [];
    public string Status { get; private set; } = "Waiting for Windows usage records";
    private static string CsvPath => Path.Combine(
        Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData),
        "BlazeSystems", "BlazeNetMonitor", "network-usage.csv");
    public static string SourcePath => CsvPath;

    public async Task RefreshAsync(bool force = false)
    {
        if (!force && DateTimeOffset.UtcNow - _lastRefresh < TimeSpan.FromMinutes(4))
            return;
        if (!await _gate.WaitAsync(0)) return;
        try
        {
            _lastRefresh = DateTimeOffset.UtcNow;
            var toolPath = new[]
            {
                Path.Combine(AppContext.BaseDirectory, "NetworkUsageView.exe"),
                Path.Combine(Path.GetDirectoryName(CsvPath)!, "NetworkUsageView.exe")
            }.FirstOrDefault(File.Exists);

            string? csv = null;
            string source;
            if (toolPath is not null)
            {
                csv = await ExportFromInstalledReader(toolPath, _stop.Token);
                source = "Windows SRUM";
            }
            else if (File.Exists(CsvPath) &&
                     new FileInfo(CsvPath).Length is > 0 and < 12_000_000)
            {
                csv = await File.ReadAllTextAsync(CsvPath, _stop.Token);
                source = "Imported Windows records";
            }
            else
            {
                Leaders = [];
                Status = "App usage history unavailable";
                return;
            }

            if (csv is null)
            {
                Leaders = [];
                Status = "Windows usage records unavailable";
                return;
            }
            var now = DateTimeOffset.UtcNow;
            var boot = AppUsageRanking.BootTimeUtc(now,
                TimeSpan.FromMilliseconds(Environment.TickCount64));
            Leaders = AppUsageRanking.TopFive(csv, boot, now);
            Status = Leaders.Count > 0
                ? $"{source} · complete hours since restart"
                : "No completed usage records since restart";
        }
        catch (OperationCanceledException) { }
        catch (Exception)
        {
            Leaders = [];
            Status = "App usage history unavailable";
        }
        finally { _gate.Release(); }
    }

    private static async Task<string?> ExportFromInstalledReader(string executable,
        CancellationToken cancelled)
    {
        if (!Path.IsPathFullyQualified(executable) ||
            executable.StartsWith(@"\\", StringComparison.Ordinal) ||
            !File.Exists(executable)) return null;
        using var timeout = CancellationTokenSource.CreateLinkedTokenSource(cancelled);
        timeout.CancelAfter(TimeSpan.FromSeconds(18));
        using var process = new Process();
        process.StartInfo = new ProcessStartInfo
        {
            FileName = executable, UseShellExecute = false,
            RedirectStandardOutput = true,
            RedirectStandardError = false,
            CreateNoWindow = true, WindowStyle = ProcessWindowStyle.Hidden
        };
        process.StartInfo.ArgumentList.Add("/scomma");
        process.StartInfo.ArgumentList.Add("");
        process.StartInfo.ArgumentList.Add("/Columns");
        process.StartInfo.ArgumentList.Add("Timestamp,App Name,Bytes Sent,Bytes Received");
        process.Start();
        try
        {
            var buffer = new char[8192];
            var output = new System.Text.StringBuilder();
            while (true)
            {
                int n = await process.StandardOutput.ReadAsync(
                    buffer.AsMemory(), timeout.Token);
                if (n == 0) break;
                if (output.Length + n > 12_000_000) return null;
                output.Append(buffer, 0, n);
            }
            await process.WaitForExitAsync(timeout.Token);
            return process.ExitCode == 0 ? output.ToString() : null;
        }
        finally
        {
            if (!process.HasExited)
            {
                try { process.Kill(entireProcessTree: true); }
                catch (InvalidOperationException) { }
            }
        }
    }

    public static bool ImportCsv(IWin32Window owner)
    {
        using var picker = new OpenFileDialog
        {
            Title = "Import Windows network usage (SRUM CSV)",
            Filter = "CSV files|*.csv|All files|*.*", CheckFileExists = true
        };
        if (picker.ShowDialog(owner) != DialogResult.OK) return false;
        try
        {
            if (new FileInfo(picker.FileName).Length > 12_000_000)
                throw new InvalidDataException("CSV exceeds 12 MB.");
            string firstLine = File.ReadLines(picker.FileName).FirstOrDefault() ?? "";
            if (!firstLine.Contains("Timestamp", StringComparison.OrdinalIgnoreCase) ||
                !firstLine.Contains("Bytes", StringComparison.OrdinalIgnoreCase))
                throw new InvalidDataException("Select a network usage CSV with time and byte columns.");
            Directory.CreateDirectory(Path.GetDirectoryName(CsvPath)!);
            File.Copy(picker.FileName, CsvPath, overwrite: true);
            return true;
        }
        catch (Exception e)
        {
            MessageBox.Show(owner, e.Message, "Network usage",
                MessageBoxButtons.OK, MessageBoxIcon.Warning);
            return false;
        }
    }

    public void Dispose()
    {
        _stop.Cancel(); _stop.Dispose(); _gate.Dispose();
    }
}
