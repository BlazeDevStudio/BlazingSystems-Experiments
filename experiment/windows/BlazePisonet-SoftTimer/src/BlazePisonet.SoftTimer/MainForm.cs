using System.Diagnostics;

namespace BlazePisonet.SoftTimer;

public sealed class MainForm : Form
{
    private readonly AppController _controller;
    private readonly Panel _content = new() { Dock = DockStyle.Fill, Padding = new Padding(22), AutoScroll = true };
    private readonly Dictionary<string, Control> _pages = new(StringComparer.OrdinalIgnoreCase);
    private readonly Dictionary<string, Button> _nav = new(StringComparer.OrdinalIgnoreCase);
    private bool _allowExit;

    private readonly Label _mTime = MetricLabel();
    private readonly Label _mHardware = MetricLabel();
    private readonly Label _mIntegration = MetricLabel();
    private readonly Label _mSales = MetricLabel();

    private readonly CheckBox _enabled = new() { Text = "Enable SoftTimer kiosk enforcement" };
    private readonly ComboBox _timerSource = NewCombo();
    private readonly ComboBox _topology = NewCombo();
    private readonly NumericUpDown _secondsPerCoin = NewNumber(10, 86400, 300);
    private readonly NumericUpDown _warningSeconds = NewNumber(0, 7200, 60);
    private readonly CheckBox _warningSoundEnabled = new() { Text = "Play warning when paid time is low" };
    private readonly TextBox _warningSoundPath = NewText();
    private readonly CheckBox _showActiveOverlay = new() { Text = "Show floating time panel while customer time is active" };
    private readonly CheckBox _allowMemberBankOverlay = new() { Text = "Allow member BANK / LOGOUT from floating time panel" };
    private readonly ComboBox _serialMode = NewCombo();
    private readonly ComboBox _serialDevices = NewCombo();
    private readonly ComboBox _coinSignal = NewCombo();
    private readonly ComboBox _timerSignal = NewCombo();
    private readonly CheckBox _coinHigh = new() { Text = "Coin input active-high" };
    private readonly CheckBox _timerHigh = new() { Text = "Timer-active signal active-high" };
    private readonly NumericUpDown _debounce = NewNumber(10, 2000, 80);
    private readonly NumericUpDown _minPulse = NewNumber(1, 2000, 20);
    private readonly NumericUpDown _maxPulse = NewNumber(20, 5000, 1000);
    private readonly CheckBox _dtr = new() { Text = "DTR enabled" };
    private readonly CheckBox _rts = new() { Text = "RTS enabled" };
    private readonly Label _serialStatus = new() { AutoSize = true, ForeColor = BlazeTheme.Muted };

    private readonly TextBox _blazeAddress = NewText();
    private readonly ListBox _blazeDevices = new() { Height = 160 };

    private readonly TextBox _stationId = NewText();
    private readonly TextBox _coordinatorUrl = NewText();
    private readonly TextBox _sharedKey = NewText();
    private readonly NumericUpDown _listenPort = NewNumber(1024, 65535, 8765);
    private readonly NumericUpDown _coinWindow = NewNumber(15, 600, 90);

    private readonly CheckBox _pwifiEnabled = new() { Text = "Connect SoftTimer to BlazePwifi" };
    private readonly CheckBox _pwifiMirror = new() { Text = "Mirror local coin pulses to an active BlazePwifi coin window" };
    private readonly CheckBox _pwifiMembers = new() { Text = "Manage Pisonet members centrally in BlazePwifi" };
    private readonly NumericUpDown _pwifiMemberSync = NewNumber(5, 300, 15);
    private readonly TextBox _pwifiUrl = NewText();
    private readonly TextBox _pwifiId = NewText();
    private readonly TextBox _pwifiKey = NewText();
    private readonly Label _pwifiStatus = new() { AutoSize = true, ForeColor = BlazeTheme.Muted };

    private readonly CheckBox _blockTaskMgr = new() { Text = "Block Task Manager while locked" };
    private readonly CheckBox _blockRegedit = new() { Text = "Block Registry Editor while locked" };
    private readonly CheckBox _disableLogoff = new() { Text = "Disable Windows logoff while locked" };
    private readonly CheckBox _disablePower = new() { Text = "Disable Windows shutdown/restart UI while locked" };
    private readonly CheckBox _blockWinKeys = new() { Text = "Block Windows/Alt-Tab/Ctrl-Esc escape shortcuts" };
    private readonly CheckBox _lockMouse = new() { Text = "Confine mouse to the primary kiosk screen while locked" };
    private readonly CheckBox _watchdog = new() { Text = "Use watchdog/recovery task" };
    private readonly CheckBox _idleShutdown = new() { Text = "Shutdown after extended user inactivity" };
    private readonly NumericUpDown _idleMinutes = NewNumber(1, 1440, 30);
    private readonly CheckBox _unusual = new() { Text = "Detect extreme/repetitive input activity" };
    private readonly TextBox _blockedProcesses = NewMultiText();
    private readonly TextBox _blockedWebsites = NewMultiText();

    private readonly TextBox _shop = NewText();
    private readonly TextBox _pc = NewText();
    private readonly TextBox _banner1 = NewText();
    private readonly TextBox _banner2 = NewText();
    private readonly TextBox _wallpaper = NewText();

    private readonly TextBox _memberUser = NewText();
    private readonly TextBox _memberPass = NewText();
    private readonly ListBox _memberList = new() { Height = 220 };
    private readonly Label _memberModeStatus = new() { AutoSize = true, ForeColor = BlazeTheme.Muted };
    private readonly TextBox _memberTransferFrom = NewText();
    private readonly TextBox _memberTransferPass = NewText();
    private readonly TextBox _memberTransferTo = NewText();
    private readonly NumericUpDown _memberTransferMinutes = NewNumber(1, 10080, 30);
    private readonly ListBox _scheduleList = new() { Height = 210 };
    private List<NotificationSchedule> _schedules = new();
    private readonly TextBox _log = NewMultiText();

    public MainForm(AppController controller)
    {
        _controller = controller;
        _controller.AttachMainForm(this);
        Text = "BlazePisonet SoftTimer";
        MinimumSize = new Size(1080, 720);
        Size = new Size(1280, 820);
        StartPosition = FormStartPosition.CenterScreen;
        BackColor = BlazeTheme.Background;
        ForeColor = BlazeTheme.Text;
        Font = new Font("Segoe UI", 9.5f);

        BuildShell();
        BuildPages();
        LoadConfigToUi();
        RefreshSerialDevices();
        RefreshMembers();
        ShowPage("Dashboard");
        BlazeTheme.Apply(this);

        _controller.StatusChanged += () => SafeUi(RefreshStatus);
        _controller.Timer.RemainingChanged += _ => SafeUi(RefreshStatus);
        Shown += (_, _) =>
        {
            _controller.Start();
            if (_controller.Config.Enabled && _controller.Config.HasAdminPassword)
            {
                _controller.ExitAdminMaintenance();
                Hide();
            }
            else _controller.EnterAdminMaintenance();
        };
        FormClosing += OnFormClosing;
    }

    private void BuildShell()
    {
        var shell = new Panel { Dock = DockStyle.Fill };
        Controls.Add(shell);
        var side = new Panel { Dock = DockStyle.Left, Width = 225, Padding = new Padding(12), Tag = "sidebar", BackColor = BlazeTheme.Sidebar };
        shell.Controls.Add(_content);
        shell.Controls.Add(side);

        var brand = new Label { Text = "BLAZE\nPisonet SoftTimer", Font = new Font("Segoe UI Semibold", 16, FontStyle.Bold), ForeColor = BlazeTheme.Accent2, Height = 72, Dock = DockStyle.Top, TextAlign = ContentAlignment.MiddleLeft };
        side.Controls.Add(brand);
        var navPanel = new FlowLayoutPanel { Dock = DockStyle.Fill, FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoScroll = true, Padding = new Padding(0, 8, 0, 0) };
        side.Controls.Add(navPanel);
        navPanel.BringToFront();
        foreach (var name in new[] { "Dashboard", "Hardware", "Centralized", "BlazePwifi", "Members", "Schedules", "Security", "Appearance", "Diagnostics" })
        {
            var b = new Button { Text = name, Width = 185, Height = 42, TextAlign = ContentAlignment.MiddleLeft, Margin = new Padding(2), FlatStyle = FlatStyle.Flat, BackColor = BlazeTheme.Panel2, ForeColor = BlazeTheme.Text };
            b.FlatAppearance.BorderSize = 0;
            b.Click += (_, _) => ShowPage(name);
            navPanel.Controls.Add(b);
            _nav[name] = b;
        }
        var footer = new Label { Text = "v0.4.0\nASApp clean-room successor", ForeColor = BlazeTheme.Muted, Dock = DockStyle.Bottom, Height = 48, TextAlign = ContentAlignment.BottomLeft };
        side.Controls.Add(footer);
    }

    private void BuildPages()
    {
        BuildDashboard();
        BuildHardware();
        BuildCentralized();
        BuildBlazePwifi();
        BuildMembers();
        BuildSchedules();
        BuildSecurity();
        BuildAppearance();
        BuildDiagnostics();
    }

    private FlowLayoutPanel NewPage(string title, string subtitle)
    {
        var root = new FlowLayoutPanel { Dock = DockStyle.Top, AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink, FlowDirection = FlowDirection.TopDown, WrapContents = false, Padding = new Padding(0), Width = 950 };
        root.Controls.Add(new Label { Text = title, Font = new Font("Segoe UI Semibold", 22, FontStyle.Bold), AutoSize = true, ForeColor = BlazeTheme.Text, Margin = new Padding(0, 0, 0, 2) });
        root.Controls.Add(new Label { Text = subtitle, AutoSize = true, ForeColor = BlazeTheme.Muted, Margin = new Padding(0, 0, 0, 16) });
        return root;
    }

    private void BuildDashboard()
    {
        var root = NewPage("Dashboard", "Local timer, hardware and integration health at a glance.");
        var metrics = new TableLayoutPanel { ColumnCount = 4, RowCount = 1, Width = 930, Height = 125, Margin = new Padding(0, 0, 0, 14) };
        for (var i = 0; i < 4; i++) metrics.ColumnStyles.Add(new ColumnStyle(SizeType.Percent, 25));
        metrics.Controls.Add(MetricCard("TIME REMAINING", _mTime), 0, 0);
        metrics.Controls.Add(MetricCard("HARDWARE", _mHardware), 1, 0);
        metrics.Controls.Add(MetricCard("INTEGRATION", _mIntegration), 2, 0);
        metrics.Controls.Add(MetricCard("COIN EVENTS", _mSales), 3, 0);
        root.Controls.Add(metrics);

        var card = Card("System controls", "Enable protection only after hardware and admin password are configured.");
        _enabled.Margin = new Padding(0, 10, 0, 12);
        card.Controls.Add(_enabled);
        var row = new FlowLayoutPanel { AutoSize = true, FlowDirection = FlowDirection.LeftToRight, WrapContents = true, Width = 880 };
        var save = PrimaryButton("SAVE & APPLY", (_, _) => SaveApply());
        var add = PrimaryButton("ADD 5 MIN TEST", (_, _) => _controller.Timer.AddSeconds(300, "admin:test:" + Guid.NewGuid().ToString("N"), false, "Admin test credit"));
        var reset = Button("RESET TIMER", (_, _) => _controller.Timer.Reset("admin"));
        var lockNow = Button("LOCK NOW", (_, _) => { _controller.Timer.Reset("manual lock"); _controller.ExitAdminMaintenance(); Hide(); });
        var exit = Button("EXIT APP", (_, _) => ExitApplication());
        row.Controls.AddRange([save, add, reset, lockNow, exit]);
        card.Controls.Add(row);
        root.Controls.Add(card);
        _pages["Dashboard"] = root;
    }

    private void BuildHardware()
    {
        var root = NewPage("Hardware", "No COM1 requirement. Select a port manually or bind SoftTimer to the physical USB-RS232 device identity.");
        var timerCard = Card("Timer architecture", "Timer source and coin topology are independent settings.");
        timerCard.Controls.Add(Field("Timer source", _timerSource));
        timerCard.Controls.Add(Field("Coin topology", _topology));
        timerCard.Controls.Add(Field("Seconds added per coin pulse", _secondsPerCoin));
        timerCard.Controls.Add(Field("Low-time warning threshold (seconds)", _warningSeconds));
        timerCard.Controls.Add(_warningSoundEnabled);
        timerCard.Controls.Add(Field("Warning WAV file (optional)", _warningSoundPath));
        var warningButtons = new FlowLayoutPanel { AutoSize = true, Width = 880 };
        warningButtons.Controls.Add(Button("BROWSE WARNING WAV", (_, _) =>
        {
            using var dialog = new OpenFileDialog { Filter = "Wave audio|*.wav|All files|*.*" };
            if (dialog.ShowDialog() == DialogResult.OK) _warningSoundPath.Text = dialog.FileName;
        }));
        warningButtons.Controls.Add(Button("TEST WARNING", (_, _) => WarningSound.Play(ReadUiIntoConfig(false))));
        timerCard.Controls.Add(warningButtons);
        timerCard.Controls.Add(_showActiveOverlay);
        timerCard.Controls.Add(_allowMemberBankOverlay);
        root.Controls.Add(timerCard);

        var serialCard = Card("Serial / USB-RS232", "Device Manager COM ports are enumerated dynamically. Exact-device binding survives COM-number changes when Windows exposes a stable PnP identity.");
        serialCard.Controls.Add(Field("Selection policy", _serialMode));
        serialCard.Controls.Add(Field("Detected serial device", _serialDevices));
        var buttons = new FlowLayoutPanel { AutoSize = true, Width = 880 };
        buttons.Controls.Add(Button("RESCAN", (_, _) => RefreshSerialDevices()));
        buttons.Controls.Add(PrimaryButton("BIND EXACT DEVICE", (_, _) => BindExactDevice()));
        buttons.Controls.Add(Button("RECONNECT", (_, _) => { _controller.Serial.Connect(ReadUiIntoConfig(false)); RefreshStatus(); }));
        serialCard.Controls.Add(buttons);
        serialCard.Controls.Add(Field("Coin input signal", _coinSignal));
        serialCard.Controls.Add(_coinHigh);
        serialCard.Controls.Add(Field("External timer active signal", _timerSignal));
        serialCard.Controls.Add(_timerHigh);
        serialCard.Controls.Add(Field("Debounce (ms)", _debounce));
        serialCard.Controls.Add(Field("Minimum pulse (ms)", _minPulse));
        serialCard.Controls.Add(Field("Maximum pulse (ms)", _maxPulse));
        serialCard.Controls.Add(_dtr);
        serialCard.Controls.Add(_rts);
        serialCard.Controls.Add(_serialStatus);
        root.Controls.Add(serialCard);

        var blazeCard = Card("Blaze Pisonet Timer · wireless bridge", "Pairs to the existing ESP8266 timer over Wi-Fi/LAN without moving its countdown, relay, EEPROM, display or coin logic into Windows.");
        blazeCard.Controls.Add(Field("Timer address", _blazeAddress));
        var scan = PrimaryButton("SCAN LOCAL NETWORK", async (_, _) => await DiscoverTimers());
        blazeCard.Controls.Add(scan);
        blazeCard.Controls.Add(_blazeDevices);
        var pair = Button("PAIR SELECTED", (_, _) => PairSelectedTimer());
        blazeCard.Controls.Add(pair);
        root.Controls.Add(blazeCard);
        _pages["Hardware"] = root;
    }

    private void BuildCentralized()
    {
        var root = NewPage("Centralized Pisonet", "One coinslot can serve many SoftTimer stations. Stations request the slot, the coordinator queues them, and each routed credit carries a unique event ID to prevent duplicate time.");
        var card = Card("Coordinator / station", "Use Centralized Coordinator on the PC physically connected to the coinslot. Use Centralized Station on client PCs.");
        card.Controls.Add(Field("Station ID", _stationId));
        card.Controls.Add(Field("Coordinator URL", _coordinatorUrl));
        card.Controls.Add(Field("Shared pairing key", _sharedKey));
        card.Controls.Add(Field("Local peer API port", _listenPort));
        card.Controls.Add(Field("Coin window (seconds)", _coinWindow));
        var row = new FlowLayoutPanel { AutoSize = true, Width = 880 };
        row.Controls.Add(PrimaryButton("REQUEST COIN SLOT", async (_, _) => await _controller.RequestCentralCoinAsync()));
        row.Controls.Add(Button("GENERATE NEW KEY", (_, _) => { _sharedKey.Text = Convert.ToHexString(System.Security.Cryptography.RandomNumberGenerator.GetBytes(24)).ToLowerInvariant(); }));
        card.Controls.Add(row);
        root.Controls.Add(card);
        _pages["Centralized"] = root;
    }

    private void BuildBlazePwifi()
    {
        var root = NewPage("BlazePwifi", "Signed BlazePwifi controller integration for coin routing, heartbeat and centralized Pisonet member authority.");
        var card = Card("Server integration", "The Vendo key is the existing BlazePwifi controller secret. Keep it private.");
        card.Controls.Add(_pwifiEnabled);
        card.Controls.Add(Field("Vendo endpoint", _pwifiUrl));
        card.Controls.Add(Field("Controller ID", _pwifiId));
        _pwifiKey.UseSystemPasswordChar = true;
        card.Controls.Add(Field("Vendo key", _pwifiKey));
        card.Controls.Add(_pwifiMirror);
        card.Controls.Add(_pwifiMembers);
        card.Controls.Add(Field("Central member sync interval (seconds)", _pwifiMemberSync));

        var row = new FlowLayoutPanel { AutoSize = true, Width = 880 };
        row.Controls.Add(PrimaryButton("TEST CONNECTION", async (_, _) =>
        {
            SaveApply();
            var ok = await _controller.BlazePwifi.PingAsync();
            if (ok && _controller.Config.BlazePwifiMemberAuthorityEnabled)
                await _controller.BlazePwifi.SyncMembersAsync();
            RefreshMembers();
            MessageBox.Show(ok ? "BlazePwifi connection succeeded." : "BlazePwifi connection failed.", "SoftTimer");
        }));
        row.Controls.Add(Button("SYNC MEMBERS", async (_, _) =>
        {
            SaveApply();
            var snapshot = await _controller.BlazePwifi.SyncMembersAsync();
            RefreshMembers();
            MessageBox.Show(
                snapshot is null ? "Member synchronization failed." : $"Member synchronization completed · revision {snapshot.Revision}.",
                "SoftTimer");
        }));
        card.Controls.Add(row);
        card.Controls.Add(_pwifiStatus);
        root.Controls.Add(card);
        _pages["BlazePwifi"] = root;
    }

    private void BuildMembers()
    {
        var root = NewPage(
            "Members",
            "Standalone mode keeps local member accounts. With BlazePwifi member authority enabled, accounts are created and managed only in BlazePwifi Admin → Pisonet Members.");
        var card = Card(
            "Member account",
            "Local CREATE/UPDATE is available only when BlazePwifi member authority is disabled. Central mode shows the synchronized BlazePwifi cache here.");
        card.Controls.Add(_memberModeStatus);
        card.Controls.Add(Field("Username", _memberUser));
        _memberPass.UseSystemPasswordChar = true;
        card.Controls.Add(Field("Password", _memberPass));
        card.Controls.Add(PrimaryButton("CREATE / UPDATE LOCAL MEMBER", (_, _) =>
        {
            if (_controller.Config.BlazePwifiMemberAuthorityEnabled)
            {
                MessageBox.Show(
                    "Central member authority is enabled. Create/edit members in BlazePwifi Admin → Pisonet Members.",
                    "BlazePisonet SoftTimer",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information);
                return;
            }

            if (_controller.Timer.CreateOrUpdateMember(_memberUser.Text, _memberPass.Text))
            {
                _memberPass.Clear();
                RefreshMembers();
            }
            else MessageBox.Show("Use a 2-32 character username and a password of at least 4 characters.");
        }));

        var memberActions = new FlowLayoutPanel { AutoSize = true, Width = 880 };
        memberActions.Controls.Add(Button("BANK CURRENT PAID TIME", async (_, _) =>
        {
            var ok = await _controller.BankTimeToMemberAsync(_memberUser.Text.Trim(), _memberPass.Text);
            _memberPass.Clear();
            RefreshMembers();
            RefreshStatus();
            MessageBox.Show(
                ok ? "Remaining paid time was banked to the member account." :
                    (_controller.Config.BlazePwifiMemberAuthorityEnabled
                        ? "Bank failed. BlazePwifi must confirm the member and balance mutation; local paid time was preserved."
                        : "Could not bank time. Check the member username/password and make sure paid time is active."),
                "BlazePisonet SoftTimer",
                MessageBoxButtons.OK,
                ok ? MessageBoxIcon.Information : MessageBoxIcon.Warning);
        }));
        memberActions.Controls.Add(Button("REFRESH CENTRAL CACHE", async (_, _) =>
        {
            if (!_controller.Config.BlazePwifiMemberAuthorityEnabled)
            {
                RefreshMembers();
                return;
            }
            await _controller.BlazePwifi.SyncMembersAsync();
            RefreshMembers();
        }));
        card.Controls.Add(memberActions);
        card.Controls.Add(_memberList);
        root.Controls.Add(card);

        var transfer = Card("Transfer member time", "Standalone mode can transfer locally. Central mode must be managed in BlazePwifi Admin so one server owns the authoritative balance ledger.");
        transfer.Controls.Add(Field("From member", _memberTransferFrom));
        _memberTransferPass.UseSystemPasswordChar = true;
        transfer.Controls.Add(Field("From member password", _memberTransferPass));
        transfer.Controls.Add(Field("To member", _memberTransferTo));
        transfer.Controls.Add(Field("Minutes to transfer", _memberTransferMinutes));
        transfer.Controls.Add(PrimaryButton("TRANSFER TIME", (_, _) =>
        {
            if (_controller.Config.BlazePwifiMemberAuthorityEnabled)
            {
                MessageBox.Show(
                    "Transfer centralized member time in BlazePwifi Admin → Pisonet Members.",
                    "BlazePisonet SoftTimer",
                    MessageBoxButtons.OK,
                    MessageBoxIcon.Information);
                return;
            }

            var seconds = (long)_memberTransferMinutes.Value * 60L;
            var ok = _controller.Timer.TransferMemberTime(
                _memberTransferFrom.Text.Trim(),
                _memberTransferPass.Text,
                _memberTransferTo.Text.Trim(),
                seconds);
            _memberTransferPass.Clear();
            if (ok)
            {
                RefreshMembers();
                MessageBox.Show("Member time transferred.");
            }
            else MessageBox.Show("Transfer failed. Check both accounts, password and available banked time.");
        }));
        root.Controls.Add(transfer);
        _pages["Members"] = root;
    }

    private void BuildSchedules()
    {
        var root = NewPage("Schedules", "Three ASApp-style shop schedules with overnight support, customer lock windows and optional shutdown policy.");
        var card = Card("Scheduled policies", "A schedule can show a message, force the customer lock screen, offer a controlled shutdown, or combine those actions.");
        _scheduleList.Width = 850;
        card.Controls.Add(_scheduleList);
        card.Controls.Add(PrimaryButton("EDIT 3 SCHEDULE WINDOWS", (_, _) => EditSchedules()));
        root.Controls.Add(card);
        _pages["Schedules"] = root;
    }

    private void BuildSecurity()
    {
        var root = NewPage("Security", "Kiosk restrictions apply only while the customer lock screen is active. Ctrl+Alt+Delete remains Windows-controlled; after returning, Home opens the timed administrator login path.");
        var card = Card("Windows protection", "These replace ASApp's brittle all-in-one protection with explicit reversible policies plus the lock-screen keyboard hook.");
        card.Controls.AddRange([_blockTaskMgr, _blockRegedit, _disableLogoff, _disablePower, _blockWinKeys, _lockMouse, _watchdog]);
        card.Controls.Add(_idleShutdown);
        card.Controls.Add(Field("Idle shutdown minutes", _idleMinutes));
        card.Controls.Add(_unusual);
        card.Controls.Add(Field("Blocked process names · one per line", _blockedProcesses));
        card.Controls.Add(Field("Blocked websites · one per line", _blockedWebsites));
        var pass = PrimaryButton("SET ADMIN PASSWORD", (_, _) => SetAdminPassword());
        card.Controls.Add(pass);
        root.Controls.Add(card);
        _pages["Security"] = root;
    }

    private void BuildAppearance()
    {
        var root = NewPage("Appearance", "Blaze dark navy/cyan/violet theme with a simple customer-facing lock screen.");
        var card = Card("Branding", "Wallpaper is optional; the lock screen stays readable without one.");
        card.Controls.Add(Field("Shop name", _shop));
        card.Controls.Add(Field("PC / station name", _pc));
        card.Controls.Add(Field("Primary lock message", _banner1));
        card.Controls.Add(Field("Secondary message", _banner2));
        card.Controls.Add(Field("Wallpaper path", _wallpaper));
        card.Controls.Add(Button("BROWSE WALLPAPER", (_, _) =>
        {
            using var dialog = new OpenFileDialog { Filter = "Images|*.jpg;*.jpeg;*.png;*.gif|All files|*.*" };
            if (dialog.ShowDialog() == DialogResult.OK) _wallpaper.Text = dialog.FileName;
        }));
        root.Controls.Add(card);
        _pages["Appearance"] = root;
    }

    private void BuildDiagnostics()
    {
        var root = NewPage("Diagnostics", "Live status and local audit log. SoftTimer never requires renaming a port to COM1.");
        var card = Card("Runtime", "Use this page when installing USB-RS232 adapters or testing integration.");
        _log.ReadOnly = true;
        _log.Height = 420;
        card.Controls.Add(_log);
        var row = new FlowLayoutPanel { AutoSize = true, Width = 880 };
        row.Controls.Add(Button("REFRESH LOG", (_, _) => LoadLog()));
        row.Controls.Add(Button("OPEN DATA FOLDER", (_, _) => Process.Start(new ProcessStartInfo("explorer.exe", Storage.RootDirectory) { UseShellExecute = true })));
        row.Controls.Add(Button("RESTORE WINDOWS POLICIES", (_, _) => { _controller.EnterAdminMaintenance(); MessageBox.Show("SoftTimer lock-screen policies are released while administrator maintenance is active."); }));
        card.Controls.Add(row);
        root.Controls.Add(card);
        _pages["Diagnostics"] = root;
    }

    private void ShowPage(string name)
    {
        _content.SuspendLayout();
        _content.Controls.Clear();
        if (_pages.TryGetValue(name, out var page)) _content.Controls.Add(page);
        foreach (var p in _nav) p.Value.BackColor = p.Key.Equals(name, StringComparison.OrdinalIgnoreCase) ? BlazeTheme.Panel : BlazeTheme.Panel2;
        _content.ResumeLayout();
        if (name == "Diagnostics") LoadLog();
        RefreshStatus();
    }

    private void LoadConfigToUi()
    {
        var c = _controller.Config;
        _enabled.Checked = c.Enabled;
        FillEnum(_timerSource, c.TimerSource);
        FillEnum(_topology, c.CoinTopology);
        FillEnum(_serialMode, c.SerialSelection);
        FillEnum(_coinSignal, c.CoinInputSignal);
        FillEnum(_timerSignal, c.TimerActiveSignal);
        _secondsPerCoin.Value = Clamp(_secondsPerCoin, c.SecondsPerCoin);
        _warningSeconds.Value = Clamp(_warningSeconds, c.WarningSeconds);
        _warningSoundEnabled.Checked = c.WarningSoundEnabled;
        _warningSoundPath.Text = c.WarningSoundPath;
        _showActiveOverlay.Checked = c.ShowActiveTimerOverlay;
        _allowMemberBankOverlay.Checked = c.AllowMemberBankFromOverlay;
        _coinHigh.Checked = c.CoinInputActiveHigh;
        _timerHigh.Checked = c.TimerActiveHigh;
        _debounce.Value = Clamp(_debounce, c.DebounceMs);
        _minPulse.Value = Clamp(_minPulse, c.MinimumPulseMs);
        _maxPulse.Value = Clamp(_maxPulse, c.MaximumPulseMs);
        _dtr.Checked = c.DtrEnabled;
        _rts.Checked = c.RtsEnabled;
        _blazeAddress.Text = c.BlazeTimerAddress;
        _stationId.Text = c.CentralStationId;
        _coordinatorUrl.Text = c.CentralCoordinatorUrl;
        _sharedKey.Text = c.CentralSharedKey;
        _listenPort.Value = Clamp(_listenPort, c.CentralListenPort);
        _coinWindow.Value = Clamp(_coinWindow, c.CentralCoinWindowSeconds);
        _pwifiEnabled.Checked = c.BlazePwifiEnabled;
        _pwifiMirror.Checked = c.MirrorLocalCoinsToBlazePwifi;
        _pwifiMembers.Checked = c.BlazePwifiMemberAuthorityEnabled;
        _pwifiMemberSync.Value = Clamp(_pwifiMemberSync, c.BlazePwifiMemberSyncSeconds);
        _pwifiUrl.Text = c.BlazePwifiVendoUrl;
        _pwifiId.Text = c.BlazePwifiControllerId;
        _pwifiKey.Text = c.BlazePwifiVendoKey;
        _blockTaskMgr.Checked = c.BlockTaskManager;
        _blockRegedit.Checked = c.BlockRegistryTools;
        _disableLogoff.Checked = c.DisableLogoff;
        _disablePower.Checked = c.DisablePowerOptions;
        _blockWinKeys.Checked = c.BlockWindowsKeys;
        _lockMouse.Checked = c.LockMouseToScreen;
        _watchdog.Checked = c.RunWatchdog;
        _idleShutdown.Checked = c.IdleShutdownEnabled;
        _idleMinutes.Value = Clamp(_idleMinutes, c.IdleShutdownMinutes);
        _unusual.Checked = c.UnusualInputShutdownEnabled;
        _blockedProcesses.Text = string.Join(Environment.NewLine, c.BlockedProcesses);
        _blockedWebsites.Text = string.Join(Environment.NewLine, c.BlockedWebsites);
        _shop.Text = c.ShopName;
        _pc.Text = c.PcName;
        _banner1.Text = c.Banner1;
        _banner2.Text = c.Banner2;
        _wallpaper.Text = c.WallpaperPath ?? string.Empty;
        _schedules = CloneSchedules(c.NotificationSchedules);
        RefreshSchedules();
        RefreshStatus();
    }

    private AppConfig ReadUiIntoConfig(bool validate)
    {
        var c = _controller.Config;
        c.Enabled = _enabled.Checked;
        c.TimerSource = SelectedEnum(_timerSource, c.TimerSource);
        c.CoinTopology = SelectedEnum(_topology, c.CoinTopology);
        c.SerialSelection = SelectedEnum(_serialMode, c.SerialSelection);
        c.CoinInputSignal = SelectedEnum(_coinSignal, c.CoinInputSignal);
        c.TimerActiveSignal = SelectedEnum(_timerSignal, c.TimerActiveSignal);
        c.SecondsPerCoin = (int)_secondsPerCoin.Value;
        c.WarningSeconds = (int)_warningSeconds.Value;
        c.WarningSoundEnabled = _warningSoundEnabled.Checked;
        c.WarningSoundPath = _warningSoundPath.Text.Trim();
        c.ShowActiveTimerOverlay = _showActiveOverlay.Checked;
        c.AllowMemberBankFromOverlay = _allowMemberBankOverlay.Checked;
        c.CoinInputActiveHigh = _coinHigh.Checked;
        c.TimerActiveHigh = _timerHigh.Checked;
        c.DebounceMs = (int)_debounce.Value;
        c.MinimumPulseMs = (int)_minPulse.Value;
        c.MaximumPulseMs = (int)_maxPulse.Value;
        c.DtrEnabled = _dtr.Checked;
        c.RtsEnabled = _rts.Checked;
        if (_serialDevices.SelectedItem is SerialDeviceItem item)
        {
            c.ManualComPort = item.Device.PortName;
            c.LastKnownComPort = item.Device.PortName;
        }
        c.BlazeTimerAddress = _blazeAddress.Text.Trim();
        c.CentralStationId = Storage.NormalizeId(_stationId.Text);
        c.CentralCoordinatorUrl = _coordinatorUrl.Text.Trim();
        c.CentralSharedKey = _sharedKey.Text.Trim();
        c.CentralListenPort = (int)_listenPort.Value;
        c.CentralCoinWindowSeconds = (int)_coinWindow.Value;
        c.BlazePwifiEnabled = _pwifiEnabled.Checked;
        c.MirrorLocalCoinsToBlazePwifi = _pwifiMirror.Checked;
        c.BlazePwifiMemberAuthorityEnabled = _pwifiMembers.Checked;
        c.BlazePwifiMemberSyncSeconds = (int)_pwifiMemberSync.Value;
        c.BlazePwifiVendoUrl = _pwifiUrl.Text.Trim();
        c.BlazePwifiControllerId = Storage.NormalizeId(_pwifiId.Text);
        c.BlazePwifiVendoKey = _pwifiKey.Text.Trim();
        c.BlockTaskManager = _blockTaskMgr.Checked;
        c.BlockRegistryTools = _blockRegedit.Checked;
        c.DisableLogoff = _disableLogoff.Checked;
        c.DisablePowerOptions = _disablePower.Checked;
        c.BlockWindowsKeys = _blockWinKeys.Checked;
        c.LockMouseToScreen = _lockMouse.Checked;
        c.RunWatchdog = _watchdog.Checked;
        c.IdleShutdownEnabled = _idleShutdown.Checked;
        c.IdleShutdownMinutes = (int)_idleMinutes.Value;
        c.UnusualInputShutdownEnabled = _unusual.Checked;
        c.BlockedProcesses = Lines(_blockedProcesses.Text);
        c.BlockedWebsites = Lines(_blockedWebsites.Text);
        c.ShopName = _shop.Text.Trim().Length > 0 ? _shop.Text.Trim() : "BlazePisonet";
        c.PcName = _pc.Text.Trim().Length > 0 ? _pc.Text.Trim() : Environment.MachineName;
        c.Banner1 = _banner1.Text.Trim();
        c.Banner2 = _banner2.Text.Trim();
        c.WallpaperPath = string.IsNullOrWhiteSpace(_wallpaper.Text) ? null : _wallpaper.Text.Trim();
        c.NotificationSchedules = CloneSchedules(_schedules);
        if (validate && c.Enabled && !c.HasAdminPassword) throw new InvalidOperationException("Set an administrator password before enabling SoftTimer.");
        if (validate && c.BlazePwifiMemberAuthorityEnabled)
        {
            if (!c.BlazePwifiEnabled)
                throw new InvalidOperationException("Enable BlazePwifi integration before enabling central member authority.");
            if (string.IsNullOrWhiteSpace(c.BlazePwifiVendoUrl) || string.IsNullOrWhiteSpace(c.BlazePwifiVendoKey))
                throw new InvalidOperationException("Central member authority requires the BlazePwifi Vendo endpoint and Vendo key.");
        }
        if (validate && c.CoinTopology != CoinTopologyMode.StandardOneToOne && c.CentralSharedKey.Length < 16) throw new InvalidOperationException("Centralized mode requires a shared key of at least 16 characters.");
        return c;
    }

    private void SaveApply()
    {
        try
        {
            var config = ReadUiIntoConfig(true);
            _controller.ApplyConfig(config);
            RefreshStatus();
            MessageBox.Show("Configuration saved and applied.", "BlazePisonet SoftTimer", MessageBoxButtons.OK, MessageBoxIcon.Information);
        }
        catch (Exception ex) { MessageBox.Show(ex.Message, "Cannot save", MessageBoxButtons.OK, MessageBoxIcon.Warning); }
    }

    private void RefreshSerialDevices()
    {
        var existing = _controller.Config.LastKnownComPort;
        _serialDevices.Items.Clear();
        foreach (var d in SerialDiscovery.Enumerate()) _serialDevices.Items.Add(new SerialDeviceItem(d));
        if (_serialDevices.Items.Count > 0)
        {
            var index = Enumerable.Range(0, _serialDevices.Items.Count).FirstOrDefault(i => ((SerialDeviceItem)_serialDevices.Items[i]!).Device.PortName.Equals(existing, StringComparison.OrdinalIgnoreCase));
            _serialDevices.SelectedIndex = index;
        }
        _serialStatus.Text = _serialDevices.Items.Count == 0 ? "No COM ports detected." : $"{_serialDevices.Items.Count} COM device(s) found in Windows.";
    }

    private void BindExactDevice()
    {
        if (_serialDevices.SelectedItem is not SerialDeviceItem item) { MessageBox.Show("Select a serial device first."); return; }
        SerialDiscovery.BindExactDevice(_controller.Config, item.Device);
        _serialMode.SelectedItem = SerialSelectionMode.ExactDevice;
        _serialStatus.Text = $"Bound to {item.Device.Display}\nPnP: {item.Device.PnpDeviceId}\nVID/PID: {item.Device.Vid}/{item.Device.Pid}";
    }

    private async Task DiscoverTimers()
    {
        _blazeDevices.Items.Clear();
        _blazeDevices.Items.Add("Scanning local IPv4 networks…");
        var devices = await _controller.DiscoverBlazeTimersAsync();
        _blazeDevices.Items.Clear();
        foreach (var d in devices) _blazeDevices.Items.Add(new BlazeTimerItem(d));
        if (devices.Count == 0) _blazeDevices.Items.Add("No Blaze Pisonet Timer found. Manual IP remains available.");
    }

    private void PairSelectedTimer()
    {
        if (_blazeDevices.SelectedItem is not BlazeTimerItem item) return;
        _blazeAddress.Text = item.Device.Address;
        _controller.Config.BlazeTimerAddress = item.Device.Address;
        _controller.Config.BlazeTimerMac = item.Device.MacAddress;
        _controller.Config.BlazeTimerName = item.Device.Name;
        _timerSource.SelectedItem = TimerSourceMode.BlazePisonetTimer;
        MessageBox.Show($"Paired with {item.Device.Name}. Save & Apply to activate the wireless timer bridge.");
    }

    private void SetAdminPassword()
    {
        using var dialog = new PasswordSetupForm();
        if (dialog.ShowDialog() != DialogResult.OK) return;
        _controller.SetAdminPassword(dialog.Password);
        MessageBox.Show("Administrator password saved. There is no universal/default admin password.");
    }

    private void EditSchedules()
    {
        using var dialog = new ScheduleEditorForm(_schedules);
        if (dialog.ShowDialog(this) != DialogResult.OK) return;
        _schedules = CloneSchedules(dialog.Schedules);
        RefreshSchedules();
    }

    private void RefreshSchedules()
    {
        _scheduleList.Items.Clear();
        for (var i = 0; i < _schedules.Count; i++)
        {
            var s = _schedules[i];
            var days = s.Days.Count == 7 ? "Every day" : string.Join(",", s.Days.OrderBy(d => (int)d).Select(d => d.ToString()[..3]));
            var actions = string.Join(" + ", new[]
            {
                s.LockDuringWindow ? "LOCK" : null,
                s.ShutdownDuringWindow ? "SHUTDOWN" : null
            }.Where(x => x is not null));
            if (actions.Length == 0) actions = "MESSAGE";
            _scheduleList.Items.Add($"{(s.Enabled ? "●" : "○")} {s.Name} · {s.Start:hh\\:mm}-{s.End:hh\\:mm} · {days} · {actions}");
        }
    }

    private static List<NotificationSchedule> CloneSchedules(IEnumerable<NotificationSchedule> schedules)
    {
        var list = schedules.Take(3).Select(s => new NotificationSchedule
        {
            Enabled = s.Enabled,
            Name = s.Name,
            Start = s.Start,
            End = s.End,
            LockDuringWindow = s.LockDuringWindow,
            ShutdownDuringWindow = s.ShutdownDuringWindow,
            Message = s.Message,
            Days = new HashSet<DayOfWeek>(s.Days)
        }).ToList();
        while (list.Count < 3) list.Add(new NotificationSchedule { Name = $"Schedule {list.Count + 1}" });
        return list;
    }

    private void RefreshMembers()
    {
        _memberList.Items.Clear();

        if (_controller.Config.BlazePwifiMemberAuthorityEnabled)
        {
            _memberModeStatus.Text =
                $"CENTRAL · BlazePwifi authoritative · cache revision {_controller.Timer.RemoteMemberRevision} · account edits belong in BlazePwifi Admin";
            _memberModeStatus.ForeColor = BlazeTheme.Accent2;

            foreach (var m in _controller.Timer.RemoteMembersSnapshot())
            {
                var state = m.Enabled ? "ENABLED" : "DISABLED";
                var label = string.IsNullOrWhiteSpace(m.Label) ? string.Empty : $" · {m.Label}";
                _memberList.Items.Add($"{m.Username,-24}  {BlazeTheme.FormatTime(m.BankedSeconds)} banked · {state}{label}");
            }

            if (_memberList.Items.Count == 0)
                _memberList.Items.Add("No central members cached yet. Use SYNC MEMBERS on the BlazePwifi page.");
            return;
        }

        _memberModeStatus.Text = "LOCAL · this PC owns standalone member accounts";
        _memberModeStatus.ForeColor = BlazeTheme.Muted;
        foreach (var m in _controller.Timer.MembersSnapshot())
            _memberList.Items.Add($"{m.Username,-24}  {BlazeTheme.FormatTime(m.BankedSeconds)} banked");
    }

    private void RefreshStatus()
    {
        _mTime.Text = BlazeTheme.FormatTime(_controller.Timer.RemainingSeconds);
        _mHardware.Text = _controller.Serial.IsConnected ? _controller.Serial.ConnectedDevice?.PortName ?? "ONLINE" : (_controller.Config.TimerSource == TimerSourceMode.BlazePisonetTimer ? "WIRELESS" : "OFFLINE");
        _mHardware.ForeColor = _controller.Serial.IsConnected || _controller.Config.TimerSource == TimerSourceMode.BlazePisonetTimer ? BlazeTheme.Good : BlazeTheme.Warn;
        _mIntegration.Text = _controller.Config.BlazePwifiEnabled ? "BLAZEPWIFI" : _controller.Config.CoinTopology.ToString().Replace("StandardOneToOne", "STANDARD").Replace("Centralized", "CENTRAL ").ToUpperInvariant();
        _mSales.Text = _controller.Timer.SalesPulseCount.ToString();
        _serialStatus.Text = _controller.HardwareStatus;
        _pwifiStatus.Text = _controller.IntegrationStatus;
    }

    private void LoadLog()
    {
        try
        {
            if (!File.Exists(Storage.LogPath)) { _log.Text = "No log entries yet."; return; }
            var lines = File.ReadLines(Storage.LogPath).TakeLast(500);
            _log.Text = string.Join(Environment.NewLine, lines);
            _log.SelectionStart = _log.TextLength;
            _log.ScrollToCaret();
        }
        catch (Exception ex) { _log.Text = ex.Message; }
    }

    private void OnFormClosing(object? sender, FormClosingEventArgs e)
    {
        if (_allowExit) return;
        if (_controller.Config.Enabled)
        {
            e.Cancel = true;
            Hide();
            _controller.ExitAdminMaintenance();
        }
    }

    private void ExitApplication()
    {
        if (MessageBox.Show("Exit BlazePisonet SoftTimer completely? Paid-time state is preserved.", "Exit", MessageBoxButtons.YesNo, MessageBoxIcon.Warning) != DialogResult.Yes) return;
        _allowExit = true;
        try { Storage.AtomicWrite(Storage.MaintenancePath, DateTimeOffset.UtcNow.AddMinutes(10).ToUnixTimeSeconds().ToString()); } catch { }
        Application.Exit();
    }

    private void SafeUi(Action action)
    {
        if (IsDisposed) return;
        try { if (InvokeRequired) BeginInvoke(action); else action(); } catch { }
    }

    private static Label MetricLabel() => new() { Text = "—", Font = new Font("Segoe UI Semibold", 17, FontStyle.Bold), ForeColor = BlazeTheme.Text, AutoSize = true };

    private static Panel MetricCard(string title, Label value)
    {
        var p = new Panel { Dock = DockStyle.Fill, BackColor = BlazeTheme.Panel, Margin = new Padding(5), Padding = new Padding(14) };
        p.Controls.Add(value); value.Location = new Point(14, 48);
        p.Controls.Add(new Label { Text = title, ForeColor = BlazeTheme.Muted, AutoSize = true, Location = new Point(14, 16) });
        return p;
    }

    private static FlowLayoutPanel Card(string title, string subtitle)
    {
        var c = new FlowLayoutPanel { FlowDirection = FlowDirection.TopDown, WrapContents = false, AutoSize = true, AutoSizeMode = AutoSizeMode.GrowAndShrink, Width = 930, Padding = new Padding(16), Margin = new Padding(0, 0, 0, 14), BackColor = BlazeTheme.Panel };
        c.Controls.Add(new Label { Text = title, Font = new Font("Segoe UI Semibold", 13, FontStyle.Bold), AutoSize = true, ForeColor = BlazeTheme.Text });
        c.Controls.Add(new Label { Text = subtitle, AutoSize = true, MaximumSize = new Size(860, 0), ForeColor = BlazeTheme.Muted, Margin = new Padding(0, 2, 0, 12) });
        return c;
    }

    private static Panel Field(string label, Control control)
    {
        var p = new Panel { Width = 870, Height = control is TextBox tb && tb.Multiline ? 150 : 68, Margin = new Padding(0, 3, 0, 3) };
        p.Controls.Add(new Label { Text = label, AutoSize = true, ForeColor = BlazeTheme.Muted, Location = new Point(0, 0) });
        control.Location = new Point(0, 24); control.Width = 850;
        if (control is TextBox mt && mt.Multiline) control.Height = 110;
        p.Controls.Add(control);
        return p;
    }

    private static Button Button(string text, EventHandler click)
    {
        var b = new Button { Text = text, AutoSize = true, Height = 38, BackColor = BlazeTheme.Panel2, ForeColor = BlazeTheme.Text, FlatStyle = FlatStyle.Flat, Margin = new Padding(0, 5, 8, 5) };
        b.FlatAppearance.BorderColor = BlazeTheme.Line; b.Click += click; return b;
    }

    private static Button PrimaryButton(string text, EventHandler click)
    {
        var b = Button(text, click); b.BackColor = BlazeTheme.Accent; b.FlatAppearance.BorderSize = 0; b.Font = new Font("Segoe UI Semibold", 9.5f, FontStyle.Bold); return b;
    }

    private static ComboBox NewCombo() => new() { DropDownStyle = ComboBoxStyle.DropDownList, Height = 32 };
    private static TextBox NewText() => new() { Height = 32 };
    private static TextBox NewMultiText() => new() { Multiline = true, ScrollBars = ScrollBars.Vertical, Height = 110 };
    private static NumericUpDown NewNumber(decimal min, decimal max, decimal value) => new() { Minimum = min, Maximum = max, Value = value, ThousandsSeparator = true, Height = 32 };
    private static decimal Clamp(NumericUpDown n, decimal value) => Math.Min(n.Maximum, Math.Max(n.Minimum, value));
    private static List<string> Lines(string text) => text.Split(new[] { '\r', '\n', ',', ';' }, StringSplitOptions.RemoveEmptyEntries | StringSplitOptions.TrimEntries).Distinct(StringComparer.OrdinalIgnoreCase).ToList();

    private static void FillEnum<T>(ComboBox box, T selected) where T : struct, Enum
    {
        box.Items.Clear(); foreach (var v in Enum.GetValues<T>()) box.Items.Add(v); box.SelectedItem = selected;
    }
    private static T SelectedEnum<T>(ComboBox box, T fallback) where T : struct, Enum => box.SelectedItem is T value ? value : fallback;

    private sealed record SerialDeviceItem(SerialDeviceInfo Device) { public override string ToString() => $"{Device.Display}  [{Device.Vid}:{Device.Pid}]"; }
    private sealed record BlazeTimerItem(BlazeTimerDevice Device) { public override string ToString() => $"{Device.Name} · {new Uri(Device.Address).Host} · {Device.MacAddress} · {BlazeTheme.FormatTime(Device.RemainingSeconds)}"; }
}

public sealed class PasswordSetupForm : Form
{
    private readonly TextBox _p1 = new() { UseSystemPasswordChar = true };
    private readonly TextBox _p2 = new() { UseSystemPasswordChar = true };
    private readonly Label _msg = new() { AutoSize = true, ForeColor = BlazeTheme.Bad };
    public string Password => _p1.Text;

    public PasswordSetupForm()
    {
        Text = "Set SoftTimer Admin Password";
        Size = new Size(430, 280);
        StartPosition = FormStartPosition.CenterParent;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = MinimizeBox = false;
        BackColor = BlazeTheme.Background;
        ForeColor = BlazeTheme.Text;
        Controls.Add(new Label { Text = "Administrator password", Font = new Font("Segoe UI Semibold", 15, FontStyle.Bold), AutoSize = true, Location = new Point(24, 20) });
        Controls.Add(new Label { Text = "At least 8 characters. No default/master password is built in.", AutoSize = true, ForeColor = BlazeTheme.Muted, Location = new Point(24, 52) });
        Controls.Add(new Label { Text = "Password", AutoSize = true, Location = new Point(24, 88) }); _p1.SetBounds(24, 110, 360, 30); Controls.Add(_p1);
        Controls.Add(new Label { Text = "Confirm", AutoSize = true, Location = new Point(24, 146) }); _p2.SetBounds(24, 168, 360, 30); Controls.Add(_p2);
        var save = new Button { Text = "SAVE PASSWORD", BackColor = BlazeTheme.Accent, ForeColor = Color.White, FlatStyle = FlatStyle.Flat, Location = new Point(24, 208), Size = new Size(160, 36) };
        save.Click += (_, _) =>
        {
            if (_p1.Text.Length < 8) { _msg.Text = "Use at least 8 characters."; return; }
            if (_p1.Text != _p2.Text) { _msg.Text = "Passwords do not match."; return; }
            DialogResult = DialogResult.OK; Close();
        };
        _msg.Location = new Point(195, 218); Controls.Add(save); Controls.Add(_msg);
    }
}
