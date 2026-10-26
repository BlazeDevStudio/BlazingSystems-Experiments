using BlazeNetMonitor.Core;

namespace BlazeNetMonitor;

internal sealed class InfoForm : Form
{
    private readonly Label _body;
    public InfoForm()
    {
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        TopMost = true;
        BackColor = Theme.Panel;
        ClientSize = new Size(420, 312);
        Padding = new Padding(15);
        _body = new Label { Dock = DockStyle.Fill, ForeColor = Theme.Text, Font = new Font("Segoe UI", 9.5f), AutoSize = false };
        Controls.Add(_body);
    }
    protected override CreateParams CreateParams
    {
        get { var p = base.CreateParams; p.ExStyle |= 0x80; return p; } // WS_EX_TOOLWINDOW; no Alt+Tab window
    }
    public void RefreshInfo(NetworkMonitor net, PersistedData data, TargetSnapshot[] snaps, SpeedSample speed, TimeSpan uptime)
    {
        var t = data.Totals;
        var entries = data.Settings.Targets.Select((target, i) =>
            $"{(i == 0 ? "●" : "●")}  {target.Name}: {snaps[i].State}   {snaps[i].LatencyMs:0} ms  |  loss {snaps[i].LossPercent:0}%  jitter {snaps[i].JitterMs:0} ms\n      {target.Protocol}  {target.Address}  ({snaps[i].Message})");
        _body.Text = $"BLAZENETMONITOR · NETWORK AT A GLANCE\n\n" +
            $"CURRENT   ↑ {MonitorMath.Rate(speed.UploadBytesPerSecond, data.Settings.UseBits)}  ↓ {MonitorMath.Rate(speed.DownloadBytesPerSecond, data.Settings.UseBits)}\n\nAdapter: {net.AdapterName}\nIPv4: {net.Address}\nSystem uptime: {uptime.Days}d {uptime.Hours:00}h {uptime.Minutes:00}m\n\n" +
            $"SESSION        ↑ {MonitorMath.Bytes(t.SessionUpload)}    ↓ {MonitorMath.Bytes(t.SessionDownload)}\n" +
            $"TODAY           ↑ {MonitorMath.Bytes(t.TodayUpload)}    ↓ {MonitorMath.Bytes(t.TodayDownload)}\n" +
            $"THIS MONTH  ↑ {MonitorMath.Bytes(t.MonthUpload)}    ↓ {MonitorMath.Bytes(t.MonthDownload)}\n\n" +
            string.Join("\n", entries) + (string.IsNullOrWhiteSpace(net.Error) ? "" : "\nAdapter: " + net.Error);
    }
}
