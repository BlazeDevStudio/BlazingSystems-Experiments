using System.Net.NetworkInformation;
using Microsoft.Win32;
using BlazeNetMonitor.Core;

namespace BlazeNetMonitor;

internal sealed class SettingsForm : Form
{
    private readonly AppSettings _settings;
    private readonly ComboBox _adapter, _unit, _placement, _themeMode;
    private readonly TrackBar _opacity;
    private readonly Label _opacityValue;
    private readonly CheckBox _showGraphs, _systemAccent;
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
        ClientSize = new Size(545, 470);
        _adapters = NetworkInterface.GetAllNetworkInterfaces().ToList();
        var tabs = new TabControl { Dock = DockStyle.Fill };
        var general = new TabPage("General") { BackColor = Theme.Panel, ForeColor = Theme.Text };
        var targets = new TabPage("Health targets") { BackColor = Theme.Panel, ForeColor = Theme.Text };
        var appearance = new TabPage("Appearance") { BackColor = Theme.Panel, ForeColor = Theme.Text };
        var about = new TabPage("About") { BackColor = Theme.Panel, ForeColor = Theme.Text };
        tabs.TabPages.AddRange([general, appearance, targets, about]);
        Controls.Add(tabs);
        _adapter = Choice(general, "Network adapter", 24, ["Automatic (default route)", .._adapters.Select(a => a.Name)]);
        _adapter.SelectedIndex = Math.Max(0, _adapters.FindIndex(a => a.Id == settings.AdapterId) + 1);
        _unit = Choice(general, "Speed units", 97, ["Mbps / Kbps (bits)", "MB/s / KB/s (bytes)"]);
        _unit.SelectedIndex = settings.UseBits ? 0 : 1;
        _placement = Choice(general, "Taskbar location", 170, ["Above taskbar (safe, default)", "Overlay inside taskbar (may cover taskbar items)"]);
        _placement.SelectedIndex = settings.DockInsideTaskbar ? 1 : 0;
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
        _opacity.ValueChanged += (_, _) => _opacityValue.Text = _opacity.Value + "%";
        appearance.Controls.AddRange([_opacity, _opacityValue]);

        _systemAccent = new CheckBox { Left = 24, Top = 195, Width = 360, Height = 26,
            Text = "Follow Windows accent color", Checked = settings.UseSystemAccent };
        _showGraphs = new CheckBox { Left = 24, Top = 229, Width = 360, Height = 26,
            Text = "Show traffic graphs when there is room", Checked = settings.ShowGraphs };
        appearance.Controls.AddRange([_systemAccent, _showGraphs]);

        var resize = new Button { Left = 24, Top = 282, Width = 254, Height = 38,
            Text = "Save and resize / move widget" };
        resize.Click += (_, _) => { ResizeAfterSave = true; Save(); };
        appearance.Controls.Add(resize);
        appearance.Controls.Add(new Label { Left = 24, Top = 334, Width = 475, Height = 64,
            ForeColor = Theme.Muted,
            Text = "Drag the highlighted corners or edges to resize. Drag the center to move. Double-click the widget or right-click and finish to save. ESC cancels the edit." });


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
            Text = OperatingSystem.IsWindowsVersionAtLeast(10, 0, 22000)
                ? "Windows 11 detected · native deskband unavailable. Freeform/tray supported."
                : OperatingSystem.IsWindowsVersionAtLeast(10)
                    ? "Windows 10 detected · classic deskband integration is planned, not installed."
                    : "Windows version unknown · freeform/tray fallback." });
        var buttons = new FlowLayoutPanel { Dock = DockStyle.Bottom, FlowDirection = FlowDirection.RightToLeft, Height = 48, Padding = new Padding(7) };
        var ok = new Button { Text = "Save", Width = 85, DialogResult = DialogResult.None };
        ok.Click += (_, _) => Save();
        var cancel = new Button { Text = "Cancel", Width = 85, DialogResult = DialogResult.Cancel };
        buttons.Controls.AddRange([ok, cancel]);
        Controls.Add(buttons);
        buttons.BringToFront();
        AcceptButton = ok;
        CancelButton = cancel;
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
    private void Save()
    {
        for (int i = 0; i < 2; i++)
        {
            var address = _addresses[i].Text.Trim();
            var proto = Enum.Parse<TargetProtocol>(_protocols[i].SelectedItem!.ToString()!);
            if (string.IsNullOrWhiteSpace(address) || (proto == TargetProtocol.Https && (!Uri.TryCreate(address, UriKind.Absolute, out var uri) || uri.Scheme != "https")))
            {
                MessageBox.Show($"Dot {i + 1}: enter a valid target. HTTPS requires a full https:// URL.");
                return;
            }
        }
        _settings.AdapterId = _adapter.SelectedIndex < 1 ? "auto" : _adapters[_adapter.SelectedIndex - 1].Id;
        _settings.UseBits = _unit.SelectedIndex == 0;
        _settings.DockInsideTaskbar = _placement.SelectedIndex == 1;
        _settings.HorizontalOffset = (int)_offset.Value;
        _settings.ProbeIntervalSeconds = (int)_interval.Value;
        _settings.ThemeMode = _themeMode.SelectedItem?.ToString() ?? "System";
        _settings.WidgetOpacityPercent = _opacity.Value;
        _settings.UseSystemAccent = _systemAccent.Checked;
        _settings.ShowGraphs = _showGraphs.Checked;
        for (int i = 0; i < 2; i++)
        {
            _settings.Targets[i].Name = _names[i].Text.Trim().Length > 0 ? _names[i].Text.Trim() : $"Target {i + 1}";
            _settings.Targets[i].Address = _addresses[i].Text.Trim();
            _settings.Targets[i].Protocol = Enum.Parse<TargetProtocol>(_protocols[i].SelectedItem!.ToString()!);
            _settings.Targets[i].Port = (int)_ports[i].Value;
        }
        try
        {
            using var run = Registry.CurrentUser.CreateSubKey(@"Software\Microsoft\Windows\CurrentVersion\Run");
            if (_autostart.Checked) run?.SetValue("BlazeNetMonitor", $"\"{Application.ExecutablePath}\"");
            else run?.DeleteValue("BlazeNetMonitor", false);
            _settings.StartWithWindows = _autostart.Checked;
        }
        catch (Exception ex) { MessageBox.Show("Could not configure Windows startup: " + ex.Message); return; }
        DialogResult = DialogResult.OK;
        Close();
    }
}
