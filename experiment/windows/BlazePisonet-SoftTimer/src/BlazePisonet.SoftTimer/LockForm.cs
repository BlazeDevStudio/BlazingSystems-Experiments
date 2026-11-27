namespace BlazePisonet.SoftTimer;

public sealed class LockForm : Form
{
    private readonly bool _primary;
    private readonly AppConfig _config;
    private readonly Label _shop = new();
    private readonly Label _pc = new();
    private readonly Label _banner = new();
    private readonly Label _time = new();
    private readonly Label _status = new();
    private readonly Button _requestCoin = new();
    private readonly Button _member = new();
    private DateTimeOffset? _deactivatedAt;
    public bool AllowClose { get; set; }

    public event Action? RequestCoin;
    public event Action? MemberLogin;
    public event Action? AdminSequenceArmRequested;

    public LockForm(AppConfig config, Screen screen, bool primary)
    {
        _config = config;
        _primary = primary;
        StartPosition = FormStartPosition.Manual;
        Bounds = screen.Bounds;
        FormBorderStyle = FormBorderStyle.None;
        ShowInTaskbar = false;
        TopMost = true;
        BackColor = ColorTranslator.FromHtml(config.BackgroundHex);
        KeyPreview = true;
        DoubleBuffered = true;

        BuildUi();
        LoadWallpaper();
        FormClosing += (_, e) => { if (!AllowClose) e.Cancel = true; };
        Deactivate += (_, _) => _deactivatedAt = DateTimeOffset.UtcNow;
        Activated += (_, _) =>
        {
            if (_deactivatedAt is { } d && (DateTimeOffset.UtcNow - d).TotalMilliseconds > 250)
                AdminSequenceArmRequested?.Invoke();
            _deactivatedAt = null;
            TopMost = true;
            Activate();
        };
    }

    private void BuildUi()
    {
        var root = new TableLayoutPanel
        {
            Dock = DockStyle.Fill,
            BackColor = Color.Transparent,
            ColumnCount = 1,
            RowCount = 7,
            Padding = new Padding(30)
        };
        root.RowStyles.Add(new RowStyle(SizeType.Percent, 15));
        root.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        root.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        root.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        root.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        root.RowStyles.Add(new RowStyle(SizeType.AutoSize));
        root.RowStyles.Add(new RowStyle(SizeType.Percent, 15));
        Controls.Add(root);

        _shop.Text = _config.ShopName;
        _shop.TextAlign = ContentAlignment.MiddleCenter;
        _shop.Font = new Font("Segoe UI Semibold", _primary ? 22 : 18, FontStyle.Bold);
        _shop.ForeColor = BlazeTheme.Accent2;
        _shop.AutoSize = true;
        _shop.Anchor = AnchorStyles.None;

        _pc.Text = _config.PcName;
        _pc.TextAlign = ContentAlignment.MiddleCenter;
        _pc.Font = new Font("Segoe UI", _primary ? 15 : 13, FontStyle.Regular);
        _pc.ForeColor = BlazeTheme.Muted;
        _pc.AutoSize = true;
        _pc.Anchor = AnchorStyles.None;

        _banner.Text = _config.Banner1;
        _banner.TextAlign = ContentAlignment.MiddleCenter;
        _banner.Font = new Font("Segoe UI Semibold", _primary ? 30 : 24, FontStyle.Bold);
        _banner.ForeColor = BlazeTheme.Text;
        _banner.AutoSize = true;
        _banner.MaximumSize = new Size(1000, 0);
        _banner.Anchor = AnchorStyles.None;

        _time.Text = "00:00";
        _time.TextAlign = ContentAlignment.MiddleCenter;
        _time.Font = new Font("Segoe UI", _primary ? 62 : 44, FontStyle.Bold);
        _time.ForeColor = BlazeTheme.Accent2;
        _time.AutoSize = true;
        _time.Anchor = AnchorStyles.None;

        _status.Text = "Waiting for credit";
        _status.TextAlign = ContentAlignment.MiddleCenter;
        _status.Font = new Font("Segoe UI", _primary ? 14 : 12);
        _status.ForeColor = BlazeTheme.Muted;
        _status.AutoSize = true;
        _status.Anchor = AnchorStyles.None;

        var actions = new FlowLayoutPanel
        {
            AutoSize = true,
            BackColor = Color.Transparent,
            FlowDirection = FlowDirection.LeftToRight,
            Anchor = AnchorStyles.None,
            Padding = new Padding(0, 18, 0, 0)
        };
        _requestCoin.Text = "REQUEST COIN SLOT";
        _requestCoin.Size = new Size(210, 48);
        _requestCoin.BackColor = BlazeTheme.Accent;
        _requestCoin.ForeColor = Color.White;
        _requestCoin.FlatStyle = FlatStyle.Flat;
        _requestCoin.FlatAppearance.BorderSize = 0;
        _requestCoin.Visible = _primary && _config.CoinTopology == CoinTopologyMode.CentralizedStation;
        _requestCoin.Click += (_, _) => RequestCoin?.Invoke();

        _member.Text = "MEMBER LOGIN";
        _member.Size = new Size(180, 48);
        _member.BackColor = BlazeTheme.Panel;
        _member.ForeColor = BlazeTheme.Text;
        _member.FlatStyle = FlatStyle.Flat;
        _member.FlatAppearance.BorderColor = BlazeTheme.Line;
        _member.Visible = _primary;
        _member.Click += (_, _) => MemberLogin?.Invoke();
        actions.Controls.Add(_requestCoin);
        actions.Controls.Add(_member);

        root.Controls.Add(new Panel { Dock = DockStyle.Fill, BackColor = Color.Transparent }, 0, 0);
        root.Controls.Add(_shop, 0, 1);
        root.Controls.Add(_pc, 0, 2);
        root.Controls.Add(_banner, 0, 3);
        root.Controls.Add(_time, 0, 4);
        root.Controls.Add(_status, 0, 5);
        root.Controls.Add(actions, 0, 6);
    }

    private void LoadWallpaper()
    {
        if (string.IsNullOrWhiteSpace(_config.WallpaperPath) || !File.Exists(_config.WallpaperPath)) return;
        try
        {
            BackgroundImage = Image.FromFile(_config.WallpaperPath);
            BackgroundImageLayout = ImageLayout.Zoom;
        }
        catch { }
    }

    public void UpdateRemaining(long seconds)
    {
        if (InvokeRequired) { BeginInvoke(() => UpdateRemaining(seconds)); return; }
        _time.Text = BlazeTheme.FormatTime(seconds);
    }

    public void SetStatus(string text, bool good = false, bool warn = false)
    {
        if (InvokeRequired) { BeginInvoke(() => SetStatus(text, good, warn)); return; }
        _status.Text = text;
        _status.ForeColor = good ? BlazeTheme.Good : warn ? BlazeTheme.Warn : BlazeTheme.Muted;
    }

    protected override bool ProcessCmdKey(ref Message msg, Keys keyData)
    {
        // The low-level hook handles protected combinations. Consume ordinary keys
        // so they cannot act on hidden Windows UI behind this full-screen surface.
        if (!AllowClose && keyData != Keys.Home) return true;
        return base.ProcessCmdKey(ref msg, keyData);
    }
}

public sealed class AdminLoginForm : Form
{
    private readonly AppConfig _config;
    private readonly TextBox _password = new();
    private readonly Label _message = new();
    private readonly System.Windows.Forms.Timer _timeout = new();
    private int _remaining;

    public bool Authenticated { get; private set; }

    public AdminLoginForm(AppConfig config)
    {
        _config = config;
        Text = "BlazePisonet SoftTimer Admin";
        Size = new Size(430, 250);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;
        TopMost = true;
        BackColor = BlazeTheme.Background;
        ForeColor = BlazeTheme.Text;

        var title = new Label { Text = "Administrator access", Font = new Font("Segoe UI Semibold", 16, FontStyle.Bold), AutoSize = true, Location = new Point(24, 24) };
        var help = new Label { Text = "Enter the SoftTimer administrator password.", AutoSize = true, Location = new Point(26, 60), ForeColor = BlazeTheme.Muted };
        _password.Location = new Point(26, 92); _password.Width = 370; _password.PasswordChar = '●'; _password.BackColor = BlazeTheme.Panel2; _password.ForeColor = BlazeTheme.Text;
        var login = new Button { Text = "UNLOCK ADMIN", Location = new Point(26, 132), Size = new Size(180, 42), BackColor = BlazeTheme.Accent, ForeColor = Color.White, FlatStyle = FlatStyle.Flat };
        login.FlatAppearance.BorderSize = 0;
        login.Click += (_, _) => TryLogin();
        _password.KeyDown += (_, e) => { if (e.KeyCode == Keys.Enter) TryLogin(); };
        _message.Location = new Point(26, 184); _message.Width = 370; _message.ForeColor = BlazeTheme.Muted;
        Controls.AddRange([title, help, _password, login, _message]);

        _remaining = Math.Max(10, config.AdminLoginTimeoutSeconds);
        _timeout.Interval = 1000;
        _timeout.Tick += (_, _) =>
        {
            _remaining--;
            Text = $"BlazePisonet SoftTimer Admin · {_remaining}s";
            if (_remaining <= 0) Close();
        };
        Shown += (_, _) => { _timeout.Start(); _password.Focus(); };
        FormClosed += (_, _) => _timeout.Stop();
    }

    private void TryLogin()
    {
        if (!_config.HasAdminPassword)
        {
            _message.Text = "Administrator password is not configured yet.";
            _message.ForeColor = BlazeTheme.Warn;
            return;
        }
        if (!Passwords.VerifyAdminPassword(_config, _password.Text))
        {
            _message.Text = "Incorrect password.";
            _message.ForeColor = BlazeTheme.Bad;
            _password.Clear();
            return;
        }
        Authenticated = true;
        DialogResult = DialogResult.OK;
        Close();
    }
}

public sealed class MemberLoginForm : Form
{
    private readonly TextBox _user = new();
    private readonly TextBox _pass = new();
    public string Username => _user.Text.Trim();
    public string Password => _pass.Text;

    public MemberLoginForm()
    {
        Text = "Member Login";
        Size = new Size(400, 240);
        StartPosition = FormStartPosition.CenterScreen;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        TopMost = true;
        BackColor = BlazeTheme.Background;
        ForeColor = BlazeTheme.Text;
        Controls.Add(new Label { Text = "Member account", Font = new Font("Segoe UI Semibold", 15, FontStyle.Bold), AutoSize = true, Location = new Point(24, 22) });
        Controls.Add(new Label { Text = "Username", AutoSize = true, Location = new Point(24, 65), ForeColor = BlazeTheme.Muted });
        _user.Location = new Point(24, 86); _user.Width = 340; _user.BackColor = BlazeTheme.Panel2; _user.ForeColor = BlazeTheme.Text;
        Controls.Add(_user);
        Controls.Add(new Label { Text = "Password", AutoSize = true, Location = new Point(24, 120), ForeColor = BlazeTheme.Muted });
        _pass.Location = new Point(24, 141); _pass.Width = 220; _pass.PasswordChar = '●'; _pass.BackColor = BlazeTheme.Panel2; _pass.ForeColor = BlazeTheme.Text;
        Controls.Add(_pass);
        var login = new Button { Text = "RESTORE TIME", Location = new Point(254, 138), Size = new Size(110, 32), BackColor = BlazeTheme.Accent, ForeColor = Color.White, FlatStyle = FlatStyle.Flat };
        login.Click += (_, _) => { DialogResult = DialogResult.OK; Close(); };
        Controls.Add(login);
    }
}
