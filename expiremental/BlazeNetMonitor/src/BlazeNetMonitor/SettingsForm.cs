using System.Net.NetworkInformation;
using Microsoft.Win32;
using BlazeNetMonitor.Core;

namespace BlazeNetMonitor;

internal sealed class SettingsForm : Form
{
    private readonly AppSettings _settings;
    private readonly ComboBox _adapter, _unit, _placement, _themeMode;
    private readonly ComboBox _graphStyle, _graphWindow, _metricMode, _unitMode;
    private readonly Button _upGraphColor, _downGraphColor;
    private string _upColorValue, _downColorValue;
    private readonly CheckBox _showFavicons;
    private readonly TrackBar _opacity, _hoverOpacity;
    private readonly Label _opacityValue, _hoverOpacityValue;
    private readonly CheckBox _showGraphs, _systemAccent, _fullscreen, _transparent;
    public event Action<AppSettings>? PreviewChanged;
    public event Action? HoverPreviewRequested;
    public AppSettings? SavedSettings { get; private set; }
    public bool ResizeAfterSave { get; private set; }
    private readonly NumericUpDown _offset, _interval;
    private readonly CheckBox _autostart;
    private readonly TextBox[] _names = new TextBox[2], _addresses = new TextBox[2];
    private readonly ComboBox[] _protocols = new ComboBox[2];
    private readonly NumericUpDown[] _ports = new NumericUpDown[2];
    private readonly List<NetworkInterface> _adapters;

    public SettingsForm(AppSettings settings)
    {
        _settings = settings;
        Text = "BlazeNetMonitor · Settings";
        Font = new Font("Segoe UI", 9.5f);
        BackColor = Theme.Background;
        ForeColor = Theme.Text;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        StartPosition = FormStartPosition.CenterScreen;
        MaximizeBox = false;
        ClientSize = new Size(545, 585);
        _adapters = NetworkInterface.GetAllNetworkInterfaces().ToList();
        var tabs = new TabControl { Dock = DockStyle.Fill };
        var general = new TabPage("General") { BackColor = Theme.Panel, ForeColor = Theme.Text };
        var targets = new TabPage("Health targets") { BackColor = Theme.Panel, ForeColor = Theme.Text };
        var appearance = new TabPage("Appearance") { BackColor = Theme.Panel, ForeColor = Theme.Text };
        var graphs = new TabPage("Graphs") { BackColor = Theme.Panel, ForeColor = Theme.Text };
        var metrics = new TabPage("Metrics") { BackColor = Theme.Panel, ForeColor = Theme.Text };
        var about = new TabPage("About") { BackColor = Theme.Panel, ForeColor = Theme.Text };
        tabs.TabPages.AddRange([general, appearance, graphs, metrics, targets, about]);
        Controls.Add(tabs);
        _adapter = Choice(general, "Network adapter", 24, ["Automatic (default route)", .._adapters.Select(a => a.Name)]);
        _adapter.SelectedIndex = Math.Max(0, _adapters.FindIndex(a => a.Id == settings.AdapterId) + 1);
        _unit = Choice(general, "Speed units", 97, ["Mbps / Kbps (bits)", "MB/s / KB/s (bytes)"]);
        _unit.SelectedIndex = settings.UseBits ? 0 : 1;
        _placement = Choice(general, "Widget placement", 170,
            ["Floating (desktop + taskbar area)", "Above taskbar (dock)", "Inside taskbar (overlay)"]);
        _placement.SelectedIndex = WidgetGeometry.ResolvePlacement(settings) switch
        {
            WidgetGeometry.Floating => 0,
            WidgetGeometry.InsideTaskbar => 2,
            _ => 1
        };
        LabelAt(general, "Horizontal offset from right edge (px)", 246);
        _offset = new NumericUpDown { Left = 24, Top = 269, Width = 116, Minimum = 0, Maximum = 4000, Value = Math.Clamp(settings.HorizontalOffset, 0, 4000) };
        general.Controls.Add(_offset);
        LabelAt(general, "Probe interval (seconds)", 305);
        _interval = new NumericUpDown { Left = 24, Top = 328, Width = 116, Minimum = 3, Maximum = 120, Value = Math.Clamp(settings.ProbeIntervalSeconds, 3, 120) };
        general.Controls.Add(_interval);
        _autostart = new CheckBox { Text = "Start with Windows (current user)", Left = 24, Top = 370, AutoSize = true, Checked = settings.StartWithWindows };
        general.Controls.Add(_autostart);
        LabelAt(appearance, "Color theme", 22);
        _themeMode = new ComboBox { Left = 24, Top = 48, Width = 310, DropDownStyle = ComboBoxStyle.DropDownList };
        _themeMode.Items.AddRange(["System", "Light", "Dark"]);
        _themeMode.SelectedItem = settings.ThemeMode is "Light" or "Dark" ? settings.ThemeMode : "System";
        appearance.Controls.Add(_themeMode);

        LabelAt(appearance, "Widget opacity", 98);
        _opacityValue = new Label { Left = 399, Top = 128, Width = 75, Height = 24, Text = Math.Clamp(settings.WidgetOpacityPercent, 40, 100) + "%" };
        _opacity = new TrackBar { Left = 16, Top = 124, Width = 365, Minimum = 40, Maximum = 100,
            TickFrequency = 10, Value = Math.Clamp(settings.WidgetOpacityPercent, 40, 100) };
        // Appearance callbacks are registered after every control is initialized.
        appearance.Controls.AddRange([_opacity, _opacityValue]);

        LabelAt(appearance, "At-a-glance opacity (independent)", 187);
        _hoverOpacityValue = new Label { Left = 399, Top = 218, Width = 75, Height = 24,
            Text = Math.Clamp(settings.HoverOpacityPercent, 40, 100) + "%" };
        _hoverOpacity = new TrackBar { Left = 16, Top = 210, Width = 365, Minimum = 40,
            Maximum = 100, TickFrequency = 10, Value = Math.Clamp(settings.HoverOpacityPercent, 40, 100) };
        appearance.Controls.AddRange([_hoverOpacity, _hoverOpacityValue]);

        _systemAccent = new CheckBox { Left = 24, Top = 274, Width = 420, Height = 25,
            Text = "Follow Windows accent color", Checked = settings.UseSystemAccent };
        _showGraphs = new CheckBox { Left = 24, Top = 307, Width = 420, Height = 25,
            Text = "Show live upload/download graphs (even in compact mode)", Checked = settings.ShowGraphs };
        _fullscreen = new CheckBox { Left = 24, Top = 340, Width = 460, Height = 25,
            Text = "Automatically hide on fullscreen apps and games", Checked = settings.AutoHideForFullscreen };
        _transparent = new CheckBox { Left = 24, Top = 374, Width = 430, Height = 25,
            Text = "Transparent background (text, dots and graphs only)",
            Checked = settings.TransparentBackground };
        appearance.Controls.AddRange([_systemAccent, _showGraphs, _fullscreen, _transparent]);

        var resize = new Button { Left = 24, Top = 413, Width = 265, Height = 36,
            Text = "Save and resize / move widget" };
        resize.Click += (_, _) => { ResizeAfterSave = true; Save(); };
        appearance.Controls.Add(resize);
        appearance.Controls.Add(new Label { Left = 24, Top = 462, Width = 485, Height = 58,
            ForeColor = Theme.Muted,
            Text = "Drag the highlighted corners or edges to resize, the center to move.\n" +
                "Double-click or right-click → Finish to save; Esc cancels." });

        _opacity.ValueChanged += (_, _) => { _opacityValue.Text = _opacity.Value + "%"; RaisePreview(); };
        _hoverOpacity.ValueChanged += (_, _) => { _hoverOpacityValue.Text = _hoverOpacity.Value + "%"; RaisePreview(); HoverPreviewRequested?.Invoke(); };
        _themeMode.SelectionChangeCommitted += (_, _) => RaisePreview();
        _themeMode.DropDownClosed += (_, _) =>
        {
            if (!IsDisposed && IsHandleCreated) BeginInvoke(new Action(ApplyEditorTheme));
        };
        _systemAccent.CheckedChanged += (_, _) => RaisePreview();
        _showGraphs.CheckedChanged += (_, _) => RaisePreview();
        _fullscreen.CheckedChanged += (_, _) => RaisePreview();
        _transparent.CheckedChanged += (_, _) => RaisePreview();
        _unit.SelectionChangeCommitted += (_, _) => RaisePreview();
        _adapter.SelectionChangeCommitted += (_, _) => RaisePreview();
        _placement.SelectionChangeCommitted += (_, _) => RaisePreview();
        _offset.ValueChanged += (_, _) => RaisePreview();
        _interval.ValueChanged += (_, _) => RaisePreview();

        // Graph customization deliberately lives in its own tab, to avoid
        // crowded appearance controls and dropdown focus/handle destruction.
        _graphStyle = Choice(graphs, "Graph drawing type", 22,
            ["Line", "Filled", "Bars", "Steps"]);
        _graphStyle.SelectedItem = DisplayPreferences.NormalizeGraphStyle(settings.GraphStyle);
        _graphWindow = Choice(graphs, "History duration", 98,
            ["Auto adaptive", "15 seconds", "30 seconds", "60 seconds",
             "120 seconds", "300 seconds", "600 seconds"]);
        var graphValues = new[] { 0, 15, 30, 60, 120, 300, 600 };
        int graphIndex = Array.IndexOf(graphValues, settings.GraphHistorySeconds);
        _graphWindow.SelectedIndex = Math.Max(0, graphIndex);
        _upColorValue = settings.GraphUploadColor;
        _downColorValue = settings.GraphDownloadColor;
        _upGraphColor = new Button { Left = 24, Top = 205, Width = 214, Height = 42,
            Text = "Upload graph color..." };
        _downGraphColor = new Button { Left = 249, Top = 205, Width = 214, Height = 42,
            Text = "Download graph color..." };
        _upGraphColor.Click += (_, _) => ChooseGraphColor(true);
        _downGraphColor.Click += (_, _) => ChooseGraphColor(false);
        graphs.Controls.AddRange([_upGraphColor, _downGraphColor]);
        graphs.Controls.Add(new Label { Left = 24, Top = 270, Width = 465, Height = 120,
            Text = "Graphs adapt to the widget dimensions, even at a 24-pixel taskbar height.\n" +
                "Auto history uses approximately 30 s in compact mode, 60 s in normal mode\n" +
                "and 120 s in wide mode. Graph colors are independent of health-dot colors.",
            ForeColor = Theme.Muted });

        _metricMode = Choice(metrics, "Extra information shown on the widget", 22,
            ["Auto adaptive", "Speed only", "Latency", "Packet loss", "Jitter", "Daily totals"]);
        _metricMode.SelectedIndex = settings.MetricMode switch
        {
            "Speed" => 1, "Latency" => 2, "Loss" => 3, "Jitter" => 4, "Totals" => 5, _ => 0
        };
        _unitMode = Choice(metrics, "Speed units", 98,
            ["Auto adaptive", "Bits per second", "Bytes per second"]);
        _unitMode.SelectedIndex = settings.UnitMode switch
        {
            "Bits" => 1, "Bytes" => 2, _ => 0
        };
        metrics.Controls.Add(new Label { Left = 24, Top = 175, Width = 476, Height = 95,
            ForeColor = Theme.Muted,
            Text = "Auto adaptive always prioritizes both live transfer rates in compact mode.\n" +
                "As height/width increase, secondary metrics become available.\n" +
                "Health dots reflect probe history, not whether you're downloading data." });
        _showFavicons = new CheckBox { Left = 24, Top = 290, Width = 490, Height = 50,
            Text = "Show round website favicons beside health dots (opt-in network fetch)",
            Checked = settings.ShowFavicons };
        metrics.Controls.Add(_showFavicons);
        metrics.Controls.Add(new Label { Left = 24, Top = 352, Width = 465, Height = 75,
            ForeColor = Theme.Muted,
            Text = "Only configured public HTTPS targets are fetched. Images are memory-cached;\n" +
                "private/local addresses and untrusted redirects are blocked.\n" +
                "If a site has no readable favicon.ico, only the health dot appears." });

        _graphStyle.SelectionChangeCommitted += (_, _) => RaisePreview();
        _graphWindow.SelectionChangeCommitted += (_, _) => RaisePreview();
        _metricMode.SelectionChangeCommitted += (_, _) => RaisePreview();
        _unitMode.SelectionChangeCommitted += (_, _) => RaisePreview();
        _showFavicons.CheckedChanged += (_, _) => RaisePreview();
        _upGraphColor.Text = "Upload: " + _upColorValue;
        _downGraphColor.Text = "Download: " + _downColorValue;

        for (int i = 0; i < 2; i++)
        {
            int y = 25 + i * 176;
            LabelAt(targets, $"DOT {i + 1} · {settings.Targets[i].Name}", y);
            _names[i] = new TextBox { Left = 24, Top = y + 27, Width = 156, Text = settings.Targets[i].Name };
            _protocols[i] = new ComboBox { Left = 188, Top = y + 27, Width = 124, DropDownStyle = ComboBoxStyle.DropDownList };
            _protocols[i].Items.AddRange(Enum.GetNames<TargetProtocol>());
            _protocols[i].SelectedItem = settings.Targets[i].Protocol.ToString();
            _ports[i] = new NumericUpDown { Left = 320, Top = y + 27, Width = 85, Minimum = 1, Maximum = 65535, Value = Math.Clamp(settings.Targets[i].Port, 1, 65535) };
            _addresses[i] = new TextBox { Left = 24, Top = y + 66, Width = 380, Text = settings.Targets[i].Address };
            targets.Controls.AddRange([_names[i], _protocols[i], _ports[i], _addresses[i]]);
            var hint = new Label { Left = 24, Top = y + 103, Width = 456, Height = 48, ForeColor = Theme.Muted, Text = "Host or DNS: 1.1.1.1 / example.com   ·   HTTPS: https://example.com\nTCP uses Port. Green/blue require consistently good probes." };
            targets.Controls.Add(hint);
        }
        about.Controls.Add(new Label { Left = 24, Top = 28, Width = 455, Height = 310, ForeColor = Theme.Text, Text = "BlazeNetMonitor v0.2.0 development\nBlaze Systems · Windows 10/11 x86/x64/Arm64\n\nIndependent implementation inspired by the functionality of classic NetSpeedMonitor by Florian Gilles. No original code or artwork bundled.\n\nStatus thresholds are latency, jitter, and packet-loss estimates, not an internet speed test. Firewalls may block ICMP; choose HTTPS for those networks.\n\nWorks without administrator rights. All settings and totals are stored locally." });
        about.Controls.Add(new Label { Left = 24, Top = 338, Width = 460, Height = 50,
            ForeColor = Theme.Muted,
            Text = WindowsVersionPolicy.ShellFamily(Environment.OSVersion.Version) switch
            {
                "Windows10Classic" => "Windows 10 detected · classic deskband integration planned, not installed.",
                "Windows11OrLater" => "Windows 11+ detected · freeform/tray fallback, no native deskband.",
                _ => "Unrecognized Windows build · safe freeform/tray fallback."
            } });
        var buttons = new FlowLayoutPanel { Dock = DockStyle.Bottom, FlowDirection = FlowDirection.RightToLeft, Height = 48, Padding = new Padding(7) };
        var ok = new Button { Text = "Save", Width = 85, DialogResult = DialogResult.None };
        ok.Click += (_, _) => Save();
        var cancel = new Button { Text = "Cancel", Width = 85, DialogResult = DialogResult.Cancel };
        buttons.Controls.AddRange([ok, cancel]);
        Controls.Add(buttons);
        buttons.BringToFront();
        AcceptButton = ok;
        CancelButton = cancel;
        ApplyEditorTheme();
    }
    private static ComboBox Choice(Control parent, string text, int y, string[] choices)
    {
        LabelAt(parent, text, y);
        var box = new ComboBox { Left = 24, Top = y + 26, Width = 430, DropDownStyle = ComboBoxStyle.DropDownList };
        box.Items.AddRange(choices);
        parent.Controls.Add(box);
        return box;
    }
    private static void LabelAt(Control parent, string text, int y) => parent.Controls.Add(new Label { Text = text, Left = 24, Top = y, Width = 445, Height = 24 });
    private AppSettings BuildPreview()
    {
        var next = _settings.Copy();
        next.AdapterId = _adapter.SelectedIndex < 1 ? "auto" : _adapters[_adapter.SelectedIndex - 1].Id;
        next.UseBits = _unit.SelectedIndex == 0;
        next.PlacementMode = _placement.SelectedIndex switch
        {
            0 => WidgetGeometry.Floating,
            2 => WidgetGeometry.InsideTaskbar,
            _ => WidgetGeometry.AboveTaskbar
        };
        next.DockInsideTaskbar = next.PlacementMode == WidgetGeometry.InsideTaskbar;
        // Selecting a dock mode anchors it correctly. Freeform retains last position.
        next.FreeformPositioned = next.PlacementMode == WidgetGeometry.ResolvePlacement(_settings)
            ? _settings.FreeformPositioned
            : next.PlacementMode == WidgetGeometry.Floating;
        next.HorizontalOffset = (int)_offset.Value;
        next.ProbeIntervalSeconds = (int)_interval.Value;
        next.ThemeMode = _themeMode.SelectedItem?.ToString() ?? "System";
        next.WidgetOpacityPercent = _opacity.Value;
        next.TransparentBackground = _transparent.Checked;
        next.HoverOpacityPercent = _hoverOpacity.Value;
        next.UseSystemAccent = _systemAccent.Checked;
        next.ShowGraphs = _showGraphs.Checked;
        next.GraphStyle = _graphStyle.SelectedItem?.ToString() ?? "Line";
        next.GraphHistorySeconds = _graphWindow.SelectedIndex switch
        {
            1 => 15, 2 => 30, 3 => 60, 4 => 120, 5 => 300, 6 => 600, _ => 0
        };
        next.GraphUploadColor = _upColorValue;
        next.GraphDownloadColor = _downColorValue;
        next.MetricMode = _metricMode.SelectedIndex switch
        {
            1 => "Speed", 2 => "Latency", 3 => "Loss", 4 => "Jitter", 5 => "Totals", _ => "Auto"
        };
        next.UnitMode = _unitMode.SelectedIndex switch
        {
            1 => "Bits", 2 => "Bytes", _ => "Auto"
        };
        next.ShowFavicons = _showFavicons.Checked;
        next.AutoHideForFullscreen = _fullscreen.Checked;
        return next;
    }

    private void RaisePreview()
    {
        // Do not restyle all live controls here: doing so closes an open native
        // ComboBox dropdown before the user can finish choosing a value.
        PreviewChanged?.Invoke(BuildPreview());
    }

    private void ChooseGraphColor(bool upload)
    {
        // ColorDialog is modal by design; only Apply the resulting color,
        // never recreate any ComboBox handle while a native dropdown is open.
        var current = upload ? _upColorValue : _downColorValue;
        using var picker = new ColorDialog { FullOpen = true, AnyColor = true };
        if (DisplayPreferences.TryGraphColor(current, out var parsed)) picker.Color = parsed;
        if (picker.ShowDialog(this) != DialogResult.OK) return;
        string value = $"#{picker.Color.R:X2}{picker.Color.G:X2}{picker.Color.B:X2}";
        if (upload)
        {
            _upColorValue = value;
            _upGraphColor.Text = "Upload: " + value;
        }
        else
        {
            _downColorValue = value;
            _downGraphColor.Text = "Download: " + value;
        }
        RaisePreview();
    }

    public void ApplyEditorTheme()
    {
        Theme.Apply(BuildPreview());
        BackColor = Theme.Background;
        ForeColor = Theme.Text;

        static void Restyle(Control parent)
        {
            foreach (Control child in parent.Controls)
            {
                if (child is TabPage or Panel or FlowLayoutPanel or TrackBar or CheckBox)
                    child.BackColor = Theme.Panel;
                if (child is TextBox or ComboBox or NumericUpDown)
                    child.BackColor = Theme.HighContrast ? SystemColors.Window : Theme.Panel;
                child.ForeColor = child is Label && !child.Enabled ? Theme.Muted : Theme.Text;
                Restyle(child);
            }
        }
        Restyle(this);
    }

    private void Save()
    {
        for (int i = 0; i < 2; i++)
        {
            var address = _addresses[i].Text.Trim();
            var proto = Enum.Parse<TargetProtocol>(_protocols[i].SelectedItem!.ToString()!);
            if (string.IsNullOrWhiteSpace(address) ||
                (proto == TargetProtocol.Https &&
                    (!Uri.TryCreate(address, UriKind.Absolute, out var uri) || uri.Scheme != "https")))
            {
                ResizeAfterSave = false;
                MessageBox.Show($"Dot {i + 1}: enter a valid target. HTTPS requires an https:// URL.");
                return;
            }
        }

        var saved = BuildPreview();
        for (int i = 0; i < 2; i++)
        {
            saved.Targets[i].Name = string.IsNullOrWhiteSpace(_names[i].Text) ? $"Target {i + 1}" : _names[i].Text.Trim();
            saved.Targets[i].Address = _addresses[i].Text.Trim();
            saved.Targets[i].Protocol = Enum.Parse<TargetProtocol>(_protocols[i].SelectedItem!.ToString()!);
            saved.Targets[i].Port = (int)_ports[i].Value;
        }
        try
        {
            using var run = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run");
            if (_autostart.Checked) run?.SetValue("BlazeNetMonitor", $"\"{Application.ExecutablePath}\"");
            else run?.DeleteValue("BlazeNetMonitor", false);
            saved.StartWithWindows = _autostart.Checked;
        }
        catch (Exception ex)
        {
            MessageBox.Show("Could not update Windows startup: " + ex.Message);
            return;
        }
        SavedSettings = saved;
        DialogResult = DialogResult.OK;
        Close();
    }
}
