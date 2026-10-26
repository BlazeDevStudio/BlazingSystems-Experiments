namespace BlazeNetMonitor;
internal static class Theme
{
    public static readonly Color Background = Color.FromArgb(22, 27, 36);
    public static readonly Color Panel = Color.FromArgb(30, 36, 47);
    public static readonly Color Border = Color.FromArgb(58, 68, 83);
    public static readonly Color Text = Color.FromArgb(235, 241, 248);
    public static readonly Color Muted = Color.FromArgb(168, 180, 195);
    public static readonly Color Accent = Color.FromArgb(255, 153, 70);
    public static Color State(BlazeNetMonitor.Core.ConnectionState state) => state switch
    {
        BlazeNetMonitor.Core.ConnectionState.Down => Color.FromArgb(247, 82, 92),
        BlazeNetMonitor.Core.ConnectionState.Unstable => Color.FromArgb(255, 153, 70),
        BlazeNetMonitor.Core.ConnectionState.Degraded => Color.FromArgb(255, 218, 78),
        BlazeNetMonitor.Core.ConnectionState.Stable => Color.FromArgb(72, 215, 144),
        BlazeNetMonitor.Core.ConnectionState.LongStable => Color.FromArgb(77, 160, 255),
        _ => Color.FromArgb(129, 142, 160)
    };
}
