namespace BlazePisonet.SoftTimer;

public sealed class ScheduleEditorForm : Form
{
    private readonly List<ScheduleTab> _tabs = new();

    public List<NotificationSchedule> Schedules { get; private set; }

    public ScheduleEditorForm(IEnumerable<NotificationSchedule> schedules)
    {
        Schedules = schedules.Select(Clone).Take(3).ToList();
        while (Schedules.Count < 3)
            Schedules.Add(new NotificationSchedule { Name = $"Schedule {Schedules.Count + 1}" });

        Text = "BlazePisonet SoftTimer · Shop Schedules";
        Size = new Size(760, 620);
        MinimumSize = new Size(720, 580);
        StartPosition = FormStartPosition.CenterParent;
        BackColor = BlazeTheme.Background;
        ForeColor = BlazeTheme.Text;
        Font = new Font("Segoe UI", 9.5f);

        var header = new Label
        {
            Text = "Scheduled lock / closing policies",
            Font = new Font("Segoe UI Semibold", 18, FontStyle.Bold),
            AutoSize = true,
            Location = new Point(22, 18)
        };
        var help = new Label
        {
            Text = "Configure up to three ASApp-style schedule windows. Overnight windows such as 22:00 → 07:00 are supported.",
            ForeColor = BlazeTheme.Muted,
            AutoSize = true,
            MaximumSize = new Size(690, 0),
            Location = new Point(24, 52)
        };

        var tabControl = new TabControl
        {
            Location = new Point(22, 88),
            Size = new Size(700, 430)
        };

        for (var i = 0; i < 3; i++)
        {
            var tab = new ScheduleTab(Schedules[i], i + 1);
            _tabs.Add(tab);
            tabControl.TabPages.Add(tab.Page);
        }

        var save = new Button
        {
            Text = "SAVE SCHEDULES",
            Size = new Size(165, 40),
            Location = new Point(22, 532),
            BackColor = BlazeTheme.Accent,
            ForeColor = Color.White,
            FlatStyle = FlatStyle.Flat
        };
        save.FlatAppearance.BorderSize = 0;
        save.Click += (_, _) =>
        {
            Schedules = _tabs.Select(t => t.ToSchedule()).ToList();
            DialogResult = DialogResult.OK;
            Close();
        };

        var cancel = new Button
        {
            Text = "CANCEL",
            Size = new Size(110, 40),
            Location = new Point(198, 532),
            BackColor = BlazeTheme.Panel2,
            ForeColor = BlazeTheme.Text,
            FlatStyle = FlatStyle.Flat
        };
        cancel.Click += (_, _) => Close();

        Controls.AddRange([header, help, tabControl, save, cancel]);
    }

    private static NotificationSchedule Clone(NotificationSchedule s) => new()
    {
        Enabled = s.Enabled,
        Name = s.Name,
        Start = s.Start,
        End = s.End,
        LockDuringWindow = s.LockDuringWindow,
        ShutdownDuringWindow = s.ShutdownDuringWindow,
        Message = s.Message,
        Days = new HashSet<DayOfWeek>(s.Days)
    };

    private sealed class ScheduleTab
    {
        public TabPage Page { get; }
        private readonly CheckBox _enabled = new() { Text = "Enable this schedule" };
        private readonly TextBox _name = new();
        private readonly DateTimePicker _start = TimePicker();
        private readonly DateTimePicker _end = TimePicker();
        private readonly CheckBox _lock = new() { Text = "Lock customer access during this window" };
        private readonly CheckBox _shutdown = new() { Text = "Offer shutdown when this window begins" };
        private readonly TextBox _message = new();
        private readonly CheckedListBox _days = new() { CheckOnClick = true, Height = 120 };

        public ScheduleTab(NotificationSchedule schedule, int number)
        {
            Page = new TabPage($"Schedule {number}")
            {
                BackColor = BlazeTheme.Background,
                ForeColor = BlazeTheme.Text,
                Padding = new Padding(18)
            };

            _enabled.Checked = schedule.Enabled;
            _enabled.SetBounds(18, 18, 220, 28);

            AddLabel(Page, "Name", 18, 55);
            _name.Text = schedule.Name;
            _name.SetBounds(18, 78, 300, 30);

            AddLabel(Page, "Start", 18, 120);
            _start.SetBounds(18, 143, 140, 30);
            _start.Value = DateTime.Today + schedule.Start;

            AddLabel(Page, "End", 178, 120);
            _end.SetBounds(178, 143, 140, 30);
            _end.Value = DateTime.Today + schedule.End;

            _lock.Checked = schedule.LockDuringWindow;
            _lock.SetBounds(18, 190, 330, 28);

            _shutdown.Checked = schedule.ShutdownDuringWindow;
            _shutdown.SetBounds(18, 220, 330, 28);

            AddLabel(Page, "Message shown to the station", 18, 258);
            _message.Text = schedule.Message;
            _message.SetBounds(18, 281, 620, 30);

            AddLabel(Page, "Days", 390, 55);
            _days.SetBounds(390, 78, 248, 165);
            foreach (var d in Enum.GetValues<DayOfWeek>())
            {
                var index = _days.Items.Add(d);
                _days.SetItemChecked(index, schedule.Days.Contains(d));
            }

            Page.Controls.AddRange([_enabled, _name, _start, _end, _lock, _shutdown, _message, _days]);
        }

        public NotificationSchedule ToSchedule()
        {
            var days = new HashSet<DayOfWeek>();
            foreach (var item in _days.CheckedItems)
                if (item is DayOfWeek day) days.Add(day);

            return new NotificationSchedule
            {
                Enabled = _enabled.Checked,
                Name = string.IsNullOrWhiteSpace(_name.Text) ? "Schedule" : _name.Text.Trim(),
                Start = _start.Value.TimeOfDay,
                End = _end.Value.TimeOfDay,
                LockDuringWindow = _lock.Checked,
                ShutdownDuringWindow = _shutdown.Checked,
                Message = _message.Text.Trim(),
                Days = days
            };
        }

        private static DateTimePicker TimePicker() => new()
        {
            Format = DateTimePickerFormat.Custom,
            CustomFormat = "HH:mm",
            ShowUpDown = true
        };

        private static void AddLabel(Control parent, string text, int x, int y)
        {
            parent.Controls.Add(new Label
            {
                Text = text,
                AutoSize = true,
                ForeColor = BlazeTheme.Muted,
                Location = new Point(x, y)
            });
        }
    }
}
