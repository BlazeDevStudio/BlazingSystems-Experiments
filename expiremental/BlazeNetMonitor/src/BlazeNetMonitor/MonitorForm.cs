using System.Diagnostics;
using System.Drawing.Drawing2D;
using System.Net.NetworkInformation;
using BlazeNetMonitor.Core;

namespace BlazeNetMonitor;

internal sealed class MonitorForm : Form
{
    private readonly Storage _storage = new(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "BlazeSystems", "BlazeNetMonitor", "state.json"));
    private readonly PersistedData _data;
    private readonly NetworkMonitor _network = new();
    private readonly System.Windows.Forms.Timer _trafficTimer = new() { Interval = 1000 };
    private readonly System.Windows.Forms.Timer _probeTimer = new();
    private readonly System.Windows.Forms.Timer _hoverTimer = new() { Interval = 400 };
    private readonly NotifyIcon _tray;
    private readonly InfoForm _info = new();
    private QualityTracker[] _trackers;
    private readonly TargetSnapshot[] _snapshots = new TargetSnapshot[2];
    private readonly Queue<double> _upSamples = new();
    private readonly Queue<double> _downSamples = new();
    private readonly CancellationTokenSource _stop = new();
    private readonly ContextMenuStrip _menu = new();
    private SpeedSample _speed;
    private bool _probing;
    private int _ticks;
    private bool _showHover;

    public MonitorForm()
    {
        _data = _storage.Load();
        _data.Totals.ResetSession();
        _trackers = [new QualityTracker(_data.Histories[0]), new QualityTracker(_data.Histories[1])];
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        TopMost = true;
        BackColor = Theme.Background;
        DoubleBuffered = true;
        ClientSize = new Size(452, 55);
        MinimumSize = ClientSize;
        MaximumSize = ClientSize;
        Cursor = Cursors.Hand;
        AccessibleName = "BlazeNetMonitor live traffic widget";
        _tray = new NotifyIcon { Text = "BlazeNetMonitor", Icon = MakeIcon(), Visible = true, ContextMenuStrip = _menu };
        BuildMenu();
        _tray.DoubleClick += (_, _) => EditSettings();
        MouseClick += (_, e) =>
        {
            if (e.Button == MouseButtons.Right) _menu.Show(Cursor.Position);
            else if (e.X <= 40) EditSettings();
            else _showHover = !_showHover;
        };
        MouseEnter += (_, _) => { _showHover = true; _hoverTimer.Stop(); UpdateHover(); };
        MouseLeave += (_, _) => _hoverTimer.Start();
        _info.MouseEnter += (_, _) => _hoverTimer.Stop();
        _info.MouseLeave += (_, _) => _hoverTimer.Start();
        _hoverTimer.Tick += (_, _) =>
        {
            if (!Bounds.Contains(Cursor.Position) && !_info.Bounds.Contains(Cursor.Position))
            {
                _hoverTimer.Stop(); _info.Hide(); _showHover = false;
            }
        };
        _trafficTimer.Tick += (_, _) => SampleTraffic();
        _probeTimer.Tick += async (_, _) => await ProbeTargets();
        _probeTimer.Interval = Math.Clamp(_data.Settings.ProbeIntervalSeconds, 3, 120) * 1000;
        Shown += async (_, _) => { Reposition(); _trafficTimer.Start(); _probeTimer.Start(); await ProbeTargets(); };
        SystemEventsHook();
    }

    protected override CreateParams CreateParams
    {
        get { var p = base.CreateParams; p.ExStyle |= 0x80; return p; } // WS_EX_TOOLWINDOW
    }

    private void SystemEventsHook()
    {
        Microsoft.Win32.SystemEvents.DisplaySettingsChanged += OnDisplayChanged;
        Microsoft.Win32.SystemEvents.UserPreferenceChanged += OnPreferenceChanged;
    }
    private void OnDisplayChanged(object? sender, EventArgs e)
    {
        if (!IsDisposed && IsHandleCreated) BeginInvoke(new Action(Reposition));
    }
    private void OnPreferenceChanged(object? sender, Microsoft.Win32.UserPreferenceChangedEventArgs e)
    {
        if (!IsDisposed && IsHandleCreated) BeginInvoke(new Action(Reposition));
    }

    private void Reposition()
    {
        var screen = Screen.PrimaryScreen;
        if (screen == null) return;
        var work = screen.WorkingArea;
        var bounds = screen.Bounds;
        int x = Math.Clamp(bounds.Right - Width - _data.Settings.HorizontalOffset, bounds.Left, bounds.Right - Width);
        // 'On taskbar' is an intentionally optional overlay, not a legacy Explorer deskband.
        int y = _data.Settings.DockInsideTaskbar ? bounds.Bottom - Height : work.Bottom - Height;
        if (work.Bottom == bounds.Bottom && work.Top > bounds.Top) y = _data.Settings.DockInsideTaskbar ? bounds.Top : work.Top;
        Location = new Point(x, Math.Clamp(y, bounds.Top, bounds.Bottom - Height));
        if (_showHover) UpdateHover();
    }

    private void BuildMenu()
    {
        _menu.Items.Clear();
        _menu.Items.Add("BlazeNetMonitor · Settings", null, (_, _) => EditSettings());
        _menu.Items.Add("Open connection table", null, (_, _) => ShowConnections());
        _menu.Items.Add("Reset session totals", null, (_, _) => { _data.Totals.ResetSession(); Invalidate(); SaveSafe(); });
        _menu.Items.Add("Copy status", null, (_, _) => CopyStatus());
        _menu.Items.Add(new ToolStripSeparator());
        _menu.Items.Add("Exit BlazeNetMonitor", null, (_, _) => Close());
    }

    private static Icon MakeIcon()
    {
        using var bmp = new Bitmap(32, 32);
        using (var g = Graphics.FromImage(bmp))
        {
            g.Clear(Theme.Background);
            using var a = new SolidBrush(Theme.Accent);
            using var b = new SolidBrush(Color.FromArgb(72, 215, 144));
            g.FillRectangle(a, 5, 19, 5, 9);
            g.FillRectangle(a, 13, 11, 5, 17);
            g.FillRectangle(b, 21, 5, 5, 23);
        }
        var handle = bmp.GetHicon();
        using var temp = Icon.FromHandle(handle);
        var clone = (Icon)temp.Clone();
        DestroyIcon(handle);
        return clone;
    }
    [System.Runtime.InteropServices.DllImport("user32.dll", SetLastError = true)]
    private static extern bool DestroyIcon(nint hIcon);

    private void CopyStatus()
    {
        var lines = new List<string>
        {
            $"BlazeNetMonitor | {DateTime.Now:yyyy-MM-dd HH:mm:ss}",
            $"Adapter: {_network.AdapterName}",
            $"Upload: {MonitorMath.Rate(_speed.UploadBytesPerSecond, _data.Settings.UseBits)}",
            $"Download: {MonitorMath.Rate(_speed.DownloadBytesPerSecond, _data.Settings.UseBits)}"
        };
        for (var i = 0; i < 2; i++) lines.Add($"{_data.Settings.Targets[i].Name}: {_snapshots[i].State} ({_snapshots[i].LatencyMs:0} ms)");
        try { Clipboard.SetText(string.Join(Environment.NewLine, lines)); }
        catch (Exception ex) { MessageBox.Show(ex.Message, "Copy status"); }
    }

    private void SampleTraffic()
    {
        var (speed, up, down) = _network.Sample(_data.Settings.AdapterId);
        _speed = speed;
        _data.Totals.Add(up, down, DateTime.Now);
        AppendSample(_upSamples, speed.UploadBytesPerSecond);
        AppendSample(_downSamples, speed.DownloadBytesPerSecond);
        _ticks++;
        if (_ticks % 5 == 0) Reposition();
        if (_ticks % 30 == 0) SaveSafe();
        _tray.Text = "BlazeNetMonitor " + MonitorMath.Rate(speed.DownloadBytesPerSecond, _data.Settings.UseBits);
        if (_showHover) UpdateHover();
        Invalidate();
    }

    private static void AppendSample(Queue<double> list, double number)
    {
        list.Enqueue(number);
        while (list.Count > 36) list.Dequeue();
    }

    private async Task ProbeTargets()
    {
        if (_probing || _stop.IsCancellationRequested) return;
        _probing = true;
        try
        {
            var targets = _data.Settings.Targets.ToArray();
            var readings = await Task.WhenAll(targets.Select(t => _network.Probe(t, _stop.Token)));
            if (_stop.IsCancellationRequested || IsDisposed) return;
            for (int i = 0; i < 2; i++)
            {
                _snapshots[i] = _trackers[i].Add(readings[i], _data.Settings.ProbeIntervalSeconds);
            }
            Invalidate();
            if (_showHover) UpdateHover();
        }
        catch (OperationCanceledException) { /* normal closing */ }
        catch (Exception ex) { System.Diagnostics.Debug.WriteLine(ex); }
        finally { _probing = false; }
    }

    private void UpdateHover()
    {
        if (IsDisposed) return;
        var uptime = TimeSpan.FromMilliseconds(Environment.TickCount64);
        _info.RefreshInfo(_network, _data, _snapshots, uptime);
        var screen = Screen.FromControl(this).WorkingArea;
        int x = Math.Clamp(Left + Width - _info.Width, screen.Left, Math.Max(screen.Left, screen.Right - _info.Width));
        int y = Top - _info.Height - 5;
        if (y < screen.Top) y = Bottom + 5;
        _info.Location = new Point(x, y);
        if (!_info.Visible) _info.Show(this);
    }

    private void EditSettings()
    {
        _info.Hide(); _showHover = false;
        _trafficTimer.Stop(); _probeTimer.Stop();
        using var settings = new SettingsForm(_data.Settings);
        if (settings.ShowDialog(this) == DialogResult.OK)
        {
            _network.Invalidate();
            // A changed probe target must never inherit a previous target's green/blue streak.
            _data.Histories = [new TargetHistory(), new TargetHistory()];
            _trackers = [new QualityTracker(_data.Histories[0]), new QualityTracker(_data.Histories[1])];
            Array.Clear(_snapshots, 0, _snapshots.Length);
            _probeTimer.Interval = Math.Clamp(_data.Settings.ProbeIntervalSeconds, 3, 120) * 1000;
            SaveSafe();
            Reposition();
            _ = ProbeTargets();
        }
        _trafficTimer.Start(); _probeTimer.Start();
    }

    private void ShowConnections()
    {
        var popup = new Form { Text = "BlazeNetMonitor · Active connections", Size = new Size(850, 480), StartPosition = FormStartPosition.CenterScreen };
        var grid = new DataGridView { Dock = DockStyle.Fill, ReadOnly = true, AllowUserToAddRows = false, AutoSizeColumnsMode = DataGridViewAutoSizeColumnsMode.Fill };
        var refresh = new Button { Dock = DockStyle.Top, Text = "Refresh TCP / UDP endpoints", Height = 35 };
        void Update()
        {
            try
            {
                var ip = IPGlobalProperties.GetIPGlobalProperties();
                var tcp = ip.GetActiveTcpConnections().Select(c => new { Protocol = "TCP", Local = c.LocalEndPoint.ToString(), Remote = c.RemoteEndPoint.ToString(), State = c.State.ToString() });
                var udp = ip.GetActiveUdpListeners().Select(c => new { Protocol = "UDP", Local = c.ToString(), Remote = "—", State = "Listening" });
                grid.DataSource = tcp.Concat(udp).ToList();
            }
            catch (Exception ex) { MessageBox.Show(ex.Message, "Connection inspection"); }
        }
        refresh.Click += (_, _) => Update();
        popup.Controls.Add(grid);
        popup.Controls.Add(refresh);
        Update();
        popup.Show();
    }

    protected override void OnPaint(PaintEventArgs e)
    {
        base.OnPaint(e);
        var g = e.Graphics;
        g.SmoothingMode = SmoothingMode.AntiAlias;
        g.Clear(Theme.Background);
        using (var border = new Pen(Theme.Border, 1f)) g.DrawRectangle(border, 0, 0, Width - 1, Height - 1);
        for (int i = 0; i < 2; i++)
        {
            var c = Theme.State(_snapshots[i].State);
            using var brush = new SolidBrush(c);
            g.FillEllipse(brush, 13, 11 + i * 23, 14, 14);
            using var light = new Pen(Color.FromArgb(120, c), 1f);
            g.DrawEllipse(light, 12, 10 + i * 23, 16, 16);
        }
        using (var divider = new Pen(Theme.Border)) { g.DrawLine(divider, 40, 4, 40, Height - 5); g.DrawLine(divider, 237, 8, 237, Height - 9); }
        using var bold = new Font("Segoe UI Semibold", 11.5f, FontStyle.Bold, GraphicsUnit.Point);
        using var small = new Font("Segoe UI", 7.2f, FontStyle.Regular, GraphicsUnit.Point);
        using var accent = new SolidBrush(Theme.Accent);
        using var muted = new SolidBrush(Theme.Muted);
        g.DrawString("↑", bold, accent, 45, 4);
        g.DrawString(MonitorMath.Rate(_speed.UploadBytesPerSecond, _data.Settings.UseBits), bold, accent, 68, 4);
        g.DrawString("↓", bold, accent, 242, 4);
        g.DrawString(MonitorMath.Rate(_speed.DownloadBytesPerSecond, _data.Settings.UseBits), bold, accent, 265, 4);
        Graph(g, _upSamples, new Rectangle(55, 32, 171, 18));
        Graph(g, _downSamples, new Rectangle(253, 32, 185, 18));
        using var pen = new Pen(Theme.Border); g.DrawLine(pen, 0, Height - 1, Width, Height - 1);
    }

    private static void Graph(Graphics g, Queue<double> samples, Rectangle r)
    {
        if (samples.Count < 2) return;
        var nums = samples.ToArray();
        var max = Math.Max(1, nums.Max());
        var points = nums.Select((v, i) => new PointF(r.Left + i * r.Width / (float)Math.Max(1, nums.Length - 1), r.Bottom - (float)(v / max) * r.Height)).ToArray();
        using var pen = new Pen(Theme.Accent, 1.35f);
        g.DrawLines(pen, points);
    }

    private void SaveSafe()
    {
        try { _storage.Save(_data); }
        catch (Exception ex) { Debug.WriteLine("Settings persistence error: " + ex); }
    }

    protected override void OnFormClosed(FormClosedEventArgs e)
    {
        _stop.Cancel();
        _trafficTimer.Stop(); _probeTimer.Stop(); _hoverTimer.Stop();
        Microsoft.Win32.SystemEvents.DisplaySettingsChanged -= OnDisplayChanged;
        Microsoft.Win32.SystemEvents.UserPreferenceChanged -= OnPreferenceChanged;
        SaveSafe();
        _tray.Visible = false;
        _tray.Dispose();
        _info.Close(); _info.Dispose();
        _menu.Dispose();
        _network.Dispose(); _stop.Dispose();
        base.OnFormClosed(e);
    }
}
