using System.Diagnostics;

namespace BlazeNetMonitor;

internal sealed class WelcomeForm : Form
{
    public WelcomeForm()
    {
        Text = "Welcome to BlazeNetMonitor";
        Font = new Font("Segoe UI", 9.3f);
        BackColor = Theme.Background;
        ForeColor = Theme.Text;
        FormBorderStyle = FormBorderStyle.FixedDialog;
        MaximizeBox = false;
        MinimizeBox = false;
        StartPosition = FormStartPosition.CenterScreen;
        ClientSize = new Size(525, 320);
        Icon = Branding.MakeIcon();

        var logo = new PictureBox { Left = 22, Top = 25, Width = 72, Height = 72,
            Image = Branding.Bitmap(72), SizeMode = PictureBoxSizeMode.Zoom };
        Controls.Add(logo);
        Controls.Add(new Label { Left = 110, Top = 28, Width = 380, Height = 34,
            Text = "BlazeNetMonitor", Font = new Font("Segoe UI Semibold", 19, FontStyle.Bold) });
        Controls.Add(new Label { Left = 112, Top = 69, Width = 383, Height = 36,
            Text = "Live network speed · Two independent health targets",
            ForeColor = Theme.Muted });
        Controls.Add(new Label { Left = 24, Top = 121, Width = 465, Height = 50,
            Text = "Customize the widget's placement, transparency, graphs, and target checks anytime from Settings." });
        var donation = DonationAssets.TryLoad();
        if (donation is not null)
        {
            var qr = new PictureBox { Left = 22, Top = 180, Width = 102, Height = 102,
                Image = donation, SizeMode = PictureBoxSizeMode.Zoom };
            Controls.Add(qr);
            Controls.Add(new Label { Left = 140, Top = 181, Width = 348, Height = 70,
                Text = "Enjoying this free project? Optional support through the creator's PayPal donation QR. Thanks for supporting Blaze Systems!" });
        }
        else
        {
            Controls.Add(new Label { Left = 24, Top = 179, Width = 456, Height = 55,
                Text = "Created by Blaze Systems. Support is optional; the creator's PayPal QR has not been configured.",
                ForeColor = Theme.Muted });
        }
        var start = new Button { Text = "Get started", Left = 348, Top = 273,
            Width = 152, Height = 34, DialogResult = DialogResult.OK };
        var later = new Button { Text = "Close", Left = 243, Top = 273,
            Width = 94, Height = 34, DialogResult = DialogResult.Cancel };
        Controls.AddRange([start, later]);
        AcceptButton = start;
        CancelButton = later;
    }
}
