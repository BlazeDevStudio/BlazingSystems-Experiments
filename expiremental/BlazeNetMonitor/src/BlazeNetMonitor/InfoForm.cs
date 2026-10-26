using System.Drawing.Drawing2D;
using BlazeNetMonitor.Core;

namespace BlazeNetMonitor;

// Compact nonactivating at-a-glance panel: separate alpha and a bounded footprint.
internal sealed class InfoForm : Form
{
    private string _adapter = "Checking network", _ipv4 = "—", _up = "0 bps", _down = "0 bps";
    private string _today = "", _month = "", _uptime = "";
    private readonly string[] _targetNames = new string[2];
    private readonly TargetSnapshot[] _targetStates = new TargetSnapshot[2];
    private IReadOnlyList<AppUsageEntry> _topApps = [];
    private string _topStatus = "Windows usage history unavailable";
    private readonly Dictionary<string, Bitmap> _icons = new(StringComparer.OrdinalIgnoreCase);

    public InfoForm()
    {
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        TopMost = true;
        DoubleBuffered = true;
        ClientSize = new Size(356, 289);
        AccessibleName = "BlazeNetMonitor network status at a glance";
    }
    protected override bool ShowWithoutActivation => true;
    protected override CreateParams CreateParams
    {
        get
        {
            var p = base.CreateParams;
            p.ExStyle |= 0x80 | 0x08000000; // toolwindow, NOACTIVATE
            return p;
        }
    }

    public void ApplyAppearance(AppSettings settings)
    {
        BackColor = Theme.Panel;
        ForeColor = Theme.Text;
        Opacity = Theme.HighContrast ? 1d : Math.Clamp(settings.HoverOpacityPercent, 40, 100) / 100d;
        Invalidate();
    }

    public void RefreshInfo(NetworkMonitor net, PersistedData data,
        TargetSnapshot[] snaps, SpeedSample speed, TimeSpan uptime)
    {
        _adapter = net.AdapterName;
        _ipv4 = net.Address;
        _up = MonitorMath.Rate(speed.UploadBytesPerSecond, data.Settings.UseBits);
        _down = MonitorMath.Rate(speed.DownloadBytesPerSecond, data.Settings.UseBits);
        _uptime = $"Uptime {uptime.Days}d {uptime.Hours:00}h";
        _today = $"Today  ↑ {MonitorMath.Bytes(data.Totals.TodayUpload)}   ↓ {MonitorMath.Bytes(data.Totals.TodayDownload)}";
        _month = $"Month  ↑ {MonitorMath.Bytes(data.Totals.MonthUpload)}   ↓ {MonitorMath.Bytes(data.Totals.MonthDownload)}";
        for (int i = 0; i < 2; i++)
        {
            _targetNames[i] = data.Settings.Targets[i].Name;
            _targetStates[i] = snaps[i];
        }
        Invalidate();
    }

    public void RefreshTopApps(IReadOnlyList<AppUsageEntry> top, string status)
    {
        _topApps = top.Take(5).ToArray();
        _topStatus = status;
        int desiredHeight = _topApps.Count > 0 ? 408 : 296;
        if (ClientSize.Height != desiredHeight) ClientSize = new Size(356, desiredHeight);
        Invalidate();
    }

    private Bitmap IconFor(AppUsageEntry usage)
    {
        var path = usage.ExecutablePath;
        string key = string.IsNullOrWhiteSpace(path) ? "default" : path;
        if (_icons.TryGetValue(key, out var bitmap)) return bitmap;
        Bitmap? result = null;
        try
        {
            if (!string.IsNullOrWhiteSpace(path) &&
                Path.IsPathFullyQualified(path) &&
                !path.StartsWith(@"\\", StringComparison.Ordinal) &&
                File.Exists(path))
            {
                using var icon = Icon.ExtractAssociatedIcon(path);
                result = icon?.ToBitmap();
            }
        }
        catch (Exception) { /* Installed app may be removed or protected. */ }
        return _icons[key] = result ?? SystemIcons.Application.ToBitmap();
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            foreach (var image in _icons.Values) image.Dispose();
            _icons.Clear();
        }
        base.Dispose(disposing);
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        var g = e.Graphics;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        g.Clear(Theme.Panel);
        using var accent = new Pen(Theme.Accent, 2f);
        using var border = new Pen(Theme.Border);
        using var text = new SolidBrush(Theme.Text);
        using var muted = new SolidBrush(Theme.Muted);
        using var small = new Font("Segoe UI", 8.3f);
        using var regular = new Font("Segoe UI", 9f);
        using var strong = new Font("Segoe UI Semibold", 12.5f, FontStyle.Bold);
        using var title = new Font("Segoe UI Semibold", 9f, FontStyle.Bold);
        using var fmt = new StringFormat { Trimming = StringTrimming.EllipsisCharacter, FormatFlags = StringFormatFlags.NoWrap };

        g.DrawRectangle(border, 0, 0, Width - 1, Height - 1);
        g.DrawLine(accent, 13, 15, 13, 34);
        g.DrawString("NETWORK AT A GLANCE", title, text, new PointF(22, 12));
        g.DrawString(_uptime, small, muted, new RectangleF(235, 15, 106, 15), fmt);
        g.DrawLine(border, 12, 43, Width - 12, 43);

        g.DrawString("↑  " + _up, strong, text, new RectangleF(13, 53, 168, 26), fmt);
        g.DrawString("↓  " + _down, strong, text, new RectangleF(187, 53, 158, 26), fmt);
        g.DrawString(_adapter + "   ·   " + _ipv4, small, muted,
            new RectangleF(14, 86, Width - 28, 19), fmt);

        g.DrawLine(border, 12, 111, Width - 12, 111);
        for (int i = 0; i < 2; i++)
        {
            float y = 119 + 30 * i;
            using var statusBrush = new SolidBrush(Theme.State(_targetStates[i].State));
            g.FillEllipse(statusBrush, 16, y + 6, 11, 11);
            var st = _targetStates[i];
            string line = $"{_targetNames[i]}: {st.State}   {st.LatencyMs:0} ms · loss {st.LossPercent:0}%";
            g.DrawString(line, regular, text, new RectangleF(34, y + 3, Width - 47, 22), fmt);
        }
        g.DrawLine(border, 12, 183, Width - 12, 183);
        g.DrawString(_today, small, text, new RectangleF(14, 189, Width - 27, 16), fmt);
        g.DrawString(_month, small, muted, new RectangleF(14, 207, Width - 27, 16), fmt);

        g.DrawLine(border, 12, 231, Width - 12, 231);
        g.DrawString("TOP APPS · SINCE RESTART", title, text,
            new RectangleF(15, 239, Width - 30, 20), fmt);
        if (_topApps.Count == 0)
        {
            g.DrawString(_topStatus, small, muted,
                new RectangleF(15, 266, Width - 30, 20), fmt);
            return;
        }
        using var numberAlign = new StringFormat {
            Alignment = StringAlignment.Far,
            LineAlignment = StringAlignment.Center,
            Trimming = StringTrimming.EllipsisCharacter,
            FormatFlags = StringFormatFlags.NoWrap
        };
        for (int i = 0; i < _topApps.Count; i++)
        {
            var app = _topApps[i];
            int y = 266 + 26 * i;
            g.DrawImage(IconFor(app), new Rectangle(16, y, 19, 19));
            g.DrawString(app.AppName, regular, text,
                new RectangleF(43, y - 1, 189, 22), fmt);
            g.DrawString(MonitorMath.Bytes(app.TotalBytes), regular, text,
                new RectangleF(237, y - 1, 102, 22), numberAlign);
        }
        g.DrawString("Recorded hours only · newest usage may be delayed",
            small, muted, new RectangleF(15, 395, Width - 28, 13), fmt);
    }
}
