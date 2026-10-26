using System.Runtime.InteropServices;
using System.Threading;

namespace BlazeNetMonitor;

internal static class Program
{
    internal const string RequestAckName = @"Local\BlazeSystems.BlazeNetMonitor.RequestAcknowledged";

    [DllImport("user32.dll", CharSet = CharSet.Unicode, SetLastError = true)]
    private static extern uint RegisterWindowMessage(string name);
    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool PostMessage(nint hWnd, uint msg, nint wParam, nint lParam);

    internal static readonly uint ShowSettingsMessage =
        RegisterWindowMessage("BlazeSystems.BlazeNetMonitor.ShowSettings.v1");

    [STAThread]
    private static int Main(string[] args)
    {
        ApplicationConfiguration.Initialize();
        // Real GDI+ QR and WinForms layout checks on the Windows CI runner.
        if (args.Contains("--verify-qr-render", StringComparer.OrdinalIgnoreCase))
            return VerifyQrRendering();
        if (args.Contains("--verify-network-connections", StringComparer.OrdinalIgnoreCase))
            return VerifyNetworkConnections();
        if (args.Contains("--verify-top-apps", StringComparer.OrdinalIgnoreCase))
            return VerifyTopApps();
        using var single = new Mutex(true, @"Local\BlazeSystems.BlazeNetMonitor", out var owner);
        using var acknowledged = new EventWaitHandle(false, EventResetMode.AutoReset, RequestAckName);
        if (!owner)
        {
            // Reopen the running instance's settings instead of spawning duplicates.
            if (ShowSettingsMessage != 0)
                PostMessage((nint)0xFFFF, ShowSettingsMessage, 0, 0); // HWND_BROADCAST
            if (!acknowledged.WaitOne(650))
                MessageBox.Show(
                    "BlazeNetMonitor is already running. The existing process may be an older version. " +
                    "Use the notification-area (hidden icons ^) menu → Exit BlazeNetMonitor, " +
                    "then launch this new version. Do not run both builds together.",
                    "BlazeNetMonitor · Already running",
                    MessageBoxButtons.OK, MessageBoxIcon.Information);
            return 0;
        }
        Application.Run(new MonitorForm());
        return 0;
    }

    private static int VerifyQrRendering()
    {
        try
        {
            foreach (int size in new[] { 154, 240, 352 })
            {
                using var image = DonationAssets.CreateQrBitmap(size);
                if (image.Width != size || image.Height != size)
                    throw new InvalidOperationException($"QR size mismatch at {size}.");
                if (image.GetPixel(0, 0).ToArgb() != Color.White.ToArgb())
                    throw new InvalidOperationException("QR quiet-zone corner is not white.");
                // Verify finder blue is present; center letter artwork can have
                // a white pixel at the precise center depending on GDI+ font metrics.
                int finder = (int)Math.Round(size * .078 + (size * .844 / 41d) * 3.5);
                if (image.GetPixel(finder, finder).ToArgb() == Color.White.ToArgb())
                    throw new InvalidOperationException("QR finder mark is missing.");
            }
            using (var splash = new DonationSplashForm(() => { }))
            {
                var view = splash.Controls.OfType<PictureBox>().Single();
                if (view.Image is null || view.Image.Width > view.ClientSize.Width ||
                    view.Image.Height > view.ClientSize.Height || splash.Opacity != 1d)
                    throw new InvalidOperationException("Splash QR is cropped or faded.");
            }
            using (var editor = new SettingsForm(new BlazeNetMonitor.Core.AppSettings()))
            {
                var tabs = editor.Controls.OfType<TabControl>().Single();
                var about = tabs.TabPages.Cast<TabPage>().Single(t => t.Text == "About");
                var qr = about.Controls.OfType<PictureBox>()
                    .Single(p => p.Image is { Width: >= 200 });
                if (qr.Image is null || qr.Image.Width > qr.Width || qr.Image.Height > qr.Height)
                    throw new InvalidOperationException("About QR image is cropped.");
                if (about.Controls.OfType<ComboBox>().Any(c => c.Items.Cast<object>()
                        .Any(x => x.ToString()?.Contains("Every launch") == true)))
                    throw new InvalidOperationException("About still contains startup settings.");
            }
            return 0;
        }
        catch (Exception ex)
        {
            File.WriteAllText(Path.Combine(Path.GetTempPath(),
                "BlazeNetMonitor-QR-render-failure.txt"), ex.ToString());
            return 3;
        }
    }

    private static int VerifyNetworkConnections()
    {
        try
        {
            var defaults = WindowsConnectionsView.Enumerate(false, out bool fromShell);
            var advanced = WindowsConnectionsView.Enumerate(true, out _);
            if (fromShell)
            {
                if (!WindowsConnectionsView.TryReadNetworkConnections(out var names))
                    throw new InvalidOperationException("Shell folder unavailable on second read");
                if (defaults.Any(n => !names.Contains(n.Name, StringComparer.OrdinalIgnoreCase)))
                    throw new InvalidOperationException("Default adapter is absent from ncpa.cpl");
            }
            else if (defaults.Count != 0)
            {
                throw new InvalidOperationException("Default list leaked guessed interfaces");
            }

            File.WriteAllText(Path.Combine(Path.GetTempPath(),
                "BlazeNetMonitor-adapter-check.txt"),
                $"Network Connections shell available: {fromShell}\n" +
                $"Default listed: {defaults.Count}\n" +
                $"Advanced listed: {advanced.Count}\n" +
                string.Join("\n", defaults.Select(n => n.Label)));
            return 0;
        }
        catch (Exception e)
        {
            File.WriteAllText(Path.Combine(Path.GetTempPath(),
                "BlazeNetMonitor-adapter-check.txt"), e.ToString());
            return 3;
        }
    }

    private static int VerifyTopApps()
    {
        try
        {
            using var glance = new InfoForm();
            var mock = Enumerable.Range(1, 7)
                .Select(n => new BlazeNetMonitor.Core.AppUsageEntry(
                    $"Test program {n}", "", 100L * n, 200L * n))
                .ToArray();
            glance.RefreshTopApps(mock, "Test Windows SRUM export");
            if (glance.ClientSize.Height < 390)
                throw new InvalidOperationException("Top-five hover rows were clipped");
            using var bitmap = new Bitmap(glance.Width, glance.Height);
            glance.DrawToBitmap(bitmap, new Rectangle(0, 0, bitmap.Width, bitmap.Height));
            glance.RefreshTopApps([], "No Windows history");
            if (glance.ClientSize.Height > 310)
                throw new InvalidOperationException("Empty top-five hover did not compact");
            File.WriteAllText(Path.Combine(Path.GetTempPath(),
                "BlazeNetMonitor-top-apps-check.txt"),
                "PASS top five app icons/drawing, cumulative historical layout and compact empty state");
            return 0;
        }
        catch (Exception ex)
        {
            File.WriteAllText(Path.Combine(Path.GetTempPath(),
                "BlazeNetMonitor-top-apps-check.txt"), ex.ToString());
            return 3;
        }
    }
}
