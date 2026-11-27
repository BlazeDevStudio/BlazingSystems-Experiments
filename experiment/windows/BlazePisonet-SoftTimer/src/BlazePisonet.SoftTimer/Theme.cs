namespace BlazePisonet.SoftTimer;

public static class BlazeTheme
{
    public static readonly Color Background = ColorTranslator.FromHtml("#07111F");
    public static readonly Color Sidebar = ColorTranslator.FromHtml("#081421");
    public static readonly Color Panel = ColorTranslator.FromHtml("#0D1B2A");
    public static readonly Color Panel2 = ColorTranslator.FromHtml("#0A1623");
    public static readonly Color Line = ColorTranslator.FromHtml("#20384F");
    public static readonly Color Text = ColorTranslator.FromHtml("#EDF7FF");
    public static readonly Color Muted = ColorTranslator.FromHtml("#8DA6BA");
    public static readonly Color Accent = ColorTranslator.FromHtml("#7C5CFF");
    public static readonly Color Accent2 = ColorTranslator.FromHtml("#22D3EE");
    public static readonly Color Good = ColorTranslator.FromHtml("#66E5A3");
    public static readonly Color Bad = ColorTranslator.FromHtml("#FF788E");
    public static readonly Color Warn = ColorTranslator.FromHtml("#FFD06A");

    public static void Apply(Control root)
    {
        root.Font = new Font("Segoe UI", 9.5f);
        ApplyRecursive(root);
    }

    private static void ApplyRecursive(Control c)
    {
        if (c is Form || c is System.Windows.Forms.Panel || c is UserControl) c.BackColor = c.Tag as string == "sidebar" ? Sidebar : Background;
        if (c is Label label)
        {
            label.ForeColor = label.Tag as string == "muted" ? Muted : Text;
            label.BackColor = Color.Transparent;
        }
        else if (c is TextBox tb)
        {
            tb.BackColor = Panel2; tb.ForeColor = Text; tb.BorderStyle = BorderStyle.FixedSingle;
        }
        else if (c is ComboBox cb)
        {
            cb.BackColor = Panel2; cb.ForeColor = Text; cb.FlatStyle = FlatStyle.Flat;
        }
        else if (c is NumericUpDown nud)
        {
            nud.BackColor = Panel2; nud.ForeColor = Text; nud.BorderStyle = BorderStyle.FixedSingle;
        }
        else if (c is CheckBox check)
        {
            check.ForeColor = Text; check.BackColor = Color.Transparent;
        }
        else if (c is Button btn)
        {
            btn.FlatStyle = FlatStyle.Flat;
            btn.FlatAppearance.BorderColor = Line;
            btn.FlatAppearance.BorderSize = 1;
            btn.BackColor = btn.Tag as string == "primary" ? Accent : Panel;
            btn.ForeColor = Text;
            btn.Padding = new Padding(8, 2, 8, 2);
        }
        else if (c is ListBox lb)
        {
            lb.BackColor = Panel2; lb.ForeColor = Text; lb.BorderStyle = BorderStyle.FixedSingle;
        }
        foreach (Control child in c.Controls) ApplyRecursive(child);
    }

    public static Panel Card(string? title = null)
    {
        var panel = new Panel
        {
            BackColor = Panel,
            Padding = new Padding(16),
            Margin = new Padding(0, 0, 0, 12),
            AutoSize = true,
            AutoSizeMode = AutoSizeMode.GrowAndShrink
        };
        if (title is not null)
        {
            panel.Controls.Add(new Label
            {
                Text = title,
                ForeColor = Text,
                Font = new Font("Segoe UI Semibold", 11f),
                Dock = DockStyle.Top,
                Height = 30
            });
        }
        return panel;
    }

    public static string FormatTime(long seconds)
    {
        seconds = Math.Max(0, seconds);
        var ts = TimeSpan.FromSeconds(seconds);
        return ts.TotalHours >= 1 ? $"{(int)ts.TotalHours:00}:{ts.Minutes:00}:{ts.Seconds:00}" : $"{ts.Minutes:00}:{ts.Seconds:00}";
    }
}
