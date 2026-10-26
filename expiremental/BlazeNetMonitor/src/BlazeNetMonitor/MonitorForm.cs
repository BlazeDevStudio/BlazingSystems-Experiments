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
    private DonationSplashForm? _donationSplash;
    private AppSettings? _settingsBeforeEdit;
    private readonly System.Windows.Forms.Timer _fullscreenTimer = new() { Interval = 750 };
    private readonly System.Windows.Forms.Timer _glancePreviewTimer = new() { Interval = 2300 };
    // Periodic reassertion is limited to explicitly selected taskbar overlay mode.
    private readonly System.Windows.Forms.Timer _overlayGuardTimer = new() { Interval = 1900 };
    private static readonly Color TransparentKeyDark = Color.FromArgb(9, 10, 11);
    private static readonly Color TransparentKeyLight = Color.FromArgb(250, 251, 252);
    private bool IsBackgroundless => _data.Settings.TransparentBackground && !_editingGeometry && !Theme.HighContrast;
    private Color TransparentCanvas => Theme.IsDark ? TransparentKeyDark : TransparentKeyLight;
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
    private readonly Bitmap?[] _favicons = new Bitmap?[2];
    private CancellationTokenSource? _faviconLoad;
    private int _faviconGeneration;
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
    private const int MinimumWidgetWidth = WidgetGeometry.CompactMinimumWidth;
    private const int MinimumWidgetHeight = WidgetGeometry.CompactMinimumHeight;

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
            if (!_glancePreviewTimer.Enabled &&
                !Bounds.Contains(Cursor.Position) && !_info.Bounds.Contains(Cursor.Position))
            {
                _hoverTimer.Stop(); _info.Hide(); _showHover = false;
            }
        };
        _trafficTimer.Tick += (_, _) => SampleTraffic();
        _probeTimer.Tick += async (_, _) => await ProbeTargets();
        _probeTimer.Interval = Math.Clamp(_data.Settings.ProbeIntervalSeconds, 3, 120) * 1000;
        _fullscreenTimer.Tick += (_, _) => RefreshFullscreenState();
        _overlayGuardTimer.Tick += (_, _) => PromoteOptionalOverlay();
        _glancePreviewTimer.Tick += (_, _) =>
        {
            _glancePreviewTimer.Stop();
            if (_settingsForm is not null)
            {
                _showHover = false;
                _info.Hide();
            }
        };
        Shown += async (_, _) =>
        {
            RestoreGeometry(); _trafficTimer.Start(); _probeTimer.Start();
            _fullscreenTimer.Start(); _overlayGuardTimer.Start();
            PromoteOptionalOverlay();
            if (_data.Settings.ShowFavicons) _ = ReloadFaviconsAsync();
            await ProbeTargets();
            if (!IsDisposed && DonationSplashPolicy.ShouldShow(
                _data.Settings.DonationSplashMode, _data.DonationSplashViewed))
                BeginInvoke(new Action(() => ShowDonationSplash(force: false)));
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
        bool backgroundless = IsBackgroundless;
        var backdrop = backgroundless ? TransparentCanvas : Theme.Background;
        // A true color-keyed hole in this form, not a semi-transparent rectangle.
        // During resize editing, backgroundless mode is suspended so handles remain clickable.
        if (!backgroundless) TransparencyKey = Color.Empty;
        BackColor = backdrop;
        if (backgroundless) TransparencyKey = backdrop;
        Opacity = Theme.HighContrast ? 1d : Math.Clamp(_data.Settings.WidgetOpacityPercent, 40, 100) / 100d;
        _info.ApplyAppearance(_data.Settings);
        int newInterval = Math.Clamp(_data.Settings.GraphRefreshSeconds, 1, 5) * 1000;
        if (_trafficTimer.Interval != newInterval)
        {
            // Historical graph samples have the old cadence; reset graph only,
            // never the user's accumulated traffic totals.
            _upSamples.Clear();
            _downSamples.Clear();
            _trafficTimer.Interval = newInterval;
        }
        // IMPORTANT: live preview must not restyle native ComboBoxes while dropped down.
        Invalidate();
    }

    private Rectangle SafeBounds(Rectangle candidate, Screen screen)
        => WidgetGeometry.ConstrainToMode(candidate, screen.Bounds, screen.WorkingArea,
            WidgetGeometry.ResolvePlacement(_data.Settings));

    [StructLayout(LayoutKind.Sequential)]
    private struct AppBarData
    {
        public uint cbSize;
        public nint hWnd;
        public uint callbackMessage;
        public uint edge;
        public WinRect rc;
        public nint lParam;
    }

    [DllImport("shell32.dll", SetLastError = true)]
    private static extern nuint SHAppBarMessage(uint message, ref AppBarData appBar);

    [DllImport("user32.dll", SetLastError = true)]
    [return: MarshalAs(UnmanagedType.Bool)]
    private static extern bool SetWindowPos(nint window, nint insertAfter,
        int x, int y, int cx, int cy, uint flags);

    private void PromoteOptionalOverlay()
    {
        // Opt-in taskbar overlay is independent of Explorer. Do not steal focus.
        if (WidgetGeometry.ResolvePlacement(_data.Settings) != WidgetGeometry.InsideTaskbar ||
            !Visible || _hiddenForFullscreen || !IsHandleCreated ||
            _settingsForm is not null) return; // never raise widget over an open Settings dropdown
        const uint flags = 0x0001 | 0x0002 | 0x0010; // NOSIZE | NOMOVE | NOACTIVATE
        SetWindowPos(Handle, (nint)(-1), 0, 0, 0, 0, flags);
    }

    private static Rectangle TaskbarBounds(Screen screen)
    {
        // ABM_GETTASKBARPOS = 5. Primary system taskbar only.
        if (screen.Primary)
        {
            var data = new AppBarData { cbSize = (uint)Marshal.SizeOf<AppBarData>() };
            if (SHAppBarMessage(5u, ref data) != 0)
            {
                var r = Rectangle.FromLTRB(data.rc.Left, data.rc.Top, data.rc.Right, data.rc.Bottom);
                if (r.Width > 0 && r.Height > 0 && screen.Bounds.IntersectsWith(r))
                    return r;
            }
        }

        // Secondary-monitor and shell fallback: derive from actual work-area
        // exclusion; do not assume the taskbar is always 48 pixels high.
        var bounds = screen.Bounds;
        var work = screen.WorkingArea;
        if (work.Bottom < bounds.Bottom)
            return new Rectangle(bounds.Left, work.Bottom, bounds.Width, bounds.Bottom - work.Bottom);
        if (work.Top > bounds.Top)
            return new Rectangle(bounds.Left, bounds.Top, bounds.Width, work.Top - bounds.Top);
        if (work.Left > bounds.Left)
            return new Rectangle(bounds.Left, bounds.Top, work.Left - bounds.Left, bounds.Height);
        if (work.Right < bounds.Right)
            return new Rectangle(work.Right, bounds.Top, bounds.Right - work.Right, bounds.Height);
        return Rectangle.Empty;
    }

    private void RestoreGeometry()
    {
        Width = Math.Clamp(_data.Settings.WidgetWidth, MinimumWidgetWidth, MaximumSize.Width);
        Height = Math.Clamp(_data.Settings.WidgetHeight, MinimumWidgetHeight, MaximumSize.Height);
        if (_data.Settings.FreeformPositioned &&
            _data.Settings.WidgetX != -1 && _data.Settings.WidgetY != -1)
            Location = new Point(_data.Settings.WidgetX, _data.Settings.WidgetY);
        Reposition();
    }

    private void Reposition()
    {
        if (_editingGeometry || IsDisposed) return;
        var mode = WidgetGeometry.ResolvePlacement(_data.Settings);
        var screen = _data.Settings.FreeformPositioned
            ? Screen.FromRectangle(Bounds)
            : (Screen.PrimaryScreen ?? Screen.FromControl(this));
        var next = Bounds;
        if (!_data.Settings.FreeformPositioned)
        {
            var positionMode = mode == WidgetGeometry.Floating ? WidgetGeometry.AboveTaskbar : mode;
            next = WidgetGeometry.DockPosition(Bounds, screen.WorkingArea,
                TaskbarBounds(screen), positionMode, _data.Settings.HorizontalOffset);
        }
        Bounds = SafeBounds(next, screen);
        PromoteOptionalOverlay();
    }

    private void FitTaskbarHeight()
    {
        var screen = Screen.FromRectangle(Bounds);
        var bar = TaskbarBounds(screen);
        if (bar.IsEmpty || bar.Width < bar.Height)
        {
            MessageBox.Show("Unable to determine a horizontal taskbar on this monitor. " +
                "Use Resize / move to set the dimensions manually.", "BlazeNetMonitor");
            return;
        }

        _data.Settings.PlacementMode = WidgetGeometry.InsideTaskbar;
        _data.Settings.DockInsideTaskbar = true;
        int newHeight = Math.Clamp(bar.Height - 4, MinimumWidgetHeight, MaximumSize.Height);
        int x = _data.Settings.FreeformPositioned ? Left :
            bar.Right - _data.Settings.HorizontalOffset - Width;
        Bounds = SafeBounds(new Rectangle(x,
            bar.Top + (bar.Height - newHeight) / 2, Width, newHeight), screen);
        _data.Settings.FreeformPositioned = true;
        _data.Settings.WidgetX = Left;
        _data.Settings.WidgetY = Top;
        _data.Settings.WidgetWidth = Width;
        _data.Settings.WidgetHeight = Height;
        SaveSafe();
        PromoteOptionalOverlay();
        Invalidate();
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
        ApplyAppearance();
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
        ApplyAppearance();
        PromoteOptionalOverlay();
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
        ApplyAppearance();
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
        int margin = Math.Clamp(Math.Min(Width, Height) / 5, 5, ResizeMargin);
        if (p.X < margin) result |= DragEdges.Left;
        if (p.X >= Width - margin) result |= DragEdges.Right;
        if (p.Y < margin) result |= DragEdges.Top;
        if (p.Y >= Height - margin) result |= DragEdges.Bottom;
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
        _menu.Items.Add("Match taskbar height (overlay)", null, (_, _) => FitTaskbarHeight());
        _menu.Items.Add("Bring widget in front", null, (_, _) => RecoverWidget(false));
        _menu.Items.Add("Recover above taskbar (safe)", null, (_, _) => RecoverWidget(true));
        _menu.Items.Add(new ToolStripSeparator());
        _menu.Items.Add("BlazeNetMonitor · Settings", null, (_, _) => EditSettings());
        _menu.Items.Add("Support development · PayPal QR", null,
            (_, _) => ShowDonationSplash(force: true));
        _menu.Items.Add("Open connection table", null, (_, _) => ShowConnections());
        _menu.Items.Add("Refresh website favicons", null, (_, _) =>
        {
            if (!_data.Settings.ShowFavicons)
                MessageBox.Show("Enable circular website favicons in Settings → Metrics first.",
                    "BlazeNetMonitor", MessageBoxButtons.OK, MessageBoxIcon.Information);
            else _ = ReloadFaviconsAsync();
        });
        _menu.Items.Add("Reset session totals", null, (_, _) => { _data.Totals.ResetSession(); Invalidate(); SaveSafe(); });
        _menu.Items.Add("Copy status", null, (_, _) => CopyStatus());
        _menu.Items.Add(_data.Settings.TransparentBackground ? "Disable backgroundless mode" : "Enable backgroundless mode",
            null, (_, _) =>
            {
                _data.Settings.TransparentBackground = !_data.Settings.TransparentBackground;
                ApplyAppearance();
                SaveSafe();
                BuildMenu();
            });
        _menu.Items.Add(new ToolStripSeparator());
        _menu.Items.Add("Exit BlazeNetMonitor", null, (_, _) => Close());
    }

    private void RecoverWidget(bool switchToSafePosition)
    {
        if (switchToSafePosition)
        {
            _data.Settings.PlacementMode = WidgetGeometry.AboveTaskbar;
            _data.Settings.DockInsideTaskbar = false;
            _data.Settings.FreeformPositioned = false;
        }
        if (_hiddenForFullscreen && _data.Settings.AutoHideForFullscreen)
        {
            // Avoid disrupting a game. Recovery can occur after fullscreen closes.
            return;
        }
        if (_editingGeometry) FinishGeometryEdit();
        if (!Visible) Show();
        Reposition();
        PromoteOptionalOverlay();
        Invalidate();
        if (switchToSafePosition) SaveSafe();
    }

    protected override void WndProc(ref Message msg)
    {
        if (msg.Msg != 0 && (uint)msg.Msg == Program.ShowSettingsMessage)
        {
            try
            {
                using var reply = EventWaitHandle.OpenExisting(Program.RequestAckName);
                reply.Set();
            }
            catch (WaitHandleCannotBeOpenedException) { }
            BeginInvoke(new Action(EditSettings));
            return;
        }
        base.WndProc(ref msg);
    }

    private static Icon MakeIcon() => Branding.MakeIcon();

    private void ShowDonationSplash(bool force)
    {
        if (IsDisposed || Disposing) return;
        if (!force && !DonationSplashPolicy.ShouldShow(
            _data.Settings.DonationSplashMode, _data.DonationSplashViewed)) return;
        if (_donationSplash is { IsDisposed: false })
        {
            _donationSplash.Activate();
            return;
        }
        _data.DonationSplashViewed = true;
        SaveSafe(); // "first launch" is durably acknowledged as it is displayed.
        var form = new DonationSplashForm(() =>
        {
            _data.Settings.DonationSplashMode = DonationSplashPolicy.Never;
            SaveSafe();
        });
        _donationSplash = form;
        form.FormClosed += (_, _) =>
        {
            if (ReferenceEquals(_donationSplash, form)) _donationSplash = null;
            form.Dispose();
        };
        form.Show(); // modeless: the tiny network monitor keeps sampling.
    }

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
        _tray.Text = "BlazeNetMonitor " + MonitorMath.Rate(speed.DownloadBytesPerSecond,
            DisplayPreferences.UseBits(_data.Settings, Width, Height));
        if (_showHover) UpdateHover();
        Invalidate();
    }

    private static void AppendSample(Queue<double> list, double number)
    {
        list.Enqueue(number);
        while (list.Count > 620) list.Dequeue();
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
        editor.HoverPreviewRequested += () =>
        {
            if (_settingsForm != editor || _hiddenForFullscreen) return;
            _showHover = true;
            UpdateHover();
            _glancePreviewTimer.Stop();
            _glancePreviewTimer.Start();
        };
        editor.FormClosed += (_, _) =>
        {
            _glancePreviewTimer.Stop();
            _showHover = false;
            _info.Hide();
            bool commit = editor.DialogResult == DialogResult.OK && editor.SavedSettings is not null;
            var final = commit ? editor.SavedSettings! : original;
            bool targetChanged = commit && TargetsDiffer(original, final);
            bool faviconsChanged = commit && (targetChanged ||
                original.ShowFavicons != final.ShowFavicons);
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
                if (faviconsChanged) _ = ReloadFaviconsAsync();
                if (editNext) BeginGeometryEdit();
                RefreshFullscreenState();
            }
        };
        // Modeless means no pause in the traffic/probe timers, and the widget
        // remains visible while appearance controls preview against the real UI.
        editor.Show(this);
    }

    private async Task ReloadFaviconsAsync()
    {
        _faviconLoad?.Cancel();
        _faviconLoad?.Dispose();
        _faviconLoad = new CancellationTokenSource();
        int generation = ++_faviconGeneration;
        var ct = _faviconLoad.Token;
        if (!_data.Settings.ShowFavicons)
        {
            for (int i = 0; i < 2; i++)
            {
                _favicons[i]?.Dispose();
                _favicons[i] = null;
            }
            Invalidate();
            return;
        }

        var targets = _data.Settings.Targets.Select(t => new ProbeTarget
        {
            Name = t.Name, Address = t.Address, Protocol = t.Protocol, Port = t.Port
        }).ToArray();
        var fetched = await Task.WhenAll(targets.Select(t => FaviconLoader.TryLoadAsync(t, ct)));
        if (ct.IsCancellationRequested || generation != _faviconGeneration || IsDisposed)
        {
            foreach (var bitmap in fetched) bitmap?.Dispose();
            return;
        }

        for (int i = 0; i < 2; i++)
        {
            _favicons[i]?.Dispose();
            _favicons[i] = fetched[i];
        }
        Invalidate();
    }

    private static void DrawCircularFavicon(Graphics g, Bitmap? favicon, float x, float y, float size)
    {
        if (favicon is null) return;
        var state = g.Save();
        try
        {
            using var clip = new GraphicsPath();
            clip.AddEllipse(x, y, size, size);
            g.SetClip(clip);
            g.DrawImage(favicon, x, y, size, size);
        }
        finally { g.Restore(state); }
    }

    private string CurrentExtraMetric(string metric)
    {
        var samples = _snapshots.Where(s => s.State != ConnectionState.Unknown).ToArray();
        if (metric == "Totals")
            return $"Today ↑{MonitorMath.Bytes(_data.Totals.TodayUpload)} ↓{MonitorMath.Bytes(_data.Totals.TodayDownload)}";
        if (samples.Length == 0) return "Waiting for connection checks";
        return metric switch
        {
            "Latency" => $"Latency {samples.Average(s => s.LatencyMs):0} ms",
            "Loss" => $"Packet loss {samples.Max(s => s.LossPercent):0.#}%",
            "Jitter" => $"Jitter {samples.Max(s => s.JitterMs):0} ms",
            _ => string.Empty
        };
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
        g.Clear(IsBackgroundless ? TransparentCanvas : Theme.Background);

        bool inline = Height < 58 || Width >= 275 || Width < 180;
        bool compact = Height < 45 || Width < 190;
        int graphHeight = WidgetGeometry.GraphHeight(Height, _data.Settings.ShowGraphs);
        string metric = DisplayPreferences.EffectiveMetric(_data.Settings.MetricMode, Width, Height);
        bool showMetricLine = metric != "Speed" && Height >= 66;
        float extraHeight = showMetricLine ? 16f : 0f;
        float textHeight = Math.Max(11f, Height - graphHeight - extraHeight - 4f);
        bool showBadges = _data.Settings.ShowFavicons &&
            Width >= (Height < 39 ? 160 : 150) && _favicons.Any(b => b is not null);
        bool useBits = DisplayPreferences.UseBits(_data.Settings, Width, Height);
        int historySeconds = DisplayPreferences.GraphWindowSeconds(
            _data.Settings.GraphHistorySeconds, Width, Height);
        int historySamples = Math.Max(2, (int)Math.Ceiling(
            (double)historySeconds / Math.Clamp(_data.Settings.GraphRefreshSeconds, 1, 5)));
        string graphStyle = DisplayPreferences.NormalizeGraphStyle(_data.Settings.GraphStyle);
        Color uploadColor = DisplayPreferences.TryGraphColor(_data.Settings.GraphUploadColor, out var parsedUp)
            ? parsedUp : Theme.Accent;
        Color downloadColor = DisplayPreferences.TryGraphColor(_data.Settings.GraphDownloadColor, out var parsedDown)
            ? parsedDown : Theme.Muted;
        float size = compact
            ? Math.Clamp(Math.Min(textHeight * 0.48f, Width / 20f), 6.5f, 10f)
            : Math.Clamp(Math.Min(inline ? Width / 35f : Width / 25f,
                inline ? textHeight * 0.55f : textHeight * 0.3f), 8f, 12f);

        using var speedFont = new Font("Segoe UI Semibold", size, FontStyle.Bold, GraphicsUnit.Point);
        using var textBrush = new SolidBrush(Theme.Text);
        using var gripBrush = new SolidBrush(Theme.Accent);
        using var border = new Pen(_editingGeometry ? Theme.Accent : Theme.Border, _editingGeometry ? 2f : 1f);
        using var fmt = new StringFormat { Trimming = StringTrimming.EllipsisCharacter,
            FormatFlags = StringFormatFlags.NoWrap, LineAlignment = StringAlignment.Center };

        if (!IsBackgroundless)
            g.DrawRectangle(border, 1, 1, Width - 3, Height - 3);

        // Two independent targets retain their ordering in all layout profiles.
        if (Height < 39)
        {
            for (int k = 0; k < 2; k++)
            {
                using var dot = new SolidBrush(Theme.State(_snapshots[k].State));
                g.FillEllipse(dot, 6 + k * 13, (Height - 10) / 2f, 10, 10);
                if (showBadges) DrawCircularFavicon(g, _favicons[k],
                    35 + k * 15, (Height - 13) / 2f, 13);
            }
        }
        else
        {
            for (int k = 0; k < 2; k++)
            {
                using var dot = new SolidBrush(Theme.State(_snapshots[k].State));
                float center = Height / 2f + (k == 0 ? -12f : 12f);
                g.FillEllipse(dot, 12, center - 6, 12, 12);
                if (showBadges) DrawCircularFavicon(g, _favicons[k], 29, center - 7, 14);
            }
        }

        float contentX = Height < 39
            ? (showBadges ? 68f : 34f)
            : (showBadges ? 48f : 39f);
        float availableWidth = Math.Max(20f, Width - contentX - 5f);
        bool abbreviate = compact || (inline && Width < 260);
        string up = abbreviate
            ? "↑" + CompactRate(_speed.UploadBytesPerSecond, useBits)
            : "↑ " + MonitorMath.Rate(_speed.UploadBytesPerSecond, useBits);
        string down = abbreviate
            ? "↓" + CompactRate(_speed.DownloadBytesPerSecond, useBits)
            : "↓ " + MonitorMath.Rate(_speed.DownloadBytesPerSecond, useBits);

        if (inline)
        {
            float half = availableWidth / 2f;
            g.DrawString(up, speedFont, textBrush,
                new RectangleF(contentX, 2, Math.Max(14, half - 3), textHeight), fmt);
            g.DrawString(down, speedFont, textBrush,
                new RectangleF(contentX + half, 2, Math.Max(14, half - 3), textHeight), fmt);
            if (graphHeight > 0)
            {
                int width = Math.Max(4, (int)half - 5);
                int y = Height - graphHeight - 2;
                Graph(g, _upSamples, new Rectangle((int)contentX + 1, y, width, graphHeight),
                    uploadColor, graphStyle, historySamples);
                Graph(g, _downSamples, new Rectangle((int)(contentX + half) + 1, y, width, graphHeight),
                    downloadColor, graphStyle, historySamples);
            }
        }
        else
        {
            float row = textHeight / 2f;
            g.DrawString(up, speedFont, textBrush,
                new RectangleF(contentX, 2, availableWidth, row), fmt);
            g.DrawString(down, speedFont, textBrush,
                new RectangleF(contentX, row + 2, availableWidth, row), fmt);
            if (graphHeight > 0)
            {
                float half = availableWidth / 2f;
                int width = Math.Max(4, (int)half - 4);
                int y = Height - graphHeight - 2;
                Graph(g, _upSamples, new Rectangle((int)contentX + 1, y, width, graphHeight),
                    uploadColor, graphStyle, historySamples);
                Graph(g, _downSamples, new Rectangle((int)(contentX + half) + 1, y, width, graphHeight),
                    downloadColor, graphStyle, historySamples);
            }
        }

        if (showMetricLine)
        {
            using var metricFont = new Font("Segoe UI", 8f, FontStyle.Regular, GraphicsUnit.Point);
            using var metricBrush = new SolidBrush(Theme.Muted);
            string extra = CurrentExtraMetric(metric);
            float y = Height - graphHeight - extraHeight - 1;
            g.DrawString(extra, metricFont, metricBrush,
                new RectangleF(contentX, y, Math.Max(12, availableWidth), extraHeight), fmt);
        }

        if (_editingGeometry)
        {
            // The background is temporarily opaque during resizing for hit-testing.
            const int handle = 7;
            foreach (var pt in new[] {
                new Point(0, 0), new Point(Width - handle - 1, 0),
                new Point(0, Height - handle - 1),
                new Point(Width - handle - 1, Height - handle - 1) })
                g.FillRectangle(gripBrush, pt.X, pt.Y, handle, handle);
        }
    }

    private static string CompactRate(double bytesPerSecond, bool bits)
    {
        double value = Math.Max(0, bytesPerSecond) * (bits ? 8.0 : 1.0);
        string[] suffixes = bits ? ["b", "Kb", "Mb", "Gb"] : ["B", "KB", "MB", "GB"];
        int index = 0;
        while (value >= 1000 && index < suffixes.Length - 1)
        {
            value /= 1000;
            index++;
        }
        return $"{value:0.#}{suffixes[index]}";
    }

    private static void Graph(Graphics g, Queue<double> samples, Rectangle rect,
        Color color, string style, int historySeconds)
    {
        if (rect.Height < 3 || rect.Width < 3) return;
        using var pen = new Pen(color, rect.Height <= 6 ? 1f : 1.45f);
        var values = samples.TakeLast(Math.Clamp(historySeconds, 10, 600)).ToArray();
        if (values.Length < 2)
        {
            float baseline = rect.Bottom - Math.Max(1, rect.Height / 3f);
            g.DrawLine(pen, rect.Left, baseline, rect.Right, baseline);
            return;
        }

        double peak = Math.Max(1d, values.Max());
        var points = values.Select((v, index) => new PointF(
            rect.Left + (float)index / Math.Max(1, values.Length - 1) * (rect.Width - 1),
            rect.Bottom - 1 - (float)(Math.Max(0, v) / peak) * Math.Max(1, rect.Height - 1)
        )).ToArray();

        switch (style)
        {
            case "Smooth":
            {
                // Smooth is kept separate from Line: Catmull-Rom interpolation.
                if (points.Length < 3) g.DrawLines(pen, points);
                else g.DrawCurve(pen, points, 0.28f);
                break;
            }
            case "Dots":
            {
                using var dotsBrush = new SolidBrush(color);
                int stride = Math.Max(1, (int)Math.Ceiling(points.Length / (double)Math.Max(4, rect.Width / 3)));
                float radius = rect.Height < 10 ? 0.75f : 1.5f;
                for (int i = 0; i < points.Length; i += stride)
                    g.FillEllipse(dotsBrush, points[i].X - radius, points[i].Y - radius,
                        radius * 2, radius * 2);
                break;
            }
            case "Impulse":
            {
                int stride = Math.Max(1, (int)Math.Ceiling(points.Length / (double)Math.Max(4, rect.Width / 2)));
                for (int i = 0; i < points.Length; i += stride)
                    g.DrawLine(pen, points[i].X, rect.Bottom - 1, points[i].X, points[i].Y);
                break;
            }
            case "Filled":
            {
                using var shade = new SolidBrush(Color.FromArgb(85, color));
                using var polygon = new GraphicsPath();
                polygon.AddLines(points);
                polygon.AddLine(points[^1].X, points[^1].Y, points[^1].X, rect.Bottom);
                polygon.AddLine(points[^1].X, rect.Bottom, points[0].X, rect.Bottom);
                polygon.CloseFigure();
                g.FillPath(shade, polygon);
                g.DrawLines(pen, points);
                break;
            }
            case "Bars":
            {
                int bars = Math.Min(values.Length, Math.Max(2, rect.Width / 3));
                float barWidth = Math.Max(1f, rect.Width / (float)bars - 1f);
                using var brush = new SolidBrush(color);
                for (int i = 0; i < bars; i++)
                {
                    int source = values.Length - bars + i;
                    float normalized = (float)(Math.Max(0d, values[source]) / peak);
                    float height = Math.Max(1f, normalized * (rect.Height - 1));
                    float x = rect.Left + i * rect.Width / (float)bars;
                    g.FillRectangle(brush, x, rect.Bottom - height, barWidth, height);
                }
                break;
            }
            case "Steps":
            {
                using var path = new GraphicsPath();
                path.StartFigure();
                for (int i = 1; i < points.Length; i++)
                {
                    path.AddLine(points[i - 1].X, points[i - 1].Y,
                        points[i].X, points[i - 1].Y);
                    path.AddLine(points[i].X, points[i - 1].Y,
                        points[i].X, points[i].Y);
                }
                g.DrawPath(pen, path);
                break;
            }
            default:
                g.DrawLines(pen, points);
                break;
        }
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
                Histories = _data.Histories,
                WelcomeAcknowledged = _data.WelcomeAcknowledged,
                DonationSplashViewed = _data.DonationSplashViewed
            });
        }
        catch (Exception ex) { Debug.WriteLine("Settings persistence error: " + ex); }
    }

    protected override void OnFormClosed(FormClosedEventArgs e)
    {
        if (_editingGeometry) CancelGeometryEdit();
        _stop.Cancel();
        ++_faviconGeneration;
        _faviconLoad?.Cancel();
        _trafficTimer.Stop(); _probeTimer.Stop(); _hoverTimer.Stop(); _fullscreenTimer.Stop(); _glancePreviewTimer.Stop(); _overlayGuardTimer.Stop();
        if (_settingsForm is { IsDisposed: false }) _settingsForm.Close();
        if (_donationSplash is { IsDisposed: false }) _donationSplash.Close();
        Microsoft.Win32.SystemEvents.DisplaySettingsChanged -= OnDisplayChanged;
        Microsoft.Win32.SystemEvents.UserPreferenceChanged -= OnPreferenceChanged;
        SaveSafe();
        foreach (var favicon in _favicons) favicon?.Dispose();
        _faviconLoad?.Dispose();
        _tray.Visible = false;
        _tray.Dispose();
        _info.Close(); _info.Dispose();
        _menu.Dispose();
        _network.Dispose(); _stop.Dispose();
        base.OnFormClosed(e);
    }
}
