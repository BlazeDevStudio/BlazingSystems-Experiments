using System.Diagnostics;
using System.Drawing.Drawing2D;
using System.Net.NetworkInformation;
using System.Runtime.InteropServices;
using BlazeNetMonitor.Core;

namespace BlazeNetMonitor;

internal sealed class MonitorForm : Form
{
    private readonly Storage _storage = new(Path.Combine(Environment.GetFolderPath(Environment.SpecialFolder.LocalApplicationData), "BlazeSystems", "BlazeNetMonitor", "state.json"));
    private readonly PersistedData _data;
    private SettingsForm? _settingsForm;
    private AppSettings? _settingsBeforeEdit;
    private readonly System.Windows.Forms.Timer _fullscreenTimer = new() { Interval = 750 };
    private bool _hiddenForFullscreen;
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
    [Flags]
    private enum DragEdges { None = 0, Left = 1, Top = 2, Right = 4, Bottom = 8, Move = 16 }
    private DragEdges _dragEdges;
    private Rectangle _dragStartBounds;
    private Point _dragStartPoint;
    private bool _dragActive;
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
        ApplyAppearance();
        _tray.DoubleClick += (_, _) => EditSettings();
        MouseClick += (_, e) =>
        {
            if (e.Button == MouseButtons.Right) _menu.Show(Cursor.Position);
            else if (_editingGeometry) return;
            else if (e.X <= 40) EditSettings();
            else _showHover = !_showHover;
        };
        MouseDoubleClick += (_, _) => { if (_editingGeometry) FinishGeometryEdit(); };
        MouseDown += StartDrag;
        MouseMove += ContinueDrag;
        MouseUp += StopDrag;
        KeyDown += (_, e) =>
        {
            if (e.KeyCode == Keys.Escape && _editingGeometry) { CancelGeometryEdit(); e.Handled = true; }
            else if (e.KeyCode == Keys.Enter && _editingGeometry) { FinishGeometryEdit(); e.Handled = true; }
        };
        ResizeEnd += (_, _) => { if (_editingGeometry) Invalidate(); };
        SizeChanged += (_, _) => Invalidate();
        MouseEnter += (_, _) =>
        {
            if (!_editingGeometry && !_hiddenForFullscreen)
            {
                _showHover = true;
                _hoverTimer.Stop();
                UpdateHover();
            }
        };
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
        _fullscreenTimer.Tick += (_, _) => RefreshFullscreenState();
        Shown += async (_, _) =>
        {
            RestoreGeometry(); _trafficTimer.Start(); _probeTimer.Start();
            _fullscreenTimer.Start(); await ProbeTargets();
        };
        SystemEventsHook();
    }

    protected override bool ShowWithoutActivation => true;

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
        Opacity = Theme.HighContrast ? 1d : Math.Clamp(_data.Settings.WidgetOpacityPercent, 40, 100) / 100d;
        _info.ApplyAppearance(_data.Settings);
        Invalidate();
    }

    private static Rectangle SafeBounds(Rectangle candidate, Screen screen)
        => WidgetGeometry.Constrain(candidate, screen.WorkingArea, MinimumWidgetWidth, MinimumWidgetHeight);

    private void RestoreGeometry()
    {
        Width = Math.Clamp(_data.Settings.WidgetWidth, MinimumWidgetWidth, MaximumSize.Width);
        Height = Math.Clamp(_data.Settings.WidgetHeight, MinimumWidgetHeight, MaximumSize.Height);
        if (_data.Settings.FreeformPositioned && _data.Settings.WidgetX != -1 && _data.Settings.WidgetY != -1)
            Location = new Point(_data.Settings.WidgetX, _data.Settings.WidgetY);
        Reposition();
    }

    private void Reposition()
    {
        if (_editingGeometry || IsDisposed) return;
        if (_data.Settings.FreeformPositioned)
        {
            Bounds = SafeBounds(Bounds, Screen.FromRectangle(Bounds));
            return;
        }
        var screen = Screen.PrimaryScreen ?? Screen.FromControl(this);
        var work = screen.WorkingArea;
        // Never overlay the taskbar, including old saved DockInsideTaskbar preferences.
        Bounds = SafeBounds(new Rectangle(
            work.Right - Width - _data.Settings.HorizontalOffset,
            work.Bottom - Height, Width, Height), screen);
    }

    private void RefreshFullscreenState()
    {
        if (IsDisposed || Disposing || !IsHandleCreated) return;
        bool hide = _data.Settings.AutoHideForFullscreen && !_editingGeometry &&
            _settingsForm is null && IsForegroundFullscreen();
        if (hide == _hiddenForFullscreen) return;
        _hiddenForFullscreen = hide;
        if (hide)
        {
            _info.Hide(); _showHover = false; _hoverTimer.Stop(); Hide();
        }
        else
        {
            Show(); Reposition(); // ShowWithoutActivation preserves foreground focus.
        }
    }

    [StructLayout(LayoutKind.Sequential)]
    private struct WinRect { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll")]
    private static extern nint GetForegroundWindow();
    [DllImport("user32.dll")]
    private static extern uint GetWindowThreadProcessId(nint window, out uint process);
    [DllImport("user32.dll")]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool GetWindowRect(nint window, out WinRect rect);

    private bool IsForegroundFullscreen()
    {
        var foreground = GetForegroundWindow();
        if (foreground == 0) return false;
        GetWindowThreadProcessId(foreground, out uint process);
        if (process == (uint)Environment.ProcessId ||
            !GetWindowRect(foreground, out var r)) return false;
        var screen = Screen.FromHandle(foreground);
        if (screen.DeviceName != Screen.FromRectangle(Bounds).DeviceName) return false;
        return WidgetGeometry.CoversScreen(
            Rectangle.FromLTRB(r.Left, r.Top, r.Right, r.Bottom), screen.Bounds);
    }

    private void BeginGeometryEdit()
    {
        if (_editingGeometry) return;
        _editOriginalBounds = Bounds;
        Bounds = SafeBounds(Bounds, Screen.FromRectangle(Bounds));
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
        _dragActive = false;
        Capture = false;
        Cursor = Cursors.Hand;
        Bounds = SafeBounds(Bounds, Screen.FromRectangle(Bounds));
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
        _dragActive = false;
        Capture = false;
        _data.Settings.FreeformPositioned = _wasFreeform;
        Bounds = SafeBounds(_editOriginalBounds, Screen.FromRectangle(_editOriginalBounds));
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

    private DragEdges FindDragEdges(Point p)
    {
        var result = DragEdges.None;
        if (p.X < ResizeMargin) result |= DragEdges.Left;
        if (p.X >= Width - ResizeMargin) result |= DragEdges.Right;
        if (p.Y < ResizeMargin) result |= DragEdges.Top;
        if (p.Y >= Height - ResizeMargin) result |= DragEdges.Bottom;
        return result == DragEdges.None ? DragEdges.Move : result;
    }

    private void StartDrag(object? sender, MouseEventArgs e)
    {
        if (!_editingGeometry || e.Button != MouseButtons.Left) return;
        _dragEdges = FindDragEdges(e.Location);
        _dragStartPoint = Cursor.Position;
        _dragStartBounds = Bounds;
        _dragActive = true;
        Capture = true;
    }

    private void ContinueDrag(object? sender, MouseEventArgs e)
    {
        if (!_editingGeometry) return;
        if (!_dragActive)
        {
            var edge = FindDragEdges(e.Location);
            if (edge is DragEdges.Left or DragEdges.Right) Cursor = Cursors.SizeWE;
            else if (edge is DragEdges.Top or DragEdges.Bottom) Cursor = Cursors.SizeNS;
            else if (edge == (DragEdges.Left | DragEdges.Top) ||
                     edge == (DragEdges.Right | DragEdges.Bottom)) Cursor = Cursors.SizeNWSE;
            else if (edge == (DragEdges.Left | DragEdges.Bottom) ||
                     edge == (DragEdges.Right | DragEdges.Top)) Cursor = Cursors.SizeNESW;
            else Cursor = Cursors.SizeAll;
            return;
        }

        int dx = Cursor.Position.X - _dragStartPoint.X;
        int dy = Cursor.Position.Y - _dragStartPoint.Y;
        var b = _dragStartBounds;
        if (_dragEdges == DragEdges.Move)
        {
            Bounds = SafeBounds(new Rectangle(b.X + dx, b.Y + dy, b.Width, b.Height),
                Screen.FromPoint(Cursor.Position));
            return;
        }

        int left = b.Left, top = b.Top, right = b.Right, bottom = b.Bottom;
        if ((_dragEdges & DragEdges.Left) != 0) left = Math.Min(right - MinimumWidgetWidth, b.Left + dx);
        if ((_dragEdges & DragEdges.Right) != 0) right = Math.Max(left + MinimumWidgetWidth, b.Right + dx);
        if ((_dragEdges & DragEdges.Top) != 0) top = Math.Min(bottom - MinimumWidgetHeight, b.Top + dy);
        if ((_dragEdges & DragEdges.Bottom) != 0) bottom = Math.Max(top + MinimumWidgetHeight, b.Bottom + dy);
        if (right - left > MaximumSize.Width)
        {
            if ((_dragEdges & DragEdges.Left) != 0) left = right - MaximumSize.Width;
            else right = left + MaximumSize.Width;
        }
        if (bottom - top > MaximumSize.Height)
        {
            if ((_dragEdges & DragEdges.Top) != 0) top = bottom - MaximumSize.Height;
            else bottom = top + MaximumSize.Height;
        }
        Bounds = SafeBounds(Rectangle.FromLTRB(left, top, right, bottom),
            Screen.FromPoint(Cursor.Position));
    }

    private void StopDrag(object? sender, MouseEventArgs e)
    {
        if (!_dragActive) return;
        _dragActive = false;
        Capture = false;
        Invalidate();
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
        if (IsDisposed || _editingGeometry || _hiddenForFullscreen) return;
        var uptime = TimeSpan.FromMilliseconds(Environment.TickCount64);
        _info.RefreshInfo(_network, _data, _snapshots, _speed, uptime);
        var area = Screen.FromRectangle(Bounds).WorkingArea;
        int x = Math.Clamp(Left + Width - _info.Width, area.Left,
            Math.Max(area.Left, area.Right - _info.Width));
        int above = Top - _info.Height - 8;
        int below = Bottom + 8;
        int y = above >= area.Top ? above :
            (below + _info.Height <= area.Bottom ? below : area.Top);
        _info.Location = new Point(x, Math.Clamp(y, area.Top,
            Math.Max(area.Top, area.Bottom - _info.Height)));
        if (!_info.Visible) _info.Show(this);
    }

    private static bool TargetsDiffer(AppSettings before, AppSettings after)
    {
        if (before.Targets.Length != after.Targets.Length) return true;
        for (int i = 0; i < before.Targets.Length; i++)
        {
            var a = before.Targets[i]; var b = after.Targets[i];
            if (a.Name != b.Name || a.Address != b.Address ||
                a.Protocol != b.Protocol || a.Port != b.Port) return true;
        }
        return false;
    }

    private void EditSettings()
    {
        if (_settingsForm is { IsDisposed: false })
        {
            _settingsForm.Activate();
            return;
        }
        if (_editingGeometry) FinishGeometryEdit();
        _info.Hide();
        _showHover = false;

        var original = _data.Settings.Copy();
        _settingsBeforeEdit = original;
        var editor = new SettingsForm(original.Copy());
        _settingsForm = editor;

        editor.PreviewChanged += candidate =>
        {
            if (_settingsForm != editor || IsDisposed) return;
            _data.Settings = candidate.Copy();
            _probeTimer.Interval = Math.Clamp(candidate.ProbeIntervalSeconds, 3, 120) * 1000;
            ApplyAppearance();
            Reposition();
        };
        editor.FormClosed += (_, _) =>
        {
            bool commit = editor.DialogResult == DialogResult.OK && editor.SavedSettings is not null;
            var final = commit ? editor.SavedSettings! : original;
            bool targetChanged = commit && TargetsDiffer(original, final);
            _data.Settings = final.Copy();
            _settingsBeforeEdit = null;
            _settingsForm = null;
            _probeTimer.Interval = Math.Clamp(final.ProbeIntervalSeconds, 3, 120) * 1000;
            _network.Invalidate();
            if (targetChanged)
            {
                _data.Histories = [new TargetHistory(), new TargetHistory()];
                _trackers = [new QualityTracker(_data.Histories[0]), new QualityTracker(_data.Histories[1])];
                Array.Clear(_snapshots);
            }
            bool editNext = commit && editor.ResizeAfterSave;
            editor.Dispose();
            if (!IsDisposed && !Disposing)
            {
                ApplyAppearance();
                Reposition();
                if (commit) SaveSafe();
                if (editNext) BeginGeometryEdit();
                RefreshFullscreenState();
            }
        };
        // Modeless means no pause in the traffic/probe timers, and the widget
        // remains visible while appearance controls preview against the real UI.
        editor.Show(this);
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

        bool narrow = Width < 275;
        bool showGraphs = _data.Settings.ShowGraphs && Height >= (narrow ? 130 : 82);
        float textScale = Math.Clamp(Width / (narrow ? 28f : 35f), 8.5f, 12f);
        using var speedFont = new Font("Segoe UI Semibold", textScale, FontStyle.Bold, GraphicsUnit.Point);
        using var accentBrush = new SolidBrush(Theme.Accent);
        using var textBrush = new SolidBrush(Theme.Text);
        using var border = new Pen(_editingGeometry ? Theme.Accent : Theme.Border, _editingGeometry ? 2f : 1f);
        using var format = new StringFormat { Trimming = StringTrimming.EllipsisCharacter,
            FormatFlags = StringFormatFlags.NoWrap, LineAlignment = StringAlignment.Center };

        g.DrawRectangle(border, 1, 1, Width - 3, Height - 3);
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
        string up = "↑ " + MonitorMath.Rate(_speed.UploadBytesPerSecond, _data.Settings.UseBits);
        string down = "↓ " + MonitorMath.Rate(_speed.DownloadBytesPerSecond, _data.Settings.UseBits);

        if (narrow)
        {
            float rowHeight = (showGraphs ? Height - 35f : Height - 8f) / 2f;
            g.DrawString(up, speedFont, textBrush,
                new RectangleF(contentX, 4f, contentWidth, rowHeight), format);
            g.DrawString(down, speedFont, textBrush,
                new RectangleF(contentX, 4f + rowHeight, contentWidth, rowHeight), format);
            if (showGraphs)
                Graph(g, _downSamples, new Rectangle((int)contentX + 2, Height - 29,
                    (int)contentWidth - 5, 21));
        }
        else
        {
            float half = contentWidth / 2f;
            float labelHeight = showGraphs ? Math.Min(38f, Height - 37f) : Height - 12f;
            float y = showGraphs ? 4f : 6f;
            g.DrawString(up, speedFont, textBrush,
                new RectangleF(contentX, y, half - 5, labelHeight), format);
            g.DrawString(down, speedFont, textBrush,
                new RectangleF(contentX + half, y, half - 5, labelHeight), format);
            if (showGraphs)
            {
                int graphY = Math.Max(27, Height - 31);
                var graphWidth = (int)Math.Max(14, half - 12);
                Graph(g, _upSamples, new Rectangle((int)contentX + 2, graphY, graphWidth, 21));
                Graph(g, _downSamples, new Rectangle((int)(contentX + half) + 2, graphY, graphWidth, 21));
            }
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
        try
        {
            if (_settingsBeforeEdit is null) _storage.Save(_data);
            else _storage.Save(new PersistedData
            {
                Settings = _settingsBeforeEdit.Copy(),
                Totals = _data.Totals,
                Histories = _data.Histories
            });
        }
        catch (Exception ex) { Debug.WriteLine("Settings persistence error: " + ex); }
    }

    protected override void OnFormClosed(FormClosedEventArgs e)
    {
        if (_editingGeometry) CancelGeometryEdit();
        _stop.Cancel();
        _trafficTimer.Stop(); _probeTimer.Stop(); _hoverTimer.Stop(); _fullscreenTimer.Stop();
        if (_settingsForm is { IsDisposed: false }) _settingsForm.Close();
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
