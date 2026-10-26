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

    public InfoForm()
    {
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        TopMost = true;
        DoubleBuffered = true;
        ClientSize = new Size(356, 226);
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
    }
}
