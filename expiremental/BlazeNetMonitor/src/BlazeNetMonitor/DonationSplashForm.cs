using BlazeNetMonitor.Core;

namespace BlazeNetMonitor;

/// <summary>
/// Nonblocking centered QR splash. Self-dismisses after a short timer. Dismissal
/// never touches traffic counters, probes, settings, or user focus after closing.
/// </summary>
internal sealed class DonationSplashForm : Form
{
    private readonly System.Windows.Forms.Timer _timer = new() { Interval = 70 };
    private readonly CheckBox _dontShow;
    private readonly Action _disable;
    private readonly PictureBox _qr;
    private long _startMs;
    private const int DisplayMs = 7000;

    public DonationSplashForm(Action disable)
    {
        _disable = disable;
        Text = "Support BlazeNetMonitor";
        Font = new Font("Segoe UI", 9.5f);
        BackColor = Theme.HighContrast ? SystemColors.Window : Theme.Panel;
        ForeColor = Theme.HighContrast ? SystemColors.WindowText : Theme.Text;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        ShowInTaskbar = false;
        StartPosition = FormStartPosition.CenterScreen;
        MaximizeBox = false;
        MinimizeBox = false;
        TopMost = true;
        ClientSize = new Size(490, 596);
        Icon = Branding.MakeIcon();
        KeyPreview = true;
        KeyDown += (_, e) => { if (e.KeyCode == Keys.Escape) Close(); };
        Controls.Add(new Label {
            Text = "SUPPORT BLAZENETMONITOR", Left = 22, Top = 16, Width = 446, Height = 35,
            TextAlign = ContentAlignment.MiddleCenter,
            Font = new Font("Segoe UI Semibold", 14.5f, FontStyle.Bold)
        });
        Controls.Add(new Label {
            Text = "Loumer Cabaluna Manreal", Left = 22, Top = 54, Width = 446, Height = 25,
            TextAlign = ContentAlignment.MiddleCenter,
            ForeColor = Theme.HighContrast ? SystemColors.WindowText : Theme.Muted
        });

        _qr = new PictureBox { Left = 69, Top = 93, Size = new Size(352, 352),
            SizeMode = PictureBoxSizeMode.Normal, Image = DonationAssets.CreateQrBitmap(352),
            BackColor = Color.White };
        Controls.Add(_qr);

        Controls.Add(new Label {
            Text = "Your support helps keep this free project improving.",
            Left = 25, Top = 462, Width = 440, Height = 24,
            TextAlign = ContentAlignment.MiddleCenter
        });
        Controls.Add(new Label {
            Text = "Any amount is deeply appreciated.",
            Left = 25, Top = 487, Width = 440, Height = 22,
            TextAlign = ContentAlignment.MiddleCenter,
            ForeColor = Theme.HighContrast ? SystemColors.WindowText : Theme.Muted
        });
        _dontShow = new CheckBox { Left = 29, Top = 531, Width = 166, Height = 27,
            Text = "Don't show on startup" };
        Controls.Add(_dontShow);
        var dismiss = new Button { Left = 215, Top = 527, Width = 105, Height = 35,
            Text = "Not now" };
        dismiss.Click += (_, _) => Close();
        var donate = new Button { Left = 332, Top = 527, Width = 130, Height = 35,
            Text = "Open PayPal" };
        donate.Click += (_, _) => { DonationAssets.OpenPayPal(this); Close(); };
        Controls.AddRange([dismiss, donate]);
        AcceptButton = donate;
        CancelButton = dismiss;
        _timer.Tick += (_, _) =>
        {
            long elapsed = Environment.TickCount64 - _startMs;
            if (elapsed < 230)
                Opacity = Math.Clamp(elapsed / 230d, 0.05, 1);
            else if (elapsed > DisplayMs - 360)
                Opacity = Math.Clamp((DisplayMs - elapsed) / 360d, 0.02, 1);
            if (elapsed >= DisplayMs) Close();
        };
        Shown += (_, _) =>
        {
            _startMs = Environment.TickCount64;
            Opacity = Theme.HighContrast ? 1 : 0.08;
            _timer.Start();
        };
        FormClosed += (_, _) =>
        {
            _timer.Stop();
            if (_dontShow.Checked) _disable();
        };
    }

    protected override void Dispose(bool disposing)
    {
        if (disposing)
        {
            _timer.Dispose();
            _qr.Image?.Dispose();
        }
        base.Dispose(disposing);
    }
}
