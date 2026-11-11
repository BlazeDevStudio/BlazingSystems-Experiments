using System.Drawing.Drawing2D;
using System.Runtime.InteropServices;

namespace BlazeNetMonitor;

/// <summary>Small vector-style Blaze Systems blue monitor mark, rendered by GDI+ at runtime.
/// Avoids large UI graphics dependencies and follows the system dark/light background.</summary>
internal static class Branding
{
    public static readonly Color BlazeBlue = Color.FromArgb(0, 102, 255);
    public static readonly Color ElectricBlue = Color.FromArgb(0, 176, 255);
    public static readonly Color DeepBlue = Color.FromArgb(0, 26, 61);

    public static void DrawMark(Graphics graphics, RectangleF rect)
    {
        var saved = graphics.Save();
        graphics.SmoothingMode = SmoothingMode.AntiAlias;
        graphics.TranslateTransform(rect.X, rect.Y);
        graphics.ScaleTransform(rect.Width / 64f, rect.Height / 64f);
        using var outer = new SolidBrush(DeepBlue);
        using var strong = new Pen(BlazeBlue, 5.2f) { StartCap = LineCap.Round, EndCap = LineCap.Round };
        using var wave = new Pen(ElectricBlue, 4.2f) { StartCap = LineCap.Round, EndCap = LineCap.Round };
        using var white = new SolidBrush(Color.White);
        graphics.FillEllipse(outer, 2, 2, 60, 60);
        graphics.DrawArc(strong, 9, 9, 45, 45, 205, 288);
        graphics.DrawArc(wave, 17, 19, 32, 32, 230, 260);
        // Arrowhead and traffic pulses: network speed plus connectivity.
        graphics.FillPolygon(white, [new PointF(23, 44), new PointF(32, 17),
            new PointF(31, 34), new PointF(41, 28), new PointF(29, 50), new PointF(30, 37)]);
        graphics.Restore(saved);
    }

    public static Bitmap Bitmap(int size)
    {
        var bitmap = new Bitmap(size, size);
        using var g = Graphics.FromImage(bitmap);
        g.Clear(Color.Transparent);
        DrawMark(g, new RectangleF(0, 0, size, size));
        return bitmap;
    }

    public static Icon MakeIcon()
    {
        using var bmp = Bitmap(48);
        nint handle = bmp.GetHicon();
        try
        {
            using var temp = Icon.FromHandle(handle);
            return (Icon)temp.Clone();
        }
        finally { DestroyIcon(handle); }
    }

    [DllImport("user32.dll", SetLastError = true)]
    private static extern bool DestroyIcon(nint icon);
}
