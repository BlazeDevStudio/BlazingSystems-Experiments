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
    private bool _editingGeometry;
    private bool _wasFreeform;
    private Rectangle _editOriginalBounds;
    private const int ResizeMargin = 11;
    private const int MinimumWidgetWidth = 210;
    private const int MinimumWidgetHeight = 52;

    public MonitorForm()
    {
        _data = _storage.Load();
        _data.Totals.ResetSession();
        Theme.Apply(_data.Settings);
        _trackers = [new QualityTracker(_data.Histories[0]), new QualityTracker(_data.Histories[1])];
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        TopMost = true;
        BackColor = Theme.Background;
        DoubleBuffered = true;
        ClientSize = new Size(312, 64);
        MinimumSize = new Size(MinimumWidgetWidth, MinimumWidgetHeight);
        MaximumSize = new Size(1050, 300);
        Opacity = Math.Clamp(_data.Settings.WidgetOpacityPercent, 40, 100) / 100d;
        Cursor = Cursors.Hand;
        AccessibleName = "BlazeNetMonitor live traffic widget";
        _tray = new NotifyIcon { Text = "BlazeNetMonitor", Icon = MakeIcon(), Visible = true, ContextMenuStrip = _menu };
        BuildMenu();
        _tray.DoubleClick += (_, _) => EditSettings();
        MouseClick += (_, e) =>
        {
            if (e.Button == MouseButtons.Right) _menu.Show(Cursor.Position);
            else if (_editingGeometry) return;
            else if (e.X <= 40) EditSettings();
            else _showHover = !_showHover;
        };
        MouseDoubleClick += (_, _) => { if (_editingGeometry) FinishGeometryEdit(); };
        KeyDown += (_, e) =>
        {
            if (e.KeyCode == Keys.Escape && _editingGeometry) { CancelGeometryEdit(); e.Handled = true; }
            else if (e.KeyCode == Keys.Enter && _editingGeometry) { FinishGeometryEdit(); e.Handled = true; }
        };
        ResizeEnd += (_, _) => { if (_editingGeometry) Invalidate(); };
        SizeChanged += (_, _) => Invalidate();
        MouseEnter += (_, _) => { if (!_editingGeometry) { _showHover = true; _hoverTimer.Stop(); UpdateHover(); } };
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
        Shown += async (_, _) => { RestoreGeometry(); _trafficTimer.Start(); _probeTimer.Start(); await ProbeTargets(); };
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
        if (!IsDisposed && IsHandleCreated) BeginInvoke(new Action(() => { ApplyAppearance(); Reposition(); }));
    }

    private void ApplyAppearance()
    {
        Theme.Apply(_data.Settings);
        BackColor = Theme.Background;
        Opacity = Math.Clamp(_data.Settings.WidgetOpacityPercent, 40, 100) / 100d;
        _info.ApplyAppearance(_data.Settings);
        Invalidate();
    }

    private void RestoreGeometry()
    {
        Width = Math.Clamp(_data.Settings.WidgetWidth, MinimumWidgetWidth, MaximumSize.Width);
        Height = Math.Clamp(_data.Settings.WidgetHeight, MinimumWidgetHeight, MaximumSize.Height);
        if (_data.Settings.FreeformPositioned && _data.Settings.WidgetX != -1 && _data.Settings.WidgetY != -1)
        {
            Location = new Point(_data.Settings.WidgetX, _data.Settings.WidgetY);
            Reposition();  // Clamp to whichever monitor still intersects, only when necessary.
        }
        else Reposition();
    }

    private void Reposition()
    {
        if (_editingGeometry || !Visible && IsHandleCreated) return;
        if (_data.Settings.FreeformPositioned)
        {
            // Preserve freeform position; re-home only when monitor was unplugged / offscreen.
            if (Screen.AllScreens.Any(s => s.WorkingArea.IntersectsWith(Bounds))) return;
            var fallback = Screen.PrimaryScreen?.WorkingArea ?? Screen.FromControl(this).WorkingArea;
            Location = new Point(fallback.Left + Math.Max(0, fallback.Width - Width - 20),
                fallback.Top + Math.Max(0, fallback.Height - Height - 20));
            return;
        }

        var screen = Screen.FromPoint(Cursor.Position);
        var work = screen.WorkingArea;
        var bounds = screen.Bounds;
        int x = Math.Clamp(bounds.Right - Width - _data.Settings.HorizontalOffset,
            bounds.Left, Math.Max(bounds.Left, bounds.Right - Width));
        int y = _data.Settings.DockInsideTaskbar ? bounds.Bottom - Height : work.Bottom - Height;
        if (work.Bottom == bounds.Bottom && work.Top > bounds.Top)
            y = _data.Settings.DockInsideTaskbar ? bounds.Top : work.Top;
        Location = new Point(x, Math.Clamp(y, bounds.Top, Math.Max(bounds.Top, bounds.Bottom - Height)));
    }

    private void BeginGeometryEdit()
    {
        if (_editingGeometry) return;
        _editOriginalBounds = Bounds;
        _wasFreeform = _data.Settings.FreeformPositioned;
        _editingGeometry = true;
        _info.Hide();
        _showHover = false;
        _hoverTimer.Stop();
        Cursor = Cursors.SizeAll;
        BuildMenu();
        Invalidate();
    }

    private void FinishGeometryEdit()
    {
        if (!_editingGeometry) return;
        _editingGeometry = false;
        Cursor = Cursors.Hand;
        _data.Settings.FreeformPositioned = true;
        _data.Settings.WidgetX = Left;
        _data.Settings.WidgetY = Top;
        _data.Settings.WidgetWidth = Width;
        _data.Settings.WidgetHeight = Height;
        SaveSafe();
        BuildMenu();
        Invalidate();
    }

    private void CancelGeometryEdit()
    {
        if (!_editingGeometry) return;
        _editingGeometry = false;
        _data.Settings.FreeformPositioned = _wasFreeform;
        Bounds = _editOriginalBounds;
        Cursor = Cursors.Hand;
        BuildMenu();
        Invalidate();
    }

    protected override bool ProcessCmdKey(ref Message msg, Keys keyData)
    {
        if (_editingGeometry && keyData == Keys.Escape) { CancelGeometryEdit(); return true; }
        if (_editingGeometry && keyData == Keys.Enter) { FinishGeometryEdit(); return true; }
        return base.ProcessCmdKey(ref msg, keyData);
    }

    protected override void WndProc(ref Message m)
    {
        const int WM_NCHITTEST = 0x84;
        if (m.Msg == WM_NCHITTEST && _editingGeometry)
        {
            base.WndProc(ref m);
            long packed = m.LParam.ToInt64();
            var pos = PointToClient(new Point(unchecked((short)(packed & 0xFFFF)),
                unchecked((short)((packed >> 16) & 0xFFFF))));
            int hit = 2; // HTCAPTION: dragging the center moves the widget.
            bool left = pos.X <= ResizeMargin, right = pos.X >= Width - ResizeMargin;
            bool top = pos.Y <= ResizeMargin, bottom = pos.Y >= Height - ResizeMargin;
            if (left && top) hit = 13; else if (right && top) hit = 14;
            else if (left && bottom) hit = 16; else if (right && bottom) hit = 17;
            else if (left) hit = 10; else if (right) hit = 11;
            else if (top) hit = 12; else if (bottom) hit = 15;
            m.Result = (nint)hit;
            return;
        }
        base.WndProc(ref m);
    }

    private void BuildMenu()
    {
        _menu.Items.Clear();
        _menu.Items.Add(_editingGeometry ? "Finish resize / move (Enter)" : "Resize / move widget",
            null, (_, _) => { if (_editingGeometry) FinishGeometryEdit(); else BeginGeometryEdit(); });
        if (_editingGeometry) _menu.Items.Add("Cancel resize (Esc)", null, (_, _) => CancelGeometryEdit());
        _menu.Items.Add(new ToolStripSeparator());
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
        // Never snap a user-positioned widget back to the taskbar during polling.
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
        if (IsDisposed || _editingGeometry) return;
        var uptime = TimeSpan.FromMilliseconds(Environment.TickCount64);
        _info.RefreshInfo(_network, _data, _snapshots, _speed, uptime);
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
            ApplyAppearance();
            SaveSafe();
            if (_data.Settings.FreeformPositioned) Reposition(); else RestoreGeometry();
            _ = ProbeTargets();
        }
        _trafficTimer.Start(); _probeTimer.Start();
        if (settings.DialogResult == DialogResult.OK && settings.ResizeAfterSave) BeginGeometryEdit();
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

        bool showGraphs = _data.Settings.ShowGraphs && Height >= 82;
        float textScale = Math.Clamp(Width / 35f, 8.5f, 12f);
        using var speedFont = new Font("Segoe UI Semibold", textScale, FontStyle.Bold, GraphicsUnit.Point);
        using var accentBrush = new SolidBrush(Theme.Accent);
        using var textBrush = new SolidBrush(Theme.Text);
        using var border = new Pen(_editingGeometry ? Theme.Accent : Theme.Border, _editingGeometry ? 2f : 1f);
        using var format = new StringFormat { Trimming = StringTrimming.EllipsisCharacter,
            FormatFlags = StringFormatFlags.NoWrap, LineAlignment = StringAlignment.Center };

        g.DrawRectangle(border, 1, 1, Width - 3, Height - 3);
        // Health indicator order never changes: first target above second target.
        for (int i = 0; i < 2; i++)
        {
            float cy = Height / 2f + (i == 0 ? -12 : 12);
            using var dot = new SolidBrush(Theme.State(_snapshots[i].State));
            g.FillEllipse(dot, 12, cy - 6, 12, 12);
            using var ring = new Pen(Theme.Border, 1);
            g.DrawEllipse(ring, 11, cy - 7, 14, 14);
        }
        using (var line = new Pen(Theme.Border)) g.DrawLine(line, 34, 5, 34, Height - 5);

        float contentX = 40f;
        float contentWidth = Math.Max(20, Width - contentX - 7);
        float half = contentWidth / 2f;
        float labelHeight = showGraphs ? Math.Min(38f, Height - 37f) : Height - 12f;
        float y = showGraphs ? 4f : 6f;
        var upRect = new RectangleF(contentX, y, half - 5, labelHeight);
        var downRect = new RectangleF(contentX + half, y, half - 5, labelHeight);

        var up = "↑ " + MonitorMath.Rate(_speed.UploadBytesPerSecond, _data.Settings.UseBits);
        var down = "↓ " + MonitorMath.Rate(_speed.DownloadBytesPerSecond, _data.Settings.UseBits);
        g.DrawString(up, speedFont, textBrush, upRect, format);
        g.DrawString(down, speedFont, textBrush, downRect, format);

        if (showGraphs)
        {
            int graphY = Math.Max(27, Height - 31);
            var graphWidth = (int)Math.Max(14, half - 12);
            Graph(g, _upSamples, new Rectangle((int)contentX + 2, graphY, graphWidth, 21));
            Graph(g, _downSamples, new Rectangle((int)(contentX + half) + 2, graphY, graphWidth, 21));
        }

        if (_editingGeometry)
        {
            // In edit mode the perimeter and handles are visible and Windows resizes via WM_NCHITTEST.
            int h = 8;
            foreach (var pt in new[] {
                new Point(0, 0), new Point(Width - h - 1, 0),
                new Point(0, Height - h - 1), new Point(Width - h - 1, Height - h - 1) })
                g.FillRectangle(accentBrush, pt.X, pt.Y, h, h);
        }
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
        if (_editingGeometry) CancelGeometryEdit();
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
