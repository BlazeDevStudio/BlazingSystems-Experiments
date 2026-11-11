using Microsoft.Win32;
using BlazeNetMonitor.Core;

namespace BlazeNetMonitor;

/// <summary>A per-process color palette. No Explorer hooks or undocumented shell APIs.</summary>
internal static class Theme
{
    public static Color Background { get; private set; }
    public static Color Panel { get; private set; }
    public static Color Border { get; private set; }
    public static Color Text { get; private set; }
    public static Color Muted { get; private set; }
    public static Color Accent { get; private set; }
    public static bool IsDark { get; private set; }
    public static bool HighContrast => SystemInformation.HighContrast;

    static Theme() => Apply(new AppSettings());

    public static void Apply(AppSettings options)
    {
        if (HighContrast)
        {
            IsDark = SystemColors.Window.GetBrightness() < .5f;
            Background = SystemColors.Window;
            Panel = SystemColors.Window;
            Border = SystemColors.WindowText;
            Text = SystemColors.WindowText;
            Muted = SystemColors.WindowText;
            Accent = SystemColors.Highlight;
            return;
        }

        var requested = options.ThemeMode;
        IsDark = requested.Equals("Dark", StringComparison.OrdinalIgnoreCase) ||
            (!requested.Equals("Light", StringComparison.OrdinalIgnoreCase) && IsWindowsDarkMode(WidgetGeometry.ResolvePlacement(options) == WidgetGeometry.InsideTaskbar));

        Background = IsDark ? Color.FromArgb(28, 32, 40) : Color.FromArgb(245, 247, 251);
        Panel = IsDark ? Color.FromArgb(38, 43, 54) : Color.White;
        Border = IsDark ? Color.FromArgb(75, 84, 98) : Color.FromArgb(193, 200, 212);
        Text = IsDark ? Color.FromArgb(245, 247, 251) : Color.FromArgb(31, 36, 45);
        Muted = IsDark ? Color.FromArgb(179, 188, 201) : Color.FromArgb(76, 86, 103);
        Accent = options.UseSystemAccent ? SystemColors.Highlight :
            (IsDark ? Color.FromArgb(255, 177, 97) : Color.FromArgb(185, 95, 24));
    }

    private static bool IsWindowsDarkMode(bool useTaskbarTheme)
    {
        try
        {
            using var key = Registry.CurrentUser.OpenSubKey(
                @"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize");
            var value = key?.GetValue(useTaskbarTheme ? "SystemUsesLightTheme" : "AppsUseLightTheme") ?? key?.GetValue("AppsUseLightTheme");
            return value is int flag && flag == 0;
        }
        catch { return false; }
    }

    public static Color State(ConnectionState state) => state switch
    {
        ConnectionState.Down => Color.FromArgb(247, 82, 92),
        ConnectionState.Unstable => Color.FromArgb(255, 153, 70),
        ConnectionState.Degraded => Color.FromArgb(245, 197, 57),
        ConnectionState.Stable => Color.FromArgb(55, 186, 116),
        ConnectionState.LongStable => Color.FromArgb(77, 160, 255),
        _ => Muted
    };
}
