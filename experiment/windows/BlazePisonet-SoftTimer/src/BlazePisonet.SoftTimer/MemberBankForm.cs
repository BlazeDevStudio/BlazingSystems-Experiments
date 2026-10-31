namespace BlazePisonet.SoftTimer;

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
