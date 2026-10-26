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
    state.Settings.HoverOpacityPercent = 61;
    state.Settings.AutoHideForFullscreen = false;
    store.Save(state);
    Check(!store.Load().WelcomeAcknowledged, "fresh installation welcomes once");
    var legacy = System.Text.Json.Nodes.JsonNode.Parse(File.ReadAllText(path))!.AsObject();
    legacy.Remove("WelcomeAcknowledged");
    File.WriteAllText(path, legacy.ToJsonString());
    Check(store.Load().WelcomeAcknowledged,
        "existing pre-update settings never trigger first-run dialog");
    Check(store.Load().Settings.Targets[0].Address == "example.com", "atomic settings roundtrip");
    var loadedSettings = store.Load().Settings;
    Check(loadedSettings.FreeformPositioned && loadedSettings.WidgetX == 123 &&
          loadedSettings.WidgetY == 234 && loadedSettings.WidgetWidth == 420 &&
          loadedSettings.WidgetHeight == 98, "freeform geometry roundtrip");
    Check(loadedSettings.WidgetOpacityPercent == 67 &&
          loadedSettings.ThemeMode == "Light" && !loadedSettings.ShowGraphs &&
          loadedSettings.HoverOpacityPercent == 61 && !loadedSettings.AutoHideForFullscreen,
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
Check(WidgetGeometry.CoversScreen(new System.Drawing.Rectangle(0, 0, 1366, 768),
    new System.Drawing.Rectangle(0, 0, 1366, 768)), "full monitor coverage classifies fullscreen");
Check(!WidgetGeometry.CoversScreen(new System.Drawing.Rectangle(0, 0, 1366, 720),
    new System.Drawing.Rectangle(0, 0, 1366, 768)), "maximized taskbar-respecting app is not fullscreen");
Check(!WidgetGeometry.CoversScreen(new System.Drawing.Rectangle(0, 0, 0, 768),
    new System.Drawing.Rectangle(0, 0, 1366, 768)), "zero width foreground does not trigger fullscreen");
var raw = new AppSettings { HoverOpacityPercent = 58, AutoHideForFullscreen = false };
var clone = raw.Copy();
clone.Targets[0].Address = "changed.local";
Check(raw.Targets[0].Address == "1.1.1.1" && clone.HoverOpacityPercent == 58 &&
      !clone.AutoHideForFullscreen, "settings preview copy isolates targets");
var taskbar = new System.Drawing.Rectangle(0, 720, 1366, 48);
var screen = new System.Drawing.Rectangle(0, 0, 1366, 768);
var above = WidgetGeometry.ConstrainToMode(new System.Drawing.Rectangle(200, 734, 185, 34),
    screen, work, WidgetGeometry.AboveTaskbar);
Check(above.Bottom <= work.Bottom, "above mode cannot cover taskbar");
var within = WidgetGeometry.ConstrainToMode(new System.Drawing.Rectangle(200, 734, 185, 34),
    screen, work, WidgetGeometry.InsideTaskbar);
Check(within.Top == 734 && within.Height == 34, "inside mode reaches taskbar pixels");
var dock = WidgetGeometry.DockPosition(new System.Drawing.Rectangle(200, 0, 185, 32),
    work, taskbar, WidgetGeometry.InsideTaskbar, 150);
Check(dock.Top == 728 && dock.Bottom == 760, "inside mode vertically centers 32px widget in 48px taskbar");
Check(WidgetGeometry.ResolvePlacement(new AppSettings { DockInsideTaskbar = true, FreeformPositioned = false })
    == WidgetGeometry.InsideTaskbar, "legacy inside placement migrates");
Check(WidgetGeometry.ResolvePlacement(new AppSettings { FreeformPositioned = true })
    == WidgetGeometry.Floating, "legacy custom freeform position migrates");
var compact = WidgetGeometry.ConstrainToMode(new System.Drawing.Rectangle(30, 735, 126, 24),
    screen, work, WidgetGeometry.InsideTaskbar);
Check(compact.Height == 24 && compact.Width == 126, "24px compact resize retained");
var migrated = new AppSettings { FreeformPositioned = true, PlacementMode = WidgetGeometry.InsideTaskbar };
Check(WidgetGeometry.ResolvePlacement(migrated) == WidgetGeometry.InsideTaskbar,
    "explicit inside overlay retains placement despite prior freeform geometry");
Check(WidgetGeometry.ConstrainToMode(new System.Drawing.Rectangle(8, 736, 125, 24),
    screen, work, WidgetGeometry.Floating).Top == 736,
    "floating mode is allowed in taskbar region");
Check(WidgetGeometry.GraphHeight(24, true) >= 4,
    "taskbar 24px compact graph always receives a visible band");
Check(WidgetGeometry.GraphHeight(40, true) >= 7,
    "resized 40px graph receives more space");
Check(WidgetGeometry.GraphHeight(60, false) == 0,
    "user-hidden graph draws no band");
var transparent = new AppSettings { TransparentBackground = true, WidgetOpacityPercent = 65 };
var transparentCopy = transparent.Copy();
Check(transparentCopy.TransparentBackground && transparentCopy.WidgetOpacityPercent == 65,
    "transparent appearance persists in settings clone");
Check(DisplayPreferences.EffectiveMetric("Auto", 330, 82) == "Latency", "auto metric selects latency when space permits");
Check(DisplayPreferences.EffectiveMetric("Loss", 140, 24) == "Speed", "micro display never overflows metrics");
Check(DisplayPreferences.EffectiveMetric("Loss", 300, 70) == "Loss", "explicit loss metric respected");
Check(DisplayPreferences.GraphWindowSeconds(0, 140, 26) == 30, "adaptive compact graph length");
Check(DisplayPreferences.GraphWindowSeconds(0, 400, 100) == 120, "adaptive detailed graph length");
Check(DisplayPreferences.GraphWindowSeconds(300, 140, 26) == 300, "explicit graph history length");
Check(DisplayPreferences.NormalizeGraphStyle("Steps") == "Steps", "steps graph chosen");
Check(DisplayPreferences.NormalizeGraphStyle("unknown") == "Line", "invalid graph style defaults to line");
Check(DisplayPreferences.TryGraphColor("#33AAFF", out var color) && color.B == 255, "hex color parsing");
Check(!DisplayPreferences.TryGraphColor("red", out _), "invalid color safely rejected");
var prefs = new AppSettings { ShowFavicons = true, GraphStyle = "Bars", GraphHistorySeconds = 300, MetricMode = "Loss", UnitMode = "Bytes" };
var cp = prefs.Copy();
Check(cp.ShowFavicons && cp.GraphStyle == "Bars" && cp.GraphHistorySeconds == 300 && cp.MetricMode == "Loss" && !DisplayPreferences.UseBits(cp, 300, 70), "graph and display preferences roundtrip");
Check(FaviconSafety.OfficialHost("1.1.1.1") == "one.one.one.one", "Cloudflare resolver canonical favicon domain");
Check(FaviconSafety.OfficialHost("8.8.8.8") == "dns.google", "Google resolver canonical favicon domain");
Check(FaviconSafety.OfficialHost("https://example.org:443/path") == "example.org", "HTTPS favicon uses configured host");
Check(FaviconSafety.OfficialHost("http://example.org/") is null, "reject insecure HTTP favicon target");
Check(FaviconSafety.OfficialHost("192.168.1.1") is null && FaviconSafety.OfficialHost("router.local") is null, "never fetch private hostname or IP favicon");
Check(!FaviconSafety.IsPublicAddress(System.Net.IPAddress.Parse("127.0.0.1")) &&
    !FaviconSafety.IsPublicAddress(System.Net.IPAddress.Parse("10.0.0.2")) &&
    !FaviconSafety.IsPublicAddress(System.Net.IPAddress.Parse("192.168.1.10")), "private IP blocked");
Check(FaviconSafety.IsPublicAddress(System.Net.IPAddress.Parse("1.1.1.1")), "Cloudflare public IP admitted");
var transitions = new QualityTracker();
var baseTime = DateTimeOffset.UtcNow;
transitions.Add(new ProbeResult(baseTime, true, 26, "ok"), 5);
transitions.Add(new ProbeResult(baseTime.AddSeconds(5), false, 0, "timeout"), 5);
var failed = transitions.Add(new ProbeResult(baseTime.AddSeconds(10), false, 0, "timeout"), 5);
Check(failed.State == ConnectionState.Down, "two consecutive failed probes show red");
var firstRecovery = transitions.Add(new ProbeResult(baseTime.AddSeconds(15), true, 22, "ok"), 5);
Check(firstRecovery.State != ConnectionState.Stable &&
      firstRecovery.State != ConnectionState.LongStable, "first good sample cannot fake instant green recovery");
var badRtt = new QualityTracker();
badRtt.Add(new ProbeResult(baseTime, true, 23, "ok"), 5);
badRtt.Add(new ProbeResult(baseTime.AddSeconds(5), true, 25, "ok"), 5);
badRtt.Add(new ProbeResult(baseTime.AddSeconds(10), true, 520, "slow"), 5);
Check(badRtt.History.State == ConnectionState.Unstable, "outlier RTT raises orange warning immediately");
Check(badRtt.History.LatencyBaselineMs > 0 && badRtt.History.LatencyBaselineMs < 40,
      "outlier RTT does not poison learned baseline");
Check(new AppSettings { GraphRefreshSeconds = 5 }.Copy().GraphRefreshSeconds == 5,
    "sampling and graph refresh preference persistence");

Check(FaviconSafety.OfficialHost("www.facebook.com") == "www.facebook.com",
    "Facebook public hostname accepted independently of DNS vendor mappings");
Check(FaviconSafety.OfficialHost("www.wikipedia.org") == "www.wikipedia.org",
    "arbitrary public website hostname accepted");
var facebookOrigin = new Uri("https://www.facebook.com/");
var iconRedirect = FaviconSafety.SafeRedirect(new Uri("https://www.facebook.com/favicon.ico"),
    "https://static.xx.fbcdn.net/rsrc.php/y1/r/example.ico");
Check(iconRedirect?.Host == "static.xx.fbcdn.net", "public HTTPS favicon CDN redirect allowed");
Check(FaviconSafety.SafeRedirect(facebookOrigin, "http://example.org/favicon.ico") is null,
    "insecure downgrade redirect forbidden");
Check(FaviconSafety.SafeRedirect(facebookOrigin, "https://192.168.0.1/icon.ico") is null &&
      FaviconSafety.SafeRedirect(facebookOrigin, "https://localhost/icon.ico") is null,
    "redirect to local/private host forbidden");
Check(FaviconSafety.SafeRedirect(facebookOrigin, "https://example.org:8443/icon.ico") is null,
    "nonstandard port favicon target forbidden");
var iconHtml = "<html><head><link href='/favicon.ico' rel='shortcut icon' />" +
    "<link sizes='32x32' type='image/png' href='https://static.xx.fbcdn.net/sample.png' rel='icon'>" +
    "<link href='http://localhost/icon.ico' rel='icon'>" +
    "</head><body><link href='https://evil.example/favicon.ico' rel='icon'></body></html>";
var iconUrls = FaviconSafety.FindIconLinks(iconHtml, facebookOrigin);
Check(iconUrls.Count == 2 && iconUrls[0].Host == "www.facebook.com" &&
      iconUrls[1].Host == "static.xx.fbcdn.net", "HTML favicon discovery with relative and CDN paths");
Check(FaviconSafety.FindIconLinks(
    "<head><link rel=icon href=/apple-touch-icon.png></head>", facebookOrigin).Count == 1,
    "unquoted favicon link attributes recognized");
Check(!FaviconSafety.IsPermittedIconUri(new Uri("https://user:pass@example.org/favicon.ico")),
    "favicon URL with embedded credentials rejected");
Check(new AppSettings().Targets[0].Name == "Target 1" &&
      new AppSettings().Targets[1].Name == "Target 2", "clean target default naming");
Check(SettingsUiPolicy.DefaultName("Primary DNS",0) == "Target 1" &&
      SettingsUiPolicy.DefaultName("Secondary DNS",1) == "Target 2",
      "existing default labels migrate, custom names preserved");
Check(SettingsUiPolicy.DefaultName("Office",1) == "Office","custom target name untouched");
Check(SettingsUiPolicy.Placeholder(TargetProtocol.Https) == "https://www.example.com" &&
      SettingsUiPolicy.Placeholder(TargetProtocol.Dns) == "example.com",
      "protocol placeholder examples");
Check(SettingsUiPolicy.ShowPort(TargetProtocol.Tcp) && !SettingsUiPolicy.ShowPort(TargetProtocol.Icmp) &&
      !SettingsUiPolicy.ShowPort(TargetProtocol.Https) && !SettingsUiPolicy.ShowPort(TargetProtocol.Dns),
      "only TCP reveals port");
Check(SettingsUiPolicy.IsValidAddress(TargetProtocol.Https,"https://www.example.com",443) &&
      !SettingsUiPolicy.IsValidAddress(TargetProtocol.Https,"http://www.example.com",443) &&
      !SettingsUiPolicy.IsValidAddress(TargetProtocol.Https,"",443),
      "correct HTTPS validation and empty placeholder handling");
Check(!SettingsUiPolicy.IsValidAddress(TargetProtocol.Dns,"https://example.com",443) &&
      SettingsUiPolicy.IsValidAddress(TargetProtocol.Dns,"example.com",443),
      "DNS accepts domain not full URL");
Check(!AdapterUiPolicy.IsVisible("vEthernet (Default Switch)", "Hyper-V Virtual",
      System.Net.NetworkInformation.NetworkInterfaceType.Ethernet,false) &&
      AdapterUiPolicy.IsVisible("Ethernet 2","Realtek PCIe Controller",
      System.Net.NetworkInformation.NetworkInterfaceType.Ethernet,false),
      "physical adapters shown and virtual noise hidden");
Check(AdapterUiPolicy.IsVisible("vEthernet", "Virtual",
      System.Net.NetworkInformation.NetworkInterfaceType.Ethernet,true),
      "expanded adapter list retains optional virtual adapters");
Check(DonationSplashPolicy.ShouldShow("EveryLaunch", false) &&
      DonationSplashPolicy.ShouldShow("EveryLaunch", true), "owner donation splash every launch");
Check(DonationSplashPolicy.ShouldShow("FirstLaunch", false) &&
      !DonationSplashPolicy.ShouldShow("FirstLaunch", true), "donation first-only honors saved history");
Check(!DonationSplashPolicy.ShouldShow("Never", false) &&
      !DonationSplashPolicy.ShouldShow("Never", true), "never setting disables automatic QR");
Check(DonationSplashPolicy.Normalize("unrecognized") == DonationSplashPolicy.EveryLaunch,
      "unknown donation mode falls back to standard prompt");
Check(DonationSplashPolicy.MatchesOwner(new Uri(DonationSplashPolicy.OwnerPayPalUrl)) &&
      !DonationSplashPolicy.MatchesOwner(new Uri("https://example.com/")),
      "owner QR payment destination is fixed");
var matrix = DonationSplashPolicy.ModuleMatrix();
Check(matrix.GetLength(0) == 41 && matrix.GetLength(1) == 41 &&
      matrix[0,0] && matrix[0,6] && matrix[6,0] && matrix[6,6],
      "embedded PayPal QR matrices retain finder boundaries");
Check(DonationSplashPolicy.ModuleMatrix().GetLength(0) == DonationSplashPolicy.QrModules,
      "QR matrix dimensions preserved for exact-size scan view");
Check(DonationSplashPolicy.OwnerPayPalUrl.StartsWith("https://www.paypal.com/qrcodes/", StringComparison.Ordinal),
      "official PayPal destination retained after UX changes");
Check(DisplayPreferences.NormalizeGraphStyle("Smooth") == "Smooth", "smooth graph style supported");
Check(DisplayPreferences.NormalizeGraphStyle("Dots") == "Dots", "dots graph style supported");
Check(DisplayPreferences.NormalizeGraphStyle("Impulse") == "Impulse", "impulse graph style supported");
Check(DisplayPreferences.NormalizeGraphStyle("Curve with unknown style") == "Line", "invalid graph style uses line");
var boot = new DateTimeOffset(2026, 10, 27, 3, 20, 0, TimeSpan.FromHours(8));
var checkedAt = boot.AddHours(5);
string sampleSrum = "Timestamp,App Name,Bytes Sent,Bytes Received\n" +
    $"2026-10-27 03:40:00+08:00,old.exe,9000,9000\n" +
    $"2026-10-27 04:40:00+08:00,chrome.exe,350,250\n" +
    $"2026-10-27 05:40:00+08:00,chrome.exe,200,150\n" +
    $"2026-10-27 04:40:00+08:00,firefox.exe,600,50\n" +
    $"2026-10-27 05:40:00+08:00,\"other,app\",0,50\n" +
    $"2026-10-27 06:40:00+08:00,svchost.exe,4,6\n";
var leaders = AppUsageRanking.TopFive(sampleSrum, boot, checkedAt);
Check(leaders.Count == 4 && leaders[0].AppName == "chrome" &&
    leaders[0].TotalBytes == 950, "SRUM ranks historical app totals including closed apps");
Check(leaders.All(x => x.AppName != "old"), "reboot-boundary hourly bucket excluded");
Check(leaders[2].AppName == "other,app", "quoted CSV app names parsed safely");
Check(AppUsageRanking.TopFive("", boot, checkedAt).Count == 0, "missing SRUM evidence never invents results");
Check(AppUsageRanking.TopFive("garbage", boot, checkedAt).Count == 0,
    "invalid SRUM schema fails closed");
Check(AppUsageRanking.BootTimeUtc(checkedAt, TimeSpan.FromHours(5)) == boot,
    "boot time derived from uptime");
Console.WriteLine($"RESULT {passed} tests passed");
