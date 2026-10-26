using BlazeNetMonitor.Core;

int passed = 0;
void Check(bool value, string label)
{
    if (!value) throw new Exception("FAIL " + label);
    Console.WriteLine("PASS " + label);
    passed++;
}
var start = DateTimeOffset.UtcNow;
var m = MonitorMath.Compute(100, 200, 300, 700, TimeSpan.FromSeconds(2));
Check(m.UploadBytesPerSecond == 100 && m.DownloadBytesPerSecond == 250, "traffic rate uses elapsed time");
Check(MonitorMath.Compute(999, 999, 1, 1, TimeSpan.FromSeconds(1)) == new SpeedSample(0, 0), "counter reset does not spike");
Check(MonitorMath.Compute(1, 1, 100, 100, TimeSpan.Zero) == new SpeedSample(0, 0), "zero interval does not divide");
Check(MonitorMath.Rate(125000, true) == "1 Mbps", "bits rate display");
Check(MonitorMath.Rate(1000, false) == "1 KB/s", "bytes rate display");
var totals = new TrafficTotals();
totals.Add(10, 20, new DateTime(2026, 10, 31, 23, 50, 0));
totals.Add(3, 7, new DateTime(2026, 11, 1, 0, 0, 0));
Check(totals.SessionUpload == 13 && totals.SessionDownload == 27, "session survives day boundary");
Check(totals.TodayUpload == 3 && totals.TodayDownload == 7, "daily rollover");
Check(totals.MonthUpload == 3 && totals.MonthDownload == 7, "monthly rollover");
totals.Add(-500, -40, new DateTime(2026, 11, 1, 0, 1, 0));
Check(totals.TodayUpload == 3 && totals.TodayDownload == 7, "negative traffic deltas ignored");
var good = new QualityTracker();
var s = good.Add(new ProbeResult(start, true, 22, "OK"), 5);
Check(s.State == ConnectionState.Stable, "healthy green");
s = good.Add(new ProbeResult(start.AddSeconds(5), true, 220, "OK"), 5);
Check(s.State == ConnectionState.Degraded, "high latency yellow");
s = good.Add(new ProbeResult(start.AddSeconds(10), true, 700, "OK"), 5);
Check(s.State == ConnectionState.Unstable, "high latency orange");
var down = new QualityTracker();
down.Add(new ProbeResult(start, false, 0, "timeout"), 5);
s = down.Add(new ProbeResult(start.AddSeconds(5), false, 0, "timeout"), 5);
Check(s.State == ConnectionState.Down, "two failures red");
var gap = new QualityTracker();
gap.Add(new ProbeResult(start, true, 20, "OK"), 5);
s = gap.Add(new ProbeResult(start.AddMinutes(10), true, 20, "OK"), 5);
Check(s.StableSinceUtc == start.AddMinutes(10), "sleep gap resets stability");
var persisted = new TargetHistory { StableSinceUtc = start.AddHours(-25), LastSampleUtc = start.AddSeconds(-5), State = ConnectionState.Stable };
var blue = new QualityTracker(persisted);
s = blue.Add(new ProbeResult(start, true, 30, "OK"), 5);
Check(s.State == ConnectionState.LongStable || persisted.StableSinceUtc != start.AddHours(-25), "blue requires calendar crossover and full 24 hours");
var shifted = new QualityTracker(new TargetHistory { StableSinceUtc = start.AddHours(-25), LastSampleUtc = start.AddSeconds(-5), State = ConnectionState.Stable });
s = shifted.Add(new ProbeResult(start, false, 0, "fail"), 5);
Check(s.StableSinceUtc == null, "failure revokes prior stable streak");
var path = Path.Combine(Path.GetTempPath(), "blazenetmonitor-test-" + Guid.NewGuid().ToString("N"), "state.json");
try
{
    var store = new Storage(path);
    var state = new PersistedData(); state.Settings.Targets[0].Address = "example.com";
    state.Settings.WidgetOpacityPercent = 67;
    state.Settings.WidgetWidth = 420;
    state.Settings.WidgetHeight = 98;
    state.Settings.WidgetX = 123;
    state.Settings.WidgetY = 234;
    state.Settings.ThemeMode = "Light";
    state.Settings.FreeformPositioned = true;
    state.Settings.ShowGraphs = false;
    store.Save(state);
    Check(store.Load().Settings.Targets[0].Address == "example.com", "atomic settings roundtrip");
    var loadedSettings = store.Load().Settings;
    Check(loadedSettings.FreeformPositioned && loadedSettings.WidgetX == 123 &&
          loadedSettings.WidgetY == 234 && loadedSettings.WidgetWidth == 420 &&
          loadedSettings.WidgetHeight == 98, "freeform geometry roundtrip");
    Check(loadedSettings.WidgetOpacityPercent == 67 &&
          loadedSettings.ThemeMode == "Light" && !loadedSettings.ShowGraphs,
          "appearance settings roundtrip");
    File.WriteAllText(path, "{INVALID JSON");
    Check(store.Load().Settings.Targets.Length == 2, "corrupt settings fail safe");
}
finally { Directory.Delete(Path.GetDirectoryName(path)!, true); }
Check(WindowsVersionPolicy.CanUseClassicDeskBand(new Version(10, 0, 19045)),
    "Windows 10 classic deskband eligible");
Check(!WindowsVersionPolicy.CanUseClassicDeskBand(new Version(10, 0, 22631)),
    "Windows 11 deskband fail closed");
Check(!WindowsVersionPolicy.CanUseClassicDeskBand(new Version(10, 0, 26100)),
    "modern Windows 11 deskband fail closed");
Check(!WindowsVersionPolicy.IsNativeHostReady(new Version(10, 0, 19045), false),
    "OS detection alone cannot claim native integration");
Check(WindowsVersionPolicy.ShellFamily(new Version(6, 1, 7601)) == "Unknown",
    "unsupported older Windows family rejected");
var work = new System.Drawing.Rectangle(0, 0, 1366, 720);
var safe = WidgetGeometry.Constrain(new System.Drawing.Rectangle(2, 705, 312, 64), work);
Check(safe.Bottom <= 720 - 5, "geometry never hides its bottom behind taskbar");
var fromLeft = WidgetGeometry.Constrain(new System.Drawing.Rectangle(-450, -50, 312, 64), work);
Check(fromLeft.Left >= 0 && fromLeft.Top >= 0, "offscreen geometry recovers");
var pos = WidgetGeometry.Constrain(new System.Drawing.Rectangle(100, 160, 260, 72), work);
Check(pos.Left == 100 && pos.Top == 160, "valid freeform geometry preserved");
var raw = new AppSettings { HoverOpacityPercent = 58, AutoHideForFullscreen = false };
var clone = raw.Copy();
clone.Targets[0].Address = "changed.local";
Check(raw.Targets[0].Address == "1.1.1.1" && clone.HoverOpacityPercent == 58 &&
      !clone.AutoHideForFullscreen, "settings preview copy isolates targets");
Console.WriteLine($"RESULT {passed} tests passed");
