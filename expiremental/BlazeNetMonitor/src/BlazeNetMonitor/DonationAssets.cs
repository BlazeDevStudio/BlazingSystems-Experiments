using System.Drawing.Drawing2D;
using System.Diagnostics;
using BlazeNetMonitor.Core;

namespace BlazeNetMonitor;

/// <summary>
/// Immutable QR destination decoded from the creator's uploaded PayPal image.
/// Reconstructed QR matrix with error correction H for crisp, scalable rendering.
/// No importing, per-user QR overrides, web service or payment credentials.
/// </summary>
internal static class DonationAssets
{
    public static string PayPalUrl => DonationSplashPolicy.OwnerPayPalUrl;

    public static Bitmap CreateQrBitmap(int size)
    {
        // Render at the caller's exact pixel dimensions. A previous 200px
        // lower bound silently created a 200x200 image in a 154x154
        // PictureBox (Normal mode), clipping the right and bottom QR modules.
        size = Math.Clamp(size, 96, 900);
        var bitmap = new Bitmap(size, size);
        using var g = Graphics.FromImage(bitmap);
        g.Clear(Color.White);
        g.SmoothingMode = SmoothingMode.AntiAlias;

        const int count = DonationSplashPolicy.QrModules;
        float margin = size * 0.078f;
        float pitch = (size - 2f * margin) / count;
        var matrix = DonationSplashPolicy.ModuleMatrix();
        using var black = new SolidBrush(Color.Black);
        using var blue = new SolidBrush(Color.FromArgb(0, 99, 240));
        for (int y = 0; y < count; y++)
            for (int x = 0; x < count; x++)
            {
                if (!matrix[y, x]) continue;
                float cx = margin + (x + 0.5f) * pitch;
                float cy = margin + (y + 0.5f) * pitch;
                float r = pitch * 0.44f;
                g.FillEllipse(black, cx - r, cy - r, 2 * r, 2 * r);
            }

        // Recreate the three blue-centered finder marks present in the owner's
        // uploaded QR. The URL and QR bitstream remain the owner's, not a new account.
        DrawFinder(g, margin, margin, pitch, blue, black);
        DrawFinder(g, margin + (count - 7) * pitch, margin, pitch, blue, black);
        DrawFinder(g, margin, margin + (count - 7) * pitch, pitch, blue, black);

        var center = size / 2f;
        var logoRadius = size * 0.078f;
        g.FillEllipse(Brushes.White, center - logoRadius, center - logoRadius,
            logoRadius * 2, logoRadius * 2);
        using var font = new Font("Segoe UI Black", size * 0.119f, FontStyle.Bold, GraphicsUnit.Pixel);
        using var format = new StringFormat { Alignment = StringAlignment.Center,
            LineAlignment = StringAlignment.Center };
        g.DrawString("P", font, Brushes.DarkBlue,
            new RectangleF(center - logoRadius, center - logoRadius,
                2 * logoRadius, 2 * logoRadius), format);
        return bitmap;
    }

    private static void DrawFinder(Graphics g, float x, float y, float step,
        Brush blue, Brush black)
    {
        g.FillRectangle(black, x, y, step * 7, step * 7);
        g.FillRectangle(Brushes.White, x + step, y + step, step * 5, step * 5);
        g.FillRectangle(blue, x + step * 2, y + step * 2, step * 3, step * 3);
    }

    public static bool OpenPayPal(IWin32Window? owner = null)
    {
        try
        {
            Process.Start(new ProcessStartInfo(PayPalUrl) { UseShellExecute = true });
            return true;
        }
        catch (Exception e)
        {
            MessageBox.Show(owner, "Could not open PayPal in your browser: " + e.Message,
                "BlazeNetMonitor", MessageBoxButtons.OK, MessageBoxIcon.Information);
            return false;
        }
    }
}
