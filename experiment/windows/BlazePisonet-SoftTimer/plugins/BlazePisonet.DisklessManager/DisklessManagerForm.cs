namespace BlazePisonet.SoftTimer;

// Out-of-process optional administrator tool; never loaded into the coin/timer process.
public sealed partial class DisklessManagerForm : Form
{
    private List<DisklessClientAssignment> _profiles;

    public DisklessManagerForm()
    {
        Text = "BlazePisonet Diskless Manager (optional add-on)";
        Width = 1020;
        Height = 860;
        StartPosition = FormStartPosition.CenterScreen;
        AutoScroll = true;
        BackColor = BlazeTheme.Background;
        ForeColor = BlazeTheme.Text;
        Font = new Font("Segoe UI", 9.5f);
        _profiles = DisklessProfileStore.Load();
        BuildDiskless();
        RefreshDisklessProfiles();
        BlazeTheme.Apply(this);
    }

    private void ImportLegacyProfiles()
    {
        try
        {
            if (_profiles.Count != 0)
                throw new InvalidOperationException("Back up and clear add-on profiles before importing.");
            var legacy = DisklessProfileStore.ReadLegacySoftTimerProfiles();
            if (legacy.Count == 0) { _disklessProfileStatus.Text = "No legacy diskless profiles found."; return; }
            if (MessageBox.Show(
                $"Import {legacy.Count} diskless profile(s)? This copies records without modifying SoftTimer paid time or configuration.",
                "Import legacy diskless profiles", MessageBoxButtons.YesNo, MessageBoxIcon.Question,
                MessageBoxDefaultButton.Button2) != DialogResult.Yes) return;
            DisklessProfileStore.Save(legacy);
            _profiles = legacy.ToList();
            RefreshDisklessProfiles();
        }
        catch (Exception ex) when (ex is InvalidOperationException or IOException or UnauthorizedAccessException or System.Text.Json.JsonException)
        {
            _disklessProfileStatus.Text = "Legacy import refused: " + ex.Message;
        }
    }

    private static TextBox NewText() => new() { Height = 32 };
    private static FlowLayoutPanel NewPage(string title, string subtitle)
    {
        var root = new FlowLayoutPanel {
            AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink,
            FlowDirection = FlowDirection.TopDown, WrapContents = false,
            Padding = new Padding(10), Width = 950
        };
        root.Controls.Add(new Label { Text = title, Font = new Font("Segoe UI Semibold", 22, FontStyle.Bold), AutoSize = true, ForeColor = BlazeTheme.Text });
        root.Controls.Add(new Label { Text = subtitle, AutoSize = true, MaximumSize = new Size(890, 0), ForeColor = BlazeTheme.Muted, Margin = new Padding(0, 0, 0, 16) });
        return root;
    }
    private static FlowLayoutPanel Card(string title, string subtitle)
    {
        var c = new FlowLayoutPanel {
            FlowDirection = FlowDirection.TopDown, WrapContents = false,
            AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink,
            Width = 930, Padding = new Padding(16),
            Margin = new Padding(0, 0, 0, 14), BackColor = BlazeTheme.Panel
        };
        c.Controls.Add(new Label { Text = title, Font = new Font("Segoe UI Semibold", 13, FontStyle.Bold), AutoSize = true, ForeColor = BlazeTheme.Text });
        c.Controls.Add(new Label { Text = subtitle, AutoSize = true, MaximumSize = new Size(860, 0), ForeColor = BlazeTheme.Muted, Margin = new Padding(0, 2, 0, 12) });
        return c;
    }
    private static Panel Field(string label, Control control)
    {
        var p = new Panel { Width = 870, Height = control is TextBox tb && tb.Multiline ? 150 : 68, Margin = new Padding(0, 3, 0, 3) };
        p.Controls.Add(new Label { Text = label, AutoSize = true, ForeColor = BlazeTheme.Muted, Location = new Point(0, 0) });
        control.Location = new Point(0, 24);
        control.Width = 850;
        if (control is TextBox mt && mt.Multiline) control.Height = 110;
        p.Controls.Add(control);
        return p;
    }
    private static Button Button(string text, EventHandler click)
    {
        var b = new Button { Text = text, AutoSize = true, Height = 38, BackColor = BlazeTheme.Panel2, ForeColor = BlazeTheme.Text, FlatStyle = FlatStyle.Flat, Margin = new Padding(0, 5, 8, 5) };
        b.FlatAppearance.BorderColor = BlazeTheme.Line;
        b.Click += click;
        return b;
    }
    private static Button PrimaryButton(string text, EventHandler click)
    {
        var b = Button(text, click);
        b.BackColor = BlazeTheme.Accent;
        b.FlatAppearance.BorderSize = 0;
        b.Font = new Font("Segoe UI Semibold", 9.5f, FontStyle.Bold);
        return b;
    }
}
