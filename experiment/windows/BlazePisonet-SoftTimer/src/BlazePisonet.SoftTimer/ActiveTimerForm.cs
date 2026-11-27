using Microsoft.Win32;

namespace BlazePisonet.SoftTimer;

public sealed class ActiveTimerForm : Form
{
    private readonly AppConfig _config;
    private readonly Label _time = new();
    private readonly Label _status = new();
    private readonly Button _bank = new();

    public event Action? BankRequested;

    public ActiveTimerForm(AppConfig config)
    {
        _config = config;
        Text = "BlazePisonet SoftTimer";
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        TopMost = true;
        StartPosition = FormStartPosition.Manual;
        Size = new Size(300, 112);
        BackColor = BlazeTheme.Panel;
        ForeColor = BlazeTheme.Text;
        Opacity = 0.96;
        Padding = new Padding(14);

        _time.Text = "00:00";
        _time.Font = new Font("Segoe UI Semibold", 24, FontStyle.Bold);
        _time.ForeColor = BlazeTheme.Accent2;
        _time.AutoSize = true;
        _time.Location = new Point(14, 10);

        _status.Text = config.PcName;
        _status.Font = new Font("Segoe UI", 9);
        _status.ForeColor = BlazeTheme.Muted;
        _status.AutoEllipsis = true;
        _status.SetBounds(16, 58, 180, 22);

        _bank.Text = "BANK / LOGOUT";
        _bank.Visible = config.AllowMemberBankFromOverlay;
        _bank.BackColor = BlazeTheme.Panel2;
        _bank.ForeColor = BlazeTheme.Text;
        _bank.FlatStyle = FlatStyle.Flat;
        _bank.FlatAppearance.BorderColor = BlazeTheme.Line;
        _bank.SetBounds(184, 18, 102, 42);
        _bank.Click += (_, _) => BankRequested?.Invoke();

        Controls.AddRange([_time, _status, _bank]);

        Shown += (_, _) => SnapToCorner();
        SystemEvents.DisplaySettingsChanged += OnDisplayChanged;
    }

    public void UpdateRemaining(long seconds)
    {
        if (InvokeRequired)
        {
            BeginInvoke(() => UpdateRemaining(seconds));
            return;
        }

        _time.Text = BlazeTheme.FormatTime(seconds);
        _time.ForeColor = seconds > 0 && seconds <= Math.Max(1, _config.WarningSeconds)
            ? BlazeTheme.Warn
            : BlazeTheme.Accent2;
    }

    public void SetStatus(string text, bool good = false, bool warn = false)
    {
        if (InvokeRequired)
        {
            BeginInvoke(() => SetStatus(text, good, warn));
            return;
        }
        _status.Text = string.IsNullOrWhiteSpace(text) ? _config.PcName : text;
        _status.ForeColor = good ? BlazeTheme.Good : warn ? BlazeTheme.Warn : BlazeTheme.Muted;
    }

    private void SnapToCorner()
    {
        var area = Screen.PrimaryScreen?.WorkingArea ?? SystemInformation.WorkingArea;
        Location = new Point(Math.Max(area.Left, area.Right - Width - 14), area.Top + 14);
    }

    private void OnDisplayChanged(object? sender, EventArgs e) => SnapToCorner();

    protected override void Dispose(bool disposing)
    {
        if (disposing) SystemEvents.DisplaySettingsChanged -= OnDisplayChanged;
        base.Dispose(disposing);
    }
}

public sealed class MemberBankForm : Form
{
    private readonly TextBox _user = new();
    private readonly TextBox _pass = new();

    public string Username => _user.Text.Trim();
    public string Password => _pass.Text;

    public MemberBankForm()
    {
        Text = "Bank Remaining Time";
        Size = new Size(420, 245);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;
        TopMost = true;
        BackColor = BlazeTheme.Background;
        ForeColor = BlazeTheme.Text;

        Controls.Add(new Label
        {
            Text = "Bank remaining paid time",
            Font = new Font("Segoe UI Semibold", 15, FontStyle.Bold),
            AutoSize = true,
            Location = new Point(24, 20)
        });
        Controls.Add(new Label
        {
            Text = "Your running time will be moved into this member account.",
            AutoSize = true,
            ForeColor = BlazeTheme.Muted,
            Location = new Point(24, 52)
        });

        Controls.Add(new Label { Text = "Username", AutoSize = true, Location = new Point(24, 84), ForeColor = BlazeTheme.Muted });
        _user.SetBounds(24, 105, 350, 30);
        _user.BackColor = BlazeTheme.Panel2;
        _user.ForeColor = BlazeTheme.Text;
        Controls.Add(_user);

        Controls.Add(new Label { Text = "Password", AutoSize = true, Location = new Point(24, 140), ForeColor = BlazeTheme.Muted });
        _pass.SetBounds(24, 161, 220, 30);
        _pass.UseSystemPasswordChar = true;
        _pass.BackColor = BlazeTheme.Panel2;
        _pass.ForeColor = BlazeTheme.Text;
        Controls.Add(_pass);

        var bank = new Button
        {
            Text = "BANK & LOG OUT",
            Location = new Point(254, 158),
            Size = new Size(120, 34),
            BackColor = BlazeTheme.Accent,
            ForeColor = Color.White,
            FlatStyle = FlatStyle.Flat
        };
        bank.FlatAppearance.BorderSize = 0;
        bank.Click += (_, _) => { DialogResult = DialogResult.OK; Close(); };
        Controls.Add(bank);
    }
}
