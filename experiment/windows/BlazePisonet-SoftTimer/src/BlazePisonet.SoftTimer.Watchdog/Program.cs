using System.Diagnostics;
using System.Text.Json;

namespace BlazePisonet.SoftTimer.Watchdog;

internal static class Program
{
    private static readonly string Root = Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.CommonApplicationData), "BlazeSystems", "BlazePisonetSoftTimer");
    private static readonly string ConfigPath = Path.Combine(Root, "config.json");
    private static readonly string MaintenancePath = Path.Combine(Root, "maintenance.until");
    private static readonly string LogPath = Path.Combine(Root, "watchdog.log");

    private static async Task Main()
    {
        using var mutex = new Mutex(true, @"Global\BlazePisonetSoftTimerWatchdog", out var created);
        if (!created) return;
        Directory.CreateDirectory(Root);
        Log("Watchdog started");

        while (true)
        {
            try
            {
                if (InMaintenance()) { await Task.Delay(3000); continue; }
                if (!SoftTimerEnabled()) { await Task.Delay(5000); continue; }
                if (Process.GetProcessesByName("BlazePisonet.SoftTimer").Length == 0)
                {
                    var exe = Path.Combine(AppContext.BaseDirectory, "BlazePisonet.SoftTimer.exe");
                    if (File.Exists(exe))
                    {
                        Process.Start(new ProcessStartInfo(exe) { UseShellExecute = true, WorkingDirectory = AppContext.BaseDirectory });
                        Log("SoftTimer process restarted");
                    }
                    else Log("SoftTimer executable missing: " + exe);
                }
            }
            catch (Exception ex) { Log("Watchdog error: " + ex.Message); }
            await Task.Delay(3000);
        }
    }

    private static bool SoftTimerEnabled()
    {
        try
        {
            if (!File.Exists(ConfigPath)) return false;
            using var doc = JsonDocument.Parse(File.ReadAllText(ConfigPath));
            return doc.RootElement.TryGetProperty("Enabled", out var e) && e.ValueKind == JsonValueKind.True;
        }
        catch { return false; }
    }

    private static bool InMaintenance()
    {
        try
        {
            if (!File.Exists(MaintenancePath)) return false;
            var text = File.ReadAllText(MaintenancePath).Trim();
            if (!long.TryParse(text, out var until)) { File.Delete(MaintenancePath); return false; }
            if (DateTimeOffset.UtcNow.ToUnixTimeSeconds() < until) return true;
            File.Delete(MaintenancePath);
        }
        catch { }
        return false;
    }

    private static void Log(string text)
    {
        try { File.AppendAllText(LogPath, $"{DateTimeOffset.Now:O} {text}{Environment.NewLine}"); } catch { }
    }
}
