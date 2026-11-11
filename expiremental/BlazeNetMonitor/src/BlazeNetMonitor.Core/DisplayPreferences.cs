using System.Drawing;
namespace BlazeNetMonitor.Core;

public static class DisplayPreferences
{
    public static string EffectiveMetric(string requested, int width, int height)
    {
        if (height < 58 || width < 195) return "Speed";
        if (requested != "Auto")
            return requested is "Speed" or "Latency" or "Loss" or "Jitter" or "Totals" ? requested : "Speed";
        return width >= 275 && height >= 75 ? "Latency" : "Speed";
    }

    public static int GraphWindowSeconds(int requested, int width, int height)
    {
        if (requested > 0) return Math.Clamp(requested, 10, 600);
        if (width < 190 || height < 45) return 30;
        if (width < 350) return 60;
        return 120;
    }

    public static bool UseBits(AppSettings s, int width, int height) => s.UnitMode switch
    {
        "Bits" => true,
        "Bytes" => false,
        _ => s.UseBits // preserve existing choice in auto, but adapt prefix through MonitorMath.Rate
    };

    public static string NormalizeGraphStyle(string? style) =>
        style is "Filled" or "Bars" or "Steps" or "Smooth" or "Dots" or "Impulse" ? style : "Line";

    public static bool TryGraphColor(string? raw, out Color color)
    {
        color = Color.Empty;
        if (raw is null || raw.Length != 7 || raw[0] != '#' ||
            !raw[1..].All(Uri.IsHexDigit)) return false;
        color = Color.FromArgb(
            Convert.ToInt32(raw.Substring(1, 2), 16),
            Convert.ToInt32(raw.Substring(3, 2), 16),
            Convert.ToInt32(raw.Substring(5, 2), 16));
        return true;
    }
}
